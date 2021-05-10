from scapy.contrib.ospf import *
from scapy.all import sendp,Ether,IP,ICMP,sniff,ls

# Send hello
packet = Ether()
packet = packet/IP(src='10.10.0.3',dst='224.0.0.5')
packet = packet/OSPF_Hdr(type=1,src='172.17.0.3')
packet = packet/OSPF_Hello(mask="255.255.255.248", options=0x02)
sendp(packet, loop=True, iter=10, iface="eth1")

# Receive hello
pkts = sniff(filter="proto 0x59", iface="eth1", count=1)
ospf = pkts[0][OSPF_Hdr]
ls(ospf)