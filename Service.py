import time
import zmq
import threading

from CryptoUtils import decrypt_json, encrypt_json

SERVICE_SECRET_KEY = "fAJHyqCDIsyyi+eTMVqgFjl7yM5ijOvcqXYJ7RlhHXs="

VALID_SERVICE_IDS = {"WEBCHAT", "COLOCAR_MAIUSCULO"}

class Service(threading.Thread):
    def __init__(self, port=5557):
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
        encrypted_ticket_service = request.get("ticket_service")
        encrypted_authenticator = request.get("authenticator")

        if not encrypted_ticket_service:
            raise Exception("Ticket de servico inexistente")

        if not encrypted_authenticator:
            raise Exception("Authenticator inexistente")

        print("[Service] Descriptografando ticket de servico...")
        ticket_service = decrypt_json(SERVICE_SECRET_KEY, encrypted_ticket_service)

        key_client_service = ticket_service.get("key_client_service")
        client_id_from_ticket = ticket_service.get("client_id")
        client_address_from_ticket = ticket_service.get("client_address")
        service_id = ticket_service.get("service_id")
        timestamp = ticket_service.get("timestamp")
        lifetime = ticket_service.get("lifetime")

        if not key_client_service or not client_id_from_ticket or not client_address_from_ticket or not service_id or timestamp is None or lifetime is None:
            raise Exception("Ticket de servico invalido")

        if service_id not in VALID_SERVICE_IDS:
            raise Exception("Servico desconhecido")
        
        timestamp = int(timestamp)
        lifetime = int(lifetime)
        print(f"[Service] Ticket service: Cliente: {client_id_from_ticket}, Key Client-Servico: {key_client_service}, timestamp: {timestamp}, lifetime: {lifetime}")

        now = int(time.time())

        if now > timestamp + lifetime:
            raise Exception("Ticket de serviço expirado")

        print("[Service] Descriptografando autenticador...")
        authenticator = decrypt_json(key_client_service, encrypted_authenticator)
        client_id_from_authenticator = authenticator.get("client_id")
        client_address_from_authenticator = authenticator.get("client_address")
        authenticator_timestamp = authenticator.get("timestamp")

        if not client_id_from_authenticator or not client_address_from_authenticator or authenticator_timestamp is None:
            raise Exception("Authenticator invalido")

        authenticator_timestamp = int(authenticator_timestamp)
        print(f"[Service] Authenticator: Cliente: {client_id_from_authenticator}, timestamp: {authenticator_timestamp}")

        if client_id_from_ticket != client_id_from_authenticator:
            raise Exception("Cliente do ticket diferente do cliente do autenticador")

        if client_address_from_ticket != client_address_from_authenticator:
            raise Exception("Endereco do ticket diferente do endereco do autenticador")

        if abs(now - authenticator_timestamp) > self.max_clock_skew:
            raise Exception("Authenticator expirado")
        
        encrypted_message = request.get("message")
        if not encrypted_message:
            raise Exception("Mensagem inexistente")
        
        print("[Service] Descriptografando mensagem do cliente...")
        message = decrypt_json(key_client_service, encrypted_message)

        service_response = self._handle_service_message(service_id, client_id_from_ticket, message)

        print("[Service] Criptografando prova de autenticacao...")
        response_authenticator = encrypt_json(key_client_service, { "timestamp": authenticator_timestamp + 1})

        response = {
            "status": "ok",
            "message": "Authorized",
            "payload": response_authenticator
        }

        if service_response is not None:
            response["message"] = service_response

        return response

    def _handle_service_message(self, service_id, client_id, message):
        if service_id == "WEBCHAT":
            print(f"[Service] {client_id}: {message}")
            return None

        if service_id == "COLOCAR_MAIUSCULO":
            upper_message = str(message).upper()
            print(f"[Service] {client_id}: {upper_message}")
            return upper_message

        raise Exception("Servico desconhecido")
