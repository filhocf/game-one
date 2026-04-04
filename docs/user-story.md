# História de Usuário — game-one

## Visão

Como apostador analítico, quero um sistema que **descubra padrões ocultos no caos** dos sorteios de loterias, usando data mining automatizado, para aumentar minhas chances de acerto.

## Personas

- **Apostador analítico**: quer decisões baseadas em dados, não intuição
- **Caçador de padrões**: busca correlações que humanos não perceberiam

## Funcionalidades

### F1 — Coleta de Dados ✅
> Como usuário, quero coletar resultados históricos da Caixa automaticamente.

- `game-one coletar` — baixa Mega-Sena e Lotofácil da API pública
- Armazena em SQLite (data, local, dezenas, acumulado)

### F2 — Descoberta de Padrões por ML ✅
> Como usuário, quero que o sistema descubra quais números têm maior probabilidade no próximo sorteio.

- Ensemble de 3 modelos (GradientBoosting, RandomForest, LogisticRegression)
- Features: lags, atraso, médias móveis, tendência, contexto (dia, mês, UF)
- `game-one descobrir --jogo lotofacil`

### F3 — Perfil de Sorteio (Mega-Sena) ✅
> Como usuário, quero prever o *perfil* do próximo sorteio (soma, pares, consecutivos, terços).

- Prevê propriedades estruturais, não números individuais
- Gera jogos que encaixam no perfil previsto
- `game-one perfil`

### F4 — Correlações ✅
> Como usuário, quero ver quais números são quentes/frios por dia da semana, mês e UF.

- Desvios significativos (>8% da média global)
- `game-one correlacoes --jogo lotofacil`

### F5 — Backtesting ✅
> Como usuário, quero validar se o modelo realmente funciona em dados passados.

- Simula previsões em N concursos históricos
- Compara com baseline aleatório
- `game-one backtesting --jogo lotofacil --ultimos 30`

### F6 — Conferência de Apostas ✅
> Como usuário, quero conferir minhas apostas automaticamente.

- `game-one conferir`

### F7 — Motor de Caça ao Caos 🆕
> Como usuário, quero que o sistema **invente hipóteses sozinho** e teste cada uma contra o histórico, buscando correlações ocultas que humanos não pensariam.

O sistema deve:
1. Gerar automaticamente dezenas de hipóteses a partir dos dados
2. Testar cada hipótese estatisticamente (chi-quadrado, mutual information)
3. Rankear por significância estatística
4. Apresentar as top N descobertas

#### Categorias de hipóteses:

**Numerologia da data:**
- Dia invertido (14→41): a dezena invertida do dia aparece mais?
- Mês invertido (04→40): idem para o mês
- Combo dia+mês: concatenação e inversões cruzadas
- Soma dos dígitos da data completa
- Diferença, produto, módulo entre dia e mês

**Numerologia do concurso:**
- Dígitos do número do concurso
- Concurso mod N (ciclos)
- Soma dos dígitos do concurso

**Contexto temporal:**
- Dia do ano (1-366)
- Semana do ano
- Fase da lua no dia do sorteio
- Dias desde o último sorteio

**Contexto geográfico:**
- Coordenadas da cidade (lat/lon → dígitos)
- Código IBGE da cidade

**Contexto financeiro:**
- Dígitos do valor do prêmio/acumulado
- Faixa de valor do prêmio

**Padrões inter-sorteios:**
- Dezenas que repetem do anterior
- Dezenas "atrasadas" (não saem há N jogos)
- Espelhamento: se saiu 5, sai 25? (complemento)
- Vizinhos: se saiu 10, saem 9 ou 11?

#### Comando:
```bash
game-one caos --jogo lotofacil           # roda todas as hipóteses
game-one caos --jogo lotofacil --top 20  # mostra top 20
```

## Evolução Futura

- [ ] LSTM para séries temporais
- [ ] Optuna para otimização de hiperparâmetros
- [ ] Coleta de valor do prêmio (API da Caixa)
- [ ] Geocoding de cidades (lat/lon)
- [ ] API da fase da lua
- [ ] Dashboard web com visualizações
