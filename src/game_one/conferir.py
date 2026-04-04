"""Conferência de apostas contra resultados reais."""

from .coleta import buscar_concurso, JOGOS


APOSTAS = {
    "lotofacil": {
        "concurso": 3652,
        "jogos": [
            [2, 5, 6, 7, 9, 10, 11, 14, 16, 17, 18, 21, 22, 23, 25],
            [3, 5, 6, 8, 10, 11, 12, 15, 16, 17, 19, 21, 22, 23, 24],
            [1, 2, 9, 10, 11, 13, 14, 15, 16, 17, 19, 20, 22, 24, 25],
        ],
    },
    "megasena": {
        "concurso": 2992,
        "jogos": [
            [7, 16, 24, 36, 47, 51],
            [7, 11, 31, 37, 41, 48],
            [7, 9, 31, 32, 38, 48],
        ],
    },
}

PREMIOS_LOTOFACIL = {11: "R$ ~6", 12: "R$ ~12", 13: "R$ ~30", 14: "R$ ~1.500", 15: "JACKPOT"}
PREMIOS_MEGASENA = {4: "quadra", 5: "quina", 6: "SENA"}


def conferir(jogo: str | None = None):
    jogos = [jogo] if jogo else list(APOSTAS.keys())

    for j in jogos:
        if j not in APOSTAS:
            continue
        info = JOGOS[j]
        aposta = APOSTAS[j]
        concurso_num = aposta["concurso"]

        print(f"\n{'='*60}")
        print(f"  {info['nome']} — Concurso {concurso_num}")
        print(f"{'='*60}")

        try:
            resultado = buscar_concurso(j, concurso_num)
            dezenas = sorted([int(d) for d in resultado["listaDezenas"]])
            print(f"\n  Resultado: {' '.join(f'{d:02d}' for d in dezenas)}")
        except Exception as e:
            print(f"\n  Concurso {concurso_num} ainda não disponível ({e})")
            continue

        print()
        for i, jogo_nums in enumerate(aposta["jogos"], 1):
            acertos = sorted(set(jogo_nums) & set(dezenas))
            n_acertos = len(acertos)
            acertos_str = " ".join(f"{d:02d}" for d in acertos) if acertos else "nenhum"

            premio = ""
            if j == "lotofacil" and n_acertos >= 11:
                premio = f"  ← PRÊMIO! ({PREMIOS_LOTOFACIL[n_acertos]})"
            elif j == "megasena" and n_acertos >= 4:
                premio = f"  ← PRÊMIO! ({PREMIOS_MEGASENA[n_acertos]})"

            jogo_str = " ".join(f"{d:02d}" for d in jogo_nums)
            print(f"  Jogo {i}: {jogo_str}")
            print(f"         {n_acertos} acertos: [{acertos_str}]{premio}")
