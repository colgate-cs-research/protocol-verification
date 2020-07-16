import re 
import json
import argparse
import os
import socket
import struct
import fileinput
import pyshark

#peeks into the next line of the file
def peek_line(f):
    pos = f.tell()
    line = f.readline()
    f.seek(pos)
    return line
#print(file.read()) 

def NSM_messages(message,time,date):
    print("------------------"+message)
    pass

def ISM_messages(message,time,date):
    print("------------------"+message)
    pass
    
def package_verification(rule):
    iccontent = []
    areacontent = []
    router_id_name ={}
    interface_id_name ={}
    #create router name and id dictionary
    with open(rule) as f:
        rules = json.load(f)
    os.system("docker container ls > router_list.txt")
    with open ("router_list.txt") as file:
        file.readline()
        while peek_line(file):
            router_n = file.readline()
            router_n = router_n.split(" ")
            router = router_n[len(router_n)-1]
            router = router.replace("\n","")
            os.system("docker exec -it "+router+" vtysh -c 'show ip ospf' > temp.txt")
            with open ("temp.txt") as ipfile:
                while peek_line(ipfile):
                    spec = ipfile.readline()
                    if "Router ID" in spec:
                        spec = spec.replace("\n","")
                        spec = spec.split(": ")
                        router_id = spec[1]
                        router_id_name[router_id] = router
                        #fill interface id and corresponding name
            os.system("docker exec -it "+router+" vtysh -c 'show ip ospf neighbor' > temp.txt")
            with open ("temp.txt") as nfile:
                while peek_line(nfile):
                    ncontent = nfile.readline()
                    if ":" in ncontent:
                        ncontent = ncontent.split(" ")
                    for i in ncontent:
                        if ":" in i:
                            in_int = i.split(":")
                            if in_int[1] not in interface_id_name:
                                interface_id_name[in_int[1]] = in_int[0]
    #we iterate through every package in the sharkparospf file
    with open("sharkparospf.txt") as sharkfile:
        sharkcontent=sharkfile.read()
    sharkcontent = sharkcontent.split("~\n")
    for package in sharkcontent:
        package = package.split("\n")    
        package.pop(len(package)-1)
        if len(package)!=0:
            print("------------------ Examining "+ package[0].replace(" (this number is not part of the packet)",""))
            package.pop(0)
            package[1],package[4] =package[4],package[1]
            package[2],package[5] =package[5],package[2]
            for fieldnvalue in package:
                fieldnvalue = fieldnvalue.split(": ")
                field = fieldnvalue[0]
                value = fieldnvalue[1]
                if field == "srcrouter":
                    srcrouter_id= value
                    print("Source Router is " + srcrouter_id)
                if field == "hello_active_neighbor":
                    hello_active_neighbor_id= value
                    print("Destination Router is "+ hello_active_neighbor_id)
                if field =="incoming_interface":
                    incoming_interface = value
                    print("Incoming interface is "+ incoming_interface)
                    arg = "show ip ospf interface " + interface_id_name[incoming_interface]
                    os.system("docker exec -it " + router_id_name[srcrouter_id] +" vtysh -c '"+arg+"' > temp.txt")
                    with open("temp.txt") as icfile:
                        iccontent = icfile.read()
                        iccontent = iccontent.replace("\n",",")
                        iccontent = iccontent.split(",")
                        for i in range(len(iccontent)):
                            if iccontent[i] != "":
                                while iccontent[i][0] == " " and iccontent[i][0]!="":
                                    iccontent[i] = iccontent[i].replace(" ", "", 1)
                if field == "area_id":
                    arg = "show ip ospf"
                    os.system("docker exec -it " + router_id_name[srcrouter_id] +" vtysh -c '"+arg+"' > temp.txt")
                    with open("temp.txt") as areafile:
                        areacontent = areafile.read()
                        areacontent = areacontent.split("\n")
                        for i in range(len(areacontent)):
                            if areacontent[i] != "":
                                while areacontent[i][0] == " " and areacontent[i][0]!="":
                                    areacontent[i] = areacontent[i].replace(" ", "", 1)
                #we go in to the ospf_rule.py file and if a field matchs a file in the package:                      
                #hello packet rules
                hello_packet_ver(rules,field,iccontent,value)
                #Packer header rules
                ospf_packet_header_ver(rules,field,iccontent,value,areacontent)
                
def hello_packet_ver(rules,field,iccontent,value):
    for i in rules["OSPF_rules"][1]["Packets"][2]["Hello"]:
        if i["Field"].count(field)>0:
            print("**Hello Packet Rule Found: Verifying Field " + i["Field"])
            if field == "hello_hello_interval":
                checking_hello_interval = iccontent_split(iccontent,21," ", 1, "s", "replace")
                print ("Packet Hello Interval == "+value +"s and Incoming Interface Hello Interval == "+checking_hello_interval+"s")
                checking_value_res(value, checking_hello_interval,"Packet Hello Interval field","Incoming Interface Hello Interval")
            if field == "hello_router_dead_interval":
                checking_dead_interval = iccontent_split(iccontent,22," ", 1, "s", "replace")
                print ("Packet Dead Interval == "+value +"s and Incoming Interface Dead Interval == "+checking_dead_interval+"s")
                checking_value_res(value, checking_dead_interval,"Packet Dead Interval field","Incoming Interface Dead Interval")
            if field == "hello_network_mask":
                checking_network_mask_m = iccontent_split(iccontent, 7, " ", 2, "/", "split")
                checking_network_mask = checking_network_mask_m[1]
                checking_network_mask = socket.inet_ntoa(struct.pack(">I", (0xffffffff << (32 - int(checking_network_mask))) & 0xffffffff))
                print ("Packet Network Mask == "+value +" and Incoming Interface Network Mask == "+checking_network_mask)
                checking_value_res(value, checking_network_mask,"Packet Network Mask field","Incoming Interface Network Mask")

def ospf_packet_header_ver(rules,field,iccontent,value,areacontent):
    for i in rules["OSPF_rules"][1]["Packets"][1]["OSPF packet header"]:
        if i["Field"].count(field)>0:
            print("**Packer Header Rule Found: Verifying Field " + i["Field"])
            if field == "area_id":
                checking_area_id = iccontent_split(iccontent, 9, " ", 1, "null", "none")
                checking_value_res(value, checking_area_id,"Packet Area ID field","Incoming Interface Area ID")
            if field == "version_number":
                checking_value_res(value, "2","Packet Version Number field","2")
            if field == "incoming_interface":
                checking_state = iccontent_split(iccontent, 15, " ", 1, "null", "none")
                checking_int_mgm_n = iccontent[19]
                if checking_state == "Backup" or checking_state == "DR":
                    if checking_int_mgm_n.count("OSPFDesignatedRouters"):
                        print("Rule Followed: Incoming Interface with OSPFDesignatedRouters is with state DR or Backup")
            if field == "auth_type":
                checking_auth_type_n = areacontent[22]
                if checking_auth_type_n == "Area has no authentication":
                    if value == "0":
                        print("Rule Followed: Packet Auth_type field specified as Null as associated area auth_type")
            
            ######modification needed if authen type set to value other than null for area (auth set for area)

def iccontent_split(iccontent, icind, s1, ind, s2, last_action):
    checking_interval_n = iccontent[icind]
    checking_interval_n = checking_interval_n.split(s1)
    checking_interval = checking_interval_n[ind]
    if last_action == "replace":
        checking_interval =checking_interval.replace(s2,"")
    elif last_action == "split":
        checking_interval =checking_interval.split(s2)
    elif last_action == "none":
        return checking_interval
    return checking_interval

def checking_value_res(value, checking_value,first,second):
    if value == checking_value:
        print("Rule Followed: "+first+" matches "+second)
    else:
        print("*****Notfication (Error): Rule not followed")

#verifies and categorizes messages
def message_categorization(file, rule):
    ISM_states = ["Down","Loopback","Waiting","Point-to-point","DR Other","Backup","DR"]
    NSM_states = ["Down","Attempt","Init","2-Way","ExStart","Exchange","Loading","Full"]
    ISM_events = ["WaitTimer","NeighborChange","BackupSeen","InterfaceUp","InterfaceDown","LoopInd","UnloopInd"]
    NSM_events = ["Start","PacketReceived","NegotiationDone","ExchangeDone","Loading Done","AdjOK?","SeqNumberMismatch","BadLSReq","KillNbr","LLDown","InactivityTimer","1-WayReceived","2-WayReceived"]
    #iterates through each line in the given file
    with open(rule) as f:
        rules = json.load(f)
    #informational setting logged ism
    while(peek_line(file)):
        curr_line= file.readline().rstrip()

        #Checks string being read is a log message
        if(re.search("\\d{4}/\\d{2}/\\d{2} \\d\\d:\\d\\d:\\d\\d [OB][SG][P][F]?:", curr_line)!=None):
            
            #extracts the message
            message=re.split("\\d{4}/\\d{2}/\\d{2} \\d\\d:\\d\\d:\\d\\d [OB][SG][P][F]?:",curr_line)[1]
            #extracts the time and date
            time = re.search("\\d\\d:\\d\\d:\\d\\d", curr_line).group()
            date = re.search("\\d{4}/\\d{2}/\\d{2}", curr_line).group()
        #Checks for NSM messages
            msg_check(rules,file,message,time,date,"NSM",NSM_states,ISM_states,NSM_events,ISM_events)
        #Checks for ISM messages
            msg_check(rules,file,message,time,date,"ISM",NSM_states,ISM_states,NSM_events,ISM_events)

def msg_check(rules,file,message,time,date,msg_type,NSM_states,ISM_states,NSM_events,ISM_events):
    if(re.search(msg_type, message)!=None):
        if msg_type == "ISM":
            ISM_messages(message,time,date)
            list_states = ISM_states
            list_events = ISM_events
        elif msg_type =="NSM":
            NSM_messages(message,time,date)
            list_states = NSM_states
            list_events = NSM_events
        splited_m = message.split()
        if (list_states.count(splited_m[1])>0):
            current_state = splited_m[1]
            print("Current state is: "+current_state)
            event = splited_m[2].replace('(','')
            event = event.replace(')','')
            print("Event is: "+event)
            rule_found = 0
            if msg_type == "ISM":
                rule_found = event_ver(rules,current_state,event,rule_found,file,ISM_states,NSM_states,"ISM")
            elif msg_type == "NSM":
                rule_found = event_ver(rules,current_state,event,rule_found,file,ISM_states,NSM_states,"NSM")
            if rule_found == 0:
                if list_events.count(event)==0:
                    print("*****Notfication (Error): Event is not found")
                else:
                    print("*****Notfication (Error): Rule Not Found")
        else:
            if (splited_m[1] != "State") and msg_type == "NSM":
                    print("*****Notfication (Error): State "+splited_m[1]+ " is not found")

def event_ver(rules,current_state,event,rule_found,file,ISM_states,NSM_states,event_type):
    ind = 0
    list_states = []
    if event_type == "ISM":
        ind = 0
        list_states = ISM_states
        event_rules = "Informational_Setting_Logged"
    elif event_type =="NSM":
        list_states = NSM_states
        ind = 1
        event_rules = "Neighbor_State_Machine"
    for i in rules["OSPF_rules"][0]["Events"][ind][event_rules]:
        if i["State(s)"].count(current_state)>0 and i["Event"]==event:
            print("Rule Found")
            rule_found =1
            if rule_found == 1:
                print("Expected state(s):")
                print(i["New_state"])
                next_message = "none"
                while(peek_line(file)):
                    next_line= peek_line(file).rstrip()
                    #Checks next string being read is a log message
                    if(re.search("\\d{4}/\\d{2}/\\d{2} \\d\\d:\\d\\d:\\d\\d [OB][SG][P][F]?:", next_line)!=None):
                        #extracts the message
                        next_message=re.split("\\d{4}/\\d{2}/\\d{2} \\d\\d:\\d\\d:\\d\\d [OB][SG][P][F]?:",next_line)[1]
                        break
                if next_message!="none":
                    if type(next_message)!= list:
                        next_message = next_message.split()
                        next_state = next_message[1]
                        if i["New_state"].count(current_state)>0:
                            print("Rule Followed: Old State == New State")
                        elif next_state == "State":
                            if list_states.count(next_message[5])==0:
                                print("*****Notfication (Error): New state in following message is not found")
                            elif list_states.count(next_message[3])==0:
                                print("*****Notfication (Error): Current state in following message is not found")
                            elif next_message[3] != current_state:
                                print("*****Notfication (Error): Inconsistent current states")
                            else:
                                if event_type == "ISM":
                                    if next_message[3]==current_state and i["New_state"].count(next_message[5]) > 0:
                                        print("Rule Followed: Old state transits to new state as indicated in the following message")
                                elif event_type == "NSM":
                                    next_event = next_message[6]
                                    next_event = next_event.replace("(","")
                                    next_event = next_event.replace(")","")
                                    if next_message[3]==current_state and i["New_state"].count(next_message[5]) > 0 and next_event == event:
                                        print("Rule Followed: Old state transits to new state as indicated in the following message")
                                    elif next_message[3]==current_state and i["New_state"].count(next_message[5]) > 0 and next_event != event:
                                        print("*****Notfication (Error): Inconsistent events")
                        else:
                            print("*****Notfication (Error): Rule not followed")
    return rule_found
def shark(packet_type):
    cap = pyshark.FileCapture('tcpdump.pcap')
    p = open('parsed'+packet_type+'.txt', 'w')
    fc = open('fullcapture.txt', 'w')
    pt = {'Hello': '1', 'DB': '2', 'LSR': '3', 'LSU': '4', 'LSA' : '5', 'ALL' : '6'}
    ptype = pt[packet_type]
    if ptype == '1':
        spec = open('sharkparospf.txt', 'w')
    print(cap, file=fc)
    count = 0

    for pkt in cap:
        print(pkt, file=fc)
        print('~', file =fc)
        count += 1
        if 'ospf' in pkt:
            if (pkt.ospf.msg == ptype) or (ptype == '6'):
                print('PACKET RECIEVED NUMBER IN CAPTURE: ' +str(count), file=p)
                print(pkt, file=p)
                print('~', file=p)
                if(ptype == '1'):
                    print('PACKET RECIEVED NUMBER IN CAPTURE: ' + str(count), file=spec)
                    print('srcrouter: ' + pkt.ospf.srcrouter, file=spec)
                    print('hello_network_mask: ' + pkt.ospf.hello_network_mask, file=spec)
                    print('hello_hello_interval: ' + pkt.ospf.hello_hello_interval, file=spec)
                    print('hello_router_dead_interval: ' + pkt.ospf.hello_router_dead_interval, file=spec)
                    print('hello_active_neighbor: ' + pkt.ospf.hello_active_neighbor, file=spec)
                    print('incoming_interface: ' + pkt.ip.src, file=spec)
                    print('version_number: ' + pkt.ospf.version, file=spec)
                    print('area_id: ' + pkt.ospf.area_id, file=spec)
                    print('auth_type: ' + pkt.ospf.auth_type, file=spec)
                    print('auth_none: ' + pkt.ospf.auth_none, file=spec)
                    print('~', file=spec)
    p.close()
    fc.close()
    if(ptype == '1'):
        spec.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--rule", help="Path to JSON rule file", required=True)
    parser.add_argument("-l", "--log", help="Path to log file", required=True)
    parser.add_argument("-p", "--packet", choices=['Hello', 'DB', 'LSR', 'LSU', 'LSA', 'ALL'], help="Option to choose OSPF packet type to collect: Hello, DB, LSR, LSU, LSA, or ALL", required=False)
    settings = parser.parse_args()
    
    #settings for wireshark
    if (settings.packet in ['Hello', 'DB', 'LSR', 'LSU', 'LSA', 'ALL']):
        shark(settings.packet)

    file = open(settings.log, "r")
    message_categorization(file,settings.rule)
    #package_verification(settings.rule)

main()
