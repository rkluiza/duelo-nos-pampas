import random

class DuelTimer:
    def __init__(self, min_seconds=0.0, max_seconds=10.0):
        # Sorteia o tempo-alvo entre 0 e 10 segundos com duas casas decimais
        self.target_time = round(random.uniform(min_seconds, max_seconds), 2)
        self.shots = {}  # Guarda {player_id: tempo_cronometrado_pelo_cliente}

    def register_shot(self, player_id: int, shot_time: float):
        """Registra o tempo vindo do cliente (ignora cliques duplicados)."""
        if player_id not in self.shots:
            self.shots[player_id] = round(float(shot_time), 3)
            return self.shots[player_id]
        return self.shots[player_id]

    def all_players_shot(self) -> bool:
        """Checa se ambos os jogadores já enviaram seus tempos."""
        return 1 in self.shots and 2 in self.shots

    def get_result(self) -> dict:
        """Calcula as diferenças absolutas e define o vencedor."""
        if not self.all_players_shot():
            return None

        t1 = self.shots[1]
        t2 = self.shots[2]

        diff_p1 = round(abs(t1 - self.target_time), 3)
        diff_p2 = round(abs(t2 - self.target_time), 3)

        if diff_p1 < diff_p2:
            winner = 1
        elif diff_p2 < diff_p1:
            winner = 2
        else:
            winner = 0  # Empate

        return {
            "winner": winner,
            "target": self.target_time,
            "player1": {"time": t1, "difference": diff_p1},
            "player2": {"time": t2, "difference": diff_p2}
        }

    def reset(self, min_seconds=0.0, max_seconds=10.0):
        """Reinicia para uma nova rodada."""
        self.target_time = round(random.uniform(min_seconds, max_seconds), 2)
        self.shots = {}