import time
import zmq
import threading

from CryptoUtils import (
    generate_key,
    encrypt_json,
    decrypt_json
)
from Service import SERVICE_SECRET_KEY, VALID_SERVICE_ID

TGS_SECRET_KEY = "IRpMmtvhXXphfL6MzrRMOOK1EB8jlwN82/Fza1I5j7I="


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

            try:
                response = self.handle_request(request)
            except Exception as error:
                response = {
                    "status": "error",
                    "message": str(error)
                }

            self.socket.send_json(response)

    def handle_request(self, request):

        service_id = request.get("service_id")
        encrypted_ticket_tgs = request.get("ticket_tgs")
        encrypted_authenticator = request.get("authenticator")

        if service_id != VALID_SERVICE_ID:
            raise Exception("Servico desconhecido")

        
        ticket_tgs = decrypt_json(TGS_SECRET_KEY, encrypted_ticket_tgs)

        client_id_from_ticket_tgs = ticket_tgs.get("client_id")
        client_address_from_ticket_tgs = ticket_tgs.get("client_address")
        key_client_tgs = ticket_tgs.get("key_client_tgs")
        ticket_tgs_timestamp = int(ticket_tgs.get("timestamp"))
        ticket_tgs_lifetime = int(ticket_tgs.get("lifetime"))
        print("[TGS] Descriptografando ticket TGS...")
        print(f"[TGS] Cliente recebido: {client_id_from_ticket_tgs}, Chave Client-TGS: {key_client_tgs}, timestamp: {ticket_tgs_timestamp}, lifetime: {ticket_tgs_lifetime}")

        now = int(time.time())

        if now > ticket_tgs_timestamp + ticket_tgs_lifetime:
            raise Exception("Ticket_tgs expirado")

        authenticator = decrypt_json(
            key_client_tgs,
            encrypted_authenticator
        )

        client_id_from_authenticator = authenticator.get("client_id")
        client_address_from_authenticator = authenticator.get("client_address")
        authenticator_timestamp = int(authenticator.get("timestamp"))
        print("[TGS] Descriptografando autenticador...")
        print(f"[TGS] Authenticator: Cliente: {client_id_from_authenticator}, timestamp: {authenticator_timestamp}")

        
        if client_id_from_ticket_tgs != client_id_from_authenticator:
            raise Exception("Cliente do TGT diferente do cliente do autenticador")
        
        if client_address_from_ticket_tgs != client_address_from_authenticator:
            raise Exception("Cliente do TGT diferente do cliente do autenticador 2")

        
        if abs(now - authenticator_timestamp) > self.max_clock_skew:
            raise Exception("Authenticator expirado ou invalido")

        
        key_client_service = generate_key()

        
        ticket_service_payload = {
            "key_client_service": key_client_service,
            "client_id": client_id_from_authenticator,
            "client_address" : client_address_from_authenticator,
            "service_id": service_id,
            "timestamp": now,
            "lifetime": 300
        }

        service_secret_key = SERVICE_SECRET_KEY

        encrypted_ticket_service = encrypt_json(
            service_secret_key,
            ticket_service_payload
        )

        
        response_payload = {
            "key_client_service": key_client_service,
            "service_id": service_id,
            "timestamp": now,
            "ticket_service": encrypted_ticket_service
        }

        encrypted_payload = encrypt_json(
            key_client_tgs,
            response_payload
        )

        return {
            "status": "ok",
            "payload": encrypted_payload
        }
