"""Análise estatística dos resultados de loterias."""

from collections import Counter
from itertools import combinations

import pandas as pd
from . import db


def carregar_df(jogo: str) -> pd.DataFrame:
    conn = db.conectar()
    df = pd.read_sql_query("""
        SELECT c.numero, c.data, c.local,
               GROUP_CONCAT(d.dezena ORDER BY d.posicao) as dezenas_str
        FROM concursos c
        JOIN dezenas d ON c.jogo = d.jogo AND c.numero = d.numero
        WHERE c.jogo = ?
        GROUP BY c.numero
        ORDER BY c.numero
    """, conn, params=(jogo,))
    conn.close()

    if df.empty:
        return df

    df["dezenas"] = df["dezenas_str"].apply(lambda s: [int(x) for x in s.split(",")])
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["dia_semana"] = df["data"].dt.weekday
    df["mes"] = df["data"].dt.month
    df["soma"] = df["dezenas"].apply(sum)
    df["pares"] = df["dezenas"].apply(lambda ds: sum(1 for d in ds if d % 2 == 0))
    return df


def frequencia(df: pd.DataFrame, max_numero: int) -> dict[int, int]:
    contagem = Counter()
    for dezenas in df["dezenas"]:
        contagem.update(dezenas)
    return {n: contagem.get(n, 0) for n in range(1, max_numero + 1)}


def atraso(df: pd.DataFrame, max_numero: int) -> dict[int, int]:
    ultimo_concurso = df["numero"].max()
    ultima_aparicao = {}
    for _, row in df.iterrows():
        for d in row["dezenas"]:
            ultima_aparicao[d] = max(ultima_aparicao.get(d, 0), row["numero"])
    return {n: ultimo_concurso - ultima_aparicao.get(n, 0) for n in range(1, max_numero + 1)}


def pares_frequentes(df: pd.DataFrame, top: int = 20) -> list[tuple]:
    contagem = Counter()
    for dezenas in df["dezenas"]:
        for par in combinations(sorted(dezenas), 2):
            contagem[par] += 1
    return contagem.most_common(top)


def faixa_soma(df: pd.DataFrame) -> dict:
    return {
        "media": float(df["soma"].mean()),
        "mediana": float(df["soma"].median()),
        "std": float(df["soma"].std()),
        "faixa_ideal": (
            int(df["soma"].mean() - df["soma"].std()),
            int(df["soma"].mean() + df["soma"].std()),
        ),
    }
