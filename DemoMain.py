import time

from AuthServer import AuthServer
from Client import Client
from Service import Service
from TicketServer import TicketServer


CLIENT_ID = "joaogui"
PASSWORD = "password123"

AS_PORT = 5555
TGS_PORT = 5556
SERVICE_PORT = 5557


if __name__ == "__main__":
    as_server = AuthServer()
    as_server.daemon = True
    as_server.start()

    ticket_server = TicketServer()
    ticket_server.daemon = True
    ticket_server.start()

    service = Service()
    service.daemon = True
    service.start()

    time.sleep(1)

    try:
        client = Client(CLIENT_ID, PASSWORD)

        print("\n=== Fluxo de Demonstracao ===")
        print("1. Solicitando autenticacao ao AS")
        client.request_auth_server(AS_PORT)

        print("\n\n2. Solicitando ticket do TGS para WEBCHAT")
        client.request_tgs("WEBCHAT", TGS_PORT)
        print("\n\n3. Chamando WEBCHAT")
        client.request_service(SERVICE_PORT, "WEBCHAT", "Havia uma pedra no meio do caminho")

        print("\n\n4. Solicitando ticket do TGS para TOUPPERCASE")
        client.request_tgs("TOUPPERCASE", TGS_PORT)
        print("\n\n5. Chamando TOUPPERCASE")
        client.request_service(SERVICE_PORT, "TOUPPERCASE", "Minha terra tem palmeiras, onde canta o sabiá")

    except Exception as error:
        print(f"[DemoMain] {error}")