"""Geração otimizada de jogos — concentra nos Top, respeita perfil estrutural, usa co-ocorrência."""

import numpy as np

from .coleta import JOGOS
from .coocorrencia import gerar_bonus_coocorrencia


def _perfil_historico(concursos: list[dict], ultimos: int = 50) -> dict:
    """Calcula perfil estrutural médio dos últimos N concursos."""
    recentes = concursos[-ultimos:]
    somas = [sum(c["dezenas"]) for c in recentes]
    pares = [sum(1 for d in c["dezenas"] if d % 2 == 0) for c in recentes]
    amplitudes = [max(c["dezenas"]) - min(c["dezenas"]) for c in recentes]
    return {
        "soma_media": np.mean(somas), "soma_std": np.std(somas),
        "pares_media": np.mean(pares),
        "amplitude_media": np.mean(amplitudes), "amplitude_std": np.std(amplitudes),
    }


def _score_perfil(dezenas: list[int], perfil: dict) -> float:
    """Quanto o jogo se encaixa no perfil histórico (0-1, maior=melhor)."""
    soma = sum(dezenas)
    pares = sum(1 for d in dezenas if d % 2 == 0)
    amp = dezenas[-1] - dezenas[0]

    score = 1.0
    # Penalizar desvio da soma
    desvio_soma = abs(soma - perfil["soma_media"]) / max(perfil["soma_std"], 1)
    score -= min(desvio_soma * 0.15, 0.4)
    # Penalizar desvio de pares
    score -= abs(pares - perfil["pares_media"]) * 0.05
    # Penalizar amplitude fora do range
    desvio_amp = abs(amp - perfil["amplitude_media"]) / max(perfil["amplitude_std"], 1)
    score -= min(desvio_amp * 0.1, 0.3)

    return max(score, 0)


def gerar_jogos_otimizados(jogo: str, scores: np.ndarray, max_num: int, qtd_dez: int,
                           qtd_jogos: int, concursos: list[dict]) -> list[dict]:
    """Gera jogos otimizados: Top números + co-ocorrência + perfil estrutural."""
    perfil = _perfil_historico(concursos)
    ranking = sorted(range(1, max_num + 1), key=lambda n: -scores[n])

    # Probabilidades base dos scores
    scores_valid = scores[1:].copy()
    if scores_valid.max() > scores_valid.min():
        scores_valid = (scores_valid - scores_valid.min()) / (scores_valid.max() - scores_valid.min())
    probs = scores_valid + 0.01
    probs = probs / probs.sum()

    # Concentrar mais nos Top: elevar ao quadrado as probabilidades
    probs_conc = probs ** 1.5
    probs_conc = probs_conc / probs_conc.sum()

    jogos = []
    tentativas = 0

    while len(jogos) < qtd_jogos and tentativas < qtd_jogos * 200:
        tentativas += 1

        # Escolher seed dos Top números
        n_seed = min(qtd_dez // 2 + 1, len(ranking))
        seed = list(np.random.choice(ranking[:max(n_seed * 2, 10)], size=n_seed, replace=False))

        # Completar com co-ocorrência
        bonus = gerar_bonus_coocorrencia(jogo, seed, max_num)
        probs_adj = probs_conc.copy()
        for n, b in bonus.items():
            if 1 <= n <= max_num:
                probs_adj[n - 1] = max(probs_adj[n - 1] + b * 0.1, 0.001)
        # Zerar os já escolhidos
        for s in seed:
            probs_adj[s - 1] = 0
        if probs_adj.sum() == 0:
            continue
        probs_adj = probs_adj / probs_adj.sum()

        restantes = max_num - len(seed) if qtd_dez > len(seed) else 0
        if restantes > 0:
            extras = list(np.random.choice(
                range(1, max_num + 1), size=qtd_dez - len(seed),
                replace=False, p=probs_adj))
            dezenas = sorted(set(seed) | set(int(n) for n in extras))
        else:
            dezenas = sorted(seed[:qtd_dez])

        if len(dezenas) != qtd_dez:
            continue
        dezenas = [int(d) for d in dezenas]

        # Filtrar por perfil estrutural
        score_perfil = _score_perfil(dezenas, perfil)
        if score_perfil < 0.4:
            continue

        score_padrao = sum(float(scores[n]) for n in dezenas)
        score_total = score_padrao * 0.7 + score_perfil * score_padrao * 0.3

        if dezenas not in [j["dezenas"] for j in jogos]:
            jogos.append({
                "dezenas": dezenas,
                "score": round(score_total, 3),
                "score_perfil": round(score_perfil, 3),
            })

    jogos.sort(key=lambda j: -j["score"])
    return jogos[:qtd_jogos]
