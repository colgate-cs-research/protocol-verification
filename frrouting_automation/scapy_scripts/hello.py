import scapy.all as scapy
from scapy_ospf import OSPF_Hdr, OSPF_Hello

packet = scapy.Ether(src='00:06:28:b9:85:31',dst='01:00:5e:00:00:05')


#packet.show()



packet = packet/scapy.Dot1Q(vlan=33)

#packet.show()
packet = packet/scapy.IP(src='192.16.2.2',dst='172.17.0.5')
packet = packet/OSPF_Hdr(src='192.16.2.2')
packet = packet/OSPF_Hello(router='172.17.2.2',backup='172.17.2.1',neighbor='172.17.2.1')
packet.show()
scapy.sendp(packet,loop=True,inter=0.1)