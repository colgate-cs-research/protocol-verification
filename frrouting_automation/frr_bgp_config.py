#!/usr/bin/env python3

import argparse
import docker
import ipaddress
import json
import os

def load_config(filepath):
    '''Read JSON configuration'''
    topology = os.path.basename(filepath).split('.')[0]
    with open(filepath, 'r') as config_file:
        config_json = json.load(config_file)
    return topology, config_json

def launch_topology(topology, router_list, bridge_dict, client):
    '''Launch containers and bridges'''
    container_create(router_list, client, topology)
    network_create(bridge_dict, client)


def ospf_config(router):
    #configurate current router
    os.system("docker cp configs/ospf_daemons " + router +":/etc/frr/daemons")
    os.system("docker cp configs/ospfd.conf " + router +":/etc/frr/ospfd.conf")


def network_create(bridge_dict,client):
    '''Create bridges and add containers to the bridge'''
    # Determine IP subnets to use
    n = len(bridge_dict)
    n = 29 - n.bit_length()
    supernet = ipaddress.IPv4Network('10.10.0.0/%d' % n)
    subnets = list(supernet.subnets(new_prefix=29))
    print(subnets)
    
    #first two addrs reserved
    #0 1
    #8 9
    #16 17
    #link and router dictionaries
    # for each bridge
    i = 0
    for bridge, cor_routers in bridge_dict.items():
        # Determine network configuration for bridge
        ipam_pool = docker.types.IPAMPool(subnet=str(subnets[i]))
        i += 1
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
        #create the bridge
        print("Creating %s" % bridge)
        current_network=client.networks.create (str(bridge), driver='bridge', ipam=ipam_config)
        #for each router in the bridge, assign that container to that bridge
        for s_router in cor_routers:
            print("Connecting %s to %s" % (s_router, bridge))
            current_network.connect(client.containers.get(s_router))

class Link:
    def __init__(self, name, subnet):
        self.name = name
        self.routers = []
        self.subnet = subnet

    def add_router(router):
        self.routers.append(router)

    def get_routers():
        return self.routers

    def get_subnet():
        return self.subnets

    def get_address(router):
        if router not in self.routers:
            return None
        return self.subnet.hosts()[self.routers.index(router)]

class Router:
    def __init__(self, name):
        self.name = name
        self.links = []

    def add_link(link):
        self.links.append(link)

def container_create(router_list, client, topology):
    '''Create and start a container for each router'''
    client.images.pull('frrouting/frr')
    for router in sorted(router_list):
        print("Creating %s" % router)
        client.containers.create('frrouting/frr', detach=True, name=str(router), labels=[topology], cap_add=["NET_ADMIN", "SYS_ADMIN"])
        print("Configuring %s" % router)
        #config current router
        ospf_config(router)
        print("Starting %s" % router)
        current_router = client.containers.get(router)
        current_router.start()

def parse_config(config):
    '''Extract list of routers and bridges from config'''
    router_list=set()
    #create a dict of bridges: bridge_dict
    #contains a keyvalue pair where key=bridge_name & value=[router1, router2] i.e. connecting routers
    bridge_dict={}
    for edge in config["edges"]:
        for node in edge.values():
            router_list.add(node['hostname'])
            if node["interfaceName"] not in bridge_dict:
                bridge_dict[node["interfaceName"]]=set()
            bridge_dict[node["interfaceName"]].add(node['hostname'])
    return router_list, bridge_dict

def cleanup_topology(topology, client):
    '''Stop and remove existing containers and bridges'''
    for container in client.containers.list(filters={"label": topology}):
        print("Cleaning up %s" % container.name)
        container.stop()
        container.remove()

    print("Cleaning up networks")
    client.networks.prune()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Path to JSON config file", required=True)
    parser.add_argument("-a", "--action", choices=['start', 'stop', 'restart'], help="Operation to perform", required=True)
    settings = parser.parse_args()

    # Load and parse configuration
    topology, config = load_config(settings.config)
    router_list, bridge_dict = parse_config(config)

    client = docker.from_env()
    # Stop old instance
    if (settings.action in ['stop', 'restart']):
        cleanup_topology(topology, client)
    # Start new instance
    if (settings.action in ['start', 'restart']):
        if client.containers.list(filters={"label": topology}):
            print("ERROR: %s is already running; stop or restart the topology" % topology)
        else:
            launch_topology(topology, router_list, bridge_dict, client)
    client.close()

if __name__ == "__main__":
    main()
