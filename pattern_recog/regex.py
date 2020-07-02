import re 
import json
import argparse

#peeks into the next line of the file
def peek_line(f):
    pos = f.tell()
    line = f.readline()
    f.seek(pos)
    return line
#print(file.read()) 

def NSM_messages(message,time,date):
    print(message)
    pass

def ISM_messages(message,time,date):
    print(message)
    pass
    
#verifies and categorizes messages
def message_categorization(file, rule):
    ISM_states = ["Down","Loopback","Waiting","Point-to-point","DR Other","Backup","DR"]
    NSM_states = ["Down","Attempt","Init","2-Way","ExStart","Exchange","Loading","Full"]
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
                                    elif next_line == "/ # cat /tmp/ospf.log":
                                        break
                                if type(next_message)!= list:
                                    next_message = next_message.split()
                                    next_state = next_message[1]
                                    if i["New_state"].count(current_state)>0 and NSM_states.count(next_state)>0:
                                        print("Rule Followed: Old State == New State")
                                    elif next_state == "State":
                                        next_event = next_message[6]
                                        next_event = next_event.replace("(","")
                                        next_event = next_event.replace(")","")
                                        if next_message[3]==current_state and i["New_state"].count(next_message[5]) > 0 and next_event == event:
                                            print("Rule Followed: Old state transits to new state as indicated in the following message")

                    if rule_found == 0:
                        print("Rule Not Found")
                    
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
                                    elif next_line == "/ # cat /tmp/ospf.log":
                                        break
                                if type(next_message)!= list:
                                    next_message = next_message.split()
                                    next_state = next_message[1]
                                    if i["New_state"].count(current_state)>0 and NSM_states.count(next_state)>0:
                                        print("Rule Followed: Old State == New State")
                                    elif next_state == "State":
                                        if next_message[3]==current_state and i["New_state"].count(next_message[5]) > 0:
                                            print("Rule Followed: Old state transits to new state as indicated in the following message")
                                    else:
                                        print("Rule not followed")

                    if rule_found == 0:
                        print("Rule Not Found")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--rule", help="Path to JSON rule file", required=True)
    parser.add_argument("-l", "--log", help="Path to log file", required=True)
    settings = parser.parse_args()
    file = open(settings.log, "r")
    message_categorization(file,settings.rule)

main()
