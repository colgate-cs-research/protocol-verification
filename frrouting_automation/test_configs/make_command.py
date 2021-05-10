import random
import sys

#simple function to check if string starts and ends with brackets
def is_brackets(string):
	open_brackets = ['<', '[', '(', '{']
	close_brackets = ['>', ']', ')', '}']
	if(string[0] in open_brackets and string[-1] in close_brackets):
		return 1
	return 0

#main function to return all possible combinations of commands
def make_command(string):
	substrings = extract_brackets(string)
	outputs = [string]
	if(is_brackets(string)):
		outputs = sub_command(string)
	if not substrings:
		return sub_command(string)
	else:
		for substring in substrings:
			commands = make_command(substring)
			outputs = add_commands(outputs, commands, substring)
	return outputs

#make all possible combinations of bracketed template
def add_commands(outputs, commands, substring):
	new_outputs = []
	temp_outputs = set()
	for command in commands:
		for output in outputs:
			try:
				index = output.index(substring)
				new_output = output[:index] + command + output[index+len(substring):]
				new_outputs.append(new_output)
			except ValueError:
				temp_outputs.add(output)
	temp_outputs = list(temp_outputs)
	new_outputs.extend(temp_outputs)
	return new_outputs

#removes comments from string template ($...)
def remove_comments(string):
	i = 0
	while i<len(string)-1:
		if (string[i] == '$'):
			j = i+1
			while j < len(string) and (string[j].isalnum() or string[j] == '_'):
				j = j + 1
			start_index = i
			end_index = j
			string = string[:start_index] + string[end_index:]
		else:
			i = i+1
	return string

#returns highest level bracketed string
def extract_brackets(string):
	open_brackets = ['<', '[', '(', '{']
	close_brackets = ['>', ']', ')', '}']
	start_index = -1
	end_index = -1
	nested_count = 0
	bracket_index = -1
	bracket_count = 0
	substrings = []
	if string[0] in open_brackets and string[-1] in close_brackets:
		string = string[1:-1]
	for i, char in enumerate(string):	
		if (char in open_brackets):
			bracket_count = bracket_count + 1
			if(nested_count == 0):
				start_index = i
				nested_count = nested_count + 1
				bracket_index = open_brackets.index(char)
		if (char in close_brackets):
			bracket_count = bracket_count - 1
			if (char == close_brackets[bracket_index]):
				if(nested_count == 1 and bracket_count == 0):
					nested_count = nested_count - 1;
					end_index = i
					substrings.append(string[start_index:end_index+1])
	return substrings

#substitute/fill-in commands depending on bracket type
def sub_command(string):
	if(string[0] == '<' and string[-1] == '>'):
		return bracket_gt(string[1:-1])
	elif(string[0] == '[' and string[-1] == ']'):
		return bracket_sq(string[1:-1])
	elif(string[0] == '(' and string[-1] == ')'):
		return bracket_cr(string[1:-1])
	elif(string[0] == '{' and string[-1] == '}'):
		return bracket_gt(string[1:-1])
	else:
		print(string)
		raise Exception("Unexpected bracket type in command")
		
#substitute commands of the form <...>
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

#substitute commands of the form [...]
def bracket_sq(string):
	outputs = []
	outputs.append(string)
	outputs.append("")
	return outputs

#substitute commands of the form (...)
def bracket_cr(string):
	outputs = []
	index = string.index("-")
	start = int(string[:index])
	end = int(string[index+1:])
	outputs.append(str(random.randint(start, end)))
	return outputs

#test_command = "access-list WORD$name [seq (1-4294967295)$seq] <deny|permit>$action <A.B.C.D/M$prefix [exact-match$exact]|any>"
test_command = sys.argv[1]

commands = make_command(remove_comments(test_command))

for command in commands:
	print(command)
