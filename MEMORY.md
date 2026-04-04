# MEMORY.md — game-one

## Última Sessão
- **Data**: 2026-04-04 08:36
- **Máquina**: claudio@home
- **O que foi feito**:
  - Motor de caça a padrões no caos v2 (34 hipóteses em 7 categorias)
  - Expandido banco: valor_acumulado, valor_estimado, valor_arrecadado, ordem_sorteio
  - Re-coletados dados financeiros de todos os 1302 concursos
  - Novas categorias: financeiro, temporal (lua), matemática (fibonacci, primos, golden ratio), ordem
  - Sugestões inteligentes: combina padrões do caos com estatística, explica cada número
  - Docs: user-story.md e sdd.md criados
  - Geocoding descartado (todos sorteios em SP)

## Descobertas Significativas
- **Lotofácil**: digitos_estimado p=0.0001 (lift=0.95↓), dia_mes_aritmetica p=0.06
- **Mega-Sena**: lua_metade p=0.0002 (lift=1.03↑), primos p=0.02 (lift=1.05↑), vizinhos_anterior p=0.08

## Próximos Passos
- [ ] Conferir Mega-Sena 2992 e Lotofácil 3652 (sábado 04/04)
- [ ] LSTM para séries temporais
- [ ] Optuna para otimização de hiperparâmetros
- [ ] Backtesting do sugerir (comparar com descobrir)
- [ ] Mais hipóteses: padrões de 3+ concursos, sazonalidade anual

## Comandos
```bash
cd ~/git/game-one && source .venv/bin/activate
game-one coletar                          # atualizar dados
game-one descobrir --jogo lotofacil       # ML por número
game-one perfil                           # ML por perfil (Mega-Sena)
game-one correlacoes --jogo lotofacil     # correlações
game-one caos --jogo lotofacil --top 20   # caçar padrões no caos
game-one sugerir --jogo lotofacil         # sugestões inteligentes (caos)
game-one backtesting --jogo lotofacil --ultimos 10
game-one conferir                         # conferir apostas
```
