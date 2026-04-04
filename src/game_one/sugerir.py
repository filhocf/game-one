"""Gerador de sugestões inteligentes usando padrões do caos."""

from datetime import datetime, timedelta

import numpy as np

from . import db
from .caos import _carregar_concursos, _gerar_hipoteses, _testar_hipotese, _fase_lua
from .coleta import JOGOS


def sugerir(jogo: str, qtd_jogos: int = 5, proximo_dt: datetime | None = None) -> dict:
    """Gera sugestões ponderadas pelos padrões significativos do caos."""
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    qtd_dez = info["qtd_dezenas"]

    concursos = _carregar_concursos(jogo)
    ultimo = concursos[-1]

    # Dados do próximo concurso (estimados)
    if not proximo_dt:
        # Estimar próxima data baseado no padrão de dias
        proximo_dt = datetime.now().replace(hour=20, minute=0, second=0, microsecond=0)

    prox = {
        "numero": ultimo["numero"] + 1,
        "dt": proximo_dt,
        "dezenas": set(),
        "prev_dezenas": ultimo["dezenas"],
        "prev_dezenas_ord": sorted(ultimo["dezenas"]),
        "local": ultimo["local"],
        "acumulado": ultimo["acumulado"],
        "valor_acumulado": ultimo["valor_acumulado"],
        "valor_estimado": ultimo["valor_estimado"],
        "valor_arrecadado": 0,
        "ordem_sorteio": [],
    }

    # 1. Testar todas as hipóteses no histórico para saber quais são significativas
    hipoteses = _gerar_hipoteses(max_num)
    pesos_hipotese = {}
    for h in hipoteses:
        r = _testar_hipotese(h, concursos, max_num, qtd_dez)
        if r and r["p_valor"] < 0.15:  # só hipóteses com alguma significância
            pesos_hipotese[h["nome"]] = {
                "lift": r["lift"],
                "p_valor": r["p_valor"],
                "peso": (1 - r["p_valor"]) * abs(r["lift"] - 1),  # quanto mais significativo e maior lift, mais peso
                "fn": h["fn"],
                "desc": h["desc"],
            }

    # 2. Para cada número, calcular score baseado nas hipóteses
    scores = np.zeros(max_num + 1)  # index 0 não usado
    contribuicoes = {n: [] for n in range(1, max_num + 1)}

    for nome, info_h in pesos_hipotese.items():
        nums_sugeridos = info_h["fn"](prox)
        if not nums_sugeridos:
            continue
        for n in nums_sugeridos:
            if 1 <= n <= max_num:
                bonus = info_h["peso"] * (1 if info_h["lift"] > 1 else -0.5)
                scores[n] += bonus
                contribuicoes[n].append((nome, round(bonus, 3)))

    # 3. Adicionar baseline de frequência histórica
    from .analise import carregar_df, frequencia, atraso
    df = carregar_df(jogo)
    freq = frequencia(df, max_num)
    atr = atraso(df, max_num)
    total = len(df)

    for n in range(1, max_num + 1):
        scores[n] += (freq[n] / total) * 0.3  # frequência histórica
        scores[n] += min(atr[n] / 15, 0.5) * 0.2  # atraso (números "devidos")

    # 4. Normalizar e gerar jogos
    scores_valid = scores[1:]
    if scores_valid.max() > scores_valid.min():
        scores_valid = (scores_valid - scores_valid.min()) / (scores_valid.max() - scores_valid.min())
    probs = scores_valid + 0.01  # evitar zero
    probs = probs / probs.sum()

    jogos = []
    for _ in range(qtd_jogos * 50):
        if len(jogos) >= qtd_jogos:
            break
        escolhidos = sorted(np.random.choice(
            range(1, max_num + 1), size=qtd_dez, replace=False, p=probs
        ))
        escolhidos = [int(n) for n in escolhidos]
        if escolhidos in [j["dezenas"] for j in jogos]:
            continue
        score = sum(float(scores[n]) for n in escolhidos)
        jogos.append({"dezenas": escolhidos, "score": round(score, 3)})

    jogos.sort(key=lambda j: -j["score"])

    # Top números por score
    ranking = sorted(range(1, max_num + 1), key=lambda n: -scores[n])

    return {
        "jogo": jogo,
        "nome": JOGOS[jogo]["nome"],
        "concurso_alvo": prox["numero"],
        "data_alvo": proximo_dt.strftime("%d/%m/%Y"),
        "fase_lua": _fase_lua(proximo_dt),
        "hipoteses_usadas": len(pesos_hipotese),
        "top_numeros": [(n, round(float(scores[n]), 3)) for n in ranking[:qtd_dez + 5]],
        "contribuicoes": {n: contribuicoes[n] for n in ranking[:10] if contribuicoes[n]},
        "jogos": jogos[:qtd_jogos],
        "hipoteses_significativas": [
            {"nome": k, "desc": v["desc"], "lift": v["lift"], "p_valor": v["p_valor"]}
            for k, v in sorted(pesos_hipotese.items(), key=lambda x: x[1]["p_valor"])
        ],
    }
