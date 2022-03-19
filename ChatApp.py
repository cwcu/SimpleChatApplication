import sys
import json
import time
import threading
from socket import *

def checkIP(IP):

	x = IP.split('.')
	if len(x) == 4:
		for i in range(4):
			if 0 <= int(x[i]) and int(x[i]) <= 255 and len(str(int(x[i]))) == len(x[i]): 
				# x[i] in [0, 255] and can't contain leading zeros
				continue
			else:
				raise Exception("Invalid IP address")
	else:
		raise Exception("Invalid IP address")

def checkPort(port):
	if 1024 <= port and port <= 65535:
		pass
	else:
		raise Exception("Assigned port out of the range 1024-65535")        

class Server:

	def __init__(self, serverPort):
		checkPort(serverPort)
		self.serverPort = serverPort
		self.table = {} # { <name> : {'IP' : <IP>, 'port' : <port>, 'name' : <name>, 'status' : <status>} }
		self.serverSocket = socket(AF_INET, SOCK_DGRAM) # ipv4, UDP
		self.serverSocket.bind(('', serverPort)) # '' -> '127.0.0.1'?

		while True:
			message, clientAddress = self.serverSocket.recvfrom(4096)
			message = json.loads(message.decode())
			if message[0] == 3: # 3: client registration request
				name = message[1]				
				IP = clientAddress[0]
				port = clientAddress[1]				
				self.addClient(name, IP, port)
			elif message[0] == 5: # 5: message to save
				# message[1] message[2]
				pass
			else:
				pass

	def broadcast(self):
		'''
		broadcast the table to all online clients
		'''

		for name, clientInfo in self.table.items():
			status = clientInfo['status']
			if status == 'yes':
				IP = clientInfo['IP']
				port = clientInfo['port']
				self.serverSocket.sendto(json.dumps([2, self.table]).encode(), (IP, port)) # type 2 message: table


	def addClient(self, name, IP, port):
		# check duplicate client name -> error
		self.table.update({name : {'IP' : IP, 'port' : port, 'name' : name, 'status' : 'yes'}})
		self.broadcast()


class Client:

	def __init__(self, name, serverIP, serverPort, port):
		checkIP(serverIP)
		checkPort(serverPort)
		checkPort(port)
		self.name = name 
		self.serverIP = serverIP
		self.serverPort = serverPort
		self.port = port # client port
		self.table = {} # { <name> : {'IP' : <IP>, 'port' : <port>, 'name' : <name>, 'status' : <status>} }

		self.clientSocket = socket(AF_INET, SOCK_DGRAM) # ipv4, UDP
		self.clientSocket.bind(('', port))	
		self.clientSocket.sendto(json.dumps([3, name]).encode(), (serverIP, serverPort)) # 3 indicates the message is for client registration request
		message, serverAddress = self.clientSocket.recvfrom(4096)
		message = json.loads(message.decode())
		if message[0] == 2: # message type 2: updated table
			print('>>> [Welcome, You are registered.]')		
			self.table = message[1]
			print('>>> [Client table updated.]')
			# self.clientSocket.settimeout(0.5) # timeout = 500 msec	
			listenThread = threading.Thread(target = self.listen).start()
			while True:
				command = input('>>> ')
				command = command.split(' ')
				if command[0] == 'send':
					self.send(command[1], command[2])
		else: # registration request rejected
			pass

	def listen(self):
		while True:
			message, sourceAddress = self.clientSocket.recvfrom(4096)	
			message = json.loads(message.decode())

			if message[0] == 0: # message type 0: ordinary message from another client
				# send back ack
				self.clientSocket.sendto(json.dumps([1]).encode(), (sourceAddress[0], sourceAddress[1]))
			elif message[0] == 1: # ack
				self.ack = True
			elif message[0] == 2: # message type 2: updated table	
				self.table = message[1]
				print('[Client table updated.]\n>>> ', end = '')
			else: # other message types to be implemented
				pass		

	# client notified leave 

	def send(self, name, message):
		'''
		implementation idea: we have two threads: the main thread (for user input command) and 
		the listening thread (for receiving messages from the server and other clients). In the main 
		thread, we first set self.ack = False, and then send the message to the target client, wait 
		for 500 msec, and then check whether the listening thread receive the ack and set self.ack = True: 
		if so, the message is received successfully; otherwise timeout and we send the message to the
		server.
		'''

		if name not in self.table.keys():
			raise Exception("target client doesn't exist")

		IP = self.table[name]['IP']
		port = self.table[name]['port']
		self.ack = False
		self.clientSocket.sendto(json.dumps([0, message]).encode(), (IP, port)) # message type 0: ordinary message
		try:
			time.sleep(0.5) # sleep for 500 msec
			if self.ack:
				print(f'[Message received by {name}.]\n>>> ', end = '')
			else:
				raise Exception()
		except:
			# timeout, send the message to server
			self.clientSocket.sendto(json.dumps([5, message, name]).encode(), 
				(self.serverIP, self.serverPort)) # type 5: message	for the server to save
			print(f'[No ACK from {name}, message sent to server.]\n>>> ', end = '')

	def __del__(self):
		'''
		handle keyboardexception -> 
		client silent leave
		'''
		self.clientSocket.close()
		print(">>> [Silent leave.]")


if sys.argv[1][1] == 's':
	server = Server(int(sys.argv[2]))
elif sys.argv[1][1] == 'c':
	client = Client(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
else: 
	raise Exception("Invalid mode argument")
	