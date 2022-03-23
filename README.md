# SimpleChatApplication

Chenqi Wang

cw3277



### Run

**Server**

We run the server first: open an individual window, and execute the following command

```
python3 ChatApp.py -s 1024
```

where the last argument \<port\> is in the range of 1024 - 65535.

**Client**

Then for each client, open an individual window, and execute 

```
python3 ChatApp.py -c <name> <server-ip> <server-port> <client-port> 
```

e.g.

```
python3 ChatApp.py -c Alice 127.0.0.1 1024 2000
```

```
python3 ChatApp.py -c Bob 127.0.0.1 1024 3000
```

```
python3 ChatApp.py -c Carol 127.0.0.1 1024 4000
```

```
python3 ChatApp.py -c Dave 127.0.0.1 1024 5000
```

where \<name\> is a string without spaces, and \<server-port\>, \<client-port\> are in the range of 1024 - 65535.



### Implementation

We designed and implemented two classes: Server and Client, for the server and clients in the simple chat application respectively.

#### **Server**

For the Server class, we implemented 8 methods:

- \_\_init\_\_(self, serverPort): the constructor. Create an UDP socket to receive requests or ack from clients, and call relative methods to handle them. The server can also use the UDP socket to send messages.
- broadcast(self): broadcast the table to all online clients.
- addClient(self, name, IP, port): register a client in the table, and broadcast the new table.
- logBackClient(self, name): log back a client, send offline messages if there are, change the client's status in the table to be online, and broadcast the new table.
- checkStatusRequest(self, name): send a request to a client to check whether it's active (online) or not.
- saveMessage(self, name, message, requestName): when the intended recipient is offline, the server save the messages in the corresponding file.
- receiveACKs(self): For channel message, the server needs to receive acks from all online clients (except the sender). This is the method that listens to those acks. We create an individual listening thread to run this method.
- handleChannelMessage(self, senderName, message): handle channel message. Send the message to all online clients (except the sender), and save the message for all offline messages. For clients that does not send back an ack, first check their status. If inactive (offline), update and broadcast the table, and then save the message in the corresponding files.

#### **Client**

For the Client class, we implemented 7 methods:

- \_\_init\_\_(self, name, serverIP, serverPort, port): the constructor. Create an UDP socket to send and receive messages, try to complete the registration. And if the registration is successful, create a listening thread that is responsible for receiving incoming messages, so the main thread can handle user inputs simultaneously. 

- listen(self): the listening thread runs this method, to listen to incoming messages and handle them appropriately.

- send(self, name, message): one client sends message to another client directly.

  ​	implementation idea: we have two threads: the main thread (for user input command) and 
  ​	the listening thread (for receiving messages from the server and other clients). In the main 
  ​	thread, we first set self.ack = False, and then send the message to the target client, wait 
  ​	for 500 msec, and then check whether the listening thread receive the ack and set self.ack = True: 
  ​	if so, the message is received successfully; otherwise timeout and we send the message to the
  ​	server.

- deregistration(self, name): notified leave. Send the de-registration request to the server and except an ack, if timeout, retry for 5 times.

- saveMessageRequest(self, name, message): save-message request. Send the request to the server and except an ack, if timeout, retry for 5 times.

- logBack(self, name): If the client exited via notified leave, it can log back by sending a log-back request to the server.

- sendAll(self, message): channel message - group chat. Send the channel message to the server and the server would handel it appropriately. It also excepts an ack from the server, if timeout, retry for 5 times.



#### **Table**

The clients and the server would maintain a table with information of clients, and the table is designed to be in the format of 

```python
{ <name> : {'IP' : <IP>, 'port' : <port>, 'name' : <name>, 'status' : <status>} }
```

i.e. a dict, where the value of each entry is also a dict recording the IP, port , name and status of a client, and each client's name serves as the corresponding key. We use name as the key to access records faster.

status = 'yes' or 'no' (indicating the client is online or offline respectively)



#### **Message**

##### message encoding & decoding 

encoding: raw message is a Python Object, and encoded with json.dumps(message).encode() to be a bytes object, so it can be sent into a socket.

decoding: a bytes object read from the socket is decoded to be a Python Object by json.loads(message.decode()). 

##### **message types:**

message is in the format of [\<type\>, \<message\> (optional), \<name\> (optional), \<table\> (optional), ...]

\<type\> =

- 0: ordinary message. e.g. [0, "Hello"]
- 1: ack. [1, \<name\> (optional)], when in channel message, the client sends an ack to the server, its name also be included in the message. Except this case, the message is just [1].
- 2: a table with information of clients. [2, \<table\>]
- 3: client registration request. [3, \<name\>]
- 4: client registration request rejected. [4] 
- 5: save-message request. [5, \<message\>, \<name\>, \<requestName\>], where \<requestName\> is the name of the client that sends the save-message request
- 6: client deregistration request. [6, \<name\>]
- 7: client log-back request. [7, \<name\>]
- 8: save-message error message from the server. [8, \<name\>, \<table\>], where \<name\> is the name of the intended recipient.
- 9: offline messages. [9, \<offline messages\>]
- 10: group chat message (i.e. channel message) from a client to the server. [10, \<sender name\>, \<message\>]
- 11: channel message from server to a client. [11, \<channel message\>]
- 12: check status request. [12]



#### **Additional Functions**

- checkIP(IP): check whether IP is in the format of a.b.c.d, and each of a, b, c, d is an integer in the range of [0, 255] that contains no leading zeros.
- checkPort(port): check whether port is in the range of [1024, 65535].



### User Input

The functionalities and their corresponding user input commands of the simple chat application are: 

1. client registration 

   ```
   python3 ChatApp.py -c <name> <server-ip> <server-port> <client-port> 
   ```

2. direct one-to-one chat between clients

   ```
   send <name> <message>
   ```

3. client deregistration (i.e. notified leave)

   ```
   dereg <name>
   ```

4. client log-back 

   ```
   reg <name>
   ```

5. offline chat

   When the client logs back, the server automatically send saved offline messages to it if there are.

6. group chat (i.e. channel message)

   ```
   send_all <message>
   ```



### Test

#### Test-case 1:

1. start server
2. start client x(the table should be sent from server to x)
3. start client y(the table should be sent from server to x and y)
4. start client z(the table should be sent from server to x and y and z)
5. chat x -> y, y->z, ... , x ->z (All combinations)
6. dereg x (the table should be sent to y, z. x should receive ’ack’)
7. chat y->x (this should fail and message should be sent to server, and message has to be saved for x in the server)
8. chat z->x (same as above)
9. reg x (messages should be sent from server to x, x’s status has to be broadcasted to all the other clients)
10. x, y, z : exit

Start 1: (use 4 different windows for each of the following 4 commands respectively)
python3 ChatApp.py -s 1024
python3 ChatApp.py -c Alice 127.0.0.1 1024 2000
python3 ChatApp.py -c Bob 127.0.0.1 1024 3000
python3 ChatApp.py -c Carol 127.0.0.1 1024 4000

Output 1:
Alice:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> send Bob Hello
\>\>\> Message received by Bob.
\>\>\> send Carol Hello
\>\>\> Message received by Carol.
\>\>\> Bob: Hello!
\>\>\> Carol: Hello!!
\>\>\> dereg Alice
\>\>\> You are Offline. Bye.
\>\>\> reg Alice 
\>\>\> You Have Messages
\>\>\> Bob: 1647982516.0493078 Hi
\>\>\> Carol: 1647982521.593001 Hi!
\>\>\> Client table updated.

Bob:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Alice: Hello
\>\>\> send Alice Hello!
\>\>\> Message received by Alice.
\>\>\> send Carol Hello!
\>\>\> Message received by Carol.
\>\>\> Carol: Hello!!
\>\>\> Client table updated.
\>\>\> send Alice Hi
\>\>\> No ACK from Alice, message sent to server.
\>\>\> Messages received by the server and saved
\>\>\> Client table updated.

Carol:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Alice: Hello
\>\>\> Bob: Hello!
\>\>\> send Alice Hello!!
\>\>\> Message received by Alice.
\>\>\> send Bob Hello!!
\>\>\> Message received by Bob.
\>\>\> Client table updated.
\>\>\> send Alice Hi!
\>\>\> No ACK from Alice, message sent to server.
\>\>\> Messages received by the server and saved
\>\>\> Client table updated.

#### Test-case 2:

1. start server
2. start client x (the table should be sent from server to x )
3. start client y (the table should be sent from server to x and y)
4. dereg y
5. server exit
6. send message x-> y (will fail with both y and server, so should make 5 attempts and exit)

Start 2:
python3 ChatApp.py -s 1024
python3 ChatApp.py -c Alice 127.0.0.1 1024 2000
python3 ChatApp.py -c Bob 127.0.0.1 1024 3000

Exit 2:
server: ctrl + c

Output 2:
Alice:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> send Bob Hello
\>\>\> No ACK from Bob, message sent to server.
\>\>\> Server not responding
\>\>\> Exiting

Bob:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> dereg Bob
\>\>\> You are Offline. Bye.

#### Test-case 3:

1. start server
2. start client x (the table should be sent from server to x )
3. start client y (the table should be sent from server to x and y)
4. start client z (the table should be sent from server to x , y and z)
5. send group message x-> y,z

Start 3:
python3 ChatApp.py -s 1024
python3 ChatApp.py -c Alice 127.0.0.1 1024 2000
python3 ChatApp.py -c Bob 127.0.0.1 1024 3000
python3 ChatApp.py -c Carol 127.0.0.1 1024 4000

Output 3:
Alice:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> send_all Welcome to Channel
\>\>\> Message received by Server.

Bob:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Channel Message Alice: Welcome to Channel

Carol:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Channel Message Alice: Welcome to Channel

#### Test-case 4:

1. start server
2. start client x(the table should be sent from server to x)
3. start client y(the table should be sent from server to x and y)
4. start client z(the table should be sent from server to x and y and z)
5. dereg x
6. send group message y -> x, z
7. chat y -> x
8. chat z -> x
9. reg x

Start 4:
python3 ChatApp.py -s 1024
python3 ChatApp.py -c Alice 127.0.0.1 1024 2000
python3 ChatApp.py -c Bob 127.0.0.1 1024 3000
python3 ChatApp.py -c Carol 127.0.0.1 1024 4000

Output 4:
Alice:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> dereg Alice
\>\>\> You are Offline. Bye.
\>\>\> reg Alice
\>\>\> You Have Messages
\>\>\> Channel Message Bob: 1647987871.428575 Welcome to Channel
\>\>\> Bob: 1647987884.8317409 Hello
\>\>\> Carol: 1647987890.298325 Hello!!
\>\>\> Client table updated.

Bob:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> send_all Welcome to Channel
\>\>\> Message received by Server.
\>\>\> send Alice Hello
\>\>\> No ACK from Alice, message sent to server.
\>\>\> Messages received by the server and saved
\>\>\> Client table updated.

Carol:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Channel Message Bob: Welcome to Channel
\>\>\> send Alice Hello!!
\>\>\> No ACK from Alice, message sent to server.
\>\>\> Messages received by the server and saved
\>\>\> Client table updated.

#### Test-case 5:

1. start server
2. start client x
3. start client y
4. start client z
5. start client w
6. dereg x
7. dereg y
8. chat z->x
9. dereg z
10. send group message w -> x, y, z 
11. chat w -> x
12. chat w -> y
13. reg x
14. reg y
15. chat y -> z
16. reg z

Start 5:
python3 ChatApp.py -s 1024
python3 ChatApp.py -c Alice 127.0.0.1 1024 2000
python3 ChatApp.py -c Bob 127.0.0.1 1024 3000
python3 ChatApp.py -c Carol 127.0.0.1 1024 4000
python3 ChatApp.py -c Dave 127.0.0.1 1024 5000

Alice:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> dereg Alice
\>\>\> You are Offline. Bye.
\>\>\> reg Alice
\>\>\> You Have Messages
\>\>\> Carol: 1647988960.81082 Hello
\>\>\> Channel Message Dave: 1647988985.398539 Welcome to Channel
\>\>\> Dave: 1647989015.692829 Hello!!
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.

Bob:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> dereg Bob
\>\>\> You are Offline. Bye.
\>\>\> reg Bob
\>\>\> You Have Messages
\>\>\> Channel Message Dave: 1647988985.399373 Welcome to Channel
\>\>\> Dave: 1647989030.010526 Hello!!
\>\>\> Client table updated.
\>\>\> send Carol Hi 
\>\>\> No ACK from Carol, message sent to server.
\>\>\> Messages received by the server and saved
\>\>\> Client table updated.

Carol:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> send Alice Hello 
\>\>\> No ACK from Alice, message sent to server.
\>\>\> Messages received by the server and saved
\>\>\> dereg Carol
\>\>\> You are Offline. Bye.
\>\>\> reg Carol
\>\>\> You Have Messages
\>\>\> Channel Message Dave: 1647988985.3998778 Welcome to Channel
\>\>\> Bob: 1647989068.503232 Hi
\>\>\> Client table updated.

Dave:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> send_all Welcome to Channel
\>\>\> Message received by Server.
\>\>\> send Alice Hello!!
\>\>\> No ACK from Alice, message sent to server.
\>\>\> Messages received by the server and saved
\>\>\> send Bob Hello!!
\>\>\> No ACK from Bob, message sent to server.
\>\>\> Messages received by the server and saved
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.

#### Test-case 6:

1. start server
2. start client x
3. chat x -> x

Start 6:
python3 ChatApp.py -s 1024
python3 ChatApp.py -c Alice 127.0.0.1 1024 2000

Output 6:
Alice:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> send Alice Hello, Alice!
\>\>\> Alice: Hello, Alice!

#### Test-case 7:

1. start server
2. start client x
3. start client y
4. x dereg y

Start 7:
python3 ChatApp.py -s 1024
python3 ChatApp.py -c Alice 127.0.0.1 1024 2000
python3 ChatApp.py -c Bob 127.0.0.1 1024 3000

Output 7:
Alice:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> dereg Bob
\>\>\> invalid name for de-registration, should be Alice

Bob:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.

#### Test-case 8:

1. start server
2. start client x with name 'Alice'
3. start client y with the same name 'Alice'

Start 8:
python3 ChatApp.py -s 1024
python3 ChatApp.py -c Alice 127.0.0.1 1024 2000
python3 ChatApp.py -c Alice 127.0.0.1 1024 3000

Output 8:
Alice (port 2000):
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.

Alice (port 3000):
\>\>\> Registration request rejected - name Alice used

#### Test-case 9: 

1. start server
2. start client x
3. start client y
4. start client z
5. server exit
6. dereg x
7. chat y -> z

Start 9:
python3 ChatApp.py -s 1024
python3 ChatApp.py -c Alice 127.0.0.1 1024 2000
python3 ChatApp.py -c Bob 127.0.0.1 1024 3000

Exit 9:
server: ctrl + c

Output 9:
Alice:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> dereg Alice
\>\>\> Server not responding
\>\>\> Exiting

Bob:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> send Carol Hello
\>\>\> Message received by Carol.

Carol:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Bob: Hello

#### Test-case 10:

1. start server
2. start client x
3. start client y
4. start client z
5. server exit
6. send group message x -> y, z

Start 10:
python3 ChatApp.py -s 1024
python3 ChatApp.py -c Alice 127.0.0.1 1024 2000
python3 ChatApp.py -c Bob 127.0.0.1 1024 3000
python3 ChatApp.py -c Carol 127.0.0.1 1024 4000

Exit 10:
server: ctrl + c

Output 10:
Alice:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> send_all Welcome to Channel
\>\>\> Server not responding.

Bob:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.

Carol:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.

#### Test-case 11:

1. start server
2. start client x
3. start client y
4. client y exits (via silent leave)
5. chat x -> y

Start 11:
python3 ChatApp.py -s 1024
python3 ChatApp.py -c Alice 127.0.0.1 1024 2000
python3 ChatApp.py -c Bob 127.0.0.1 1024 3000

Exit 11:
client y: ctrl + c

Output 11:
Alice:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> send Bob Hello
\>\>\> No ACK from Bob, message sent to server.
\>\>\> Client table updated.
\>\>\> Messages received by the server and saved

Bob:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.

#### Test-case 12:

1. start server
2. start client x
3. start client y
4. start client z
5. client x exits (via silent leave)
6. chat y -> z

Start 12:
python3 ChatApp.py -s 1024
python3 ChatApp.py -c Alice 127.0.0.1 1024 2000
python3 ChatApp.py -c Bob 127.0.0.1 1024 3000
python3 ChatApp.py -c Carol 127.0.0.1 1024 4000

Exit 12:
client x: close SSH window

Output 12:
Alice:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> Client table updated.

Bob:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Client table updated.
\>\>\> send Carol Hello
\>\>\> Message received by Carol.

Carol:
\>\>\> Welcome, You are registered.
\>\>\> Client table updated.
\>\>\> Bob: Hello