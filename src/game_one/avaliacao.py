"""Avaliação retroativa — simula sugestões em concursos passados e mede acuidade."""

from datetime import datetime

import numpy as np

from . import db
from .caos import _carregar_concursos, _gerar_hipoteses
from .coleta import JOGOS
from .gerador import gerar_hipoteses_programaticas
from .prospector import carregar_padroes_ativos
from .evolucao import gerar_evolucoes
from .analise import carregar_df, frequencia, atraso


def _reconstruir_funcoes(max_num: int, padroes_db: list[dict]) -> dict:
    """Reconstrói todas as funções de hipóteses disponíveis."""
    h_caos = {h["nome"]: h for h in _gerar_hipoteses(max_num)}
    h_prog = {h["nome"]: h for h in gerar_hipoteses_programaticas(max_num)}
    h_evo = {}
    for _ in range(20):
        for e in gerar_evolucoes(padroes_db, max_num, qtd=100):
            h_evo[e["nome"]] = e
    return {**h_caos, **h_prog, **h_evo}


def avaliar(jogo: str, ultimos: int = 10, jogos_por_concurso: int = 5) -> dict:
    """Simula sugestões retroativas e mede acuidade."""
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    qtd_dez = info["qtd_dezenas"]

    concursos = _carregar_concursos(jogo)
    padroes_db = carregar_padroes_ativos(jogo)
    todas = _reconstruir_funcoes(max_num, padroes_db)

    df = carregar_df(jogo)
    freq = frequencia(df, max_num)
    atr_map = atraso(df, max_num)
    total_df = len(df)

    ultimos = min(ultimos, len(concursos) - 3)
    resultados = []

    for offset in range(ultimos, 0, -1):
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

        # Calcular scores
        scores = np.zeros(max_num + 1)
        padroes_usados = 0
        for p in padroes_db:
            h = todas.get(p["nome"])
            if not h:
                continue
            nums = h["fn"](prox)
            if not nums:
                continue
            peso = (1 - p["p_valor"]) * abs(p["lift"] - 1)
            direcao = 1 if p["lift"] > 1 else -0.5
            for n in nums:
                if 1 <= n <= max_num:
                    scores[n] += peso * direcao
            padroes_usados += 1

        for n in range(1, max_num + 1):
            scores[n] += (freq[n] / total_df) * 0.3
            scores[n] += min(atr_map[n] / 15, 0.5) * 0.2

        ranking = sorted(range(1, max_num + 1), key=lambda n: -scores[n])

        # Gerar jogos
        scores_valid = scores[1:]
        if scores_valid.max() > scores_valid.min():
            scores_valid = (scores_valid - scores_valid.min()) / (scores_valid.max() - scores_valid.min())
        probs = scores_valid + 0.01
        probs = probs / probs.sum()

        np.random.seed(real["numero"])
        jogos = []
        for _ in range(jogos_por_concurso * 50):
            if len(jogos) >= jogos_por_concurso:
                break
            escolhidos = sorted(np.random.choice(
                range(1, max_num + 1), size=qtd_dez, replace=False, p=probs))
            escolhidos = [int(n) for n in escolhidos]
            if escolhidos not in jogos:
                jogos.append(escolhidos)

        resultado = real["dezenas"]

        # Medir acertos
        acertos_ranking = {}
        for topn in [qtd_dez, 10, 15, 20]:
            if topn > max_num:
                continue
            acertos_ranking[topn] = len(set(ranking[:topn]) & resultado)

        acertos_jogos = []
        for j in jogos:
            ac = len(set(j) & resultado)
            acertos_jogos.append({"dezenas": j, "acertos": ac,
                                  "acertou": sorted(set(j) & resultado)})

        melhor_jogo = max(acertos_jogos, key=lambda x: x["acertos"])

        resultados.append({
            "concurso": real["numero"],
            "data": real["dt"].strftime("%d/%m/%Y"),
            "resultado": sorted(resultado),
            "padroes_usados": padroes_usados,
            "ranking_top": {k: v for k, v in acertos_ranking.items()},
            "jogos": acertos_jogos,
            "melhor_jogo": melhor_jogo["acertos"],
            "top_numeros": ranking[:qtd_dez],
        })

    # Estatísticas agregadas
    baseline = qtd_dez * qtd_dez / max_num
    top_n_acertos = [r["ranking_top"].get(qtd_dez, 0) for r in resultados]
    melhores = [r["melhor_jogo"] for r in resultados]
    todos_jogos_acertos = [j["acertos"] for r in resultados for j in r["jogos"]]

    # Premios
    if jogo == "lotofacil":
        premio_min = 11
        premios = {11: "R$6", 12: "R$12", 13: "R$30", 14: "R$1.500", 15: "Jackpot"}
    else:
        premio_min = 4
        premios = {4: "Quadra", 5: "Quina", 6: "Sena"}

    premios_ganhos = sum(1 for a in todos_jogos_acertos if a >= premio_min)
    premios_detalhe = {}
    for a in todos_jogos_acertos:
        if a >= premio_min and a in premios:
            premios_detalhe[premios[a]] = premios_detalhe.get(premios[a], 0) + 1

    diagnostico = []
    media_top = np.mean(top_n_acertos)
    media_jogos = np.mean(todos_jogos_acertos)

    if media_top > baseline * 1.15:
        diagnostico.append(f"✅ Ranking Top {qtd_dez} acima do baseline ({media_top:.1f} vs {baseline:.1f})")
    else:
        diagnostico.append(f"⚠️ Ranking Top {qtd_dez} próximo do baseline ({media_top:.1f} vs {baseline:.1f})")

    if media_jogos > baseline:
        diagnostico.append(f"✅ Jogos gerados acima do aleatório ({media_jogos:.1f} vs {baseline:.1f})")
    else:
        diagnostico.append(f"⚠️ Jogos gerados no nível do aleatório ({media_jogos:.1f} vs {baseline:.1f})")

    if premios_ganhos > 0:
        diagnostico.append(f"🏆 {premios_ganhos} prêmio(s) em {len(todos_jogos_acertos)} jogos simulados")
    else:
        diagnostico.append(f"❌ Nenhum prêmio em {len(todos_jogos_acertos)} jogos simulados")

    # Recomendações
    recomendacoes = []
    if len(padroes_db) < 50:
        recomendacoes.append("🔬 Rodar mais rodadas de prospecção (banco pequeno)")
    if media_top > baseline * 1.2 and media_jogos <= baseline * 1.05:
        recomendacoes.append("🎯 Concentrar jogos nos Top números (ranking bom, geração dispersa)")
    if max(top_n_acertos) - min(top_n_acertos) > qtd_dez * 0.4:
        recomendacoes.append("📊 Alta variância — considerar mais padrões ou meta-aprendizado")
    if not recomendacoes:
        recomendacoes.append("👍 Sistema operando bem — continuar prospectando")

    return {
        "jogo": jogo,
        "nome": info["nome"],
        "concursos_avaliados": len(resultados),
        "padroes_no_banco": len(padroes_db),
        "baseline": round(baseline, 2),
        "media_top_n": round(media_top, 2),
        "media_jogos": round(media_jogos, 2),
        "melhor_jogo_max": max(melhores),
        "premios_ganhos": premios_ganhos,
        "premios_detalhe": premios_detalhe,
        "diagnostico": diagnostico,
        "recomendacoes": recomendacoes,
        "resultados": resultados,
    }


def imprimir_avaliacao(r: dict):
    """Imprime avaliação formatada."""
    info = JOGOS[r["jogo"]]
    qtd_dez = info["qtd_dezenas"]

    print(f"\n{'='*75}")
    print(f"  {r['nome']} — Avaliação Retroativa ({r['concursos_avaliados']} concursos)")
    print(f"  Banco: {r['padroes_no_banco']} padrões ativos")
    print(f"{'='*75}")

    for res in r["resultados"]:
        data = res["data"]
        num = res["concurso"]
        resultado_str = " ".join(f"{d:02d}" for d in res["resultado"])
        top_str = " ".join(f"{d:02d}" for d in sorted(res["top_numeros"]))
        ac_top = res["ranking_top"].get(qtd_dez, 0)

        print(f"\n  #{num} ({data})  Resultado: {resultado_str}")
        print(f"    Top {qtd_dez}: {top_str} → {ac_top} acertos")

        for i, j in enumerate(res["jogos"], 1):
            dez = " ".join(f"{d:02d}" for d in j["dezenas"])
            ac = j["acertos"]
            ac_str = " ".join(f"{d:02d}" for d in j["acertou"]) if j["acertou"] else "-"
            premio = ""
            if r["jogo"] == "lotofacil" and ac >= 11:
                premio = " ← PRÊMIO!"
            elif r["jogo"] == "megasena" and ac >= 4:
                premio = " ← PRÊMIO!"
            print(f"    Jogo {i}: {dez} → {ac} [{ac_str}]{premio}")

    print(f"\n  {'─'*70}")
    print(f"  RESUMO")
    print(f"  {'─'*70}")
    print(f"  Baseline aleatório:     {r['baseline']}")
    print(f"  Média Top {qtd_dez}:            {r['media_top_n']}")
    print(f"  Média jogos gerados:    {r['media_jogos']}")
    print(f"  Melhor jogo (max):      {r['melhor_jogo_max']}")
    if r["premios_detalhe"]:
        det = ", ".join(f"{v}x {k}" for k, v in r["premios_detalhe"].items())
        print(f"  Prêmios:                {det}")
    else:
        print(f"  Prêmios:                nenhum")

    print(f"\n  DIAGNÓSTICO")
    for d in r["diagnostico"]:
        print(f"    {d}")

    print(f"\n  RECOMENDAÇÕES")
    for rec in r["recomendacoes"]:
        print(f"    {rec}")
    print()
