import zmq
import threading

class Service(threading.Thread):
    def __init__(self, port=5557):
        super().__init__()
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://*:{self.port}")

    def run(self):
        print(f"[Service] Listening on port {self.port}...")
        while True:
            request = self.socket.recv_json()
            print(f"[Service] Received: {request}")
            
            # TODO: Descriptografar o Ticket de Serviço, verificar o Autenticador, conceder acesso

            
            response = {"status": "access_granted", "data": "Welcome to the secure service!"}
            self.socket.send_json(response)
