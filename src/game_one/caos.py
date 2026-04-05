"""Motor de caça a padrões no caos — gera hipóteses e testa automaticamente."""

import math
from datetime import datetime

import numpy as np
from scipy import stats

from . import db
from .coleta import JOGOS


def _carregar_concursos(jogo: str) -> list[dict]:
    """Carrega concursos com todos os dados disponíveis."""
    conn = db.conectar()
    rows = conn.execute("""
        SELECT c.numero, c.data, c.local, c.acumulado,
               c.valor_acumulado, c.valor_estimado, c.valor_arrecadado, c.ordem_sorteio,
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
        prev2_dezenas = sorted(int(x) for x in rows[i - 2]["dezenas_str"].split(",")) if i > 1 else []
        ordem = [int(x) for x in row["ordem_sorteio"].split(",") if x.strip()] if row["ordem_sorteio"] else []
        concursos.append({
            "numero": row["numero"], "dt": dt, "dezenas": set(dezenas),
            "dezenas_ord": dezenas,
            "local": row["local"] or "", "acumulado": row["acumulado"],
            "prev_dezenas": set(prev_dezenas),
            "prev_dezenas_ord": sorted(int(x) for x in rows[i - 1]["dezenas_str"].split(",")) if i > 0 else [],
            "prev2_dezenas": set(prev2_dezenas),
            "valor_acumulado": row["valor_acumulado"] or 0,
            "valor_estimado": row["valor_estimado"] or 0,
            "valor_arrecadado": row["valor_arrecadado"] or 0,
            "ordem_sorteio": ordem,
        })
    return concursos


def _inverter(n: int) -> int | None:
    s = f"{n:02d}"
    inv = int(s[::-1])
    return inv if inv > 0 else None


def _fase_lua(dt: datetime) -> str:
    """Calcula fase da lua (algoritmo de Conway). Retorna: nova/crescente/cheia/minguante."""
    y, m, d = dt.year, dt.month, dt.day
    # Algoritmo simplificado baseado no ciclo de 29.53 dias
    # Referência: lua nova em 2000-01-06
    ref = datetime(2000, 1, 6)
    dias = (dt - ref).days
    ciclo = dias % 29.53
    if ciclo < 1.85:
        return "nova"
    elif ciclo < 9.23:
        return "crescente"
    elif ciclo < 16.61:
        return "cheia"
    elif ciclo < 23.99:
        return "minguante"
    return "nova"


def _fase_lua_num(dt: datetime) -> int:
    """Retorna posição no ciclo lunar (0-29)."""
    ref = datetime(2000, 1, 6)
    return int((dt - ref).days % 29.53)


# Sequência de Fibonacci até 60
_FIB = set()
a, b = 1, 1
while a <= 60:
    _FIB.add(a)
    a, b = b, a + b

# Proporção áurea
_PHI = (1 + math.sqrt(5)) / 2


def _extrair_digitos_valor(valor: float, max_num: int) -> set[int]:
    """Extrai dígitos significativos de um valor monetário."""
    if valor <= 0:
        return set()
    nums = set()
    # Dígitos do valor inteiro
    s = str(int(valor))
    for ch in s:
        d = int(ch)
        if 1 <= d <= max_num:
            nums.add(d)
    # Pares de dígitos
    for i in range(len(s) - 1):
        v = int(s[i:i + 2])
        if 1 <= v <= max_num:
            nums.add(v)
    return nums


def _gerar_hipoteses(max_num: int) -> list[dict]:
    """Gera todas as hipóteses a testar."""
    H = []

    # ==================== DATA ====================

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

    def h_dia_mes_aritmetica(c):
        d, m = c["dt"].day, c["dt"].month
        nums = set()
        for v in [d + m, abs(d - m),
                  int(f"{d}{m}") if d < 10 and m < 10 else None,
                  int(f"{m}{d}") if m < 10 and d < 10 else None]:
            if v and 1 <= v <= max_num:
                nums.add(v)
        return nums
    H.append({"nome": "dia_mes_aritmetica", "cat": "data", "fn": h_dia_mes_aritmetica,
              "desc": "Dia+mês, |dia-mês|, concatenações"})

    # ==================== CONCURSO ====================

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

    def h_pares_digitos_conc(c):
        s = str(c["numero"])
        nums = set()
        for i in range(len(s) - 1):
            v = int(s[i:i + 2])
            if 1 <= v <= max_num:
                nums.add(v)
        return nums
    H.append({"nome": "pares_digitos_concurso", "cat": "concurso", "fn": h_pares_digitos_conc,
              "desc": "Pares de dígitos consecutivos do concurso (3651→36,65,51)"})

    # ==================== TEMPORAL ====================

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

    def h_fase_lua(c):
        v = _fase_lua_num(c["dt"]) + 1  # 1-30
        return {v} if 1 <= v <= max_num else set()
    H.append({"nome": "fase_lua", "cat": "temporal", "fn": h_fase_lua,
              "desc": "Posição no ciclo lunar (1-30)"})

    def h_lua_nova_cheia(c):
        fase = _fase_lua(c["dt"])
        pos = _fase_lua_num(c["dt"])
        # Na lua nova/cheia, testar números baixos; crescente/minguante, altos
        if fase in ("nova", "cheia"):
            return {n for n in range(1, max_num // 2 + 1)}
        return {n for n in range(max_num // 2 + 1, max_num + 1)}
    H.append({"nome": "lua_metade", "cat": "temporal", "fn": h_lua_nova_cheia,
              "desc": "Lua nova/cheia → metade baixa; crescente/minguante → metade alta"})

    # ==================== FINANCEIRO ====================

    def h_digitos_acumulado(c):
        return _extrair_digitos_valor(c["valor_acumulado"], max_num)
    H.append({"nome": "digitos_acumulado", "cat": "financeiro", "fn": h_digitos_acumulado,
              "desc": "Dígitos e pares de dígitos do valor acumulado"})

    def h_digitos_estimado(c):
        return _extrair_digitos_valor(c["valor_estimado"], max_num)
    H.append({"nome": "digitos_estimado", "cat": "financeiro", "fn": h_digitos_estimado,
              "desc": "Dígitos e pares de dígitos do valor estimado"})

    def h_digitos_arrecadado(c):
        return _extrair_digitos_valor(c["valor_arrecadado"], max_num)
    H.append({"nome": "digitos_arrecadado", "cat": "financeiro", "fn": h_digitos_arrecadado,
              "desc": "Dígitos e pares de dígitos do valor arrecadado"})

    def h_magnitude_premio(c):
        """Ordem de grandeza do prêmio como dezena."""
        v = c["valor_estimado"]
        if v <= 0:
            return set()
        mag = int(math.log10(v))  # 6 = milhão, 7 = dezena de milhões
        return {mag} if 1 <= mag <= max_num else set()
    H.append({"nome": "magnitude_premio", "cat": "financeiro", "fn": h_magnitude_premio,
              "desc": "Ordem de grandeza do prêmio (log10)"})

    # ==================== INTER-SORTEIO ====================

    def h_repeticoes(c):
        return c["prev_dezenas"] if c["prev_dezenas"] else set()
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
            inv = _inverter(d)
            if inv and 1 <= inv <= max_num:
                espelhos.add(inv)
        return espelhos
    H.append({"nome": "espelho_anterior", "cat": "inter-sorteio", "fn": h_espelho,
              "desc": "Inversão de dígitos das dezenas anteriores"})

    def h_soma_pares(c):
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
    H.append({"nome": "soma_pares_consecutivos", "cat": "inter-sorteio", "fn": h_soma_pares,
              "desc": "Soma de pares consecutivos do sorteio anterior mod max"})

    def h_diff_consecutivos(c):
        if not c["prev_dezenas_ord"] or len(c["prev_dezenas_ord"]) < 2:
            return set()
        nums = set()
        prev = c["prev_dezenas_ord"]
        for i in range(len(prev) - 1):
            v = prev[i + 1] - prev[i]
            if 1 <= v <= max_num:
                nums.add(v)
        return nums
    H.append({"nome": "gaps_anterior", "cat": "inter-sorteio", "fn": h_diff_consecutivos,
              "desc": "Diferenças entre dezenas consecutivas do anterior"})

    def h_media_anterior(c):
        if not c["prev_dezenas"]:
            return set()
        v = int(round(sum(c["prev_dezenas"]) / len(c["prev_dezenas"])))
        return {v} if 1 <= v <= max_num else set()
    H.append({"nome": "media_anterior", "cat": "inter-sorteio", "fn": h_media_anterior,
              "desc": "Média aritmética das dezenas do anterior"})

    def h_mediana_anterior(c):
        if not c["prev_dezenas_ord"]:
            return set()
        v = c["prev_dezenas_ord"][len(c["prev_dezenas_ord"]) // 2]
        return {v} if 1 <= v <= max_num else set()
    H.append({"nome": "mediana_anterior", "cat": "inter-sorteio", "fn": h_mediana_anterior,
              "desc": "Mediana das dezenas do anterior"})

    # ==================== MATEMÁTICA ====================

    def h_fibonacci(c):
        return c["dezenas"] & _FIB
    # Não — isso testa se as dezenas sorteadas SÃO fibonacci, não se fibonacci PREDIZ
    # Reformular: testar se números fibonacci saem mais que não-fibonacci
    def h_fibonacci_pred(c):
        return {n for n in _FIB if 1 <= n <= max_num}
    H.append({"nome": "fibonacci", "cat": "matemática", "fn": h_fibonacci_pred,
              "desc": "Números de Fibonacci (1,2,3,5,8,13,21,34,55) saem mais?"})

    def h_golden_ratio(c):
        """Dezenas na proporção áurea do range."""
        nums = set()
        for k in range(1, 10):
            v = int(round(max_num * k / _PHI)) % max_num
            if v == 0: v = max_num
            if 1 <= v <= max_num:
                nums.add(v)
        return nums
    H.append({"nome": "golden_ratio", "cat": "matemática", "fn": h_golden_ratio,
              "desc": "Posições na proporção áurea do range (max × k/φ)"})

    def h_primos(c):
        primos = set()
        for n in range(2, max_num + 1):
            if all(n % i != 0 for i in range(2, int(n**0.5) + 1)):
                primos.add(n)
        return primos
    H.append({"nome": "primos", "cat": "matemática", "fn": h_primos,
              "desc": "Números primos saem mais que compostos?"})

    def h_quadrados(c):
        return {n * n for n in range(1, int(max_num**0.5) + 1) if n * n <= max_num}
    H.append({"nome": "quadrados_perfeitos", "cat": "matemática", "fn": h_quadrados,
              "desc": "Quadrados perfeitos (1,4,9,16,25,36,49) saem mais?"})

    def h_multiplos_7(c):
        return {n for n in range(7, max_num + 1, 7)}
    H.append({"nome": "multiplos_7", "cat": "matemática", "fn": h_multiplos_7,
              "desc": "Múltiplos de 7 saem mais?"})

    # ==================== ORDEM DE SORTEIO ====================

    def h_primeira_bola(c):
        """A primeira bola sorteada tende a ser de alguma faixa?"""
        if not c["ordem_sorteio"]:
            return set()
        primeira = c["ordem_sorteio"][0]
        # Testar se vizinhos da primeira bola saem
        viz = set()
        if primeira - 1 >= 1: viz.add(primeira - 1)
        if primeira + 1 <= max_num: viz.add(primeira + 1)
        return viz
    H.append({"nome": "vizinhos_primeira_bola", "cat": "ordem", "fn": h_primeira_bola,
              "desc": "Vizinhos da primeira bola sorteada (ordem de sorteio)"})

    def h_ultima_bola_pred(c):
        """Última bola do sorteio anterior prediz algo?"""
        if not c["prev_dezenas_ord"]:
            return set()
        # Usar a maior dezena do anterior como semente
        ultima = max(c["prev_dezenas"])
        v = (ultima * 2) % max_num
        if v == 0: v = max_num
        return {v} if 1 <= v <= max_num else set()
    H.append({"nome": "dobro_max_anterior", "cat": "inter-sorteio", "fn": h_ultima_bola_pred,
              "desc": "Dobro da maior dezena do anterior mod max"})

    # ==================== 2ª ORDEM (padrões sobre padrões) ====================

    quadrados = {n * n for n in range(1, int(max_num**0.5) + 1) if n * n <= max_num}

    def h_quadrados_apos_quadrados(c):
        """Se anterior teve 2+ quadrados, apostar em quadrados."""
        prev_q = len(c["prev_dezenas"] & quadrados)
        return quadrados if prev_q >= 2 else set()
    H.append({"nome": "quadrados_apos_quadrados", "cat": "2a-ordem", "fn": h_quadrados_apos_quadrados,
              "desc": "Se anterior teve 2+ quadrados → apostar em quadrados"})

    def h_soma_anterior_mod(c):
        """Soma das dezenas do anterior mod max_num."""
        if not c["prev_dezenas"]:
            return set()
        v = sum(c["prev_dezenas"]) % max_num
        if v == 0: v = max_num
        return {v} if 1 <= v <= max_num else set()
    H.append({"nome": "soma_anterior_mod", "cat": "2a-ordem", "fn": h_soma_anterior_mod,
              "desc": "Soma das dezenas do anterior mod max"})

    def h_xor_digitos_anterior(c):
        """XOR dos dígitos das dezenas do anterior."""
        if not c["prev_dezenas"]:
            return set()
        nums = set()
        prev = sorted(c["prev_dezenas"])
        for i in range(len(prev) - 1):
            v = prev[i] ^ prev[i + 1]
            if 1 <= v <= max_num:
                nums.add(v)
        return nums
    H.append({"nome": "xor_anterior", "cat": "2a-ordem", "fn": h_xor_digitos_anterior,
              "desc": "XOR entre dezenas consecutivas do anterior"})

    def h_centesimos_concurso(c):
        """Últimos 2 dígitos do concurso."""
        v = c["numero"] % 100
        nums = set()
        if 1 <= v <= max_num:
            nums.add(v)
        # Inverter também
        inv = _inverter(v)
        if inv and 1 <= inv <= max_num:
            nums.add(inv)
        return nums
    H.append({"nome": "centesimos_concurso", "cat": "concurso", "fn": h_centesimos_concurso,
              "desc": "Últimos 2 dígitos do concurso e sua inversão"})

    def h_amplitude_anterior(c):
        """Amplitude do anterior como dezena."""
        if not c["prev_dezenas"]:
            return set()
        amp = max(c["prev_dezenas"]) - min(c["prev_dezenas"])
        return {amp} if 1 <= amp <= max_num else set()
    H.append({"nome": "amplitude_anterior", "cat": "2a-ordem", "fn": h_amplitude_anterior,
              "desc": "Amplitude (max-min) do anterior como dezena"})

    def h_dezenas_ausentes_2(c):
        """Dezenas que não saíram nos últimos 2 sorteios (se tiver dados)."""
        if not c.get("prev2_dezenas"):
            return set()
        ausentes = set(range(1, max_num + 1)) - c["prev_dezenas"] - c["prev2_dezenas"]
        # Retornar só as que têm final par (reduzir ruído)
        return {n for n in ausentes if n % 2 == 0}
    H.append({"nome": "ausentes_2_pares", "cat": "2a-ordem", "fn": h_dezenas_ausentes_2,
              "desc": "Dezenas pares ausentes nos últimos 2 sorteios"})

    return H


def _testar_hipotese(hipotese: dict, concursos: list[dict], max_num: int, qtd_dezenas: int) -> dict | None:
    """Testa uma hipótese contra o histórico."""
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
    # Taxa esperada: P(pelo menos 1 acerto) = 1 - C(M-K, N) / C(M, N)
    # Aproximação: 1 - ((M-K)/M)^N
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
