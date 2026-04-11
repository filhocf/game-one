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
    if len(parts) != 2 or ">" in parts[1]:
        # Já é cadeia ou não é unário simples
        pass
    campo = parts[0]
    ops_chain = parts[1] if len(parts) == 2 else None
    if not ops_chain or campo not in FIELDS:
        return None

    # Permitir encadear sobre cadeias existentes (profundidade N)
    existing_ops = ops_chain.split(">")
    if len(existing_ops) >= 6:
        return None  # limitar profundidade máxima

    op_new = random.choice(_all_op_names())
    new_chain = ops_chain + ">" + op_new
    tag = f"{campo}.{new_chain}"

    ff = FIELDS[campo]
    ops_list = [UNARY_OPS[o] for o in new_chain.split(">") if o in UNARY_OPS]
    if len(ops_list) != len(new_chain.split(">")):
        return None

    def fn(c, _ff=ff, _ops=ops_list, _mx=max_num):
        v = _ff(c)
        for op in _ops:
            if not isinstance(v, (int, float)):
                return set()
            v = op(int(v))
        if not isinstance(v, int):
            return set()
        v = v % _mx
        if v == 0:
            v = _mx
        return {v} if 1 <= v <= _mx else set()

    depth = len(ops_list)
    return {"nome": tag, "cat": f"evo-cadeia-d{depth}", "fn": fn,
            "desc": f"{campo} → {'→'.join(new_chain.split('>'))} → dezena (depth={depth})"}


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


def compor_conjuntos(max_num: int) -> dict | None:
    """Combina dois extratores de conjunto com operação de conjuntos."""
    s1_nome = random.choice(_all_set_names())
    s2_nome = random.choice([s for s in _all_set_names() if s != s1_nome])
    op = random.choice(["inter", "union", "diff"])

    s1_fn = SET_EXTRACTORS[s1_nome]
    s2_fn = SET_EXTRACTORS[s2_nome]
    tag = f"setop.{s1_nome}_{op}_{s2_nome}"

    def fn(c, _s1=s1_fn, _s2=s2_fn, _op=op, _mx=max_num):
        a = _s1(c, _mx)
        b = _s2(c, _mx)
        if _op == "inter":
            return a & b
        elif _op == "union":
            return a | b
        else:
            return a - b

    return {"nome": tag, "cat": "evo-setop", "fn": fn,
            "desc": f"set({s1_nome}) {op} set({s2_nome})"}


def expressao_aninhada(max_num: int) -> dict | None:
    """Cria expressão binária aninhada: op(campo_a op campo_b, campo_c) → dezena."""
    campos = random.sample(_all_field_names(), 3)
    ops = [random.choice(_all_binary_names()) for _ in range(2)]

    fa, fb, fc = FIELDS[campos[0]], FIELDS[campos[1]], FIELDS[campos[2]]
    op1, op2 = BINARY_OPS[ops[0]], BINARY_OPS[ops[1]]
    tag = f"nest.({campos[0]}{ops[0]}{campos[1]}){ops[1]}{campos[2]}"

    def fn(c, _fa=fa, _fb=fb, _fc=fc, _o1=op1, _o2=op2, _mx=max_num):
        a, b, cc = _fa(c), _fb(c), _fc(c)
        try:
            r1 = int(_o1(a, b))
            r2 = int(_o2(r1, cc)) % _mx
        except:
            return set()
        if r2 == 0:
            r2 = _mx
        return {r2} if 1 <= r2 <= _mx else set()

    return {"nome": tag, "cat": "evo-aninhada", "fn": fn,
            "desc": f"({campos[0]} {ops[0]} {campos[1]}) {ops[1]} {campos[2]} → dezena"}


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
    """Gera hipóteses novas por mutação, cruzamento, invenção e composição."""
    novas = []
    nomes_existentes = {p["nome"] for p in padroes_ativos}
    nomes = [p["nome"] for p in padroes_ativos]

    tentativas = 0
    max_tent = qtd * 10

    while len(novas) < qtd and tentativas < max_tent:
        tentativas += 1
        h = None
        r = random.random()

        if r < 0.18 and nomes:
            h = mutar_unario(random.choice(nomes), max_num)
        elif r < 0.32 and nomes:
            h = mutar_binario(random.choice(nomes), max_num)
        elif r < 0.42 and len(nomes) >= 2:
            a, b = random.sample(nomes, 2)
            h = cruzar(a, b, max_num)
        elif r < 0.55 and nomes:
            h = encadear(random.choice(nomes), max_num)
        elif r < 0.65:
            h = combinar_campo_com_set(max_num)
        elif r < 0.75:
            h = inventar_window(max_num)
        elif r < 0.85:
            h = compor_conjuntos(max_num)
        else:
            h = expressao_aninhada(max_num)

        if h and h["nome"] not in nomes_existentes:
            nomes_existentes.add(h["nome"])
            novas.append(h)

    return novas
