# SDD — Software Design Document — game-one

## 1. Visão Geral

Sistema de descoberta autônoma de padrões em loterias da Caixa usando ML, geração programática de hipóteses e prospecção contínua.

**Stack**: Python 3.12+, SQLite, scikit-learn, pandas, numpy, scipy, textual

## 2. Arquitetura

```
game-one (CLI + TUI)
├── coleta.py          — API Caixa → SQLite
├── db.py              — SQLite (concursos + padrões descobertos)
├── analise.py         — Estatísticas básicas (frequência, atraso, pares)
├── descoberta.py      — ML ensemble (GB+RF+LR), correlações, backtesting ML
├── perfil.py          — Previsão de perfil estrutural (Mega-Sena)
├── caos.py            — Motor de hipóteses hardcoded (40 hipóteses em 8 categorias)
├── gerador.py         — 🆕 Gerador programático (757+ hipóteses combinatórias)
├── prospector.py      — 🆕 Busca contínua de padrões → banco de padrões
├── sugerir.py         — Sugestões via banco de padrões (consumidor)
├── conferir.py        — Conferência de apostas
├── backtesting_caos.py — Backtesting do motor de caos
├── tui.py             — 🆕 Interface visual interativa (Textual)
└── cli.py             — Interface de linha de comando
```

## 3. Banco de Dados

```sql
-- Dados brutos
concursos (jogo, numero, data, local, acumulado,
           valor_acumulado, valor_estimado, valor_arrecadado, ordem_sorteio)
dezenas   (jogo, numero, dezena, posicao)

-- Conhecimento acumulado
padroes   (jogo, nome, cat, desc, formula,
           p_valor, lift, taxa_obs, taxa_esp, tentativas,
           descoberto_em, ultima_validacao, concursos_na_validacao, ativo)
```

O banco `data/loterias.db` é commitado no git para portabilidade entre máquinas.

## 4. Arquitetura Produtor/Consumidor

```
┌──────────────────────────────────────────────┐
│  PROSPECTOR (produtor)                       │
│  Gera hipóteses novas, testa contra          │
│  histórico, salva descobertas no banco       │
│  Revalida 10% dos existentes por rodada      │
│  Modo: rodada única ou contínuo (loop)       │
└──────────────┬───────────────────────────────┘
               │ INSERT/UPDATE padroes
               ▼
┌──────────────────────────────────────────────┐
│  BANCO DE PADRÕES (tabela padroes)           │
│  Persistente, portável via git               │
│  Cada padrão: nome, p-valor, lift, status    │
└──────────────┬───────────────────────────────┘
               │ SELECT WHERE ativo=1
               ▼
┌──────────────────────────────────────────────┐
│  SUGERIR (consumidor)                        │
│  Consulta padrões ativos, aplica ao contexto │
│  do próximo concurso, gera jogos ponderados  │
│  Se banco vazio → auto-prospecta             │
└──────────────────────────────────────────────┘
```

## 5. Módulo gerador.py — Geração Programática de Hipóteses

### 5.1 Conceito

Em vez de hipóteses nomeadas escritas à mão, o gerador **combina operações primitivas sobre campos** automaticamente, criando centenas de hipóteses que nenhum humano pensaria.

### 5.2 Componentes

**16 campos** extraídos de cada concurso:
- Data: dia, mês, ano (2 dígitos), dia do ano, semana
- Concurso: número, número mod 100
- Inter-sorteio: soma anterior, amplitude anterior, max/min anterior, média anterior, pares anterior, contagem de repetições
- Contexto: posição lunar, magnitude do prêmio

**9 operações unárias**: identidade, mod10, mod7, inverter dígitos, soma de dígitos, raiz quadrada, log2, dobro, metade

**5 operações binárias**: soma, subtração, multiplicação, xor, módulo

**9 extratores de conjunto**: dezenas anteriores, vizinhos, espelho, complemento, gaps, xor entre consecutivas, soma de pares, ausentes em 2 sorteios, dezenas do penúltimo

**Sliding windows**: padrões condicionais (ex: "se soma do anterior foi baixa → apostar em números baixos")

### 5.3 Combinações

- Tipo 1: campo → op_unária → dezena candidata (16 × 9 = 144)
- Tipo 2: campo_A × campo_B → op_binária → dezena (C(16,2) × 5 = 600)
- Tipo 3: extratores de conjunto (9)
- Tipo 4: sliding windows (4)
- **Total: ~757 hipóteses por rodada**

### 5.4 Teste Estatístico

Mesmo do caos.py: chi-quadrado, lift, p-valor < 0.05, amostra mínima 30.

## 6. Módulo prospector.py — Busca Contínua

### 6.1 Rodada de prospecção

1. Carrega hipóteses de ambos os motores (caos + gerador)
2. Filtra as que ainda não foram testadas
3. Seleciona 10% das já testadas para revalidação
4. Testa cada uma contra o histórico
5. Salva significativas (p < 0.05) no banco
6. Desativa as que perderam significância

### 6.2 Modo contínuo

Loop infinito com intervalo configurável. Cada rodada pode descobrir padrões novos conforme dados são atualizados.

## 7. Módulo caos.py — Motor de Hipóteses Hardcoded

40 hipóteses em 8 categorias: data, concurso, temporal, financeiro, inter-sorteio, matemática, ordem, 2ª-ordem.

(Detalhes mantidos do SDD anterior — ver histórico git)

## 8. Interface

### 8.1 CLI

```bash
game-one coletar                                      # atualizar dados
game-one caos --jogo lotofacil --top 20               # hipóteses hardcoded
game-one gerador --jogo lotofacil --top 30            # hipóteses programáticas
game-one prospectar --jogo lotofacil                   # uma rodada de prospecção
game-one prospectar --jogo todos --continuo            # prospecção contínua
game-one sugerir --jogo lotofacil                      # sugestões via banco
game-one descobrir --jogo lotofacil                    # ML ensemble
game-one perfil                                        # perfil Mega-Sena
game-one backtesting --jogo lotofacil --metodo caos    # backtesting
game-one conferir                                      # conferir apostas
game-one tui                                           # interface visual
```

### 8.2 TUI (Textual)

Interface visual interativa com:
- Home: status do banco (concursos + padrões por jogo)
- Coletar: atualizar dados da Caixa
- Caos: motor de hipóteses hardcoded
- Gerador: hipóteses programáticas combinatórias
- Prospector: busca de padrões + status do banco
- Sugestões: gerar jogos via banco de padrões
- Conferir: conferir apostas
- Backtesting: validação histórica

Navegação por teclas de atalho (C/A/G/P/S/F/B/Q) ou botões.

## 9. Fluxo de Dados

```
API Caixa ──→ coleta.py ──→ SQLite (concursos + dezenas)
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
         caos.py          gerador.py       descoberta.py
         (40 hipóteses)   (757+ hipóteses)  (ML ensemble)
              │                │
              └───────┬────────┘
                      ▼
              prospector.py ──→ SQLite (padroes)
                                    │
                                    ▼
                              sugerir.py ──→ jogos sugeridos
```

## 10. Evolução Planejada

| Versão | Feature |
|--------|---------|
| v0.1 ✅ | Coleta, ML ensemble, perfil, correlações, backtesting |
| v0.2 ✅ | Motor de caos v1 (17 hipóteses em 5 categorias) |
| v0.3 ✅ | Dados financeiros + 40 hipóteses em 8 categorias + sugerir inteligente |
| v0.4 ✅ | Gerador programático (757+), prospector, banco de padrões, TUI |
| v0.5 ✅ | Ramo B: filtros hipergeométricos, wheeling, anti-crowd, ROI |
| v0.6 ✅ | Ramo C: diagnóstico avançado (PE, RQA, Lyapunov, surrogate, changepoint) |
| v0.7 | Transfer Entropy, GNN temporal, Mamba/SSM |
| v0.8 | Dados externos (temperatura, manutenção, operador) |
| v0.9 | Conformal prediction, Bayesian hierarchical |
| v1.0 | Dashboard web + acompanhamento de resultados |

## 11. Módulo diagnostico.py — Diagnóstico Avançado (v0.6)

### 11.1 Conceito

Tratar a loteria como sistema físico dinâmico, não abstração matemática.
Aplicar ferramentas de dinâmica não-linear e teoria da informação para
detectar se existe estrutura determinística oculta no ruído.

### 11.2 Testes implementados

1. **Permutation Entropy (PE)**: mede regularidade na ordenação temporal. PE < baseline i.i.d. → estrutura.
2. **RQA**: Recurrence Quantification Analysis via Takens embedding (dim=3, delay=1). Métricas: DET (determinismo), LAM (laminaridade), ENTR (entropia diagonal).
3. **Surrogate Data Testing**: 100 shuffled surrogates, compara PE e DET reais vs IC 95%.
4. **Changepoint Detection**: sliding window chi-square sobre frequências para detectar mudanças de regime.
5. **Lyapunov Exponent**: estima λ máximo. λ > 0 = caos determinístico.

### 11.3 Resultado (Mega-Sena, 525 concursos, 25/04/2026)

| Métrica | Valor | Interpretação |
|---------|-------|---------------|
| PE | 0.49 | Abaixo do i.i.d. (0.999) → estrutura |
| DET | 0.49 | 49% determinismo |
| LAM | 0.99 | Laminaridade alta |
| Lyapunov λ | 0.033 | Caos determinístico |
| Surrogate | p < 0.05 | Padrões confirmados como reais |
| Changepoints | 0 | Regime estável |
