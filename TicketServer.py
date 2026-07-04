import time
import zmq
import threading

from CryptoUtils import (
    TGS_SECRET_KEY,
    SERVICE_KEYS,
    generate_key,
    encrypt_json,
    decrypt_json
)


class TicketServer(threading.Thread):
    def __init__(self, port=5556):
        super().__init__()
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://*:{self.port}")

        
        self.max_clock_skew = 300

    def run(self):
        print(f"[TGS] Listening on port {self.port}...")

        while True:
            request = self.socket.recv_json()
            print(f"[TGS] Received: {request}")

            try:
                response = self.handle_request(request)
            except Exception as error:
                response = {
                    "status": "error",
                    "message": str(error)
                }

            self.socket.send_json(response)

    def handle_request(self, request):

        service_id = request["service_id"]
        encrypted_tgt = request["tgt"]
        encrypted_authenticator = request["authenticator"]

        if service_id not in SERVICE_KEYS:
            raise Exception("Servico desconhecido")

        
        tgt = decrypt_json(TGS_SECRET_KEY, encrypted_tgt)

        client_id_from_tgt = tgt["client_id"]
        session_key_client_tgs = tgt["session_key_tgs"]
        tgt_timestamp = int(tgt["timestamp"])
        tgt_lifetime = int(tgt["lifetime"])

        now = int(time.time())

        if now > tgt_timestamp + tgt_lifetime:
            raise Exception("Ticket_tgs expirado")

        authenticator = decrypt_json(
            session_key_client_tgs,
            encrypted_authenticator
        )

        client_id_from_authenticator = authenticator["client_id"]
        authenticator_timestamp = int(authenticator["timestamp"])

        #
        if client_id_from_tgt != client_id_from_authenticator:
            raise Exception("Cliente do TGT diferente do cliente do autenticador")

        
        if abs(now - authenticator_timestamp) > self.max_clock_skew:
            raise Exception("Authenticator_c expirado ou invalido")

        
        session_key_client_service = generate_key()

        
        ticket_service_payload = {
            "client_id": client_id_from_tgt,
            "service_id": service_id,
            "session_key_service": session_key_client_service,
            "timestamp": now,
            "lifetime": 300
        }

        service_secret_key = SERVICE_KEYS[service_id]

        encrypted_ticket_service = encrypt_json(
            service_secret_key,
            ticket_service_payload
        )

        
        response_payload = {
            "session_key_service": session_key_client_service,
            "service_id": service_id,
            "timestamp": now,
            "ticket_service": encrypted_ticket_service
        }

        encrypted_response = encrypt_json(
            session_key_client_tgs,
            response_payload
        )

        return {
            "status": "ok",
            "encrypted_response": encrypted_response
        }
