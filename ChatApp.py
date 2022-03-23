'''
CSEE4119 Programming Assignment 1 - Simple Chat Application
Chenqi Wang
cw3277
'''

import sys
import json
import time
import threading
from socket import *

def checkIP(IP):
	'''
	check whether IP is in the format of a.b.c.d, and 
	each of a, b, c, d is an integer in the range of [0, 255] 
	that contains no leading zeros.
	'''

	x = IP.split('.')
	if len(x) == 4:
		for i in range(4):
			if 0 <= int(x[i]) and int(x[i]) <= 255 and len(str(int(x[i]))) == len(x[i]): 
				# x[i] in [0, 255] and can't contain leading zeros
				continue
			else:
				print('>>> invalid IP address')
				sys.exit()
	else:
		print('>>> invalid IP address')
		sys.exit()

def checkPort(port):
	'''
	check whether port is in the range of [1024, 65535].
	'''
	
	if 1024 <= port and port <= 65535:
		pass
	else:
		print('>>> assigned port out of the range 1024-65535')
		sys.exit()      

class Server:

	def __init__(self, serverPort):
		'''
		Create an UDP socket to receive requests or ack from clients, 
		and call relative methods to handle them. The server can also 
		use the UDP socket to send messages.
		'''

		checkPort(serverPort)
		self.serverPort = serverPort
		self.table = {} # { <name> : {'IP' : <IP>, 'port' : <port>, 'name' : <name>, 'status' : <status>} }
		self.serverSocket = socket(AF_INET, SOCK_DGRAM) # ipv4, UDP
		self.serverSocket.bind(('', serverPort)) # '' represents INADDR_ANY: bind to all interfaces. For a server, you typically want to bind to all interfaces - not just "localhost".

		while True:
			self.serverSocket.settimeout(None) # put the socket in blocking mode
			message, clientAddress = self.serverSocket.recvfrom(4096)
			message = json.loads(message.decode())
			if message[0] == 1: # 1: ack
				self.ack = True
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
			elif message[0] == 10: # 10: channel message
				name = message[1]
				msg = message[2]
				self.handleChannelMessage(name, msg)
			else: # other message types, simply do nothing
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
		'''
		register a client in the table, and broadcast the table.
		'''
		if name in self.table.keys():
			# client registers with a duplicate name
			self.serverSocket.sendto(json.dumps([4]).encode(), (IP, port)) # 4: registration rejection		
			return

		self.table.update({name : {'IP' : IP, 'port' : port, 'name' : name, 'status' : 'yes'}})
		self.broadcast()

	def logBackClient(self, name):
		'''
		log back a client, send offline messages if there are, 
		change the client's status in the table to be online, and broadcast the new table.
		'''
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
					offlineMessages[-1] += '>>> '

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

	def checkStatusRequest(self, name):
		'''
		send a request to a client to check whether it's active (online) or not.
		'''
		IP = self.table[name]['IP']
		port = self.table[name]['port']
		self.ack = False
		self.serverSocket.sendto(json.dumps([12]).encode(), (IP, port))	# check status request 
		time.sleep(0.5)
		if self.ack:
			return True
		else:
			return False

	def saveMessage(self, name, message, requestName):
		'''
		when the intended recipient is offline, the server save the messages in the corresponding file.

		:name: name of the intended recipient of message
		:requestName: name of the client that sends the save-message request
		'''

		sourceIP = self.table[requestName]['IP']
		sourcePort = self.table[requestName]['port']

		if self.table[name]['status'] == 'no':
			fileName = name + '.txt'
			with open(fileName, 'a') as f:  
				savedMessage = '>>> ' + requestName + ': ' + str(time.time()) + ' ' + message + '\n'
				f.write(savedMessage)

			self.serverSocket.sendto(json.dumps([1]).encode(), (sourceIP, sourcePort)) # ack
		elif self.checkStatusRequest(name):
			# the intended recipient is online
			self.serverSocket.sendto(json.dumps([8, name, self.table]).encode(), (sourceIP, sourcePort)) # save-message error message
		else:
			# offline
			self.table[name]['status'] = 'no'
			self.broadcast()

			fileName = name + '.txt'
			with open(fileName, 'a') as f:  
				savedMessage = '>>> ' + requestName + ': ' + str(time.time()) + ' ' + message + '\n'
				f.write(savedMessage)

			self.serverSocket.sendto(json.dumps([1]).encode(), (sourceIP, sourcePort)) # ack

	def receiveACKs(self):
		'''
		For channel message, the server needs to receive acks from 
		all online clients (except the sender). This is the method 
		that listens to those acks. We create an individual listening 
		thread to run this method.
		'''

		self.serverSocket.settimeout(0.5) 

		try:
			while True:
				message, clientAddress = self.serverSocket.recvfrom(4096)
				message = json.loads(message.decode())
				if message[0] == 1: # message = [1, <name>], name of the client that sends ack
					name = message[1]
					self.acks[name] = True
		except:
			pass

		self.serverSocket.settimeout(None) # put the socket in blocking mode 

	def handleChannelMessage(self, senderName, message):
		'''
 		handle channel message. Send the message to all online clients (except the sender), 
 		and save the message for all offline messages. For clients that does not send back 
 		an ack, first check their status. If inactive (offline), update and broadcast the 
 		table, and then save the message in the corresponding files.
		'''
		senderIP = self.table[senderName]['IP']
		senderPort = self.table[senderName]['port']
		self.serverSocket.sendto(json.dumps([1]).encode(), (senderIP, senderPort)) # ack		

		self.acks = {} # {<name> : <ack>}

		# create a listening thread to receive acks from all online clients
		self.listenThread = threading.Thread(target = self.receiveACKs) 
		self.listenThread.daemon = True
		self.listenThread.start()

		for name, clientInfo in self.table.items():
			if name == senderName:
				continue

			IP = clientInfo['IP']
			port = clientInfo['port']
			if clientInfo['status'] == 'yes':
				# online
				channelMessage = 'Channel Message ' + senderName + ': ' + message + '\n>>> '
				self.acks[name] = False
				self.serverSocket.sendto(json.dumps([11, channelMessage]).encode(), (IP, port)) 		
			else:
				# offline
				fileName = name + '.txt'
				with open(fileName, 'a') as f:  
					savedMessage = '>>> ' + 'Channel Message ' + senderName + ': ' + str(time.time()) + ' ' + message + '\n'	
					f.write(savedMessage)				

		time.sleep(0.5)
		
		for name, ack in self.acks.items():
			if not ack:
				if not self.checkStatusRequest(name):
					# the intended recipient is offline
					self.table[name]['status'] = 'no'
					self.broadcast()

					fileName = name + '.txt'
					with open(fileName, 'a') as f:  
						savedMessage = '>>> ' + 'Channel Message ' + senderName + ': ' + str(time.time()) + ' ' + message + '\n'	
						f.write(savedMessage)	

class Client:

	def __init__(self, name, serverIP, serverPort, port):
		'''
		Create an UDP socket to send and receive messages, try to complete 
		the registration. And if the registration is successful, create a 
		listening thread that is responsible for receiving incoming messages, 
		so the main thread can handle user inputs simultaneously. 
		'''
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
			print('>>> Welcome, You are registered.')		
			self.table = message[1]
			print('>>> Client table updated.')	

			self.listenThread = threading.Thread(target = self.listen) # create the listening thread
			self.listenThread.daemon = True # daemon = True, so the listening thread would be automatically terminated when the process ends
			self.listenThread.start()

			while True:
				self.shift = True 
				command = input('>>> ')
				command = command.split(' ')
				self.shift = False # when a command is typed in and enter 'return', we get to a new line, so no '>>>' at the beginning
				if command[0] == 'send':
					self.send(command[1], ' '.join(command[2:]))
				elif command[0] == 'dereg':
					self.deregistration(command[1])
				elif command[0] == 'reg':
					self.logBack(command[1])
				elif command[0] == 'send_all':
					self.sendAll(' '.join(command[1:]))
		else: # registration request rejected - register with same name
			print(f'>>> Registration request rejected - name {name} used')
			sys.exit()

	def listen(self):
		'''
 		the listening thread runs this method, to listen to incoming messages and handle them appropriately.
		'''

		while True:
			message, sourceAddress = self.clientSocket.recvfrom(4096)	
			message = json.loads(message.decode())

			if message[0] == 0: # message type 0: ordinary message from another client
				# if client is offline
				print(message[1] + '\n>>> ', end = '')
				# send back ack
				self.clientSocket.sendto(json.dumps([1]).encode(), (sourceAddress[0], sourceAddress[1]))
			elif message[0] == 1: # ack
				self.ack = True
			elif message[0] == 2: # message type 2: updated table	
				# if receive an updated table when offline (via notified leave), no update would be made
				if self.table[self.name]['status'] == 'no':
					continue

				self.table = message[1]
				if self.shift:
					print('Client table updated.\n>>> ', end = '')
				else: 
					print('>>> Client table updated.')
			elif message[0] == 8: # message type 8: save-message error message
				print(f'>>> Client {message[1]} exists!!')
				self.table = message[2]
				print('>>> Client table updated.')
			elif message[0] == 9: # message type 9: offline messages
				offlineMessages = message[1]
				for line in offlineMessages:
					print(line, end = '')
			elif message[0] == 11: # 11: channel message from server to a client
				channelMessage = message[1]
				print(channelMessage, end = '')
				# send an ack to the server
				self.clientSocket.sendto(json.dumps([1, self.name]).encode(), (self.serverIP, self.serverPort))				
			elif message[0] == 12: # 12: check status request
				# if notified leave, wouldn't receive a check status request
				self.clientSocket.sendto(json.dumps([1]).encode(), (self.serverIP, self.serverPort))
			else: # other message types, simply do nothing
				pass	

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
			print('>>> nonexistent intended recipient')
			return

		if self.table[name]['status'] == 'no':
			# the recipient is offline (exit via notified leave)
			print(f'>>> No ACK from {name}, message sent to server.')
			self.saveMessageRequest(name, message)
			return

		if name == self.name:
			# send message to the client itself
			print('>>> ' + self.name + ': ' + message)
			return

		IP = self.table[name]['IP']
		port = self.table[name]['port']
		self.ack = False
		self.clientSocket.sendto(json.dumps([0, self.name + ': ' + message]).encode(), (IP, port)) # message type 0: ordinary message 	
		try:
			time.sleep(0.5) # sleep for 500 msec
			if self.ack:
				print(f'>>> Message received by {name}.\n', end = '')
			else:
				raise Exception()
		except:
			# timeout, send the message to server
			print(f'>>> No ACK from {name}, message sent to server.')
			self.saveMessageRequest(name, message)

	def deregistration(self, name):
		'''
		notified leave. Send the de-registration request to the server and except an ack, if timeout, retry for 5 times.
		'''

		if name != self.name:
			print(f'>>> invalid name for de-registration, should be {self.name}')
			return

		self.ack = False
		self.clientSocket.sendto(json.dumps([6, name]).encode(), (self.serverIP, self.serverPort)) # 6: de-registration request
		time.sleep(0.5) # the listening thread is expecting an ack from the server
		if self.ack: 
			print('>>> You are Offline. Bye.\n', end = '')
			return
		else:
			# didn't receive an ack, retry for 5 times
			for i in range(5):
				self.clientSocket.sendto(json.dumps([6, name]).encode(), (self.serverIP, self.serverPort))	
				time.sleep(0.5)
				if self.ack:
					print('>>> You are Offline. Bye.\n', end = '')
					return

		print('>>> Server not responding\n>>> Exiting')
		sys.exit()

	def saveMessageRequest(self, name, message):
		'''
		save-message request. Send the request to the server and except an ack, if timeout, retry for 5 times.
		'''
		self.ack = False
		self.clientSocket.sendto(json.dumps([5, message, name, self.name]).encode(), 
			(self.serverIP, self.serverPort)) # type 5: save message request	
		# wait for 500 msec by default
		time.sleep(0.5)
		if self.ack:
			print('>>> Messages received by the server and saved')
			return
		else:
			# retry 5 times
			for i in range(5):
				self.clientSocket.sendto(json.dumps([5, message, name, self.name]).encode(), 
					(self.serverIP, self.serverPort)) # type 5: save message request	
				time.sleep(0.5)				

				if self.ack:
					print('>>> Messages received by the server and saved')
					return

		print('>>> Server not responding\n>>> Exiting')
		sys.exit()

	def logBack(self, name):
		'''
		If the client exited via notified leave, it can log back by sending a log-back request to the server.
		'''
		if name != self.name:
			print('>>> invalid name for log-back')
			return

		self.clientSocket.sendto(json.dumps([7, name]).encode(), (self.serverIP, self.serverPort)) # 7: client log-back request		

	def sendAll(self, message):
		'''
		channel message - group chat. Send the channel message 
		to the server and the server would handel it appropriately. 
		It also excepts an ack from the server, if timeout, retry for 5 times.
		'''

		self.ack = False
		self.clientSocket.sendto(json.dumps([10, self.name, message]).encode(), (self.serverIP, self.serverPort)) # 10: group chat message			
		time.sleep(0.5)

		if self.ack:
			print('>>> Message received by Server.')
			return
		else:
			# receive no ack, retry 5 times
			for i in range(5):
				self.clientSocket.sendto(json.dumps([10, self.name, message]).encode(), (self.serverIP, self.serverPort)) # 10: group chat message	
				time.sleep(0.5)
				if self.ack:
					print('>>> Message received by Server.')
					return

		print('>>> Server not responding.')


if __name__ == '__main__':
	try: 
		if sys.argv[1][1] == 's':
			server = Server(int(sys.argv[2]))
		elif sys.argv[1][1] == 'c':
			client = Client(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
		else:
			raise Exception()
	except KeyboardInterrupt: # client silent leave via ctrl + c 
		sys.exit()
	except Exception: # all built-in non-system-exit, all user-defined exceptions
		print(">>> invalid command line arguments")
		sys.exit()
	