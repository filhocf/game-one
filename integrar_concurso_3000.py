"""Integração Ramo A + Ramo B + Diagnóstico para Mega-Sena concurso 3000."""

import json
from collections import Counter
from game_one.sugerir import sugerir
from game_one.wheeling import gerar_wheel
from game_one.filtros import avaliar, PERFIS
from game_one.anticrowd import score_impopularidade, rankear
from game_one.diagnostico import diagnosticar
from game_one.caos import _carregar_concursos

JOGO = "megasena"
PREV_DEZENAS = {9, 24, 26, 38, 45, 58}  # Concurso 2999


def run():
    concursos = _carregar_concursos(JOGO)

    # ── Ramo A: Sugestões inteligentes ──
    print("=" * 70)
    print("  RAMO A — Sugestões Inteligentes (10 jogos)")
    print("=" * 70)
    ramo_a = sugerir(JOGO, qtd_jogos=10)
    jogos_a = ramo_a["jogos"]
    for i, j in enumerate(jogos_a, 1):
        dez = " ".join(f"{d:02d}" for d in j["dezenas"])
        print(f"  Jogo {i}: {dez}  (score={j['score']})")

    # ── Ramo B: Wheeling ──
    print(f"\n{'=' * 70}")
    print("  RAMO B — Wheeling System (cobertura)")
    print("=" * 70)
    freq = Counter()
    for c in concursos[-30:]:
        freq.update(c["dezenas"])
    pool = sorted(n for n, _ in freq.most_common(18))
    print(f"  Pool: {' '.join(f'{n:02d}' for n in pool)}")

    wheel = gerar_wheel(pool, JOGO, garantia=3, max_bilhetes=30,
                        prev_dezenas=PREV_DEZENAS)
    jogos_b_raw = wheel["bilhetes"]
    jogos_b = rankear(JOGO, jogos_b_raw)
    for i, j in enumerate(jogos_b, 1):
        dez = " ".join(f"{d:02d}" for d in j["dezenas"])
        print(f"  Jogo {i}: {dez}  (impopularidade={j['impopularidade']:.2f})")

    # ── Diagnóstico ──
    print(f"\n{'=' * 70}")
    print("  DIAGNÓSTICO")
    print("=" * 70)
    diag = diagnosticar(JOGO)
    print(f"  Veredito: {diag['veredito']}")
    print(f"  Sinais: {', '.join(diag['sinais_estrutura'])}")
    print(f"  PE={diag['entropy']['permutation_entropy']}  DET={diag['rqa']['DET']}  "
          f"LAM={diag['rqa']['LAM']}  λ={diag['lyapunov']['lyapunov']}")

    # ── Integração ──
    print(f"\n{'=' * 70}")
    print("  INTEGRAÇÃO A+B+DIAGNÓSTICO — 10 jogos otimizados")
    print("=" * 70)

    # Scores por número do Ramo A
    scores_a = {}
    for n, s in ramo_a["top_numeros"]:
        scores_a[n] = s

    # Frequência no pool do Ramo B (números que passaram nos filtros)
    nums_b = Counter()
    for b in jogos_b_raw:
        for d in b:
            nums_b[d] += 1
    max_b = max(nums_b.values()) if nums_b else 1

    # Diagnóstico: viés por frequência recente (dezenas quentes/frias)
    freq_recente = Counter()
    for c in concursos[-50:]:
        freq_recente.update(c["dezenas"])
    freq_esperada = 50 * 6 / 60  # ~5.0
    vies = {}
    for n in range(1, 61):
        desvio = (freq_recente.get(n, 0) - freq_esperada) / freq_esperada
        if abs(desvio) > 0.3:  # >30% de desvio = viés
            vies[n] = desvio

    if vies:
        print(f"\n  Viés detectado (diagnóstico): {len(vies)} dezenas com desvio >30%")
        quentes = sorted([(n, d) for n, d in vies.items() if d > 0], key=lambda x: -x[1])[:5]
        frias = sorted([(n, d) for n, d in vies.items() if d < 0], key=lambda x: x[1])[:5]
        if quentes:
            print(f"    Quentes: {', '.join(f'{n:02d}(+{d:.0%})' for n, d in quentes)}")
        if frias:
            print(f"    Frias:   {', '.join(f'{n:02d}({d:.0%})' for n, d in frias)}")

    # Score integrado por número
    score_integrado = {}
    for n in range(1, 61):
        s = 0.0
        # Ramo A: score do caos (peso 0.5)
        s += scores_a.get(n, 0) * 0.5
        # Ramo B: presença no wheeling (peso 0.3)
        s += (nums_b.get(n, 0) / max_b) * 0.3
        # Diagnóstico: viés (peso 0.2) — quentes ganham bonus
        if n in vies and vies[n] > 0:
            s += vies[n] * 0.2
        score_integrado[n] = s

    # Gerar candidatos: todas as combinações dos top 20 números
    ranking = sorted(range(1, 61), key=lambda n: -score_integrado[n])
    top_nums = ranking[:20]

    # Gerar jogos por sampling ponderado
    import numpy as np
    np.random.seed(3000)  # Seed = concurso alvo

    weights = np.array([score_integrado[n] for n in top_nums])
    weights = weights - weights.min() + 0.01
    weights = weights / weights.sum()

    candidatos = []
    tentativas = 0
    while len(candidatos) < 200 and tentativas < 5000:
        tentativas += 1
        escolhidos = sorted(np.random.choice(top_nums, size=6, replace=False, p=weights))
        dezenas = list(escolhidos)
        # Filtro estrutural
        r = avaliar(JOGO, dezenas, PREV_DEZENAS)
        if r["passou"]:
            candidatos.append(dezenas)

    # Rankear por score_final = score_integrado_medio + impopularidade
    jogos_finais = []
    for dez in candidatos:
        s_int = sum(score_integrado[d] for d in dez) / 6
        imp = score_impopularidade(JOGO, dez)
        score_final = s_int * 0.6 + imp * 0.4
        jogos_finais.append({"dezenas": dez, "score_final": round(score_final, 3),
                             "score_int": round(s_int, 3), "imp": round(imp, 2)})

    # Deduplica e pega top 10
    seen = set()
    unicos = []
    for j in sorted(jogos_finais, key=lambda x: -x["score_final"]):
        key = tuple(j["dezenas"])
        if key not in seen:
            seen.add(key)
            unicos.append(j)
        if len(unicos) >= 10:
            break

    print()
    for i, j in enumerate(unicos, 1):
        dez = " ".join(f"{d:02d}" for d in j["dezenas"])
        print(f"  Jogo {i}: {dez}  (score_final={j['score_final']})")

    # ── Salvar markdown ──
    md = ["# Jogos Mega-Sena — Concurso 3000 (25/04/2026)\n"]
    md.append(f"Gerado em: 25/04/2026 | Último resultado (2999): {' '.join(f'{d:02d}' for d in sorted(PREV_DEZENAS))}\n")
    md.append(f"Diagnóstico: {diag['veredito']} | Sinais: {', '.join(diag['sinais_estrutura'])}\n")

    md.append("\n## Ramo A (Previsão)\n")
    for i, j in enumerate(jogos_a, 1):
        dez = " ".join(f"{d:02d}" for d in j["dezenas"])
        md.append(f"Jogo {i}: {dez} (score={j['score']})\n")

    md.append("\n## Ramo B (Cobertura)\n")
    md.append(f"Pool: {' '.join(f'{d:02d}' for d in pool)} | {wheel['n_bilhetes']} bilhetes | Cobertura: {wheel['cobertura_pct']:.0%}\n\n")
    for i, j in enumerate(jogos_b, 1):
        dez = " ".join(f"{d:02d}" for d in j["dezenas"])
        md.append(f"Jogo {i}: {dez} (impopularidade={j['impopularidade']:.2f})\n")

    md.append("\n## Integrado (A+B+Diagnóstico)\n")
    md.append("Pesos: Ramo A 50% + Ramo B 30% + Diagnóstico 20% | Filtros estruturais + anti-crowd\n\n")
    for i, j in enumerate(unicos, 1):
        dez = " ".join(f"{d:02d}" for d in j["dezenas"])
        md.append(f"Jogo {i}: {dez} (score_final={j['score_final']})\n")

    with open("jogos-concurso-3000.md", "w") as f:
        f.writelines(md)
    print(f"\n  ✅ Salvo em jogos-concurso-3000.md")


if __name__ == "__main__":
    run()
