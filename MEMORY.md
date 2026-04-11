# MEMORY.md — game-one

## Última Sessão
- **Data**: 2026-04-11 14:24 — em andamento
- **Máquina**: sirdata (casa, servidor)
- **O que foi feito**:
  - Banco portável: `data/loterias.db` commitado no git
  - Gerador programático (`gerador.py`): 757+ hipóteses combinatórias automáticas
  - Prospector (`prospector.py`): busca contínua → banco de padrões
  - Sugerir reescrito: consulta banco de padrões (produtor/consumidor)
  - TUI (`tui.py`): interface visual Textual com todas as telas
  - Docs atualizados: SDD e user-story com F8-F11
  - Prospecção inicial: Lotofácil 47 padrões, Mega-Sena 46 padrões
  - Conferência: LF 3652 ML Jogo2=10/15, LF 3653 caos Jogo2=10/15, convergentes=10/14
  - Dados atualizados: Mega #2994 (09/04), Lotofácil #3658 (10/04)

## Conferência Lotofácil 3652 (02/04/2026 — ML)
- **Resultado**: 01 03 06 07 11 12 13 15 16 18 19 20 21 23 24
- Jogo 1: 7 acertos | Jogo 2: **10 acertos** | Jogo 3: 8 acertos

## Conferência Lotofácil 3653 (04/04/2026 — Caos)
- **Resultado**: 02 03 04 06 07 08 10 11 13 14 16 18 19 20 21
- Jogo 1: 9 acertos | Jogo 2: **10 acertos** | Jogo 3: 9 acertos
- Top convergentes (caos≥5 E ML≥3): **10/14 acertos**

## Conferência Mega-Sena 2992 (04/04/2026)
- **Resultado**: 04 17 23 33 36 49
- Melhor: 1 acerto (fraco)

## Resultados recentes (não conferidos com sugestões)
- LF 3654 (06/04): 01 02 03 04 06 07 11 15 17 19 20 22 23 24 25
- LF 3655 (07/04): 01 02 04 05 06 10 11 12 17 18 19 21 22 23 24
- LF 3656 (08/04): 03 04 06 07 08 11 12 14 15 18 19 20 21 24 25
- LF 3657 (09/04): 01 02 04 07 08 10 12 13 17 18 19 20 22 23 24
- LF 3658 (10/04): 02 03 04 05 09 10 11 12 13 16 18 20 22 23 24
- MS 2993 (07/04): 03 15 31 42 43 51
- MS 2994 (09/04): 01 10 23 31 40 55

## Banco de Padrões
- Lotofácil: 47 ativos (melhor p=8e-06)
- Mega-Sena: 46 ativos (melhor p=8.8e-05)

## Próximos Passos
- [ ] Push para origin
- [ ] Symbolic regression (PySR)
- [ ] Cross-lottery Mega↔Lotofácil
- [ ] Meta-aprendizado — pesos dinâmicos
- [ ] TUI polish — gráficos, dashboard acuidade
- [ ] Backtesting comparativo: banco de padrões vs caos puro vs ML

## Comandos
```bash
cd ~/git/game-one
uv run game-one tui                                     # interface visual
uv run game-one coletar                                 # atualizar dados
uv run game-one prospectar --jogo lotofacil              # buscar padrões
uv run game-one prospectar --continuo                    # busca contínua
uv run game-one sugerir --jogo lotofacil                 # sugestões via banco
uv run game-one gerador --jogo lotofacil --top 30        # hipóteses programáticas
uv run game-one caos --jogo lotofacil --top 20           # hipóteses hardcoded
uv run game-one conferir                                 # conferir apostas
uv run game-one backtesting --jogo lotofacil --metodo caos
```
