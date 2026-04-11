# História de Usuário — game-one

## Visão

Como apostador analítico, quero um sistema que **descubra padrões ocultos no caos** dos sorteios de loterias de forma autônoma e contínua, usando geração automática de hipóteses e prospecção, para aumentar minhas chances de acerto.

## Personas

- **Apostador analítico**: quer decisões baseadas em dados, não intuição
- **Caçador de padrões**: busca correlações que humanos não perceberiam

## Funcionalidades

### F1 — Coleta de Dados ✅
> Como usuário, quero coletar resultados históricos da Caixa automaticamente.

- `game-one coletar` — baixa Mega-Sena e Lotofácil da API pública
- Armazena em SQLite (data, local, dezenas, acumulado, valores financeiros, ordem de sorteio)
- Banco portável via git (sync entre máquinas)

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
- `game-one backtesting --jogo lotofacil --metodo caos`

### F6 — Conferência de Apostas ✅
> Como usuário, quero conferir minhas apostas automaticamente.

- `game-one conferir`

### F7 — Motor de Caça ao Caos ✅
> Como usuário, quero que o sistema invente hipóteses sozinho e teste cada uma contra o histórico.

- 40 hipóteses hardcoded em 8 categorias (data, concurso, temporal, financeiro, inter-sorteio, matemática, ordem, 2ª-ordem)
- Teste estatístico: chi-quadrado, lift, p-valor
- `game-one caos --jogo lotofacil`

### F8 — Gerador Programático de Hipóteses 🆕 ✅
> Como usuário, quero que o sistema gere hipóteses que nenhum humano pensaria, combinando operações matemáticas sobre os dados automaticamente.

O sistema deve:
1. Combinar 16 campos × 9 operações unárias × 5 binárias automaticamente
2. Incluir extratores de conjunto (vizinhos, espelho, gaps, xor, etc.)
3. Incluir sliding windows (padrões condicionais)
4. Testar cada combinação estatisticamente
5. Gerar 757+ hipóteses por rodada

- `game-one gerador --jogo lotofacil --top 30`

### F9 — Prospector (Busca Contínua) 🆕 ✅
> Como usuário, quero que o sistema fique buscando padrões novos continuamente enquanto estiver ativado, acumulando conhecimento.

O sistema deve:
1. Testar hipóteses de todos os motores (caos + gerador)
2. Salvar descobertas significativas (p < 0.05) no banco de padrões
3. Revalidar 10% dos padrões existentes a cada rodada
4. Desativar padrões que perderam significância
5. Funcionar em modo rodada única ou contínuo (loop)

- `game-one prospectar --jogo lotofacil` (uma rodada)
- `game-one prospectar --continuo` (loop até Ctrl+C)

### F10 — Sugestões via Banco de Padrões 🆕 ✅
> Como usuário, quando peço uma sugestão, quero que o sistema use TUDO que já sabe — todos os padrões já descobertos por qualquer motor — para me dar os melhores números para o próximo jogo.

O sistema deve:
1. Consultar o banco de padrões (todos os ativos)
2. Aplicar cada padrão ao contexto do próximo concurso
3. Ponderar por significância (p-valor) e força (lift)
4. Combinar com frequência histórica e atraso
5. Se banco vazio, auto-prospectar antes de sugerir

- `game-one sugerir --jogo lotofacil`

### F11 — Interface Visual (TUI) 🆕 ✅
> Como usuário, quero uma interface visual interativa no terminal, com menus e navegação, em vez de decorar comandos CLI.

- `game-one tui`
- Telas: Home, Coletar, Caos, Gerador, Prospector, Sugestões, Conferir, Backtesting
- Navegação por teclas de atalho ou botões
- Status do banco (concursos + padrões) na tela inicial
- DataTables para resultados tabulares
- Workers async para não travar a interface

## Evolução Futura

- [ ] Symbolic regression (PySR) — descobrir fórmulas matemáticas
- [ ] Cross-lottery — correlações Mega↔Lotofácil
- [ ] Meta-aprendizado — pesos dinâmicos por performance recente
- [ ] Dados externos (clima, índices econômicos)
- [ ] LSTM para séries temporais
- [ ] Optuna para otimização de hiperparâmetros
- [ ] Geocoding de cidades (lat/lon)
- [ ] Dashboard web com visualizações
