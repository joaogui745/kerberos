import time

import AuthServer
import Client
import Service
import TicketServer

if __name__ == "__main__":
    # 1. Iniciar os servidores
    as_server = AuthServer()
    tgs_server = TicketServer()
    app_server = Service()
    
    # Definir como threads daemon para encerrarem quando o script principal terminar
    as_server.daemon = True
    tgs_server.daemon = True
    app_server.daemon = True
    
    as_server.start()
    tgs_server.start()
    app_server.start()
    
    time.sleep(1) # Dar um segundo para os servidores vincularem às portas
    
    # 2. Executar o fluxo do cliente
    client = Client("alice")
    
    # Phase 1
    tgt = client.request_as()
    
    # Phase 2
    service_ticket = client.request_tgs(tgt)
    
    # Phase 3
    client.request_service(service_ticket)
    
    print("\n[System] Kerberos flow completed successfully.")