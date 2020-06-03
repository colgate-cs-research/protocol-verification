#!/usr/bin/env python3

import argparse
import docker
import json
import os
import time

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

    #list all neworks and containers
    #print("All CONTAINERS")
    #for container in client.containers.list(all=True):
    #    print(container.name, container.status)
    #print("ALL NETWORKS")
    #for network in client.networks.list():
    #    print(network.name, network.containers)

def network_create(bridge_dict,client):
    '''Create bridges and add containers to the bridge'''
    # for each bridge
    for bridge, cor_routers in bridge_dict.items():
        #create the bridge
        print("Creating %s" % bridge)
        current_network=client.networks.create (str(bridge),driver="bridge")
        #for each router in the bridge, assign that container to that bridge
        for s_router in cor_routers:
            print("Connecting %s to %s" % (s_router, bridge))
            current_container = client.containers.get(s_router)
            current_network.connect(current_container)

def container_create(router_list, client, topology):
    '''Create and start a container for each router'''
    client.images.pull('frrouting/frr')
    for router in sorted(router_list):
        print("Starting %s" % router)
        client.containers.run('frrouting/frr', detach=True, name=str(router), labels=[topology], cap_add=["NET_ADMIN", "SYS_ADMIN"])

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
