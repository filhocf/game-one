"""Evolução genética de hipóteses — muta, cruza e encadeia padrões que funcionaram."""

import random
import math
from datetime import datetime

from .gerador import UNARY_OPS, BINARY_OPS, FIELDS, SET_EXTRACTORS


def _all_op_names():
    return list(UNARY_OPS.keys())

def _all_field_names():
    return list(FIELDS.keys())

def _all_binary_names():
    return list(BINARY_OPS.keys())

def _all_set_names():
    return list(SET_EXTRACTORS.keys())


# ── Mutações ───────────────────────────────────────────────────────────

def mutar_unario(nome: str, max_num: int) -> dict | None:
    """Pega uma hipótese unária (campo.op) e troca o campo ou a operação."""
    parts = nome.split(".")
    if len(parts) != 2:
        return None
    campo, op = parts
    if campo not in FIELDS or op not in UNARY_OPS:
        return None

    if random.random() < 0.5:
        # Mutar campo
        novo_campo = random.choice([f for f in _all_field_names() if f != campo])
        tag = f"{novo_campo}.{op}"
    else:
        # Mutar operação
        nova_op = random.choice([o for o in _all_op_names() if o != op])
        tag = f"{campo}.{nova_op}"

    return _build_unary(tag, max_num)


def mutar_binario(nome: str, max_num: int) -> dict | None:
    """Pega uma hipótese binária (campoA+campoB.op) e muta um componente."""
    parts = nome.split(".")
    if len(parts) != 2:
        return None
    campos_str, op = parts
    if "+" not in campos_str:
        return None
    campo_a, campo_b = campos_str.split("+", 1)

    choice = random.randint(0, 2)
    if choice == 0 and campo_a in FIELDS:
        novo = random.choice([f for f in _all_field_names() if f != campo_a and f != campo_b])
        tag = f"{novo}+{campo_b}.{op}"
    elif choice == 1 and campo_b in FIELDS:
        novo = random.choice([f for f in _all_field_names() if f != campo_b and f != campo_a])
        tag = f"{campo_a}+{novo}.{op}"
    else:
        nova_op = random.choice([o for o in _all_binary_names() if o != op])
        tag = f"{campo_a}+{campo_b}.{nova_op}"

    return _build_binary(tag, max_num)


def cruzar(nome_a: str, nome_b: str, max_num: int) -> dict | None:
    """Cruza dois padrões: pega campo de um e operação de outro."""
    parts_a = nome_a.split(".")
    parts_b = nome_b.split(".")
    if len(parts_a) != 2 or len(parts_b) != 2:
        return None

    # Pegar campo(s) de A e operação de B
    campos_a, op_b = parts_a[0], parts_b[1]

    if "+" in campos_a:
        return _build_binary(f"{campos_a}.{op_b}", max_num)
    else:
        return _build_unary(f"{campos_a}.{op_b}", max_num)


def encadear(nome: str, max_num: int) -> dict | None:
    """Encadeia: aplica uma op extra no resultado de uma hipótese unária."""
    parts = nome.split(".")
    if len(parts) != 2:
        return None
    campo, op1 = parts
    if campo not in FIELDS or op1 not in UNARY_OPS:
        return None

    op2 = random.choice(_all_op_names())
    tag = f"{campo}.{op1}>{op2}"

    ff = FIELDS[campo]
    of1 = UNARY_OPS[op1]
    of2 = UNARY_OPS[op2]

    def fn(c, _ff=ff, _of1=of1, _of2=of2, _mx=max_num):
        v = _ff(c)
        r1 = _of1(v)
        if not isinstance(r1, int):
            return set()
        r2 = _of2(r1)
        if not isinstance(r2, int):
            return set()
        r2 = r2 % _mx
        if r2 == 0:
            r2 = _mx
        return {r2} if 1 <= r2 <= _mx else set()

    return {"nome": tag, "cat": "evo-cadeia", "fn": fn,
            "desc": f"{campo} → {op1} → {op2} → dezena"}


def combinar_campo_com_set(max_num: int) -> dict | None:
    """Combina um campo escalar com um extrator de conjunto via filtro."""
    campo_nome = random.choice(_all_field_names())
    set_nome = random.choice(_all_set_names())
    op_nome = random.choice(["add", "sub", "xor"])

    campo_fn = FIELDS[campo_nome]
    set_fn = SET_EXTRACTORS[set_nome]
    op_fn = BINARY_OPS[op_nome]

    tag = f"set.{set_nome}@{campo_nome}.{op_nome}"

    def fn(c, _cf=campo_fn, _sf=set_fn, _of=op_fn, _mx=max_num):
        nums = _sf(c, _mx)
        if not nums:
            return set()
        v = _cf(c)
        result = set()
        for n in nums:
            try:
                r = int(_of(n, v)) % _mx
                if r == 0:
                    r = _mx
                if 1 <= r <= _mx:
                    result.add(r)
            except:
                pass
        return result

    return {"nome": tag, "cat": "evo-set-campo", "fn": fn,
            "desc": f"set({set_nome}) {op_nome} {campo_nome} → dezenas"}


def inventar_window(max_num: int) -> dict | None:
    """Inventa uma regra condicional: se campo > threshold → apostar em faixa."""
    campo_nome = random.choice(_all_field_names())
    campo_fn = FIELDS[campo_nome]
    comparador = random.choice(["alto", "baixo"])
    faixa = random.choice(["baixos", "altos", "pares", "impares"])

    tag = f"window.{campo_nome}_{comparador}→{faixa}"

    def fn(c, _cf=campo_fn, _comp=comparador, _faixa=faixa, _mx=max_num):
        v = _cf(c)
        mediana = _mx // 2
        if _comp == "alto" and v <= mediana:
            return set()
        if _comp == "baixo" and v > mediana:
            return set()
        half = _mx // 2
        if _faixa == "baixos":
            return set(range(1, half + 1))
        elif _faixa == "altos":
            return set(range(half + 1, _mx + 1))
        elif _faixa == "pares":
            return {n for n in range(2, _mx + 1, 2)}
        else:
            return {n for n in range(1, _mx + 1, 2)}

    return {"nome": tag, "cat": "evo-window", "fn": fn,
            "desc": f"Se {campo_nome} {comparador} → apostar {faixa}"}


# ── Builders auxiliares ────────────────────────────────────────────────

def _build_unary(tag: str, max_num: int) -> dict | None:
    parts = tag.split(".")
    if len(parts) != 2:
        return None
    campo, op = parts
    if campo not in FIELDS or op not in UNARY_OPS:
        return None
    ff = FIELDS[campo]
    of = UNARY_OPS[op]

    def fn(c, _ff=ff, _of=of, _mx=max_num):
        v = _ff(c)
        r = _of(v)
        if not isinstance(r, int):
            return set()
        r = r % _mx
        if r == 0:
            r = _mx
        return {r} if 1 <= r <= _mx else set()

    return {"nome": tag, "cat": "evo-unário", "fn": fn,
            "desc": f"{campo} → {op} → dezena"}


def _build_binary(tag: str, max_num: int) -> dict | None:
    parts = tag.split(".")
    if len(parts) != 2:
        return None
    campos_str, op = parts
    if "+" not in campos_str or op not in BINARY_OPS:
        return None
    campo_a, campo_b = campos_str.split("+", 1)
    if campo_a not in FIELDS or campo_b not in FIELDS:
        return None
    ffa = FIELDS[campo_a]
    ffb = FIELDS[campo_b]
    ofn = BINARY_OPS[op]

    def fn(c, _ffa=ffa, _ffb=ffb, _of=ofn, _mx=max_num):
        a, b = _ffa(c), _ffb(c)
        try:
            r = int(_of(a, b)) % _mx
        except:
            return set()
        if r == 0:
            r = _mx
        return {r} if 1 <= r <= _mx else set()

    return {"nome": tag, "cat": "evo-binário", "fn": fn,
            "desc": f"{campo_a} {op} {campo_b} → dezena"}


# ── Gerador evolutivo principal ────────────────────────────────────────

def gerar_evolucoes(padroes_ativos: list[dict], max_num: int, qtd: int = 50) -> list[dict]:
    """Gera hipóteses novas por mutação, cruzamento e invenção."""
    novas = []
    nomes_existentes = {p["nome"] for p in padroes_ativos}

    # Nomes dos padrões ativos para mutar/cruzar
    nomes = [p["nome"] for p in padroes_ativos]

    tentativas = 0
    max_tent = qtd * 10

    while len(novas) < qtd and tentativas < max_tent:
        tentativas += 1
        h = None
        estrategia = random.random()

        if estrategia < 0.25 and nomes:
            # Mutação de unário
            h = mutar_unario(random.choice(nomes), max_num)
        elif estrategia < 0.45 and nomes:
            # Mutação de binário
            h = mutar_binario(random.choice(nomes), max_num)
        elif estrategia < 0.60 and len(nomes) >= 2:
            # Cruzamento
            a, b = random.sample(nomes, 2)
            h = cruzar(a, b, max_num)
        elif estrategia < 0.70 and nomes:
            # Encadeamento
            h = encadear(random.choice(nomes), max_num)
        elif estrategia < 0.85:
            # Combinar set com campo
            h = combinar_campo_com_set(max_num)
        else:
            # Inventar window
            h = inventar_window(max_num)

        if h and h["nome"] not in nomes_existentes:
            nomes_existentes.add(h["nome"])
            novas.append(h)

    return novas
