#!/usr/bin/env python3

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
        print_field(child, indent + "  ")

def print_proto(proto):
    for field in proto:
        print_field(field, "")

def print_packet(packet):
    for proto in packet:
        if proto.attrib['name'] == "ospf":
            print_proto(proto)

def print_packets(xml):
    for packet in xml:
        print_packet(packet)
        print('~')

def main():
    pcappath = "tcpdump.pcap"
    xmlpath = gen_xml(pcappath)
    xml = parse_xml(xmlpath)
    print_packets(xml)

if __name__ == "__main__":
    main()
