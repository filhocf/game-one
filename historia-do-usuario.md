# História do Usuário — game-one

## Motivação

Eu, como um jogador de loteria, quero um sistema de análise estatística dos resultados da Mega-Sena e Lotofácil que identifique padrões históricos e me sugira combinações de números para os próximos jogos.

## Escopo

### Fonte de dados
- Resultados oficiais da Caixa Econômica Federal (loterias.caixa.gov.br)
- Período: últimos 5 anos
- Jogos: Mega-Sena e Lotofácil (módulos separados — regras distintas)

### Análises realizadas
- Frequência absoluta e relativa de cada número
- Números "atrasados" (tempo sem ser sorteado)
- Pares e trios com co-ocorrência acima do esperado
- Correlação com dia da semana e mês do sorteio
- Distribuição: pares/ímpares, altos/baixos, primos
- Faixa de soma mais frequente dos números sorteados
- Localidade do sorteio (se disponível nos dados)

### Saída principal
- **Sugestão de combinações numéricas** para o próximo jogo, baseadas nos padrões encontrados, com score de confiança relativo

### Critérios de aceite
- Dados atualizados automaticamente (ou sob demanda)
- Análises separadas por jogo (Mega-Sena / Lotofácil)
- Interface CLI para consulta rápida
- Disclaimer: análise estatística exploratória, não garantia de acerto

## Regras dos jogos

- **Mega-Sena**: escolher 6 números de 1 a 60
- **Lotofácil**: escolher 15 números de 1 a 25
