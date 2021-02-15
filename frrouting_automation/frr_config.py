#!/usr/bin/env python3

import argparse
import bisect
import docker
import ipaddress
import json
import os
import fileinput
import time


def load_config(filepath):
    '''Read JSON configuration'''
    topology = os.path.basename(filepath).split('.')[0]
    with open(filepath, 'r') as config_file:
        config_json = json.load(config_file)
    return topology, config_json

def launch_topology(topology, routers, links, client):
    '''Launch containers and bridges'''
    create_containers(routers, client, topology)
    create_networks(links, client)
    config_routers(routers, client)

def create_networks(links, client):
    '''Create bridges and add containers to the bridge'''
    for link_name in sorted(links.keys()):
        link = links[link_name]

        # Determine network configuration for bridge
        ipam_pool = docker.types.IPAMPool(subnet=str(link.subnet))
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])

        # Create the bridge
        print("Creating %s" % link.name)
        current_network = client.networks.create(link.name, driver='bridge', ipam=ipam_config)

        # For each router in the bridge, assign that container to that bridge
        for router in link.routers:
            print("Connecting %s to %s" % (router.name, link.name))
            current_network.connect(client.containers.get(router.name))

def create_containers(routers, client, topology):
    '''Create a container for each router'''
    images = set()

    for router_name in sorted(routers.keys()):
        router = routers[router_name]
        print("Creating %s (%s)" % (router.name, router.image))
        if router.image not in images:
            client.images.pull(router.image)
            images.add(router.image)
        client.containers.create(router.image, detach=True, name=router.name,
                labels=[topology], cap_add=["ALL"],
                command="/bin/bash", stdin_open=True, tty=True)

def config_routers(routers, client):
    for router_name in sorted(routers.keys()):
        router = routers[router_name]
        if "frr" in router.image:
            config_daemons(router)
            config_vtysh(router)

            if "bgp" in router.protocols:
                config_bgp(router)
            if "ospf" in router.protocols:
                config_ospf(router)
        elif "bird" in router.image:
            config_bird(router)
        print("Starting %s" % router.name)
        container = client.containers.get(router.name)
        container.start()
        if "bird" in router.image:
            os.system("docker exec -it " + router.name +" bin/bash -c 'service bird start'")


def config_bird(router):
    with open ('configs/bird_conf.txt',"r") as file:
        template = file.read()
    with open('/tmp/bird.conf', 'w') as file:
        file.write(template)
    os.system("docker cp /tmp/bird.conf " + router.name +":/etc/bird/bird.conf")

def config_daemons(router):
    '''Configure daemons'''
    # Load template
    with open('configs/daemons_temp', 'r') as file:
        template = file.read()

    # Fill-in template
    for protocol in router.protocols:
        template = template.replace(protocol+'d=no', protocol+'d=yes')

    # Put configuration on router
    with open('/tmp/daemons', 'w') as file:
        file.write(template)
    os.system("docker cp /tmp/daemons " + router.name +":/etc/frr/daemons")

def config_vtysh(router):
    '''Configure vtysh'''
    # Load template
    with open('configs/vtysh.conf_temp', 'r') as file:
        template = file.read()

    # Fill-in template
    template = template.replace('<router_name>', router.name)

    # Put configuration on router
    with open('/tmp/vtysh.conf', 'w') as file:
        file.write(template)
    os.system("docker cp /tmp/vtysh.conf " + router.name +":/etc/frr/vtysh.conf")


def config_bgp(router):
    print("Configuring BGP for "+router.name)

    # Load configuration template
    with open('configs/bgpd.conf_temp', 'r') as file:
        template = file.read()

    # Fill-in holes in template
    template = template.replace('<router_name>', router.name)
    template = template.replace('<as_num>',str(router.as_num))
    template = template.replace('<id_num>',str(router.id_num))

    # Advertise bridges that only contain this router
    networks = ""
    for link in router.links:
        if len(link.routers) == 1:
            networks += ' network '+str(link.subnet)+'\n'
    template = template.replace(' <networks>\n', networks)

    # Determine neighbors
    neighbors = ""
    for link in router.links:
        for linked_router in link.routers:
            if linked_router != router and "bgp" in linked_router.protocols:
                peer = link.get_address(linked_router)
                neighbors += ' neighbor %s remote-as %d\n' % (peer, linked_router.as_num)
                neighbors += ' neighbor %s next-hop-self\n' % (peer)
    template = template.replace(' <neighbours>\n', neighbors)

    # Put configuration on router
    with open('/tmp/bgpd.conf', 'w') as file:
        file.write(template)
    os.system("docker cp /tmp/bgpd.conf " + router.name +":/etc/frr/bgpd.conf")

def config_ospf(router):
    print("Configuring OSPF for "+router.name)

# Load configuration template
    with open('configs/ospfd.conf_temp', 'r') as file:
        template = file.read()

    # Fill-in holes in template
    template = template.replace('<router_name>', router.name)

    # Put configuration on router
    with open('/tmp/ospfd.conf', 'w') as file:
            file.write(template)
    os.system("docker cp /tmp/ospfd.conf " + router.name +":/etc/frr/ospfd.conf")

class Link:
    def __init__(self, name, subnet):
        self.name = name
        self.routers = []
        self.subnet = subnet

    @classmethod
    def from_config(self, config, subnet):
        link = Link(config["name"], subnet)
        return link

    def add_router(self, router):
        # Routers must be inserted in lexicographic order, because routers are
        # started in lexicographic order
        bisect.insort(self.routers, router)

    def get_routers():
        return self.routers

    def get_subnet():
        return self.subnet

    def get_address(self, router):
        if router not in self.routers:
            return None
        return list(self.subnet.hosts())[self.routers.index(router)+1]

    def __str__(self):
        return "Link<%s,%s,[%s]>" % (self.name, self.subnet,
                ','.join([r.name for r in self.routers]))

class Router:
    def __init__(self, name, as_num):
        self.name = name
        self.image = 'frrouting/frr'
        self.links = []
        self.protocols = set()
        self.as_num = as_num
        self.ad_bridge = None
        self.id_num = None

    @classmethod
    def from_config(self, config, as_num):
        router = Router(config["name"], as_num)
        if "protocols" in config:
            for protocol in config["protocols"]:
                router.add_protocol(protocol)
        if "image" in config:
            router.image = config["image"]
        return router

    def add_link(self, link):
        if self.id_num is None:
            self.id_num = link.get_address(self)
        self.links.append(link)

    def add_protocol(self, protocol):
        if protocol not in ["bgp", "ospf"]:
            raise ConfigurationError("Invalid protocol: %s" % protocol)
        self.protocols.add(protocol)

    def __lt__(self, other):
        return self.name < other.name

class ConfigurationError(Exception):
    pass

def parse_config(config):
    '''Extract list of routers and links from config'''

    # Create router objects
    as_nums = (n for n in range(1,len(config["routers"])+1))
    routers = {}
    for router_config in config["routers"]:
        # Use specified or auto-generated ASN
        if "as_num" in router_config:
            as_num = router_config["as_num"]
        else:
            as_num = next(as_nums)

        # Create router
        router = Router.from_config(router_config, as_num)
        routers[router.name] = router

    # Determine IP subnets to use
    n = len(config["links"])
    n = 29 - n.bit_length()
    supernet = ipaddress.IPv4Network('10.10.0.0/%d' % n)
    subnets = supernet.subnets(new_prefix=29)

    # Create link objects
    links = {}
    for link_config in config["links"]:
        # Use specified or auto-generated subnet
        if "subnet" in link_config:
            subnet = link_config["subnet"]
        else:
            subnet = next(subnets)

        # Create link
        link = Link.from_config(link_config, subnet)
        links[link.name] = link

        # Add routers to link
        for router_name in link_config["routers"]:
            if router_name not in routers:
                raise ConfigurationError("No such node: %s" % router_name)
            router = routers[router_name]
            link.add_router(router)
            router.add_link(link)
    return routers, links

def cleanup_topology(topology, client):
    '''Stop and remove existing containers and bridges'''
    for container in client.containers.list(filters={"label": topology}):
        print("Cleaning up running container %s" % container.name)
        container.stop()
        container.remove()
    print("Cleaning up all unused containers")
    client.containers.prune()
    print("Cleaning up networks")
    client.networks.prune()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Path to JSON config file", required=True)
    parser.add_argument("-a", "--action", choices=['start', 'stop', 'restart'], help="Operation to perform", required=True)
    parser.add_argument("-t", "--tcp", choices=['tcpon'], help="Option to have tcpdump on", required=False)
    parser.add_argument("-d", "--delay", help="Interfaces to apply delay to", required=False)
    settings = parser.parse_args()

    # Load and parse configuration
    topology, config = load_config(settings.config)
    routers, links = parse_config(config)

    client = docker.from_env()
    # Stop old instance
    if (settings.action in ['stop', 'restart']):
        cleanup_topology(topology, client)
    # Start new instance
    if (settings.action in ['start', 'restart']):
        if client.containers.list(filters={"label": topology}):
            print("ERROR: %s is already running; stop or restart the topology" % topology)
        else:
            launch_topology(topology, routers, links, client)

    #time for manually excuting the delay/need to be automated
    if settings.delay != None:
        delay_components = settings.delay.split("//")
        delaying_interfaces = delay_components[0].split("/")
        delaying_options = delay_components[1].split("/")
        for delaying_interface in delaying_interfaces:
            print('Appying delay to interface '+delaying_interface)
            os.system('nohup pumba netem --duration '+delaying_options[0]+'s -i '+ delaying_interface +' --tc-image gaiadocker/iproute2 delay --time '+delaying_options[1]+' --jitter '+delaying_options[2]+' >/dev/null 2>&1 &')

    #Settings for tcpdump
    if (settings.tcp in ['tcpon']):
        os.system('docker run --rm --net=host -v ~/protocol-verification/pattern_recog:/tcpdump kaazing/tcpdump')
    client.close()

if __name__ == "__main__":
    main()