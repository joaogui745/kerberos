import zmq
import threading
import time

from CryptoUtils import TGS_SECRET_KEY, encrypt_json, generate_key


SESSION_KEYS = {
    "joaogui": "KI0qrlG3Mn7QoWIdUnHAbB0oVIhcV1ivKQth1cJ2Nu4="
}

TGS_ID = "FOO"

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

                print(f"[AS] Cliente: {client_id}, timestamp: {request.get('timestamp')}")

                client_key = SESSION_KEYS[client_id]
                client_tgs_key = generate_key()
                now = int(time.time())

                ticket_tgs_payload = {
                    "client_tgs_key": client_tgs_key,
                    "client_id" : client_id,
                    "client_address" : "foo",
                    "tgs_id" : TGS_ID,
                    "timestamp": now,
                    "lifetime": 300
                }

                tgs_ticket = encrypt_json(TGS_SECRET_KEY, ticket_tgs_payload)

                response_payload = {
                    "client_tgs_key": client_tgs_key,
                    "tgs_id" : TGS_ID,
                    "timestamp": now,
                    "lifetime" : 300,
                    "tgs_ticket": tgs_ticket,
                }

                encrypted_response = encrypt_json(client_key, response_payload)

                response = {
                    "status": "ok",
                    "payload": encrypted_response
                }
            except Exception as error:
                response = {
                    "status": "error",
                    "message": str(error)
                }

            self.socket.send_json(response)