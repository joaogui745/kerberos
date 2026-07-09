import zmq
import threading
import time

from CryptoUtils import encrypt_json, generate_key
from TicketServer import TGS_SECRET_KEY


SESSION_KEYS = {
    "joaogui": "KI0qrlG3Mn7QoWIdUnHAbB0oVIhcV1ivKQth1cJ2Nu4=",
    "guilherme" : "BqZ4g3W8+rEXgz/Y07pes9yWWyyOqouO6xHXeanpkLQ=", 
    "sara" : "scd5k2H9j0UtypyZtFwoXQyLA2+zMiCxtoTRHCWu8mo="
}

TGS_ID = "server_tgs0"

class AuthServer(threading.Thread):
    def __init__(self, port=5555):
        super().__init__()
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP) # Socket de resposta
        self.socket.bind(f"tcp://*:{self.port}")

    def run(self):
        print(f"[AS] Escutando na porta {self.port}...")
        while True:
            request = self.socket.recv_json() # Aguarda a requisição do cliente
            
            try:
                if request["service"] != "auth_service":
                    raise Exception("Serviço indisponível")
    
                client_id = request["client_id"]

                if client_id not in SESSION_KEYS:
                    raise Exception("Cliente desconhecido")

                print(f"[AS] Cliente Recebido: {client_id}, timestamp: {request.get('timestamp')}")

                client_key = SESSION_KEYS[client_id]
                key_client_tgs = generate_key()
                now = int(time.time())

                ticket_tgs_payload = {
                    "key_client_tgs": key_client_tgs,
                    "client_id" : client_id,
                    "client_address" : "localhost",
                    "tgs_id" : TGS_ID,
                    "timestamp": now,
                    "lifetime": 300
                }

                ticket_tgs = encrypt_json(TGS_SECRET_KEY, ticket_tgs_payload)

                print("[AS] Criptografando payload do ticket TGS...")

                response_payload = {
                    "key_client_tgs": key_client_tgs,
                    "tgs_id" : TGS_ID,
                    "timestamp": now,
                    "lifetime" : 300,
                    "ticket_tgs": ticket_tgs,
                }

                encrypted_payload = encrypt_json(client_key, response_payload)

                response = {
                    "status": "ok",
                    "payload": encrypted_payload
                }
            except Exception as error:
                response = {
                    "status": "error",
                    "message": str(error)
                }

            self.socket.send_json(response)