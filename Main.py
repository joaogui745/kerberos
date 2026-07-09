import time

from AuthServer import AuthServer
from Client import Client
from Service import Service 
from TicketServer import TicketServer

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


    time.sleep(1);

    joao : Client = Client("joaogui", "password123")
    
    joao.request_auth_server(5555)
    joao.request_tgs("WEBCHAT", 5556)
    joao.request_service(5557)