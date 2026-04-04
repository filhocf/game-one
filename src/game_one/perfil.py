"""Abordagem por perfil de jogo para Mega-Sena: prevê propriedades do sorteio, não números individuais."""

import time
import warnings
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier, RandomForestRegressor
from sklearn.linear_model import Ridge

from . import db

warnings.filterwarnings("ignore")


def _carregar_megasena() -> pd.DataFrame:
    conn = db.conectar()
    rows = conn.execute("""
        SELECT c.numero, c.data, c.acumulado,
               GROUP_CONCAT(d.dezena ORDER BY d.posicao) as dezenas_str
        FROM concursos c
        JOIN dezenas d ON c.jogo = d.jogo AND c.numero = d.numero
        WHERE c.jogo = 'megasena'
        GROUP BY c.numero ORDER BY c.numero
    """).fetchall()
    conn.close()

    from datetime import datetime
    records = []
    for row in rows:
        dezenas = sorted([int(x) for x in row["dezenas_str"].split(",")])
        dt = datetime.strptime(row["data"], "%d/%m/%Y")
        records.append({
            "concurso": row["numero"], "data": dt, "dezenas": dezenas,
            "dia_semana": dt.weekday(), "dia_mes": dt.day, "mes": dt.month,
            "acumulado": row["acumulado"],
            "soma": sum(dezenas),
            "amplitude": dezenas[-1] - dezenas[0],
            "pares": sum(1 for d in dezenas if d % 2 == 0),
            "impares": sum(1 for d in dezenas if d % 2 != 0),
            "primos": sum(1 for d in dezenas if d in {2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59}),
            "consecutivos": sum(1 for i in range(5) if dezenas[i+1] - dezenas[i] == 1),
            "terco1": sum(1 for d in dezenas if d <= 20),
            "terco2": sum(1 for d in dezenas if 21 <= d <= 40),
            "terco3": sum(1 for d in dezenas if d >= 41),
            "menor": dezenas[0],
            "maior": dezenas[-1],
            "media": np.mean(dezenas),
            "std": np.std(dezenas),
        })

    df = pd.DataFrame(records)

    # Quantos números se repetem do concurso anterior
    repeticoes = [0]
    for i in range(1, len(df)):
        prev = set(df.iloc[i-1]["dezenas"])
        curr = set(df.iloc[i]["dezenas"])
        repeticoes.append(len(prev & curr))
    df["repeticoes"] = repeticoes

    # Lags das propriedades
    props = ["soma", "amplitude", "pares", "consecutivos", "terco1", "terco2", "terco3",
             "repeticoes", "media", "std", "menor", "maior"]
    for p in props:
        for lag in [1, 2, 3]:
            df[f"{p}_lag{lag}"] = df[p].shift(lag)
        df[f"{p}_ma5"] = df[p].rolling(5, min_periods=1).mean().shift(1)
        df[f"{p}_ma10"] = df[p].rolling(10, min_periods=1).mean().shift(1)

    return df.dropna().reset_index(drop=True)


def _feature_cols():
    base = ["dia_semana", "dia_mes", "mes", "acumulado"]
    props = ["soma", "amplitude", "pares", "consecutivos", "terco1", "terco2", "terco3",
             "repeticoes", "media", "std", "menor", "maior"]
    cols = base.copy()
    for p in props:
        for lag in [1, 2, 3]:
            cols.append(f"{p}_lag{lag}")
        cols.append(f"{p}_ma5")
        cols.append(f"{p}_ma10")
    return cols


def prever_perfil(verbose: bool = True) -> dict:
    """Prevê as propriedades do próximo sorteio da Mega-Sena."""
    df = _carregar_megasena()
    feat_cols = _feature_cols()

    alvos = {
        "soma": "reg", "amplitude": "reg", "pares": "reg",
        "consecutivos": "reg", "terco1": "reg", "terco2": "reg",
        "terco3": "reg", "repeticoes": "reg", "media": "reg",
        "menor": "reg", "maior": "reg",
    }

    X = df[feat_cols].iloc[:-1].values
    ultimo = df[feat_cols].iloc[-1:].values

    split = int(len(X) * 0.8)
    previsoes = {}

    if verbose:
        print(f"\n  Prevendo perfil do próximo sorteio ({len(df)} concursos)...", flush=True)

    for alvo, tipo in alvos.items():
        y = df[alvo].iloc[1:].values
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        # Ensemble de 3 regressores
        gb = GradientBoostingRegressor(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
        rf = RandomForestRegressor(n_estimators=80, max_depth=5, random_state=42)
        lr = Ridge(alpha=1.0)

        preds = []
        erros = []
        for model in [gb, rf, lr]:
            model.fit(X_train, y_train)
            pred_test = model.predict(X_test)
            erro = np.mean(np.abs(pred_test - y_test))
            erros.append(erro)
            preds.append(model.predict(ultimo)[0])

        pred = np.mean(preds)
        erro_medio = np.mean(erros)

        # Desvio padrão histórico pra definir faixa
        std_hist = df[alvo].std()

        previsoes[alvo] = {
            "valor": round(float(pred), 1),
            "faixa": (round(float(pred - std_hist * 0.5), 1), round(float(pred + std_hist * 0.5), 1)),
            "erro_medio": round(float(erro_medio), 2),
        }

        if verbose:
            real_ultimo = df[alvo].iloc[-1]
            print(f"    {alvo:15s}: previsto={pred:.1f}  faixa=[{previsoes[alvo]['faixa'][0]:.0f}, {previsoes[alvo]['faixa'][1]:.0f}]  erro_médio={erro_medio:.1f}  (último real={real_ultimo})", flush=True)

    return previsoes


def gerar_jogos_por_perfil(previsoes: dict, qtd: int = 5, verbose: bool = True) -> list[dict]:
    """Gera combinações que encaixam no perfil previsto."""
    if verbose:
        print(f"\n  Gerando jogos que encaixam no perfil previsto...", flush=True)

    soma_min, soma_max = previsoes["soma"]["faixa"]
    amp_min, amp_max = previsoes["amplitude"]["faixa"]
    pares_alvo = round(previsoes["pares"]["valor"])
    t1_alvo = round(previsoes["terco1"]["valor"])
    t2_alvo = round(previsoes["terco2"]["valor"])
    t3_alvo = round(previsoes["terco3"]["valor"])
    consec_alvo = round(previsoes["consecutivos"]["valor"])

    jogos = []
    tentativas = 0
    max_tent = 500_000

    while len(jogos) < qtd and tentativas < max_tent:
        tentativas += 1
        nums = sorted(np.random.choice(range(1, 61), size=6, replace=False))
        soma = sum(nums)
        if not (soma_min <= soma <= soma_max):
            continue

        amp = nums[-1] - nums[0]
        if not (amp_min <= amp <= amp_max):
            continue

        pares = sum(1 for n in nums if n % 2 == 0)
        if abs(pares - pares_alvo) > 1:
            continue

        t1 = sum(1 for n in nums if n <= 20)
        t2 = sum(1 for n in nums if 21 <= n <= 40)
        t3 = sum(1 for n in nums if n >= 41)
        if abs(t1 - t1_alvo) > 1 or abs(t2 - t2_alvo) > 1 or abs(t3 - t3_alvo) > 1:
            continue

        consec = sum(1 for i in range(5) if nums[i+1] - nums[i] == 1)
        if abs(consec - consec_alvo) > 1:
            continue

        # Score: quanto mais perto do perfil, melhor
        score = 0.0
        score -= abs(soma - previsoes["soma"]["valor"]) / 50
        score -= abs(amp - previsoes["amplitude"]["valor"]) / 20
        score -= abs(pares - pares_alvo) * 0.2
        score -= abs(t1 - t1_alvo + t2 - t2_alvo + t3 - t3_alvo) * 0.1
        score -= abs(consec - consec_alvo) * 0.15

        jogos.append({
            "dezenas": [int(n) for n in nums],
            "soma": soma, "pares": pares, "amplitude": amp,
            "tercos": f"{t1}-{t2}-{t3}", "consecutivos": consec,
            "score": round(score, 3),
        })

    jogos.sort(key=lambda j: -j["score"])
    jogos = jogos[:qtd]

    if verbose:
        print(f"  {len(jogos)} jogos gerados em {tentativas} tentativas", flush=True)

    return jogos
