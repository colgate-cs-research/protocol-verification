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

def print_field(proto, field, outfile, short=False, indent=""):
    value = None
    if 'showname' in field.attrib:
        value = field.attrib['showname']
    elif 'show' in field.attrib:
        value = field.attrib['show']

    if (short):
        if (proto.attrib['name'] == "ip"):
            if (field.attrib['name'] not in ["ip.src", "ip.dst"]):
                return 
        elif (proto.attrib['name'] == "ospf"):
            if (field.attrib['name'] in ["ospf.version", "ospf.checksum", "ospf.v2.options.dn", "ospf.v2.options.o", "ospf.v2.options.dc", "ospf.v2.options.l", "ospf.v2.options.n", "ospf.v2.options.mc", "ospf.v2.options.e", "ospf.v2.options.mt"]):
                return
    
    outfile.write(indent + value +"\n")

    for child in field:
        print_field(proto, child, outfile, short, indent + " "*4)

def print_proto(proto, outfile, short=False):
    outfile.write("Layer %s:" % (proto.attrib["name"].upper())+"\n")
    for field in proto:
        print_field(proto, field, outfile, short, " "*4)

def print_packet(packet, outfile, short=False):
    for proto in packet:
        if (proto.attrib['name'] == 'geninfo'):
            for field in proto:
                if (field.attrib['name'] == 'timestamp'):
                    outfile.write('Time Stamp%s' % field.attrib['value']+"\n")
        elif ((not short and proto.attrib['name'] != "frame") 
                or proto.attrib['name'] == "ip" or proto.attrib['name'] == "ospf"):
            print_proto(proto, outfile, short)

def print_packets(xml, outpath, short=False):
    with open(outpath, "w") as outfile:
        count = 0
        for packet in xml:
            count += 1
            outfile.write('PACKET RECIEVED NUMBER IN CAPTURE: %d' % (count)+"\n")
            print_packet(packet, outfile, short)
            outfile.write('~'+"\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pcap", help="Path to PCAP file", 
            required=True)
    parser.add_argument("-s", "--short", help="Only display OSPF header", 
            action="store_true")
    parser.add_argument("-o", "--out", help="Path to output file", 
            required=True)
    settings = parser.parse_args()

    xmlpath = gen_xml(settings.pcap)
    xml = parse_xml(xmlpath)
    print_packets(xml, settings.out, settings.short)

if __name__ == "__main__":
    main()
