import zmq
import threading

class AuthServer(threading.Thread):
    def __init__(self, port=5555):
        super().__init__()
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP) # Socket de resposta
        self.socket.bind(f"tcp://*:{self.port}")

    def run(self):
        print(f"[AS] Listening on port {self.port}...")
        while True:
            request = self.socket.recv_json() # Aguarda a requisição do cliente
            print(f"[AS] Received: {request}")
            
            # TODO: Verificar o usuário, gerar a chave de sessão e o TGT (Ticket Granting Ticket)

            response = {"status": "ok", "tgt": "encrypted_tgt_payload"}
            self.socket.send_json(response)