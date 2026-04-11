# MEMORY.md — game-one

## Última Sessão
- **Data**: 2026-04-11 14:24 — 18:32
- **Máquina**: sirdata (casa, servidor)
- **O que foi feito**:
  - **v0.4 completa** — 5 melhorias implementadas numa sessão:
  1. Banco portável (data/ no git)
  2. Gerador programático (757+ hipóteses combinatórias)
  3. TUI interativo (Textual) com 8 telas
  4. Prospector com evolução genética (profundidade variável, composição de conjuntos, expressões aninhadas)
  5. Validação rigorosa (Bonferroni, temporal, score de confiança, poda)
  6. Co-ocorrência (pares que saem juntos)
  7. Otimizador de jogos (concentra Top + perfil estrutural)
  8. Meta-aprendizado (pesos dinâmicos por performance recente)
  9. Cross-lottery (correlações Mega↔Lotofácil)
  10. Avaliação retroativa com diagnóstico e recomendações
  - Conferência: LF 3652 ML=10/15, LF 3653 caos=10/15, Mega fraco
  - Simulação retroativa LF: 1 prêmio (11 acertos) em 15 jogos simulados
  - Banco validado: LF 11 padrões, MS 14 padrões (após poda rigorosa)

## Banco de Padrões (pós-validação rigorosa)
- Lotofácil: 11 ativos (melhor score=0.342)
- Mega-Sena: 14 ativos (melhor score=0.740)

## Arquitetura Final v0.4
```
coleta → SQLite → prospector (caos+gerador+evolução) → banco padrões
                                                            ↓
                  meta-learning ← avaliação retroativa ← sugerir
                  cross-lottery ←                        ↓
                  co-ocorrência ←                   otimizador → jogos
```

## Módulos (13 arquivos)
- coleta.py, db.py, analise.py, descoberta.py, perfil.py
- caos.py, gerador.py, evolucao.py, prospector.py
- coocorrencia.py, meta.py, otimizador.py, sugerir.py
- avaliacao.py, conferir.py, backtesting_caos.py
- tui.py, cli.py

## Próximos Passos
- [ ] Push para origin
- [ ] Rodar prospecção contínua para acumular mais padrões
- [ ] Symbolic regression (PySR) — fórmulas matemáticas livres
- [ ] Dados externos (clima, feriados)
- [ ] Dashboard web
- [ ] Backtesting do sistema completo (otimizador + meta) vs antigo

## Comandos
```bash
cd ~/git/game-one
uv run game-one tui                                     # interface visual
uv run game-one coletar                                 # atualizar dados
uv run game-one prospectar --jogo lotofacil              # buscar padrões
uv run game-one prospectar --continuo                    # busca contínua
uv run game-one sugerir --jogo megasena                  # sugestões
uv run game-one avaliar --jogo lotofacil --ultimos 10    # medir acuidade
uv run game-one coocorrencia --jogo megasena             # pares frequentes
uv run game-one conferir                                 # conferir apostas
```
