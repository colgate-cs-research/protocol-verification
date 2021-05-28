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
def parse_logs(fname, recv):
    inter = ""
    src_router = ""
    des_router = ""
    message = ""
    #source router + interface = destination router
    pkts = {}
    for value in recv.values():
        if value not in pkts:
            pkts[value] = []
    with open (fname) as file:
        line = file.readline()
        while line:
            line = line.strip()
            #print("\t"+line)
            #timestamp of msg
            if line.startswith("Time Stamp"):
                time = line.replace("Time Stamp", "")
            #interface of message
            elif line.startswith("Source:"):
                inter = line.replace("Source: ", "")
            #type of message
            elif line.startswith("Message Type:"):
                message = line.replace("Message Type: ", "")
            #source and dest router of message
            elif line.startswith("Source OSPF Router:"):
                src_router = line.replace("Source OSPF Router: ", "")
                recv_key = src_router+inter
                des_router = recv[recv_key]
                #####can add more information/conditions to distinguish packets if want to
                #####below is excample
                if message == "LS Update (4)" or message == "LS Acknowledge (5)":
                    # Process each LSA
                    LSTline = None
                    line = file.readline()
                    while line and '~' not in line:
                        line = line.strip()
                        #print("\t"+line)
                        value = None
                        if ":" in line:
                            value = line.split(":")[1].strip()
                        if "LS Age" in line:
                            LSAGEline = value
                        elif line.startswith("LS Type:"):
                            if LSTline is not None:
                                #if "/AR"+ARline + "SN"+SNline not in message:
                                message = message + "/AGE"+LSAGEline+"LST"+LSTline+ "LSID"+LSIDline+ "AR"+ARline + "SN"+SNline+"/#"
                            LSTline = value
                        elif line.startswith("Link State ID:"):
                            LSIDline = value
                        elif line.startswith("Advertising Router:"):
                            ARline = value
                        elif line.startswith("Sequence Number:"):
                            SNline = value
                        line = file.readline()
                    if LSTline is not None:
                        #if "/AR"+ARline + "SN"+SNline not in message:
                        message = message + "/AGE"+LSAGEline+"LST"+LSTline+ "LSID"+LSIDline+ "AR"+ARline + "SN"+SNline+"/#"
                #print(message)
                #####
                #Assign messages to router sets with sent or receive at end of message
                pkts[src_router].append(message+"Send at "+time + " to " + des_router)
                pkts[des_router].append(message+"Receive at "+time + " from " +src_router)
            line = file.readline() 
    return pkts

#computing the causal sets
def run(final_result, logs_file, causal_file, specific_causal_file):
    #dictionaries with all information on packets
    # send -> receive
    send_dict = defaultdict(set)
    # receive -> send
    recv_dict = defaultdict(set)

    #dictionary of all information on packets with timestamps
    # send -> receive
    timestamp_trace_send_recv = defaultdict(set)
    # receive -> send
    timestamp_trace_recv_send = defaultdict(set)

    with open(logs_file, 'w') as f:
        json.dump(final_result, f, indent=4)

    #iterate through topologies
    for topologies in final_result:
        #iterate through logs in each topology
        for router, logs in topologies.items():
            # iterate through all msgs in each log
            for k in range(len(logs)):
                #after sending a packet
                if "Send" in logs[k]:
                    current_msg = logs[k]
                    send_time = re.search('at (\d+\.\d+) ', current_msg)
                    send_time = float(send_time.group(1))
                    curr_t_router = current_msg.split("to ")[1]
                    #finding first msg received
                    for l in range(k,len(logs)):
                        next_msg = logs[l]
                        if "Receive" in next_msg:
                            next_t_router = next_msg.split("from ")[1]
                            recv_time = re.search('at (\d+\.\d+) ', next_msg)
                            recv_time = float(recv_time.group(1))
                            #appending to causal if condition is met: time diff > 6 and communicating routers are identical
                            if (recv_time - send_time)>0.9 and curr_t_router == next_t_router:
                                #print(current_msg, next_msg)
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
    #dictionary with only type information
        # send -> receive
    type_send_dict = defaultdict(set)
    # receive -> send
    type_recv_dict = defaultdict(set)
    for key in send_dict:
        f_type = key.split('/')[0]
        for s_packet in send_dict[key]:
            s_type = s_packet.split('/')[0]
            type_send_dict[f_type].add(s_type)
    
    for key in recv_dict:
        f_type = key.split('/')[0]
        for s_packet in recv_dict[key]:
            s_type = s_packet.split('/')[0]
            type_recv_dict[f_type].add(s_type)
    

    with open (causal_file, 'w') as f:
        f.write("receive -> send\n")
        for key in type_recv_dict:
            f.write(key+"\n")
            f.write(str(type_recv_dict[key])+"\n")
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
        for key in type_send_dict:
            f.write(key+"\n")
            f.write(str(type_send_dict[key])+"\n")
    
    #  recv -> send
    specific_causal_recv_sn = defaultdict(set)
    #  send -> recv
    specific_causal_send_sn = defaultdict(set)
    #  recv -> send
    specific_causal_recv_age = defaultdict(set)
    #  send -> recv
    specific_causal_send_age = defaultdict(set)
    
    #output more specific causal relationships
    with open (specific_causal_file,'w') as f:
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
                                first_packet_lssn = re.findall(r'SN(.*?)/', f_lsa,re.DOTALL)
                                second_packet_lssn = re.findall(r'SN(.*?)/', s_lsa,re.DOTALL)
                                #check if the lsas are correspondng by ar, type, and id
                                if first_packet_lst == second_packet_lst and first_packet_lsid == second_packet_lsid and first_packet_ar == second_packet_ar:
                                    # input relation values to be checked
                                    if first_packet_lssn[0] < second_packet_lssn[0]:
                                        specific_causal_recv_sn[key.split("/")[0]].add(i.split("/")[0])
                                        # ######optional code to trace these paired packets
                                        # for f_packet in timestamp_trace_recv_send:
                                        #     for i1 in f_packet.split('#'):
                                        #         found_f = False
                                        #         if first_packet_lst[0] in i1 and first_packet_lsid[0] in i1 and first_packet_ar[0] in i1 and first_packet_lssn[0] in i1:
                                        #             found_f = True
                                        #             for s_packet in timestamp_trace_recv_send[f_packet]:
                                        #                 found_s = False
                                        #                 for j1 in s_packet.split('#'):
                                        #                     if second_packet_lst[0] in j1 and second_packet_lsid[0] in j1 and second_packet_ar[0] in j1 and second_packet_lssn[0] in j1:
                                        #                         print(f_packet)
                                        #                         print(s_packet)
                                        #                         print(i1)
                                        #                         print(j1)
                                        #                         print()
                                        #                         found_s= True
                                        #                 if found_s == True:
                                        #                     break
                                        #         if found_f == True:
                                        #             break
                                        # ########
                                    if int(first_packet_age[0]) < int(second_packet_age[0]):
                                        specific_causal_recv_age[key.split("/")[0]].add(i.split("/")[0])
                                        # ######optional code to trace these paired packets
                                        # for f_packet in timestamp_trace_recv_send:
                                        #     for i1 in f_packet.split('#'):
                                        #         found_f = False
                                        #         if first_packet_lst[0] in i1 and first_packet_lsid[0] in i1 and first_packet_ar[0] in i1 and "AGE"+first_packet_age[0] in i1:
                                        #             found_f = True
                                        #             for s_packet in timestamp_trace_recv_send[f_packet]:
                                        #                 found_s = False
                                        #                 for j1 in s_packet.split('#'):
                                        #                     if second_packet_lst[0] in j1 and second_packet_lsid[0] in j1 and second_packet_ar[0] in j1 and "AGE"+second_packet_age[0] in j1:
                                        #                         print(f_packet)
                                        #                         print(s_packet)
                                        #                         print(i1)
                                        #                         print(j1)
                                        #                         print()
                                        #                         found_s= True
                                        #                 if found_s == True:
                                        #                     break
                                        #         if found_f == True:
                                        #             break
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
                                first_packet_lssn = re.findall(r'SN(.*?)/', f_lsa,re.DOTALL)
                                second_packet_lssn = re.findall(r'SN(.*?)/', s_lsa,re.DOTALL)
                                #check if the lsas are correspondng by ar, type, and id
                                if first_packet_lst == second_packet_lst and first_packet_lsid == second_packet_lsid and first_packet_ar == second_packet_ar:
                                    # input relation values to be checked
                                    if first_packet_lssn[0] < second_packet_lssn[0]:
                                        specific_causal_send_sn[key.split("/")[0]].add(i.split("/")[0])
                                        # ######optional code to trace these paired packets
                                        # for f_packet in timestamp_trace_send_recv:
                                        #     for i1 in f_packet.split('#'):
                                        #         found_f = False
                                        #         if first_packet_lst[0] in i1 and first_packet_lsid[0] in i1 and first_packet_ar[0] in i1 and first_packet_lssn[0] in i1:
                                        #             found_f = True
                                        #             for s_packet in timestamp_trace_send_recv[f_packet]:
                                        #                 found_s = False
                                        #                 for j1 in s_packet.split('#'):
                                        #                     if second_packet_lst[0] in j1 and second_packet_lsid[0] in j1 and second_packet_ar[0] in j1 and second_packet_lssn[0] in j1:
                                        #                         print(f_packet)
                                        #                         print(s_packet)
                                        #                         print(i1)
                                        #                         print(j1)
                                        #                         print()
                                        #                         found_s= True
                                        #                 if found_s == True:
                                        #                     break
                                        #         if found_f == True:
                                        #             break
                                        # ########
                                    if int(first_packet_age[0]) < int(second_packet_age[0]):
                                        specific_causal_send_age[key.split("/")[0]].add(i.split("/")[0])
                                        # ######optional code to trace these paired packets
                                        # for f_packet in timestamp_trace_send_recv:
                                        #     for i1 in f_packet.split('#'):
                                        #         found_f = False
                                        #         if first_packet_lst[0] in i1 and first_packet_lsid[0] in i1 and first_packet_ar[0] in i1 and "AGE"+first_packet_age[0] in i1:
                                        #             found_f = True
                                        #             for s_packet in timestamp_trace_send_recv[f_packet]:
                                        #                 found_s = False
                                        #                 for j1 in s_packet.split('#'):
                                        #                     if second_packet_lst[0] in j1 and second_packet_lsid[0] in j1 and second_packet_ar[0] in j1 and "AGE"+second_packet_age[0] in j1:
                                        #                         print(f_packet)
                                        #                         print(s_packet)
                                        #                         print(i1)
                                        #                         print(j1)
                                        #                         print()
                                        #                         found_s= True
                                        #                 if found_s == True:
                                        #                     break
                                        #         if found_f == True:
                                        #             break
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

"""Perform causal analysis for FRR"""
def main_frr(topology):
    final_result = []

    # triangle topology
    if (topology in ["triangle", "all"]):
        files3 = ['logs/l800_1_3.txt','logs/l800_2_3.txt',
        'logs/l800_3_3.txt','logs/l800_4_3.txt',
        'logs/l800_5_3.txt','logs/l800_6_3.txt',
        'logs/l800_7_3.txt','logs/l800_8_3.txt',
        'logs/l800_9_3.txt','logs/l800_10_3.txt',]
        #source router + interface = destination router
        recv3 = {"172.17.0.210.10.0.2":"172.17.0.3","172.17.0.210.10.0.18":"172.17.0.4","172.17.0.310.10.0.3":"172.17.0.2","172.17.0.310.10.0.10":"172.17.0.4","172.17.0.410.10.0.11":"172.17.0.3","172.17.0.410.10.0.19":"172.17.0.2"} 
        for input_file3 in files3:
            final_result.append(parse_logs(input_file3, recv3))

    # double topology
    if (topology in ["double", "all"]):
        files2 = ['logs/l1000_1_2.txt','logs/l1000_2_2.txt',
        'logs/l1000_3_2.txt','logs/l1000_4_2.txt',
        'logs/l1000_5_2.txt']
        #source router + interface = destination router
        recv2 = {"172.17.0.210.10.0.2":"172.17.0.3","172.17.0.310.10.0.3":"172.17.0.2"}
        for input_file2 in files2:
            final_result.append(parse_logs(input_file2, recv2))

    run(final_result, 'output/logs_frr.txt', 'output/causal_frr.txt', 'output/specific_causal_frr.txt')

"""Perform causal analysis for Bird"""
def main_bird(topology):
    final_result = []

    # triangle topology
    if (topology in ["triangle", "all"]):
        files3 = ['logs/lb800_1_3.txt','logs/lb800_2_3.txt',
        'logs/lb800_3_3.txt','logs/lb800_4_3.txt',
        'logs/lb800_5_3.txt','logs/lb800_6_3.txt',
        'logs/lb800_7_3.txt','logs/lb800_8_3.txt',
        'logs/lb800_9_3.txt','logs/lb800_10_3.txt',]
        #source router + interface = destination router
        recv3 = {"10.10.0.210.10.0.2":"10.10.0.3","10.10.0.210.10.0.18":"10.10.0.11","10.10.0.310.10.0.3":"10.10.0.2","10.10.0.310.10.0.10":"10.10.0.11","10.10.0.1110.10.0.11":"10.10.0.3","10.10.0.1110.10.0.19":"10.10.0.2"}
        for input_file3 in files3:
            final_result.append(parse_logs(input_file3, recv3))

    # double topology
    if (topology in ["double", "all"]):
        files2 = ['logs/lb1000_1_2.txt','logs/lb1000_2_2.txt',
        'logs/lb1000_3_2.txt','logs/lb1000_4_2.txt',
        'logs/lb1000_5_2.txt']
        #source router + interface = destination router
        recv2 = {"10.10.0.210.10.0.2":"10.10.0.3","10.10.0.310.10.0.3":"10.10.0.2"}
        for input_file2 in files2:
            final_result.append(parse_logs(input_file2, recv2))

    run(final_result, 'output/logs_bird.txt', 'output/causal_bird.txt', 'output/specific_causal_bird.txt')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--implementation", choices=['frr', 'bird', 'all'], help="Implementation for which to perform causal analysis", default='all')
    parser.add_argument("-t", "--topology", choices=['triangle', 'double', 'all'], help="Topology for which to perform causal analysis", default='all')
    settings = parser.parse_args()

    if (settings.implementation in ["frr", "all"]):
        main_frr(settings.topology)
    if (settings.implementation in ["bird", "all"]):
        main_bird(settings.topology)

if __name__ == "__main__":
    main()

#DB Description (2)
#LS Update (4)
#LS Request (3)
#LS Acknowledge (5)
#Hello Packet (1)