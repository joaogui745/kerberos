import time
import zmq
import json

from CryptoUtils import encrypt_json, decrypt_json, derive_kerberos_key


class Client:
    def __init__(self, client_id, password):
        self.client_id = client_id
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)

        self.session_key = derive_kerberos_key(password, client_id)
        self.client_tgs_key = None
        self.session_key_service = None
        self.service_ticket = None

    def request_as(self, port=5555):
        print(f"\n[Cliente] Solicitando Ticket ao AS na porta {port}...")

        if self.session_key is None:
            raise Exception("Cliente não possui chave configurada.")

        self.socket.connect(f"tcp://localhost:{port}")

        request = {
            "client_id": self.client_id,
            "service": "auth_service",
            "timestamp": int(time.time())
        }

        self.socket.send_json(request)

        response = self.socket.recv_json()

        self.socket.disconnect(f"tcp://localhost:{port}")

        if response.get("status") != "ok":
            raise Exception(response.get("message"))

        payload = response.get("payload")
        print(f"[Cliente] Payload recebido: Tamanho da cifra: {len(payload["ciphertext"])}")

        decrypted_response = decrypt_json(self.session_key, payload)

        # Mostrar campos principais da resposta decifrada
        self.client_tgs_key = decrypted_response.get("client_tgs_key")
        print(f"[Cliente] Chave Cliente-TGS: {self.client_tgs_key}")
        print(f"[Cliente] ID TGS: {decrypted_response.get('tgs_id')}, timestamp: {decrypted_response.get('timestamp')}, lifetime: {decrypted_response.get('lifetime')}")

        # Mostrar metadados do ticket TGS (permanece cifrado para o TGS)
        tgs_ticket = decrypted_response.get('tgs_ticket')
        print(f"[Cliente] TGS ticket: Tamanho da cifra:  {len(tgs_ticket["ciphertext"])}")

        return decrypted_response.get("tgs_ticket")

    def request_tgs(self, tgt, session_key_tgs=None, service_id="service1", port=5556):
    
        print(f"\n[Cliente] 2. Solicitando Ticket de Serviço ao TGS (Porta {port})...")

        if session_key_tgs is not None:
            self.session_key_tgs = session_key_tgs

        if self.session_key_tgs is None:
            raise Exception("Cliente não possui K_c_tgs. Obtenha a chave no AS.")

        self.socket.connect(f"tcp://localhost:{port}")

        now = int(time.time())

        authenticator_payload = {
            "client_id": self.client_id,
            "timestamp": now
        }

        encrypted_authenticator = encrypt_json(
            self.session_key_tgs,
            authenticator_payload
        )

        request = {
            "service_id": service_id,
            "tgt": tgt,
            "authenticator": encrypted_authenticator
        }

        self.socket.send_json(request)

        response = self.socket.recv_json()

        print(f"[Cliente] Resposta do TGS: {response}")

        self.socket.disconnect(f"tcp://localhost:{port}")

        if response["status"] != "ok":
            raise Exception(response["message"])

        decrypted_response = decrypt_json(
            self.session_key_tgs,
            response["encrypted_response"]
        )

        self.session_key_service = decrypted_response["session_key_service"]
        self.service_ticket = decrypted_response["ticket_service"]

        print("[Cliente] Ticket de serviço recebido com sucesso.")
        print("[Cliente] K_c_v obtida com sucesso.")

        return self.service_ticket

    def request_service(self, service_ticket, port=5557):
        print(f"\n[Cliente] 3. Solicitando acesso ao Serviço (Porta {port})...")

        self.socket.connect(f"tcp://localhost:{port}")

        self.socket.send_json({
            "service_ticket": service_ticket,
            "authenticator": "encrypted_auth_data_2"
        })

        response = self.socket.recv_json()

        print(f"[Cliente] Resposta do Serviço: {response}")

        self.socket.disconnect(f"tcp://localhost:{port}")