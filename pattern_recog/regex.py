import re 
import json
import argparse
import os
import socket
import struct

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
    os.system("cp ~/protocol-verification/frrouting_automation/router_id_name.txt ~/protocol-verification/pattern_recog")
    os.system("cp ~/protocol-verification/frrouting_automation/sharkparospf.txt ~/protocol-verification/pattern_recog")
    router_id_name ={}
    interface_id_name ={}
    with open(rule) as f:
        rules = json.load(f)
    with open ("router_id_name.txt") as file:
        while peek_line(file):
            router = file.readline()
            router = router.replace("\n","")
            os.system("docker exec -it "+router+" vtysh -c 'show ip ospf' > ipcontent.txt")
            with open ("ipcontent.txt") as ipfile:
                while peek_line(ipfile):
                    spec = ipfile.readline()
                    if "Router ID" in spec:
                        spec = spec.replace("\n","")
                        spec = spec.split(": ")
                        router_id = spec[1]
                        router_id_name[router_id] = router
            os.system("docker exec -it "+router+" vtysh -c 'show ip ospf neighbor' > ipneighbor.txt")
            with open ("ipneighbor.txt") as nfile:
                while peek_line(nfile):
                    ncontent = nfile.readline()
                    if ":" in ncontent:
                        ncontent = ncontent.split(" ")
                    for i in ncontent:
                        if ":" in i:
                            in_int = i.split(":")
                            if in_int[1] not in interface_id_name:
                                interface_id_name[in_int[1]] = in_int[0]
    print(interface_id_name)
    print(router_id_name)

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
                    os.system("docker exec -it " + router_id_name[srcrouter_id] +" vtysh -c '"+arg+"' > interfacecontent.txt")
                    with open("interfacecontent.txt") as icfile:
                        iccontent = icfile.read()
                        iccontent = iccontent.replace("\n",",")
                        iccontent = iccontent.split(",")
                        for i in range(len(iccontent)):
                            if iccontent[i] != "":
                                while iccontent[i][0] == " " and iccontent[i][0]!="":
                                    iccontent[i] = iccontent[i].replace(" ", "", 1)
                for i in rules["OSPF_rules"][1]["Packets"][2]["Hello"]:
                    if i["Field"].count(field)>0:
                        print("Rule Found: Verifying Field " + i["Field"])
                        if field == "hello_hello_interval":
                            checking_hello_interval_n = iccontent[21]
                            checking_hello_interval_n = checking_hello_interval_n.split(" ")
                            checking_hello_interval = checking_hello_interval_n[1]
                            checking_hello_interval =checking_hello_interval.replace("s","")
                            print ("Packet Hello Interval == "+value +"s and Incoming Interface Hello Interval == "+checking_hello_interval+"s")
                            if value == checking_hello_interval:
                                print("Rule Followed: Packet Hello Interval field matches Incoming Interface Hello Interval")
                            else:
                                print("*****Notfication (Error): Rule not followed")
                        if field == "hello_router_dead_interval":
                            checking_dead_interval_n = iccontent[22]
                            checking_dead_interval_n = checking_dead_interval_n.split(" ")
                            checking_dead_interval = checking_dead_interval_n[1]
                            checking_dead_interval =checking_dead_interval.replace("s","")
                            print ("Packet Dead Interval == "+value +"s and Incoming Interface Dead Interval == "+checking_dead_interval+"s")
                            if value == checking_dead_interval:
                                print("Rule Followed: Packet Dead Interval field matches Incoming Interface Dead Interval")
                            else:
                                print("*****Notfication (Error): Rule not followed")
                        if field == "hello_network_mask":
                            checking_network_mask_n = iccontent[7]
                            checking_network_mask_n = checking_network_mask_n.split(" ")
                            checking_network_mask_m = checking_network_mask_n[2]
                            checking_network_mask_m =checking_network_mask_m.split("/")
                            checking_network_mask = checking_network_mask_m[1]
                            checking_network_mask = socket.inet_ntoa(struct.pack(">I", (0xffffffff << (32 - int(checking_network_mask))) & 0xffffffff))
                            print ("Packet Network Mask == "+value +" and Incoming Interface Network Mask == "+checking_network_mask)
                            if value == checking_network_mask:
                                print("Rule Followed: Packet Network Mask field matches Incoming Interface Network Mask")
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
    #print(rules["OSPF_rules"][0]["Events"][0]["Informational_Setting_Logged"][1]["State(s)"][1])
    #for each in rules["OSPF_rules"][0]["Events"][0]["Informational_Setting_Logged"]:
        #print(each["State(s)"])
    #nsm
    #print(rules["OSPF_rules"][0]["Events"][1])

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
            if(re.search("NSM", message)!=None): 
                NSM_messages(message,time,date)
                splited_m = message.split()
                if (NSM_states.count(splited_m[1])>0):
                    current_state = splited_m[1]
                    print("Current state is: "+current_state)
                    event = splited_m[2].replace('(','')
                    event = event.replace(')','')
                    print("Event is: "+event)
                    rule_found = 0
                    for i in rules["OSPF_rules"][0]["Events"][1]["Neighbor_State_Machine"]:
                        if i["State(s)"].count(current_state)>0 and i["Event"]==event:
                            print("Rule Found")
                            rule_found =1
                            if rule_found == 1:
                                print("Expected state(s):")
                                print(i["New_state"])
                                while(peek_line(file)):
                                    next_line= peek_line(file).rstrip()
                                    #Checks next string being read is a log message
                                    if(re.search("\\d{4}/\\d{2}/\\d{2} \\d\\d:\\d\\d:\\d\\d [OB][SG][P][F]?:", next_line)!=None):
                                        #extracts the message
                                        next_message=re.split("\\d{4}/\\d{2}/\\d{2} \\d\\d:\\d\\d:\\d\\d [OB][SG][P][F]?:",next_line)[1]
                                        break
                                if type(next_message)!= list:
                                    next_message = next_message.split()
                                    next_state = next_message[1]
                                    if i["New_state"].count(current_state)>0:
                                        print("Rule Followed: Old State == New State")
                                    elif next_state == "State":
                                        next_event = next_message[6]
                                        next_event = next_event.replace("(","")
                                        next_event = next_event.replace(")","")
                                        if NSM_states.count(next_message[5])==0:
                                            print("*****Notfication (Error): New state in following message is not found")
                                        elif NSM_states.count(next_message[3])==0:
                                            print("*****Notfication (Error): Current state in following message is not found")
                                        elif next_message[3] != current_state:
                                            print("*****Notfication (Error): Inconsistent current states")
                                        elif next_message[3]==current_state and i["New_state"].count(next_message[5]) > 0 and next_event == event:
                                            print("Rule Followed: Old state transits to new state as indicated in the following message")
                                        elif next_message[3]==current_state and i["New_state"].count(next_message[5]) > 0 and next_event != event:
                                            print("*****Notfication (Error): Inconsistent events")
                                    else:
                                        print("*****Notfication (Error): Rule not followed")
                    if rule_found == 0:
                        if NSM_events.count(event)==0:
                            print("*****Notfication (Error): Event is not found")
                        else:
                            print("*****Notfication (Error): Rule Not Found")
                elif (splited_m[1] != "State"):
                    print("*****Notfication (Error): State "+splited_m[1]+ " is not found")
            #Checks for ISM messages
            if(re.search("ISM", message)!=None):
                ISM_messages(message,time,date)
                splited_m = message.split()
                if (ISM_states.count(splited_m[1])>0):
                    current_state = splited_m[1]
                    print("Current state is: "+current_state)
                    event = splited_m[2].replace('(','')
                    event = event.replace(')','')
                    print("Event is: "+event)
                    rule_found = 0
                    for i in rules["OSPF_rules"][0]["Events"][0]["Informational_Setting_Logged"]:
                        if i["State(s)"].count(current_state)>0 and i["Event"]==event:
                            print("Rule Found")
                            rule_found =1
                            if rule_found == 1:
                                print("Expected state(s):")
                                print(i["New_state"])
                                while(peek_line(file)):
                                    next_line= peek_line(file).rstrip()
                                    #Checks next string being read is a log message
                                    if(re.search("\\d{4}/\\d{2}/\\d{2} \\d\\d:\\d\\d:\\d\\d [OB][SG][P][F]?:", next_line)!=None):
                                        #extracts the message
                                        next_message=re.split("\\d{4}/\\d{2}/\\d{2} \\d\\d:\\d\\d:\\d\\d [OB][SG][P][F]?:",next_line)[1]
                                        break
                                if type(next_message)!= list:
                                    next_message = next_message.split()
                                    next_state = next_message[1]
                                    if i["New_state"].count(current_state)>0:
                                        print("Rule Followed: Old State == New State")
                                    elif next_state == "State":
                                        if ISM_states.count(next_message[5])==0:
                                            print("*****Notfication (Error): New state in following message is not found")
                                        elif ISM_states.count(next_message[3])==0:
                                            print("*****Notfication (Error): Current state in following message is not found")
                                        elif next_message[3] != current_state:
                                            print("*****Notfication (Error): Inconsistent current states")
                                        elif next_message[3]==current_state and i["New_state"].count(next_message[5]) > 0:
                                            print("Rule Followed: Old state transits to new state as indicated in the following message")
                                    else:
                                        print("*****Notfication (Error): Rule not followed")

                    if rule_found == 0:
                        if ISM_events.count(event)==0:
                            print("*****Notfication (Error): Event is not found")
                        else:
                            print("*****Notfication (Error): Rule Not Found")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--rule", help="Path to JSON rule file", required=True)
    parser.add_argument("-l", "--log", help="Path to log file", required=True)
    settings = parser.parse_args()
    file = open(settings.log, "r")
    message_categorization(file,settings.rule)
    package_verification(settings.rule)

main()
