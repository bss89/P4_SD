	Commands

	uv run main.py
  
-----------------------------------------------------------------------------------------------------
						FUNCTIONAL DESCRIPTION 
-----------------------------------------------------------------------------------------------------

This project implements Maekawa’s distributed mutual exclusion algorithm using TCP sockets and Lamport timestamps (lamport_ts).

A group of nodes simulate a distributed system where every node can request access to a shared critical section (CS).  
To ensure mutual exclusion, each node must obtain permission (a vote) from all members of its quorum (a subset of nodes with which it communicates directly).

When a node wants to enter the critical section makes the following steps:
  1. It broadcasts a REQUEST message to all nodes in its quorum.  
  2. Each node can vote only one vote at a time. If it hasn’t voted yet, it sends back a REPLY. Otherwise, it postpones the request until it becomes free.  
  3. When the requester receives a REPLY from every quorum member (subset of 2 nodes), it enters the critical section.  
  4. After finishing, it sends a RELEASE message to free all the votes it received, allowing others to enter.

-----------------------------------------------------------------------------------------------------
						CODE STRUCTURE
-----------------------------------------------------------------------------------------------------

- main.py  
  Initializes the MaekawaMutex class, creates all nodes, and starts the execution.

- maekawaMutex.py 
  Manages the creation of all node.py instances. Manages their setup and launches each node thread. Represents the global 
  control of the algorithm.

- node.py 
  Implements the full node logic for Maekawa’s mutual exclusion, including:
  Lamport timestamp (lamport_ts)
  Quorum membership (collegues)
  Voting state (voted_for)
  Request queue for postponed votes (request_queue)
  Synchronization via Condition() (reply_condition)
  Tracking of received votes (reply_received)
  Critical-section state (RELEASED, REQUESTED, HELD)
  request_access() — sends REQUESTs and waits for all votes
  release_access() — sends RELEASE and resets state
  
  The main loop simulates the node repeatedly requesting, entering, and releasing the critical section.All messages are created 
  using the Message class and sent through NodeSend.

- nodeServer.py  
  Thread that listens for incoming TCP messages.  
  Upon receiving a REQUEST, REPLY, or RELEASE message, it updates the node’s local state according to Maekawa’s algorithm.

- nodeSend.py  
  Manages the TCP connections and messages. 

- message.py 
  Defines the structure of the messages exchanged between nodes. Each message includes a type (REQUEST, REPLY, RELEASE) 
  a source, a destination, a Lamport timestamp, and data.

- config.py
  Manages the global configuration.

- utils.py  
  Auxilliary functions to create the server and sockets.


