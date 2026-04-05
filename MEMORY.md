# MEMORY.md — game-one

## Última Sessão
- **Data**: 2026-04-04 22:49
- **Máquina**: claudio@home
- **O que foi feito**:
  - Motor de caos v2: 40 hipóteses em 8 categorias
  - Banco expandido: valor_acumulado, valor_estimado, valor_arrecadado, ordem_sorteio
  - Re-coletados dados financeiros de todos os 1302 concursos
  - Hipóteses 2ª ordem: ausentes_2_pares, amplitude_anterior, xor, soma_mod, centesimos
  - Sugestões inteligentes (sugerir.py): combina caos + estatística, explica cada número
  - Backtesting caos: Mega +0.1, Lotofácil +0.3 sobre baseline
  - Conferência Mega-Sena 2992: melhor jogo acertou 2/6 (caos e perfil)
  - Lotofácil 3652: caos Jogo 1 acertou 10/15
  - Geradas sugestões para Lotofácil 3653 (segunda-feira)

## Conferência Mega-Sena 2992 (04/04/2026)
- **Resultado**: 04 17 23 33 36 49 (acumulou)
- **Melhor caos**: Jogo 3 → 2 acertos (04, 17)
- **Melhor perfil**: Jogos 3,4,5 → 2 acertos cada
- **ML**: máx 1 acerto
- **Lições**: 3/6 quadrados perfeitos (raro 1.7%), 3/6 repetições do anterior (raro 0.8%)
- **Hipóteses que acertaram**: quadrados_perfeitos(3), repeticoes_anterior(3), lua_metade(3), gaps_anterior(2), primos(2), mediana_anterior(1)

## Sugestões Lotofácil 3653 (segunda 07/04) — CONFERIR
```
Jogo 1: 01 02 04 05 07 09 10 13 14 16 20 21 22 24 25  (convergência máxima)
Jogo 2: 01 02 03 04 07 09 10 11 13 16 20 21 22 23 25  (variação)
Jogo 3: 01 04 05 09 10 11 13 14 16 19 20 21 22 24 25  (variação)
```
Top 15 convergentes: 01 02 04 05 07 09 10 11 13 14 16 20 21 22 25
Forte convergência (caos≥5 E ML≥3): 01 02 04 05 07 10 13 16 20 21 22 25

## Descobertas Significativas
### Mega-Sena
- lua_metade p=0.0002 (lift=1.03↑) — lua nova/cheia→baixos, crescente/minguante→altos
- ausentes_2_pares p=0.0046 (lift=1.04↑)
- amplitude_anterior p=0.0089 (lift=1.34↑)
- primos p=0.0194 (lift=1.05↑)

### Lotofácil
- ausentes_2_pares p=0.0000 (lift=0.93↓ — anti-correlação!)
- digitos_estimado p=0.0001 (lift=0.95↓)
- quadrados_perfeitos p=0.076 (lift=1.01↑)

## Próximos Passos
- [ ] Conferir Lotofácil 3653 (segunda 07/04)
- [ ] LSTM para séries temporais
- [ ] Optuna para otimização de hiperparâmetros
- [ ] Backtesting comparativo ML vs Caos (100+ concursos)
- [ ] Integrar amplitude_anterior e ausentes_2_pares no sugerir com mais peso

## Comandos
```bash
cd ~/git/game-one && source .venv/bin/activate
game-one coletar                                    # atualizar dados
game-one caos --jogo lotofacil --top 20             # caçar padrões no caos
game-one sugerir --jogo lotofacil                   # sugestões inteligentes
game-one descobrir --jogo lotofacil                 # ML ensemble
game-one perfil                                     # perfil Mega-Sena
game-one backtesting --jogo lotofacil --metodo caos # backtesting caos
game-one backtesting --jogo lotofacil --metodo ml   # backtesting ML
game-one conferir                                   # conferir apostas
```
