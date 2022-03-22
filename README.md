# SimpleChatApplication



### Table

The clients and the server would maintain a table with information of clients, and the table is designed to be in the format of 

```python
{ <name> : {'IP' : <IP>, 'port' : <port>, 'name' : <name>, 'status' : <status>} }
```

i.e. a dict, where the value of each entry is also a dict recording the IP, port , name and status of a client, and each client's name serves as the corresponding key.

status = 'yes' or 'no' (indicating the client is online or offline)

### Message

#### message encoding & decoding 

**encoding**: raw message is a Python Object, and encoded with json.dumps(message).encode() to be a bytes object, so it can be sent into a socket.

**decoding**: a bytes object read from the socket is decoded to be a Python Object by json.loads(message.decode()). 

#### **message types:**

message is in the format of [\<type\>, \<message\>, \<name\>, \<table\>, ...]

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

