"""Filtros estruturais — elimina combinações fora dos perfis estatísticos reais.

Valores derivados analiticamente (hipergeométrica/CLT) e confirmados por
enumeração completa de C(25,15)=3.268.760 combinações (Lotofácil).
"""

from math import sqrt
from .coleta import JOGOS

# Parâmetros exatos por jogo (E, σ, faixa_util)
PERFIS = {
    "lotofacil": {
        "soma":       {"e": 195,  "s": 18.03, "lo": 177, "hi": 213},
        "impares":    {"e": 7.8,  "s": 1.25,  "lo": 7,   "hi": 9},
        "repeticoes": {"e": 9,    "s": 1.22,  "lo": 8,   "hi": 10},
        "max_seq":    {"e": 5.0,  "s": 1.49,  "lo": 3,   "hi": 7},
        "por_faixa":  {"e": 3,    "s": 1.0,   "lo": 2,   "hi": 4},
        "faixas": [(1, 5), (6, 10), (11, 15), (16, 20), (21, 25)],
    },
    "megasena": {
        "soma":       {"e": 183,  "s": 40.25, "lo": 143, "hi": 223},
        "impares":    {"e": 3.0,  "s": 1.22,  "lo": 2,   "hi": 4},
        "repeticoes": {"e": 0.6,  "s": 0.73,  "lo": 0,   "hi": 2},
        "max_seq":    {"e": 1.3,  "s": 0.6,   "lo": 1,   "hi": 2},
        "por_faixa":  {"e": 1.0,  "s": 0.85,  "lo": 0,   "hi": 2},
        "faixas": [(1, 10), (11, 20), (21, 30), (31, 40), (41, 50), (51, 60)],
    },
}


def _maior_sequencia(dezenas: list[int]) -> int:
    """Tamanho da maior sequência consecutiva."""
    if not dezenas:
        return 0
    s = sorted(dezenas)
    melhor = atual = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            atual += 1
            melhor = max(melhor, atual)
        else:
            atual = 1
    return melhor


def _contagem_faixas(dezenas: list[int], faixas: list[tuple]) -> list[int]:
    """Conta dezenas em cada faixa."""
    ds = set(dezenas)
    return [sum(1 for d in ds if lo <= d <= hi) for lo, hi in faixas]


def avaliar(jogo: str, dezenas: list[int], prev_dezenas: set[int] | None = None) -> dict:
    """Avalia uma combinação contra os filtros estruturais.

    Retorna dict com score (0-1), detalhes por filtro, e se passou.
    """
    p = PERFIS[jogo]
    checks = {}
    total = 0
    passou = 0

    # Soma
    soma = sum(dezenas)
    ok = p["soma"]["lo"] <= soma <= p["soma"]["hi"]
    checks["soma"] = {"valor": soma, "ok": ok, **p["soma"]}
    total += 1; passou += ok

    # Ímpares
    imp = sum(1 for d in dezenas if d % 2 == 1)
    ok = p["impares"]["lo"] <= imp <= p["impares"]["hi"]
    checks["impares"] = {"valor": imp, "ok": ok, **p["impares"]}
    total += 1; passou += ok

    # Maior sequência
    ms = _maior_sequencia(dezenas)
    ok = p["max_seq"]["lo"] <= ms <= p["max_seq"]["hi"]
    checks["max_seq"] = {"valor": ms, "ok": ok, **p["max_seq"]}
    total += 1; passou += ok

    # Distribuição por faixas
    contagens = _contagem_faixas(dezenas, p["faixas"])
    faixas_ok = all(p["por_faixa"]["lo"] <= c <= p["por_faixa"]["hi"] for c in contagens)
    checks["faixas"] = {"valor": contagens, "ok": faixas_ok, **p["por_faixa"]}
    total += 1; passou += faixas_ok

    # Repetições (se tiver concurso anterior)
    if prev_dezenas is not None:
        rep = len(set(dezenas) & prev_dezenas)
        ok = p["repeticoes"]["lo"] <= rep <= p["repeticoes"]["hi"]
        checks["repeticoes"] = {"valor": rep, "ok": ok, **p["repeticoes"]}
        total += 1; passou += ok

    return {"score": passou / total, "passou": passou == total, "checks": checks}


def filtrar(jogo: str, combinacoes: list[list[int]],
            prev_dezenas: set[int] | None = None) -> list[list[int]]:
    """Filtra combinações, mantendo apenas as que passam em todos os filtros."""
    return [c for c in combinacoes if avaliar(jogo, c, prev_dezenas)["passou"]]
