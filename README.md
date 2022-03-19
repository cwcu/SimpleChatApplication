# SimpleChatApplication



### Table

The clients and the server would maintain a table with information of clients, and the table is designed to be in the format of 

```python
{ <name> : {'IP' : <IP>, 'port' : <port>, 'name' : <name>, 'status' : <status>} }
```

i.e. a dict, where the value of each entry is also a dict recording the IP, port ,name and status of a client, and each client's name serves as the corresponding key.

### Message

#### message encoding & decoding 

**encoding**: raw message is a Python Object, and encoded with json.dumps(message).encode() to be a bytes object, so it can be sent into a socket.

**decoding**: a bytes object read from the socket is decoded to be a Python Object by json.loads(message.decode()). 

#### **message types:**

message is in the format of [\<type\>, \<message\>, ...], \<type\> =

- 0: ordinary message. e.g. [0, "Hello"]
- 1: ack, where in this case the message = [1], i.e. no \<message\> part
- 2: a table with information of clients. [2, \<table\>]
- 3: client registration request. [3, \<name\>]
- 4: client registration request rejected. [4] 
- 5: message for the server to save. [5, \<message\>, \<name\>]

