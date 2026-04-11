"""Meta-aprendizado — ajusta pesos dos padrões baseado em performance recente."""

from . import db
from .caos import _carregar_concursos, _gerar_hipoteses
from .gerador import gerar_hipoteses_programaticas
from .evolucao import gerar_evolucoes
from .coleta import JOGOS


def avaliar_padroes_retroativo(jogo: str, ultimos: int = 10) -> dict[str, float]:
    """Para cada padrão ativo, mede quantas vezes acertou nos últimos N concursos."""
    info = JOGOS[jogo]
    max_num = info["max_numero"]

    concursos = _carregar_concursos(jogo)
    padroes_db = db.conectar().execute(
        "SELECT nome, cat, desc, p_valor, lift FROM padroes WHERE jogo=? AND ativo=1", (jogo,)
    ).fetchall()
    padroes_db = [dict(r) for r in padroes_db]

    # Reconstruir funções
    h_caos = {h["nome"]: h for h in _gerar_hipoteses(max_num)}
    h_prog = {h["nome"]: h for h in gerar_hipoteses_programaticas(max_num)}
    h_evo = {}
    for _ in range(10):
        for e in gerar_evolucoes(padroes_db, max_num, qtd=50):
            h_evo[e["nome"]] = e
    todas = {**h_caos, **h_prog, **h_evo}

    # Para cada concurso recente, ver quais padrões acertaram
    acertos_por_padrao = {p["nome"]: 0 for p in padroes_db}
    tentativas_por_padrao = {p["nome"]: 0 for p in padroes_db}

    for offset in range(min(ultimos, len(concursos) - 2), 0, -1):
        idx = len(concursos) - offset
        real = concursos[idx]
        ant = concursos[idx - 1]
        ant2 = concursos[idx - 2] if idx > 1 else None

        prox = {
            "numero": real["numero"], "dt": real["dt"],
            "dezenas": set(), "dezenas_ord": [],
            "prev_dezenas": ant["dezenas"],
            "prev_dezenas_ord": sorted(ant["dezenas"]),
            "prev2_dezenas": ant2["dezenas"] if ant2 else set(),
            "local": ant["local"], "acumulado": ant["acumulado"],
            "valor_acumulado": ant["valor_acumulado"],
            "valor_estimado": ant["valor_estimado"],
            "valor_arrecadado": 0, "ordem_sorteio": [],
        }

        for p in padroes_db:
            h = todas.get(p["nome"])
            if not h:
                continue
            nums = h["fn"](prox)
            if not nums:
                continue
            tentativas_por_padrao[p["nome"]] += 1
            if nums & real["dezenas"]:
                acertos_por_padrao[p["nome"]] += 1

    # Calcular taxa de acerto recente
    meta_pesos = {}
    for nome in acertos_por_padrao:
        tent = tentativas_por_padrao[nome]
        if tent == 0:
            meta_pesos[nome] = 0.5  # neutro
        else:
            meta_pesos[nome] = round(acertos_por_padrao[nome] / tent, 3)

    return meta_pesos


def cross_lottery_bonus(max_num_alvo: int) -> dict[int, float]:
    """Correlações cruzadas: números da Lotofácil que saíram recentemente como bonus para Mega."""
    try:
        from .caos import _carregar_concursos
        conc_lf = _carregar_concursos("lotofacil")
        conc_ms = _carregar_concursos("megasena")
    except:
        return {}

    if not conc_lf or not conc_ms:
        return {}

    # Últimas 5 dezenas da Lotofácil
    ultimas_lf = set()
    for c in conc_lf[-3:]:
        ultimas_lf.update(c["dezenas"])

    # Últimas 5 dezenas da Mega
    ultimas_ms = set()
    for c in conc_ms[-3:]:
        ultimas_ms.update(c["dezenas"])

    bonus = {}
    # Números que saíram na LF recente e estão no range da Mega
    for n in ultimas_lf:
        if 1 <= n <= max_num_alvo:
            bonus[n] = bonus.get(n, 0) + 0.02

    # Complementos: se saiu 10 na Mega, testar 60-10+1=51
    for n in ultimas_ms:
        comp = max_num_alvo + 1 - n
        if 1 <= comp <= max_num_alvo:
            bonus[comp] = bonus.get(comp, 0) + 0.01

    return bonus
