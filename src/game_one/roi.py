"""Simulador de ROI — compara Ramo A (prospecção) vs B (otimização) vs AB."""

import numpy as np
from .caos import _carregar_concursos
from .coleta import JOGOS
from .filtros import filtrar, avaliar
from .anticrowd import rankear
from .wheeling import gerar_wheel, simular_wheel

# Prêmios típicos da Lotofácil (R$)
PREMIOS_LF = {11: 6, 12: 12, 13: 30, 14: 1500, 15: 1_500_000}
PREMIOS_MS = {4: 1200, 5: 50_000, 6: 50_000_000}
CUSTO_BILHETE = {"lotofacil": 3.0, "megasena": 5.0}


def _premios(jogo: str) -> dict:
    return PREMIOS_LF if jogo == "lotofacil" else PREMIOS_MS


def _premio_acertos(jogo: str, acertos: int) -> float:
    return _premios(jogo).get(acertos, 0)


def _gerar_pool_frequencia(concursos: list[dict], max_num: int, pool_size: int) -> list[int]:
    """Pool baseado em frequência recente (últimos 30 concursos)."""
    from collections import Counter
    freq = Counter()
    for c in concursos[-30:]:
        freq.update(c["dezenas"])
    ranking = sorted(range(1, max_num + 1), key=lambda n: -freq.get(n, 0))
    return ranking[:pool_size]


def _gerar_jogos_ramo_a(jogo: str, concursos: list[dict], idx: int,
                         qtd_jogos: int) -> list[list[int]]:
    """Gera jogos pelo Ramo A (prospecção — scores do sugerir existente)."""
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    k = info["qtd_dezenas"]
    ant = concursos[idx - 1]

    # Usar frequência + atraso como proxy simples do Ramo A
    from collections import Counter
    freq = Counter()
    for c in concursos[:idx]:
        freq.update(c["dezenas"])
    total = len(concursos[:idx])

    # Atraso
    ultimo_visto = {}
    for c in concursos[:idx]:
        for d in c["dezenas"]:
            ultimo_visto[d] = c["numero"]

    scores = np.zeros(max_num + 1)
    for n in range(1, max_num + 1):
        f = freq.get(n, 0) / max(total, 1)
        atraso = concursos[idx - 1]["numero"] - ultimo_visto.get(n, 0)
        scores[n] = f * 0.6 + min(atraso / 20, 0.5) * 0.4

    probs = scores[1:].copy()
    probs = probs - probs.min() + 0.01
    probs = probs / probs.sum()

    jogos = []
    for _ in range(qtd_jogos * 50):
        if len(jogos) >= qtd_jogos:
            break
        escolhidos = sorted(np.random.choice(range(1, max_num + 1), size=k,
                                              replace=False, p=probs))
        j = [int(n) for n in escolhidos]
        if j not in jogos:
            jogos.append(j)
    return jogos[:qtd_jogos]


def _gerar_jogos_ramo_b(jogo: str, concursos: list[dict], idx: int,
                         qtd_jogos: int, pool_size: int = 18) -> list[list[int]]:
    """Gera jogos pelo Ramo B (otimização — wheeling + filtros + anti-crowd)."""
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    k = info["qtd_dezenas"]
    ant = concursos[idx - 1]
    prev = ant["dezenas"]

    pool = _gerar_pool_frequencia(concursos[:idx], max_num, pool_size)
    garantia = 11 if jogo == "lotofacil" else 4

    wheel = gerar_wheel(pool, jogo, garantia=garantia, max_bilhetes=qtd_jogos * 3,
                        prev_dezenas=prev)
    bilhetes = wheel.get("bilhetes", [])

    if not bilhetes:
        # Fallback: gerar aleatório filtrado
        from itertools import combinations
        import random
        cands = [list(c) for c in combinations(pool, k)]
        cands = filtrar(jogo, cands, prev)
        ranked = rankear(jogo, cands)
        bilhetes = [r["dezenas"] for r in ranked[:qtd_jogos]]
    else:
        ranked = rankear(jogo, bilhetes)
        bilhetes = [r["dezenas"] for r in ranked[:qtd_jogos]]

    return bilhetes


def simular_roi(jogo: str, ultimos: int = 20, jogos_por_concurso: int = 5,
                pool_size: int = 18) -> dict:
    """Simula ROI comparativo entre Ramo A, B e aleatório."""
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    k = info["qtd_dezenas"]
    custo_bilhete = CUSTO_BILHETE[jogo]

    concursos = _carregar_concursos(jogo)
    ultimos = min(ultimos, len(concursos) - 35)

    resultados = {"A": [], "B": [], "random": []}

    for offset in range(ultimos, 0, -1):
        idx = len(concursos) - offset
        real = concursos[idx]
        resultado = real["dezenas"]

        np.random.seed(real["numero"])

        # Ramo A
        jogos_a = _gerar_jogos_ramo_a(jogo, concursos, idx, jogos_por_concurso)
        # Ramo B
        jogos_b = _gerar_jogos_ramo_b(jogo, concursos, idx, jogos_por_concurso, pool_size)
        # Aleatório (controle)
        jogos_r = []
        for _ in range(jogos_por_concurso * 50):
            if len(jogos_r) >= jogos_por_concurso:
                break
            j = sorted(np.random.choice(range(1, max_num + 1), size=k, replace=False))
            j = [int(n) for n in j]
            if j not in jogos_r:
                jogos_r.append(j)

        for ramo, jogos in [("A", jogos_a), ("B", jogos_b), ("random", jogos_r)]:
            premio_total = 0
            acertos_lista = []
            for j in jogos:
                ac = len(set(j) & resultado)
                acertos_lista.append(ac)
                premio_total += _premio_acertos(jogo, ac)
            custo = len(jogos) * custo_bilhete
            resultados[ramo].append({
                "concurso": real["numero"],
                "acertos": acertos_lista,
                "melhor": max(acertos_lista) if acertos_lista else 0,
                "premio": premio_total,
                "custo": custo,
                "lucro": premio_total - custo,
            })

    # Agregar
    resumo = {}
    for ramo in ["A", "B", "random"]:
        dados = resultados[ramo]
        todos_acertos = [a for r in dados for a in r["acertos"]]
        total_premio = sum(r["premio"] for r in dados)
        total_custo = sum(r["custo"] for r in dados)
        premios_ganhos = sum(1 for a in todos_acertos if _premio_acertos(jogo, a) > 0)
        resumo[ramo] = {
            "concursos": len(dados),
            "jogos_total": len(todos_acertos),
            "media_acertos": round(np.mean(todos_acertos), 2),
            "melhor_acerto": max(todos_acertos) if todos_acertos else 0,
            "premios_ganhos": premios_ganhos,
            "total_premio": total_premio,
            "total_custo": total_custo,
            "roi_pct": round((total_premio / total_custo - 1) * 100, 1) if total_custo else 0,
            "lucro": total_premio - total_custo,
        }

    return {"jogo": jogo, "nome": info["nome"], "ultimos": ultimos,
            "jogos_por_concurso": jogos_por_concurso, "resumo": resumo,
            "detalhes": resultados}


def imprimir_roi(r: dict):
    """Imprime comparativo de ROI formatado."""
    print(f"\n{'='*70}")
    print(f"  {r['nome']} — Simulação ROI ({r['ultimos']} concursos, "
          f"{r['jogos_por_concurso']} jogos/concurso)")
    print(f"{'='*70}")
    print(f"\n  {'Métrica':<25} {'Ramo A':>10} {'Ramo B':>10} {'Aleatório':>10}")
    print(f"  {'─'*55}")
    for key, label in [
        ("media_acertos", "Média acertos"),
        ("melhor_acerto", "Melhor acerto"),
        ("premios_ganhos", "Prêmios ganhos"),
        ("total_premio", "Total prêmios (R$)"),
        ("total_custo", "Total custo (R$)"),
        ("lucro", "Lucro (R$)"),
        ("roi_pct", "ROI (%)"),
    ]:
        a = r["resumo"]["A"][key]
        b = r["resumo"]["B"][key]
        rand = r["resumo"]["random"][key]
        fmt = ".1f" if isinstance(a, float) else ""
        print(f"  {label:<25} {a:>10{fmt}} {b:>10{fmt}} {rand:>10{fmt}}")
    print()
