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
                            if "LS Age" in line:
                                LSAGEline = line.strip("\n")
                                LSAGEline = LSAGEline.strip('\t')
                                LSAGEline = LSAGEline.split("LS Age (seconds): ")[1]
                            elif "LS Type" in line:
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
                                    message = message + "/AGE"+LSAGEline+"LST"+LSTline+ "LSID"+LSIDline+ "AR"+ARline + "SN"+SNline+"CS"+CSline+"/#"
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
                    r3.append(message+"Receive at "+time + " from " +src_router)
    return r1,r2,r3

#extract messages for each router in double topology
def double(fname):
    inter = ""
    src_router = ""
    des_router = ""
    message = ""
    #source router + interface = destination router
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
                            if "LS Age" in line:
                                LSAGEline = line.strip("\n")
                                LSAGEline = LSAGEline.strip('\t')
                                LSAGEline = LSAGEline.split("LS Age (seconds): ")[1]
                            elif "LS Type" in line:
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
                                    message = message + "/AGE"+LSAGEline+"LST"+LSTline+ "LSID"+LSIDline+ "AR"+ARline + "SN"+SNline+"CS"+CSline+"/#"
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

#computing the causal sets
def run(final_result):
    # send -> receive
    send_dict = defaultdict(set)
    # receive -> send
    recv_dict = defaultdict(set)
    # send -> receive
    timestamp_trace_send_recv = defaultdict(set)
    # receive -> send
    timestamp_trace_recv_send = defaultdict(set)
    #iterate through topologies
    for topologies in final_result:
        #iterate through logs in each topology
        for logs in topologies:
            # iterate through all msgs in each log
            for k in range(len(logs)):
                #after sending a packet
                if "Send" in logs[k]:
                    current_msg = logs[k]
                    send_time = re.search('Send at (.*) to ', current_msg)
                    send_time = float(send_time.group(1))
                    curr_t_router = current_msg.split("to ")[1]
                    #finding first msg received
                    for l in range(k,len(logs)):
                        next_msg = logs[l]
                        if "Receive" in next_msg:
                            next_t_router = next_msg.split("from ")[1]
                            recv_time = re.search('Receive at (.*) from ', next_msg)
                            recv_time = float(recv_time.group(1))
                            #appending to causal if condition is met: time diff > 6 and communicating routers are identical
                            if (recv_time - send_time)>0.9 and curr_t_router == next_t_router:
                                timestamp_trace_send_recv[current_msg.split(" to ")[0]].add(next_msg.split(" from ")[0])
                                send_dict[current_msg.split("Send")[0]].add(next_msg.split("Receive")[0])
                                break
                # same as above but after receiving a packet
                else:
                    current_msg = logs[k]
                    recv_time = re.search('Receive at (.*) from ', current_msg)
                    recv_time = float(recv_time.group(1))
                    curr_t_router = current_msg.split("from ")[1]
                    for l in range(k,len(logs)):
                        next_msg = logs[l]
                        if "Send" in next_msg:
                            next_t_router = next_msg.split("to ")[1]
                            send_time = re.search('Send at (.*) to ', next_msg)
                            send_time = float(send_time.group(1))
                            if (send_time - recv_time)>0.9 and curr_t_router == next_t_router:
                                timestamp_trace_recv_send[current_msg.split(" from ")[0]].add(next_msg.split(" to ")[0])
                                recv_dict[current_msg.split("Receive")[0]].add(next_msg.split("Send")[0])
                                break

    #output general causal relations based on type
    with open ('output/causal.txt', 'w') as f:
        f.write("receive -> send\n")
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
        f.write("send -> receive\n")
        for key in send_dict:
            f.write(key+"\n")
            f.write(str(send_dict[key])+"\n")
    
    #  recv -> send
    specific_causal_recv_sn = defaultdict(set)
    #  send -> recv
    specific_causal_send_sn = defaultdict(set)
    #  recv -> send
    specific_causal_recv_age = defaultdict(set)
    #  send -> recv
    specific_causal_send_age = defaultdict(set)
    
    #output more specific causal relationships
    with open ('output/specific_causal.txt','w') as f:
        for key in recv_dict:
            #check if related to lsa
            if "LS Update (4)" in key or "LS Acknowledge (5)" in key:
                for i in recv_dict[key]:
                    if "LS Update (4)" in i or "LS Acknowledge (5)" in i:
                        #listing all lsa in the two packets
                        first_lsa_list = (key.split("/",1)[1]).split("#")
                        second_lsa_list = (i.split("/",1)[1]).split("#")
                        first_lsa_list.remove("")
                        second_lsa_list.remove("")
                        #iterate through all lsas in the first and second packets
                        for f_lsa in first_lsa_list:
                            for s_lsa in second_lsa_list:
                                first_packet_age = re.findall(r'AGE(.*?)LST', f_lsa,re.DOTALL)
                                second_packet_age = re.findall(r'AGE(.*?)LST', s_lsa,re.DOTALL)

                                first_packet_ar = re.findall(r'AR(.*?)SN', f_lsa,re.DOTALL)
                                second_packet_ar = re.findall(r'AR(.*?)SN', s_lsa,re.DOTALL)
                                #lst values
                                first_packet_lst = re.findall(r'LST(.*?)LSID', f_lsa,re.DOTALL)
                                second_packet_lst = re.findall(r'LST(.*?)LSID', s_lsa,re.DOTALL)
                                #lsid values
                                first_packet_lsid = re.findall(r'LSID(.*?)AR', f_lsa,re.DOTALL)
                                second_packet_lsid = re.findall(r'LSID(.*?)AR', s_lsa,re.DOTALL)
                                #lssn values
                                first_packet_lssn = re.findall(r'SN(.*?)CS', f_lsa,re.DOTALL)
                                second_packet_lssn = re.findall(r'SN(.*?)CS', s_lsa,re.DOTALL)
                                #lscs values
                                first_packet_lscs = re.findall(r'CS(.*?)/', f_lsa,re.DOTALL)
                                second_packet_lscs = re.findall(r'CS(.*?)/', s_lsa,re.DOTALL)
                                #check if the lsas are correspondng by ar, type, and id
                                if first_packet_lst == second_packet_lst and first_packet_lsid == second_packet_lsid and first_packet_ar == second_packet_ar:
                                    # input relation values to be checked
                                    if first_packet_lssn[0] < second_packet_lssn[0]:
                                        specific_causal_recv_sn[key.split("/")[0]].add(i.split("/")[0])
                                        # ######optional code to trace these paired packets
                                        # for i1 in timestamp_trace_recv_send:
                                        #     if first_packet_lst[0] in i1 and first_packet_lsid[0] in i1 and first_packet_ar[0] in i1 and first_packet_lssn[0] in i1:
                                        #         for j1 in timestamp_trace_recv_send[i1]:
                                        #             if second_packet_lst[0] in j1 and second_packet_lsid[0] in j1 and second_packet_ar[0] in j1 and second_packet_lssn[0] in j1:
                                        #                 print(i1)
                                        #                 print(j1)
                                        #                 print()
                                        #                 break
                                        # ########
                                    if int(first_packet_age[0]) < int(second_packet_age[0]):
                                        specific_causal_recv_age[key.split("/")[0]].add(i.split("/")[0])
                                        # ######optional code to trace these paired packets
                                        # for i1 in timestamp_trace_recv_send:
                                        #     if first_packet_lst[0] in i1 and first_packet_lsid[0] in i1 and first_packet_ar[0] in i1 and "AGE"+first_packet_age[0] in i1:
                                        #         for j1 in timestamp_trace_recv_send[i1]:
                                        #             if second_packet_lst[0] in j1 and second_packet_lsid[0] in j1 and second_packet_ar[0] in j1 and "AGE"+second_packet_age[0] in j1:
                                        #                 print(i1)
                                        #                 print(j1)
                                        #                 print()
                                        #                 break
                                        # ########



        for key in send_dict:
            if "LS Update (4)" in key or "LS Acknowledge (5)" in key:
                for i in send_dict[key]:
                    if "LS Update (4)" in i or "LS Acknowledge (5)" in i:
                        #listing all lsa in the two packets
                        first_lsa_list = (key.split("/",1)[1]).split("#")
                        second_lsa_list = (i.split("/",1)[1]).split("#")
                        first_lsa_list.remove("")
                        second_lsa_list.remove("")
                        #iterate through all lsas in the first and second packets
                        for f_lsa in first_lsa_list:
                            for s_lsa in second_lsa_list:
                                first_packet_age = re.findall(r'AGE(.*?)LST', f_lsa,re.DOTALL)
                                second_packet_age = re.findall(r'AGE(.*?)LST', s_lsa,re.DOTALL)

                                first_packet_ar = re.findall(r'AR(.*?)SN', f_lsa,re.DOTALL)
                                second_packet_ar = re.findall(r'AR(.*?)SN', s_lsa,re.DOTALL)
                                #lst values
                                first_packet_lst = re.findall(r'LST(.*?)LSID', f_lsa,re.DOTALL)
                                second_packet_lst = re.findall(r'LST(.*?)LSID', s_lsa,re.DOTALL)
                                #lsid values
                                first_packet_lsid = re.findall(r'LSID(.*?)AR', f_lsa,re.DOTALL)
                                second_packet_lsid = re.findall(r'LSID(.*?)AR', s_lsa,re.DOTALL)
                                #lssn values
                                first_packet_lssn = re.findall(r'SN(.*?)CS', f_lsa,re.DOTALL)
                                second_packet_lssn = re.findall(r'SN(.*?)CS', s_lsa,re.DOTALL)
                                #lscs values
                                first_packet_lscs = re.findall(r'CS(.*?)/', f_lsa,re.DOTALL)
                                second_packet_lscs = re.findall(r'CS(.*?)/', s_lsa,re.DOTALL)
                                #check if the lsas are correspondng by ar, type, and id
                                if first_packet_lst == second_packet_lst and first_packet_lsid == second_packet_lsid and first_packet_ar == second_packet_ar:
                                    # input relation values to be checked
                                    if first_packet_lssn[0] < second_packet_lssn[0]:
                                        specific_causal_send_sn[key.split("/")[0]].add(i.split("/")[0])
                                        # ######optional code to trace these paired packets
                                        # for i1 in timestamp_trace_send_recv:
                                        #     if first_packet_lst[0] in i1 and first_packet_lsid[0] in i1 and first_packet_ar[0] in i1 and first_packet_lssn[0] in i1:
                                        #         for j1 in timestamp_trace_send_recv[i1]:
                                        #             if second_packet_lst[0] in j1 and second_packet_lsid[0] in j1 and second_packet_ar[0] in j1 and second_packet_lssn[0] in j1:
                                        #                 print(i1)
                                        #                 print(j1)
                                        #                 print()
                                        #                 break
                                        # ########
                                    if int(first_packet_age[0]) < int(second_packet_age[0]):
                                        specific_causal_send_age[key.split("/")[0]].add(i.split("/")[0])
                                        # ######optional code to trace these paired packets
                                        # for i1 in timestamp_trace_send_recv:
                                        #     if first_packet_lst[0] in i1 and first_packet_lsid[0] in i1 and first_packet_ar[0] in i1 and "AGE"+first_packet_age[0] in i1:
                                        #         for j1 in timestamp_trace_send_recv[i1]:
                                        #             if second_packet_lst[0] in j1 and second_packet_lsid[0] in j1 and second_packet_ar[0] in j1 and "AGE"+second_packet_age[0] in j1:
                                        #                 print(i1)
                                        #                 print(j1)
                                        #                 print()
                                        #                 break
                                        # ########
                                        
        f.write("--------------Recv -> send, responding lsa containing greater sn."+"\n")
        for key in specific_causal_recv_sn:
            f.write(key+"\n")
            f.write(str(specific_causal_recv_sn[key])+"\n")
            f.write("\n")
        f.write("--------------send -> recv, responding lsa containg greater sn"+"\n")
        for key in specific_causal_send_sn:
            f.write(key+"\n")
            f.write(str(specific_causal_send_sn[key])+"\n")
            f.write("\n")
        f.write("###########################################################################################################################################################\n")
        
        f.write("--------------recv -> send, responding lsa containing greater age."+"\n")
        for key in specific_causal_recv_age:
            f.write(key+"\n")
            f.write(str(specific_causal_recv_age[key])+"\n")
            f.write("\n")
        f.write("--------------send -> recv, responding lsa containg greater age"+"\n")
        for key in specific_causal_send_age:
            f.write(key+"\n")
            f.write(str(specific_causal_send_age[key])+"\n")
            f.write("\n")



def main():
    final_result = []
    ### delay is 3000 ms
    files3 = ['logs/l800_1_3.txt','logs/l800_2_3.txt',
    'logs/l800_3_3.txt','logs/l800_4_3.txt',
    'logs/l800_5_3.txt','logs/l800_6_3.txt',
    'logs/l800_7_3.txt','logs/l800_8_3.txt',
    'logs/l800_9_3.txt','logs/l800_10_3.txt',]

    for input_file3 in files3:
        final_result.append(triangle(input_file3))

    files2 = ['logs/l1000_1_2.txt','logs/l1000_2_2.txt',
    'logs/l1000_3_2.txt','logs/l1000_4_2.txt',
    'logs/l1000_5_2.txt']
    for input_file2 in files2:
        final_result.append(double(input_file2))

    run(final_result)
main()
#DB Description (2)
#LS Update (4)
#LS Request (3)
#LS Acknowledge (5)
#Hello Packet (1)
