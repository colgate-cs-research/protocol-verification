import re 
import json
import argparse
import os
import socket
import struct
import fileinput
from collections import defaultdict

Hello = "Hello"
DD = "Database Description"
LSR = "Link State Request"
LSU = "Link State Update"
LSA = "Link State Acknowledgment"
def peek_line(f):
    pos = f.tell()
    line = f.readline()
    f.seek(pos)
    return line

#extract messages for each router in triangle topology
def triangle(fname):
    inter = ""
    src_router = ""
    des_router = ""
    message = ""
    #source router + interface = destination router
    recv ={"172.17.0.210.10.0.2":"172.17.0.3","172.17.0.210.10.0.18":"172.17.0.4","172.17.0.310.10.0.3":"172.17.0.2","172.17.0.310.10.0.10":"172.17.0.4","172.17.0.410.10.0.11":"172.17.0.3","172.17.0.410.10.0.19":"172.17.0.2"}
    #r1 = 172.17.0.2
    r1 = []
    #r2 = 172.17.0.3
    r2 = []
    #r3 = 172.17.0.4
    r3 = []
    with open (fname) as file:
        while peek_line(file):
            line = file.readline()
            #timestamp of msg
            if "Time Stamp" in line:
                line = line.strip("\n")
                line = line.strip('\t')
                line = line.strip("Time Stamp")
                time = line
            #interface of message
            elif "Source: 10" in line:
                line = line.strip("\n")
                line = line.strip('\t')
                line = line.strip("Source: ")
                inter = line
            #type of message
            elif "Message Type" in line:
                line = line.strip("\n")
                line = line.strip('\t')
                line = line.strip("Message Type: ")
                message = line
            #source and dest router of message
            elif "Source OSPF Router" in line:
                line = line.strip("\n")
                line = line.strip('\t')
                line = line.strip("Source OSPF Router: ")
                src_router = line
                recv_key = src_router+inter
                des_router = recv[recv_key]
                #####can add more information/conditions to distinguish packets if want to
                #####below is excample
                if message == "LS Update (4)" or message == "LS Acknowledge (5)":
                    while peek_line(file):
                        line = file.readline()
                        if "~" not in line:
                            if "Sequence Number" in line:
                                SNline = line.strip("\n")
                                SNline = SNline.strip('\t')
                                SNline = SNline.strip("Sequence Number: ")
                                if "SN"+SNline not in message:
                                    message = message + "/SN"+SNline+"END"
                        else:
                            break
                #####
                #Assign messages to router sets with sent or receive at end of message
                if src_router == "172.17.0.2":
                    r1.append(message+"Send at "+time + " to " + des_router)
                elif src_router == "172.17.0.3":
                    r2.append(message+"Send at "+time + " to " + des_router)
                elif src_router == "172.17.0.4":
                    r3.append(message+"Send at "+time + " to " + des_router )
                
                if des_router == "172.17.0.2":
                    r1.append(message+"Receive at "+time + " from " +src_router)
                elif des_router == "172.17.0.3":
                    r2.append(message+"Receive at "+time + " from " +src_router)
                elif des_router == "172.17.0.4":
                    r3.append(message+"Receive at "+time + " from " +src_router)\

    return r1,r2,r3

def double(fname):
    inter = ""
    src_router = ""
    des_router = ""
    message = ""
    recv ={"172.17.0.210.10.0.2":"172.17.0.3","172.17.0.310.10.0.3":"172.17.0.2"}
    #r1 = 172.17.0.2
    r1 = []
    #r2 = 172.17.0.3
    r2 = []

    with open (fname) as file:
        while peek_line(file):
            line = file.readline()
            if "Time Stamp" in line:
                line = line.strip("\n")
                line = line.strip('\t')
                line = line.strip("Time Stamp")
                time = line
            elif "Source: 10" in line:
                line = line.strip("\n")
                line = line.strip('\t')
                line = line.strip("Source: ")
                inter = line
            #type of message
            elif "Message Type" in line:
                line = line.strip("\n")
                line = line.strip('\t')
                line = line.strip("Message Type: ")
                message = line
            #source and dest router of message
            elif "Source OSPF Router" in line:
                line = line.strip("\n")
                line = line.strip('\t')
                line = line.strip("Source OSPF Router: ")
                src_router = line
                recv_key = src_router+inter
                des_router = recv[recv_key]
                #####can add more information/conditions to distinguish packets if want to
                #####below is excample
                if message == "LS Update (4)" or message == "LS Acknowledge (5)":
                    while peek_line(file):
                        line = file.readline()
                        if "~" not in line:
                            if "Sequence Number" in line:
                                SNline = line.strip("\n")
                                SNline = SNline.strip('\t')
                                SNline = SNline.strip("Sequence Number: ")
                                if "SN"+SNline not in message:
                                    message = message + "/SN"+SNline+"END"
                        else:
                            break
                #####
                #Assign messages to router sets with sent or receive at end of message
                if src_router == "172.17.0.2":
                    r1.append(message+"Send at "+time + " to " + des_router)
                elif src_router == "172.17.0.3":
                    r2.append(message+"Send at "+time + " to " + des_router)
                
                if des_router == "172.17.0.2":
                    r1.append(message+"Receive at "+time + " from " +src_router)
                elif des_router == "172.17.0.3":
                    r2.append(message+"Receive at "+time + " from " +src_router)
    return r1, r2

def run(final_result):
    send_dict = defaultdict(set)
    recv_dict = defaultdict(set)
    for topologies in final_result:
        for logs in topologies:
            considered= []
            for k in range(len(logs)):
                if "Send" in logs[k]:
                    current_msg = logs[k]
                    send_time = re.search('Send at (.*) to ', current_msg)
                    send_time = float(send_time.group(1))
                    for l in range(k,len(logs)):
                        next_msg = logs[l]
                        if "Receive" in next_msg:
                            recv_time = re.search('Receive at (.*) from ', next_msg)
                            recv_time = float(recv_time.group(1))
                            if (recv_time - send_time)>6:
                                send_dict[current_msg.split("Send")[0]].add(next_msg.split("Receive")[0])
                                break
                else:
                    current_msg = logs[k]
                    recv_time = re.search('Receive at (.*) from ', current_msg)
                    recv_time = float(recv_time.group(1))
                    for l in range(k,len(logs)):
                        next_msg = logs[l]
                        if "Send" in next_msg:
                            send_time = re.search('Send at (.*) to ', next_msg)
                            send_time = float(send_time.group(1))
                            if (send_time - recv_time)>6:
                                recv_dict[current_msg.split("Receive")[0]].add(next_msg.split("Send")[0])
                                break

    with open ('output/causal.txt', 'w') as f:
        f.write("List of packets can be received given last sent packet type"+"\n")
        for key in recv_dict:
            f.write(key+"\n")
            f.write(str(recv_dict[key])+"\n")
            # ##### amount of packet can be added by uncommenting
            # p_amount = ""
            # for value in recv_dict[key]:
            #     pair = key + value
            #     p_amount = p_amount + str(recv_dict_counter[pair]) + "/"
            # f.write(p_amount+"\n")
            # f.write("\n")
            # #####
        f.write("###########################################################################################################################################################\n")
        f.write("List of packets can be send given last received packet type"+"\n")
        for key in send_dict:
            f.write(key+"\n")
            f.write(str(send_dict[key])+"\n")

    specific_causal_recv = defaultdict(set)
    specific_causal_send = defaultdict(set)
    with open ('output/specific_causal.txt','w') as f:
        for key in recv_dict:
            if "LS Update (4)" in key or "LS Acknowledge (5)" in key:
                for i in recv_dict[key]:
                    if "LS Update (4)" in i or "LS Acknowledge (5)" in i:
                        first_sn = re.findall(r'/SN(.*?)END', key,re.DOTALL)
                        second_sn = re.findall(r'/SN(.*?)END', i,re.DOTALL)
                        if max(first_sn) < min(second_sn):
                            specific_causal_recv[key.split("/")[0]].add(i.split("/")[0])
        for key in send_dict:
            if "LS Update (4)" in key or "LS Acknowledge (5)" in key:
                for i in recv_dict[key]:
                    if "LS Update (4)" in i or "LS Acknowledge (5)" in i:
                        first_sn = re.findall(r'/SN(.*?)END', key,re.DOTALL)
                        second_sn = re.findall(r'/SN(.*?)END', i,re.DOTALL)
                        if max(first_sn) < min(second_sn):
                            specific_causal_send[key.split("/")[0]].add(i.split("/")[0])
        f.write("List of packets with greater sn that can be received given last sent packet type"+"\n")
        for key in specific_causal_recv:
            f.write(key+"\n")
            f.write(str(specific_causal_recv[key])+"\n")
        f.write("###########################################################################################################################################################\n")
        f.write("List of packets with greater sn that can be send given last received packet type"+"\n")
        for key in specific_causal_send:
            f.write(key+"\n")
            f.write(str(specific_causal_send[key])+"\n")


def main():
    final_result = []
    ### delay is 3000 ms
    files3 = ['logs/l800_1_3.txt',
    'logs/l800_2_3.txt']

    for input_file3 in files3:
        final_result.append(triangle(input_file3))

    files2 = ['logs/l1000_1_2.txt']
    for input_file2 in files2:
        final_result.append(double(input_file2))

    #final_result.append(star('star_1000.txt'))
    #final_result.append(linear('linear_1000.txt'))

    run(final_result)
main()
#DB Description (2)
#LS Update (4)
#LS Request (3)
#LS Acknowledge (5)
#Hello Packet (1)
