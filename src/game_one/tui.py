"""TUI interativo do game-one usando Textual."""

from textual.app import App
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, Button, DataTable, Label, Select, LoadingIndicator
from textual.screen import Screen
from textual import work

from .coleta import JOGOS


class HomeScreen(Screen):
    """Tela principal com menu."""

    BINDINGS = [
        ("c", "coletar", "Coletar dados"),
        ("a", "analisar", "Análise caos"),
        ("g", "gerador", "Gerador programático"),
        ("s", "sugerir", "Sugestões"),
        ("f", "conferir", "Conferir apostas"),
        ("b", "backtesting", "Backtesting"),
        ("q", "quit", "Sair"),
    ]

    def compose(self):
        yield Header(show_clock=True)
        with Vertical(id="home"):
            yield Static(
                "🎲  [bold cyan]game-one[/]  —  Descoberta de Padrões em Loterias\n",
                id="title",
            )
            yield Static(self._status_text(), id="status")
            with Horizontal(classes="menu-row"):
                yield Button("📥 Coletar [C]", id="btn-coletar", variant="default")
                yield Button("🔍 Caos [A]", id="btn-caos", variant="primary")
                yield Button("🧬 Gerador [G]", id="btn-gerador", variant="warning")
            with Horizontal(classes="menu-row"):
                yield Button("💡 Sugestões [S]", id="btn-sugerir", variant="success")
                yield Button("✅ Conferir [F]", id="btn-conferir", variant="default")
                yield Button("📊 Backtesting [B]", id="btn-backtesting", variant="default")
            yield Static("", id="output")
        yield Footer()

    def _status_text(self) -> str:
        try:
            from . import db
            conn = db.conectar()
            lines = []
            for jogo, info in JOGOS.items():
                total = db.total_concursos(conn, jogo)
                ultimo = db.ultimo_concurso_salvo(conn, jogo)
                lines.append(f"  {info['nome']:15s}  {total:>5} concursos  (último: #{ultimo})")
            conn.close()
            return "📊 Banco de dados:\n" + "\n".join(lines)
        except Exception as e:
            return f"⚠ Banco não disponível: {e}\n  Execute 'Coletar' primeiro."

    def on_button_pressed(self, event: Button.Pressed):
        actions = {
            "btn-coletar": "coletar",
            "btn-caos": "analisar",
            "btn-gerador": "gerador",
            "btn-sugerir": "sugerir",
            "btn-conferir": "conferir",
            "btn-backtesting": "backtesting",
        }
        action = actions.get(event.button.id)
        if action:
            self.app.push_screen(action)

    def action_coletar(self):
        self.app.push_screen("coletar")

    def action_analisar(self):
        self.app.push_screen("analisar")

    def action_gerador(self):
        self.app.push_screen("gerador")

    def action_sugerir(self):
        self.app.push_screen("sugerir")

    def action_conferir(self):
        self.app.push_screen("conferir")

    def action_backtesting(self):
        self.app.push_screen("backtesting")

    def action_quit(self):
        self.app.exit()


class JogoSelectScreen(Screen):
    """Base para telas que precisam selecionar jogo."""

    BINDINGS = [("escape", "pop_screen", "Voltar")]

    def _jogo_select(self):
        options = [(info["nome"], jogo) for jogo, info in JOGOS.items()]
        options.append(("Todos", "todos"))
        return Select(options, value="lotofacil", id="jogo-select")


class ColetarScreen(JogoSelectScreen):
    def compose(self):
        yield Header()
        with VerticalScroll():
            yield Static("📥 [bold]Coletar Dados da Caixa[/]\n")
            yield self._jogo_select()
            yield Button("Iniciar coleta", id="btn-go", variant="primary")
            yield Static("", id="result")
        yield Footer()

    def on_button_pressed(self, event):
        if event.button.id == "btn-go":
            self._run_coletar()

    @work(thread=True)
    def _run_coletar(self):
        jogo = self.query_one("#jogo-select", Select).value
        result = self.query_one("#result", Static)
        result.update("⏳ Coletando...")
        try:
            from .coleta import coletar
            jogos = list(JOGOS.keys()) if jogo == "todos" else [jogo]
            for j in jogos:
                coletar(j, anos=5)
            result.update("✅ Coleta concluída!")
        except Exception as e:
            result.update(f"❌ Erro: {e}")


class CaosScreen(JogoSelectScreen):
    def compose(self):
        yield Header()
        with VerticalScroll():
            yield Static("🔍 [bold]Motor de Caos — Hipóteses Hardcoded (40)[/]\n")
            yield self._jogo_select()
            yield Button("Rodar caos", id="btn-go", variant="primary")
            yield DataTable(id="table")
        yield Footer()

    def on_button_pressed(self, event):
        if event.button.id == "btn-go":
            self._run()

    @work(thread=True)
    def _run(self):
        jogo = self.query_one("#jogo-select", Select).value
        table = self.query_one("#table", DataTable)
        table.clear(columns=True)
        table.add_columns("#", "p-valor", "lift", "taxa", "esp", "n", "cat", "hipótese")
        try:
            from .caos import cacar_padroes
            jogos = list(JOGOS.keys()) if jogo == "todos" else [jogo]
            for j in jogos:
                r = cacar_padroes(j, top=20)
                for i, h in enumerate(r["resultados"], 1):
                    d = "↑" if h["lift"] > 1 else "↓"
                    table.add_row(
                        str(i), f"{h['p_valor']:.4f}", f"{h['lift']:.2f}{d}",
                        f"{h['taxa_obs']:.1%}", f"{h['taxa_esp']:.1%}",
                        str(h["tentativas"]), h["cat"], h["nome"],
                    )
        except Exception as e:
            table.add_row("❌", str(e), "", "", "", "", "", "")


class GeradorScreen(JogoSelectScreen):
    def compose(self):
        yield Header()
        with VerticalScroll():
            yield Static("🧬 [bold]Gerador Programático — Hipóteses Combinatórias[/]\n")
            yield self._jogo_select()
            yield Button("Gerar e testar", id="btn-go", variant="warning")
            yield Static("", id="progress")
            yield DataTable(id="table")
        yield Footer()

    def on_button_pressed(self, event):
        if event.button.id == "btn-go":
            self._run()

    @work(thread=True)
    def _run(self):
        jogo = self.query_one("#jogo-select", Select).value
        progress = self.query_one("#progress", Static)
        table = self.query_one("#table", DataTable)
        table.clear(columns=True)
        table.add_columns("#", "p-valor", "lift", "taxa", "esp", "n", "cat", "hipótese")
        progress.update("⏳ Gerando hipóteses combinatórias e testando...")
        try:
            from .gerador import rodar_gerador
            jogos = list(JOGOS.keys()) if jogo == "todos" else [jogo]
            for j in jogos:
                r = rodar_gerador(j, top=30)
                progress.update(
                    f"✅ {r['hipoteses_testadas']} testadas → "
                    f"{r['hipoteses_significativas']} significativas (p<0.05)"
                )
                for i, h in enumerate(r["resultados"], 1):
                    d = "↑" if h["lift"] > 1 else "↓"
                    table.add_row(
                        str(i), f"{h['p_valor']:.4f}", f"{h['lift']:.2f}{d}",
                        f"{h['taxa_obs']:.1%}", f"{h['taxa_esp']:.1%}",
                        str(h["tentativas"]), h["cat"], h["nome"],
                    )
        except Exception as e:
            progress.update(f"❌ Erro: {e}")


class SugerirScreen(JogoSelectScreen):
    def compose(self):
        yield Header()
        with VerticalScroll():
            yield Static("💡 [bold]Sugestões Inteligentes (Caos + Estatística)[/]\n")
            yield self._jogo_select()
            yield Button("Gerar sugestões", id="btn-go", variant="success")
            yield Static("", id="result")
        yield Footer()

    def on_button_pressed(self, event):
        if event.button.id == "btn-go":
            self._run()

    @work(thread=True)
    def _run(self):
        jogo = self.query_one("#jogo-select", Select).value
        result = self.query_one("#result", Static)
        result.update("⏳ Calculando sugestões...")
        try:
            from .sugerir import sugerir
            jogos = list(JOGOS.keys()) if jogo == "todos" else [jogo]
            lines = []
            for j in jogos:
                r = sugerir(j, qtd_jogos=5)
                lines.append(f"\n[bold]{r['nome']}[/] — Concurso {r['concurso_alvo']} ({r['data_alvo']}) 🌙 {r['fase_lua']}")
                lines.append(f"{r['hipoteses_usadas']} hipóteses significativas\n")
                for i, jg in enumerate(r["jogos"], 1):
                    dez = " ".join(f"{d:02d}" for d in jg["dezenas"])
                    lines.append(f"  Jogo {i}: [bold green]{dez}[/]  (score={jg['score']})")
                lines.append("")
                top = "  ".join(f"{n:02d}({s:.2f})" for n, s in r["top_numeros"][:10])
                lines.append(f"  Top números: {top}")
            result.update("\n".join(lines))
        except Exception as e:
            result.update(f"❌ Erro: {e}")


class ConferirScreen(Screen):
    BINDINGS = [("escape", "pop_screen", "Voltar")]

    def compose(self):
        yield Header()
        with VerticalScroll():
            yield Static("✅ [bold]Conferir Apostas[/]\n")
            yield Button("Conferir", id="btn-go", variant="primary")
            yield Static("", id="result")
        yield Footer()

    def on_button_pressed(self, event):
        if event.button.id == "btn-go":
            self._run()

    @work(thread=True)
    def _run(self):
        result = self.query_one("#result", Static)
        result.update("⏳ Conferindo...")
        try:
            from .conferir import conferir as _conferir, APOSTAS, JOGOS as _J
            from .coleta import buscar_concurso
            lines = []
            for j, aposta in APOSTAS.items():
                info = _J[j]
                num = aposta["concurso"]
                try:
                    res = buscar_concurso(j, num)
                    dezenas = sorted(int(d) for d in res["listaDezenas"])
                    dez_str = " ".join(f"{d:02d}" for d in dezenas)
                    lines.append(f"\n[bold]{info['nome']}[/] — Concurso {num}")
                    lines.append(f"  Resultado: [bold yellow]{dez_str}[/]\n")
                    for i, jogo_nums in enumerate(aposta["jogos"], 1):
                        acertos = sorted(set(jogo_nums) & set(dezenas))
                        n_ac = len(acertos)
                        ac_str = " ".join(f"{d:02d}" for d in acertos) if acertos else "nenhum"
                        jogo_str = " ".join(f"{d:02d}" for d in jogo_nums)
                        premio = ""
                        if j == "lotofacil" and n_ac >= 11:
                            premio = " [bold red]← PRÊMIO![/]"
                        elif j == "megasena" and n_ac >= 4:
                            premio = " [bold red]← PRÊMIO![/]"
                        lines.append(f"  Jogo {i}: {jogo_str}")
                        lines.append(f"         {n_ac} acertos: [{ac_str}]{premio}")
                except Exception as e:
                    lines.append(f"\n{info['nome']} #{num}: não disponível ({e})")
            result.update("\n".join(lines))
        except Exception as e:
            result.update(f"❌ Erro: {e}")


class BacktestingScreen(JogoSelectScreen):
    def compose(self):
        yield Header()
        with VerticalScroll():
            yield Static("📊 [bold]Backtesting[/]\n")
            yield self._jogo_select()
            yield Button("Rodar backtesting caos", id="btn-go", variant="primary")
            yield Static("", id="result")
        yield Footer()

    def on_button_pressed(self, event):
        if event.button.id == "btn-go":
            self._run()

    @work(thread=True)
    def _run(self):
        jogo = self.query_one("#jogo-select", Select).value
        result = self.query_one("#result", Static)
        result.update("⏳ Rodando backtesting (pode demorar)...")
        try:
            from .backtesting_caos import backtesting_sugerir
            jogos = list(JOGOS.keys()) if jogo == "todos" else [jogo]
            lines = []
            for j in jogos:
                r = backtesting_sugerir(j, ultimos_n=30)
                lines.append(f"\n[bold]{r['nome']}[/] — {r['concursos_testados']} concursos")
                lines.append(f"  Média caos:      {r['caos_media']:.1f}")
                lines.append(f"  Baseline teórico: {r['baseline_teorico']:.1f}")
                lines.append(f"  Vantagem:         {r['vantagem']:+.1f}")
                lines.append(f"  Melhor: {r['caos_max']}  Pior: {r['caos_min']}")
                lines.append(f"\n  Distribuição:")
                for ac, vezes in sorted(r["distribuicao"].items()):
                    barra = "█" * vezes
                    lines.append(f"    {int(ac):2d} acertos: {barra} ({vezes}x)")
            result.update("\n".join(lines))
        except Exception as e:
            result.update(f"❌ Erro: {e}")


CSS = """
Screen {
    background: $surface;
}
#home {
    padding: 1 2;
}
#title {
    text-align: center;
    padding: 1;
}
#status {
    padding: 1;
    margin-bottom: 1;
    border: solid $primary;
}
.menu-row {
    height: auto;
    padding: 0 1;
    align: center middle;
}
.menu-row Button {
    margin: 0 1;
    min-width: 24;
}
#output, #result, #progress {
    padding: 1;
}
DataTable {
    height: auto;
    max-height: 30;
}
"""


class GameOneApp(App):
    TITLE = "game-one"
    SUB_TITLE = "Descoberta de Padrões em Loterias"
    CSS = CSS

    SCREENS = {
        "home": HomeScreen,
        "coletar": ColetarScreen,
        "analisar": CaosScreen,
        "gerador": GeradorScreen,
        "sugerir": SugerirScreen,
        "conferir": ConferirScreen,
        "backtesting": BacktestingScreen,
    }

    def on_mount(self):
        self.push_screen("home")


def run_tui():
    app = GameOneApp()
    app.run()
