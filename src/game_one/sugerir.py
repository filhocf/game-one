"""Gerador de sugestões — usa banco de padrões + co-ocorrência + meta + cross-lottery + otimizador."""

from datetime import datetime

import numpy as np

from . import db
from .caos import _carregar_concursos, _gerar_hipoteses, _fase_lua
from .gerador import gerar_hipoteses_programaticas
from .prospector import carregar_padroes_ativos, prospectar_rodada, stats_padroes
from .meta import avaliar_padroes_retroativo, cross_lottery_bonus
from .otimizador import gerar_jogos_otimizados
from .coleta import JOGOS


def sugerir(jogo: str, qtd_jogos: int = 5, proximo_dt: datetime | None = None) -> dict:
    """Gera sugestões usando todos os sinais disponíveis."""
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    qtd_dez = info["qtd_dezenas"]

    # 1. Garantir banco de padrões
    padroes_db = carregar_padroes_ativos(jogo)
    if len(padroes_db) < 3:
        print("  Banco pequeno — rodando prospecção...", flush=True)
        prospectar_rodada(jogo, verbose=True)
        padroes_db = carregar_padroes_ativos(jogo)

    # 2. Carregar concursos e contexto
    concursos = _carregar_concursos(jogo)
    ultimo = concursos[-1]

    if not proximo_dt:
        proximo_dt = datetime.now().replace(hour=20, minute=0, second=0, microsecond=0)

    prox = {
        "numero": ultimo["numero"] + 1, "dt": proximo_dt,
        "dezenas": set(), "dezenas_ord": [],
        "prev_dezenas": ultimo["dezenas"],
        "prev_dezenas_ord": sorted(ultimo["dezenas"]),
        "prev2_dezenas": concursos[-2]["dezenas"] if len(concursos) > 1 else set(),
        "local": ultimo["local"], "acumulado": ultimo["acumulado"],
        "valor_acumulado": ultimo["valor_acumulado"],
        "valor_estimado": ultimo["valor_estimado"],
        "valor_arrecadado": 0, "ordem_sorteio": [],
    }

    # 3. Reconstruir funções
    from .evolucao import gerar_evolucoes
    h_caos = {h["nome"]: h for h in _gerar_hipoteses(max_num)}
    h_prog = {h["nome"]: h for h in gerar_hipoteses_programaticas(max_num)}
    h_evo = {}
    for _ in range(10):
        for e in gerar_evolucoes(padroes_db, max_num, qtd=50):
            h_evo[e["nome"]] = e
    todas = {**h_caos, **h_prog, **h_evo}

    # 4. Meta-pesos (performance recente de cada padrão)
    meta_pesos = avaliar_padroes_retroativo(jogo, ultimos=10)

    # 5. Calcular scores
    scores = np.zeros(max_num + 1)
    contribuicoes = {n: [] for n in range(1, max_num + 1)}
    padroes_usados = []

    for p in padroes_db:
        h = todas.get(p["nome"])
        if not h:
            continue
        nums = h["fn"](prox)
        if not nums:
            continue

        # Peso base: score de confiança do banco
        peso_base = p.get("score_confianca", 0) or ((1 - p["p_valor"]) * abs(p["lift"] - 1))
        # Ajuste meta: multiplicar pela taxa de acerto recente
        meta = meta_pesos.get(p["nome"], 0.5)
        peso = peso_base * (0.5 + meta)  # meta=1.0 → peso×1.5, meta=0 → peso×0.5
        direcao = 1 if p["lift"] > 1 else -0.5

        for n in nums:
            if 1 <= n <= max_num:
                bonus = peso * direcao
                scores[n] += bonus
                contribuicoes[n].append((p["nome"], round(bonus, 3)))
        padroes_usados.append(p)

    # 6. Cross-lottery bonus
    cross_bonus = cross_lottery_bonus(max_num)
    for n, b in cross_bonus.items():
        if 1 <= n <= max_num:
            scores[n] += b

    # 7. Frequência e atraso
    from .analise import carregar_df, frequencia, atraso
    df = carregar_df(jogo)
    freq = frequencia(df, max_num)
    atr = atraso(df, max_num)
    total = len(df)
    for n in range(1, max_num + 1):
        scores[n] += (freq[n] / total) * 0.3
        scores[n] += min(atr[n] / 15, 0.5) * 0.2

    # 8. Gerar jogos otimizados (com co-ocorrência + perfil)
    jogos = gerar_jogos_otimizados(jogo, scores, max_num, qtd_dez, qtd_jogos, concursos)

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
        "meta_aplicado": True,
        "cross_lottery": len(cross_bonus) > 0,
        "top_numeros": [(n, round(float(scores[n]), 3)) for n in ranking[:qtd_dez + 5]],
        "contribuicoes": {n: contribuicoes[n] for n in ranking[:10] if contribuicoes[n]},
        "jogos": jogos[:qtd_jogos],
        "hipoteses_significativas": [
            {"nome": p["nome"], "desc": p["desc"], "lift": p["lift"], "p_valor": p["p_valor"],
             "score": p.get("score_confianca", 0), "meta": meta_pesos.get(p["nome"], 0.5)}
            for p in sorted(padroes_usados, key=lambda x: x.get("score_confianca", 0), reverse=True)[:15]
        ],
    }
