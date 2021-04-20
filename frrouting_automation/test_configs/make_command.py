import random

def is_brackets(string):
	open_brackets = ['<', '[', '(', '{']
	close_brackets = ['>', ']', ')', '}']
	if(string[0] in open_brackets and string[-1] in close_brackets):
		return 1
	return 0

def make_command(string):
	substrings = extract_brackets(string)
	outputs = [string]
	if not substrings:
		return sub_command(string)
	else:
		for substring in substrings:
			commands = make_command(substring)
			outputs = add_commands(outputs, commands, substring)
	if(is_brackets(string)):
		final_outputs = []
		for output in outputs:
			final_outputs.extend(sub_command(output))
		outputs = final_outputs
	
	return outputs
			
def add_commands(outputs, commands, substring):
	new_outputs = []
	for command in commands:
		for output in outputs:
			index = output.index(substring)
			new_output = output[:index] + command + output[index+len(substring):]
			new_outputs.append(new_output)
	return new_outputs

def remove_comments(string):
	i = 0
	while i<len(string)-1:
		if (string[i] == '$'):
			j = i+1
			while j < len(string) and string[j].isalnum():
				j = j + 1
			start_index = i
			end_index = j
			string = string[:start_index] + string[end_index:]
		else:
			i = i+1
	return string

def extract_brackets(string): #returns bracketed string
	open_brackets = ['<', '[', '(', '{']
	close_brackets = ['>', ']', ')', '}']
	start_index = -1
	end_index = -1
	nested_count = 0
	bracket_index = -1
	substrings = []
	if string[0] in open_brackets and string[-1] in close_brackets:
		string = string[1:-1]
	for i, char in enumerate(string):	
		if (char in open_brackets):
			if(nested_count == 0):
				start_index = i
				nested_count = nested_count + 1
				bracket_index = open_brackets.index(char)
		if (char == close_brackets[bracket_index]):
			if(nested_count == 1):
				nested_count = nested_count - 1;
				end_index = i
				substrings.append(string[start_index:end_index+1])
	return substrings

def sub_command(string):
	if(string[0] == '<' and string[-1] == '>'):
		return bracket_gt(string[1:-1])
	elif(string[0] == '[' and string[-1] == ']'):
		return bracket_sq(string[1:-1])
	elif(string[0] == '(' and string[-1] == ')'):
		return bracket_cr(string[1:-1])
	else:
		print(string)
		raise Exception("Unexpected bracket type in command")
	
def bracket_gt(string):
	num_options = string.count("|") + 1
	start_index = 0
	outputs = []
	for i in range(1, num_options):
		option_index = string.index("|", start_index)
		option = string[start_index:option_index]
		start_index = option_index + 1
		outputs.append(option)
	outputs.append(string[start_index:])
	return outputs

def bracket_sq(string):
	outputs = []
	outputs.append(string)
	outputs.append("")
	return outputs

def bracket_cr(string):
	outputs = []
	index = string.index("-")
	start = int(string[:index])
	end = int(string[index+1:])
	outputs.append(str(random.randint(start, end)))
	return outputs

test_command = "access-list WORD$name [seq (1-4294967295)$seq] <deny|permit>$action <A.B.C.D/M$prefix [exact-match$exact]|any>"
#print(remove_comments(test_command))
#print(extract_brackets(remove_comments(test_command)))

#test_command = "access-list WORD$name [seq (1-5)$seq]"
#test_command = "[seq (1-425)]"

commands = make_command(remove_comments(test_command))

for command in commands:
	print(command)
