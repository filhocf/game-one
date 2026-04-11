"""Prospector — busca contínua com validação rigorosa e poda."""

import random
import time
from datetime import datetime

from scipy import stats as sp_stats

from . import db
from .coleta import JOGOS
from .caos import _carregar_concursos, _gerar_hipoteses
from .gerador import gerar_hipoteses_programaticas, testar_hipotese


def _testar_recente(hipotese: dict, concursos: list[dict], max_num: int, qtd_dez: int,
                    ultimos_n: int = 50) -> dict | None:
    """Testa hipótese apenas nos últimos N concursos (validação temporal)."""
    recentes = concursos[-ultimos_n:] if len(concursos) > ultimos_n else concursos
    return testar_hipotese(hipotese, recentes, max_num, qtd_dez)


def _calcular_score(p_global: float, p_recente: float, lift_global: float, lift_recente: float) -> float:
    """Score de confiança: combina significância global + recente + força do lift."""
    # Penalizar se p_recente é muito pior que p_global (padrão decaindo)
    sig_global = max(0, 1 - p_global / 0.05)       # 0-1, quanto menor p melhor
    sig_recente = max(0, 1 - p_recente / 0.10)      # mais tolerante no recente (menos dados)
    forca = min(abs(lift_global - 1), 0.5) * 2       # 0-1, quanto mais longe de 1 melhor
    forca_recente = min(abs(lift_recente - 1), 0.5) * 2

    # Peso maior para validação recente
    return sig_global * 0.25 + sig_recente * 0.35 + forca * 0.15 + forca_recente * 0.25


def _salvar_padrao(conn, jogo: str, r_global: dict, r_recente: dict | None, formula: str):
    """Salva padrão com scores de confiança."""
    agora = datetime.now().isoformat(timespec="seconds")
    p_rec = r_recente["p_valor"] if r_recente else 1.0
    lift_rec = r_recente["lift"] if r_recente else 1.0
    score = _calcular_score(r_global["p_valor"], p_rec, r_global["lift"], lift_rec)

    conn.execute("""
        INSERT INTO padroes (jogo, nome, cat, desc, formula, p_valor, lift,
                             taxa_obs, taxa_esp, tentativas,
                             descoberto_em, ultima_validacao, concursos_na_validacao,
                             ativo, p_valor_recente, lift_recente, score_confianca)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
        ON CONFLICT(jogo, nome) DO UPDATE SET
            p_valor=excluded.p_valor, lift=excluded.lift,
            taxa_obs=excluded.taxa_obs, taxa_esp=excluded.taxa_esp,
            tentativas=excluded.tentativas,
            ultima_validacao=excluded.ultima_validacao,
            concursos_na_validacao=excluded.concursos_na_validacao,
            p_valor_recente=excluded.p_valor_recente,
            lift_recente=excluded.lift_recente,
            score_confianca=excluded.score_confianca,
            ativo = CASE WHEN excluded.score_confianca > 0.1 THEN 1 ELSE 0 END
    """, (jogo, r_global["nome"], r_global["cat"], r_global["desc"],
          formula, r_global["p_valor"], r_global["lift"],
          r_global["taxa_obs"], r_global["taxa_esp"], r_global["tentativas"],
          agora, agora, r_global["tentativas"],
          p_rec, lift_rec, round(score, 4)))


def carregar_padroes_ativos(jogo: str) -> list[dict]:
    """Carrega padrões ativos ordenados por score de confiança."""
    conn = db.conectar()
    rows = conn.execute("""
        SELECT nome, cat, desc, formula, p_valor, lift, taxa_obs, taxa_esp, tentativas,
               p_valor_recente, lift_recente, score_confianca
        FROM padroes WHERE jogo = ? AND ativo = 1
        ORDER BY score_confianca DESC
    """, (jogo,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def stats_padroes(jogo: str) -> dict:
    """Estatísticas do banco de padrões."""
    conn = db.conectar()
    total = conn.execute("SELECT COUNT(*) FROM padroes WHERE jogo=?", (jogo,)).fetchone()[0]
    ativos = conn.execute("SELECT COUNT(*) FROM padroes WHERE jogo=? AND ativo=1", (jogo,)).fetchone()[0]
    melhor = conn.execute("SELECT MIN(p_valor) FROM padroes WHERE jogo=? AND ativo=1", (jogo,)).fetchone()[0]
    melhor_score = conn.execute("SELECT MAX(score_confianca) FROM padroes WHERE jogo=? AND ativo=1", (jogo,)).fetchone()[0]
    conn.close()
    return {"total": total, "ativos": ativos, "melhor_p": melhor, "melhor_score": melhor_score}


def _podar(conn, jogo: str, verbose: bool = True) -> int:
    """Desativa padrões com score baixo ou que não se sustentam no recente."""
    podados = conn.execute("""
        UPDATE padroes SET ativo = 0
        WHERE jogo = ? AND ativo = 1 AND (
            score_confianca < 0.05
            OR (p_valor_recente > 0.3 AND p_valor > 0.03)
        )
    """, (jogo,)).rowcount
    if verbose and podados:
        print(f"    🪓 Podados {podados} padrões fracos/decadentes", flush=True)
    return podados


def prospectar_rodada(jogo: str, verbose: bool = True) -> dict:
    """Executa uma rodada de prospecção com validação rigorosa."""
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    qtd_dez = info["qtd_dezenas"]

    concursos = _carregar_concursos(jogo)
    conn = db.conectar()

    ja_testadas = {r[0] for r in conn.execute(
        "SELECT nome FROM padroes WHERE jogo=?", (jogo,)
    ).fetchall()}

    # Gerar hipóteses
    hipoteses_caos = _gerar_hipoteses(max_num)
    hipoteses_prog = gerar_hipoteses_programaticas(max_num)
    todas = hipoteses_caos + hipoteses_prog

    from .evolucao import gerar_evolucoes
    padroes_ativos = [dict(r) for r in conn.execute(
        "SELECT nome, cat, desc, p_valor, lift FROM padroes WHERE jogo=? AND ativo=1", (jogo,)
    ).fetchall()]
    evolucoes = gerar_evolucoes(padroes_ativos, max_num, qtd=80)
    todas += evolucoes

    novas = [h for h in todas if h["nome"] not in ja_testadas]
    revalidar = [h for h in todas if h["nome"] in ja_testadas and random.random() < 0.15]
    lote = novas + revalidar
    random.shuffle(lote)

    if verbose:
        n_evo = len([h for h in novas if h["cat"].startswith("evo-")])
        print(f"\n  Prospecção {info['nome']}: {len(novas)} novas ({n_evo} evoluções) + "
              f"{len(revalidar)} revalidações (banco: {len(ja_testadas)} já testadas)", flush=True)

    descobertas = 0
    invalidadas = 0

    # Correção de Bonferroni: ajustar threshold pelo número de testes
    n_testes = max(len(lote), 1)
    p_threshold = min(0.05, 0.05 * 100 / n_testes)  # mais conservador com mais testes

    for h in lote:
        # Teste global (histórico completo)
        r_global = testar_hipotese(h, concursos, max_num, qtd_dez)
        if not r_global:
            continue

        formula = f"{h['cat']}:{h['nome']}"

        if r_global["p_valor"] < p_threshold:
            # Validação temporal: testar nos últimos 50 concursos
            r_recente = _testar_recente(h, concursos, max_num, qtd_dez, ultimos_n=50)

            score = _calcular_score(
                r_global["p_valor"],
                r_recente["p_valor"] if r_recente else 1.0,
                r_global["lift"],
                r_recente["lift"] if r_recente else 1.0,
            )

            if score > 0.1:  # só salvar se score mínimo
                _salvar_padrao(conn, jogo, r_global, r_recente, formula)
                descobertas += 1
                if verbose and h["nome"] not in ja_testadas:
                    d = "↑" if r_global["lift"] > 1 else "↓"
                    rec = f" rec_p={r_recente['p_valor']:.3f}" if r_recente else " rec=N/A"
                    print(f"    ✨ NOVO: {r_global['nome']} p={r_global['p_valor']:.4f} "
                          f"lift={r_global['lift']:.2f}{d} score={score:.2f}{rec}", flush=True)
        elif h["nome"] in ja_testadas:
            conn.execute("UPDATE padroes SET ativo=0, ultima_validacao=? WHERE jogo=? AND nome=?",
                         (datetime.now().isoformat(timespec="seconds"), jogo, h["nome"]))
            invalidadas += 1

    # Poda: remover padrões que não se sustentam
    podados = _podar(conn, jogo, verbose)

    conn.commit()
    conn.close()

    stats = stats_padroes(jogo)
    if verbose:
        print(f"\n  Resultado: +{descobertas} descobertas, -{invalidadas} invalidadas, -{podados} podados")
        print(f"  Banco: {stats['ativos']} padrões ativos / {stats['total']} total"
              f" | melhor score={stats['melhor_score']}")

    return {
        "jogo": jogo, "novas_testadas": len(novas), "revalidadas": len(revalidar),
        "descobertas": descobertas, "invalidadas": invalidadas, "podados": podados, **stats,
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
            print(f"  {JOGOS[j]['nome']}: {s['ativos']} padrões ativos / {s['total']} total"
                  f" | melhor score={s['melhor_score']}")
