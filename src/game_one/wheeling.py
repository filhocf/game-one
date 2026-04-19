"""Wheeling / Covering Design — gera menor conjunto de bilhetes com garantia de prêmio.

Três estratégias (escolhida automaticamente pelo tamanho do problema):
1. MILP (PuLP+CBC) — solução ótima, viável para pool ≤ 20
2. Greedy com sobreposição estruturada (insight Liu Changchun 2024)
3. Greedy clássico — fallback rápido

Referências:
- Nurmela & Östergård, COVER (Simulated Annealing)
- Liu Changchun et al. 2024-2025: redundância estruturada > diversificação cega
- La Jolla Covering Repository (LJCR)
"""

from itertools import combinations
from .coleta import JOGOS
from .filtros import avaliar

# Limites para escolha de estratégia
_MILP_MAX_CANDIDATOS = 200  # MILP só para problemas muito pequenos
_MILP_MAX_ALVOS = 200


def _cobertura(bilhete_set: frozenset, alvos: set, garantia: int) -> set:
    """Quais alvos este bilhete cobre."""
    return {a for a in alvos if len(bilhete_set & a) >= garantia}


def _candidatos_filtrados(pool, jogo, k, prev_dezenas, usar_filtros):
    """Gera candidatos, opcionalmente filtrados."""
    cands = list(combinations(pool, k))
    if usar_filtros:
        cands = [c for c in cands if avaliar(jogo, list(c), prev_dezenas)["passou"]]
    return cands


def _wheel_milp(candidatos, alvos, garantia, max_bilhetes):
    """Solução ótima via Programação Linear Inteira Mista."""
    import pulp

    prob = pulp.LpProblem("wheel", pulp.LpMinimize)

    # Variável binária por candidato: 1 = incluir bilhete
    x = {i: pulp.LpVariable(f"x{i}", cat="Binary") for i in range(len(candidatos))}

    # Objetivo: minimizar número de bilhetes
    prob += pulp.lpSum(x[i] for i in range(len(candidatos)))

    # Restrição: cada alvo coberto por pelo menos 1 bilhete
    cand_sets = [frozenset(c) for c in candidatos]
    for alvo in alvos:
        cobrindo = [i for i, cs in enumerate(cand_sets) if len(cs & alvo) >= garantia]
        if not cobrindo:
            continue  # alvo impossível de cobrir
        prob += pulp.lpSum(x[i] for i in cobrindo) >= 1

    # Limite de bilhetes
    prob += pulp.lpSum(x[i] for i in range(len(candidatos))) <= max_bilhetes

    prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=30))

    if prob.status != 1:
        return None  # Sem solução

    bilhetes = [list(candidatos[i]) for i in range(len(candidatos)) if x[i].varValue and x[i].varValue > 0.5]
    return bilhetes


def _wheel_greedy_estruturado(candidatos, alvos, garantia, max_bilhetes, overlap_target=0.4):
    """Greedy com sobreposição estruturada (Liu Changchun).

    Pré-computa coberturas para performance em problemas grandes.
    """
    # Pré-computar: para cada candidato, quais alvos ele cobre
    # Para problemas grandes, amostrar candidatos
    cand_sets = [frozenset(c) for c in candidatos]
    if len(cand_sets) * len(alvos) > 2_000_000:
        import random
        random.seed(42)
        n_sample = min(len(cand_sets), max(500, max_bilhetes * 10))
        indices = random.sample(range(len(cand_sets)), n_sample)
        cand_sets = [cand_sets[i] for i in indices]
        candidatos = [candidatos[i] for i in indices]

    cob_map = {}
    for i, cs in enumerate(cand_sets):
        cob_map[i] = {a for a in alvos if len(cs & a) >= garantia}

    bilhetes = []
    escolhidos_sets = []
    nao_cobertos = set(alvos)
    usados = set()

    while nao_cobertos and len(bilhetes) < max_bilhetes:
        melhor = None
        melhor_score = -1

        for i in range(len(cand_sets)):
            if i in usados:
                continue
            cob_nova = cob_map[i] & nao_cobertos
            cobertura_nova = len(cob_nova)
            if cobertura_nova == 0:
                continue

            if escolhidos_sets:
                overlaps = [len(cand_sets[i] & es) / len(cand_sets[i]) for es in escolhidos_sets]
                overlap_medio = sum(overlaps) / len(overlaps)
                overlap_score = 1.0 - abs(overlap_medio - overlap_target)
            else:
                overlap_score = 1.0

            score = cobertura_nova * 0.7 + overlap_score * cobertura_nova * 0.3
            if score > melhor_score:
                melhor_score = score
                melhor = i

        if melhor is None:
            break

        bilhetes.append(list(candidatos[melhor]))
        escolhidos_sets.append(cand_sets[melhor])
        nao_cobertos -= cob_map[melhor]
        usados.add(melhor)

    return bilhetes, nao_cobertos


def gerar_wheel(pool: list[int], jogo: str, garantia: int = 11,
                condicao: int | None = None, max_bilhetes: int = 200,
                usar_filtros: bool = True, prev_dezenas: set[int] | None = None,
                metodo: str = "auto") -> dict:
    """Gera wheeling system.

    Args:
        pool: números favoritos (ex: 18-20 números)
        jogo: 'lotofacil' ou 'megasena'
        garantia: acertos mínimos garantidos por bilhete (ex: 11 para LF)
        condicao: quantos do pool precisam sair (default: qtd_dezenas do jogo)
        max_bilhetes: limite de bilhetes gerados
        usar_filtros: aplicar filtros estruturais nos bilhetes
        prev_dezenas: concurso anterior (para filtro de repetições)
        metodo: 'auto', 'milp', 'greedy', 'estruturado'
    """
    info = JOGOS[jogo]
    k = info["qtd_dezenas"]
    pool = sorted(pool)

    if len(pool) < k:
        return {"erro": f"Pool ({len(pool)}) menor que bilhete ({k})"}

    if condicao is None:
        condicao = k

    # Alvos: todos os subconjuntos de tamanho 'condicao' do pool
    alvos = {frozenset(c) for c in combinations(pool, condicao)}
    candidatos = _candidatos_filtrados(pool, jogo, k, prev_dezenas, usar_filtros)

    if not candidatos:
        # Fallback sem filtros
        candidatos = list(combinations(pool, k))

    # Escolher método
    if metodo == "auto":
        metodo = "milp" if (len(candidatos) <= _MILP_MAX_CANDIDATOS and len(alvos) <= _MILP_MAX_ALVOS) else "estruturado"

    bilhetes = None
    nao_cobertos = alvos
    metodo_usado = metodo

    if metodo == "milp":
        bilhetes = _wheel_milp(candidatos, alvos, garantia, max_bilhetes)
        if bilhetes is not None:
            # Recalcular cobertura
            nao_cobertos = set(alvos)
            for b in bilhetes:
                nao_cobertos -= _cobertura(frozenset(b), nao_cobertos, garantia)

    if bilhetes is None:
        metodo_usado = "estruturado" if metodo != "greedy" else "greedy"
        if metodo_usado == "estruturado":
            bilhetes, nao_cobertos = _wheel_greedy_estruturado(
                candidatos, alvos, garantia, max_bilhetes)
        else:
            bilhetes, nao_cobertos = _wheel_greedy_estruturado(
                candidatos, alvos, garantia, max_bilhetes, overlap_target=0.0)

    cobertura_pct = 1 - len(nao_cobertos) / len(alvos) if alvos else 0
    custo = len(bilhetes) * (3.0 if jogo == "lotofacil" else 5.0)

    return {
        "jogo": jogo,
        "pool": pool,
        "pool_size": len(pool),
        "garantia": garantia,
        "condicao": condicao,
        "metodo": metodo_usado,
        "bilhetes": bilhetes,
        "n_bilhetes": len(bilhetes),
        "custo_total": custo,
        "alvos_total": len(alvos),
        "alvos_cobertos": len(alvos) - len(nao_cobertos),
        "cobertura_pct": round(cobertura_pct, 4),
    }


def simular_wheel(wheel: dict, resultado: set[int]) -> dict:
    """Simula um wheel contra um resultado real."""
    pool_acertos = len(set(wheel["pool"]) & resultado)
    acertos = []
    for b in wheel["bilhetes"]:
        ac = len(set(b) & resultado)
        acertos.append({"dezenas": b, "acertos": ac})
    melhor = max(acertos, key=lambda x: x["acertos"]) if acertos else None
    return {
        "n_bilhetes": len(acertos),
        "melhor_acertos": melhor["acertos"] if melhor else 0,
        "acertos_por_bilhete": acertos,
        "pool_no_resultado": pool_acertos,
    }
