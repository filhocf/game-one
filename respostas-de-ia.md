# Pergunta: Estou construindo um sistema de análise de loterias em Python (Mega-Sena 6/60 e   Lotofácil 15/25). Atualmente uso chi-quadrado para testar hipóteses e um gerador genético  de padrões. A avaliação retroativa mostra performance no nível do aleatório. Quais são as abordagens com fundamentação matemática real (não numerologia) que podem dar algum edge, mesmo que pequeno? Considere: modelo CDM (Dirichlet-Multinomial), wheeling systems, entropia condicional, e filtros estruturais. Seja honesto sobre o que funciona e o que é ilusão.

## Resposta Gemini
Para ser direto e matematicamente honesto: em loterias regulamentadas e auditadas (como as da Caixa), **não existe "edge" para prever quais números serão sorteados.** O sorteio é um processo estocástico de alta entropia. O fato de sua avaliação retroativa estar no nível do aleatório não é uma falha do seu código, é a confirmação de que o sistema de sorteio está funcionando corretamente.

Dito isso, existem abordagens matemáticas para **otimizar o valor esperado (EV)** e a **cobertura combinatória**. Se você quer sair da "numerologia" e focar em fundamentos reais, aqui está o que faz sentido e o que é ilusão:

---

## 1. Wheeling Systems (Fechamentos Combinatórios)
Este é o único campo com fundamentação matemática sólida (Teoria de Design e Combinatória) que realmente "funciona", mas não para prever números, e sim para **garantir retornos**.

* **O que é:** Uso de **Covering Designs**. Se você escolher 20 números na Lotofácil, o "fechamento" garante que, se 15 dos sorteados estiverem entre os seus 20, você terá pelo menos um bilhete com 14 pontos (ou 13, etc.), gastando muito menos que uma aposta múltipla oficial.
* **Fundamentação:** Em vez de focar na probabilidade de um evento ($P$), você foca na **densidade de cobertura** do espaço amostral.
* **Onde aplicar no seu Python:** Use algoritmos de busca (como o seu genético ou *Simulated Annealing*) para encontrar o menor conjunto de combinações que cubra um design específico, como um $t-(v, k, \lambda)$ design.

## 2. Modelo Dirichlet-Multinomial (CDM)
O CDM é excelente para modelar dados categóricos onde as contagens são esparsas ou para detectar **viés físico**.

* **O que é:** Uma distribuição de probabilidade composta onde a distribuição de Dirichlet é a *prior* para os parâmetros de uma distribuição Multinomial.
* **A Realidade:** Em um mundo perfeito, todos os números têm probabilidade $1/60$ (Mega) ou $1/25$ (Lotofácil). O CDM poderia detectar se uma bolinha específica está saindo mais por conta de peso ou desgaste (viés mecânico).
* **O Problema:** Loterias modernas trocam os conjuntos de bolas e usam equipamentos de alta precisão. Qualquer viés detectado pelo CDM geralmente é ruído estatístico ou desaparece antes que você consiga capitalizar sobre ele. 
* **Utilidade:** Serve como um "teste de sanidade" para provar que o sorteio continua justo. Se o CDM mostrar uma concentração absurda em um parâmetro, há um erro no processo físico de sorteio.

## 3. Entropia Condicional e Teoria da Informação
Aqui você tenta medir se o sorteio $N$ fornece alguma informação sobre o sorteio $N+1$.

* **O que é:** Calcular $H(X_{n+1} | X_n)$. Se a entropia condicional for menor que a entropia marginal, haveria "memória" no sistema.
* **A Realidade:** Em loterias, a informação mútua $I(X_n; X_{n+1})$ é efetivamente zero. Tentar encontrar padrões sequenciais em sorteios independentes é cair na **Falácia do Apostador**.
* **Edge Real:** A única entropia que importa é a **Entropia de Seleção dos Apostadores**.

## 4. Filtros Estruturais (Onde está o "Edge" Social)
Aqui está o segredo que a maioria dos "sistemas" ignora: o prêmio da Mega-Sena é **rateado**. 

* **O Edge:** Você não ganha mais vezes, mas **ganha mais dinheiro quando ganha**.
* **Como fazer:** Use filtros para evitar combinações que os humanos tendem a escolher (datas, sequências óbvias, desenhos no volante). 
    * Exemplo: Se você jogar `01-02-03-04-05-06` e ganhar, dividirá o prêmio com centenas de pessoas. Se jogar uma combinação com alta entropia visual e sem padrões culturais, as chances de ganhar sozinho são ordens de magnitude maiores.
* **Abordagem Python:** Use modelos de *clustering* em dados históricos de ganhadores (se disponíveis) para identificar zonas de "sobre-aposta" e configure seu gerador genético para **evitar** essas zonas.

---

### Tabela Comparativa: Realidade vs. Ilusão

| Técnica | Fundamentação | Objetivo Real | Status |
| :--- | :--- | :--- | :--- |
| **Chi-Quadrado** | Estatística Frequentista | Verificar se o sorteio é justo/aleatório. | **Funciona** (para auditoria) |
| **Genetic Algorithms** | Otimização | Encontrar coberturas (Wheeling) eficientes. | **Funciona** (para logística) |
| **Filtros de Soma/Pares** | Heurística | Reduzir o custo da aposta removendo outliers. | **Ilusão** (o outlier tem a mesma $P$) |
| **Análise de Frequência** | Estatística Descritiva | Apostar nos que "mais saem" ou "mais faltam". | **Ilusão** (independência estatística) |
| **Teoria dos Jogos** | Economia | Escolher números que ninguém escolhe. | **Edge Real** (maximiza o prêmio) |

### Proposta de Mudança de Arquitetura
Se você quer que seu sistema seja matematicamente robusto, pare de tentar **prever** e comece a **otimizar**:

1.  **Módulo de Cobertura:** Implemente algoritmos para gerar o menor número de volantes que garantam $N-1$ pontos se $N$ números forem acertados (Wheeling).
2.  **Módulo de Valor Esperado (EV):** Crie um estimador de "popularidade" de números baseado em comportamento humano (evitar padrões geométricos, datas, etc.) e use-o como um filtro de rejeição.
3.  **Módulo de Kelly Criterion:** Se você for aplicar isso de forma sistemática, use o Critério de Kelly para gerir o *bankroll*, embora em loterias o $EV$ seja quase sempre negativo, o que sugeriria não apostar.

**Conclusão Sincera:** O "edge" em loterias não é sobre ser um vidente, é sobre ser um **logístico** (gastar menos para cobrir mais) e um **psicólogo** (não dividir o prêmio com a massa). Qualquer sistema que prometa prever os números de amanhã com base nos de ontem está apenas redesenhando o ruído.

## Resposta Perplexity
Em loterias justas como Mega-Sena (6/60) e Lotofácil (15/25), os sorteios são independentes e uniformemente aleatórios, o que significa que não há edge matemático real para previsões além do aleatório puro — sua performance atual é o esperado. Qualquer "padrão" detectado é ilusão estatística (lei dos pequenos números ou viés de confirmação). [github](https://github.com/dadosnapratica/mega-sena-simulador)

## Modelo CDM (Dirichlet-Multinomial)
O CDM é um modelo bayesiano válido que usa Dirichlet como prior para parâmetros multinomiais, gerando previsões via posterior preditiva: \( \mathbb{E}(z_j) = M \frac{\alpha_j + n_j}{\sum (\alpha_j + n_j)} \), onde \( n_j \) são contagens históricas e \( \alpha \) é estimado (ex.: máxima verossimilhança). Em testes com dados reais (ex.: loterias 6/52), acerta 2 números a cada ~12 sorteios (próximo ao aleatório esperado: \( \binom{6}{2} / \binom{52}{6} \approx 1/221 \), mas ajustado por pool), e falha em jackpots (previsão de 6 números em 104k anos). Para Mega-Sena/Lotofácil, pode suavizar frequências, mas não supera aleatório em EV (expected value) negativo. [scribd](https://www.scribd.com/document/737275432/2403-12836v1)

## Wheeling Systems
Sistemas de wheeling cobrem combinações sistemáticas de um pool reduzido (ex.: 10 números em Mega-Sena geram múltiplas 6-plays), garantindo prêmios menores se o sorteio cair no pool. É combinatória pura: aumenta cobertura (ex.: full wheel de 12/60 custa \( \binom{12}{6} = 924 \) bilhetes), mas o custo excede ganhos esperados em loterias com EV negativo (~ -50%). Útil em bolões para prêmios secundários, mas sem edge sobre aleatório ajustado por custo. [businessresearchinsights](https://www.businessresearchinsights.com/pt/market-reports/lottery-software-and-prediction-tools-market-112908)

## Entropia Condicional
Entropia condicional \( H(X|Y) = -\sum p(x,y) \log p(x|y) \) mede incerteza residual; em sorteios i.i.d., é máxima e constante (sem dependência). [scielo](https://www.scielo.br/j/rbef/a/FwpdFPyszdS69BYVkJFNXkR/?lang=pt) Pode filtrar apostas com alta entropia (evitando linhas retas como 10-20-30), que historicamente ocorrem menos por física dos globos, mas isso é mínimo e não altera probabilidades teóricas. [regys.com](https://regys.com.br/a-ciencia-da-incerteza-por-que-a-matematica-nao-pode-vencer-a-mega-sena/) Ilusão comum: assume não-estacionaridade, mas Mega-Sena é projetada para uniformidade. [github](https://github.com/dadosnapratica/mega-sena-simulador)

## Filtros Estruturais
Filtros como soma (Mega-Sena: média ~150-200), pares/ímpares (~3:3), repetições do anterior (50% zero repetidas), setores do volante evitam extremos improváveis. São baseados em CLT (distribuição central converge a normal), reduzindo apostas ruins (ex.: 6 pares ~1-2% dos sorteios). Melhora cobertura vs. picks ruins, mas aleatório puro já segue isso em média; backtests superestimam por overfitting. [loteriasinteligente.com](https://www.loteriasinteligente.com.br/analise_estatistica_avancada_lotofacil)

## Abordagens Viáveis
| Abordagem | Edge Real | Limitação | Aplicação em Python |
|-----------|-----------|-----------|---------------------|
| CDM | Nenhum (aleatório-like) | Overfitting histórico  | Use `numpy` + `scipy.special.gammaln` para PDF; teste Monte Carlo. |
| Wheeling | Cobertura, não prob. | Custo alto  [lotteryngo](https://lotteryngo.com/pt/blog/lottery-strategies/lottery-wheeling-systems/) | `itertools.combinations` para gerar wheels. |
| Entropia | Filtragem mínima | Independência quebra  [regys.com](https://regys.com.br/a-ciencia-da-incerteza-por-que-a-matematica-nao-pode-vencer-a-mega-sena/) | `scipy.stats.entropy` em histórico condicional. |
| Filtros | Evita perdas bobas | ~0 edge  [loteriasinteligente.com](https://www.loteriasinteligente.com.br/analise_estatistica_avancada_lotofacil) | Regras if-then em soma/pares; simule 1M apostas. [nucleodoconhecimento.com](https://www.nucleodoconhecimento.com.br/matematica/simulacao-computacional) |

Honestamente, nada dá edge positivo em EV; foque diversão ou bolões. Para código, priorize simulações realistas vs. histórico para validar. [github](https://github.com/dadosnapratica/mega-sena-simulador)

## Resposta Manus
# Relatório Técnico: Abordagens Matemáticas para Análise de Loterias (Mega-Sena e Lotofácil)

Este relatório apresenta uma análise crítica e fundamentada de métodos matemáticos aplicados à análise de loterias, distinguindo entre ferramentas de **otimização de apostas** e ilusões de **previsão de sorteio**.

---

## 1. Avaliação Honestidade: O que funciona e o que é ilusão?

Antes de detalhar os modelos, é fundamental estabelecer a realidade matemática: as loterias da Caixa (Mega-Sena e Lotofácil) são sistemas de **eventos independentes com reposição total do espaço amostral**.

| Conceito | Realidade Matemática | Status |
| :--- | :--- | :--- |
| **Previsão de Dezenas** | Impossível. O histórico de sorteios passados não altera a probabilidade dos futuros. | **Ilusão** |
| **Filtros Estruturais** | Úteis para evitar jogos "burros" (ex: 1,2,3,4,5,6) que muitos dividem, mas não aumentam a chance de acerto. | **Otimização** |
| **Wheeling Systems** | Matemática real (Covering Designs). Garante prêmios menores se certas condições forem atendidas. | **Ferramenta Real** |
| **Entropia Condicional** | Mede a desordem, mas em sistemas perfeitamente aleatórios, a entropia é máxima e constante. | **Inútil para Previsão** |

---

## 2. O Modelo Compound Dirichlet-Multinomial (CDM)

O modelo CDM é uma extensão bayesiana da distribuição multinomial. Ele trata as probabilidades de cada número como variáveis aleatórias que seguem uma distribuição de Dirichlet.

### Fundamentação
Diferente do Chi-Quadrado (que testa se a distribuição é uniforme), o CDM tenta estimar os parâmetros de uma "urna viciada". Se o processo de sorteio fosse perfeitamente aleatório, o CDM convergiria para uma probabilidade idêntica para todos os números.

### Aplicação em Python
O uso do CDM em loterias geralmente foca em detectar **pequenos desvios sistemáticos** (vieses físicos nas máquinas ou bolas).

```python
import numpy as np
from scipy.special import gammaln

def cdm_log_likelihood(alpha, counts):
    """
    Calcula a log-verossimilhança do modelo Dirichlet-Multinomial.
    alpha: parâmetros da Dirichlet (vetor de tamanho K)
    counts: contagens observadas de cada número (vetor de tamanho K)
    """
    n = np.sum(counts)
    a0 = np.sum(alpha)
    
    term1 = gammaln(a0) - gammaln(n + a0)
    term2 = np.sum(gammaln(counts + alpha) - gammaln(alpha))
    
    return term1 + term2

# Exemplo: Estimativa de Alpha via Método dos Momentos (Simplificado)
def estimate_alpha_moments(data_matrix):
    # data_matrix: (n_sorteios, k_dezenas) - 1 se presente, 0 se ausente
    p_mean = np.mean(data_matrix, axis=0)
    p_var = np.var(data_matrix, axis=0)
    
    # Estimativa bruta do parâmetro de precisão S
    s = np.mean(p_mean * (1 - p_mean) / p_var - 1)
    alpha_est = p_mean * s
    return alpha_est
```

**Veredito:** O CDM é matematicamente sólido para inferência estatística, mas sua performance em loterias modernas é "nível aleatório" porque o viés físico é praticamente inexistente.

---

## 3. Wheeling Systems (Sistemas de Fechamento)

Esta é a única área com **edge real** no sentido de eficiência de capital. Se você pretende jogar 20 números na Lotofácil, em vez de pagar uma aposta múltipla caríssima, você usa um "fechamento".

### Matemática dos Covering Designs
Um sistema $(v, k, t, m) = b$ garante que, se você escolher $v$ números e $m$ deles forem sorteados, você terá pelo menos um bilhete com $t$ acertos, usando $b$ bilhetes de $k$ números.

### Exemplo de Edge
- **Sem Wheeling:** Você joga combinações aleatórias. Pode acertar 15 números entre os 20 escolhidos e, por azar, não ter nenhum bilhete com 15 pontos.
- **Com Wheeling:** Você garante matematicamente o prêmio se a condição for atingida.

---

## 4. Entropia Condicional e Filtros Estruturais

### Entropia Condicional $H(X|Y)$
A ideia seria medir quanta informação o sorteio anterior ($Y$) fornece sobre o próximo ($X$). 
- Em uma loteria justa: $H(X|Y) = H(X)$. A informação mútua é zero.
- **Onde pode haver edge:** Se houver correlação temporal (extremamente improvável em sorteios auditados).

### Filtros Estruturais (Análise Combinatória)
Filtros não aumentam a probabilidade, mas **melhoram o Valor Esperado ($EV$)** ao evitar combinações sobrecarregadas (onde, se você ganhar, dividirá o prêmio com milhares de pessoas).

**Filtros recomendados:**
1. **Soma das Dezenas:** Para a Mega-Sena, a maioria dos sorteios cai na faixa de 150 a 210.
2. **Pares/Ímpares:** Distribuição 3:3 ou 4:2 (Mega) e 8:7 ou 7:8 (Lotofácil).
3. **Distância de Hamming:** Evitar jogos muito próximos de sorteios anteriores.

---

## 5. Conclusão e Recomendação para seu Sistema

Se o seu sistema atual performa como o aleatório, **ele está correto**. Qualquer sistema que prometa performance superior ao aleatório em testes retroativos honestos está sofrendo de *overfitting* ou viés de sobrevivência.

**Onde focar seu código Python:**
1. **Otimizador de Wheeling:** Implemente algoritmos genéticos não para "prever", mas para encontrar o **menor número de bilhetes** que cubra um espaço $(v, k, t, m)$.
2. **Análise de EV:** Crie um filtro que elimine jogos com alta probabilidade de serem jogados por humanos (datas, sequências óbvias, padrões visuais no volante).
3. **Gestão de Risco:** Use o critério de Kelly (adaptado para probabilidades extremamente baixas) para gerir o bankroll, embora em loterias o $EV$ seja quase sempre negativo.

**Lembre-se:** A matemática da loteria serve para entender que o único "edge" real é gastar o mínimo possível para garantir o retorno desejado, dado que os números saiam dentro do seu conjunto escolhido.


## Resposta DeepSeek
## Resposta direta (spoiler)

Nenhuma abordagem matemática consegue transformar a expectativa negativa da loteria em positiva. O que existe são **estratégias de otimização de retorno condicional** (aumentar o prêmio *se* você acertar) e **métodos de redução de custo** (cobrir mais combinações com menos bilhetes). Mas prever números? Não há edge preditivo real.

Vou analisar cada item que você mencionou com honestidade brutal.

---

### 1. Modelo Dirichlet-Multinomial (CDM)

**O que é**: Modelo bayesiano que assume que as probabilidades dos números são desconhecidas, mas extraídas de uma distribuição Dirichlet, e que as extrações seguem uma multinomial.

**Funciona?** ❌ **Não para previsão.**

- A loteria é *projetada* para ser uniforme e independente. Qualquer desvio observado em amostras finitas é ruído amostral.
- O CDM vai "aprender" padrões do passado, mas esses padrões não se repetem no futuro – você estará ajustando o modelo a flutuações aleatórias (overfitting).
- Testes retroativos que mostram desempenho aleatório já confirmam isso: o CDM não supera a distribuição uniforme.

**Útil para algo?** Sim, para *estimativa conservadora de incerteza* se você quisesse calcular intervalos de confiança para frequências. Mas não para selecionar números.

---

### 2. Wheeling Systems

**O que é**: Conjunto de combinações que garante *pelo menos um bilhete com prêmio menor* se você acertar um subconjunto dos números sorteados (ex.: se acertar 5 dos 6 da Mega, você tem garantido um terno ou quadra).

**Funciona?** ✅ **Funciona, mas não é "edge" preditivo.**

- É uma **estratégia de cobertura condicional**: você aumenta a chance de ganhar *prêmios secundários* dado que acertou parte dos números.
- Não aumenta a probabilidade de acertar os números principais. O valor esperado continua negativo.
- Útil em **bolões**: com R$ 100, você cobre mais combinações relevantes do que escolhendo 10 jogos aleatórios. Mas ainda perde dinheiro no longo prazo.

**Exemplo real**: Na Mega-Sena, um wheel 6 números se você escolheu 8 números (C(8,6)=28 combinações) garante que, se os 6 sorteados estiverem entre seus 8, você tem a sena. Mas você pagou 28x o preço. Se acertar 5 entre os 8, garante algumas quadras. É matematicamente sólido, mas não cria vantagem – apenas redistribui os prêmios condicionais.

---

### 3. Entropia Condicional

**O que é**: Mede a incerteza residual de um evento dado o conhecimento de outro. Em loterias, seria algo como H(número futuro | números passados).

**Funciona?** ❌ **Ilusão completa.**

- Para processos independentes e identicamente distribuídos (i.i.d.), a entropia condicional é igual à entropia marginal. O passado não informa o futuro.
- A loteria é i.i.d. por construção. Qualquer tentativa de usar entropia condicional pressupõe dependência serial que não existe.
- Você pode calcular entropia de distribuições empíricas, mas estará medindo ruído, não sinal.

**Cuidado**: Há papers pseudocientíficos que usam entropia para "detectar padrões" em loterias. São todos metodologicamente falhos (data snooping, múltiplos testes sem correção).

---

### 4. Filtros Estruturais

**O que é**: Regras heurísticas para eliminar combinações "óbvias" (ex.: 1-2-3-4-5-6, todas pares, todas ímpares, sequências em progressão aritmética, números repetidos do sorteio anterior, etc.).

**Funciona?** ✅ **Sim, mas apenas para aumentar o retorno esperado *condicional ao acerto*.**

- A probabilidade de 1-2-3-4-5-6 sair é a mesma de qualquer outra combinação. O problema é que, se sair, você dividirá o prêmio com centenas ou milhares de pessoas que apostaram nela.
- Ao evitar combinações populares, você **não aumenta sua chance de ganhar**, mas aumenta o prêmio líquido *se* ganhar.
- Isso é matematicamente fundamentado: o valor esperado de um bilhete é E = P(ganhar) × (Prêmio / N_ganhadores). Evitar combinações superpopuladas aumenta o denominador esperado.

**Edge real?** Sim, mas pequeno e não transforma o jogo. Estudos mostram que combinações como sequências numéricas ou datas (1-12) são superapostadas. Um filtro estrutural bem feito pode elevar o EV em ~10-20% – ainda muito negativo (ex.: de -50% para -40%).

---

## O que NÃO funciona (ilusões comuns)

- **Análise de frequência**: Números "atrasados" ou "quentes" não predizem nada. É a falácia do jogador.
- **Geradores genéticos / algoritmos evolutivos**: Se a função fitness é baseada em dados passados, você otimiza ruído. Não há evidência de que funcionem.
- **Teste de hipóteses (chi-quadrado, etc.)**: Rejeitar a hipótese nula de uniformidade em amostras passadas é esperado devido a múltiplos testes. Mas isso não se traduz em previsão futura.
- **Teoria do caos / redes neurais / machine learning**: Dados i.i.d. não têm estrutura previsível. Qualquer "padrão" encontrado é overfitting. Retroavaliação com dados de treino/teste separados sempre volta ao aleatório.

---

## O que realmente funciona (edge matemático real, mas limitado)

| Abordagem | Tipo de edge | Magnitude | Funciona? |
|-----------|--------------|-----------|------------|
| Evitar combinações populares | ↑ valor esperado condicional | Pequeno (10-30% no EV, ainda negativo) | ✅ Sim |
| Wheeling systems | Redução de custo por prêmio garantido (dado acerto parcial) | Reduz variância, não melhora EV | ✅ Sim (útil em bolões) |
| Bolões (syndicates) | Compartilhar custo e prêmio, aumentando volume de combinações | Melhora a chance de *algum* prêmio, mas EV permanece negativo | ✅ Sim (racional para jogadores que vão jogar de qualquer forma) |
| Qualquer predição (CDM, entropia, ML, etc.) | Nenhum | Zero | ❌ Não |

---

## Conclusão honesta

> **Você não vai encontrar um edge preditivo porque ele não existe.** Loterias são processos aleatórios com expectativa negativa. O que você pode fazer é:
> 1. **Minimizar danos**: Evite combinações populares.
> 2. **Otimizar retorno condicional**: Use wheeling systems se você joga com muitos números (útil para bolões).
> 3. **Parar de tentar prever**: Abandone chi-quadrado, geradores genéticos, CDM para seleção de números. Eles são ruído.

Se você quer um projeto científico interessante, mude o foco: em vez de prever números, construa um sistema que *estime a popularidade das combinações* (usando dados históricos de apostas, não de sorteios) para maximizar o EV dado o prêmio esperado. Isso sim tem fundamentação econômica e estatística. Mas ainda assim, o EV será negativo – apenas menos pior.

## Kimi
Vou ser direto: **nenhum modelo matemático pode prever números de loteria em sorteios mecanicamente honestos**. Os sorteios são processos IID (independentes e identicamente distribuídos). A probabilidade da Mega-Sena permanece fixa em $1 / \binom{60}{6} \approx 1$ em 50 milhões, e da Lotofácil em $1 / \binom{25}{15} \approx 1$ em 3,2 milhões, independentemente do histórico.

O que a matemática pode oferecer são **micro-vantagens estruturais e comportamentais**, nunca oráculos preditivos. Abaixo, desmonto cada técnica que você mencionou com honestidade radical, seguido do que realmente move a agulha no valor esperado (EV).

---

### 1. Modelo Dirichlet-Multinomial (CDM): Detecção de Viés Mecânico

**O que é:** Em vez de assumir que cada bola tem probabilidade exatamente $1/n$, o CDM modela as probabilidades das categorias (bolas) como variáveis aleatórias extraídas de uma distribuição Dirichlet. Isso captura **superdispersão** — variações na frequência histórica maiores do que o esperado por acaso.

**Honestidade:**
- **Ilusão:** Usar CDM para "prever" que uma bola "atrasada" vai sair. Isso é a falácia do jogador (gambler's fallacy) com roupa bayesiana.
- **Realidade:** O CDM pode, em princípio, detectar **viés mecânico sistêmico** (bolas levemente desbalanceadas, desgaste de ventosas, imperfeições de fabricação). Em loterias modernas com auditoria rigorosa (como a Caixa), esse viés é estatisticamente imperceptível (< 0,01%). Mesmo que detectável, requer milhares de sorteios e a vantagem é microscópica.

**Aplicação válida:** Teste de hipótese sequencial. Se a posteriori do CDM mostrar que $P(\theta_i \neq 1/n \mid \text{dados}) > 0.95$ para alguma bola, você tem evidência de não-uniformidade. Mas apostar nisso é arriscado — a Caixa pode trocar o equipamento a qualquer momento.

**Python (conceitual):**
```python
import numpy as np
from scipy.stats import dirichlet

# Contagens históricas das 60 bolas
counts = np.array([...])  # shape (60,)
alpha_prior = np.ones(60)  # Dirichlet uniforme
alpha_posterior = alpha_prior + counts

# Amostras da posteriori
samples = dirichlet.rvs(alpha_posterior, size=10000)
# Intervalo de credibilidade para cada bola
# Se 1/60 não estiver no intervalo, há evidência de viés
```

---

### 2. Wheeling Systems: Cobertura Combinatória, não Predição

**O que é:** Um wheel é um conjunto estruturado de apostas que garante cobertura mínima de certos prêmios secundários se um subconjunto dos seus números-base for sorteado.

**Honestidade:**
- **Ilusão:** Achar que wheeling aumenta a chance de ganhar o prêmio máximo. Não aumenta. Se você aposta 100 jogos, sua chance de acertar a sena é exatamente $100 / \binom{60}{6}$, seja com wheeling ou com números aleatórios.
- **Realidade:** O edge do wheeling é **otimização de cobertura de prêmios secundários** (quina, quadra). Um wheel bem construído garante que, se você tiver 5 acertos entre seus 12 números escolhidos, maximize o número de quinas obtidas. É pura matemática combinatória (teoria dos blocos, coverings).

**Edge real:** Em sindicatos (bolões), wheeling permite cobrir mais números com eficiência de custo. A "vantagem" é estrutural no pagamento, não na probabilidade de acerto.

**Referência matemática:** Busque por *"covering designs"* $C(v, k, t)$ — cobertura mínima de $t$-subconjuntos por $k$-subconjuntos de um $v$-conjunto. Para Mega-Sena, $v=12, k=6, t=4$.

---

### 3. Entropia Condicional: Detecção de Dependência que Quase Sempre é Espúria

**O que é:** Mede $H(X_t \mid X_{t-1}, \ldots, X_{t-k})$, a incerteza do sorteio atual dado o histórico. Se $H(X_t \mid \text{passado}) < H(X_t)$, há informação preditiva.

**Honestidade:**
- **Ilusão:** 99,9% das "dependências" encontradas em séries temporais de loteria são **ruído amostral** (data dredging). Com milhares de possíveis padrões testados, alguns parecerão significativos por acaso (problema de multiplicidade).
- **Realidade:** Se um sorteio apresentasse dependência mensurável, seria evidência de fraude ou defeito mecânico grave, não de um padrão natural. Loterias são projetadas para serem processos de Markov com memória zero.

**Onde pode ter valor:** Entropia de **distribuições marginais** (não condicional). Comparar a entropia das frequências históricas vs. a entropia máxima (uniforme) pode quantificar o quanto o sistema se desviou da aleatoriedade perfeita. Mas isso é diagnóstico, não preditivo.

---

### 4. Filtros Estruturais: Evitar Multidões, não Adivinhar Bolas

**O que são:** Regras como "nunca mais que 3 números pares", "soma entre 150 e 200", "não sequências", etc.

**Honestidade:**
- **Ilusão:** Acreditar que essas regras aumentam a chance de acerto. Cada combinação de 6 números tem exatamente a mesma probabilidade de sair: $\binom{60}{6}^{-1}$. Uma sequência como $(1, 2, 3, 4, 5, 6)$ é tão provável quanto $(4, 12, 23, 34, 45, 56)$.
- **Realidade:** O edge aqui é **comportamental, não probabilístico**. Humanos evitam sequências e padrões "não aleatórios". Portanto, se você apostar em $(1,2,3,4,5,6)$ e ganhar, provavelmente dividirá o prêmio com dezenas de pessoas. Se apostar em uma combinação "feia" (distribuída, com soma extrema), reduz drasticamente a probabilidade de dividir o prêmio.

**Aplicação válida:** Modelar a distribuição de popularidade das apostas e fazer **inverse frequency weighting** — escolher combinações que minimizem $P(\text{dividir} \mid \text{ganhar})$.

---

### O que REALMENTE Funciona (Edge Verificável)

Se você quer aumentar o EV (valor esperado), esqueça predição. Foque em:

#### A. Otimização do Prêmio Líquido (Avoiding the Crowd)
O EV de uma loteria é negativo. A única forma de torná-lo menos negativo (ou, em raras superacumulações, ligeiramente positivo) é reduzir a chance de dividir o prêmio.

- **Análise de frequência de apostas humanas:** Números de datas (1-31), sequências, padrões geométricos na cartela, números "quentes" da mídia.
- **Estratégia:** Use um gerador que produza combinações com:
  - Soma total extrema (muito baixa ou muito alta) — evita o centro da distribuição que humanos favorecem.
  - Máxima dispersão espacial na cartela.
  - Evitar números consecutivos.
  - Incluir números > 31.

Isso não aumenta sua chance de ganhar, mas aumenta o valor esperado do prêmio *condicional* a ganhar.

#### B. Wheeling Matemático com Foco em Prêmios Secundários
Se você tem orçamento para apostar sistematicamente, use algoritmos de cobertura (covering designs) para garantir retorno mínimo em quinas/quadras se acertar 5 ou 4 números do seu conjunto-base.

#### C. Kelly Criterion / Bankroll Management
Se você identifica um EV positivo (raro, geralmente apenas em rollovers muito altos), o Critério de Kelly determina a fração ótima do bankroll a apostar:

$$f^* = \frac{bp - q}{b}$$

Onde $b$ é a odd líquida, $p$ a probabilidade, $q = 1-p$. Na prática, para loteria, $f^*$ será próximo de zero — ou seja, não aposte mais que uma fração minúscula.

#### D. Análise de Viés Real (Testes Rigidos)
Se você tem acesso a dados granulares (não apenas resultados, mas ordem de extração, máquina usada, peso das bolas), pode aplicar:
- **Teste de Kolmogorov-Smirnov** nas frequências.
- **Teste de Runs** para aleatoriedade sequencial.
- **Análise de Variância (ANOVA)** entre diferentes máquinas/bolas.

Mas requer milhares de observações e a vantagem, se existir, é marginal.

---

### O que é Ilusão Pura (Evite Gastar Ciclos)

| Técnica | Status | Por quê |
|---------|--------|---------|
| **Números quentes/frios** | Ilusão | Falácia do jogador; bolas não têm memória. |
| **Entropia condicional preditiva** | Ilusão | Processos IID têm $H(X_t \mid X_{<t}) = H(X_t)$; qualquer desvio é ruído. |
| **Geradores genéticos de padrões** | Ilusão | Fitness function baseada em retrospectiva = overfitting extremo. |
| **Filtros estruturais como preditores** | Ilusão | Restringir o espaço de busca não altera a probabilidade dos eventos restantes. |
| **CDM para escolher números "atrasados"** | Ilusão | Bayesianismo mal aplicado; posteriori não cria causalidade retroativa. |

---

### Arquitetura Recomendada para seu Sistema Python

Se você quer um projeto estatisticamente honesto, redefina o objetivo: **maximizar o prêmio líquido esperado**, não a taxa de acerto.

```python
import numpy as np
import pandas as pd
from scipy.special import comb
from itertools import combinations

class HonestLotterySystem:
    def __init__(self, game='megasena'):
        self.game = game
        self.n = 60 if game == 'megasena' else 25
        self.k = 6 if game == 'megasena' else 15
        self.total_combos = comb(self.n, self.k, exact=True)
        
    def structural_unpopularity_score(self, combo):
        """
        Quanto maior o score, mais "feia" e impopular a aposta.
        Isso reduz P(dividir | ganhar).
        """
        combo = np.array(combo)
        score = 0
        # Penaliza números de data (1-31 são mais apostados)
        score += np.sum(combo <= 31) * 2
        # Penaliza sequências (ex: 10,11,12)
        diffs = np.diff(np.sort(combo))
        score += np.sum(diffs == 1) * 5
        # Penaliza somas centrais (humanos evitam extremos)
        s = np.sum(combo)
        mean_sum = self.k * (self.n + 1) / 2
        score -= abs(s - mean_sum) * 0.1  # Extremos são bons
        # Penaliza padrões geométricos na cartela (se aplicável)
        return score
    
    def generate_unpopular_combo(self):
        """Gera combinação que minimiza chance de divisão."""
        best = None
        best_score = -np.inf
        for _ in range(10000):  # amostragem
            combo = np.random.choice(self.n, self.k, replace=False) + 1
            s = self.structural_unpopularity_score(combo)
            if s > best_score:
                best_score = s
                best = combo
        return np.sort(best)
    
    def covering_wheel(self, base_numbers, guarantee=4):
        """
        Implementa wheeling básico. Garante que se 'guarantee' números 
        do base_numbers estiverem no sorteio, pelo menos um jogo os captura.
        """
        # Algoritmo de cobertura gulosa (simplificado)
        # Na prática, use tabelas otimizadas (La Jolla Covering Repository)
        from itertools import combinations
        base = list(base_numbers)
        all_guarantees = list(combinations(base, guarantee))
        games = []
        # Heurística gulosa: cobrir o máximo de garantias não cobertas
        uncovered = set(all_guarantees)
        while uncovered:
            # Encontrar jogo de k números que cobre mais garantias
            best_game = None
            best_cover = 0
            for game in combinations(base, self.k):
                covers = sum(1 for g in uncovered if set(g).issubset(set(game)))
                if covers > best_cover:
                    best_cover = covers
                    best_game = game
            if best_game is None:
                break
            games.append(best_game)
            # Remover coberturas
            uncovered = {g for g in uncovered if not set(g).issubset(set(best_game))}
        return games
    
    def kelly_fraction(self, jackpot, ticket_price, secondary_ev=0):
        """
        Fração ótima do bankroll a apostar, dado EV.
        """
        p = 1 / self.total_combos
        net_odds = (jackpot * (1 - 0.27) + secondary_ev) / ticket_price  # 27% IR
        b = net_odds - 1
        q = 1 - p
        f = (b * p - q) / b if b > 0 else 0
        return max(0, f)

# Exemplo de uso
sys = HonestLotterySystem('megasena')
combo = sys.generate_unpopular_combo()
print(f"Aposta 'anti-crowd': {combo}")
```

---

### Veredito Final

Seu sistema atual performa no nível do aleatório **porque esse é o limite teórico superior para predição**. Não há erro de implementação — há erro de expectativa.

A matemática honesta oferece apenas três edges verdadeiros em loterias:
1. **Não dividir o prêmio** (fugir das multidões comportamentais).
2. **Cobertura combinatória eficiente** (wheeling para prêmios secundários).
3. **Detecção de falhas mecânicas** (quase impossível em loterias reguladas modernas).

Todo o resto — chi-quadrado preditivo, entropia condicional, GA de padrões, CDM como bola de cristal — é **apofenia estatística** (ver padrões onde existe apenas ruído). Reconhecer isso não é derrota; é o primeiro passo para construir um sistema que pelo menos otimiza o que é matematicamente otimizável.

# Pergunta: Para a Lotofácil brasileira (15/25), quais são os filtros estruturais com base estatística comprovada? Por exemplo: distribuição de soma, equilíbrio par/ímpar, distribuição por faixas (1-5, 6-10, 11-15, 16-20, 21-25), sequências consecutivas, repetições do concurso anterior. Quero os valores esperados e desvios padrão reais, não aproximações.

## Resposta Gemini
Para analisar a Lotofácil sob uma ótica de engenharia de dados e estatística pura, precisamos primeiro definir o universo amostral. O número total de combinações possíveis é dado por:

$$C(25, 15) = \binom{25}{15} = \frac{25!}{15!(25-15)!} = 3.268.760$$

Aqui estão os parâmetros estruturais exatos, baseados na distribuição hipergeométrica e na análise combinatória do espaço amostral completo.

---

### 1. Equilíbrio Par/Ímpar
Na Lotofácil, temos 13 números ímpares e 12 pares no volante. A probabilidade de uma combinação ter $k$ números ímpares segue a distribuição hipergeométrica:

$$P(X=k) = \frac{\binom{13}{k} \binom{12}{15-k}}{\binom{25}{15}}$$

| Ímpares | Pares | Combinações | Probabilidade | Status |
| :--- | :--- | :--- | :--- | :--- |
| 8 | 7 | 1.019.304 | **31,18%** | Moda (Mais provável) |
| 7 | 8 | 849.420 | **25,99%** | Alta frequência |
| 9 | 6 | 660.660 | **20,21%** | Alta frequência |
| 6 | 9 | 283.140 | 8,66% | Baixa frequência |
| 10 | 5 | 226.512 | 6,93% | Baixa frequência |

* **Valor Esperado ($E$):** $15 \cdot (13/25) = \mathbf{7,8}$ ímpares.
* **Desvio Padrão ($\sigma$):** $\approx \mathbf{1,21}$.

---

### 2. Repetições do Concurso Anterior
Este é um filtro de memória de curto prazo. Como 15 números são sorteados de 25, a interseção entre dois sorteios independentes é alta.

| Repetidos | Combinações | Probabilidade |
| :--- | :--- | :--- |
| 9 | 1.051.050 | **32,15%** |
| 8 | 772.200 | **23,62%** |
| 10 | 756.756 | **23,15%** |
| 7 | 250.250 | 7,65% |
| 11 | 273.000 | 8,35% |

* **Valor Esperado ($E$):** $15 \cdot (15/25) = \mathbf{9}$ números repetidos.
* **Desvio Padrão ($\sigma$):** $\sqrt{15 \cdot \frac{15}{25} \cdot \frac{10}{25} \cdot \frac{10}{24}} = \mathbf{1,22}$.

---

### 3. Distribuição de Soma
A soma dos 15 números sorteados varia entre 120 ($1+2+...+15$) e 270 ($11+12+...+25$). Pelo Teorema Central do Limite, a distribuição das somas aproxima-se de uma Gaussiana.



* **Média Teórica ($\mu$):** $15 \cdot \frac{(1+25)}{2} = \mathbf{195}$.
* **Desvio Padrão ($\sigma$):** $\sqrt{\frac{n(N-n)}{N-1} \cdot \sigma^2_{pop}} \approx \mathbf{18,02}$.
* **Filtro Real:** Aproximadamente **68%** dos sorteios estarão no intervalo $[\mu - \sigma, \mu + \sigma]$, ou seja, entre **177 e 213**. Apostas fora de $[160, 230]$ são estatisticamente raras (outliers).

---

### 4. Distribuição por Faixas (Grupos de 5)
Dividindo o volante em 5 faixas (1-5, 6-10, 11-15, 16-20, 21-25):

* **Valor Esperado por Faixa:** $15 \cdot (5/25) = \mathbf{3}$ números.
* **Comportamento Real:** A configuração mais comum não é $3-3-3-3-3$ (que ocorre em apenas ~3,8% dos casos), mas sim variações em torno dela, como $3-3-3-4-2$ ou $4-3-3-3-2$.
* **Filtro de Ouro:** Evite qualquer faixa com 0 ou 5 números. A probabilidade de uma faixa vir vazia é de apenas **0,8%**.

---

### 5. Sequências Consecutivas (Números Adjacentes)
Diferente da Mega-Sena, na Lotofácil é matematicamente impossível *não* ter sequências, dado que você escolhe 60% dos números disponíveis.

* **Média de Maior Sequência:** Em média, o maior bloco de números consecutivos em um sorteio da Lotofácil tem tamanho **4 ou 5**.
* **Filtro:** Sorteios onde a maior sequência é $\leq 2$ ou $\geq 10$ são extremamente raros.

---

### A Realidade Matemática do "Edge"

Para o seu sistema em Python, aqui está a "pílula amarga":

1.  **Filtros não aumentam a probabilidade de ganhar:** Ao aplicar um filtro de "Soma entre 177-213", você reduz o seu custo de aposta (elimina combinações), mas a probabilidade de o sorteio cair fora desse intervalo é exatamente proporcional à quantidade de números eliminados. 
2.  **Onde está o erro do seu Modelo Genético?** Provavelmente ele está convergindo para a "média" (ex: gerando apenas jogos com 8 ímpares, 9 repetidos e soma 195). O problema é que o sorteio real *varia*. Se você só joga na "média", você perde em todos os concursos que se desviam dela (que são a maioria, individualmente).
3.  **Abordagem CDM:** O uso de Dirichlet-Multinomial para capturar viés físico só teria edge se houvesse uma "não-aleatoriedade" mecânica persistente. Se a avaliação retroativa deu nível aleatório, seu teste de hipótese chi-quadrado já confirmou que o sistema é **estocasticamente robusto**.

**Sugestão técnica:** Em vez de usar o algoritmo genético para buscar "o número que vai sair", use-o para gerar **Covering Designs** (Wheeling Systems). Foque em garantir 14 pontos se 15 forem acertados dentro de um grupo de 18-20 números. Isso é matemática pura e aplicada, sem depender de "padrões" que o chi-quadrado já provou não existirem.

## Resposta Perplexity
Para a Lotofácil (15/25), filtros estruturais baseiam-se em dados históricos de ~3664 concursos (até 17/04/2026), mas desvios são pequenos e compatíveis com aleatoriedade hipergeométrica (sem edge preditivo). Valores reais derivam de contagens exatas; esperados teóricos usam soma dos primeiros 25 inteiros ajustada (\( \mu \approx 195 \), \( \sigma \approx 10.4 \)). [megaloterias.com](https://www.megaloterias.com.br/lotofacil/estatisticas/soma-das-dezenas)

## Soma das Dezenas
Soma histórica varia de 120-270, com ~90% entre 166-225; moda em 181-210. [megaloterias.com](https://www.megaloterias.com.br/lotofacil/estatisticas/soma-das-dezenas)
- Média real: ~195 (calculada de faixas: pico 30.75% em 181-195, 27.55% em 196-210).  
- Desvio padrão: ~12.5 (faixas de 15 unidades cobrem ~2σ).  
Filtro: Evite <166 ou >225 (4.86% + 4.34% = ~9% histórico). [megaloterias.com](https://www.megaloterias.com.br/lotofacil/estatisticas/soma-das-dezenas)

## Equilíbrio Par/Ímpar
13 pares/ímpares nos 25 números (12 pares, 13 ímpares). Histórico (3664 concursos):  
- 7P/8I: 31.20% (1143x).  
- 8P/7I: 25.44% (932x).  
- 6P/9I: 20.41% (748x).  
- 9P/6I: 11.65% (427x).  
Filtro: Priorize 6-9 pares (84% histórico); esperados ~7.5 ±1.5.

## Distribuição por Faixas
Faixas padrão: 1-5 (5 nums), 6-10 (5), 11-15 (5), 16-20 (5), 21-25 (5). Histórico não detalhado por faixa exata, mas equilíbrio ~3 por faixa (15/5=3). [loteriasinteligente.com](https://www.loteriasinteligente.com.br/analise_estatistica_avancada_lotofacil)
- Esperado: 3 ±1.4 por faixa (hipergeométrica σ=√(15*(5/25)*(20/25))≈1.4).  
Filtro: 2-4 por faixa (99% cobertura); evite 0 ou 5 em qualquer (raro <1%). [loteriasinteligente.com](https://www.loteriasinteligente.com.br/analise_estatistica_avancada_lotofacil)

## Sequências Consecutivas
Frequência de pares/trios consecutivos moderada (ex.: trios comuns: 4-5-6 em 72x, 10-11-12 em 67x até 2026). [solotofacil](https://solotofacil.com/numerosconsecutivos)
- Média histórica: 2-3 pares consecutivos por sorteio (~70% com ≥1 par).  
- Desvio: ±1; trios raros (~2%).  
Filtro: Inclua 1-2 pares (ex.: +1 num), evite >4 ( <5%). [solotofacil](https://solotofacil.com/numerosconsecutivos)

## Repetições do Concurso Anterior
~7.5 repetições em média (hipergeométrica: 15*(15/25)=9 esperadas? Ajuste real ~7-8 por independência). [loteriasinteligente.com](https://www.loteriasinteligente.com.br/analise_estatistica_avancada_lotofacil)
- Desvio padrão: ~2.1.  
Filtro: 5-10 repetições (90% histórico); 0 ou >12 raro. [steemit](https://steemit.com/pt/@paulomurilo/analisando-mais-a-fundo-os-resultados-da-mega-sena-and-ordem-vs-aleatoriedade)

| Filtro | Frequência Histórica Alta | Teórico Esperado | σ Real |
|--------|---------------------------|------------------|--------|
| Soma | 181-210 (~58%) | 195 | 12.5  [megaloterias.com](https://www.megaloterias.com.br/lotofacil/estatisticas/soma-das-dezenas) |
| Par/Ímpar | 7-8 cada (~57%) | 7.5 | 1.5  |
| Faixas | 2-4/faixa | 3/faixa | 1.4 |
| Consecutivos | 1-3 pares | 2 | 1  [solotofacil](https://solotofacil.com/numerosconsecutivos) |
| Repetições | 5-10 | 7.5 | 2.1  [loteriasinteligente.com](https://www.loteriasinteligente.com.br/analise_estatistica_avancada_lotofacil) |

Use em Python: Baixe histórico oficial (Caixa), calcule com `pandas.describe()` para atualizar σ reais. [github](https://github.com/dadosnapratica/mega-sena-simulador)

## Resposta Manus
# Relatório Técnico: Análise Estatística de Filtros Estruturais para Lotofácil (15/25)

Este relatório apresenta uma análise combinatória detalhada dos principais filtros estruturais para a Lotofácil (15/25), fornecendo valores esperados (EV) e desvios padrão (DP) exatos para cada categoria. O objetivo é subsidiar a criação de filtros matematicamente fundamentados para otimização de apostas.

---

## 1. Premissas e Metodologia

A Lotofácil consiste na escolha de 15 números dentre 25 disponíveis. O número total de combinações possíveis é $\binom{25}{15} = 3.268.760$. Todos os cálculos foram realizados considerando um sorteio perfeitamente aleatório e justo, onde cada combinação tem a mesma probabilidade de ser sorteada.

---

## 2. Distribuição Par/Ímpar

No universo de 25 números, temos 13 números ímpares e 12 números pares. A tabela abaixo mostra a distribuição de probabilidade para a quantidade de números ímpares e pares em um sorteio de 15 dezenas.

| Números Ímpares | Números Pares | Combinações | Probabilidade (%) |
| :-------------- | :------------ | :---------- | :---------------- |
| 3               | 12            | 286         | 0.0087            |
| 4               | 11            | 8.580       | 0.2625            |
| 5               | 10            | 84.942      | 2.5986            |
| 6               | 9             | 377.520     | 11.5493           |
| 7               | 8             | 849.420     | 25.9860           |
| 8               | 7             | 1.019.304   | 31.1832           |
| 9               | 6             | 660.660     | 20.2113           |
| 10              | 5             | 226.512     | 6.9296            |
| 11              | 4             | 38.610      | 1.1812            |
| 12              | 3             | 2.860       | 0.0875            |
| 13              | 2             | 66          | 0.0020            |

**Estatísticas:**
- **EV (Número de Ímpares):** 7.8000
- **DP (Número de Ímpares):** 1.2490

**Recomendação de Filtro:** A maioria dos sorteios (aproximadamente 77%) terá entre 7 e 9 números ímpares (e, consequentemente, entre 8 e 6 números pares). Jogos fora dessa faixa são estatisticamente menos prováveis.

---

## 3. Repetições do Concurso Anterior

Considerando que um concurso anterior já sorteou 15 números, e 10 não foram sorteados, a distribuição de quantos números se repetem do concurso anterior segue a distribuição hipergeométrica. A tabela abaixo mostra a probabilidade de um determinado número de dezenas se repetir do sorteio anterior.

| Números Repetidos | Combinações | Probabilidade (%) |
| :---------------- | :---------- | :---------------- |
| 5                 | 3.003       | 0.0919            |
| 6                 | 50.050      | 1.5312            |
| 7                 | 289.575     | 8.8589            |
| 8                 | 772.200     | 23.6236           |
| 9                 | 1.051.050   | 32.1544           |
| 10                | 756.756     | 23.1512           |
| 11                | 286.650     | 8.7694            |
| 12                | 54.600      | 1.6704            |
| 13                | 4.725       | 0.1446            |
| 14                | 150         | 0.0046            |
| 15                | 1           | 0.0000            |

**Estatísticas:**
- **EV (Número de Repetições):** 9.0000
- **DP (Número de Repetições):** 1.2247

**Recomendação de Filtro:** A grande maioria dos sorteios (aproximadamente 79%) terá entre 8 e 10 números repetidos do concurso anterior. Jogos com poucas ou muitas repetições são menos comuns.

---

## 4. Distribuição por Faixas (Quadrantes)

Dividimos os 25 números em 5 faixas de 5 números cada (1-5, 6-10, 11-15, 16-20, 21-25). A distribuição de números sorteados em cada faixa é idêntica devido à simetria. A tabela abaixo mostra a probabilidade de ter $k$ números em uma faixa específica.

| Números na Faixa | Combinações | Probabilidade (%) |
| :--------------- | :---------- | :---------------- |
| 0                | 15.504      | 0.4743            |
| 1                | 193.800     | 5.9289            |
| 2                | 775.200     | 23.7154           |
| 3                | 1.259.700   | 38.5375           |
| 4                | 839.800     | 25.6917           |
| 5                | 184.756     | 5.6522            |

**Estatísticas (por Faixa):**
- **EV (Números na Faixa):** 3.0000
- **DP (Números na Faixa):** 1.0000

**Recomendação de Filtro:** A maioria dos sorteios (aproximadamente 88%) terá entre 2 e 4 números em cada faixa. É raro ter 0, 1 ou 5 números em uma única faixa.

---

## 5. Soma das Dezenas

A soma das 15 dezenas sorteadas pode variar de 120 (1+2+...+15) a 270 (11+12+...+25). A distribuição da soma é aproximadamente normal. As estatísticas exatas são:

**Estatísticas:**
- **EV (Soma das Dezenas):** 195.0000
- **DP (Soma das Dezenas):** 18.0278

**Intervalos de Confiança (aproximados pela distribuição normal):**
- **68.2% (1 DP):** Entre 177 e 213
- **95.4% (2 DP):** Entre 159 e 231
- **99.7% (3 DP):** Entre 144 e 246

**Recomendação de Filtro:** A grande maioria dos sorteios terá a soma das dezenas entre 177 e 213. Jogos com somas muito baixas ou muito altas são estatisticamente menos prováveis.

---

## 6. Maior Sequência Consecutiva

Este filtro analisa o comprimento da maior sequência de números consecutivos em um sorteio. A tabela abaixo mostra a distribuição de probabilidade para o comprimento da maior sequência.

| Maior Sequência | Combinações | Probabilidade (%) |
| :-------------- | :---------- | :---------------- |
| 2               | 9.042       | 0.2766            |
| 3               | 402.292     | 12.3072           |
| 4               | 990.110     | 30.2901           |
| 5               | 866.888     | 26.5204           |
| 6               | 519.695     | 15.8988           |
| 7               | 266.805     | 8.1623            |
| 8               | 125.840     | 3.8498            |
| 9               | 55.055      | 1.6843            |
| 10              | 22.022      | 0.6737            |
| 11              | 7.865       | 0.2406            |
| 12              | 2.420       | 0.0740            |
| 13              | 605         | 0.0185            |
| 14              | 110         | 0.0034            |
| 15              | 11          | 0.0003            |

**Estatísticas:**
- **EV (Maior Sequência):** 5.0029
- **DP (Maior Sequência):** 1.4926

**Recomendação de Filtro:** A maioria dos sorteios (aproximadamente 85%) terá uma maior sequência consecutiva entre 3 e 7 números. Sequências muito curtas (2) ou muito longas (acima de 8) são menos prováveis.

---

## 7. Conclusão

Os filtros estruturais apresentados não aumentam a probabilidade de acertar as 15 dezenas, pois a Lotofácil é um jogo de sorteio aleatório. No entanto, eles são ferramentas valiosas para **otimizar a escolha de combinações** que se alinham com padrões estatisticamente mais frequentes, evitando jogos com características muito improváveis ou que são populares entre outros apostadores (o que diluiria o prêmio em caso de acerto). Ao utilizar esses filtros, o apostador pode direcionar suas apostas para um subconjunto de combinações que, embora não mais prováveis de serem sorteadas, são mais representativas dos resultados históricos e podem, indiretamente, melhorar o valor esperado do prêmio ao evitar divisões com múltiplos ganhadores em padrões 

## Resposta DeepSeek
Esta é uma pergunta matemática direta: para cada filtro estrutural na Lotofácil (15 números escolhidos de 1 a 25), a distribuição de probabilidade segue um modelo hipergeométrico ou multinomial. Os valores esperados e desvios padrão são, portanto, perfeitamente determinados pela combinatoria.

Para que você possa verificar, implementar e confiar nos resultados, apresento os cálculos analíticos exatos para cada um dos filtros solicitados.

---

### 1. Distribuição de Soma (Somatória dos 15 números)

A média da soma (`E[S]`) e a variância (`Var(S)`) são calculadas diretamente pela soma das médias e covariâncias dos números individuais.

- **Números do Universo**: $1, 2, \dots, 25$.
- **Média populacional**: $\mu_X = \frac{1+25}{2} = 13$
- **Variância populacional**: $\sigma_X^2 = \frac{25^2 - 1}{12} = 52$

**Valores Esperados Exatos**:
- **Média da Soma**: $E[S] = n \cdot \mu_X = 15 \cdot 13 = \mathbf{195}$
- **Variância da Soma**: $Var(S) = n \cdot \sigma_X^2 \cdot \frac{N-n}{N-1} = 15 \cdot 52 \cdot \frac{25-15}{25-1} = 780 \cdot \frac{10}{24} = \mathbf{325}$
- **Desvio Padrão da Soma**: $\sigma_S = \sqrt{Var(S)} = \sqrt{325} \approx \mathbf{18.03}$

**Interpretação**: A soma total de qualquer resultado deve ficar entre 120 (1+2+...+15) e 330 (11+12+...+25). O valor esperado é exatamente 195. Aproximadamente 95% das somas estarão entre $195 \pm 2 \cdot 18.03 = [159, 231]$.

---

### 2. Equilíbrio Par/Ímpar

Este é um problema hipergeométrico: temos 13 números ímpares (1, 3, ..., 25) e 12 pares no universo de 25. Ao sortear 15 números, qual a distribuição da quantidade de ímpares ($k$) na amostra?

- **População**: $N = 25$, com $K = 13$ ímpares (sucessos).
- **Amostra**: $n = 15$.

**Valores Esperados Exatos**:
- **Média (Quantidade de Ímpares)**: $E[X] = n \cdot \frac{K}{N} = 15 \cdot \frac{13}{25} = \mathbf{7.8}$
- **Variância**: $Var(X) = n \cdot \frac{K}{N} \cdot \frac{N-K}{N} \cdot \frac{N-n}{N-1} = 15 \cdot \frac{13}{25} \cdot \frac{12}{25} \cdot \frac{10}{24} = \mathbf{1.56}$
- **Desvio Padrão**: $\sigma_X = \sqrt{1.56} \approx \mathbf{1.25}$

**Distribuição Completa** (Probabilidades exatas para cada $k$):
| Ímpares | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Pares | 11 | 10 | 9 | 8 | 7 | 6 | 5 | 4 |
| Prob. (%) | 0.08 | 0.84 | 4.80 | 13.72 | 21.77 | 20.07 | 10.41 | 2.77 |

> **Conclusão Estatística**: A configuração de 7 ímpares e 8 pares, apesar de ser a mais próxima da média (7.8), não é a mais provável. A moda da distribuição é **8 ímpares e 7 pares**, com uma probabilidade de 21.77%.

---

### 3. Distribuição por Faixas (5 faixas de 5 números)

Este é um problema **Multinomial Generalizado**. Dividimos o universo de 25 números em 5 grupos de 5: $G_1 = \{1..5\}, G_2 = \{6..10\}, G_3 = \{11..15\}, G_4 = \{16..20\}, G_5 = \{21..25\}$. Em cada sorteio de 15 números, queremos a distribuição de quantos números vêm de cada grupo.

- **Parâmetros**: Cada grupo tem $N_i = 5$ números. A amostra total é $n = 15$.
- **Média por grupo**: $E[X_i] = n \cdot \frac{N_i}{N} = 15 \cdot \frac{5}{25} = \mathbf{3}$

**Valores Esperados e Limites Estatísticos**:
- **Média**: Espera-se exatamente **3 números por grupo**.
- **Desvio Padrão**: $\sigma = \sqrt{ n \cdot p \cdot (1-p) \cdot \frac{N-n}{N-1} } = \sqrt{ 15 \cdot 0.2 \cdot 0.8 \cdot \frac{10}{24} } \approx \mathbf{1.0}$

**Análise dos Desvios**:
- 68% dos sorteios terão entre 2 e 4 números por grupo (média ± 1 desvio).
- 95% dos sorteios terão entre 1 e 5 números por grupo (média ± 2 desvios).
- É extremamente raro (menos de 1% dos casos) uma faixa ter 0 números, e virtualmente impossível ter 6 ou mais.

---

### 4. Sequências Consecutivas

A probabilidade de não haver *nenhuma* sequência de dois números consecutivos em um sorteio de 15 números de 1 a 25 é calculada por um problema clássico de "estrelas e barras". A quantidade de combinações sem consecutivos é $C(25-15+1, 15) = C(11, 15) = 0$. Isso prova que **é impossível sortear 15 números de 1 a 25 sem que haja pelo menos um par consecutivo**.

Para quantificar a quantidade esperada de pares consecutivos, podemos usar variáveis indicadoras.

- **Número de pares de números consecutivos possíveis no universo**: 24 pares (1-2, 2-3, ..., 24-25).
- **Probabilidade de um par específico (ex: 1 e 2) estar presente**: $\frac{C(23, 13)}{C(25, 15)} \approx 0.4$.
- **Média (Quantidade Esperada de Pares Consecutivos)**: $E[C] = 24 \cdot 0.4 \approx \mathbf{9.6}$

> **Interpretação**: É esperado que um resultado da Lotofácil contenha aproximadamente **9 ou 10 pares de números consecutivos**.

---

### 5. Repetições do Concurso Anterior

Se o concurso anterior sorteou um conjunto fixo $A$ de 15 números, qual a distribuição do número de repetições ($k$) no próximo concurso?

- **População**: $N = 25$, com $K = 15$ "sucessos" (os números do concurso passado).
- **Amostra**: $n = 15$.

**Valores Esperados Exatos**:
- **Média (Repetições Esperadas)**: $E[X] = n \cdot \frac{K}{N} = 15 \cdot \frac{15}{25} = \mathbf{9}$
- **Variância**: $Var(X) = n \cdot \frac{K}{N} \cdot \frac{N-K}{N} \cdot \frac{N-n}{N-1} = 15 \cdot \frac{15}{25} \cdot \frac{10}{25} \cdot \frac{10}{24} = \mathbf{1.5}$
- **Desvio Padrão**: $\sigma_X = \sqrt{1.5} \approx \mathbf{1.22}$

**Distribuição Completa**:
| Repetições | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Prob. (%) | 0.01 | 0.14 | 0.98 | 4.00 | 10.00 | 15.87 | 15.87 | 10.00 | 4.00 |

> **Conclusão Estatística**: É praticamente impossível ter menos de 5 ou mais de 13 repetições. A grande maioria dos sorteios repete entre **7 e 11 números** do concurso anterior, com 9 ou 10 repetições sendo os casos mais prováveis.

---

### Tabela de Resumo (Valores Teóricos Exatos)

| Filtro | Média Esperada (E) | Desvio Padrão (σ) | Faixa Comum (E ± σ) |
| :--- | :--- | :--- | :--- |
| **Soma dos Números** | 195 | 18.03 | 177 – 213 |
| **Números Ímpares** | 7.8 | 1.25 | 6.5 – 9.1 |
| **Números por Faixa (1-5,6-10,...)** | 3 | 1.0 | 2 – 4 |
| **Repetições do Concurso Anterior** | 9 | 1.22 | 8 – 10 |

> **Nota Final**: Os valores esperados e desvios padrão apresentados acima são os parâmetros teóricos e exatos que regem a Lotofácil. Qualquer desvio observado na sua base de dados histórica em relação a esses valores não indica um "padrão preditivo", mas sim uma flutuação estatística esperada devido ao tamanho finito da amostra, que será corrigida pela lei dos grandes números.

Se você tiver outras variáveis que gostaria de analisar ou precisar de ajuda para implementar esses cálculos em Python, é só me falar.

## Resposta Kimi
Vou calcular os valores exatos via enumeração completa do espaço amostral (3.268.760 combinações) e derivar as fórmulas analíticas quando possível. Isso elimina qualquer aproximação.
Aqui estão os parâmetros populacionais exatos da Lotofácil (15/25) sob a hipótese nula de sorteio uniforme e independente. Todos os valores foram derivados analiticamente e confirmados por enumeração completa das 3.268.760 combinações.

---

### 1. Soma dos 15 Números

| Métrica | Valor Exato | Decimal |
|---------|-------------|---------|
| **Valor Esperado** | $195$ | 195,0 |
| **Variância** | $325$ | 325,0 |
| **Desvio Padrão** | $5\sqrt{13}$ | 18,0278 |

**Derivacão:** A soma de uma amostra sem reposição de tamanho $n=15$ de $\{1,\ldots,25\}$ tem valor esperado $n \cdot \frac{N+1}{2} = 15 \cdot 13$. A variância é $n \cdot \frac{N+1}{2} \cdot \frac{N-n}{N-1} \cdot \frac{N+1}{6}$ ... mais diretamente: $\text{Var}(S) = n \cdot \sigma^2_{\text{pop}} \cdot \frac{N-n}{N-1} = 15 \cdot 52 \cdot \frac{10}{24} = 325$.

---

### 2. Distribuição Par/Ímpar

Há 13 ímpares e 12 pares em $\{1,\ldots,25\}$. Seja $X$ o número de ímpares sorteados. $X \sim \text{Hipergeométrica}(N=25, K=13, n=15)$.

| Métrica | Ímpares | Pares |
|---------|---------|-------|
| **Valor Esperado** | $\frac{39}{5} = 7{,}8$ | $\frac{36}{5} = 7{,}2$ |
| **Variância** | $\frac{39}{25} = 1{,}56$ | $\frac{39}{25} = 1{,}56$ |
| **Desvio Padrão** | $\frac{\sqrt{39}}{5}$ | $\frac{\sqrt{39}}{5}$ |
| | $\approx 1{,}2490$ | $\approx 1{,}2490$ |

---

### 3. Distribuição por Faixas (1–5, 6–10, 11–15, 16–20, 21–25)

Cada faixa contém exatamente 5 números. Por simetria, a distribuição conjunta é uma hipergeométrica multivariada equilibrada.

| Faixa | $E[X_i]$ | $\text{Var}(X_i)$ | $\text{DP}(X_i)$ |
|-------|----------|-------------------|------------------|
| 1–5 | $3$ | $1$ | $1$ |
| 6–10 | $3$ | $1$ | $1$ |
| 11–15 | $3$ | $1$ | $1$ |
| 16–20 | $3$ | $1$ | $1$ |
| 21–25 | $3$ | $1$ | $1$ |

**Covariância entre quaisquer duas faixas distintas:** $\text{Cov}(X_i, X_j) = -\frac{1}{4} = -0{,}25$

*(Verificação: $5 \cdot 1 + 20 \cdot (-0{,}25) = 5 - 5 = 0$, consistente com $\sum X_i = 15$ ser constante.)*

---

### 4. Sequências Consecutivas

Definições precisas:
- **Pares Consecutivos ($C$):** número de ocorrências $(k, k+1)$ dentro do sorteio. Exemplo: $\{3,4,5\}$ contribui com 2 pares.
- **Runs ($R$):** número de blocos consecutivos. Exemplo: $\{1,2,4,5,6,10\}$ tem $R=3$ runs.
- **Maior Sequência ($M$):** tamanho do maior bloco consecutivo.

**Relação exata:** $C = 15 - R$ (pois em cada run de tamanho $L$ há $L-1$ pares, e $\sum L_i = 15$).

| Métrica | Pares Consecutivos ($C$) | Runs ($R$) | Maior Sequência ($M$) |
|---------|--------------------------|------------|----------------------|
| **Valor Esperado** | $\frac{42}{5} = 8{,}4$ | $\frac{33}{5} = 6{,}6$ | $5{,}0029$ |
| **Variância** | $\frac{77}{50} = 1{,}54$ | $\frac{77}{50} = 1{,}54$ | $2{,}2278$ |
| **Desvio Padrão** | $\frac{\sqrt{154}}{10} \approx 1{,}2410$ | $\frac{\sqrt{154}}{10} \approx 1{,}2410$ | $\approx 1{,}4926$ |

A variância de $C$ foi derivada analiticamente:
$$\text{Var}(C) = 24 \cdot \frac{91}{400} + 46 \cdot \frac{693}{9200} + 506 \cdot \left(-\frac{1477}{101200}\right) = \frac{77}{50}$$

**Distribuição exata da Maior Sequência ($M$):**

| Tamanho $m$ | Combinações | Probabilidade Exata |
|-------------|-------------|---------------------|
| 2 | 9.042 | $\frac{4521}{1634380} \approx 0{,}002766$ |
| 3 | 402.292 | $\approx 0{,}123072$ |
| 4 | 990.110 | $\approx 0{,}302901$ |
| 5 | 866.888 | $\approx 0{,}265204$ |
| 6 | 519.695 | $\approx 0{,}158988$ |
| 7 | 266.805 | $\approx 0{,}081623$ |
| 8 | 125.840 | $\approx 0{,}038498$ |
| 9 | 55.055 | $\approx 0{,}016843$ |
| 10 | 22.022 | $\approx 0{,}006737$ |
| 11 | 7.865 | $\approx 0{,}002406$ |
| 12 | 2.420 | $\approx 0{,}000740$ |
| 13 | 605 | $\approx 0{,}000185$ |
| 14 | 110 | $\approx 0{,}000034$ |
| 15 | 11 | $\approx 0{,}000003$ |

*(Note: $M \geq 2$ com probabilidade 1, pois 15 números em 25 posições forçam pelo menos uma adjacência — de fato, $P(M=1) = 0$.)*

---

### 5. Repetições em Relação ao Concurso Anterior

Seja $Y$ o número de dezenas repetidas de um sorteio anterior fixado. $Y \sim \text{Hipergeométrica}(N=25, K=15, n=15)$.

| Métrica | Valor Exato | Decimal |
|---------|-------------|---------|
| **Valor Esperado** | $9$ | 9,0 |
| **Variância** | $\frac{3}{2}$ | 1,5 |
| **Desvio Padrão** | $\sqrt{\frac{3}{2}} = \frac{\sqrt{6}}{2}$ | 1,2247 |

**Derivacão:** $E[Y] = n \cdot \frac{K}{N} = 15 \cdot \frac{15}{25} = 9$. $\text{Var}(Y) = 15 \cdot \frac{15}{25} \cdot \frac{10}{25} \cdot \frac{10}{24} = \frac{3}{2}$.

---

### O que isso significa para filtros?

Esses números são os **parâmetros da hipótese nula**. Eles definem o que um sorteio aleatório "deveria" produzir. A utilidade estatística desses filtros é **diagnóstica, não preditiva**:

| Filtro | Uso Válido | Ilusão a Evitar |
|--------|------------|-----------------|
| **Soma** | Detectar *bias* mecânico se a média histórica desviar significativamente de 195 | Acreditar que "somas atrasadas" corrigirão-se |
| **Par/Ímpar** | Testar uniformidade; esperado ~7-8 ímpares | Evitar "equilíbrio perfeito" (7/8 ou 8/7 é esperado, não obrigatório) |
| **Faixas** | Identificar desvios de equiprobabilidade por região | Não há memória entre faixas; cada sorteio é independente |
| **Consecutivos** | 8,4 pares é a moda natural; runs ~6,6 | Maior sequência de 5 é mais comum que 3 (27% vs 12%) |
| **Repetições** | 9 repetições é o esperado natural | "Evitar repetições do último" reduz seu espaço sem aumentar probabilidade |

**O único edge estrutural verificável:** Na Lotofácil, o prêmio é dividido entre acertadores. Se seu gerador produzir combinações com **soma extrema** (muito abaixo de 177 ou muito acima de 213, i.e., $|Z| > 1$), **maior número de runs** (aposta "fragmentada") ou **padrões de faixas incomuns**, você reduz a chance de dividir o prêmio caso ganhe — pois humanos tendem a apostar em somas centrais, sequências simétricas e padrões geométricos na cartela.

A matemática diz: você não pode aumentar $P(\text{ganhar})$, mas pode, em princípio, aumentar $E[\text{prêmio líquido} \mid \text{ganhar}]$.

# Pergunta: Faça uma pesquisa profunda sobre 'lottery number prediction machine learning' e         
  'covering design lottery optimization'. Quero saber: (a) algum paper acadêmico demonstrou  
  edge real sobre o aleatório em loterias tipo 6/60 ou 15/25? (b) quais são os melhores      
  algoritmos de covering design para minimizar bilhetes? (c) existe alguma implementação     
  open-source de wheeling system em Python?
  
## Resposta Gemini Deep Research
