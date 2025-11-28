import select
from threading import Thread
import utils
from message import Message
import json

class NodeServer(Thread):
    def __init__(self, node):
        Thread.__init__(self)
        self.node = node
        self.daemon = True
    
    def run(self):
        self.update()

    def update(self):
        self.connection_list = []
        self.server_socket = utils.create_server_socket(self.node.port)
        self.connection_list.append(self.server_socket)

        while self.node.daemon:
            (read_sockets, write_sockets, error_sockets) = select.select(
                self.connection_list, [], [], 5)
            if not (read_sockets or write_sockets or error_sockets):
                print('NS%i - Timed out'%self.node.id) #force to assert the while condition 
            else:
                for read_socket in read_sockets:
                    if read_socket == self.server_socket:
                        (conn, addr) = read_socket.accept()
                        self.connection_list.append(conn)
                    else:
                        try:
                            msg_stream = read_socket.recvfrom(4096)
                            for msg in msg_stream:
                                try:
                                    ms = json.loads(str(msg,"utf-8"))
                                    self.process_message(ms)
                                except:
                                    None
                        except:
                            read_socket.close()
                            self.connection_list.remove(read_socket)
                            continue
        
        self.server_socket.close()

    def process_message(self, msg):
        #TODO MANDATORY manage the messages according to the Maekawa algorithm (TIP: HERE OR IN ANOTHER FILE...)
        print("Node_%i receive msg: %s"%(self.node.id,msg))
        # Obtenemos los datos del mensaje
        msg_type = msg.get("msg_type", None)
        src = msg.get("src", None)
        data = msg.get("data", {})
        
        # Cada nodo puede emitir un voto a la vez
        # Si llega un REQUEST y no hemos votado, votamos.
        if msg_type == "REQUEST":
            if self.node.voted_for is None:
                self.node.voted_for = src
                print(f"Node_{self.node.id} votes for Node_{src}")
                reply = Message(
                    msg_type="REPLY",
                    src=self.node.id,
                    dest=src,
                    data={"ts_reply": self.node.lamport_ts}
                )
                self.node.client.send_message(reply, src)

            else: # Ya ha votado, encolamos
                self.node.request_queue.append(src)
                print(f"Node_{self.node.id} added in queue REQUEST from Node_{src}")

        elif msg_type == "REPLY":
            with self.node.reply_condition:
                if src not in self.node.reply_received:
                    self.node.reply_received.add(src)
                    print(f"Node_{self.node.id} got REPLY from Node_{src}")

                if len(self.node.reply_received) >= len(self.node.collegues):
                    self.node.reply_condition.notify()

        # Cuando un nodo sale de la SC manda un RELEASE para devolver el lock
        elif msg_type == "RELEASE":
            # Reiniciamos los votos
            if self.node.voted_for == src:
                print(f"Node_{self.node.id} frees vote from Node_{src}")
                self.node.voted_for = None

                if self.node.request_queue: # Quedan peticiones pendientes
                    next_id = self.node.request_queue.pop(0)
                    self.node.voted_for = next_id
                    print(f"Node_{self.node.id} votes for Node_{next_id} from queue")

                    reply = Message(
                        msg_type="REPLY",
                        src=self.node.id,
                        dest=next_id,
                        data={"ts_reply": self.node.lamport_ts}
                    )
                    self.node.client.send_message(reply, next_id)




 