#!/usr/bin/env python3

import argparse
import docker
import json
import pprint
import os

#refresh/empty networks/containers
os.system("docker stop $(docker ps -aq)")
os.system("docker rm $(docker ps -aq)")
os.system("docker system prune -f")

def load_config(filepath):
    with open(filepath, 'r') as config_file:
        config_json = json.load(config_file)
    pp = pprint.PrettyPrinter()
    pp.pprint(config_json)
    return config_json

def launch_containers(config):
    client = docker.from_env()
    for key, value in config.items():
        config_list = value
    #config_list is a list
    #each item in config list is a dict with key=node, value = router + bridge
    #create a list of routers: router_list
    router_list_bridge_dict = parsing(config_list)
    router_list = router_list_bridge_dict[0]
    bridge_dict = router_list_bridge_dict[1]
    # for each router in router list, create a container
    container_create(router_list,client)
    #create bridges and link containers
    network_create(bridge_dict,client)
    #list all neworks
    #list all containers
    print("ALL NETWORKS")
    os.system("docker network ls")
    print("All CONTAINERS")
    os.system("docker container ls -a")

def network_create(bridge_dict,client):
    # for each bridge
    for bridge, cor_routers in bridge_dict.items():
        #create the bridge
        current_network=client.networks.create (str(bridge),driver="bridge")
        #for each router in the bridge, assign that container to that bridge
        for s_router in cor_routers:
            current_container = client.containers.get(s_router)
            current_network.connect(current_container)

def container_create(router_list,client):
    for router in router_list:
        client.containers.run('frrouting/frr', detach=True, name=str(router))

def parsing(config_list):
    router_list=[]
    #create a dict of bridges: bridge_dict
    #contains a keyvalue pair where key=bridge_name & value=[router1, router2] i.e. connecting routers
    bridge_dict={}
    node_num = 1
    for list_dict in config_list:
        #three times
        for key, host_inter in list_dict.items():
            #two times
            if host_inter['hostname'] not in router_list:
                router_list.append(host_inter['hostname'])
            if host_inter["interfaceName"] in bridge_dict:
                if host_inter["hostname"] not in bridge_dict[host_inter["interfaceName"]]:
                    bridge_dict[host_inter["interfaceName"]].append(host_inter['hostname'])
            else: 
                bridge_dict[host_inter["interfaceName"]]=list()
                bridge_dict[host_inter["interfaceName"]].append(host_inter['hostname'])
    return router_list, bridge_dict

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Path to JSON config file", required=True)
    settings = parser.parse_args()

    config = load_config(settings.config)
    launch_containers(config)

if __name__ == "__main__":
    main()