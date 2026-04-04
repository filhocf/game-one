"""Descoberta automática de padrões em resultados de loterias usando ML."""

import pickle
import time
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler

from . import db
from .coleta import JOGOS

warnings.filterwarnings("ignore")

MODEL_DIR = Path(__file__).parent.parent.parent / "data" / "modelos"


def carregar_features(jogo: str) -> pd.DataFrame:
    conn = db.conectar()
    info = JOGOS[jogo]
    max_num = info["max_numero"]

    rows = conn.execute("""
        SELECT c.numero, c.data, c.local, c.acumulado,
               GROUP_CONCAT(d.dezena ORDER BY d.posicao) as dezenas_str
        FROM concursos c
        JOIN dezenas d ON c.jogo = d.jogo AND c.numero = d.numero
        WHERE c.jogo = ?
        GROUP BY c.numero ORDER BY c.numero
    """, (jogo,)).fetchall()
    conn.close()

    records = []
    prev_dt = None
    for row in rows:
        dezenas = sorted([int(x) for x in row["dezenas_str"].split(",")])
        dt = datetime.strptime(row["data"], "%d/%m/%Y")

        r = {f"n{n:02d}": int(n in dezenas) for n in range(1, max_num + 1)}
        t = max_num // 3

        r.update({
            "concurso": row["numero"],
            "dia_semana": dt.weekday(),
            "dia_mes": dt.day,
            "mes": dt.month,
            "ano": dt.year,
            "semana_ano": dt.isocalendar()[1],
            "acumulado": row["acumulado"],
            "soma": sum(dezenas),
            "amplitude": dezenas[-1] - dezenas[0],
            "pares": sum(1 for d in dezenas if d % 2 == 0),
            "primos": sum(1 for d in dezenas if d in {2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59}),
            "consecutivos": sum(1 for i in range(len(dezenas)-1) if dezenas[i+1] - dezenas[i] == 1),
            "dias_desde_anterior": (dt - prev_dt).days if prev_dt else 0,
            "terco_baixo": sum(1 for d in dezenas if d <= t),
            "terco_medio": sum(1 for d in dezenas if t < d <= 2*t),
            "terco_alto": sum(1 for d in dezenas if d > 2*t),
            "dezenas": dezenas,
        })

        for u in range(10):
            r[f"final_{u}"] = sum(1 for d in dezenas if d % 10 == u)

        local = row["local"] or ""
        r["uf"] = local.split(",")[-1].strip() if "," in local else ""

        records.append(r)
        prev_dt = dt

    df = pd.DataFrame(records)

    if df["uf"].nunique() > 1:
        le = LabelEncoder()
        df["uf_cod"] = le.fit_transform(df["uf"].fillna(""))
    else:
        df["uf_cod"] = 0
    df.drop(columns=["uf"], inplace=True)

    return df


def _features_contextuais():
    return [
        "concurso", "dia_semana", "dia_mes", "mes", "ano", "semana_ano",
        "acumulado", "soma", "amplitude", "pares", "primos", "consecutivos",
        "dias_desde_anterior", "terco_baixo", "terco_medio", "terco_alto",
        "final_0", "final_1", "final_2", "final_3", "final_4",
        "final_5", "final_6", "final_7", "final_8", "final_9", "uf_cod",
    ]


def _construir_lags(df: pd.DataFrame, max_num: int) -> tuple[pd.DataFrame, list[str]]:
    ctx_cols = _features_contextuais()
    lag_data = {}

    for n in range(1, max_num + 1):
        col = f"n{n:02d}"

        # Lags
        for lag in [1, 2, 3, 5, 10]:
            lag_data[f"{col}_lag{lag}"] = df[col].shift(lag).fillna(0).astype(int)

        # Atraso
        atraso = []
        ultimo = 0
        for i, val in enumerate(df[col]):
            if val == 1:
                ultimo = i
            atraso.append(i - ultimo)
        lag_data[f"{col}_atraso"] = atraso

        # Médias móveis: 5, 10, 20, 50
        for w in [5, 10, 20, 50]:
            lag_data[f"{col}_freq{w}"] = df[col].rolling(w, min_periods=1).mean().shift(1).fillna(0)

        # Tendência: freq5 - freq50 (subindo ou descendo?)
        lag_data[f"{col}_tend"] = lag_data[f"{col}_freq5"] - lag_data[f"{col}_freq50"]

    lag_df = pd.DataFrame(lag_data, index=df.index)
    df = pd.concat([df, lag_df], axis=1)

    feature_cols = ctx_cols.copy()
    for n in range(1, max_num + 1):
        col = f"n{n:02d}"
        for lag in [1, 2, 3, 5, 10]:
            feature_cols.append(f"{col}_lag{lag}")
        feature_cols.append(f"{col}_atraso")
        for w in [5, 10, 20, 50]:
            feature_cols.append(f"{col}_freq{w}")
        feature_cols.append(f"{col}_tend")

    return df.dropna().reset_index(drop=True), feature_cols


def _treinar_ensemble(X_train, y_train, X_pred):
    """Treina 3 modelos e retorna média das probabilidades."""
    gb = GradientBoostingClassifier(
        n_estimators=150, max_depth=3, learning_rate=0.05,
        random_state=42, min_samples_leaf=20, subsample=0.8
    )
    rf = RandomForestClassifier(
        n_estimators=100, max_depth=5, random_state=42, min_samples_leaf=15
    )
    lr = LogisticRegression(max_iter=500, random_state=42, C=0.1)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    X_pred_scaled = scaler.transform(X_pred)

    probs = []
    for model, X_t, X_p in [
        (gb, X_train, X_pred),
        (rf, X_train, X_pred),
        (lr, X_scaled, X_pred_scaled),
    ]:
        model.fit(X_t, y_train)
        p = model.predict_proba(X_p)
        probs.append(p[0][1] if len(p[0]) > 1 else 0.0)

    return np.mean(probs), gb  # retorna GB pra feature importance


def descobrir_padroes(jogo: str, salvar: bool = True) -> dict:
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    df = carregar_features(jogo)
    df, feature_cols = _construir_lags(df, max_num)

    resultados = {}
    importancias_globais = {}

    print(f"\n  Treinando ensemble (3 modelos × {max_num} números)...", flush=True)

    for n in range(1, max_num + 1):
        col_alvo = f"n{n:02d}"
        X = df[feature_cols].iloc[:-1].values
        y = df[col_alvo].iloc[1:].values

        split = int(len(X) * 0.8)
        X_train = X[:split]
        y_train = y[:split]

        ultimo = df[feature_cols].iloc[-1:].values
        prob, gb_model = _treinar_ensemble(X_train, y_train, ultimo)

        for fname, imp in zip(feature_cols, gb_model.feature_importances_):
            importancias_globais[fname] = importancias_globais.get(fname, 0) + imp

        resultados[n] = {"prob": round(float(prob), 4)}

    if salvar:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        path = MODEL_DIR / f"{jogo}_resultado.pkl"
        pickle.dump(resultados, path.open("wb"))
        print(f"  Resultados salvos em {path}")

    top_features = sorted(importancias_globais.items(), key=lambda x: -x[1])[:30]
    freq_esperada = info["qtd_dezenas"] / max_num

    return {
        "jogo": jogo, "nome": info["nome"], "total_concursos": len(df),
        "freq_esperada": round(freq_esperada, 4), "numeros": resultados,
        "top_features": top_features, "max_numero": max_num,
        "qtd_dezenas": info["qtd_dezenas"],
    }


def correlacoes(jogo: str) -> dict:
    """Analisa correlações entre features contextuais e números sorteados."""
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    df = carregar_features(jogo)

    resultados = {}

    # 1. Dia da semana
    print(f"\n  Analisando correlações para {info['nome']}...", flush=True)
    dias_nome = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    dia_freq = {}
    for dia in sorted(df["dia_semana"].unique()):
        sub = df[df["dia_semana"] == dia]
        if len(sub) < 10:
            continue
        freqs = {}
        for n in range(1, max_num + 1):
            freqs[n] = round(sub[f"n{n:02d}"].mean(), 3)
        dia_freq[dias_nome[dia]] = {"concursos": len(sub), "freq": freqs}
    resultados["dia_semana"] = dia_freq

    # 2. Mês
    mes_freq = {}
    for mes in sorted(df["mes"].unique()):
        sub = df[df["mes"] == mes]
        if len(sub) < 10:
            continue
        freqs = {}
        for n in range(1, max_num + 1):
            freqs[n] = round(sub[f"n{n:02d}"].mean(), 3)
        mes_freq[mes] = {"concursos": len(sub), "freq": freqs}
    resultados["mes"] = mes_freq

    # 3. UF (localização)
    conn = db.conectar()
    rows = conn.execute("""
        SELECT c.local, GROUP_CONCAT(d.dezena) as dezenas
        FROM concursos c
        JOIN dezenas d ON c.jogo = d.jogo AND c.numero = d.numero
        WHERE c.jogo = ? AND c.local != ''
        GROUP BY c.numero
    """, (jogo,)).fetchall()
    conn.close()

    uf_counts = {}
    for row in rows:
        local = row["local"] or ""
        uf = local.split(",")[-1].strip() if "," in local else ""
        if uf:
            uf_counts[uf] = uf_counts.get(uf, 0) + 1

    uf_freq = {}
    for uf in sorted(uf_counts, key=lambda u: -uf_counts[u])[:10]:
        sub = df[df.apply(lambda r: True, axis=1)]  # placeholder
        # Filtrar por UF no dataframe original
        mask = []
        conn2 = db.conectar()
        uf_concursos = conn2.execute("""
            SELECT numero FROM concursos WHERE jogo = ? AND local LIKE ?
        """, (jogo, f"%{uf}")).fetchall()
        conn2.close()
        uf_nums = {r["numero"] for r in uf_concursos}
        sub = df[df["concurso"].isin(uf_nums)]
        if len(sub) < 10:
            continue
        freqs = {}
        for n in range(1, max_num + 1):
            freqs[n] = round(sub[f"n{n:02d}"].mean(), 3)
        uf_freq[uf] = {"concursos": len(sub), "freq": freqs}
    resultados["uf"] = uf_freq

    # 4. Encontrar desvios significativos
    freq_global = {n: round(df[f"n{n:02d}"].mean(), 3) for n in range(1, max_num + 1)}
    resultados["freq_global"] = freq_global

    desvios = []
    for dim_nome, dim_data in [("dia_semana", dia_freq), ("mes", mes_freq), ("uf", uf_freq)]:
        for grupo, dados in dim_data.items():
            for n in range(1, max_num + 1):
                freq_local = dados["freq"][n]
                freq_g = freq_global[n]
                diff = freq_local - freq_g
                if abs(diff) > 0.08:  # desvio > 8 pontos percentuais
                    desvios.append({
                        "dimensao": dim_nome, "grupo": grupo,
                        "numero": n, "freq_local": freq_local,
                        "freq_global": freq_g, "desvio": round(diff, 3),
                        "amostra": dados["concursos"],
                    })
    desvios.sort(key=lambda d: -abs(d["desvio"]))
    resultados["desvios_significativos"] = desvios[:30]

    return resultados


def backtesting(jogo: str, ultimos_n: int = 50) -> dict:
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    qtd_dezenas = info["qtd_dezenas"]
    df = carregar_features(jogo)
    df, feature_cols = _construir_lags(df, max_num)

    total = len(df)
    inicio_teste = total - ultimos_n
    treino_min = int(total * 0.6)

    if inicio_teste < treino_min:
        inicio_teste = treino_min
        ultimos_n = total - inicio_teste

    print(f"\n  Backtesting {info['nome']}: simulando {ultimos_n} concursos (ensemble)...", flush=True)

    acertos_por_concurso = []
    acertos_top_n = []

    for idx in range(inicio_teste, total):
        t0 = time.time()
        step = idx - inicio_teste + 1
        concurso_num = int(df["concurso"].iloc[idx])
        print(f"  [{step}/{ultimos_n}] Concurso {concurso_num}: treinando {max_num}×3 modelos...", end="", flush=True)

        X_train = df[feature_cols].iloc[:idx-1].values
        y_real = {n: df[f"n{n:02d}"].iloc[idx] for n in range(1, max_num + 1)}
        reais = sorted(n for n, v in y_real.items() if v == 1)

        probs = {}
        for n in range(1, max_num + 1):
            y_train = df[f"n{n:02d}"].iloc[1:idx].values
            X_t = X_train[:len(y_train)]
            feat = df[feature_cols].iloc[idx-1:idx].values
            prob, _ = _treinar_ensemble(X_t, y_train, feat)
            probs[n] = prob

        top = sorted(probs, key=lambda k: -probs[k])[:qtd_dezenas]
        acertos = len(set(top) & set(reais))
        acertos_por_concurso.append(acertos)

        top_amplo = sorted(probs, key=lambda k: -probs[k])[:qtd_dezenas * 2]
        acertos_amplo = len(set(top_amplo) & set(reais))
        acertos_top_n.append(acertos_amplo)

        elapsed = time.time() - t0
        restante = elapsed * (ultimos_n - step)
        top_str = " ".join(f"{d:02d}" for d in sorted(top))
        real_str = " ".join(f"{d:02d}" for d in reais)
        print(f" {elapsed:.1f}s | acertos={acertos} | previsto=[{top_str}] real=[{real_str}] | ETA {restante:.0f}s", flush=True)

    acertos_arr = np.array(acertos_por_concurso)
    acertos_amplo_arr = np.array(acertos_top_n)
    baseline = qtd_dezenas * qtd_dezenas / max_num

    return {
        "jogo": jogo, "nome": info["nome"], "concursos_testados": ultimos_n,
        "acertos_media": round(float(acertos_arr.mean()), 2),
        "acertos_mediana": int(np.median(acertos_arr)),
        "acertos_max": int(acertos_arr.max()),
        "acertos_min": int(acertos_arr.min()),
        "acertos_std": round(float(acertos_arr.std()), 2),
        "acertos_amplo_media": round(float(acertos_amplo_arr.mean()), 2),
        "baseline_aleatorio": round(baseline, 2),
        "distribuicao": dict(zip(*np.unique(acertos_arr, return_counts=True))),
    }


def gerar_sugestoes(resultado: dict, qtd_jogos: int = 5) -> list[dict]:
    nums = resultado["numeros"]
    max_num = resultado["max_numero"]
    qtd = resultado["qtd_dezenas"]

    jogos = []
    probs = np.array([nums[n]["prob"] for n in range(1, max_num + 1)])
    if probs.sum() == 0:
        probs = np.ones(max_num) / max_num
    else:
        probs = probs / probs.sum()

    for _ in range(qtd_jogos * 20):
        if len(jogos) >= qtd_jogos:
            break
        escolhidos = sorted(np.random.choice(
            range(1, max_num + 1), size=qtd, replace=False, p=probs
        ))
        escolhidos = [int(n) for n in escolhidos]
        if escolhidos in [j["dezenas"] for j in jogos]:
            continue
        score = sum(nums[n]["prob"] for n in escolhidos)
        jogos.append({"dezenas": escolhidos, "score": round(score, 4)})

    jogos.sort(key=lambda j: -j["score"])
    return jogos
