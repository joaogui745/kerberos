
"""
Este arquivo foi criado apenas para validar a implementação da segunda etapa
do protocolo Kerberos, simula a comunicação entre Cliente e TGS.

Aqui o Servidor de Autenticação (AS) é simulado manualmente, aí ele gera:
- K_c_tgs: chave de sessão entre Cliente e TGS;
- Ticket_tgs: ticket criptografado com a chave secreta do TGS.

Na versão final integrada do projeto, essa simulação tem que ser trocada
pela resposta real do AuthServer.py.
"""


import time

import Client
import TicketServer

from CryptoUtils import TGS_SECRET_KEY, generate_key, encrypt_json


if __name__ == "__main__":
    # Inicia somente o TGS.
    tgs_server = TicketServer.TicketServer()

    tgs_server.daemon = True
    tgs_server.start()

    time.sleep(1)

    # Simulando o que o AS deveria gerar.
    client_id = "alice"

    # Essa é a chave K_c_tgs.
    session_key_tgs = generate_key()

    # Esse é o Ticket_tgs.
    tgt_payload = {
        "client_id": client_id,
        "session_key_tgs": session_key_tgs,
        "timestamp": int(time.time()),
        "lifetime": 300
    }

    encrypted_tgt = encrypt_json(TGS_SECRET_KEY, tgt_payload)

    # Cliente pede ao TGS um ticket para acessar service1.
    client = Client.Client(client_id)

    service_ticket = client.request_tgs(
        tgt=encrypted_tgt,
        session_key_tgs=session_key_tgs,
        service_id="service1"
    )

    print("\n[System] Parte Cliente <-> TGS concluida com sucesso.")
    print("[System] Ticket_v recebido:")
    print(service_ticket)