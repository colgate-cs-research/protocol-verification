import re 

#peeks into the next line of the file
def peek_line(f):
    pos = f.tell()
    line = f.readline()
    f.seek(pos)
    return line

file = open("demo_file_short.txt", "r")
#print(file.read()) 

def NSM_messages(message,time,date):
    #print(message)
    pass

def ISM_messages(message,time,date):
    print(message)
    pass
    
#verifies and categorizes messages
def message_categorization():
    #iterates through each line in the given file
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
            #Checks for ISM messages
            if(re.search("ISM", message)!=None):
                ISM_messages(message,time,date)


message_categorization()

