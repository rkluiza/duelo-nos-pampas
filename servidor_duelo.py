import random
import time

from server import ServerConnection

HOST = '127.0.0.1'
PORT = 5000
VITORIAS_NECESSARIAS = 2  # melhor de 3: quem fizer 2 rounds primeiro, vence


def sortear_tempo():
    """Sorteia o tempo alvo do round, entre 2 e 10 segundos, com 2 casas decimais."""
    return round(random.uniform(2.0, 10.0), 2)


def jogar_rodada(server, conexoes, numero_rodada):
    tempo_sorteado = sortear_tempo()
    print(f"\n--- Rodada {numero_rodada} | tempo sorteado (uso interno do servidor): "
          f"{tempo_sorteado:.2f}s ---")

    # 1) avisa os dois jogadores de qual tempo eles terão que estimar
    for conexao in conexoes:
        server.send_message_to_player(conexao, f"TEMPO;{tempo_sorteado:.2f}")

    # pequena pausa de "preparem-se" antes da largada, só por imersão
    time.sleep(random.uniform(1.0, 3.0))

    # 2) sinal de largada — disparado para os dois em sequência imediata,
    #    o mais simultâneo possível dado que são dois sends distintos
    for conexao in conexoes:
        server.send_message_to_player(conexao, "DUELEM!")

    # 3) espera a estimativa de cada jogador (cada um mede o próprio tempo
    #    localmente e manda de volta só o número, já com 2 casas decimais)
    tempos_marcados = []
    for conexao in conexoes:
        resposta = server.receive_message(conexao)
        tempos_marcados.append(float(resposta))

    diffs = [abs(t - tempo_sorteado) for t in tempos_marcados]
    print(f"Jogador 1 marcou {tempos_marcados[0]:.2f}s (diferença {diffs[0]:.2f})")
    print(f"Jogador 2 marcou {tempos_marcados[1]:.2f}s (diferença {diffs[1]:.2f})")

    if diffs[0] < diffs[1]:
        vencedor = 0
    elif diffs[1] < diffs[0]:
        vencedor = 1
    else:
        vencedor = None  # empate exato: round não conta ponto pra ninguém

    vencedor_str = str(vencedor) if vencedor is not None else "EMPATE"
    resumo = (f"RESULTADO;{tempo_sorteado:.2f};"
              f"{tempos_marcados[0]:.2f};{tempos_marcados[1]:.2f};{vencedor_str}")
    for conexao in conexoes:
        server.send_message_to_player(conexao, resumo)

    return vencedor


def main():
    server = ServerConnection(HOST, PORT)
    server.listen()

    conexoes = []
    for indice in range(2):
        conexao, _endereco = server.accept_player()
        conexoes.append(conexao)
        server.send_message_to_player(conexao, f"BEMVINDO;{indice}")

    print("Os dois jogadores conectaram. Duelo começando!")

    placar = [0, 0]
    rodada = 0

    while max(placar) < VITORIAS_NECESSARIAS:
        rodada += 1
        vencedor = jogar_rodada(server, conexoes, rodada)
        if vencedor is not None:
            placar[vencedor] += 1
        print(f"Placar: Jogador 1 {placar[0]} x {placar[1]} Jogador 2")

    campeao = 0 if placar[0] > placar[1] else 1
    for conexao in conexoes:
        server.send_message_to_player(
            conexao, f"FIM;{campeao};{placar[0]};{placar[1]}")

    for conexao in conexoes:
        conexao.close()

    print(f"\nFim de jogo! Jogador {campeao + 1} venceu o duelo "
          f"por {placar[0]} x {placar[1]}.")


if __name__ == "__main__":
    main()
