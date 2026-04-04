# SDD — Software Design Document — game-one

## 1. Visão Geral

Sistema de descoberta de padrões em loterias da Caixa usando ML e data mining automatizado.

**Stack**: Python 3.12+, SQLite, scikit-learn, pandas, numpy, scipy

## 2. Arquitetura

```
game-one (CLI)
├── coleta.py        — API Caixa → SQLite
├── db.py            — Conexão SQLite
├── analise.py       — Estatísticas básicas (frequência, atraso, pares)
├── descoberta.py    — ML ensemble (GB+RF+LR), correlações, backtesting
├── perfil.py        — Previsão de perfil estrutural (Mega-Sena)
├── sugestao.py      — Gerador de jogos por peso estatístico
├── conferir.py      — Conferência de apostas
├── caos.py          — 🆕 Motor de caça a padrões no caos
└── cli.py           — Interface de linha de comando
```

## 3. Banco de Dados

```sql
concursos (jogo, numero, data, local, acumulado)
dezenas   (jogo, numero, dezena, posicao)
```

## 4. Módulo caos.py — Motor de Caça a Padrões

### 4.1 Conceito

Em vez de análises fixas definidas pelo usuário, o motor **gera hipóteses automaticamente** e testa cada uma contra o histórico. Busca correlações que humanos não pensariam.

### 4.2 Pipeline

```
Dados brutos → Gerador de Hipóteses → Teste Estatístico → Ranking → Output
```

### 4.3 Gerador de Hipóteses

Cada hipótese é uma função `(concurso) → valor_derivado` que produz um número a partir dos dados do concurso. O motor testa se esse valor derivado tem correlação com as dezenas sorteadas.

**Categorias implementadas (v1):**

| Categoria | Hipótese | Exemplo |
|-----------|----------|---------|
| Data | dia_invertido | dia=14 → testa dezena 41 |
| Data | mes_invertido | mês=04 → testa dezena 40 |
| Data | dia_mes_concat | dia=14,mês=04 → testa 14, 04 |
| Data | soma_digitos_data | 04/04/2026 → 0+4+0+4+2+0+2+6=18 |
| Data | diff_dia_mes | |14-4|=10 |
| Data | produto_dia_mes | min(14×4, max_num) |
| Concurso | digitos_concurso | 3651 → testa 3,6,5,1 |
| Concurso | concurso_mod | 3651 mod 25 = 1 |
| Concurso | soma_digitos_conc | 3+6+5+1=15 |
| Concurso | pares_digitos_conc | 3651 → 36,65,51 |
| Temporal | dia_do_ano | 1-366 mod max_num |
| Temporal | semana_do_ano | 1-53 |
| Temporal | fase_lua | Posição no ciclo lunar (1-30) |
| Temporal | lua_metade | Nova/cheia→baixos, crescente/minguante→altos |
| Financeiro | digitos_acumulado | R$3.5M → dígitos 3,5,35 |
| Financeiro | digitos_estimado | Idem para valor estimado |
| Financeiro | digitos_arrecadado | Idem para valor arrecadado |
| Financeiro | magnitude_premio | log10(valor) como dezena |
| Inter-sorteio | repeticoes_anterior | Dezenas do anterior como preditoras |
| Inter-sorteio | complemento | se saiu 5, testa 25-5=20 |
| Inter-sorteio | vizinhos | se saiu 10, testa 9 e 11 |
| Inter-sorteio | espelho | Inversão de dígitos do anterior |
| Inter-sorteio | soma_pares | Soma de consecutivos do anterior |
| Inter-sorteio | gaps | Diferenças entre consecutivos do anterior |
| Inter-sorteio | media/mediana | Média e mediana do anterior |
| Inter-sorteio | dobro_max | 2×maior_anterior mod max |
| Matemática | fibonacci | 1,2,3,5,8,13,21,34,55 saem mais? |
| Matemática | golden_ratio | Posições na proporção áurea |
| Matemática | primos | Primos saem mais que compostos? |
| Matemática | quadrados | 1,4,9,16,25,36,49 saem mais? |
| Matemática | multiplos_7 | 7,14,21,28... saem mais? |
| Ordem | vizinhos_primeira_bola | Vizinhos da 1ª bola sorteada |

### 4.4 Teste Estatístico

Para cada hipótese, calcula:
- **Taxa de acerto**: % de vezes que o valor derivado apareceu nas dezenas
- **p-valor** (chi-quadrado): probabilidade de o resultado ser por acaso
- **Mutual Information**: informação compartilhada entre hipótese e resultado
- **Lift**: taxa_observada / taxa_esperada

Filtra por:
- p-valor < 0.05 (significância 95%)
- Amostra mínima de 30 concursos

### 4.5 Output

Ranking das hipóteses por p-valor, mostrando:
- Nome da hipótese
- p-valor
- Lift (quanto acima/abaixo do esperado)
- Amostra (quantos concursos testados)
- Exemplo concreto

## 5. Fluxo de Dados

```
API Caixa ──→ coleta.py ──→ SQLite
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
              descoberta   correlações   caos
              (ML ensemble) (dia/mês/UF) (hipóteses auto)
                    │          │          │
                    └──────────┼──────────┘
                               ▼
                         sugestões de jogos
```

## 6. Evolução Planejada

| Versão | Feature |
|--------|---------|
| v0.1 ✅ | Coleta, ML ensemble, perfil, correlações, backtesting |
| v0.2 ✅ | Motor de caos v1 (17 hipóteses em 5 categorias) |
| v0.3 ✅ | Dados financeiros + 34 hipóteses em 7 categorias + fase da lua |
| v0.4 | Geocoding de cidades (lat/lon) → hipóteses geográficas |
| v0.5 | LSTM séries temporais + Optuna |
| v0.6 | Integrar padrões do caos no gerador de sugestões |
| v0.7 | Dashboard web |
