import os
import queue
import threading
import time

import pygame

from player import PlayerConection

HOST = "127.0.0.1"
PORT = 5000

ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "assets",
)

LARGURA, ALTURA = 1280, 720
ALTURA_SPRITE = 330

BRANCO = (255, 255, 255)
AMARELO = (255, 224, 102)

DURACAO_FLASH = 0.15
DURACAO_VOO = 0.35
DURACAO_IMPACTO = 0.25


def caminho(nome):
    return os.path.join(ASSETS_DIR, nome)


def carregar_imagens():
    imagens = {
        "fundo": pygame.image.load(
            caminho("missoes_bg_entardecer_1280x720.png")
        ).convert(),
        "p1": pygame.image.load(
            caminho("gaucho1_transp.png")
        ).convert_alpha(),
        "p2": pygame.image.load(
            caminho("gaucho2_transp.png")
        ).convert_alpha(),
        "flash": pygame.image.load(
            caminho("fogo_tiro.png")
        ).convert_alpha(),
        "bala_direita": pygame.image.load(
            caminho("projetil.png")
        ).convert_alpha(),
        "bala_esquerda": pygame.image.load(
            caminho("projetil_esquerda.png")
        ).convert_alpha(),
    }

    for chave in ("p1", "p2"):
        img = imagens[chave]
        escala = ALTURA_SPRITE / img.get_height()
        nova_largura = int(img.get_width() * escala)

        imagens[chave] = pygame.transform.scale(
            img,
            (nova_largura, ALTURA_SPRITE),
        )

    return imagens


def rede_thread(player, fila):
    while True:
        try:
            mensagem = player.wait_message()
        except (OSError, ConnectionError):
            break

        if not mensagem:
            break

        fila.put(mensagem)


def iniciar_animacao_tiro(
    animacao,
    atirador_idx,
    alvo_idx,
    posicoes_cano,
):
    animacao.clear()
    animacao["ativa"] = True
    animacao["fase"] = "flash"
    animacao["relogio"] = 0.0
    animacao["atirador"] = atirador_idx
    animacao["origem"] = posicoes_cano[atirador_idx]
    animacao["destino"] = posicoes_cano[alvo_idx]
    animacao["pos_bala"] = list(posicoes_cano[atirador_idx])


def atualizar_animacao(animacao, dt):
    if not animacao.get("ativa"):
        return

    animacao["relogio"] += dt

    if (
        animacao["fase"] == "flash"
        and animacao["relogio"] >= DURACAO_FLASH
    ):
        animacao["fase"] = "voo"
        animacao["relogio"] = 0.0

    elif animacao["fase"] == "voo":
        t = min(1.0, animacao["relogio"] / DURACAO_VOO)

        ox, oy = animacao["origem"]
        dx, dy = animacao["destino"]

        animacao["pos_bala"] = [
            ox + (dx - ox) * t,
            oy + (dy - oy) * t,
        ]

        if t >= 1.0:
            animacao["fase"] = "impacto"
            animacao["relogio"] = 0.0

    elif (
        animacao["fase"] == "impacto"
        and animacao["relogio"] >= DURACAO_IMPACTO
    ):
        animacao["ativa"] = False


def processar_mensagem(
    mensagem,
    estado,
    animacao,
    posicoes_cano,
):
    tipo = mensagem.get("type")
    data = mensagem.get("data", {})

    if tipo == "STATUS":
        codigo = data.get("code")

        if codigo == "PLAYER_CONNECTED":
            player_id = data.get("player_id")

            estado["meu_id"] = player_id
            estado["texto_topo"] = (
                f"Você é o Jogador {player_id}"
            )
            estado["texto_sub"] = data.get(
                "message",
                "Aguardando o outro jogador...",
            )

        elif codigo == "ERROR":
            estado["texto_topo"] = "Erro"
            estado["texto_sub"] = data.get(
                "message",
                "Ocorreu um erro.",
            )

        elif codigo == "DISCONNECTED":
            estado["fase"] = "fim"
            estado["texto_topo"] = "Conexão encerrada"
            estado["texto_sub"] = data.get(
                "message",
                "O servidor encerrou a conexão.",
            )

    elif tipo == "GAME":
        codigo = data.get("code")

        if codigo == "READY":
            estado["fase"] = "preparar"
            rodada = data.get("round")

            estado["texto_topo"] = (
                f"Rodada {rodada}"
                if rodada is not None
                else "Nova rodada"
            )
            estado["texto_sub"] = "Prepare-se..."

        elif codigo == "START":
            estado["fase"] = "duelo"
            estado["inicio_duelo"] = time.perf_counter()
            estado["texto_topo"] = "DUELEM!"
            estado["texto_sub"] = (
                "Aperte ESPAÇO quando achar que o tempo passou"
            )

        elif codigo == "SHOT_REGISTERED":
            if estado["fase"] != "fim":
                estado["texto_sub"] = (
                    "Tiro registrado. "
                    "Aguardando o outro jogador..."
                )

        elif codigo == "NEW_ROUND":
            estado["fase"] = "preparar"
            rodada = data.get("round")

            estado["tempo_sorteado"] = None
            estado["inicio_duelo"] = None

            estado["texto_topo"] = (
                f"Rodada {rodada}"
                if rodada is not None
                else "Nova rodada"
            )
            estado["texto_sub"] = "Prepare-se..."

    elif tipo == "TARGET":
        estado["tempo_sorteado"] = float(
            data["target"]
        )
        estado["texto_topo"] = (
            f"Tempo-alvo: {estado['tempo_sorteado']:.2f}s"
        )
        estado["texto_sub"] = "Prepare-se..."

    elif tipo == "RESULT":
        estado["fase"] = "resultado"

        vencedor = data.get("winner")
        score = data.get("score", {})

        estado["placar"] = [
            int(score.get("player1", 0)),
            int(score.get("player2", 0)),
        ]

        target = data.get("target")
        p1 = data.get("player1", {})
        p2 = data.get("player2", {})

        if vencedor == 0:
            estado["texto_topo"] = "Empate na rodada!"
        else:
            if vencedor == estado["meu_id"]:
                estado["texto_topo"] = "Você venceu a rodada!"
            else:
                estado["texto_topo"] = (
                    f"Jogador {vencedor} venceu a rodada!"
                )

            vencedor_idx = vencedor - 1
            alvo_idx = 1 - vencedor_idx

            iniciar_animacao_tiro(
                animacao,
                vencedor_idx,
                alvo_idx,
                posicoes_cano,
            )

        estado["texto_sub"] = (
            f"Alvo: {target:.2f}s | "
            f"J1: {p1.get('time', 0):.3f}s "
            f"({p1.get('difference', 0):.3f}) | "
            f"J2: {p2.get('time', 0):.3f}s "
            f"({p2.get('difference', 0):.3f})"
        )


def desenhar_textos(tela, fontes, estado):
    largura = tela.get_width()

    faixa = pygame.Surface(
        (largura, 110),
        pygame.SRCALPHA,
    )
    faixa.fill((0, 0, 0, 140))
    tela.blit(faixa, (0, 0))

    topo = fontes["grande"].render(
        estado["texto_topo"],
        True,
        BRANCO,
    )
    tela.blit(
        topo,
        (
            largura // 2 - topo.get_width() // 2,
            12,
        ),
    )

    sub = fontes["media"].render(
        estado["texto_sub"],
        True,
        AMARELO,
    )
    tela.blit(
        sub,
        (
            largura // 2 - sub.get_width() // 2,
            68,
        ),
    )

    placar_txt = fontes["media"].render(
        f"Placar: {estado['placar'][0]} x "
        f"{estado['placar'][1]}",
        True,
        BRANCO,
    )

    tela.blit(
        placar_txt,
        (
            largura - placar_txt.get_width() - 20,
            20,
        ),
    )


def desenhar(
    tela,
    imagens,
    fontes,
    posicoes_sprite,
    estado,
    animacao,
):
    tela.blit(imagens["fundo"], (0, 0))
    tela.blit(imagens["p1"], posicoes_sprite[0])
    tela.blit(imagens["p2"], posicoes_sprite[1])

    if animacao.get("ativa"):
        fase = animacao["fase"]

        if fase == "flash":
            fx, fy = animacao["origem"]
            img = imagens["flash"]

            tela.blit(
                img,
                (
                    fx - img.get_width() // 2,
                    fy - img.get_height() // 2,
                ),
            )

        elif fase == "voo":
            bx, by = animacao["pos_bala"]

            if animacao["atirador"] == 0:
                img = imagens["bala_direita"]
            else:
                img = imagens["bala_esquerda"]

            tela.blit(
                img,
                (
                    bx - img.get_width() // 2,
                    by - img.get_height() // 2,
                ),
            )

        elif fase == "impacto":
            ix, iy = animacao["destino"]
            img = imagens["flash"]

            tela.blit(
                img,
                (
                    ix - img.get_width() // 2,
                    iy - img.get_height() // 2,
                ),
            )

    desenhar_textos(tela, fontes, estado)


def main():
    pygame.init()

    pygame.display.set_caption("Duelo nos Pampas")

    tela = pygame.display.set_mode(
        (LARGURA, ALTURA)
    )
    relogio = pygame.time.Clock()

    fontes = {
        "grande": pygame.font.Font(None, 56),
        "media": pygame.font.Font(None, 32),
    }

    imagens = carregar_imagens()

    pos1 = (
        250,
        660 - ALTURA_SPRITE,
    )
    pos2 = (
        880,
        660 - ALTURA_SPRITE,
    )

    posicoes_sprite = [pos1, pos2]

    w1 = imagens["p1"].get_width()
    w2 = imagens["p2"].get_width()

    gun1 = (
        pos1[0] + int(w1 * 0.98),
        pos1[1] + int(ALTURA_SPRITE * 0.335),
    )
    gun2 = (
        pos2[0] + int(w2 * 0.02),
        pos2[1] + int(ALTURA_SPRITE * 0.335),
    )

    posicoes_cano = [gun1, gun2]

    player = PlayerConection(HOST, PORT)

    fila = queue.Queue()

    threading.Thread(
        target=rede_thread,
        args=(player, fila),
        daemon=True,
    ).start()

    estado = {
        "fase": "conectado",
        "meu_id": None,
        "tempo_sorteado": None,
        "inicio_duelo": None,
        "texto_topo": "Conectado!",
        "texto_sub": "Aguardando o servidor...",
        "placar": [0, 0],
    }

    animacao = {
        "ativa": False,
    }

    rodando = True

    while rodando:
        dt = relogio.tick(60) / 1000.0

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

            elif (
                evento.type == pygame.KEYDOWN
                and evento.key == pygame.K_SPACE
            ):
                if estado["fase"] == "duelo":
                    tempo_medido = round(
                        time.perf_counter()
                        - estado["inicio_duelo"],
                        3,
                    )

                    estado["fase"] = "aguardando_resultado"
                    estado["texto_topo"] = (
                        f"Você marcou {tempo_medido:.3f}s"
                    )
                    estado["texto_sub"] = (
                        "Aguardando o outro jogador..."
                    )

                    player.send_message_to_server(
                        "SHOT",
                        {
                            "time": tempo_medido,
                        },
                    )

        try:
            while True:
                mensagem = fila.get_nowait()

                processar_mensagem(
                    mensagem,
                    estado,
                    animacao,
                    posicoes_cano,
                )

        except queue.Empty:
            pass

        atualizar_animacao(animacao, dt)

        desenhar(
            tela,
            imagens,
            fontes,
            posicoes_sprite,
            estado,
            animacao,
        )

        pygame.display.flip()

    try:
        player.player.close()
    except OSError:
        pass

    pygame.quit()


if __name__ == "__main__":
    main()
