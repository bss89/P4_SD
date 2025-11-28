from threading import Event, Thread, Timer, Condition
from datetime import datetime, timedelta
import time
from nodeServer import NodeServer
from nodeSend import NodeSend
from message import Message
import config
import random 

class Node(Thread):
    _FINISHED_NODES = 0
    _HAVE_ALL_FINISHED = Condition()

    def __init__(self,id):
        Thread.__init__(self)
        self.id = id
        self.port = config.port+id
        self.daemon = True
        self.lamport_ts = 0

        self.server = NodeServer(self) 
        self.server.start()

        #TODO OPTIONAL This is a simple way to define the collegues, but it is not the best way to do it.
        # You can implement a more complex way to define the collegues, but for now this is enough.
        if id % 2 == 0:
            self.collegues = list(range(0,config.numNodes,2))
        else:
            self.collegues = list(range(1,config.numNodes,2))

        self.client = NodeSend(self)    

        self.wakeupcounter = 0
        self.pending_replies = set()
        self.voted_for = None
        self.request_queue = []
        self.reply_received = set()          
        self.reply_condition = Condition()   
        self.in_critical_section = False 
        self.state = "RELEASED" 



    def do_connections(self):
        self.client.build_connection()

    def run(self):
        print("Run Node%i with the follows %s"%(self.id,self.collegues))
        self.client.start()

        
        #TODO MANDATORY Change this loop to simulate the Maekawa algorithm to 
        # - Request the lock
        # - Wait for the lock
        # - Release the lock
        # - Repeat until some condition is met (e.g. timeout, wakeupcounter == 3)    

        while self.wakeupcounter <= 2: # Termination criteria

            # Nodes with different starting times
            time_offset = random.randint(2, 8)
            time.sleep(time_offset) 

            # Enviamos el request a los compañeros del quorum
            self.state = "REQUESTED"
            self.lamport_ts += 1
            self.replies_pending = set(self.collegues) # Tantos compañeros haya, los esperaremos
            # Nos añadimos nosotros mismos si estamos en el quorum
            if self.id in self.collegues:
                self.reply_received.add(self.id)
                if self.id in self.pending_replies:
                    self.pending_replies.remove(self.id)

            req_msg = Message(
                msg_type="REQUEST",
                src=self.id,
                data={"ts_req": self.lamport_ts}
            )
            print(f"Node_{self.id} requests CS (TS={self.lamport_ts})")
            self.client.multicast(req_msg, self.collegues)

            # Espera hasta que todos los compañeros hayan respondido
            while len(self.replies_pending) > 0:
                time.sleep(0.5)
            
            # SC
            self.state = "HELD"
            self.in_critical_section = True
            print(f"Node_{self.id} ENTERS CS (TS={self.lamport_ts})")
            time.sleep(random.randint(1, 3))

            # Salimos de la SC y dejamos el lock
            self.state = "RELEASED"
            self.in_critical_section = False
            self.lamport_ts += 1
            rel_msg = Message(
                msg_type="RELEASE",
                src=self.id,
                data={"ts_rel": self.lamport_ts}
            )
            print(f"Node_{self.id} RELEASE CS (TS={self.lamport_ts})")
            self.client.multicast(rel_msg, self.collegues)

            # Reiniciamos las listas para la siguiente iteracion
            self.pending_replies = set()
            self.reply_received = set()

            # Control iteration 
            self.wakeupcounter += 1 
                
        # Wait for all nodes to finish
        print("Node_%i is waiting for all nodes to finish"%self.id)
        self._finished()

        print("Node_%i DONE!"%self.id)

    #TODO OPTIONAL you can change the way to stop
    def _finished(self): 
        with Node._HAVE_ALL_FINISHED:
            Node._FINISHED_NODES += 1
            if Node._FINISHED_NODES == config.numNodes:
                Node._HAVE_ALL_FINISHED.notify_all()

            while Node._FINISHED_NODES < config.numNodes:
                Node._HAVE_ALL_FINISHED.wait()