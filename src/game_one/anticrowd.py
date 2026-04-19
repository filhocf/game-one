"""Anti-crowd — score de impopularidade para maximizar prêmio líquido.

O único edge real em loterias: evitar combinações que muita gente joga,
reduzindo P(dividir | ganhar) e aumentando E[prêmio líquido].
"""

import numpy as np
from .coleta import JOGOS


def _popularidade_numero(n: int, max_num: int) -> float:
    """Estima popularidade relativa de um número (0-1, maior=mais popular)."""
    score = 0.0
    # Números de data (1-31) são mais apostados
    if n <= 31:
        score += 0.3
    # Números baixos (1-12 = meses) ainda mais
    if n <= 12:
        score += 0.2
    # Números "redondos" (múltiplos de 5 e 10)
    if n % 10 == 0:
        score += 0.15
    if n % 5 == 0:
        score += 0.1
    # Centro do volante (mais visível)
    centro = max_num / 2
    dist_centro = abs(n - centro) / centro
    score += (1 - dist_centro) * 0.1
    # Números "bonitos" (repetidos: 11, 22, 33, etc.)
    if n >= 10 and n // 10 == n % 10:
        score += 0.15
    return min(score, 1.0)


def _score_sequencia(dezenas: list[int]) -> float:
    """Penaliza sequências óbvias (PA, consecutivos longos)."""
    s = sorted(dezenas)
    pen = 0.0
    # Consecutivos longos
    run = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            run += 1
        else:
            if run >= 4:
                pen += run * 0.05
            run = 1
    if run >= 4:
        pen += run * 0.05
    # PA perfeita
    diffs = [s[i + 1] - s[i] for i in range(len(s) - 1)]
    if len(set(diffs)) == 1:
        pen += 0.5  # PA perfeita = muito popular
    return pen


def score_impopularidade(jogo: str, dezenas: list[int]) -> float:
    """Score de impopularidade (0-1, maior=menos popular=melhor).

    Combinações impopulares maximizam o prêmio líquido se ganharem.
    """
    info = JOGOS[jogo]
    max_num = info["max_numero"]

    # Média de popularidade dos números
    pops = [_popularidade_numero(d, max_num) for d in dezenas]
    pop_media = np.mean(pops)

    # Penalidade por sequências
    pen_seq = _score_sequencia(dezenas)

    # Soma extrema (humanos preferem somas centrais)
    soma = sum(dezenas)
    k = info["qtd_dezenas"]
    soma_media = k * (max_num + 1) / 2
    soma_desvio = abs(soma - soma_media) / soma_media
    bonus_soma = min(soma_desvio * 0.3, 0.15)

    # Score final: inverter popularidade + bonus por ser "feia"
    score = (1 - pop_media) - pen_seq + bonus_soma
    return max(0.0, min(1.0, score))


def rankear(jogo: str, combinacoes: list[list[int]]) -> list[dict]:
    """Rankeia combinações por impopularidade (melhor primeiro)."""
    scored = [{"dezenas": c, "impopularidade": score_impopularidade(jogo, c)}
              for c in combinacoes]
    scored.sort(key=lambda x: -x["impopularidade"])
    return scored
