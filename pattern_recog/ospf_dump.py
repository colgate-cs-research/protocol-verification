#!/usr/bin/env python3

import argparse
import os
import subprocess
import xml.etree.ElementTree as ET

def gen_xml(pcappath):
    basepath, pcapfilename  = os.path.split(pcappath)
    xmlfilename =  pcapfilename.replace('.pcap', '_ospf.xml')
    xmlpath = os.path.join(basepath, xmlfilename)
    with open(xmlpath, 'w+') as xmlfile:
        cmd = ["tshark", "-T", "pdml", "-r", pcappath, "ospf"]
        subprocess.run(cmd, stdout=xmlfile)
    return xmlpath

def parse_xml(xmlpath):
   return ET.parse(xmlpath).getroot()

def print_field(field, indent=""):
    if 'showname' in field.attrib:
        print(indent + field.attrib['showname'])
    elif 'show' in field.attrib:
        print(indent + field.attrib['show'])
    for child in field:
        print_field(child, indent + " "*4)

def print_proto(proto):
    print("Layer %s:" % (proto.attrib['name'].upper()))
    for field in proto:
        print_field(field, " "*4)

def print_packet(packet, short=False):
    for proto in packet:

        if (proto.attrib['name'] == 'geninfo'):
            for field in proto:
                if (field.attrib['name'] == 'timestamp'):
                    print('Time Stamp%s' % field.attrib['value'])
        elif ((not short and proto.attrib['name'] != "frame") 
                or proto.attrib['name'] == "ospf"):
            print_proto(proto)

def print_packets(xml, short=False):
    count = 0
    for packet in xml:
        count += 1
        print('PACKET RECIEVED NUMBER IN CAPTURE: %d' % (count))
        print_packet(packet, short)
        print('~')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pcap", help="Path to PCAP file", 
            required=True)
    parser.add_argument("-s", "--short", help="Only display OSPF header", 
            action="store_true")
    settings = parser.parse_args()

    xmlpath = gen_xml(settings.pcap)
    xml = parse_xml(xmlpath)
    print_packets(xml, settings.short)

if __name__ == "__main__":
    main()
