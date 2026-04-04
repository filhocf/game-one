# MEMORY.md — game-one

## Última Sessão
- **Data**: 2026-04-04 00:33
- **Máquina**: claudio@home
- **O que foi feito**:
  - Criado projeto do zero: história do usuário, estrutura, coleta, análise, ML
  - Coleta da API pública da Caixa (grátis): 521 Mega-Sena + 781 Lotofácil
  - SQLite como banco (data/loterias.db)
  - Ensemble ML (3 modelos) para descoberta de padrões
  - Abordagem por perfil para Mega-Sena (prevê propriedades, não números)
  - Relatório de correlações (dia, mês, UF)
  - Backtesting com output verboso
  - Conferência automática de apostas
  - Primeira aposta: Lotofácil 3652 → Jogo 2 acertou 10/15

## Próximos Passos
- [ ] Conferir Mega-Sena 2992 (sábado 04/04)
- [ ] LSTM para séries temporais
- [ ] Optuna para otimização de hiperparâmetros
- [ ] Backtesting robusto (100+ concursos Lotofácil)
- [ ] Expandir histórico se necessário

## Comandos
```bash
cd ~/git/game-one && source .venv/bin/activate
game-one coletar                          # atualizar dados
game-one descobrir --jogo lotofacil       # ML por número (Lotofácil)
game-one perfil                           # ML por perfil (Mega-Sena)
game-one correlacoes --jogo lotofacil     # análise de correlações
game-one backtesting --jogo lotofacil --ultimos 10
game-one conferir                         # conferir apostas
```
