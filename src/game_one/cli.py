"""CLI do game-one."""

import argparse
from .coleta import coletar, JOGOS


def cmd_coletar(args):
    print("Coletando resultados da Caixa...\n")
    for jogo in _jogos(args):
        coletar(jogo, anos=args.anos)


def cmd_descobrir(args):
    from .descoberta import descobrir_padroes, gerar_sugestoes

    for jogo in _jogos(args):
        resultado = descobrir_padroes(jogo)

        print(f"\n{'='*60}")
        print(f"  {resultado['nome']} — Descoberta de Padrões")
        print(f"  {resultado['total_concursos']} concursos analisados")
        print(f"  Frequência esperada (aleatório): {resultado['freq_esperada']:.1%}")
        print(f"{'='*60}")

        print(f"\n  Features mais relevantes (descobertas pelo modelo):")
        for fname, imp in resultado["top_features"][:15]:
            print(f"    {fname:30s} importância={imp:.2f}")

        nums = resultado["numeros"]
        ranking = sorted(nums.items(), key=lambda x: -x[1]["prob"])
        esperado = resultado["freq_esperada"]

        print(f"\n  Números com probabilidade ACIMA do esperado ({esperado:.1%}):")
        acima = [(n, d) for n, d in ranking if d["prob"] > esperado]
        for n, d in acima[:15]:
            delta = d["prob"] - esperado
            print(f"    {n:2d}: prob={d['prob']:.1%} (+{delta:.1%})")

        print(f"\n  Números com probabilidade ABAIXO do esperado:")
        abaixo = [(n, d) for n, d in ranking if d["prob"] <= esperado]
        for n, d in abaixo[:10]:
            delta = esperado - d["prob"]
            print(f"    {n:2d}: prob={d['prob']:.1%} (-{delta:.1%})")

        jogos = gerar_sugestoes(resultado, args.qtd)
        print(f"\n  {'─'*60}")
        print(f"  {args.qtd} sugestões baseadas nos padrões descobertos:")
        print(f"  * Análise por ML, não garantia de acerto\n")
        for i, j in enumerate(jogos, 1):
            dezenas = " ".join(f"{d:02d}" for d in j["dezenas"])
            print(f"  Jogo {i}: {dezenas}  (score={j['score']})")


def cmd_backtesting(args):
    from .descoberta import backtesting
    from .backtesting_caos import backtesting_sugerir

    for jogo in _jogos(args):
        if args.metodo in ("ml", "todos"):
            r = backtesting(jogo, ultimos_n=args.ultimos)

            print(f"\n{'='*60}")
            print(f"  {r['nome']} — Backtesting ML ({r['concursos_testados']} concursos)")
            print(f"{'='*60}")
            print(f"\n  Acertos por concurso (top {JOGOS[jogo]['qtd_dezenas']} previstos):")
            print(f"    Média:   {r['acertos_media']:.1f} de {JOGOS[jogo]['qtd_dezenas']}")
            print(f"    Mediana: {r['acertos_mediana']}")
            print(f"    Melhor:  {r['acertos_max']}")
            print(f"    Pior:    {r['acertos_min']}")
            print(f"    Desvio:  ±{r['acertos_std']:.1f}")
            print(f"\n  Baseline aleatório: {r['baseline_aleatorio']:.1f}")
            print(f"  Vantagem do modelo: {r['acertos_media'] - r['baseline_aleatorio']:+.1f}")
            print(f"\n  Distribuição de acertos:")
            for acertos, vezes in sorted(r["distribuicao"].items()):
                barra = "█" * vezes
                print(f"    {int(acertos):2d} acertos: {barra} ({vezes}x)")

        if args.metodo in ("caos", "todos"):
            r = backtesting_sugerir(jogo, ultimos_n=args.ultimos)

            print(f"\n{'='*60}")
            print(f"  {r['nome']} — Backtesting CAOS ({r['concursos_testados']} concursos)")
            print(f"{'='*60}")
            print(f"\n  Acertos por concurso (top {JOGOS[jogo]['qtd_dezenas']} previstos):")
            print(f"    Média:   {r['caos_media']:.1f} de {JOGOS[jogo]['qtd_dezenas']}")
            print(f"    Melhor:  {r['caos_max']}")
            print(f"    Pior:    {r['caos_min']}")
            print(f"    Desvio:  ±{r['caos_std']:.1f}")
            print(f"\n  Baseline teórico: {r['baseline_teorico']:.1f}")
            print(f"  Aleatório real:   {r['aleatorio_media']:.1f}")
            print(f"  Vantagem caos:    {r['vantagem']:+.1f}")
            print(f"\n  Distribuição de acertos:")
            for acertos, vezes in sorted(r["distribuicao"].items()):
                barra = "█" * vezes
                print(f"    {int(acertos):2d} acertos: {barra} ({vezes}x)")


def cmd_conferir(args):
    from .conferir import conferir
    conferir(args.jogo if args.jogo != "todos" else None)


def cmd_perfil(args):
    from .perfil import prever_perfil, gerar_jogos_por_perfil

    previsoes = prever_perfil()

    print(f"\n{'='*60}")
    print(f"  Mega-Sena — Jogos por Perfil Previsto")
    print(f"{'='*60}")

    jogos = gerar_jogos_por_perfil(previsoes, qtd=args.qtd)

    print(f"\n  Perfil-alvo: soma~{previsoes['soma']['valor']:.0f}  "
          f"pares~{previsoes['pares']['valor']:.0f}  "
          f"consec~{previsoes['consecutivos']['valor']:.0f}  "
          f"terços~{previsoes['terco1']['valor']:.0f}-{previsoes['terco2']['valor']:.0f}-{previsoes['terco3']['valor']:.0f}")
    print(f"  * Análise por ML, não garantia de acerto\n")

    for i, j in enumerate(jogos, 1):
        dezenas = " ".join(f"{d:02d}" for d in j["dezenas"])
        print(f"  Jogo {i}: {dezenas}  (soma={j['soma']} pares={j['pares']} amp={j['amplitude']} terços={j['tercos']} consec={j['consecutivos']})")


def cmd_caos(args):
    from .caos import cacar_padroes

    for jogo in _jogos(args):
        r = cacar_padroes(jogo, top=args.top)

        print(f"{'='*70}")
        print(f"  {r['nome']} — Caça a Padrões no Caos")
        print(f"  {r['total_concursos']} concursos | {r['hipoteses_testadas']} hipóteses testadas | {r['hipoteses_validas']} válidas")
        print(f"{'='*70}")

        if not r["resultados"]:
            print("\n  Nenhum padrão significativo encontrado.")
            continue

        print(f"\n  {'#':>3}  {'p-valor':>8}  {'lift':>5}  {'taxa':>6}  {'esp':>6}  {'n':>4}  {'cat':<14} {'hipótese'}")
        print(f"  {'─'*80}")
        for i, h in enumerate(r["resultados"], 1):
            sig = "***" if h["p_valor"] < 0.01 else "** " if h["p_valor"] < 0.05 else "*  " if h["p_valor"] < 0.1 else "   "
            direcao = "↑" if h["lift"] > 1 else "↓" if h["lift"] < 1 else "="
            print(f"  {i:3d}  {h['p_valor']:8.4f}  {h['lift']:4.2f}{direcao} {h['taxa_obs']:5.1%}  {h['taxa_esp']:5.1%}  {h['tentativas']:4d}  {h['cat']:<14} {h['nome']} {sig}")
            print(f"       {h['desc']}")


def cmd_gerador(args):
    from .gerador import rodar_gerador

    for jogo in _jogos(args):
        r = rodar_gerador(jogo, top=args.top)

        print(f"{'='*70}")
        print(f"  {r['nome']} — Gerador Programático de Hipóteses")
        print(f"  {r['total_concursos']} concursos | {r['hipoteses_testadas']} combinações | {r['hipoteses_significativas']} significativas")
        print(f"{'='*70}")

        if not r["resultados"]:
            print("\n  Nenhum padrão significativo encontrado.")
            continue

        print(f"\n  {'#':>3}  {'p-valor':>8}  {'lift':>5}  {'taxa':>6}  {'esp':>6}  {'n':>4}  {'cat':<14} {'hipótese'}")
        print(f"  {'─'*80}")
        for i, h in enumerate(r["resultados"], 1):
            sig = "***" if h["p_valor"] < 0.01 else "** " if h["p_valor"] < 0.05 else "*  "
            direcao = "↑" if h["lift"] > 1 else "↓" if h["lift"] < 1 else "="
            print(f"  {i:3d}  {h['p_valor']:8.4f}  {h['lift']:4.2f}{direcao} {h['taxa_obs']:5.1%}  {h['taxa_esp']:5.1%}  {h['tentativas']:4d}  {h['cat']:<14} {h['nome']} {sig}")
            print(f"       {h['desc']}")


def cmd_prospectar(args):
    from .prospector import prospectar_continuo, prospectar_rodada, stats_padroes

    if args.continuo:
        prospectar_continuo(args.jogo, intervalo=args.intervalo)
    else:
        for jogo in _jogos(args):
            prospectar_rodada(jogo)
            s = stats_padroes(jogo)
            print(f"\n  Banco: {s['ativos']} ativos / {s['total']} total | melhor p={s['melhor_p']}")


def cmd_sugerir(args):
    from .sugerir import sugerir

    for jogo in _jogos(args):
        r = sugerir(jogo, qtd_jogos=args.qtd)

        print(f"\n{'='*70}")
        print(f"  {r['nome']} — Sugestões Inteligentes")
        print(f"  Concurso-alvo: {r['concurso_alvo']} ({r['data_alvo']}) | Lua: {r['fase_lua']}")
        print(f"  Banco: {r['padroes_no_banco']} padrões ativos | {r['padroes_usados']} aplicáveis ao próximo")
        print(f"{'='*70}")

        print(f"\n  Hipóteses ativas:")
        for h in r["hipoteses_significativas"][:8]:
            sig = "***" if h["p_valor"] < 0.01 else "** " if h["p_valor"] < 0.05 else "*  "
            direcao = "↑" if h["lift"] > 1 else "↓"
            print(f"    {h['nome']:30s} lift={h['lift']:.2f}{direcao} p={h['p_valor']:.4f} {sig}")

        print(f"\n  Top números (score do caos):")
        nums_str = "  ".join(f"{n:02d}({s:.2f})" for n, s in r["top_numeros"][:15])
        print(f"    {nums_str}")

        if r["contribuicoes"]:
            print(f"\n  Por que esses números?")
            for n, contribs in list(r["contribuicoes"].items())[:5]:
                c_str = ", ".join(f"{nome}({v:+.3f})" for nome, v in contribs[:3])
                print(f"    {n:02d}: {c_str}")

        print(f"\n  {'─'*70}")
        print(f"  {args.qtd} sugestões baseadas nos padrões do caos:")
        print(f"  * Análise estatística, não garantia de acerto\n")
        for i, j in enumerate(r["jogos"], 1):
            dezenas = " ".join(f"{d:02d}" for d in j["dezenas"])
            print(f"  Jogo {i}: {dezenas}  (score={j['score']})")


def cmd_correlacoes(args):
    from .descoberta import correlacoes

    for jogo in _jogos(args):
        r = correlacoes(jogo)
        info = JOGOS[jogo]
        freq_g = r["freq_global"]

        print(f"\n{'='*60}")
        print(f"  {info['nome']} — Análise de Correlações")
        print(f"{'='*60}")

        # Dia da semana
        print(f"\n  POR DIA DA SEMANA:")
        for dia, dados in r["dia_semana"].items():
            quentes = sorted(dados["freq"], key=lambda n: -dados["freq"][n])[:5]
            frios = sorted(dados["freq"], key=lambda n: dados["freq"][n])[:5]
            q_str = ", ".join(f"{n}({dados['freq'][n]:.0%})" for n in quentes)
            f_str = ", ".join(f"{n}({dados['freq'][n]:.0%})" for n in frios)
            print(f"    {dia} ({dados['concursos']} concursos):")
            print(f"      Quentes: {q_str}")
            print(f"      Frios:   {f_str}")

        # Mês
        meses_nome = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
                      7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
        print(f"\n  POR MÊS:")
        for mes, dados in r["mes"].items():
            quentes = sorted(dados["freq"], key=lambda n: -dados["freq"][n])[:5]
            q_str = ", ".join(f"{n}({dados['freq'][n]:.0%})" for n in quentes)
            print(f"    {meses_nome[mes]} ({dados['concursos']}x): quentes={q_str}")

        # UF
        if r["uf"]:
            print(f"\n  POR LOCALIZAÇÃO (UF):")
            for uf, dados in r["uf"].items():
                quentes = sorted(dados["freq"], key=lambda n: -dados["freq"][n])[:5]
                q_str = ", ".join(f"{n}({dados['freq'][n]:.0%})" for n in quentes)
                print(f"    {uf} ({dados['concursos']}x): quentes={q_str}")

        # Desvios significativos
        desvios = r["desvios_significativos"]
        if desvios:
            print(f"\n  DESVIOS SIGNIFICATIVOS (>8% da média global):")
            for d in desvios[:20]:
                sinal = "+" if d["desvio"] > 0 else ""
                print(f"    Nº {d['numero']:2d} em {d['dimensao']}={d['grupo']}: "
                      f"{d['freq_local']:.0%} vs {d['freq_global']:.0%} "
                      f"({sinal}{d['desvio']:.0%}, {d['amostra']} concursos)")
        else:
            print(f"\n  Nenhum desvio significativo encontrado (>8%).")


def _jogos(args) -> list[str]:
    return list(JOGOS.keys()) if args.jogo == "todos" else [args.jogo]


def main():
    parser = argparse.ArgumentParser(prog="game-one", description="Descoberta de padrões em loterias da Caixa")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("coletar", help="Baixar resultados da Caixa")
    p.add_argument("--jogo", choices=list(JOGOS) + ["todos"], default="todos")
    p.add_argument("--anos", type=int, default=5)

    p = sub.add_parser("descobrir", help="Descobrir padrões e gerar sugestões")
    p.add_argument("--jogo", choices=list(JOGOS) + ["todos"], default="todos")
    p.add_argument("--qtd", type=int, default=5, help="Quantidade de jogos sugeridos")

    p = sub.add_parser("conferir", help="Conferir apostas contra resultado real")
    p.add_argument("--jogo", choices=list(JOGOS) + ["todos"], default="todos")

    p = sub.add_parser("perfil", help="Mega-Sena: gerar jogos por perfil previsto")
    p.add_argument("--qtd", type=int, default=5, help="Quantidade de jogos")

    p = sub.add_parser("caos", help="Caçar padrões no caos (hipóteses automáticas)")
    p.add_argument("--jogo", choices=list(JOGOS) + ["todos"], default="todos")
    p.add_argument("--top", type=int, default=15, help="Quantidade de padrões no ranking")

    p = sub.add_parser("sugerir", help="Sugestões inteligentes baseadas nos padrões do caos")
    p.add_argument("--jogo", choices=list(JOGOS) + ["todos"], default="todos")
    p.add_argument("--qtd", type=int, default=5, help="Quantidade de jogos sugeridos")

    p = sub.add_parser("prospectar", help="Buscar novos padrões (contínuo ou rodada única)")
    p.add_argument("--jogo", choices=list(JOGOS) + ["todos"], default="todos")
    p.add_argument("--continuo", action="store_true", help="Rodar em loop contínuo")
    p.add_argument("--intervalo", type=int, default=5, help="Segundos entre rodadas (modo contínuo)")

    p = sub.add_parser("correlacoes", help="Analisar correlações (dia, mês, UF)")
    p.add_argument("--jogo", choices=list(JOGOS) + ["todos"], default="todos")

    p = sub.add_parser("gerador", help="Gerador programático de hipóteses combinatórias")
    p.add_argument("--jogo", choices=list(JOGOS) + ["todos"], default="todos")
    p.add_argument("--top", type=int, default=30, help="Quantidade de padrões no ranking")

    p = sub.add_parser("backtesting", help="Simular previsões em concursos passados")
    p.add_argument("--jogo", choices=list(JOGOS) + ["todos"], default="todos")
    p.add_argument("--ultimos", type=int, default=30, help="Quantos concursos simular")
    p.add_argument("--metodo", choices=["ml", "caos", "todos"], default="ml", help="Método a testar")

    sub.add_parser("tui", help="Interface visual interativa")

    args = parser.parse_args()

    if args.comando == "tui":
        from .tui import run_tui
        run_tui()
        return

    {"coletar": cmd_coletar, "descobrir": cmd_descobrir, "conferir": cmd_conferir, "perfil": cmd_perfil, "caos": cmd_caos, "sugerir": cmd_sugerir, "correlacoes": cmd_correlacoes, "gerador": cmd_gerador, "prospectar": cmd_prospectar, "backtesting": cmd_backtesting}[args.comando](args)


if __name__ == "__main__":
    main()
