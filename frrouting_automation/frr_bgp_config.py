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

def launch_topology(topology, router_list, bridge_dict, client):
    '''Launch containers and bridges'''
    router_class_list = container_create(router_list, client, topology)
    network_create(bridge_dict, client,router_class_list)


def bgp_config(router_class_list, link_class_list, client):
    for router_object in router_class_list:
        print("Configuring "+router_object.name)
        #find all neighbors
        with open('configs/bgpd.conf_temp.txt', 'r') as file:
            filedata = file.read()
        filedata=filedata.replace('as_num',str(router_object.as_num))
        filedata=filedata.replace('id_num',str(router_object.id_num))
        filedata=filedata.replace('ad_bridge',str(router_object.ad_bridge))
        for link_bridge in router_object.links:
            for linked_router in link_bridge.routers:
                if linked_router.name != router_object.name:
                    filedata=filedata.replace('!neighbour config', 'neighbor '+str(linked_router.id_num)+' remote-as '+str(link_bridge.as_num)+'\n!neighbour config')
        with open('configs/bgpd.conf', 'w') as file:
            file.write(filedata)
        os.system("docker cp configs/bgp_daemons " + router_object.name +":/etc/frr/daemons")
        os.system("docker cp configs/bgpd.conf " + router_object.name +":/etc/frr/bgpd.conf")
        print("Starting %s" % router_object.name)
        current_router = client.containers.get(router_object.name)
        current_router.start()


def network_create(bridge_dict,client,router_class_list):
    '''Create bridges and add containers to the bridge'''
    # Determine IP subnets to use
    n = len(bridge_dict)
    n = 29 - n.bit_length()
    supernet = ipaddress.IPv4Network('10.10.0.0/%d' % n)
    subnets = list(supernet.subnets(new_prefix=29))
    print(subnets)
    static_id_num = ipaddress.IPv4Address('10.10.0.2')
    i = 0

    #create list of links
    link_class_list = []
    as_num = 0
    loop_count = 0
    for bridge, cor_routers in bridge_dict.items():
        if loop_count == 0:
            loop_count += 1
            id_num = static_id_num
        else:
            id_num = static_id_num+8
        # Determine network configuration for bridge
        ipam_pool = docker.types.IPAMPool(subnet=str(subnets[i]))
        i += 1
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
        #create the bridge
        print("Creating %s" % bridge)
        current_network=client.networks.create (str(bridge), driver='bridge', ipam=ipam_config)
        #for each router in the bridge, assign that container to that bridge
        current_link = Link(bridge,subnets[i],as_num)
        link_class_list.append(current_link)
        for s_router in cor_routers:
            print("Connecting %s to %s" % (s_router, bridge))
            current_network.connect(client.containers.get(s_router))
            #two direction connect link class and router class
            for router_object in router_class_list:
                if (router_object.name == s_router):
                    router_object.add_link(current_link)
                    current_link.add_router(router_object)
                    # assign as number to router object
                    router_object.add_as_num(as_num)
                    if router_object.id_num == None:
                        router_object.add_id_num(id_num)
                        id_num+=1
        as_num += 1
    #config routers
    ospf_config(router_class_list, link_class_list,client)


                    
class Link:
    def __init__(self, name, subnet, as_num):
        self.name = name
        self.routers = []
        self.subnet = subnet
        self.as_num = as_num

    def add_router(self, router):
        self.routers.append(router)

    def get_routers():
        return self.routers

    def get_subnet():
        return self.subnet

    def get_address(self, router):
        if router not in self.routers:
            return None
        return self.subnet.hosts()[self.routers.index(router)]

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

def container_create(router_list, client, topology):
    '''Create and start a container for each router'''
    client.images.pull('frrouting/frr')
    #create a list of router class objects
    router_class_list = []
    
    n = len(router_list)
    n = 29 - n.bit_length()
    supernet = ipaddress.IPv4Network('10.20.0.0/%d' % n)
    subnets = list(supernet.subnets(new_prefix=29))
    print(subnets)
    i = 0

    for router in sorted(router_list):
        print("Creating %s" % router)
        client.containers.create('frrouting/frr', detach=True, name=str(router), labels=[topology], cap_add=["NET_ADMIN", "SYS_ADMIN"])
        #create router class objects
        current_router = Router(router,subnets[i])
        i+=1
        #append to router_class_list
        router_class_list.append(current_router)
    return router_class_list

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
