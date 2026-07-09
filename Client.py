import time
import zmq
import json

from CryptoUtils import encrypt_json, decrypt_json, derive_kerberos_key

portas = {
    "server_tgs0" : 5556,
    "service1": 5557
}

class Client:
    def __init__(self, client_id, password):
        self.client_id = client_id
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)

        self.session_key = derive_kerberos_key(password, client_id)
        self.key_client_tgs = None
        self.tgs_id = None
        self.ticket_tgs = None
        self.ticket_tgs_meta = None

        self.key_client_service = {}
        self.ticket_service = {}
        self.ticket_service_meta = {}
        self.service_id = None

    def has_valid_service_ticket(self, service_id):
        ticket_service = self.ticket_service.get(service_id)
        ticket_meta = self.ticket_service_meta.get(service_id)

        if not ticket_service or not ticket_meta:
            return False

        timestamp = ticket_meta.get("timestamp")
        lifetime = ticket_meta.get("lifetime")

        if timestamp is None or lifetime is None:
            return False

        return int(time.time()) <= int(timestamp) + int(lifetime)

    def has_valid_tgt(self):
        if not self.ticket_tgs or not self.ticket_tgs_meta:
            return False

        timestamp = self.ticket_tgs_meta.get("timestamp")
        lifetime = self.ticket_tgs_meta.get("lifetime")

        if timestamp is None or lifetime is None:
            return False

        return int(time.time()) <= int(timestamp) + int(lifetime)

    def request_auth_server(self, porta):
        print(f"\n[Cliente] Solicitando Ticket ao AS na porta {porta}...")

        if not self.session_key:
            raise Exception("Cliente não possui chave configurada.")

        self.socket.connect(f"tcp://localhost:{porta}")

        request = {
            "client_id": self.client_id,
            "service": "auth_service",
            "timestamp": int(time.time())
        }

        self.socket.send_json(request)

        response = self.socket.recv_json()

        self.socket.disconnect(f"tcp://localhost:{porta}")

        if response.get("status") != "ok":
            raise Exception(response.get("message"))

        payload = response.get("payload")
        print(f"[Cliente] Payload recebido do AS: Tamanho da cifra: {len(payload.get("ciphertext"))}")

        print("[Cliente] Descriptografando payload do AS...")
        decrypted_response = decrypt_json(self.session_key, payload)

        self.key_client_tgs = decrypted_response.get("key_client_tgs")
        self.tgs_id = decrypted_response.get('tgs_id')
        self.ticket_tgs_meta = {
            "timestamp": decrypted_response.get("timestamp"),
            "lifetime": decrypted_response.get("lifetime"),
        }
        # Mostrar campos principais da resposta decifrada
        print(f"[Cliente] Chave Cliente-TGS: {self.key_client_tgs}")
        print(f"[Cliente] ID TGS: {self.tgs_id}, timestamp: {decrypted_response.get('timestamp')}, lifetime: {decrypted_response.get('lifetime')}")

        # Mostrar metadados do ticket TGS (permanece cifrado para o TGS)
        self.ticket_tgs = decrypted_response.get('ticket_tgs')
        print(f"[Cliente] Ticket TGS: Tamanho da cifra:  {len(self.ticket_tgs['ciphertext'])}")

        return

    def request_tgs(self, service_id, porta):
        if not self.tgs_id:
            raise Exception("Cliente não possui ID TGS")
        
        if not self.key_client_tgs:
            raise Exception("Cliente não possui chave Cliente-TGS")
        
        if not service_id:
            raise Exception("ID do serviço inexistente")
        
        print(f"\n[Cliente] Solicitando Ticket de Serviço ao TGS (Porta {porta})...")

        self.socket.connect(f"tcp://localhost:{porta}")

        now = int(time.time())

        authenticator_payload = {
            "client_id": self.client_id,
            "client_address" : "localhost",
            "timestamp": now
        }

        encrypted_authenticator = encrypt_json(
            self.key_client_tgs,
            authenticator_payload
        )

        request = {
            "service_id": service_id,
            "ticket_tgs": self.ticket_tgs,
            "authenticator": encrypted_authenticator
        }

        self.socket.send_json(request)

        response = self.socket.recv_json()

        self.socket.disconnect(f"tcp://localhost:{porta}")


        if response.get("status") != "ok":
            raise Exception(response.get("message"))

        decrypted_response = decrypt_json(
            self.key_client_tgs,
            response.get("payload")
        )

        print("[Cliente] Descriptografando payload do TGS...")

        service_id = decrypted_response.get("service_id")
        key_client_service = decrypted_response.get("key_client_service")
        ticket_service = decrypted_response.get("ticket_service")

        self.service_id = service_id
        self.key_client_service[service_id] = key_client_service
        self.ticket_service[service_id] = ticket_service
        self.ticket_service_meta[service_id] = {
            "timestamp": decrypted_response.get("timestamp"),
            "lifetime": decrypted_response.get("lifetime"),
        }

        print(f"[Cliente] Service ID: {service_id}, Chave Cliente-servico: {key_client_service}")
        print(f"[Cliente] Ticket service: Tamanho da cifra: {len(ticket_service.get('ciphertext'))}")
        return

    def request_service(self, porta, service_id=None, message=None):

        if not self.client_id:
            raise Exception("Cliente não possui ID configurado")

        if not service_id:
            service_id = self.service_id

        if not service_id:
            raise Exception("ID do serviço inexistente")

        if service_id not in self.ticket_service:
            raise Exception(f"Ticket de serviço inexistente para {service_id}")

        if service_id not in self.key_client_service:
            raise Exception(f"Chave Cliente-serviço inexistente para {service_id}")

        ticket_service = self.ticket_service[service_id]
        key_client_service = self.key_client_service[service_id]

        if service_id == "WEBCHAT" and not message:
            raise Exception("Mensagem inexistente para WEBCHAT")

        if service_id == "TOUPPERCASE" and not message:
            message = "Meu nome não é Johnny!"
        
        print(f"\n[Cliente] Solicitando acesso ao Serviço (Porta {porta})...")
        print(f"[Cliente] Service ID: {service_id}")
        print(f"[Cliente] Ticket service: Tamanho da cifra: {len(ticket_service.get('ciphertext'))}")

        self.socket.connect(f"tcp://localhost:{porta}")

        now = int(time.time())

        authenticator_payload = {
            "client_id": self.client_id,
            "client_address" : "localhost",
            "timestamp": now
        }

        encrypted_authenticator = encrypt_json(
            key_client_service,
            authenticator_payload
        )

        print(f"[Cliente] Authenticator service: Tamanho da cifra: {len(encrypted_authenticator.get('ciphertext'))}")

        encrypted_message = encrypt_json(
            key_client_service,
            message
        )

        print(f"[Cliente] Message service: Tamanho da cifra: {len(encrypted_message.get('ciphertext'))}")

        self.socket.send_json({
            "ticket_service": ticket_service,
            "authenticator": encrypted_authenticator,
            "message" : encrypted_message
        })

        response = self.socket.recv_json()
        self.socket.disconnect(f"tcp://localhost:{porta}")

        if response.get("status") != "ok":
            raise Exception(response.get("message"))

        service_message = response.get("message")
        if service_message and service_message != "Authorized":
            print(f"[Cliente] Resposta do serviço: {service_message}")

        print("[Cliente] Descriptografando prova de autenticacao do Service...")

        service_proof = decrypt_json(key_client_service, response.get("payload"))

        if service_proof.get("timestamp") != now + 1:
            raise Exception("Prova de autenticacao do Service invalida")

        print(f"[Cliente] Prova de autenticacao validada: timestamp {service_proof.get('timestamp')}")