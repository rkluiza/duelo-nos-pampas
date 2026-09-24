# Duelo dos Pampas

Uma aplicação baseada numa arquitetura cliente/servidor com protocolos únicos de aplicação.
**Integrantes:** Heber Gonçalves, Luiza Klein e Pedro Haubert.

## Sobre o Projeto

O "Duelo dos Pampas" é um jogo de reflexo onde dois jogadores competem para acionar um disparo o mais próximo possível de um tempo-alvo sorteado pelo servidor. O servidor atua como participante ativo da comunicação, centralizando o controlo do estado da partida, validando as mensagens recebidas, calculando os resultados de cada rodada e encaminhando as informações necessárias aos clientes.

## Arquitetura e Tecnologias

* **Linguagem:** Python, selecionada pela sua sintaxe simples e disponibilidade de bibliotecas nativas para rede e concorrência.


* **Interface Gráfica:** Pygame, utilizada para criar a janela do jogo e interagir com o jogador de forma independente das regras do servidor.


* **Comunicação de Rede:** Sockets TCP na camada de transporte, garantindo uma comunicação fiável, controlo de fluxo e retransmissão de dados sem necessidade de mecanismos próprios na aplicação.


* **Concorrência:** Módulo `threading`, utilizado para processar a comunicação de rede numa thread separada, evitando o bloqueio da interface gráfica principal.


* **Formato de Mensagens:** JSON (JavaScript Object Notation), escolhido pela sua estrutura simples e legível baseada em pares de chave e valor.


* **Repositório:** O controle de versão é mantido no GitHub no endereço [https://github.com/rkluiza/duelo-nos-pampas]


## Protocolos de Comunicação

A troca de mensagens segue uma estrutura JSON bidirecional com tipos específicos:

* **STATUS (Servidor ↔ Cliente):** Informa o estado da ligação, identificando o jogador (Jogador 1 ou 2) e reportando situações de erro ou abandono da partida através dos códigos `PLAYER_CONNECTED`, `ERROR` e `DISCONNECTED`.


* **GAME (Servidor ↔ Cliente):** Controla os estados e eventos da partida através de sinais de coordenação, tais como `READY`, `START`, `SHOT_REGISTERED` e `NEW_ROUND`.


* **TARGET (Servidor → Cliente):** Envia o tempo-alvo da rodada (em segundos) sorteado pelo servidor, que será exibido aos dois jogadores antes do início da contagem.


* **SHOT (Cliente → Servidor):** Regista o momento em que o jogador pressiona o botão de disparo. O tempo é calculado localmente no cliente por *timestamp* antes do envio, evitando que a latência da rede interfira na precisão do jogador.


* **RESULT (Servidor → Cliente):** Informa o desfecho da rodada, contendo o vencedor, as diferenças de tempo calculadas para cada jogador e o placar atualizado.



## Fluxo e Tratamento de Dados

* **Sequência Básica:** A comunicação segue a ordem `STATUS(PLAYER_CONNECTED) → GAME(READY) → TARGET → GAME(START) → SHOT → GAME(SHOT_REGISTERED) → RESULT → GAME(NEW_ROUND)`.


* *Tratamento de Exceções:* Situações anómalas em qualquer etapa da rodada são geridas através do envio de mensagens `STATUS` contendo os códigos `ERROR` ou `DISCONNECTED`.


* **Prevenção de Fragmentação:** Como o protocolo TCP atua como um fluxo contínuo de bytes, a aplicação implementa um delimitador de quebra de linha e um sistema de buffer por ligação. Este sistema acumula os bytes até encontrar o delimitador, assegurando a remontagem correta do JSON e prevenindo erros de leitura de dados colados ou fragmentados.