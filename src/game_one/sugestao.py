"""Gerador de sugestões de jogos baseado em análise estatística."""

import numpy as np
from . import analise


def gerar_sugestoes(df, max_numero: int, qtd_dezenas: int, qtd_jogos: int = 5) -> list[dict]:
    freq = analise.frequencia(df, max_numero)
    atr = analise.atraso(df, max_numero)
    soma_stats = analise.faixa_soma(df)
    pares_top = {n for par in analise.pares_frequentes(df, 30) for n in par[0]}
    total = len(df)

    # Pesos: frequência + atraso + bonus de pares frequentes
    numeros = list(range(1, max_numero + 1))
    pesos = np.array([
        (freq[n] / total * 0.5) + (min(atr[n] / 20, 1.0) * 0.35) + (0.1 if n in pares_top else 0) + 0.05
        for n in numeros
    ])
    pesos /= pesos.sum()

    jogos = []
    soma_min, soma_max = soma_stats["faixa_ideal"]

    for _ in range(qtd_jogos * 50):
        if len(jogos) >= qtd_jogos:
            break
        escolhidos = sorted(np.random.choice(numeros, size=qtd_dezenas, replace=False, p=pesos))
        soma = sum(escolhidos)
        if not (soma_min <= soma <= soma_max):
            continue
        n_pares = sum(1 for n in escolhidos if n % 2 == 0)
        if abs(n_pares - qtd_dezenas // 2) > 2:
            continue
        escolhidos = [int(n) for n in escolhidos]
        if escolhidos in [j["dezenas"] for j in jogos]:
            continue

        score = round(max(0.0, min(1.0,
            0.3 * (1 - abs(soma - soma_stats["media"]) / soma_stats["std"])
            + 0.3 * (sum(freq[n] for n in escolhidos) / (total * qtd_dezenas))
            + 0.2 * (sum(1 for n in escolhidos if n in pares_top) / qtd_dezenas)
            + 0.2 * (sum(atr[n] for n in escolhidos) / (20 * qtd_dezenas))
        )), 3)

        jogos.append({"dezenas": escolhidos, "soma": soma, "pares": n_pares, "impares": qtd_dezenas - n_pares, "score": score})

    jogos.sort(key=lambda j: j["score"], reverse=True)
    return jogos
