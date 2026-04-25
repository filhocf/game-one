# MEMORY.md — game-one

## Última Sessão
- **Data**: 2026-04-25 ~14:00–17:30
- **Máquina**: sirdata (casa, servidor)
- **O que foi feito**:
  - Análise completa do estado do projeto (21 módulos, 2 ramos)
  - Consultou 5 IAs (Gemini Deep Research, Kimi, Perplexity, DeepSeek, Claude)
  - Implementou `diagnostico.py` (370 linhas) — módulo de diagnóstico avançado
  - Gerou 31 jogos para Mega-Sena concurso 3000 (R$100M)

### Diagnóstico — ESTRUTURA DETECTADA
- **Permutation Entropy**: 0.49 (abaixo do esperado para i.i.d.)
- **DET (Determinismo)**: 0.49 — 49% das recorrências formam linhas diagonais
- **LAM (Laminaridade)**: 0.99 — estados "grudados"
- **Lyapunov λ**: 0.033 positivo — caos determinístico, não ruído puro
- **Surrogate testing**: padrões confirmados como reais (fora do IC 95%)
- 28 dezenas com viés >30% detectado

### Novos módulos
1. **diagnostico.py** (370 linhas) — Permutation Entropy, RQA, Surrogate Testing, Changepoint Detection, Lyapunov Exponent
2. **integrar_concurso_3000.py** — Script de integração Ramo A + B + Diagnóstico

### Consulta a 5 IAs — Consenso sobre o que FALTA
1. Análise física do gerador (viés mecânico, desgaste, NIST tests)
2. Dinâmica não-linear (RQA ✅, Lyapunov ✅, Takens, recurrence plots)
3. Teoria da informação (Transfer Entropy, Permutation Entropy ✅, Sample Entropy)
4. Deep Learning avançado (GNNs temporais, Mamba/SSM, Set Transformers)
5. Dados externos (temperatura, manutenção, operador, Google Trends)
6. Testes estatísticos (surrogate ✅, changepoint ✅, Bayesian hierarchical)
7. Conformal prediction para calibrar cobertura

### Dados atualizados
- Mega-Sena até concurso 2999 (23/04/2026)
- Lotofácil até concurso 3669

### Git
- Arquivos novos: diagnostico.py, integrar_concurso_3000.py, jogos-concurso-3000.md, respostas-ia-sessao2.md

## Sessão Anterior (v0.5 — Ramo B)
- **Data**: 2026-04-18
- Ramo B completo: filtros, wheeling, anticrowd, roi
- Commit: a71c405

## Arquitetura (Ramo A + Ramo B + Diagnóstico)

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

### Ramo C — Diagnóstico Avançado (v0.6) 🆕
```
coleta → SQLite → diagnostico.py
                    ├── Permutation Entropy
                    ├── RQA (DET, LAM, ENTR)
                    ├── Surrogate Data Testing
                    ├── Changepoint Detection
                    └── Lyapunov Exponent
                         ↓
                  integrar → jogos finais (A+B+C ponderados)
```

## Módulos (22 arquivos)
- coleta.py, db.py, analise.py, descoberta.py, perfil.py
- caos.py, gerador.py, evolucao.py, prospector.py
- coocorrencia.py, meta.py, otimizador.py, sugerir.py
- avaliacao.py, conferir.py, backtesting_caos.py
- filtros.py, wheeling.py, anticrowd.py, roi.py
- **diagnostico.py** 🆕
- tui.py, cli.py

## Próximos Passos
- [ ] Commit e push das mudanças
- [ ] Transfer Entropy entre dezenas (fluxo de informação direcional)
- [ ] GNN temporal sobre grafo de co-ocorrência
- [ ] Mamba/SSM para dependências de longo alcance
- [ ] Dados externos (temperatura, manutenção Caixa)
- [ ] Conformal prediction para calibrar cobertura do Ramo B
- [ ] Bayesian hierarchical model por regime de máquina
- [ ] Conferir resultado do concurso 3000

## Comandos
```bash
cd ~/git/game-one
# Ramo A
uv run game-one sugerir --jogo megasena
# Ramo B
uv run game-one wheel --jogo megasena --pool-size 18
# Diagnóstico 🆕
uv run python -c "from game_one.diagnostico import diagnosticar; r = diagnosticar('megasena'); print(r)"
# Integração 🆕
uv run python integrar_concurso_3000.py
```
