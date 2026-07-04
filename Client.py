import time
import zmq

from CryptoUtils import encrypt_json, decrypt_json


class Client:
    def __init__(self, client_id):
        self.client_id = client_id
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)

        self.session_key_tgs = None
        self.session_key_service = None
        self.service_ticket = None

    def request_as(self, port=5555):
        print(f"\n[Client] 1. Requesting TGT from AS (Port {port})...")

        self.socket.connect(f"tcp://localhost:{port}")

        self.socket.send_json({
            "client_id": self.client_id,
            "service": "TGS"
        })

        response = self.socket.recv_json()

        print(f"[Client] AS Response: {response}")

        self.socket.disconnect(f"tcp://localhost:{port}")

        return response.get("tgt")

    def request_tgs(self, tgt, session_key_tgs=None, service_id="service1", port=5556):
    
        print(f"\n[Client] 2. Requesting Service Ticket from TGS (Port {port})...")

        if session_key_tgs is not None:
            self.session_key_tgs = session_key_tgs

        if self.session_key_tgs is None:
            raise Exception("Cliente nao possui K_c_tgs. Obtenha a chave no AS.")

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

        print(f"[Client] TGS Response: {response}")

        self.socket.disconnect(f"tcp://localhost:{port}")

        if response["status"] != "ok":
            raise Exception(response["message"])

        decrypted_response = decrypt_json(
            self.session_key_tgs,
            response["encrypted_response"]
        )

        self.session_key_service = decrypted_response["session_key_service"]
        self.service_ticket = decrypted_response["ticket_service"]

        print("[Client] Ticket de servico recebido com sucesso.")
        print("[Client] K_c_v obtida com sucesso.")

        return self.service_ticket

    def request_service(self, service_ticket, port=5557):
        print(f"\n[Client] 3. Requesting access to Service (Port {port})...")

        self.socket.connect(f"tcp://localhost:{port}")

        self.socket.send_json({
            "service_ticket": service_ticket,
            "authenticator": "encrypted_auth_data_2"
        })

        response = self.socket.recv_json()

        print(f"[Client] Service Response: {response}")

        self.socket.disconnect(f"tcp://localhost:{port}")