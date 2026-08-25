# Metodologia Inicial — Projeto 3
## Identificação de Parâmetros Ópticos por Ajuste Simultâneo de Transmissão e Reflexão

> **Documento vivo.**
>
> Este documento será atualizado conforme novas informações, restrições físicas e resultados forem obtidos durante o desenvolvimento do projeto.

---

# 1. Objetivo

Desenvolver, implementar e comparar diferentes algoritmos de otimização para identificar os parâmetros físicos de uma estrutura multicamada que melhor reproduzam **simultaneamente** os dados experimentais de transmissão e reflexão.

O problema será tratado como um problema inverso de identificação de parâmetros.

Dado um conjunto experimental contendo espessura, transmissão e reflexão, deseja-se encontrar o vetor de parâmetros físicos:

$$
\mathbf{p}^{*} = \arg\min_{\mathbf{p}\in\Omega} J(\mathbf{p})
$$

onde:

- $\mathbf{p}$ é o vetor dos oito parâmetros físicos;
- $\Omega$ é o espaço de busca sujeito às restrições físicas;
- $J(\mathbf{p})$ é a função objetivo que mede conjuntamente os erros de transmissão e reflexão.

O objetivo científico não será apenas encontrar o menor erro possível, mas também avaliar quais algoritmos apresentam maior:

- qualidade de ajuste;
- robustez;
- eficiência computacional;
- estabilidade dos parâmetros recuperados;
- consistência física.

---

# 2. Estrutura Física Inicial

O código atualmente fornecido considera uma estrutura com quatro meios:

1. ar;
2. camada de óxido;
3. camada ativa;
4. substrato de vidro.

Representação:

$$
\text{ar} \;|\; \text{óxido} \;|\; \text{camada ativa} \;|\; \text{vidro}
$$

A espessura da camada ativa é calculada no modelo a partir da espessura experimental e da espessura do óxido:

$$
d_{\text{ativa}} = d_{\text{medido}} - d_2
$$

---

# 3. Dados Experimentais

Cada observação experimental possui:

$$
[d_i,\; T_i^{exp},\; R_i^{exp}]
$$

onde:

- $d_i$ = espessura experimental;
- $T_i^{exp}$ = transmissão experimental;
- $R_i^{exp}$ = reflexão experimental.

O conjunto atualmente disponível possui 10 pontos experimentais, com espessuras entre aproximadamente 65 nm e 600 nm.

Transmissão e reflexão deverão ser utilizadas **simultaneamente** durante a identificação dos parâmetros.

---

# 4. Variáveis de Decisão

O vetor atualmente utilizado pelo modelo contém oito parâmetros:

$$
\mathbf{p} =
[
\log_{10}(\chi),
d_2,
n_{2,\omega},
n_{2,2\omega},
\operatorname{Re}(n_{3,\omega}),
\operatorname{Im}(n_{3,\omega}),
\operatorname{Re}(n_{3,2\omega}),
\operatorname{Im}(n_{3,2\omega})
]
$$

## 4.1 Susceptibilidade

$$
\log_{10}(\chi)
$$

Representa o parâmetro de escala associado à susceptibilidade utilizada pelo modelo.

**Limites:** ainda a definir.

---

## 4.2 Espessura do óxido

$$
d_2
$$

Restrição inicial:

$$
0 \leq d_2 \leq 20\;\text{nm}
$$

A espessura do óxido não poderá assumir valores negativos.

---

## 4.3 Índices de refração — parte real

Parâmetros:

$$
n_{2,\omega},\quad n_{2,2\omega},
$$

$$
\operatorname{Re}(n_{3,\omega}),\quad
\operatorname{Re}(n_{3,2\omega})
$$

Como o índice do ar é aproximadamente 1, será adotado inicialmente:

$$
n_{\text{real}} > 1
$$

ou, caso seja adotado um limite físico mais conservador:

$$
n_{\text{real}} \geq 1.2
$$

O limite inferior definitivo deverá ser confirmado.

**Limites superiores:** ainda a definir.

---

## 4.4 Índices de refração — parte imaginária

Parâmetros:

$$
\operatorname{Im}(n_{3,\omega})
$$

e

$$
\operatorname{Im}(n_{3,2\omega})
$$

Restrição inicial:

$$
0 \leq k \leq 4
$$

---

# 5. Restrições Físicas

As soluções produzidas pelos algoritmos deverão respeitar tanto os limites individuais quanto relações físicas entre os parâmetros.

## 5.1 Restrição da espessura do óxido

$$
0 \leq d_2 \leq 20\;\text{nm}
$$

---

## 5.2 Restrição dos índices reais

Inicialmente:

$$
n_{\text{real}} > 1
$$

ou:

$$
n_{\text{real}} \geq 1.2
$$

conforme definição final do orientador.

---

## 5.3 Restrição das partes imaginárias

$$
0 \leq k \leq 4
$$

---

## 5.4 Restrição de dispersão normal

Na condição de **dispersão normal**, o índice de refração aumenta com o aumento da frequência angular.

Como:

$$
2\omega > \omega
$$

deverá ser respeitada a relação:

$$
n(\omega) < n(2\omega)
$$

Portanto, para a camada 2:

$$
n_{2,\omega} < n_{2,2\omega}
$$

e, para a parte real do índice da camada 3:

$$
\operatorname{Re}(n_{3,\omega})
<
\operatorname{Re}(n_{3,2\omega})
$$

Esta é uma **restrição conjunta**, pois não pode ser garantida apenas pelos limites individuais de cada variável.

### Estratégias possíveis para impor a restrição

Preferência inicial:

1. reparametrização;
2. mecanismo nativo de restrições do algoritmo;
3. reparo de soluções;
4. função de penalidade.

Uma possível reparametrização é:

$$
n(2\omega)=n(\omega)+\Delta n
$$

com:

$$
\Delta n > 0
$$

garantindo automaticamente a condição de dispersão normal.

A estratégia escolhida deverá ser aplicada de forma equivalente entre os algoritmos para não favorecer artificialmente nenhum método.

---

# 6. Função Objetivo

O objetivo é minimizar simultaneamente o erro entre:

- transmissão experimental e teórica;
- reflexão experimental e teórica.

A função objetivo inicial será:

$$
J(\mathbf{p}) =
w_T J_T(\mathbf{p})
+
w_R J_R(\mathbf{p})
$$

Inicialmente:

$$
w_T = w_R = 1
$$

## 6.1 Erro de transmissão

$$
J_T =
\frac{1}{N}
\sum_{i=1}^{N}
\left(
\frac{
T_i^{exp}-T_i^{teo}(\mathbf{p})
}{
\max(T^{exp})
}
\right)^2
$$

## 6.2 Erro de reflexão

$$
J_R =
\frac{1}{N}
\sum_{i=1}^{N}
\left(
\frac{
R_i^{exp}-R_i^{teo}(\mathbf{p})
}{
\max(R^{exp})
}
\right)^2
$$

## 6.3 Erro total

Com pesos unitários:

$$
J = J_T + J_R
$$

A normalização separada é importante porque transmissão e reflexão apresentam escalas numéricas diferentes.

---

# 7. Penalidade do Pico de Transmissão

O código atual possui uma penalização adicional destinada a reproduzir o pico experimental de transmissão.

A função utilizada atualmente pode ser representada por:

$$
J =
w_TJ_T +
w_RJ_R +
w_PJ_P
$$

onde $J_P$ representa o erro associado ao pico experimental de transmissão.

O código atual utiliza um peso elevado para esse termo.

Para a comparação inicial entre algoritmos, deverão ser estudados pelo menos dois cenários:

## Cenário A — Ajuste global

$$
J = J_T + J_R
$$

## Cenário B — Ajuste global com penalização do pico

$$
J = J_T + J_R + w_PJ_P
$$

Isso permitirá avaliar se a penalização melhora efetivamente a identificação física ou apenas força o ajuste de um ponto específico.

---

# 8. Baseline

O método atualmente implementado no código do orientador será utilizado como **baseline**.

O procedimento atual utiliza múltiplos pontos iniciais e otimização local por mínimos quadrados não lineares ou método local equivalente.

Também poderá ser utilizado:

- Random Search;

como baseline simples para comparação.

---

# 9. Algoritmos Candidatos

A primeira comparação deverá considerar algoritmos adequados para otimização contínua e não linear.

## Baselines

- método local/multistart atual;
- Random Search.

## Metaheurísticas

- Genetic Algorithm (GA);
- Particle Swarm Optimization (PSO);
- Differential Evolution (DE);
- CMA-ES.

## Métodos híbridos

Após a comparação inicial, poderão ser testadas combinações entre busca global e refinamento local:

$$
DE \rightarrow \text{Local Search}
$$

$$
CMA\text{-}ES \rightarrow \text{Local Search}
$$

$$
GA \rightarrow \text{Local Search}
$$

A metaheurística localiza uma região promissora do espaço de busca e o método local realiza o refinamento final.

## Métodos futuros

- Bayesian Optimization;
- Surrogate Optimization;
- redes neurais como modelos substitutos do simulador.

---

# 10. Comparação Justa entre Algoritmos

Todos os algoritmos deverão receber:

- os mesmos dados experimentais;
- os mesmos limites físicos;
- as mesmas restrições;
- a mesma função objetivo;
- o mesmo orçamento de avaliações da função;
- critérios de parada comparáveis.

A principal unidade de orçamento computacional será o:

**número de avaliações da função objetivo.**

Não será utilizado apenas o número de iterações, pois diferentes algoritmos realizam quantidades diferentes de avaliações por iteração.

Valor inicial a definir, por exemplo:

$$
B = 10\,000,\; 25\,000\; \text{ou}\; 50\,000
$$

avaliações por execução.

---

# 11. Execuções Independentes

Como GA, PSO, DE, CMA-ES e outros métodos possuem componentes estocásticos, uma única execução não será considerada suficiente.

Proposta inicial:

$$
30 \text{ execuções independentes}
$$

Caso o custo computacional permita:

$$
50 \text{ execuções independentes}
$$

As mesmas seeds poderão ser utilizadas para organizar os experimentos:

```text
1
2
3
...
30
```

ou:

```text
1
2
3
...
50
```

---

# 12. Informações Registradas

Cada execução deverá armazenar:

- algoritmo;
- seed;
- função objetivo final $J$;
- erro de transmissão $J_T$;
- erro de reflexão $J_R$;
- oito parâmetros encontrados;
- número de avaliações;
- tempo total;
- critério de parada;
- curva de convergência;
- validade física da solução.

Exemplo de estrutura:

| Algoritmo | Seed | J | JT | JR | Avaliações | Tempo | Parâmetros |
|---|---:|---:|---:|---:|---:|---:|---|
| DE | 1 | ... | ... | ... | ... | ... | ... |
| DE | 2 | ... | ... | ... | ... | ... | ... |
| PSO | 1 | ... | ... | ... | ... | ... | ... |

---

# 13. Curvas de Convergência

Durante cada execução será registrado o melhor erro encontrado em função do número de avaliações.

Exemplo:

```text
Avaliações    Melhor J

100           0.482
500           0.193
1000          0.091
5000          0.028
10000         0.021
```

O gráfico principal será:

$$
\text{número de avaliações}
\rightarrow
\text{melhor }J
$$

Também poderão ser acompanhados separadamente:

$$
J_T
$$

e:

$$
J_R
$$

para verificar como cada algoritmo equilibra o ajuste das duas curvas.

---

# 14. Métricas de Comparação

A avaliação dos algoritmos será dividida em quatro dimensões principais.

## 14.1 Qualidade da solução

Para $J$, $J_T$ e $J_R$:

- melhor resultado;
- média;
- mediana;
- pior resultado;
- desvio padrão;
- intervalo interquartil (IQR).

A mediana deverá receber atenção especial devido à natureza estocástica dos algoritmos.

---

## 14.2 Robustez

Avaliar:

- dispersão dos erros entre execuções;
- IQR;
- frequência de convergência;
- presença de execuções muito ruins;
- taxa de sucesso.

Poderá ser definido posteriormente um limiar:

$$
J \leq J_{\text{alvo}}
$$

e:

$$
\text{Taxa de sucesso}
=
\frac{\text{execuções que atingiram }J_{\text{alvo}}}
{\text{execuções totais}}
$$

---

## 14.3 Eficiência Computacional

Avaliar:

- tempo de execução;
- número de avaliações até determinado erro;
- velocidade de convergência;
- avaliações necessárias para atingir determinado percentual da melhor solução conhecida.

---

## 14.4 Estabilidade dos Parâmetros Físicos

Além do erro final, deverá ser analisada a distribuição dos oito parâmetros encontrados.

Para cada parâmetro serão calculados, entre outros:

- mediana;
- média;
- desvio padrão;
- IQR;
- intervalo observado.

O objetivo é verificar se diferentes execuções convergem para aproximadamente os mesmos parâmetros físicos.

---

# 15. Identificabilidade dos Parâmetros

Um erro pequeno não garante necessariamente que os parâmetros físicos tenham sido identificados de forma única.

Pode ocorrer:

$$
J(\mathbf{p}_A) \approx J(\mathbf{p}_B)
$$

mas:

$$
\mathbf{p}_A \neq \mathbf{p}_B
$$

Isso indicaria que diferentes combinações de parâmetros conseguem reproduzir curvas semelhantes de transmissão e reflexão.

Portanto, deverá ser investigada a **identificabilidade** do problema.

Serão observadas:

- distribuições dos parâmetros;
- correlações entre parâmetros;
- soluções equivalentes;
- regiões do espaço de busca com erros semelhantes;
- parâmetros que permanecem estáveis;
- parâmetros pouco identificáveis.

---

# 16. Melhor Solução Conhecida

Como o ótimo global provavelmente é desconhecido, será considerada:

$$
J_{\text{best}}
=
\min_{\text{todos os algoritmos e execuções}} J
$$

Essa solução servirá como referência experimental, mas não deverá ser interpretada automaticamente como o ótimo global verdadeiro.

Poderá ser calculado um gap relativo:

$$
gap =
\frac{J_{\text{alg}}-J_{\text{best}}}
{\max(|J_{\text{best}}|,\epsilon)}
$$

onde $\epsilon$ evita divisão por zero.

---

# 17. Validação Estatística

A comparação estatística dependerá da estrutura final dos experimentos.

## Caso A — Um único problema experimental

Se todos os algoritmos forem avaliados repetidamente sobre o mesmo conjunto experimental, será considerada inicialmente uma comparação não paramétrica das distribuições, por exemplo:

- Kruskal-Wallis para comparação global;
- teste pós-hoc apropriado;
- correção de Holm para múltiplas comparações;
- medidas de tamanho de efeito.

## Caso B — Múltiplos problemas ou cenários

Caso existam diferentes:

- materiais;
- amostras;
- conjuntos experimentais;
- níveis de ruído;
- funções objetivo;
- cenários físicos;

poderão ser utilizados:

- Friedman;
- Iman-Davenport;
- testes pós-hoc;
- correção de Holm;
- medidas de tamanho de efeito.

A metodologia estatística definitiva será escolhida após a definição completa dos experimentos.

---

# 18. Validação Física

Toda solução encontrada deverá ser verificada quanto a:

- $0 \leq d_2 \leq 20$ nm;
- índices reais dentro dos limites estabelecidos;
- $0 \leq k \leq 4$;
- condição de dispersão normal;
- $n(\omega) < n(2\omega)$;
- ausência de espessuras físicas inválidas;
- estabilidade numérica;
- ausência de NaN ou infinito;
- consistência das curvas calculadas;
- plausibilidade física dos parâmetros.

Uma solução com baixo erro matemático, mas que viole as restrições físicas, não será considerada válida.

---

# 19. Análise de Sensibilidade

As melhores soluções serão perturbadas para verificar a sensibilidade da função objetivo aos parâmetros recuperados.

Para um parâmetro $p_j$:

$$
p_j' = p_j + \Delta p_j
$$

e será recalculado:

$$
J(\mathbf{p}')
$$

A análise poderá utilizar perturbações relativas, por exemplo:

$$
\pm 0.1\%,\quad
\pm 1\%,\quad
\pm 5\%
$$

ou perturbações físicas específicas para cada parâmetro.

O objetivo será identificar:

- parâmetros críticos;
- parâmetros pouco sensíveis;
- regiões robustas;
- soluções excessivamente dependentes de valores muito específicos.

---

# 20. Validação e Generalização

Como o conjunto experimental atual possui poucos pontos, deverá ser estudada uma estratégia de validação.

Possibilidades:

## Leave-One-Out

Retirar um ponto experimental, ajustar os parâmetros utilizando os demais e verificar a capacidade do modelo de reproduzir o ponto retirado.

## Bootstrap

Criar reamostragens dos dados experimentais e observar a distribuição dos parâmetros recuperados.

Essas análises poderão auxiliar na avaliação da estabilidade e identificabilidade dos parâmetros.

---

# 21. Organização dos Experimentos

Cada execução deverá possuir um identificador único.

Exemplo:

```text
EXP001

Algoritmo: DE
Seed: 1
Budget: 50000 avaliações

J_total: ...
J_T: ...
J_R: ...

Parâmetros:
log10_chi: ...
d2: ...
n2_w: ...
n2_2w: ...
Re_n3_w: ...
Im_n3_w: ...
Re_n3_2w: ...
Im_n3_2w: ...

Tempo: ... s
Solução física válida: sim/não
```

---

# 22. Estrutura Inicial dos Arquivos

```text
project_3/

├── papers/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── simulator/
│   └── matlab_original/
│
├── optimization/
│   ├── baseline/
│   ├── ga/
│   ├── pso/
│   ├── de/
│   ├── cmaes/
│   └── hybrid/
│
├── experiments/
│
├── results/
│   ├── raw/
│   ├── summary/
│   └── statistical_tests/
│
├── figures/
│
├── logs/
│
├── notebooks/
│
└── methodology.md
```

---

# 23. Perguntas em Aberto

## Parâmetros

- Qual será o limite inferior definitivo dos índices reais: $>1$ ou $\geq1.2$?
- Quais serão os limites superiores dos índices reais?
- Qual será o intervalo permitido para $\log_{10}(\chi)$?
- A restrição de dispersão normal será aplicada às partes reais dos índices das duas camadas exatamente como definido neste documento?
- Existe alguma restrição adicional envolvendo as partes imaginárias?

## Função objetivo

- A penalização do pico de transmissão deverá permanecer?
- Qual peso deverá ser utilizado para o pico?
- $T$ e $R$ terão inicialmente pesos iguais?
- Existem incertezas experimentais disponíveis para cada ponto?

## Computação

- Quanto tempo leva uma avaliação completa do modelo?
- O simulador será mantido em MATLAB/Octave ou será migrado/encapsulado em Python?
- É possível paralelizar as avaliações?
- Qual orçamento máximo de avaliações é computacionalmente viável?

## Validação

- Existem valores experimentais ou de literatura conhecidos para alguns dos oito parâmetros?
- Existem outras amostras ou conjuntos experimentais disponíveis?
- Existe uma faixa esperada para cada índice que possa restringir melhor o espaço de busca?

---

# 24. Próximos Passos

1. Reproduzir o resultado atual do código fornecido pelo orientador.
2. Confirmar o significado físico dos oito parâmetros.
3. Confirmar todos os limites superiores e inferiores.
4. Implementar explicitamente a restrição de dispersão normal:
   $$
n(\omega)<n(2\omega)
$$
5. Isolar o simulador físico da rotina de otimização.
6. Criar uma interface única para avaliação de $\mathbf{p}$.
7. Implementar a função objetivo conjunta $J_T+J_R$.
8. Reproduzir o método atual como baseline.
9. Implementar Random Search.
10. Implementar Differential Evolution.
11. Implementar Genetic Algorithm.
12. Implementar PSO.
13. Implementar CMA-ES.
14. Definir um orçamento comum de avaliações.
15. Executar inicialmente 30 seeds por algoritmo.
16. Registrar curvas de convergência.
17. Comparar qualidade, robustez e eficiência.
18. Comparar a estabilidade dos parâmetros físicos.
19. Realizar análise estatística.
20. Investigar identificabilidade.
21. Realizar análise de sensibilidade.
22. Testar métodos híbridos global + local.
23. Avaliar estratégias de validação e reamostragem.
24. Produzir gráficos e tabelas para publicação.

---

# 25. Ideias Futuras

Após a consolidação da metodologia principal:

- otimização multiobjetivo de $J_T$ e $J_R$;
- NSGA-II;
- Bayesian Optimization;
- Surrogate Models;
- redes neurais substituindo parcialmente o simulador;
- otimização híbrida global-local;
- análise de incerteza dos parâmetros;
- análise de perfil da função objetivo;
- paralelização das avaliações;
- GPU computing, quando aplicável;
- execução em cluster;
- comparação entre diferentes estratégias de tratamento de restrições.

---

# 26. Resumo da Formulação Atual

## Problema

Identificar oito parâmetros físicos:

$$
\mathbf{p} =
[
\log_{10}(\chi),
d_2,
n_{2,\omega},
n_{2,2\omega},
\operatorname{Re}(n_{3,\omega}),
\operatorname{Im}(n_{3,\omega}),
\operatorname{Re}(n_{3,2\omega}),
\operatorname{Im}(n_{3,2\omega})
]
$$

## Objetivo

$$
\min_{\mathbf{p}} J(\mathbf{p})
$$

com:

$$
J = J_T + J_R
$$

como formulação inicial.

## Restrições atualmente conhecidas

$$
0 \leq d_2 \leq 20\;\text{nm}
$$

$$
n_{\text{real}} > 1
$$

ou, a confirmar:

$$
n_{\text{real}} \geq 1.2
$$

$$
0 \leq k \leq 4
$$

e, devido à dispersão normal:

$$
n(\omega) < n(2\omega)
$$

isto é:

$$
n_{2,\omega} < n_{2,2\omega}
$$

e:

$$
\operatorname{Re}(n_{3,\omega})
<
\operatorname{Re}(n_{3,2\omega})
$$

## Comparação inicial

Algoritmos principais:

- método atual como baseline;
- Random Search;
- GA;
- PSO;
- DE;
- CMA-ES.

Cada algoritmo deverá receber o mesmo orçamento de avaliações da função objetivo e será executado múltiplas vezes com diferentes seeds.

O algoritmo final será avaliado não apenas pelo menor erro, mas pela combinação de:

$$
\boxed{
\text{qualidade}
+
\text{robustez}
+
\text{eficiência}
+
\text{estabilidade física}
}
$$
