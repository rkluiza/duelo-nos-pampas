import socket

host = '127.0.0.1' # IP do pré-configurado do servidor
port = 5000       # Mesma porta do servidor

class PlayerConection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        # Create: Cria o socket
        self.player = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect: Tenta se conectar ao servidor
        self.player.connect((self.host, self.port))

        # Buffer de recebimento: TCP é um fluxo de bytes, então duas
        # mensagens do servidor podem chegar coladas num único recv(), ou
        # uma mensagem pode chegar picada em vários recv(). Guardamos aqui
        # o que sobrou entre uma chamada e outra de wait_message().
        self._buffer = b''

    def wait_message(self):
        # Recv: Aguarda a resposta do servidor, lendo até achar o
        # delimitador '\n' que marca o fim de uma mensagem completa
        while b'\n' not in self._buffer:
            pedaco = self.player.recv(1024)
            if not pedaco:
                break
            self._buffer += pedaco

        linha, _, resto = self._buffer.partition(b'\n')
        self._buffer = resto

        server_feedback = linha.decode('utf-8')
        print(f"Resposta do servidor: {server_feedback}")

        return server_feedback

    def send_message_to_server(self, message):
        # Send: Envia dados (sempre convertidos para bytes com .encode()),
        # com \n marcando o fim da mensagem
        self.player.sendall((message + '\n').encode('utf-8'))
        print("Mensagem enviada para o servidor")
