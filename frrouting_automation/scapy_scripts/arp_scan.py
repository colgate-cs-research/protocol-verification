import scapy.all as scapy

def Arp(ip):
    print(ip)
    arp_r = scapy.ARP(pdst=ip)
    br = scapy.Ether(dst='ff:ff:ff:ff:ff:ff')
    request = br/arp_r
    answered, unanswered = scapy.srp(request, timeout=1)
    print('\tIP \t\t\t MAC')
    for i in answered:
        ip, mac = i[1].psrc, i[1].hwsrc
        print(ip, '\t\t' + mac)
    
            
Arp('172.17.0.0/24') # call the method