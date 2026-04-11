"""Padrões de co-ocorrência — descobre pares/trios que saem juntos."""

from collections import Counter
from itertools import combinations

from scipy import stats

from .caos import _carregar_concursos
from .coleta import JOGOS


def descobrir_coocorrencias(jogo: str, min_lift: float = 1.15, top: int = 50) -> dict:
    """Descobre pares de números que co-ocorrem acima do esperado."""
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    qtd_dez = info["qtd_dezenas"]

    concursos = _carregar_concursos(jogo)
    total = len(concursos)

    # Frequência individual
    freq = Counter()
    for c in concursos:
        freq.update(c["dezenas"])

    # Frequência de pares
    pares_freq = Counter()
    for c in concursos:
        for par in combinations(sorted(c["dezenas"]), 2):
            pares_freq[par] += 1

    # Calcular lift de cada par
    resultados = []
    for (a, b), obs in pares_freq.items():
        p_a = freq[a] / total
        p_b = freq[b] / total
        esperado = p_a * p_b * total
        if esperado < 5:
            continue
        lift = obs / esperado
        # Chi-quadrado
        chi2, p_valor = stats.chisquare([obs, total - obs], [esperado, total - esperado])
        if lift >= min_lift and p_valor < 0.05:
            resultados.append({
                "par": (a, b), "obs": obs, "esperado": round(esperado, 1),
                "lift": round(lift, 3), "p_valor": round(p_valor, 6),
            })

    resultados.sort(key=lambda r: -r["lift"])

    # Anti-correlações (pares que NUNCA ou raramente saem juntos)
    anti = []
    for (a, b), obs in pares_freq.items():
        p_a = freq[a] / total
        p_b = freq[b] / total
        esperado = p_a * p_b * total
        if esperado < 5:
            continue
        lift = obs / esperado
        chi2, p_valor = stats.chisquare([obs, total - obs], [esperado, total - esperado])
        if lift <= (1 / min_lift) and p_valor < 0.05:
            anti.append({
                "par": (a, b), "obs": obs, "esperado": round(esperado, 1),
                "lift": round(lift, 3), "p_valor": round(p_valor, 6),
            })
    anti.sort(key=lambda r: r["lift"])

    return {
        "jogo": jogo, "nome": info["nome"], "total_concursos": total,
        "pares_positivos": resultados[:top],
        "pares_negativos": anti[:top],
    }


def gerar_bonus_coocorrencia(jogo: str, dezenas_base: list[int], max_num: int) -> dict[int, float]:
    """Dado um conjunto de dezenas já escolhidas, retorna bonus para números que co-ocorrem."""
    info = JOGOS[jogo]
    concursos = _carregar_concursos(jogo)
    total = len(concursos)

    freq = Counter()
    pares_freq = Counter()
    for c in concursos:
        freq.update(c["dezenas"])
        for par in combinations(sorted(c["dezenas"]), 2):
            pares_freq[par] += 1

    bonus = {}
    for n in range(1, max_num + 1):
        if n in dezenas_base:
            continue
        score = 0.0
        for d in dezenas_base:
            par = tuple(sorted([n, d]))
            obs = pares_freq.get(par, 0)
            p_d = freq[d] / total
            p_n = freq[n] / total
            esperado = p_d * p_n * total
            if esperado > 0:
                lift = obs / esperado
                if lift > 1.1:
                    score += (lift - 1) * 0.5
                elif lift < 0.9:
                    score -= (1 - lift) * 0.3
        if abs(score) > 0.01:
            bonus[n] = round(score, 3)

    return bonus
