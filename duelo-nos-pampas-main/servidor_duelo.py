import random
import time

from game_logic import DuelTimer
from server import ServerConnection

HOST = "127.0.0.1"
PORT = 5000
VITORIAS_NECESSARIAS = 2


def enviar_status(server, conexao, player_id, code, message):
    server.send_message_to_player(
        conexao,
        "STATUS",
        {
            "code": code,
            "player_id": player_id,
            "message": message,
        },
    )


def enviar_game(server, conexao, code, round_number=None):
    data = {"code": code}
    if round_number is not None:
        data["round"] = round_number

    server.send_message_to_player(conexao, "GAME", data)


def enviar_target(server, conexoes, target):
    for conexao in conexoes:
        server.send_message_to_player(
            conexao,
            "TARGET",
            {"target": target},
        )


def enviar_resultado(server, conexoes, resultado, placar):
    data = {
        **resultado,
        "score": {
            "player1": placar[1],
            "player2": placar[2],
        },
    }

    for conexao in conexoes:
        server.send_message_to_player(conexao, "RESULT", data)


def receber_tiro(server, conexao, player_id, duel):
    while True:
        mensagem = server.receive_message(conexao)

        if not mensagem:
            return False

        try:
            if mensagem["type"] != "SHOT":
                enviar_status(
                    server,
                    conexao,
                    player_id,
                    "ERROR",
                    "Mensagem inesperada. Era esperado um SHOT.",
                )
                continue

            tempo = mensagem["data"]["time"]
            tempo = float(tempo)

            # O servidor continua sendo responsável por registrar o tiro.
            # O cliente apenas mede o tempo e informa o valor.
            duel.register_shot(player_id, tempo)

            enviar_game(server, conexao, "SHOT_REGISTERED")
            return True

        except (KeyError, TypeError, ValueError):
            enviar_status(
                server,
                conexao,
                player_id,
                "ERROR",
                "Mensagem SHOT inválida.",
            )


def jogar_rodada(server, conexoes, duel, placar, numero_rodada):
    print(f"\n--- Rodada {numero_rodada} ---")
    print(f"Tempo-alvo: {duel.target_time:.2f}s")

    # Informa aos clientes que a rodada está pronta.
    for conexao in conexoes:
        enviar_game(server, conexao, "READY", numero_rodada)

    # Informa o tempo que deve ser estimado.
    enviar_target(server, conexoes, duel.target_time)

    # Pequeno intervalo antes da largada.
    time.sleep(random.uniform(1.0, 3.0))

    # Inicia a rodada nos dois clientes.
    for conexao in conexoes:
        enviar_game(server, conexao, "START", numero_rodada)

    # Recebe os dois tiros.
    for player_id, conexao in enumerate(conexoes, start=1):
        if not receber_tiro(server, conexao, player_id, duel):
            return False

    if not duel.all_players_shot():
        return False

    resultado = duel.get_result()

    if resultado is None:
        return False

    vencedor = resultado["winner"]

    if vencedor in (1, 2):
        placar[vencedor] += 1

    enviar_resultado(server, conexoes, resultado, placar)

    print(
        f"J1: {resultado['player1']['time']:.3f}s "
        f"(diferença {resultado['player1']['difference']:.3f})"
    )
    print(
        f"J2: {resultado['player2']['time']:.3f}s "
        f"(diferença {resultado['player2']['difference']:.3f})"
    )
    print(f"Vencedor da rodada: {vencedor}")
    print(f"Placar: J1 {placar[1]} x {placar[2]} J2")

    return True


def desconectar_jogadores(server, conexoes):
    for player_id, conexao in enumerate(conexoes, start=1):
        try:
            enviar_status(
                server,
                conexao,
                player_id,
                "DISCONNECTED",
                "Servidor encerrando a conexão.",
            )
        except (OSError, BrokenPipeError):
            pass

        try:
            conexao.close()
        except OSError:
            pass


def main():
    server = ServerConnection(HOST, PORT)
    server.listen()

    conexoes = []

    # Aceita exatamente dois jogadores.
    for player_id in range(1, 3):
        conexao, endereco = server.accept_player()
        conexoes.append(conexao)

        enviar_status(
            server,
            conexao,
            player_id,
            "PLAYER_CONNECTED",
            "Jogador conectado.",
        )

        print(f"Jogador {player_id} conectado: {endereco}")

    print("Os dois jogadores conectaram. Duelo começando!")

    # Placar da partida
    placar = {
        1: 0,
        2: 0
    }

    numero_rodada = 0

    try:
        while max(placar.values()) < VITORIAS_NECESSARIAS:
            numero_rodada += 1

            duel = DuelTimer(
                min_seconds=2.0,
                max_seconds=10.0,
            )

            rodada_ok = jogar_rodada(
                server,
                conexoes,
                duel,
                placar,
                numero_rodada,
            )

            if not rodada_ok:
                break

            if max(placar.values()) < VITORIAS_NECESSARIAS:
                for conexao in conexoes:
                    enviar_game(
                        server,
                        conexao,
                        "NEW_ROUND",
                        numero_rodada + 1,
                    )

                time.sleep(1.5)

        print(
            f"\nFim de jogo! "
            f"Placar final: J1 {placar[1]} x {placar[2]} J2"
        )

    except (KeyboardInterrupt, OSError) as erro:
        print(f"Servidor encerrado: {erro}")

    finally:
        desconectar_jogadores(server, conexoes)


if __name__ == "__main__":
    main()
