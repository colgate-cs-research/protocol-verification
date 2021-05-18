#!/usr/bin/env python3

import argparse
import json
import os
import shutil

def load_config(filepath):
    '''Read JSON configuration'''
    experiment = os.path.basename(filepath).split('.')[0]
    with open(filepath, 'r') as config_file:
        config_json = json.load(config_file)
    return experiment, config_json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Path to JSON config file", required=True)
    parser.add_argument("-o", "--output", help="Path to output directory",
    required=True)
    parser.add_argument("-r", "--repeat", help="Number of times to repeat each topology", default=1, type=int)
    settings = parser.parse_args()

    # Load experiment configuration
    experiment, config = load_config(settings.config)

    # Prepare output directory
    base_outdir = os.path.join(os.path.abspath(settings.output), experiment)
    os.makedirs(base_outdir, exist_ok=True)

    base_frr_cmd = ["python3", "frr_config.py", "-a" ]

    # Run experiment specified number of times
    for iteration in range(settings.repeat):
        print("\n## RUNNING ITERATION %d..." % (iteration+1))
        # Run experiment for each topology
        for topology in config["topologies"]:
            print("\n#### RUNNING TOPOLOGY %s..." % topology)
            # Prepare topology output directory
            topo_outdir = os.path.join(base_outdir, "%s_%02d" % (topology, iteration + 1))
            os.makedirs(topo_outdir, exist_ok=True)

            # Run frr_config.py
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "topologies", "%s.json" % topology) 
            extra_frr_args = ["-t", topo_outdir, "-c", config_path, "-p", str(config["packets"]), "-f", '"%s"' % config["filter"]]
            if ("delay" in config):
                extra_frr_args.extend(["-d", config["delay"]])
            frr_cmd = " ".join(base_frr_cmd) + " start " + " ".join(extra_frr_args)
            print(frr_cmd)
            os.system(frr_cmd)
            frr_cmd = " ".join(base_frr_cmd) + " stop " + " ".join(extra_frr_args)
            print(frr_cmd)
            os.system(frr_cmd)

            # Run ospf_dump.py
            pcap_path = os.path.join(topo_outdir, "tcpdump.pcap")
            ospf_dump_args = ["python3", "../pattern_recog/ospf_dump.py", "-p", pcap_path]
            ospf_dump_cmd = " ".join(ospf_dump_args)
            print(ospf_dump_cmd)
            os.system(ospf_dump_cmd)
            shutil.move("parsed_tcp.txt", os.path.join(topo_outdir, "parsed_tcp.txt"))

if __name__ == "__main__":
    main()