import socket
import json
from protocol import encode, decode

class PlayerConection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.player = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.player.connect((self.host, self.port))
        self._buffer = b''

    def wait_message(self):
        while b'\n' not in self._buffer:
            pedaco = self.player.recv(1024)

            if not pedaco:
                return None

            self._buffer += pedaco

        linha, _, resto = self._buffer.partition(b'\n')
        self._buffer = resto

        mensagem = linha.decode('utf-8')

        print(f"Resposta do servidor: {mensagem}")

        try:
            return decode(mensagem)
        except (json.JSONDecodeError, TypeError):
            print("Mensagem JSON inválida.")
            return None

    def send_message_to_server(self, message_type, data=None):
        message = encode(message_type, data)
        self.player.sendall(message)