import sys

def remove_config(command):
	tester.write(r'send -- "'+"no "+command+r'\r"'+'\n')
	tester.write(r'expect "*#"'+'\n')

def add_config(command):
	tester.write('send -- "'+command+r'\r"'+'\n')
	tester.write(r'expect "*#"'+'\n')

config = open(sys.argv[1], "r")
tester = open("run_tests", "w")

lines = config.readlines()

#Get indentation (ie number of whitespaces) of first line
current_indent = 0

#Get indentation of next line
next_indent = 0

#Keep track of section count
exits = 0

tester.write("#!/usr/bin/expect -f"+'\n')
tester.write("set timeout -1"+'\n')
tester.write("log_file tests.log"+'\n')
tester.write("spawn vtysh"+'\n')
tester.write(r'expect "*#"'+'\n')
tester.write(r'send -- "configure terminal\r"'+'\n')
tester.write(r'expect "*#"'+'\n')

for index in range(0, len(lines)-1):
	
	next_indent = len(lines[index+1]) - len(lines[index+1].lstrip())
	current_indent = len(lines[index]) - len(lines[index].lstrip())

	command = lines[index].strip()
	
	if(command == "!"):
		continue
		
	if(current_indent < next_indent): #Indicates start of sub section
		add_config(command)
		exits = exits + 1
		continue
	
	elif(current_indent > next_indent): #Indicates inside/end of sub section
		if(command.startswith("no ")):
			add_config(command[3:])
			remove_config(command[3:])
		else:
			remove_config(command)
			add_config(command)
		tester.write(r'send -- "exit\r"'+'\n')
		exits = exits - 1
		tester.write(r'expect "*#"'+'\n')
		
	else:
		if(command.startswith("no ")):
			add_config(command[3:])
			remove_config(command[3:])
		else:
			remove_config(command)
			add_config(command)

for i in range(0, exits+1):
	tester.write(r'send -- "exit\r"'+'\n')
	tester.write(r'expect "*#"'+'\n')
	
tester.write(r'send -- "exit\r"'+'\n')
tester.write(r'expect "*#"'+'\n')

tester.write(r'send -- "exit\r"'+'\n')

tester.write("expect eof"+'\n')
		
