import zmq
import threading

class TicketServer(threading.Thread):
    def __init__(self, port=5556):
        super().__init__()
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://*:{self.port}")

    def run(self):
        print(f"[TGS] Listening on port {self.port}...")
        while True:
            request = self.socket.recv_json()
            print(f"[TGS] Received: {request}")
            
            # TODO: Descriptografar o TGT, verificar o timestamp do Autenticador, emitir o Ticket de Serviço
            
            response = {"status": "ok", "service_ticket": "encrypted_service_ticket"}
            self.socket.send_json(response)
