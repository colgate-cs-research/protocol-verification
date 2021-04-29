import re 
import json
import argparse
import os
import socket
import struct
import fileinput
from collections import defaultdict
from collections import Counter

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
    recv ={"10.10.0.210.10.0.2":"10.10.0.3","10.10.0.210.10.0.18":"10.10.0.11","10.10.0.310.10.0.3":"10.10.0.2","10.10.0.310.10.0.10":"10.10.0.11","10.10.0.1110.10.0.11":"10.10.0.3","10.10.0.1110.10.0.19":"10.10.0.2"}
    #r1 = 10.10.0.2
    r1 = []
    #r2 = 10.10.0.3
    r2 = []
    #r3 = 10.10.0.11
    r3 = []

    with open (fname) as file:
        while peek_line(file):
            line = file.readline()
            #interface of message
            if "Source: 10" in line:
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
                # #####can add more information/conditions to distinguish packets if want to
                # #####below is excample
                # if message == "LS Update (4)":
                #     while peek_line(file):
                #         line = file.readline()
                #         if "~" not in line:
                #             if "LS Type" in line:
                #                 LSTline = line.strip("\n")
                #                 LSTline = LSTline.strip('\t')
                #                 LSTline = LSTline.strip("LS Type: ")
                #             elif "Link State ID: " in line:
                #                 LSIDline = line.strip("\n")
                #                 LSIDline = LSIDline.strip('\t')
                #                 LSIDline = LSIDline.strip("Link State ID: ")
                #             elif "Advertising Router" in line:
                #                 ARline = line.strip("\n")
                #                 ARline = ARline.strip('\t')
                #                 ARline = ARline.strip("Advertising Router: ")
                #             elif "Sequence Number" in line:
                #                 SNline = line.strip("\n")
                #                 SNline = SNline.strip('\t')
                #                 SNline = SNline.strip("Sequence Number: ")
                #                 if "/AR"+ARline + "SN"+SNline not in message:
                #                     message = message + "/LST"+LSTline+ "LSID"+LSIDline+ "AR"+ARline + "SN"+SNline
                #         else:
                #             break
                # #####
                #Assign messages to router sets with sent or receive at end of message
                if src_router == "10.10.0.2":
                    r1.append(message+"Send")
                elif src_router == "10.10.0.3":
                    r2.append(message+"Send")
                elif src_router == "10.10.0.11":
                    r3.append(message+"Send")
                
                if des_router == "10.10.0.2":
                    r1.append(message+"Receive")
                elif des_router == "10.10.0.3":
                    r2.append(message+"Receive")
                elif des_router == "10.10.0.11":
                    r3.append(message+"Receive")
    return r1,r2,r3

#extract messages for each router in double topology
def double(fname):
    inter = ""
    src_router = ""
    des_router = ""
    message = ""
    #source router + interface = destination router
    recv ={"10.10.0.210.10.0.2":"10.10.0.3","10.10.0.310.10.0.3":"10.10.0.2"}
    #r7 = 10.10.0.2
    r7 = []
    #r8 = 10.10.0.3
    r8 = []

    with open (fname) as file:
        while peek_line(file):
            line = file.readline()
            #interface of message
            if "Source: 10" in line:
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
                # #####can add more information/conditions to distinguish packets if want to
                # #####below is excample
                # if message == "LS Update (4)":
                #     while peek_line(file):
                #         line = file.readline()
                #         if "~" not in line:
                #             if "LS Type" in line:
                #                 LSTline = line.strip("\n")
                #                 LSTline = LSTline.strip('\t')
                #                 LSTline = LSTline.strip("LS Type: ")
                #             elif "Link State ID: " in line:
                #                 LSIDline = line.strip("\n")
                #                 LSIDline = LSIDline.strip('\t')
                #                 LSIDline = LSIDline.strip("Link State ID: ")
                #             elif "Advertising Router" in line:
                #                 ARline = line.strip("\n")
                #                 ARline = ARline.strip('\t')
                #                 ARline = ARline.strip("Advertising Router: ")
                #             elif "Sequence Number" in line:
                #                 SNline = line.strip("\n")
                #                 SNline = SNline.strip('\t')
                #                 SNline = SNline.strip("Sequence Number: ")
                #                 if "/AR"+ARline + "SN"+SNline not in message:
                #                     message = message + "/LST"+LSTline+ "LSID"+LSIDline+ "AR"+ARline + "SN"+SNline
                #         else:
                #             break
                # #####
                #Assign messages to router sets with sent or receive at end of message
                if src_router == "10.10.0.2":
                    r7.append(message+"Send")
                elif src_router == "10.10.0.3":
                    r8.append(message+"Send")
                
                if des_router == "10.10.0.2":
                    r7.append(message+"Receive")
                elif des_router == "10.10.0.3":
                    r8.append(message+"Receive")
    return r7,r8

#computing causal sets
def run(final_result):
    send_dict = defaultdict(set)
    recv_dict = defaultdict(set)
    send_dict_counter = Counter()
    recv_dict_counter = Counter()
    #iterate through all topologies
    for i in range(len(final_result)):
        #iterate through all router sets
        for j in range(len(final_result[i])):
            r = final_result[i][j]
            last_send= ""
            #iterate through all pakcets in router set
            #compute the causal_recive(i,s) set
            for msg in r:
                if r.index(msg) == 0:
                    if "Send" in msg:
                        last_send = msg
                else:
                    if "Receive" in msg:
                        recv_dict[last_send.strip("Send")].add(msg.strip("Receive"))
                        recv_dict_counter[last_send.strip("Send")+msg.strip("Receive")]+=1
                    elif "Send" in msg:
                        last_send = msg
            last_receive = ""
            #compute the causal_send(i,r) set
            for msg in r:
                if r.index(msg) == 0:
                    if "Receive" in msg:
                        last_receive = msg
                else:
                    if "Send" in msg:
                        send_dict[last_receive.strip("Receive")].add(msg.strip("Send"))
                        send_dict_counter[last_receive.strip("Receive")+msg.strip("Send")]+=1
                    elif "Receive" in msg:
                        last_receive = msg
    #union and output all sets
    with open ('extraction_bird_output.txt', 'w') as f:
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
            # ##### amount of packets can be added by uncommenting
            # p_amount = ""
            # for value in send_dict[key]:
            #     pair = key + value
            #     p_amount = p_amount + str(send_dict_counter[pair]) + "/"
            # f.write(p_amount+"\n")
            # f.write("\n")
            # #####


def main():
    final_result = []
    files3 = ['b800_1_3.txt','b800_2_3.txt','b800_3_3.txt','b800_4_3.txt',
    'b800_5_3.txt','b800_6_3.txt','b800_7_3.txt','b800_8_3.txt',
    'b800_9_3.txt','b800_10_3.txt','b800_11_3.txt','b800_12_3.txt',
    'b800_13_3.txt','b800_14_3.txt','b800_15_3.txt']
    files2 = ["b1000_1_2.txt","b1000_2_2.txt","b1000_3_2.txt","b1000_4_2.txt",
    "b1000_5_2.txt","b1000_6_2.txt","b1000_7_2.txt","b1000_8_2.txt","b1000_9_2.txt",
    "b1000_10_2.txt"]
    for input_file3 in files3:
        final_result.append(triangle(input_file3))
    for input_file2 in files2:
        final_result.append(double(input_file2))
    run(final_result)

main()
#DB Description (2)
#LS Update (4)
#LS Request (3)
#LS Acknowledge (5)
#Hello Packet (1)
