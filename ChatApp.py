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
				msg = message[1]
				name = message[2]
				requestName = message[3]
				self.saveMessage(name, msg, requestName)
			elif message[0] == 6: # 6: client deregistration request
				name = message[1]
				self.table[name]['status'] = 'no'
				IP = self.table[name]['IP'] 
				port = self.table[name]['port']
				self.broadcast()
				self.serverSocket.sendto(json.dumps([1]).encode(), (IP, port)) # send ack
			elif message[0] == 7: # 7: client log-back request
				name = message[1]
				self.logBackClient(name)
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

	def logBackClient(self, name):
		if name not in self.table.keys():
			raise Exception("invalid name for client log-back")

		fileName = name + '.txt'
		try:
			offlineMessages = ['You Have Messages\n']
			with open(fileName, 'r') as f:  
				line = f.readline()
				if not line:
					# no offline message
					raise Exception()
				else:
					# assume the memory is enough for all the offline messages for one client
					# so we pack all the offline messages for a client and send them together
					while line:
						offlineMessages.append(line)
						line = f.readline()

					IP = self.table[name]['IP']
					port = self.table[name]['port']
					self.serverSocket.sendto(json.dumps([9, offlineMessages]).encode(), 
						(IP, port)) # type 9: offline messages	

			# clear all the offline messages for the client in the server
			with open(fileName, 'w') as f:  
				pass

		except Exception:
			pass
			
		self.table[name]['status'] = 'yes'
		self.broadcast()

	def saveMessage(self, name, message, requestName):
		if name not in self.table.keys():
			# print(<error message>) 
			# return ?
			raise Exception("nonexistent client") 

		if requestName not in self.table.keys():
			raise Exception("save-message request sent from nonexistent client")

		sourceIP = self.table[requestName]['IP']
		sourcePort = self.table[requestName]['port']

		if self.table[name]['status'] == 'yes':
			self.serverSocket.sendto(json.dumps([8, name, self.table]).encode(), (sourceIP, sourcePort)) # save-message error message
		else:
			self.table[name]['status'] = 'no'
			self.broadcast()

			fileName = name + '.txt'
			with open(fileName, 'a') as f:  
				savedMessage = requestName + ': ' + str(time.time()) + ' ' + message + '\n'
				f.write(savedMessage)

			self.serverSocket.sendto(json.dumps([1]).encode(), (sourceIP, sourcePort)) # ack

	def __del__(self):
		# delete all saved message files?
		pass

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
		self.shift = False # at current command line, whether there's '>>>' at the beginning

		self.clientSocket = socket(AF_INET, SOCK_DGRAM) # ipv4, UDP
		self.clientSocket.bind(('', port))	
		self.clientSocket.sendto(json.dumps([3, name]).encode(), (serverIP, serverPort)) # 3 indicates the message is for client registration request
		message, serverAddress = self.clientSocket.recvfrom(4096)
		message = json.loads(message.decode())
		if message[0] == 2: # message type 2: updated table
			print('>>> [Welcome, You are registered.]')		
			self.table = message[1]
			print('>>> [Client table updated.]')	

			self.listenThread = threading.Thread(target = self.listen) # create the listening thread
			self.listenThread.daemon = True
			self.listenThread.start()

			while True:
				self.shift = True 
				command = input('>>> ')
				command = command.split(' ')
				self.shift = False # when a command is typed in and enter 'return', we get to a new line, so no '>>>' at the beginning
				if command[0] == 'send':
					self.send(command[1], command[2])
				elif command[0] == 'dereg':
					self.deregistration(command[1])
				elif command[0] == 'reg':
					self.logBack(command[1])
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
				if self.shift:
					print('[Client table updated.]\n>>> ', end = '')
				else: 
					print('>>> [Client table updated.]')
			elif message[0] == 8: # message type 8: save-message error message
				print(f'>>> [Client {message[1]} exists!!]')
				self.table = message[2]
				print('>>> [Client table updated.]')
			elif message[0] == 9: # message type 9: offline messages
				offlineMessages = message[1]
				for line in offlineMessages:
					print(line + '>>> ', end = '')
			else: # other message types to be implemented
				pass		

	# client notified leave 

	def send(self, name, message):
		'''
		one client sends message to another client directly

		implementation idea: we have two threads: the main thread (for user input command) and 
		the listening thread (for receiving messages from the server and other clients). In the main 
		thread, we first set self.ack = False, and then send the message to the target client, wait 
		for 500 msec, and then check whether the listening thread receive the ack and set self.ack = True: 
		if so, the message is received successfully; otherwise timeout and we send the message to the
		server.
		'''

		if name not in self.table.keys():
			# exception -> print error message after '>>> '  
			raise Exception("target client doesn't exist")

		if self.table[name]['status'] == 'no':
			# the recipient is offline (exit via notified leave)

			self.saveMessageRequest(name, message)
			return

		IP = self.table[name]['IP']
		port = self.table[name]['port']
		self.ack = False
		self.clientSocket.sendto(json.dumps([0, message]).encode(), (IP, port)) # message type 0: ordinary message
		try:
			time.sleep(0.5) # sleep for 500 msec
			if self.ack:
				print(f'>>> [Message received by {name}.]\n', end = '')
			else:
				raise Exception()
		except:
			# timeout, send the message to server
			print(f'>>> [No ACK from {name}, message sent to server.]')
			self.saveMessageRequest(name, message)

	def deregistration(self, name):
		if name != self.name:
			raise Exception("invalid name for de-registration")

		self.ack = False
		self.clientSocket.sendto(json.dumps([6, name]).encode(), (self.serverIP, self.serverPort)) # 6: de-registration request
		time.sleep(0.5) # the listening thread is expecting an ack from the server
		if self.ack: 
			print('>>> [You are Offline. Bye.]\n', end = '')
			return
		else:
			# didn't receive an ack, retry for 5 times
			for i in range(5):
				self.clientSocket.sendto(json.dumps([6, name]).encode(), (self.serverIP, self.serverPort))	
				time.sleep(0.5)
				if self.ack:
					print('>>> [You are Offline. Bye.]\n', end = '')
					return

		print('>>> [Server not responding]\n>>> [Exiting]', end = '')
		self.clientSocket.close()
		sys.exit()

	def saveMessageRequest(self, name, message):
		self.ack = False
		self.clientSocket.sendto(json.dumps([5, message, name, self.name]).encode(), 
			(self.serverIP, self.serverPort)) # type 5: message	for the server to save		
		# wait for 500 msec by default
		time.sleep(0.5)
		if self.ack:
			print('>>> [Messages received by the server and saved]')
		# what if unsuccessful save-message request, other than the recipient is online?

	def logBack(self, name):
		if name != self.name:
			raise Exception("invalid name for log-back")

		self.clientSocket.sendto(json.dumps([7, name]).encode(), (self.serverIP, self.serverPort)) # 7: client log-back request		

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
	