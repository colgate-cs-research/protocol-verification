import re 
import json
import argparse
import os
import socket
import struct
import fileinput
from collections import defaultdict
from collections import Counter
from pydtmc import (
    MarkovChain,
    plot_graph
)

from pytest import (
    mark
)
import matplotlib.pyplot as plt

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
    #r1 = 172.17.0.3
    r1 = []
    #r2 = 172.17.0.4
    r2 = []
    #r3 = 172.17.0.4
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
                #####can add more information/conditions to distinguish packets if want to

                #add lsu fields
                if message == "LS Update (4)":
                    while peek_line(file):
                        line = file.readline()
                        if "~" not in line:
                            if "LS Type" in line:
                                LSTline = line.strip("\n")
                                LSTline = LSTline.strip('\t')
                                LSTline = LSTline.strip("LS Type: ")
                            elif "Link State ID: " in line:
                                LSIDline = line.strip("\n")
                                LSIDline = LSIDline.strip('\t')
                                LSIDline = LSIDline.strip("Link State ID: ")
                            elif "Advertising Router" in line:
                                ARline = line.strip("\n")
                                ARline = ARline.strip('\t')
                                ARline = ARline.strip("Advertising Router: ")
                            elif "Sequence Number" in line:
                                SNline = line.strip("\n")
                                SNline = SNline.strip('\t')
                                SNline = SNline.strip("Sequence Number: ")
                            elif "Checksum" in line and "Length" in peek_line(file):
                                CSline = line.strip("\n")
                                CSline = CSline.strip('\t')
                                CSline = CSline.strip("Checksum: ")
                                if "/AR"+ARline + "SN"+SNline not in message:
                                    message = message + "/LST"+LSTline+ "LSID"+LSIDline+ "AR"+ARline + "SN"+SNline+"CS"+CSline+"/"
                        else:
                            break

                #add ls ack fields
                elif message == "LS Acknowledge (5)":
                    while peek_line(file):
                        line = file.readline()
                        if "~" not in line:
                            if "LS Type" in line:
                                LSTline = line.strip("\n")
                                LSTline = LSTline.strip('\t')
                                LSTline = LSTline.strip("LS Type: ")
                            elif "Link State ID: " in line:
                                LSIDline = line.strip("\n")
                                LSIDline = LSIDline.strip('\t')
                                LSIDline = LSIDline.strip("Link State ID: ")
                            elif "Advertising Router" in line:
                                ARline = line.strip("\n")
                                ARline = ARline.strip('\t')
                                ARline = ARline.strip("Advertising Router: ")
                            elif "Sequence Number" in line:
                                SNline = line.strip("\n")
                                SNline = SNline.strip('\t')
                                SNline = SNline.strip("Sequence Number: ")
                            elif "Checksum" in line and "Length" in peek_line(file):
                                CSline = line.strip("\n")
                                CSline = CSline.strip('\t')
                                CSline = CSline.strip("Checksum: ")
                                if "/AR"+ARline + "SN"+SNline not in message:
                                    message = message + "/LST"+LSTline+ "LSID"+LSIDline+ "AR"+ARline + "SN"+SNline+"CS"+CSline+"/"
                        else:
                            break
                #####
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
    #r7 = 172.17.0.3
    r7 = []
    #r8 = 172.17.0.4
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

                #####can add more information/conditions to distinguish packets if want to

                #add lsu fields
                if message == "LS Update (4)":
                    while peek_line(file):
                        line = file.readline()
                        if "~" not in line:
                            if "LS Type" in line:
                                LSTline = line.strip("\n")
                                LSTline = LSTline.strip('\t')
                                LSTline = LSTline.strip("LS Type: ")
                            elif "Link State ID: " in line:
                                LSIDline = line.strip("\n")
                                LSIDline = LSIDline.strip('\t')
                                LSIDline = LSIDline.strip("Link State ID: ")
                            elif "Advertising Router" in line:
                                ARline = line.strip("\n")
                                ARline = ARline.strip('\t')
                                ARline = ARline.strip("Advertising Router: ")
                            elif "Sequence Number" in line:
                                SNline = line.strip("\n")
                                SNline = SNline.strip('\t')
                                SNline = SNline.strip("Sequence Number: ")
                            elif "Checksum" in line and "Length" in peek_line(file):
                                CSline = line.strip("\n")
                                CSline = CSline.strip('\t')
                                CSline = CSline.strip("Checksum: ")
                                if "/AR"+ARline + "SN"+SNline not in message:
                                    message = message + "/LST"+LSTline+ "LSID"+LSIDline+ "AR"+ARline + "SN"+SNline+"CS"+CSline+"/"
                        else:
                            break

                #add ls ack fields
                elif message == "LS Acknowledge (5)":
                    while peek_line(file):
                        line = file.readline()
                        if "~" not in line:
                            if "LS Type" in line:
                                LSTline = line.strip("\n")
                                LSTline = LSTline.strip('\t')
                                LSTline = LSTline.strip("LS Type: ")
                            elif "Link State ID: " in line:
                                LSIDline = line.strip("\n")
                                LSIDline = LSIDline.strip('\t')
                                LSIDline = LSIDline.strip("Link State ID: ")
                            elif "Advertising Router" in line:
                                ARline = line.strip("\n")
                                ARline = ARline.strip('\t')
                                ARline = ARline.strip("Advertising Router: ")
                            elif "Sequence Number" in line:
                                SNline = line.strip("\n")
                                SNline = SNline.strip('\t')
                                SNline = SNline.strip("Sequence Number: ")
                            elif "Checksum" in line and "Length" in peek_line(file):
                                CSline = line.strip("\n")
                                CSline = CSline.strip('\t')
                                CSline = CSline.strip("Checksum: ")
                                if "/AR"+ARline + "SN"+SNline not in message:
                                    message = message + "/LST"+LSTline+ "LSID"+LSIDline+ "AR"+ARline + "SN"+SNline+"CS"+CSline+"/"
                        else:
                            break
                #####
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

#generating the markov chain and calling for computing the acceptable sets
def run(final_result):
    print("Calculating frequency of occurance of packets...")
    #all unique transition pairs counter
    transition_counter = Counter()
    for i in range(len(final_result)):
        for j in range(len(final_result[i])):
            for k in range(len(final_result[i][j])-1):
                transition_counter[final_result[i][j][k]+"|||"+final_result[i][j][k+1]]+=1
    #total occurance of the first item in the transition pairs
    first_total = Counter()
    for i in transition_counter:
        first_total[i.split("|||")[0]]+=transition_counter[i]
    #converting transition_counter to pure frequency in percentage
    # transition = message1 to message2
    # final_frequency = [transition : frequency of occurance]
    final_frequency = defaultdict()
    for i in transition_counter:
        final_frequency[i] = transition_counter[i]/first_total[i.split("|||")[0]]


    #proceed to rule extraction for acceptable sets
    rule_extraction(final_frequency)

    # ##### THE FOLLOWING GENERATES A MARKOV CHAIN IF UNCOMMENTED.
    # #list of all the nodes in first_total
    # node_list = []
    # for i in first_total:
    #     node_list.append(i)
    # # list of frequencies in matrixs format
    # p = [ [0]*len(node_list) for _ in range(len(node_list))]
    # for i in node_list:
    #     for j in node_list:
    #         if i+"|||"+j in final_frequency:
    #             p[node_list.index(i)][node_list.index(j)]=final_frequency[i+"|||"+j]
    # #node_list rename, save_correspondance to symbol_packet_pair
    # symbol_packet_pair = defaultdict()
    # symbol = 0
    # print("Converting packet name to symbol...")
    # for i in range(len(node_list)):
    #     symbol_packet_pair[str(symbol)]=node_list[i]
    #     node_list[i]=str(symbol)
    #     symbol = symbol+1
    # print("Writing out symbol_packet_pair...")
    # with open ('extraction_symbol_packet_pair.txt', 'w') as f:
    #     for i in symbol_packet_pair:
    #         f.write(i+"   :   "+symbol_packet_pair[i]+"\n")
    # #creating and saving the markov chain
    # print("Creating markov chain...")
    # mc = MarkovChain(p, node_list)
    # print("Plotting MC...")
    # plt.figure.Figure = plot_graph(mc)[0]
    # plt.subplots.figure = plot_graph(mc)[1]
    # plt.savefig("mc.png")

#computing the accepatable sets
def rule_extraction(final_frequency):
    print("Extracting rules...")
    #default dict of investigating items
    investigating = defaultdict()
    for i in final_frequency:
        #isolating first and second packets
        first_packet = i.split("|||")[0]
        second_packet = i.split("|||")[1]
        #item specification/can be modified
        if "LS " in first_packet and "LS " in second_packet and "LS R" not in i:
            investigating[i]=final_frequency[i]
    
    #rules
    found_ar_rule = set()
    found_lst_rule = set()
    found_lsid_rule = set()
    found_lssn_rule = set()
    found_lscs_rule = set()
    found_lssn_greater_rule = set()

    for i in investigating:
        #finding the needed field values
        first_packet = i.split("|||")[0]
        second_packet = i.split("|||")[1]
        #ar values
        first_packet_ar = re.findall(r'AR(.*?)SN', first_packet,re.DOTALL)
        second_packet_ar = re.findall(r'AR(.*?)SN', second_packet,re.DOTALL)
        #lst values
        first_packet_lst = re.findall(r'LST(.*?)LSID', first_packet,re.DOTALL)
        second_packet_lst = re.findall(r'LST(.*?)LSID', second_packet,re.DOTALL)
        #lsid values
        first_packet_lsid = re.findall(r'LSID(.*?)AR', first_packet,re.DOTALL)
        second_packet_lsid = re.findall(r'LSID(.*?)AR', second_packet,re.DOTALL)
        #lssn values
        first_packet_lssn = re.findall(r'SN(.*?)/', first_packet,re.DOTALL)
        second_packet_lssn = re.findall(r'SN(.*?)/', second_packet,re.DOTALL)
        #lscs values
        first_packet_lscs = re.findall(r'CS(.*?)/', first_packet,re.DOTALL)
        second_packet_lscs = re.findall(r'CS(.*?)/', second_packet,re.DOTALL)


        # adding send or receive to packets
        if "Send" in first_packet:
            first_packet_id = first_packet.split('/')[0] + " Send"
        else:
            first_packet_id = first_packet.split('/')[0] + " Receive"
        if "Send" in second_packet:
            second_packet_id = second_packet.split('/')[0] + " Send"
        else:
            second_packet_id = second_packet.split('/')[0] + " Receive"

        #identifying packets with intersection in types/id, more conditions can be added to add specification
        if len(list(set(first_packet_lst) & set(second_packet_lst)))>=1:
            found_lst_rule.add(first_packet_id + "|" + second_packet_id)
        if len(list(set(first_packet_lsid) & set(second_packet_lsid)))>=1:
            found_lsid_rule.add(first_packet_id + "|" + second_packet_id)
        if len(list(set(first_packet_ar) & set(second_packet_ar)))>=1:
            found_ar_rule.add(first_packet_id + "|" + second_packet_id)
        if len(list(set(first_packet_lssn) & set(second_packet_lssn)))>=1:
            found_lssn_rule.add(first_packet_id + "|" + second_packet_id)
        if len(list(set(first_packet_lscs) & set(second_packet_lscs)))>=1:
            found_lscs_rule.add(first_packet_id + "|" + second_packet_id)
        if max(first_packet_lssn) < min(second_packet_lssn):
            found_lssn_greater_rule.add(first_packet_id + "|" + second_packet_id)

    #outputing the rules
    with open ("output/accept_bird.txt","w") as efile:
        efile.write("Observed packets with intersecting LS Type sets:\n")
        rule_counter = 0
        for i in found_lst_rule:
            efile.write(str(rule_counter)+") "+i+"\n")
            rule_counter = rule_counter+1
        efile.write("------------------------------------------------------------------------------\n")

        rule_counter = 0
        efile.write("Observed packets with intersecting Link State ID sets:\n")
        for i in found_lsid_rule:
            efile.write(str(rule_counter)+") "+i+"\n")
            rule_counter = rule_counter+1
        efile.write("------------------------------------------------------------------------------\n")

        rule_counter = 0
        efile.write("Observed packets with intersecting Advertising Router sets:\n")
        for i in found_ar_rule:
            efile.write(str(rule_counter)+") "+i+"\n")
            rule_counter = rule_counter+1
        efile.write("------------------------------------------------------------------------------\n")        

        rule_counter = 0
        efile.write("Observed packets with intersecting Link State Sequence Number sets:\n")
        for i in found_lssn_rule:
            efile.write(str(rule_counter)+") "+i+"\n")
            rule_counter = rule_counter+1
        efile.write("------------------------------------------------------------------------------\n")        

        rule_counter = 0
        efile.write("Observed packets with intersecting Link State Checksum sets:\n")
        for i in found_lscs_rule:
            efile.write(str(rule_counter)+") "+i+"\n")
            rule_counter = rule_counter+1
        efile.write("------------------------------------------------------------------------------\n")        

        rule_counter = 0
        efile.write("Observed packets with second having all greater Link State Sequence Numbers:\n")
        for i in found_lssn_greater_rule:
            efile.write(str(rule_counter)+") "+i+"\n")
            rule_counter = rule_counter+1


        
def main():

    final_result = []
    print("Isolating packets from log files...")
    files3 = ['logs/b800_1_3.txt','logs/b800_2_3.txt','logs/b800_3_3.txt','logs/b800_4_3.txt',
    'logs/b800_5_3.txt','logs/b800_6_3.txt','logs/b800_7_3.txt','logs/b800_8_3.txt',
    'logs/b800_9_3.txt','logs/b800_10_3.txt','logs/b800_11_3.txt','logs/b800_12_3.txt',
    'logs/b800_13_3.txt','logs/b800_14_3.txt','logs/b800_15_3.txt']
    files2 = ["logs/b1000_1_2.txt","logs/b1000_2_2.txt","logs/b1000_3_2.txt","logs/b1000_4_2.txt",
    "logs/b1000_5_2.txt","logs/b1000_6_2.txt","logs/b1000_7_2.txt","logs/b1000_8_2.txt","logs/b1000_9_2.txt",
    "logs/b1000_10_2.txt"]
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
