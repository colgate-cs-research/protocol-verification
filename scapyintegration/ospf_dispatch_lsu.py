from scapy.contrib.ospf import *
from scapy.all import sendp,Ether,IP,sniff,ls,get_if_addr

last_update = None

# Handle a received packet
def handle_ospf(packet):
    print(packet.summary())
    ospf = packet[OSPF_Hdr]
    # LS update
    if ospf.type == 4:
        update = packet[OSPF_LSUpd]
        for lsa in update.lsalist:
            print("  %d %d" % (lsa.type, lsa.seq))
            # Router LSA
            if lsa.type == 1:
                print("    %s" % (lsa.linklist))
            # Network LSA
            elif lsa.type == 2:
                print("    %s %s %s" % (lsa. id, lsa.mask, lsa.routerlist))
        last_update = update
    # LS ACK
    elif ospf.type == 5:
        ack = packet[OSPF_LSAck]
        for lsa in ack.lsaheaders:
            print("  %d %d" % (lsa.type, lsa.seq))

# Receive OSPF packets
my_ip = get_if_addr("eth1")
pkts = sniff(prn=handle_ospf, filter="proto 0x59", iface="eth1", count=100)