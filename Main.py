import time

from AuthServer import AuthServer
from Client import Client
from Service import Service 
from TicketServer import TicketServer

SERVICE_OPTIONS = {
    "1": "WEBCHAT",
    "2": "TOUPPERCASE",
}


def prompt_login():
    print("====== Login ======")
    client_id = input("ID do cliente: ").strip()
    password = input("Senha: ").strip()

    if not client_id:
        raise Exception("ID do cliente nao pode ser vazio")

    if not password:
        raise Exception("Senha nao pode ser vazia")

    return Client(client_id, password)


def prompt_service_selection():
    print("\n=== Menu de Servicos ===")
    for option, service_id in SERVICE_OPTIONS.items():
        print(f"{option} - {service_id}")
    print("0 - Sair")

    choice = input("Selecione um servico: ").strip()

    if choice == "0":
        return None

    service_id = SERVICE_OPTIONS.get(choice)
    if not service_id:
        raise Exception("Opcao de servico invalida")

    return service_id


def prompt_service_message(service_id):
    message = input(f"Mensagem para enviar ao {service_id}: ").strip()
    if not message:
        raise Exception(f"Mensagem nao pode ser vazia para {service_id}")

    return message


def request_tgs_with_retry(client, service_id, tgs_port, as_port):
    try:
        client.request_tgs(service_id, tgs_port)
        return
    except Exception as error:
        error_message = str(error)

        if "Ticket_tgs expirado" in error_message or "Authenticator expirado" in error_message:
            client.request_auth_server(as_port)
            client.request_tgs(service_id, tgs_port)
            return

        raise


def request_service_with_retry(client, service_id, service_port, tgs_port, as_port, message):
    try:
        client.request_service(service_port, service_id, message)
        return
    except Exception as error:
        error_message = str(error)

        if "Ticket de serviço expirado" in error_message:
            request_tgs_with_retry(client, service_id, tgs_port, as_port)
            client.request_service(service_port, service_id, message)
            return

        raise

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

    try:
        client = prompt_login()

        while True:
            service_id = prompt_service_selection()
            if service_id is None:
                print("Encerrando...")
                break

            if not client.has_valid_tgt():
                client.request_auth_server(5555)

            if not client.has_valid_service_ticket(service_id):
                request_tgs_with_retry(client, service_id, 5556, 5555)

            message = prompt_service_message(service_id)
            request_service_with_retry(client, service_id, 5557, 5556, 5555, message)
    except Exception as error:
        print(f"[Main] {error}")