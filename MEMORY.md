# MEMORY.md — game-one

## Última Sessão
- **Data**: 2026-04-18 ~18:00–22:00
- **Máquina**: sirdata (casa, servidor)
- **O que foi feito**:
  - **Ramo B completo** — nova abordagem: em vez de prever números, otimizar cobertura e maximizar prêmio líquido
  - Consultou 5 IAs + Gemini Deep Research sobre covering design e edge real em loterias
  - Conclusão das IAs: previsão de números = ilusão; edge real = wheeling + anti-crowd + filtros estruturais

### Novos módulos (4 arquivos, 613 linhas)
1. **filtros.py** — filtros com valores exatos via distribuição hipergeométrica (LF e Mega)
2. **wheeling.py** — covering design (MILP + greedy estruturado Liu Changchun)
3. **anticrowd.py** — score de impopularidade para maximizar prêmio líquido
4. **roi.py** — simulador ROI comparativo (Ramo A vs B vs aleatório)

### CLI: 3 novos comandos
- `game-one filtros` — aplicar filtros estruturais
- `game-one wheel` — gerar covering design
- `game-one roi` — simular ROI comparativo

### Dados atualizados
- Banco até concurso 3664 (LF) e 2997 (Mega)
- megasena.json atualizado (7296 linhas)

### Documentação
- respostas-de-ia.md: respostas de 5 IAs sobre covering design
- "Otimização de Loterias com ML e Covering Design.md": Gemini Deep Research completo
- docs/sdd.md e docs/user-story.md atualizados

### Git
- Commit: a71c405 — push OK para origin/master

## Sessão Anterior (v0.4)
- **Data**: 2026-04-11
- 10 melhorias: banco portável, gerador programático 757+ hipóteses, TUI Textual 8 telas, prospector genético, validação Bonferroni, co-ocorrência, otimizador, meta-aprendizado, cross-lottery, avaliação retroativa
- 13 módulos Python, 10+ comandos CLI

## Arquitetura (Ramo A + Ramo B)

### Ramo A — Previsão de números (v0.1–v0.4)
```
coleta → SQLite → prospector (caos+gerador+evolução) → banco padrões
                                                            ↓
                  meta-learning ← avaliação retroativa ← sugerir
                  cross-lottery ←                        ↓
                  co-ocorrência ←                   otimizador → jogos
```

### Ramo B — Cobertura e anti-crowd (v0.5)
```
coleta → SQLite → filtros (hipergeométrica) → wheeling (covering design)
                                                    ↓
                  anticrowd (impopularidade) → jogos otimizados
                                                    ↓
                  roi (simulação comparativa A vs B vs aleatório)
```

## Módulos (17 arquivos)
- coleta.py, db.py, analise.py, descoberta.py, perfil.py
- caos.py, gerador.py, evolucao.py, prospector.py
- coocorrencia.py, meta.py, otimizador.py, sugerir.py
- avaliacao.py, conferir.py, backtesting_caos.py
- filtros.py, wheeling.py, anticrowd.py, roi.py
- tui.py, cli.py

## Próximos Passos
- [ ] Integrar Ramo A + Ramo B (filtros como pré-processamento do sugerir)
- [ ] Backtesting do Ramo B (ROI simulado em histórico longo)
- [ ] Symbolic regression (PySR) — fórmulas matemáticas livres
- [ ] Dados externos (clima, feriados)
- [ ] Dashboard web
- [ ] TUI para Ramo B (telas de filtros, wheeling, ROI)

## Comandos
```bash
cd ~/git/game-one
# Ramo A
uv run game-one tui                                     # interface visual
uv run game-one coletar                                 # atualizar dados
uv run game-one prospectar --jogo lotofacil              # buscar padrões
uv run game-one sugerir --jogo megasena                  # sugestões
uv run game-one avaliar --jogo lotofacil --ultimos 10    # medir acuidade
uv run game-one conferir                                 # conferir apostas
# Ramo B
uv run game-one filtros                                  # filtros estruturais
uv run game-one wheel                                    # covering design
uv run game-one roi                                      # simulação ROI
```
