#!/usr/bin/env python3

import argparse
import docker
import json
import pprint

def load_config(filepath):
    with open(filepath, 'r') as config_file:
        config_json = json.load(config_file)

    pp = pprint.PrettyPrinter()
    pp.pprint(config_json)
    return config_json

def launch_containers(config):
    client = docker.from_env()
    # TODO: properly start containers

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Path to JSON config file", required=True)
    settings = parser.parse_args()

    config = load_config(settings.config)
    launch_containers(config)

if __name__ == "__main__":
    main()