# ftpclient.py 0.1
# A simple ftp client written in python
# Mike Dank, 2012

import sys
import socket
import string
from time import strftime, gmtime
import time
import array

host = ""
port = 21
is_authed = 0
is_pasv = 0
is_port = 0
sendstr = ""
logfilename = ""
newsock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
clisock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
hostsock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )

#Custom logging function, timestamps and writes to log
def loggit(s):
	timestamp = strftime("%Y-%m-%d %H:%M:%S", gmtime()) #Make timestamp
	log.write(timestamp + " " + s + '\n') 

#Function to receive from the socket
def receive():
	time.sleep(1.5) #Pause to make sure you don't receive too fast
	rec = clisock.recv(1024) #Receive data from socket
	loggit("Received: " + rec[:-1]) #Log the received line
	return rec
	
#Function to send a command to the socket	
def send(s):
	clisock.sendall(s + "\n") #Send string with line return
	loggit("Sent: " + s) #Log the sent line
	
#Issue a PASV command, set up a new connection	
def pasv_cmd():
	#Access the global variables
	global is_pasv
	global newsock
	
	send("PASV")
	line = receive()
	
	#Break the return line up to the string between the parenthesis
	line = line[line.rindex('(')+1:line.rindex(')')]
	#Split the six fields up by the comma separation
	lineparts = line.split(',')
	#Make a new string for the ipaddress from the split
	newhost = lineparts[0] + '.' + lineparts[1]+ '.' + lineparts[2] + '.' + lineparts[3]
	#Make an int for the port by multiplying p1 by 256 and adding p2
	newport = int(lineparts[4]) * 256 + int(lineparts[5])
	loggit("PASV string processed, host="+newhost+", port="+str(newport))
	
	#Attempt connection to the new socket
	try:
		newsock.connect( (newhost, newport) )
		print "New socket connection completed!"
		loggit("Connection to new socket successful!")
	except socket.gaierror:
		print "New socket host or port incorrect, terminating"
		loggit("New socket host or port incorrect, terminating")
	is_pasv = 1 #Set is_pasv variable to 1

#Function to issue USER command
def user_cmd():
	print ("Please enter your username")
	user = sys.stdin.readline()
	send("USER "+user[:-1])
	rec = receive()

	if "331 " in rec:
		#User is valid, prompt for a password
		pass_cmd()
	elif "503 " in rec:
		#User is already logged in
		print "Already logged in"
	else:
		#The username is invalid
		print "Invalid username"

#Function to handle the PASS command
def pass_cmd():
	global is_authed
	print ("Please enter your password")
	password = sys.stdin.readline()
	send("PASS "+ password[:-1])
	rec = receive()
	
	if "230 " in rec:
		"Password accepted!"
		is_authed = 1 #Set is_authed to 1
	elif "503 " in rec:
		#User is already logged in
		print "Already logged in"
	else:
		print "Password not accepted"

#Function to handle the CWD command
def cwd_cmd():
	print "What directory do you want to change to?"
	sendstr = sys.stdin.readline()
	send("CWD "+sendstr[:-1])
	rec = receive()
	
	if "250 " in rec:
		#CWD command accepted
		print "Change successful"
	else:
		print "Change unsuccessful"

#Function to handle the CDUP command
def cdup_cmd():

	send("CDUP")
	rec = receive()
	if "250 " in rec:
		print "CDUP successful!"
	else:
		print "CDUP not successful"

#Function to handle the QUIT command
def quit_cmd():
	send("QUIT")
	rec = receive()
	if "221 " in rec:
		#QUIT command accepted
		print "Disconnection successful, goodbye"
	else:
		print "Disconnection unsuccessful"

#Function for handling the PORT command
def port_cmd():
	#Access global variable
	global hostsock
	global is_port
	is_port = 1
	
	#Bind a socket with next available port
	try:
		hostsock.bind(('',0)) 
	
		#retrieve host port number
		hostport = hostsock.getsockname()[1]
		#Retreive host ip address
		hostip = socket.gethostbyname(socket.getfqdn())#hostsock.getsockname()[0]
		loggit("Binding with ip=" + hostip + ", and port=" + str(hostport))
		
		p2 = hostport%256 #Create p2 by getting remainder of port divided by 256
		p1 = (hostport-p2)/256 #Create p1 by result of dividing, subtract p2 to avoid a decimal result
		
		#Split the host ip up by periods
		lineparts = hostip.split('.')
		#Send over the PORT command with ip address and port components
		send("PORT "+lineparts[0]+","+lineparts[1]+","+lineparts[2]+","+lineparts[3]+","+str(p1)+","+str(p2))
		rec = receive()
		print rec#[:4]
	
	except socket.error:
		print "Unable to bind host"
		loggit("Unable to bind host")
	
#Function for handling the HELP command.
def help_cmd():
	print "What command would you like help for?"
	sendstr = sys.stdin.readline() #Read command
	#Keep list of valid commands that help can be retrieved for
	valid_commands = ["USER", "PASS", "CWD", "CDUP", "QUIT", "PASV", "PORT", "RETR", "PWD", "LIST", "HELP"]
	#Convert user command to uppercase and see if it's in list
	if sendstr.upper()[:-1] in valid_commands:
		#If it is, issue help command
		send("HELP "+sendstr[:-1])
		rec = receive()
		print rec[:4]
	else:
		print "Command not supported"
		
#Function for handling the LIST command
def list_cmd():
	print "What file would you like to use?"
	sendstr = sys.stdin.readline()
	send("LIST "+sendstr[:-1])
	print "Please wait"
	time.sleep(40)
	rec = receive()
	if "450 " in rec:
		print "No such file or directory"
	elif "425 " in rec:
		print "Unable to connect"
	elif "150 " in rec:
		print "Sending ascii list"
		#Saving list to a file
		output = open("list", "wb")
		loggit("File, list opened")
		loggit("Reading file data from socket...")
		#Start write loop
		while 1:
			filedata = newsock.recv(1024) #receive data from socket
			if not filedata:
				#if there is no data being read, exit the loop
				break;
			else:
				loggit("File data: " + filedata)
				output.write(filedata) #write the output to a file
		print "File transferred!"
		output.close() #close the file
		loggit("File, list closed")
	else:
		print rec[:4]

#Function for handling the PWD command
def pwd_cmd():
	send("PWD")
	rec = receive()
	#Print working directory
	print rec[4:]
	
#Function to handle the RETR command
def retr_cmd():
	print "What file would you like to retrieve?"
	sendstr = sys.stdin.readline() #get file name from user
	send("RETR "+sendstr[:-1])
	rec = receive()
	
	if "550 " in rec:
		#File or dir doesn't exist
		print "File or directory does not exist"
	else:
		#Set up an output file using name from user
		#Use flags 'w' for write, 'b' for binary
		output = open(sendstr, "wb")
		loggit("File, " + sendstr[:-1] + " opened")
		loggit("Reading file data from socket...")
		#Start write loop
		while 1:
			filedata = newsock.recv(1024) #receive data from socket
			if not filedata:
				#if there is no data being read, exit the loop
				break;
			else:
				loggit("File data: " + filedata)
				output.write(filedata) #write the output to a file
		print "File transferred!"
		output.close() #close the file
		loggit("File, " + sendstr[:-1] + " closed")
		
if (len(sys.argv) == 3) or (len(sys.argv) == 4):
	host = sys.argv[1]
	logfilename = sys.argv[2]
	if (len(sys.argv) == 4):
		port = int(sys.argv[3])
	
	#Set up logging with logfile, give it an append flag
	log = open(logfilename, 'a')
	
	#Make socket
	loggit("Attempting server connection...")
	try:
		clisock.connect( (host, port) )
		loggit("Connection successful!")
		print receive()[4:] # Print server greeting
	except socket.gaierror:
		print "Host or port incorrect, terminating"
		loggit("Host or port incorrect, terminating")

	#Prompt for username and password	
	user_cmd()

	#Run the loop while thje user doesn't quit
	while sendstr.startswith("quit")==False:
		print("ftp> "), #Set up the prompt
		sendstr = sys.stdin.readline() #read command
		
		#If they are not authed, only allow the user to log in
		if is_authed == 0:
			if sendstr.lower().startswith("user"):
				user_cmd()
			else:
				print "You must be logged in to do that"
		elif sendstr.lower().startswith("pass"):
			pass_cmd()
		elif sendstr.lower().startswith("user"):
			user_cmd()
		elif sendstr.lower().startswith("cwd"):
			cwd_cmd()
		elif sendstr.lower().startswith("cdup"):
			cdup_cmd()
		elif sendstr.lower().startswith("pasv"):
			if is_pasv == 0:
				pasv_cmd()
			else:
				print "Already connected"
		elif sendstr.lower().startswith("port"):
			if is_port == 0:
				port_cmd()
			else:
				print "Already connected"
		elif sendstr.lower().startswith("retr"):
			if is_pasv == 1:
				retr_cmd()
			else:
				print "Must be preceded by a PASV"
		elif sendstr.lower().startswith("pwd"):
			pwd_cmd()
		elif sendstr.lower().startswith("list"):
			if (is_pasv == 1 or is_port == 1):
				list_cmd()
			else:
				print "Must be preceded by a PORT or PASV"
		elif sendstr.lower().startswith("help"):
			help_cmd()
		elif sendstr.lower().startswith("quit"):
			quit_cmd()
		else:
			print("Command invalid or unsuported, please try again")
			
	#Close sockets before exit depending on whether or not they were opened
	clisock.close()
	loggit("Client socket is now closing")
	if is_pasv == 1:
		newsock.close()
		loggit("New socket is now closing")
	if is_port == 1:
		hostsock.close()
		loggit("Host socket is now closing")
		
	# Write a visual separater to the log
	log.write('----------------------------------------\n')
	#Close the log
	log.close()

else:
	print "Incorrect usage. Use: python ftpclient host logfile port"
	print "Port field is optional"