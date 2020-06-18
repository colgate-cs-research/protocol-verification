#!/usr/bin/env python3

import argparse
import docker
import ipaddress
import json
import os
import fileinput


def load_config(filepath):
    '''Read JSON configuration'''
    topology = os.path.basename(filepath).split('.')[0]
    with open(filepath, 'r') as config_file:
        config_json = json.load(config_file)
    return topology, config_json

def launch_topology(topology, router_list, bridge_dict, client,protocol_dict):
    '''Launch containers and bridges'''
    router_class_list = container_create(router_list, client, topology)
    link_class_list = network_create(bridge_dict, client,router_class_list, protocol_dict)
    #config routers
    config(router_class_list, link_class_list,client,protocol_dict)

def network_create(bridge_dict,client,router_class_list,protocol_dict):
    '''Create bridges and add containers to the bridge'''
    # Determine IP subnets to use
    n = len(bridge_dict)
    n = 29 - n.bit_length()
    supernet = ipaddress.IPv4Network('10.10.0.0/%d' % n)
    subnets = list(supernet.subnets(new_prefix=29))
    print(subnets)
    static_id_num = ipaddress.IPv4Address('10.0.0.1')
    i = 0
    #create list of links
    link_class_list = []
    loop_count = 0
    for bridge, cor_routers in bridge_dict.items():
        if loop_count == 0:
            loop_count += 1
            id_num = static_id_num
        else:
            id_num = static_id_num+8
        # Determine network configuration for bridge
        ipam_pool = docker.types.IPAMPool(subnet=str(subnets[i]))
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
        #create the bridge
        print("Creating %s" % bridge)
        current_network=client.networks.create (str(bridge), driver='bridge', ipam=ipam_config)
        #for each router in the bridge, assign that container to that bridge
        current_link = Link(bridge,subnets[i])
        link_class_list.append(current_link)
        i += 1
        link_router_connect(cor_routers, bridge, current_network, router_class_list, current_link, id_num, client)
    return link_class_list

def link_router_connect(cor_routers, bridge, current_network, router_class_list, current_link, id_num, client):
    as_num = 1
    for s_router in sorted(cor_routers):
        print("Connecting %s to %s" % (s_router, bridge))
        current_network.connect(client.containers.get(s_router))
        #two direction connect link class and router class
        for router_object in router_class_list:
            if (router_object.name == s_router):
                router_object.add_link(current_link)
                current_link.add_router(router_object)
                # assign as number to router object
                if router_object.as_num == None:
                    router_object.add_as_num(as_num)
                    as_num += 1
                if router_object.id_num == None:
                    router_object.add_id_num(id_num)
                    id_num+=1


def container_create(router_list, client, topology):
    '''Create and start a container for each router'''
    client.images.pull('frrouting/frr')
    #create a list of router class objects
    router_class_list = []
    #range of addresses for router class objects
    n = len(router_list)
    n = 29 - n.bit_length()
    supernet = ipaddress.IPv4Network('10.20.0.0/%d' % n)
    subnets = list(supernet.subnets(new_prefix=29))
    print(subnets)
    i = 0
    #create router containers
    for router in sorted(router_list):
        print("Creating %s" % router)
        client.containers.create('frrouting/frr', detach=True, name=str(router), labels=[topology], cap_add=["NET_ADMIN", "SYS_ADMIN"])
        #create router class objects
        current_router = Router(router,subnets[i])
        i+=1
        #append to router_class_list
        router_class_list.append(current_router)
    return router_class_list

def config(router_class_list, link_class_list, client,protocol_dict):
    for router_object in router_class_list:
        pro_num = 0
        for i in range(len(protocol_dict[router_object.name])):
            #configuring routers with BGP
            if protocol_dict[router_object.name][i] == "bgp":
                pro_num = bgp_config(router_object, pro_num)
            #configuring routers with OSPF
            elif protocol_dict[router_object.name][i] == "ospf":
                pro_num = ospf_config(router_object, pro_num)

        print("Starting %s" % router_object.name)
        current_router = client.containers.get(router_object.name)
        current_router.start()

def bgp_config(router_object, pro_num):
    print("Configuring BGP for "+router_object.name)
    #find all neighbors
    with open('configs/bgpd_bug.conf_temp', 'r') as file:
        filedata = file.read()
    filedata=filedata.replace('as_num',str(router_object.as_num))
    filedata=filedata.replace('id_num',str(router_object.id_num))
    filedata=filedata.replace('ad_bridge',str(router_object.ad_bridge))
    for link_bridge in router_object.links:
        for linked_router in link_bridge.routers:
            if linked_router.name != router_object.name:
                filedata=filedata.replace('linked_router_ad',str(link_bridge.get_address(linked_router)))
                filedata=filedata.replace('!neighbour config', 'neighbor '+str(link_bridge.get_address(linked_router))+' remote-as '+str(linked_router.as_num)+'\n !neighbour config')
                if linked_router.name == "router2" and router_object.name == "router1":
                    filedata=filedata.replace('!neighbour max prefix', 'neighbor '+str(link_bridge.get_address(linked_router))+ ' maximum-prefix 3 warning-only')
    with open('configs/bgpd.conf', 'w') as file:
        file.write(filedata)
    #modifying daemons files
    if pro_num == 0:
        with open('configs/daemons_temp', 'r') as file:
            filedata = file.read()
        filedata=filedata.replace('bgpd=no','bgpd=yes')
        with open('configs/daemons', 'w') as file:
            file.write(filedata)
        pro_num = 1
    else:
        with open('configs/daemons', 'r') as file:
            filedata = file.read()
        filedata=filedata.replace('bgpd=no','bgpd=yes')
        with open('configs/daemons', 'w') as file:
            file.write(filedata)
    os.system("docker cp configs/daemons " + router_object.name +":/etc/frr/daemons")
    os.system("docker cp configs/bgpd.conf " + router_object.name +":/etc/frr/bgpd.conf")
    return pro_num

def ospf_config(router_object, pro_num):
    print("Configuring OSPF for "+router_object.name)
    if pro_num ==0:
        with open('configs/daemons_temp', 'r') as file:
            filedata = file.read()
        filedata=filedata.replace('ospfd=no','ospfd=yes')
        with open('configs/daemons', 'w') as file:
            file.write(filedata)
        pro_num = 1
    else:
        with open('configs/daemons', 'r') as file:
            filedata = file.read()
        filedata=filedata.replace('ospfd=no','ospfd=yes')
        with open('configs/daemons', 'w') as file:
            file.write(filedata)
    os.system("docker cp configs/daemons " + router_object.name +":/etc/frr/daemons")
    os.system("docker cp configs/ospfd.conf " + router_object.name +":/etc/frr/ospfd.conf")
    return pro_num


class Link:
    def __init__(self, name, subnet):
        self.name = name
        self.routers = []
        self.subnet = subnet

    def add_router(self, router):
        self.routers.append(router)

    def get_routers():
        return self.routers

    def get_subnet():
        return self.subnet

    def get_address(self, router):
        if router not in self.routers:
            return None
        return list(self.subnet.hosts())[self.routers.index(router)+1]

class Router:
    def __init__(self, name, ad_bridge):
        self.name = name
        self.links = []
        self.as_num = None
        self.ad_bridge = ad_bridge
        self.id_num = None

    def add_link(self, link):
        self.links.append(link)
    
    def add_as_num(self, as_num):
        if self.as_num == None:
            self.as_num = as_num

    def add_id_num (self, id_num):
        if self.id_num == None:
            self.id_num = id_num
    

def parse_config(config):
    '''Extract list of routers and bridges from config'''
    router_list=set()
    #create a dict of bridges: bridge_dict
    #contains a keyvalue pair where key=bridge_name & value=[router1, router2] i.e. connecting routers
    bridge_dict={}
    protocol_dict ={}
    for protocol in config["protocols"]:
        for pro in protocol.values():
            protocol_dict[pro["router"]] = (pro["protocol"])
    for edge in config["edges"]:
        for node in edge.values():
            router_list.add(node['hostname'])
            if node["interfaceName"] not in bridge_dict:
                bridge_dict[node["interfaceName"]]=set()
            bridge_dict[node["interfaceName"]].add(node['hostname'])
    return router_list, bridge_dict, protocol_dict

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
    settings = parser.parse_args()

    # Load and parse configuration
    topology, config = load_config(settings.config)
    router_list, bridge_dict, protocol_dict = parse_config(config)

    client = docker.from_env()
    # Stop old instance
    if (settings.action in ['stop', 'restart']):
        cleanup_topology(topology, client)
    # Start new instance
    if (settings.action in ['start', 'restart']):
        if client.containers.list(filters={"label": topology}):
            print("ERROR: %s is already running; stop or restart the topology" % topology)
        else:
            launch_topology(topology, router_list, bridge_dict, client,protocol_dict)
    client.close()

if __name__ == "__main__":
    main()
