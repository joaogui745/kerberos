import time

from AuthServer import AuthServer
from Client import Client
import Service
import TicketServer

if __name__ == "__main__":
    as_server = AuthServer()
    as_server.daemon = True

    as_server.start()

    time.sleep(3);

    joao : Client = Client("joaogui", "password123")
    
    joao.request_as();