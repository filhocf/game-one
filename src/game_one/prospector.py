"""Prospector — busca contínua de padrões novos, salva descobertas no banco."""

import random
import time
from datetime import datetime

from . import db
from .coleta import JOGOS
from .caos import _carregar_concursos, _gerar_hipoteses
from .gerador import gerar_hipoteses_programaticas, testar_hipotese


def _salvar_padrao(conn, jogo: str, resultado: dict, formula: str):
    """Salva ou atualiza um padrão no banco."""
    agora = datetime.now().isoformat(timespec="seconds")
    conn.execute("""
        INSERT INTO padroes (jogo, nome, cat, desc, formula, p_valor, lift,
                             taxa_obs, taxa_esp, tentativas,
                             descoberto_em, ultima_validacao, concursos_na_validacao, ativo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(jogo, nome) DO UPDATE SET
            p_valor=excluded.p_valor, lift=excluded.lift,
            taxa_obs=excluded.taxa_obs, taxa_esp=excluded.taxa_esp,
            tentativas=excluded.tentativas,
            ultima_validacao=excluded.ultima_validacao,
            concursos_na_validacao=excluded.concursos_na_validacao,
            ativo = CASE WHEN excluded.p_valor < 0.05 THEN 1 ELSE 0 END
    """, (jogo, resultado["nome"], resultado["cat"], resultado["desc"],
          formula, resultado["p_valor"], resultado["lift"],
          resultado["taxa_obs"], resultado["taxa_esp"], resultado["tentativas"],
          agora, agora, resultado["tentativas"]))


def carregar_padroes_ativos(jogo: str) -> list[dict]:
    """Carrega padrões significativos do banco."""
    conn = db.conectar()
    rows = conn.execute("""
        SELECT nome, cat, desc, formula, p_valor, lift, taxa_obs, taxa_esp, tentativas
        FROM padroes WHERE jogo = ? AND ativo = 1
        ORDER BY p_valor
    """, (jogo,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def stats_padroes(jogo: str) -> dict:
    """Estatísticas do banco de padrões."""
    conn = db.conectar()
    total = conn.execute("SELECT COUNT(*) FROM padroes WHERE jogo=?", (jogo,)).fetchone()[0]
    ativos = conn.execute("SELECT COUNT(*) FROM padroes WHERE jogo=? AND ativo=1", (jogo,)).fetchone()[0]
    melhor = conn.execute("SELECT MIN(p_valor) FROM padroes WHERE jogo=? AND ativo=1", (jogo,)).fetchone()[0]
    conn.close()
    return {"total": total, "ativos": ativos, "melhor_p": melhor}


def prospectar_rodada(jogo: str, verbose: bool = True) -> dict:
    """Executa uma rodada de prospecção: testa hipóteses e salva descobertas."""
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    qtd_dez = info["qtd_dezenas"]

    concursos = _carregar_concursos(jogo)
    conn = db.conectar()

    # Já testadas
    ja_testadas = {r[0] for r in conn.execute(
        "SELECT nome FROM padroes WHERE jogo=?", (jogo,)
    ).fetchall()}

    # Gerar hipóteses de ambos os motores
    hipoteses_caos = _gerar_hipoteses(max_num)
    hipoteses_prog = gerar_hipoteses_programaticas(max_num)
    todas = hipoteses_caos + hipoteses_prog

    # Evoluções: mutar/cruzar padrões que já funcionaram
    from .evolucao import gerar_evolucoes
    padroes_ativos = [dict(r) for r in conn.execute(
        "SELECT nome, cat, desc, p_valor, lift FROM padroes WHERE jogo=? AND ativo=1", (jogo,)
    ).fetchall()]
    evolucoes = gerar_evolucoes(padroes_ativos, max_num, qtd=80)
    todas += evolucoes

    # Filtrar as que ainda não foram testadas (ou re-validar aleatoriamente 10%)
    novas = [h for h in todas if h["nome"] not in ja_testadas]
    revalidar = [h for h in todas if h["nome"] in ja_testadas and random.random() < 0.1]
    lote = novas + revalidar
    random.shuffle(lote)

    if verbose:
        n_evo = len([h for h in novas if h["cat"].startswith("evo-")])
        print(f"\n  Prospecção {info['nome']}: {len(novas)} novas ({n_evo} evoluções) + "
              f"{len(revalidar)} revalidações (banco: {len(ja_testadas)} já testadas)", flush=True)

    descobertas = 0
    invalidadas = 0

    for h in lote:
        r = testar_hipotese(h, concursos, max_num, qtd_dez)
        if not r:
            continue

        formula = f"{h['cat']}:{h['nome']}"

        if r["p_valor"] < 0.05:
            _salvar_padrao(conn, jogo, r, formula)
            descobertas += 1
            if verbose and h["nome"] not in ja_testadas:
                d = "↑" if r["lift"] > 1 else "↓"
                print(f"    ✨ NOVO: {r['nome']} p={r['p_valor']:.4f} lift={r['lift']:.2f}{d}", flush=True)
        elif h["nome"] in ja_testadas:
            # Era significativo, agora não é mais — desativar
            conn.execute("UPDATE padroes SET ativo=0, ultima_validacao=? WHERE jogo=? AND nome=?",
                         (datetime.now().isoformat(timespec="seconds"), jogo, h["nome"]))
            invalidadas += 1

    conn.commit()
    conn.close()

    stats = stats_padroes(jogo)
    if verbose:
        print(f"\n  Resultado: +{descobertas} descobertas, -{invalidadas} invalidadas")
        print(f"  Banco: {stats['ativos']} padrões ativos / {stats['total']} total")

    return {
        "jogo": jogo, "novas_testadas": len(novas), "revalidadas": len(revalidar),
        "descobertas": descobertas, "invalidadas": invalidadas, **stats,
    }


def prospectar_continuo(jogo: str = "todos", intervalo: int = 5):
    """Prospecção contínua — roda em loop até Ctrl+C."""
    jogos = list(JOGOS.keys()) if jogo == "todos" else [jogo]

    print("🔬 Prospector iniciado — Ctrl+C para parar\n")
    rodada = 0
    try:
        while True:
            rodada += 1
            for j in jogos:
                print(f"\n── Rodada {rodada} ──")
                prospectar_rodada(j)
            print(f"\n  Próxima rodada em {intervalo}s...", flush=True)
            time.sleep(intervalo)
    except KeyboardInterrupt:
        print("\n\n🛑 Prospector encerrado.")
        for j in jogos:
            s = stats_padroes(j)
            print(f"  {JOGOS[j]['nome']}: {s['ativos']} padrões ativos / {s['total']} total")
