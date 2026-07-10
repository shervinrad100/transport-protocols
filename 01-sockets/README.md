# 1. Sockets
Sockets sit on the **Session** layer of the OSI model. Since a session can be established with a whole range of device combinations, it means we have various types of sockets.

So let's look at everything that sits underneath it that allows this to work for the type of socket we want to build:

**Transport layer**
Sockets are built on TCP so this decision is already made for us. The TCP handshake establishes three channels:
- Write buffer
- Read buffer
- Control logic
When receiving data, we allocate a certain buffer. If the data size is larger, this layer deals with chunking it and sending it in batches. 

**Network layer**
Since we want to communicate with other devices over a network we will use IP protocol here. 
The `socket` package in python also allows us to use different address families (`AF_`). For example, AF_UNIX which allows us to connect to a UNIX file and stream bytes. 

**Data and Physical**
The data is routed over the network via your network card and over the network. This is the low level part of things. In order for us to get from a Python program to the network, we need to talk to the OS to route and deliver the packets. This is where the `socket` package comes in handy and bridges the gap. 

# The idea
Imagine this is a chat function on a gaming server. One server, clients connect to it and send their messages. The server then forwards this to the clients on that connection.

# How to run
Starting the server:
```
poetry run python3 gaming_server.py --ip 127.0.0.1 --port 5001
```

Starting the client:
```
poetry run python3 client.py --ip 127.0.0.1 --port 5001
```