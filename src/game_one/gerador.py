"""Gerador programático de hipóteses — combina operações primitivas automaticamente."""

import math
from datetime import datetime
from itertools import product

import numpy as np
from scipy import stats

from . import db
from .coleta import JOGOS


# ── Operações primitivas sobre campos ──────────────────────────────────

def _op_identity(v):
    return v

def _op_mod10(v):
    return v % 10 if v else 0

def _op_mod7(v):
    return v % 7 if v else 0

def _op_invert_digits(v):
    s = f"{int(abs(v)):02d}"
    return int(s[::-1])

def _op_digit_sum(v):
    return sum(int(c) for c in str(int(abs(v))))

def _op_sqrt_floor(v):
    return int(math.isqrt(int(abs(v)))) if v > 0 else 0

def _op_log2(v):
    return int(math.log2(v)) if v and v > 0 else 0

def _op_double(v):
    return v * 2

def _op_half(v):
    return v // 2 if v else 0

def _op_complement(v, mx):
    return mx + 1 - v if 1 <= v <= mx else 0


UNARY_OPS = {
    "id": _op_identity,
    "mod10": _op_mod10,
    "mod7": _op_mod7,
    "inv": _op_invert_digits,
    "dsum": _op_digit_sum,
    "sqrt": _op_sqrt_floor,
    "log2": _op_log2,
    "x2": _op_double,
    "half": _op_half,
}

BINARY_OPS = {
    "add": lambda a, b: a + b,
    "sub": lambda a, b: abs(a - b),
    "mul": lambda a, b: a * b,
    "xor": lambda a, b: a ^ b,
    "mod": lambda a, b: a % b if b else 0,
}


# ── Extratores de campos de um concurso ────────────────────────────────

def _field_dia(c):
    return c["dt"].day

def _field_mes(c):
    return c["dt"].month

def _field_ano_2d(c):
    return c["dt"].year % 100

def _field_dia_ano(c):
    return c["dt"].timetuple().tm_yday

def _field_semana(c):
    return c["dt"].isocalendar()[1]

def _field_concurso(c):
    return c["numero"]

def _field_conc_mod100(c):
    return c["numero"] % 100

def _field_soma_prev(c):
    return sum(c["prev_dezenas"]) if c["prev_dezenas"] else 0

def _field_amplitude_prev(c):
    if not c["prev_dezenas"]:
        return 0
    return max(c["prev_dezenas"]) - min(c["prev_dezenas"])

def _field_max_prev(c):
    return max(c["prev_dezenas"]) if c["prev_dezenas"] else 0

def _field_min_prev(c):
    return min(c["prev_dezenas"]) if c["prev_dezenas"] else 0

def _field_media_prev(c):
    return int(round(sum(c["prev_dezenas"]) / len(c["prev_dezenas"]))) if c["prev_dezenas"] else 0

def _field_pares_prev(c):
    return sum(1 for d in c["prev_dezenas"] if d % 2 == 0) if c["prev_dezenas"] else 0

def _field_repeticoes_count(c):
    """Quantas dezenas do anterior se repetiram no anterior-do-anterior."""
    if not c["prev_dezenas"] or not c.get("prev2_dezenas"):
        return 0
    return len(c["prev_dezenas"] & c["prev2_dezenas"])

def _field_lua_pos(c):
    ref = datetime(2000, 1, 6)
    return int((c["dt"] - ref).days % 29.53)

def _field_acumulado_mag(c):
    v = c.get("valor_estimado", 0) or 0
    return int(math.log10(v)) if v > 0 else 0


FIELDS = {
    "dia": _field_dia,
    "mes": _field_mes,
    "ano2d": _field_ano_2d,
    "dia_ano": _field_dia_ano,
    "semana": _field_semana,
    "conc": _field_concurso,
    "conc100": _field_conc_mod100,
    "soma_prev": _field_soma_prev,
    "amp_prev": _field_amplitude_prev,
    "max_prev": _field_max_prev,
    "min_prev": _field_min_prev,
    "media_prev": _field_media_prev,
    "pares_prev": _field_pares_prev,
    "rep_count": _field_repeticoes_count,
    "lua": _field_lua_pos,
    "premio_mag": _field_acumulado_mag,
}


# ── Extratores de conjuntos (retornam set de dezenas) ──────────────────

def _set_prev_dezenas(c, mx):
    return c["prev_dezenas"] if c["prev_dezenas"] else set()

def _set_prev_vizinhos(c, mx):
    viz = set()
    for d in (c["prev_dezenas"] or set()):
        if d - 1 >= 1: viz.add(d - 1)
        if d + 1 <= mx: viz.add(d + 1)
    return viz - (c["prev_dezenas"] or set())

def _set_prev_espelho(c, mx):
    r = set()
    for d in (c["prev_dezenas"] or set()):
        inv = int(f"{d:02d}"[::-1])
        if 1 <= inv <= mx:
            r.add(inv)
    return r

def _set_prev_complemento(c, mx):
    return {mx + 1 - d for d in (c["prev_dezenas"] or set()) if 1 <= mx + 1 - d <= mx}

def _set_prev_gaps(c, mx):
    if not c.get("prev_dezenas_ord") or len(c["prev_dezenas_ord"]) < 2:
        return set()
    r = set()
    prev = c["prev_dezenas_ord"]
    for i in range(len(prev) - 1):
        v = prev[i + 1] - prev[i]
        if 1 <= v <= mx:
            r.add(v)
    return r

def _set_prev_xor(c, mx):
    if not c.get("prev_dezenas_ord") or len(c["prev_dezenas_ord"]) < 2:
        return set()
    r = set()
    prev = c["prev_dezenas_ord"]
    for i in range(len(prev) - 1):
        v = prev[i] ^ prev[i + 1]
        if 1 <= v <= mx:
            r.add(v)
    return r

def _set_prev_soma_pares(c, mx):
    if not c.get("prev_dezenas_ord") or len(c["prev_dezenas_ord"]) < 2:
        return set()
    r = set()
    prev = c["prev_dezenas_ord"]
    for i in range(len(prev) - 1):
        v = (prev[i] + prev[i + 1]) % mx
        if v == 0: v = mx
        if 1 <= v <= mx:
            r.add(v)
    return r

def _set_ausentes_2(c, mx):
    if not c.get("prev2_dezenas"):
        return set()
    return set(range(1, mx + 1)) - (c["prev_dezenas"] or set()) - c["prev2_dezenas"]

def _set_prev2_dezenas(c, mx):
    return c.get("prev2_dezenas") or set()


SET_EXTRACTORS = {
    "prev": _set_prev_dezenas,
    "prev_viz": _set_prev_vizinhos,
    "prev_esp": _set_prev_espelho,
    "prev_comp": _set_prev_complemento,
    "prev_gaps": _set_prev_gaps,
    "prev_xor": _set_prev_xor,
    "prev_soma2": _set_prev_soma_pares,
    "ausentes2": _set_ausentes_2,
    "prev2": _set_prev2_dezenas,
}


# ── Gerador combinatório ──────────────────────────────────────────────

def gerar_hipoteses_programaticas(max_num: int) -> list[dict]:
    """Gera hipóteses combinando campos × operações automaticamente."""
    H = []

    # Tipo 1: campo → op_unária → dezena candidata
    for fname, ffn in FIELDS.items():
        for oname, ofn in UNARY_OPS.items():
            tag = f"{fname}.{oname}"

            def make_fn(ff=ffn, of=ofn, mx=max_num):
                def fn(c):
                    v = ff(c)
                    r = of(v)
                    return {r % mx or mx} if isinstance(r, int) and 1 <= (r % mx or mx) <= mx else set()
                return fn

            H.append({"nome": tag, "cat": "prog-unário", "fn": make_fn(),
                       "desc": f"{fname} → {oname} → dezena"})

    # Tipo 2: campo_A × campo_B → op_binária → dezena
    field_items = list(FIELDS.items())
    for i in range(len(field_items)):
        for j in range(i + 1, len(field_items)):
            fa_name, fa_fn = field_items[i]
            fb_name, fb_fn = field_items[j]
            for oname, ofn in BINARY_OPS.items():
                tag = f"{fa_name}+{fb_name}.{oname}"

                def make_fn(ffa=fa_fn, ffb=fb_fn, of=ofn, mx=max_num):
                    def fn(c):
                        a, b = ffa(c), ffb(c)
                        try:
                            r = of(a, b)
                        except:
                            return set()
                        r = int(r) % mx if isinstance(r, (int, float)) else 0
                        if r == 0: r = mx
                        return {r} if 1 <= r <= mx else set()
                    return fn

                H.append({"nome": tag, "cat": "prog-binário", "fn": make_fn(),
                           "desc": f"{fa_name} {oname} {fb_name} → dezena"})

    # Tipo 3: extratores de conjuntos (padrões inter-sorteio)
    for sname, sfn in SET_EXTRACTORS.items():
        def make_fn(sf=sfn, mx=max_num):
            def fn(c):
                return sf(c, mx)
            return fn

        H.append({"nome": f"set.{sname}", "cat": "prog-conjunto", "fn": make_fn(),
                   "desc": f"Conjunto derivado: {sname}"})

    # Tipo 4: sliding window — padrões de sequência
    # "Se soma do anterior > mediana histórica, apostar em números altos"
    for threshold_name, threshold_fn in [
        ("soma_alta", lambda c, med: sum(c["prev_dezenas"]) > med if c["prev_dezenas"] else False),
        ("soma_baixa", lambda c, med: sum(c["prev_dezenas"]) <= med if c["prev_dezenas"] else False),
    ]:
        for target in ["baixos", "altos"]:
            tag = f"window.{threshold_name}→{target}"

            def make_fn(tfn=threshold_fn, tgt=target, mx=max_num):
                median_cache = [None]
                def fn(c, _concursos=None):
                    if not c["prev_dezenas"]:
                        return set()
                    # Usar mediana fixa como proxy
                    med = mx * 7.5  # ~metade da soma típica
                    if not tfn(c, med):
                        return set()
                    half = mx // 2
                    if tgt == "baixos":
                        return set(range(1, half + 1))
                    return set(range(half + 1, mx + 1))
                return fn

            H.append({"nome": tag, "cat": "prog-window", "fn": make_fn(),
                       "desc": f"Se {threshold_name} → apostar {target}"})

    return H


def testar_hipotese(hipotese: dict, concursos: list[dict], max_num: int, qtd_dezenas: int) -> dict | None:
    """Testa uma hipótese contra o histórico. Reutilizável."""
    acertos = 0
    tentativas = 0
    total_previstos = 0

    for c in concursos[1:]:
        previstos = hipotese["fn"](c)
        if not previstos:
            continue
        tentativas += 1
        total_previstos += len(previstos)
        if previstos & c["dezenas"]:
            acertos += 1

    if tentativas < 30:
        return None

    taxa_obs = acertos / tentativas
    media_previstos = total_previstos / tentativas
    taxa_esp = 1 - ((max_num - qtd_dezenas) / max_num) ** media_previstos
    if taxa_esp <= 0 or taxa_esp >= 1:
        taxa_esp = qtd_dezenas / max_num

    esperado_sim = tentativas * taxa_esp
    esperado_nao = tentativas * (1 - taxa_esp)
    if esperado_sim < 5 or esperado_nao < 5:
        return None

    chi2, p_valor = stats.chisquare(
        [acertos, tentativas - acertos],
        [esperado_sim, esperado_nao]
    )

    lift = taxa_obs / taxa_esp if taxa_esp > 0 else 0

    return {
        "nome": hipotese["nome"],
        "cat": hipotese["cat"],
        "desc": hipotese["desc"],
        "acertos": acertos,
        "tentativas": tentativas,
        "taxa_obs": round(taxa_obs, 4),
        "taxa_esp": round(taxa_esp, 4),
        "lift": round(lift, 3),
        "p_valor": round(p_valor, 6),
        "chi2": round(chi2, 2),
        "media_previstos": round(media_previstos, 1),
    }


def rodar_gerador(jogo: str, top: int = 30, p_max: float = 0.05) -> dict:
    """Roda o gerador programático completo."""
    from .caos import _carregar_concursos

    info = JOGOS[jogo]
    max_num = info["max_numero"]
    qtd_dez = info["qtd_dezenas"]

    concursos = _carregar_concursos(jogo)
    hipoteses = gerar_hipoteses_programaticas(max_num)

    print(f"\n  Gerador programático: {len(hipoteses)} hipóteses combinatórias", flush=True)
    print(f"  Testando contra {len(concursos)} concursos de {info['nome']}...\n", flush=True)

    resultados = []
    for i, h in enumerate(hipoteses):
        r = testar_hipotese(h, concursos, max_num, qtd_dez)
        if r and r["p_valor"] < p_max:
            resultados.append(r)
        if (i + 1) % 200 == 0:
            print(f"  ... {i+1}/{len(hipoteses)} testadas, {len(resultados)} significativas", flush=True)

    resultados.sort(key=lambda r: r["p_valor"])
    print(f"\n  Total: {len(resultados)} hipóteses com p < {p_max} (de {len(hipoteses)} testadas)")

    return {
        "jogo": jogo,
        "nome": info["nome"],
        "total_concursos": len(concursos),
        "hipoteses_testadas": len(hipoteses),
        "hipoteses_significativas": len(resultados),
        "resultados": resultados[:top],
    }
