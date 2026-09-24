import json
import socket
from protocol import encode, decode

host = '127.0.0.1'  # IP pré-configurado
port = 5000        # Porta pré-configurada


class ServerConnection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET,
                                    socket.SOCK_STREAM) #Socket IPv4 (AF_INET) usando protocolo TCP (SOCK_STREAM)
        # Permite reutilizar a porta rapidamente após encerrar o servidor
        self.server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )
        self.server.bind((self.host, self.port))

        # Buffer de recebimento por conexão. Necessário porque TCP é um
        # fluxo de bytes: duas mensagens enviadas em sequência podem chegar
        # coladas num único recv(), ou uma mensagem pode chegar picada em
        # vários recv(). Guardamos aqui o que sobrou de cada socket entre
        # uma chamada e outra de receive_message().
        self._buffers = {}

    def listen(self):
        self.server.listen()  # Servidor em modo de escuta
        print("Servidor aguardando jogadores...")

    def accept_player(self):
        """Aceita um jogador por vez.

        Diferente do listen() original (que guardava a conexão em
        self.conection), este método devolve a conexão para quem chamou,
        permitindo aceitar e manter várias conexões simultâneas — uma para
        cada jogador do duelo.
        """
        conection, address = self.server.accept()
        print(f"Cliente conectado: {address}")
        self._buffers[conection] = b''
        return conection, address

    def receive_message(self, conection):
        # Lê do socket até encontrar o delimitador '\n', usando o buffer
        # dessa conexão para não perder (nem misturar) bytes de mensagens
        # diferentes.
        buffer = self._buffers.get(conection, b'')
        while b'\n' not in buffer:
            pedaco = conection.recv(1024)
            if not pedaco:
                break
            buffer += pedaco

        linha, _, resto = buffer.partition(b'\n')
        self._buffers[conection] = resto

        message = linha.decode("utf-8")

        try:
            return decode(message)
        except json.JSONDecodeError:
            return None

    def send_message_to_player(
        self,
        conection,
        message_type,
        data=None
    ):
        message = encode(message_type, data)
        conection.sendall(message)
