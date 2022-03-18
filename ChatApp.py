import sys
import json
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
		self.serverSocket.bind(('', serverPort))

		while True:
			message, clientAddress = self.serverSocket.recvfrom(4096)
			# assume message is client registration
			name = message.decode()
			IP = clientAddress[0]
			port = clientAddress[1]
			self.addClient(name, IP, port)

	def broadcast(self):
		'''
		broadcast the table to all online clients
		'''

		for name, clientInfo in self.table.items():
			status = clientInfo['status']
			if status == 'yes':
				IP = clientInfo['IP']
				port = clientInfo['port']
				self.serverSocket.sendto(json.dumps(self.table).encode(), (IP, port))


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
		self.clientSocket.sendto(name.encode(), (serverIP, serverPort))
		message, serverAddress = self.clientSocket.recvfrom(4096)
		# assume message is the updated table
		self.updateTable(json.loads(message.decode()))

		print('>>> [Welcome, You are registered.]')
		input('>>>')

	def updateTable(self, table):
		self.table = table
		print('>>> [Client table updated.]')

	# client notified leave 

	def __del__(self):
		'''
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
	