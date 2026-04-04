"""Motor de caça a padrões no caos — gera hipóteses e testa automaticamente."""

from datetime import datetime

import numpy as np
from scipy import stats

from . import db
from .coleta import JOGOS


def _carregar_concursos(jogo: str) -> list[dict]:
    """Carrega concursos com dezenas e dados do anterior."""
    conn = db.conectar()
    rows = conn.execute("""
        SELECT c.numero, c.data, c.local, c.acumulado,
               GROUP_CONCAT(d.dezena ORDER BY d.posicao) as dezenas_str
        FROM concursos c
        JOIN dezenas d ON c.jogo = d.jogo AND c.numero = d.numero
        WHERE c.jogo = ?
        GROUP BY c.numero ORDER BY c.numero
    """, (jogo,)).fetchall()
    conn.close()

    concursos = []
    for i, row in enumerate(rows):
        dt = datetime.strptime(row["data"], "%d/%m/%Y")
        dezenas = sorted(int(x) for x in row["dezenas_str"].split(","))
        prev_dezenas = sorted(int(x) for x in rows[i - 1]["dezenas_str"].split(",")) if i > 0 else []
        concursos.append({
            "numero": row["numero"], "dt": dt, "dezenas": set(dezenas),
            "local": row["local"] or "", "acumulado": row["acumulado"],
            "prev_dezenas": set(prev_dezenas),
        })
    return concursos


def _inverter(n: int) -> int | None:
    """Inverte dígitos: 14→41, 03→30, 5→50."""
    s = f"{n:02d}"
    inv = int(s[::-1])
    return inv if inv > 0 else None


def _gerar_hipoteses(max_num: int) -> list[dict]:
    """Gera todas as hipóteses a testar."""
    H = []

    # --- Data ---
    def h_dia_invertido(c):
        inv = _inverter(c["dt"].day)
        return {inv} if inv and 1 <= inv <= max_num else set()
    H.append({"nome": "dia_invertido", "cat": "data", "fn": h_dia_invertido,
              "desc": "Dia do mês com dígitos invertidos (14→41)"})

    def h_mes_invertido(c):
        inv = _inverter(c["dt"].month)
        return {inv} if inv and 1 <= inv <= max_num else set()
    H.append({"nome": "mes_invertido", "cat": "data", "fn": h_mes_invertido,
              "desc": "Mês com dígitos invertidos (04→40)"})

    def h_dia_e_mes(c):
        d, m = c["dt"].day, c["dt"].month
        nums = set()
        for v in [d, m, _inverter(d), _inverter(m)]:
            if v and 1 <= v <= max_num:
                nums.add(v)
        return nums
    H.append({"nome": "dia_mes_combo", "cat": "data", "fn": h_dia_e_mes,
              "desc": "Dia, mês e suas inversões como dezenas"})

    def h_soma_digitos_data(c):
        s = sum(int(ch) for ch in c["dt"].strftime("%d%m%Y"))
        return {s} if 1 <= s <= max_num else set()
    H.append({"nome": "soma_digitos_data", "cat": "data", "fn": h_soma_digitos_data,
              "desc": "Soma de todos os dígitos da data (dd+mm+aaaa)"})

    def h_diff_dia_mes(c):
        v = abs(c["dt"].day - c["dt"].month)
        return {v} if 1 <= v <= max_num else set()
    H.append({"nome": "diff_dia_mes", "cat": "data", "fn": h_diff_dia_mes,
              "desc": "|dia - mês|"})

    def h_produto_dia_mes(c):
        v = c["dt"].day * c["dt"].month
        return {v} if 1 <= v <= max_num else set()
    H.append({"nome": "produto_dia_mes", "cat": "data", "fn": h_produto_dia_mes,
              "desc": "dia × mês"})

    def h_dia_mes_concat(c):
        d, m = c["dt"].day, c["dt"].month
        nums = set()
        for v in [int(f"{d}{m}") if d < 10 and m < 10 else None,
                  int(f"{m}{d}") if m < 10 and d < 10 else None,
                  d + m, abs(d - m)]:
            if v and 1 <= v <= max_num:
                nums.add(v)
        return nums
    H.append({"nome": "dia_mes_aritmetica", "cat": "data", "fn": h_dia_mes_concat,
              "desc": "Dia+mês, |dia-mês|, concatenações"})

    # --- Concurso ---
    def h_digitos_concurso(c):
        return {int(ch) for ch in str(c["numero"]) if 1 <= int(ch) <= max_num}
    H.append({"nome": "digitos_concurso", "cat": "concurso", "fn": h_digitos_concurso,
              "desc": "Dígitos individuais do número do concurso"})

    def h_concurso_mod(c):
        v = c["numero"] % max_num
        return {v} if v >= 1 else {max_num}
    H.append({"nome": "concurso_mod", "cat": "concurso", "fn": h_concurso_mod,
              "desc": f"Número do concurso mod {max_num}"})

    def h_soma_digitos_conc(c):
        v = sum(int(ch) for ch in str(c["numero"]))
        return {v} if 1 <= v <= max_num else set()
    H.append({"nome": "soma_digitos_concurso", "cat": "concurso", "fn": h_soma_digitos_conc,
              "desc": "Soma dos dígitos do número do concurso"})

    # --- Temporal ---
    def h_dia_do_ano(c):
        v = c["dt"].timetuple().tm_yday % max_num
        return {v} if v >= 1 else {max_num}
    H.append({"nome": "dia_do_ano_mod", "cat": "temporal", "fn": h_dia_do_ano,
              "desc": f"Dia do ano (1-366) mod {max_num}"})

    def h_semana_ano(c):
        v = c["dt"].isocalendar()[1]
        return {v} if 1 <= v <= max_num else {v % max_num or max_num}
    H.append({"nome": "semana_do_ano", "cat": "temporal", "fn": h_semana_ano,
              "desc": "Semana do ano (1-53)"})

    # --- Inter-sorteio ---
    def h_repeticoes(c):
        """Testa se dezenas do anterior que NÃO saíram agora tendem a sair."""
        if not c["prev_dezenas"]:
            return set()
        # Dezenas do anterior que poderiam repetir (exclui as que já sabemos que repetiram)
        # Retorna as que NÃO estavam no anterior — testa se "ausência no anterior" prediz presença
        return c["prev_dezenas"]
    H.append({"nome": "repeticoes_anterior", "cat": "inter-sorteio", "fn": h_repeticoes,
              "desc": "Dezenas do concurso anterior como preditoras"})

    def h_complemento(c):
        return {max_num + 1 - d for d in c["prev_dezenas"] if 1 <= max_num + 1 - d <= max_num} if c["prev_dezenas"] else set()
    H.append({"nome": "complemento", "cat": "inter-sorteio", "fn": h_complemento,
              "desc": f"Complemento das dezenas anteriores ({max_num}+1 - d)"})

    def h_vizinhos(c):
        viz = set()
        for d in c["prev_dezenas"]:
            if d - 1 >= 1: viz.add(d - 1)
            if d + 1 <= max_num: viz.add(d + 1)
        return viz - c["prev_dezenas"]
    H.append({"nome": "vizinhos_anterior", "cat": "inter-sorteio", "fn": h_vizinhos,
              "desc": "Vizinhos (±1) das dezenas do concurso anterior"})

    def h_espelho(c):
        espelhos = set()
        for d in c["prev_dezenas"]:
            dezena = d % 10
            dezena_inv = (d // 10) if d >= 10 else d * 10
            if 1 <= dezena_inv <= max_num:
                espelhos.add(dezena_inv)
        return espelhos
    H.append({"nome": "espelho_anterior", "cat": "inter-sorteio", "fn": h_espelho,
              "desc": "Inversão de dígitos das dezenas anteriores"})

    def h_soma_pares_anterior(c):
        if not c["prev_dezenas"]:
            return set()
        nums = set()
        prev = sorted(c["prev_dezenas"])
        for i in range(len(prev) - 1):
            v = (prev[i] + prev[i + 1]) % max_num
            if v == 0: v = max_num
            if 1 <= v <= max_num:
                nums.add(v)
        return nums
    H.append({"nome": "soma_pares_consecutivos", "cat": "inter-sorteio", "fn": h_soma_pares_anterior,
              "desc": "Soma de pares consecutivos do sorteio anterior mod max"})

    return H


def _testar_hipotese(hipotese: dict, concursos: list[dict], max_num: int, qtd_dezenas: int) -> dict | None:
    """Testa uma hipótese contra o histórico."""
    acertos = 0
    tentativas = 0
    total_previstos = 0

    for c in concursos[1:]:  # pula o primeiro (sem anterior)
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
    # Taxa esperada: prob de pelo menos 1 acerto dado N previstos e K dezenas em M números
    media_previstos = total_previstos / tentativas
    taxa_esp = 1 - np.prod([(max_num - qtd_dezenas - i) / (max_num - i)
                             for i in range(min(int(media_previstos), max_num - qtd_dezenas))])
    if taxa_esp == 0:
        taxa_esp = qtd_dezenas / max_num

    # Chi-quadrado
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


def cacar_padroes(jogo: str, top: int = 15) -> dict:
    """Executa o motor de caça a padrões."""
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    qtd_dez = info["qtd_dezenas"]

    print(f"\n  Carregando concursos de {info['nome']}...", flush=True)
    concursos = _carregar_concursos(jogo)

    hipoteses = _gerar_hipoteses(max_num)
    print(f"  Testando {len(hipoteses)} hipóteses contra {len(concursos)} concursos...\n", flush=True)

    resultados = []
    for h in hipoteses:
        r = _testar_hipotese(h, concursos, max_num, qtd_dez)
        if r:
            resultados.append(r)

    resultados.sort(key=lambda r: r["p_valor"])

    return {
        "jogo": jogo,
        "nome": info["nome"],
        "total_concursos": len(concursos),
        "hipoteses_testadas": len(hipoteses),
        "hipoteses_validas": len(resultados),
        "resultados": resultados[:top],
    }
