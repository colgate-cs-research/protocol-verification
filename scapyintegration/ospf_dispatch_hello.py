from scapy.contrib.ospf import *
from scapy.all import sendp,Ether,IP,sniff,ls

neighbors = []

# Handle a received packet
def handle_ospf(packet):
    ospf = packet[OSPF_Hdr]
    ls(ospf)
    if ospf.type == 1:
        hello = packet[OSPF_Hello]
        if ospf.src not in neighbors:
            neighbors.append(ospf.src)

        # Send hello
        packet = Ether()
        packet = packet/IP(src='10.10.0.3',dst='224.0.0.5')
        packet = packet/OSPF_Hdr(type=1,src='172.17.0.3')
        packet = packet/OSPF_Hello(mask="255.255.255.248", options=0x02, neighbors=neighbors)
        sendp(packet, iface="eth1")

# Receive OSPF packets
pkts = sniff(prn=handle_ospf, filter="proto 0x59", iface="eth1", count=10)