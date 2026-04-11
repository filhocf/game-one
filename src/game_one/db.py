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
    _migrar(conn)


def ultimo_concurso_salvo(conn: sqlite3.Connection, jogo: str) -> int:
    row = conn.execute(
        "SELECT MAX(numero) as ultimo FROM concursos WHERE jogo = ?", (jogo,)
    ).fetchone()
    return row["ultimo"] or 0


def inserir_concurso(conn: sqlite3.Connection, jogo: str, dados: dict):
    conn.execute(
        """INSERT OR IGNORE INTO concursos
           (jogo, numero, data, local, acumulado, valor_acumulado, valor_estimado, valor_arrecadado, ordem_sorteio)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (jogo, dados["numero"], dados["data"], dados.get("local", ""),
         int(dados.get("acumulado", False)),
         dados.get("valor_acumulado", 0), dados.get("valor_estimado", 0),
         dados.get("valor_arrecadado", 0), dados.get("ordem_sorteio", "")),
    )
    # Atualizar campos financeiros se já existia (podem ter sido 0 na primeira coleta)
    conn.execute(
        """UPDATE concursos SET valor_acumulado=?, valor_estimado=?, valor_arrecadado=?, ordem_sorteio=?
           WHERE jogo=? AND numero=? AND valor_acumulado=0 AND ?>0""",
        (dados.get("valor_acumulado", 0), dados.get("valor_estimado", 0),
         dados.get("valor_arrecadado", 0), dados.get("ordem_sorteio", ""),
         jogo, dados["numero"], dados.get("valor_arrecadado", 0)),
    )
    for i, d in enumerate(dados["dezenas"]):
        conn.execute(
            "INSERT OR IGNORE INTO dezenas (jogo, numero, dezena, posicao) VALUES (?, ?, ?, ?)",
            (jogo, dados["numero"], int(d), i),
        )


def total_concursos(conn: sqlite3.Connection, jogo: str) -> int:
    return conn.execute("SELECT COUNT(*) FROM concursos WHERE jogo = ?", (jogo,)).fetchone()[0]


def _migrar(conn: sqlite3.Connection):
    """Adiciona colunas novas se não existem (migração incremental)."""
    colunas = {r[1] for r in conn.execute("PRAGMA table_info(concursos)").fetchall()}
    novas = {
        "valor_acumulado": "REAL DEFAULT 0",
        "valor_estimado": "REAL DEFAULT 0",
        "valor_arrecadado": "REAL DEFAULT 0",
        "ordem_sorteio": "TEXT DEFAULT ''",
    }
    for col, tipo in novas.items():
        if col not in colunas:
            conn.execute(f"ALTER TABLE concursos ADD COLUMN {col} {tipo}")

    # Tabela de padrões descobertos (banco de conhecimento)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS padroes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jogo TEXT NOT NULL,
            nome TEXT NOT NULL,
            cat TEXT NOT NULL,
            desc TEXT NOT NULL,
            formula TEXT NOT NULL,
            p_valor REAL NOT NULL,
            lift REAL NOT NULL,
            taxa_obs REAL NOT NULL,
            taxa_esp REAL NOT NULL,
            tentativas INTEGER NOT NULL,
            descoberto_em TEXT NOT NULL,
            ultima_validacao TEXT NOT NULL,
            concursos_na_validacao INTEGER NOT NULL,
            ativo INTEGER DEFAULT 1,
            UNIQUE(jogo, nome)
        );
        CREATE INDEX IF NOT EXISTS idx_padroes_jogo ON padroes(jogo, ativo, p_valor);
    """)
    conn.commit()
