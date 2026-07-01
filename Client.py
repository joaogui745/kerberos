import zmq

class Client:
    def __init__(self, client_id):
        self.client_id = client_id
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ) # REQ = Socket de requisição

    def request_as(self, port=5555):
        print(f"\n[Client] 1. Requesting TGT from AS (Port {port})...")
        self.socket.connect(f"tcp://localhost:{port}")
        
        self.socket.send_json({"client_id": self.client_id, "service": "TGS"})
        response = self.socket.recv_json()

        print(f"[Client] AS Response: {response}")
        self.socket.disconnect(f"tcp://localhost:{port}")
        
        # TODO: Descriptografar a resposta com a senha do usuário para obter TGT e Chave de Sessão

        return response.get("tgt")

    def request_tgs(self, tgt, port=5556):
        print(f"\n[Client] 2. Requesting Service Ticket from TGS (Port {port})...")
        self.socket.connect(f"tcp://localhost:{port}")
        
        # TODO: Construir o Autenticador (ID + Timestamp) criptografado com a Chave de Sessão

        self.socket.send_json({"tgt": tgt, "authenticator": "encrypted_auth_data"})
        response = self.socket.recv_json()
        print(f"[Client] TGS Response: {response}")
        self.socket.disconnect(f"tcp://localhost:{port}")
        
        return response.get("service_ticket")

    def request_service(self, service_ticket, port=5557):
        print(f"\n[Client] 3. Requesting access to Service (Port {port})...")
        self.socket.connect(f"tcp://localhost:{port}")
        
        # TODO: Construir novo Autenticador criptografado com a Chave de Sessão do Serviço

        self.socket.send_json({"service_ticket": service_ticket, "authenticator": "encrypted_auth_data_2"})
        response = self.socket.recv_json()
        print(f"[Client] Service Response: {response}")
        self.socket.disconnect(f"tcp://localhost:{port}")
