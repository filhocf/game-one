"""Coleta de dados das loterias da Caixa via API pública."""

import sys
import httpx
from . import db

BASE_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api"

JOGOS = {
    "megasena": {"nome": "Mega-Sena", "qtd_dezenas": 6, "max_numero": 60},
    "lotofacil": {"nome": "Lotofácil", "qtd_dezenas": 15, "max_numero": 25},
}


def buscar_concurso(jogo: str, numero: int | None = None) -> dict:
    url = f"{BASE_URL}/{jogo}/{numero}" if numero else f"{BASE_URL}/{jogo}/"
    resp = httpx.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _normalizar(dados: dict) -> dict:
    ordem = dados.get("dezenasSorteadasOrdemSorteio", [])
    return {
        "numero": dados["numero"],
        "data": dados["dataApuracao"],
        "dezenas": [int(d) for d in dados["listaDezenas"]],
        "local": dados.get("nomeMunicipioUFSorteio", ""),
        "acumulado": dados.get("acumulado", False),
        "valor_acumulado": dados.get("valorAcumuladoProximoConcurso", 0) or 0,
        "valor_estimado": dados.get("valorEstimadoProximoConcurso", 0) or 0,
        "valor_arrecadado": dados.get("valorArrecadado", 0) or 0,
        "ordem_sorteio": ",".join(str(int(d)) for d in ordem) if ordem else "",
    }


def _barra(atual, total, largura=40):
    pct = atual / total if total else 0
    preenchido = int(largura * pct)
    barra = "█" * preenchido + "░" * (largura - preenchido)
    sys.stdout.write(f"\r  [{barra}] {atual}/{total} ({pct:.0%})")
    sys.stdout.flush()


def coletar(jogo: str, anos: int = 5):
    info = JOGOS[jogo]
    conn = db.conectar()
    ultimo_salvo = db.ultimo_concurso_salvo(conn, jogo)

    # Descobrir último concurso disponível
    ultimo = buscar_concurso(jogo)
    ultimo_numero = ultimo["numero"]

    # Estimar primeiro concurso do período
    concursos_por_ano = 104 if jogo == "megasena" else 156
    primeiro = max(1, ultimo_numero - (concursos_por_ano * anos))
    inicio = max(primeiro, ultimo_salvo + 1)

    # Salvar o último se ainda não temos
    if ultimo_salvo < ultimo_numero:
        db.inserir_concurso(conn, jogo, _normalizar(ultimo))

    total = ultimo_numero - inicio + 1
    if total <= 1:
        conn.commit()
        total_db = db.total_concursos(conn, jogo)
        print(f"  {info['nome']}: banco atualizado ({total_db} concursos)")
        conn.close()
        return

    print(f"  {info['nome']}: baixando concursos {inicio} a {ultimo_numero}...")
    erros = 0
    for i, num in enumerate(range(inicio, ultimo_numero), 1):
        try:
            dados = buscar_concurso(jogo, num)
            db.inserir_concurso(conn, jogo, _normalizar(dados))
            if i % 10 == 0:
                conn.commit()
        except Exception:
            erros += 1
        _barra(i, total)

    conn.commit()
    total_db = db.total_concursos(conn, jogo)
    print(f"\n  Concluído: {total_db} concursos no banco ({erros} erros)")
    conn.close()
