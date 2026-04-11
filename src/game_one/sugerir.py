"""Gerador de sugestões — consulta o banco de padrões para montar jogos."""

from datetime import datetime

import numpy as np

from . import db
from .caos import _carregar_concursos, _gerar_hipoteses, _fase_lua
from .gerador import gerar_hipoteses_programaticas
from .prospector import carregar_padroes_ativos, prospectar_rodada, stats_padroes
from .coleta import JOGOS


def sugerir(jogo: str, qtd_jogos: int = 5, proximo_dt: datetime | None = None) -> dict:
    """Gera sugestões usando TODOS os padrões conhecidos do banco."""
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    qtd_dez = info["qtd_dezenas"]

    # 1. Garantir que o banco de padrões tem conteúdo
    padroes_db = carregar_padroes_ativos(jogo)
    if len(padroes_db) < 10:
        print("  Banco de padrões vazio/pequeno — rodando prospecção inicial...", flush=True)
        prospectar_rodada(jogo, verbose=True)
        padroes_db = carregar_padroes_ativos(jogo)

    # 2. Carregar concursos e montar contexto do próximo
    concursos = _carregar_concursos(jogo)
    ultimo = concursos[-1]

    if not proximo_dt:
        proximo_dt = datetime.now().replace(hour=20, minute=0, second=0, microsecond=0)

    prox = {
        "numero": ultimo["numero"] + 1,
        "dt": proximo_dt,
        "dezenas": set(),
        "dezenas_ord": [],
        "prev_dezenas": ultimo["dezenas"],
        "prev_dezenas_ord": sorted(ultimo["dezenas"]),
        "prev2_dezenas": concursos[-2]["dezenas"] if len(concursos) > 1 else set(),
        "local": ultimo["local"],
        "acumulado": ultimo["acumulado"],
        "valor_acumulado": ultimo["valor_acumulado"],
        "valor_estimado": ultimo["valor_estimado"],
        "valor_arrecadado": 0,
        "ordem_sorteio": [],
    }

    # 3. Reconstruir funções das hipóteses para aplicar ao próximo concurso
    hipoteses_caos = {h["nome"]: h for h in _gerar_hipoteses(max_num)}
    hipoteses_prog = {h["nome"]: h for h in gerar_hipoteses_programaticas(max_num)}
    todas_hipoteses = {**hipoteses_caos, **hipoteses_prog}

    # 4. Calcular scores usando padrões do banco
    scores = np.zeros(max_num + 1)
    contribuicoes = {n: [] for n in range(1, max_num + 1)}
    padroes_usados = []

    for p in padroes_db:
        h = todas_hipoteses.get(p["nome"])
        if not h:
            continue

        nums_sugeridos = h["fn"](prox)
        if not nums_sugeridos:
            continue

        # Peso: quanto menor o p-valor e maior o lift, mais peso
        peso = (1 - p["p_valor"]) * abs(p["lift"] - 1)
        direcao = 1 if p["lift"] > 1 else -0.5

        for n in nums_sugeridos:
            if 1 <= n <= max_num:
                bonus = peso * direcao
                scores[n] += bonus
                contribuicoes[n].append((p["nome"], round(bonus, 3)))

        padroes_usados.append(p)

    # 5. Adicionar baseline de frequência e atraso
    from .analise import carregar_df, frequencia, atraso
    df = carregar_df(jogo)
    freq = frequencia(df, max_num)
    atr = atraso(df, max_num)
    total = len(df)

    for n in range(1, max_num + 1):
        scores[n] += (freq[n] / total) * 0.3
        scores[n] += min(atr[n] / 15, 0.5) * 0.2

    # 6. Normalizar e gerar jogos
    scores_valid = scores[1:]
    if scores_valid.max() > scores_valid.min():
        scores_valid = (scores_valid - scores_valid.min()) / (scores_valid.max() - scores_valid.min())
    probs = scores_valid + 0.01
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

    ranking = sorted(range(1, max_num + 1), key=lambda n: -scores[n])
    st = stats_padroes(jogo)

    return {
        "jogo": jogo,
        "nome": JOGOS[jogo]["nome"],
        "concurso_alvo": prox["numero"],
        "data_alvo": proximo_dt.strftime("%d/%m/%Y"),
        "fase_lua": _fase_lua(proximo_dt),
        "padroes_no_banco": st["ativos"],
        "padroes_usados": len(padroes_usados),
        "top_numeros": [(n, round(float(scores[n]), 3)) for n in ranking[:qtd_dez + 5]],
        "contribuicoes": {n: contribuicoes[n] for n in ranking[:10] if contribuicoes[n]},
        "jogos": jogos[:qtd_jogos],
        "hipoteses_significativas": [
            {"nome": p["nome"], "desc": p["desc"], "lift": p["lift"], "p_valor": p["p_valor"]}
            for p in sorted(padroes_usados, key=lambda x: x["p_valor"])[:15]
        ],
    }
