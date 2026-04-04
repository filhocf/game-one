"""Banco de dados SQLite para resultados de loterias."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "loterias.db"


def conectar() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _criar_tabelas(conn)
    return conn


def _criar_tabelas(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS concursos (
            jogo TEXT NOT NULL,
            numero INTEGER NOT NULL,
            data TEXT NOT NULL,
            local TEXT DEFAULT '',
            acumulado INTEGER DEFAULT 0,
            PRIMARY KEY (jogo, numero)
        );
        CREATE TABLE IF NOT EXISTS dezenas (
            jogo TEXT NOT NULL,
            numero INTEGER NOT NULL,
            dezena INTEGER NOT NULL,
            posicao INTEGER NOT NULL,
            PRIMARY KEY (jogo, numero, posicao),
            FOREIGN KEY (jogo, numero) REFERENCES concursos(jogo, numero)
        );
        CREATE INDEX IF NOT EXISTS idx_dezenas_dezena ON dezenas(jogo, dezena);
        CREATE INDEX IF NOT EXISTS idx_concursos_data ON concursos(jogo, data);
    """)


def ultimo_concurso_salvo(conn: sqlite3.Connection, jogo: str) -> int:
    row = conn.execute(
        "SELECT MAX(numero) as ultimo FROM concursos WHERE jogo = ?", (jogo,)
    ).fetchone()
    return row["ultimo"] or 0


def inserir_concurso(conn: sqlite3.Connection, jogo: str, dados: dict):
    conn.execute(
        "INSERT OR IGNORE INTO concursos (jogo, numero, data, local, acumulado) VALUES (?, ?, ?, ?, ?)",
        (jogo, dados["numero"], dados["data"], dados.get("local", ""), int(dados.get("acumulado", False))),
    )
    for i, d in enumerate(dados["dezenas"]):
        conn.execute(
            "INSERT OR IGNORE INTO dezenas (jogo, numero, dezena, posicao) VALUES (?, ?, ?, ?)",
            (jogo, dados["numero"], int(d), i),
        )


def total_concursos(conn: sqlite3.Connection, jogo: str) -> int:
    return conn.execute("SELECT COUNT(*) FROM concursos WHERE jogo = ?", (jogo,)).fetchone()[0]
