"""Backtesting do sugerir (caos) vs descobrir (ML) vs aleatório."""

import time
from datetime import datetime

import numpy as np

from .caos import _carregar_concursos, _gerar_hipoteses, _testar_hipotese
from .coleta import JOGOS


def backtesting_sugerir(jogo: str, ultimos_n: int = 50) -> dict:
    """Simula o sugerir em concursos passados e conta acertos."""
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    qtd_dez = info["qtd_dezenas"]

    concursos = _carregar_concursos(jogo)
    total = len(concursos)
    inicio = max(total - ultimos_n, 30)  # mínimo 30 concursos de treino
    ultimos_n = total - inicio

    print(f"\n  Backtesting sugerir {info['nome']}: {ultimos_n} concursos...", flush=True)

    acertos_caos = []
    acertos_aleatorio = []

    for idx in range(inicio, total):
        t0 = time.time()
        step = idx - inicio + 1
        concurso = concursos[idx]
        treino = concursos[:idx]

        # Testar hipóteses no histórico até idx
        hipoteses = _gerar_hipoteses(max_num)
        scores = np.zeros(max_num + 1)

        for h in hipoteses:
            r = _testar_hipotese(h, treino, max_num, qtd_dez)
            if r and r["p_valor"] < 0.15:
                nums = h["fn"](concurso)
                peso = (1 - r["p_valor"]) * abs(r["lift"] - 1)
                for n in nums:
                    if 1 <= n <= max_num:
                        scores[n] += peso * (1 if r["lift"] > 1 else -0.5)

        # Top N por score
        top_caos = sorted(range(1, max_num + 1), key=lambda n: -scores[n])[:qtd_dez]
        acertos = len(set(top_caos) & concurso["dezenas"])
        acertos_caos.append(acertos)

        # Baseline aleatório
        alea = np.random.choice(range(1, max_num + 1), size=qtd_dez, replace=False)
        acertos_aleatorio.append(len(set(alea) & concurso["dezenas"]))

        elapsed = time.time() - t0
        restante = elapsed * (ultimos_n - step)
        print(f"  [{step}/{ultimos_n}] #{concurso['numero']}: caos={acertos} | {elapsed:.1f}s | ETA {restante:.0f}s", flush=True)

    caos_arr = np.array(acertos_caos)
    alea_arr = np.array(acertos_aleatorio)
    baseline = qtd_dez * qtd_dez / max_num

    return {
        "jogo": jogo, "nome": info["nome"], "concursos_testados": ultimos_n,
        "caos_media": round(float(caos_arr.mean()), 2),
        "caos_max": int(caos_arr.max()),
        "caos_min": int(caos_arr.min()),
        "caos_std": round(float(caos_arr.std()), 2),
        "aleatorio_media": round(float(alea_arr.mean()), 2),
        "baseline_teorico": round(baseline, 2),
        "vantagem": round(float(caos_arr.mean() - baseline), 2),
        "distribuicao": dict(zip(*np.unique(caos_arr, return_counts=True))),
    }
