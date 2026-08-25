# Metodologia Definitiva — Projeto 3
## Identificação de Parâmetros Ópticos por Ajuste Simultâneo de Transmissão e Reflexão

> **Documento vivo.**
>
> Esta versão consolida as definições atualmente acordadas para o Projeto 3 e deve ser utilizada como referência metodológica principal no repositório.

---

# 1. Objetivo

Desenvolver, implementar e comparar diferentes algoritmos de otimização para identificar os parâmetros físicos de uma estrutura multicamada que melhor reproduzam **simultaneamente** os dados experimentais de transmissão e reflexão.

O problema será tratado como um problema inverso de identificação de parâmetros:

$$
\mathbf{p}^{*}=\arg\min_{\mathbf{p}\in\Omega}J(\mathbf{p})
$$

onde:

- $\mathbf{p}$ é o vetor dos oito parâmetros físicos;
- $\Omega$ é o espaço de busca sujeito às restrições físicas;
- $J(\mathbf{p})$ é a função objetivo conjunta de transmissão e reflexão.

A comparação dos algoritmos deverá considerar não apenas o menor erro, mas também robustez, eficiência computacional, estabilidade dos parâmetros e consistência física.

---

# 2. Implementação

Toda a nova infraestrutura será desenvolvida em **Python**.

O código MATLAB/Octave original será preservado em `legacy_matlab/` como:

- referência da formulação física;
- referência numérica;
- base de validação da implementação Python.

A implementação Python deverá reproduzir numericamente o comportamento do código original **antes** da introdução de novos algoritmos de otimização.

---

# 3. Estrutura Física

O modelo considera quatro meios:

1. ar;
2. camada de óxido;
3. camada ativa;
4. substrato de vidro.

$$
\text{ar}\;|\;\text{óxido}\;|\;\text{camada ativa}\;|\;\text{vidro}
$$

A espessura efetiva da camada ativa é:

$$
d_{\text{ativa}}=d_{\text{medido}}-d_2
$$

---

# 4. Dados Experimentais

Cada observação possui:

$$
[d_i,\;T_i^{exp},\;R_i^{exp}]
$$

| $d$ (nm) | $T_{exp}$ | $R_{exp}$ |
|---:|---:|---:|
| 65 | 2192.89 | 621.17 |
| 80 | 2133.53 | 876.81 |
| 100 | 2522.53 | 1137.68 |
| 150 | 3857.56 | 731.88 |
| 190 | 3649.85 | 1021.73 |
| 250 | 1988.13 | 920.289 |
| 300 | 359.05 | 1521.73 |
| 400 | 59.64 | 1072.46 |
| 500 | 37.68 | 1057.97 |
| 600 | 16.17 | 1028.98 |

Comprimento de onda fundamental:

$$
\lambda=1560\text{ nm}
$$

---

# 5. Vetor de Parâmetros

$$
\mathbf{p}=
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

---

# 6. Limites dos Parâmetros

## 6.1 Susceptibilidade

A variável usada pelo otimizador será:

$$
x_{\chi}=\log_{10}(\chi)
$$

com:

$$
-10\leq\log_{10}(\chi)\leq10
$$

A recuperação do valor físico é:

$$
\chi=10^{\log_{10}(\chi)}
$$

O logaritmo é utilizado apenas para tornar o espaço de otimização numericamente mais adequado.

## 6.2 Espessura do óxido

$$
0\leq d_2\leq20\text{ nm}
$$

## 6.3 Partes reais dos índices

$$
1.5\leq n_{\text{real}}\leq6
$$

Logo:

$$
1.5\leq n_{2,\omega},\;n_{2,2\omega},\;\operatorname{Re}(n_{3,\omega}),\;\operatorname{Re}(n_{3,2\omega})\leq6
$$

## 6.4 Partes imaginárias

$$
0\leq\operatorname{Im}(n_{3,\omega})\leq4
$$

$$
0\leq\operatorname{Im}(n_{3,2\omega})\leq4
$$

---

# 7. Restrição de Dispersão Normal

Na condição adotada de dispersão normal:

$$
n(\omega)<n(2\omega)
$$

Portanto:

$$
n_{2,\omega}<n_{2,2\omega}
$$

$$
\operatorname{Re}(n_{3,\omega})<\operatorname{Re}(n_{3,2\omega})
$$

Essas relações são obrigatórias para uma solução fisicamente válida.

A estratégia preferencial é utilizar parametrização ou constraints que evitem avaliações inválidas. Uma possível reparametrização é:

$$
n(2\omega)=n(\omega)+\Delta n
$$

com:

$$
\Delta n>0
$$

e mantendo:

$$
n(2\omega)\leq6
$$

A mesma lógica de tratamento de restrições deverá ser usada de forma justa em todos os algoritmos.

---

# 8. Funções Físicas Auxiliares

## 8.1 Impedância característica

$$
Z_0=\frac{1}{\varepsilon_0c}
$$

## 8.2 Coeficiente de reflexão

$$
r_{ij}=\frac{n_i-n_j-Z_0\sigma_S}{n_i+n_j+Z_0\sigma_S}
$$

## 8.3 Coeficiente de transmissão

$$
t_{ij}=\frac{2n_i}{n_i+n_j+Z_0\sigma_S}
$$

## 8.4 Índice do vidro

$$
n_{\text{glass}}=1.5130-0.003169l^2+\frac{0.003962}{l^2}
$$

onde:

$$
l=\frac{\lambda}{10^{-6}}
$$

com $l$ em micrômetros.

---

# 9. Função Objetivo

A função objetivo principal será:

$$
J(\mathbf{p})=J_T(\mathbf{p})+J_R(\mathbf{p})
$$

Não será utilizada, na formulação principal, a penalização especial do pico presente no código MATLAB original.

## 9.1 Erro de transmissão

Para preservar a formulação original:

$$
J_T=\sum_{i=1}^{N}\left(\frac{T_i^{exp}-T_i^{teo}(\mathbf{p})}{\max(T^{exp})}\right)^2
$$

## 9.2 Erro de reflexão

$$
J_R=\sum_{i=1}^{N}\left(\frac{R_i^{exp}-R_i^{teo}(\mathbf{p})}{\max(R^{exp})}\right)^2
$$

## 9.3 Erro total

$$
J=J_T+J_R
$$

Quanto menor $J$, melhor a solução.

A normalização separada evita que uma das respostas domine numericamente a função objetivo apenas por diferença de escala.

---

# 10. Penalização do Pico

O código MATLAB original possui um termo adicional para reforçar o ajuste do pico de transmissão.

Esse termo **não fará parte da função objetivo principal** deste projeto.

Poderá ser estudado futuramente apenas como experimento complementar.

---

# 11. Saídas Registradas

Cada avaliação completa deverá permitir recuperar:

- $J$;
- $J_T$;
- $J_R$;
- vetor completo $\mathbf{p}$;
- $T^{teo}$;
- $R^{teo}$.

Cada execução deverá registrar:

- algoritmo;
- seed;
- número de avaliações;
- tempo total;
- $J$ final;
- $J_T$ final;
- $J_R$ final;
- oito parâmetros encontrados;
- curva de convergência;
- critério de parada;
- validade física.

---

# 12. Validação MATLAB → Python

Esta etapa é obrigatória antes da comparação dos algoritmos.

Para o mesmo vetor de parâmetros $\mathbf{p}_{test}$, deverá ser verificado:

$$
T_{\text{Python}}\approx T_{\text{MATLAB}}
$$

$$
R_{\text{Python}}\approx R_{\text{MATLAB}}
$$

$$
J_{T,\text{Python}}\approx J_{T,\text{MATLAB}}
$$

$$
J_{R,\text{Python}}\approx J_{R,\text{MATLAB}}
$$

$$
J_{\text{Python}}\approx J_{\text{MATLAB}}
$$

Nenhum algoritmo novo deverá ser considerado validado antes da equivalência numérica do simulador.

A regressão automática atual usa `rtol=1e-12` e `atol=1e-28`, valores
conservadores diante dos erros observados de ordem 1e-14 a 1e-15. Qualquer
alteração futura dessa tolerância deve ser justificada pela validação física.

---

# 13. Separação entre Física e Otimização

A implementação deverá separar completamente:

1. simulador físico;
2. função objetivo;
3. constraints;
4. algoritmos de otimização;
5. execução dos experimentos;
6. análise dos resultados.

Fluxo:

```text
parâmetros p
    ↓
simulador físico
    ↓
T_teórico, R_teórico
    ↓
função objetivo
    ↓
J_T, J_R, J
    ↓
otimizador
```

Nenhum algoritmo deverá possuir lógica física exclusiva fora das constraints compartilhadas.

---

# 14. Baselines

Os baselines já implementados são Random Search e Differential Evolution.
O método local/multistart legado permanece apenas como referência histórica,
não como participante da comparação principal atual.

---

# 15. Algoritmos de Otimização

A comparação principal deverá incluir:

- Differential Evolution (DE);
- Genetic Algorithm (GA);
- Particle Swarm Optimization (PSO);
- CMA-ES.

Estado no checkpoint de 25 de agosto de 2026: Random Search e Differential
Evolution estão implementados e testados. A próxima implementação é Genetic
Algorithm, seguida de PSO e CMA-ES.

---

# 16. Métodos Híbridos

Após a comparação principal poderão ser estudados:

$$
DE\rightarrow\text{Local Search}
$$

$$
CMA\text{-}ES\rightarrow\text{Local Search}
$$

$$
GA\rightarrow\text{Local Search}
$$

---

# 17. Comparação Justa entre Algoritmos

Todos os algoritmos deverão utilizar:

- mesmos dados experimentais;
- mesmos limites;
- mesmas restrições;
- mesma função objetivo;
- mesmo orçamento de avaliações;
- critérios de parada comparáveis.

A unidade principal de orçamento será o **número de avaliações da função objetivo**.

Não será utilizado apenas o número de iterações.

O orçamento final será escolhido após medir o custo de uma avaliação completa em Python.

---

# 18. Execuções Independentes

Plano inicial:

$$
30\text{ execuções independentes}
$$

Se o custo computacional permitir:

$$
50\text{ execuções independentes}
$$

As seeds deverão ser registradas para reprodutibilidade.

---

# 19. Curvas de Convergência

Cada execução deverá registrar:

$$
\text{número de avaliações}\rightarrow\text{melhor }J
$$

Também poderão ser armazenados $J_T$ e $J_R$ ao longo da execução.

---

# 20. Métricas de Comparação

## 20.1 Qualidade

Para $J$, $J_T$ e $J_R$:

- melhor resultado;
- média;
- mediana;
- pior resultado;
- desvio padrão;
- intervalo interquartil (IQR).

## 20.2 Robustez

- dispersão entre execuções;
- frequência de convergência;
- presença de outliers;
- taxa de sucesso;
- estabilidade dos resultados.

Poderá ser definido:

$$
J\leq J_{\text{alvo}}
$$

com:

$$
\text{Taxa de sucesso}=\frac{\text{execuções que atingiram }J_{\text{alvo}}}{\text{execuções totais}}
$$

## 20.3 Eficiência

- tempo de execução;
- número de avaliações até determinado erro;
- velocidade de convergência;
- avaliações necessárias para atingir um percentual da melhor solução conhecida.

## 20.4 Estabilidade Física

Para cada um dos oito parâmetros:

- média;
- mediana;
- desvio padrão;
- IQR;
- mínimo;
- máximo.

---

# 21. Identificabilidade

Um erro baixo não garante identificação única dos parâmetros.

Pode ocorrer:

$$
J(\mathbf{p}_A)\approx J(\mathbf{p}_B)
$$

mas:

$$
\mathbf{p}_A\neq\mathbf{p}_B
$$

Serão investigados:

- distribuições dos parâmetros;
- correlações;
- soluções equivalentes;
- regiões de baixo erro;
- parâmetros estáveis;
- parâmetros pouco identificáveis.

---

# 22. Melhor Solução Conhecida

$$
J_{\text{best}}=\min_{\text{todos os algoritmos e execuções}}J
$$

Essa solução será usada como referência experimental, sem ser automaticamente considerada o ótimo global verdadeiro.

Opcionalmente:

$$
gap=\frac{J_{\text{alg}}-J_{\text{best}}}{\max(|J_{\text{best}}|,\epsilon)}
$$

---

# 23. Validação Estatística

## Um único problema experimental

- Kruskal-Wallis;
- pós-hoc apropriado;
- correção de Holm;
- tamanho de efeito.

## Múltiplos cenários

Caso sejam criados diferentes materiais, amostras, conjuntos, níveis de ruído ou cenários:

- Friedman;
- Iman-Davenport;
- pós-hoc;
- correção de Holm;
- tamanho de efeito.

A escolha definitiva deverá ser justificada de acordo com a estrutura final dos experimentos.

---

# 24. Validação Física

Uma solução só será considerada válida se respeitar:

$$
0\leq d_2\leq20\text{ nm}
$$

$$
1.5\leq n_{\text{real}}\leq6
$$

$$
0\leq k\leq4
$$

$$
n(\omega)<n(2\omega)
$$

Além disso:

- ausência de NaN;
- ausência de infinito;
- estabilidade numérica;
- consistência das curvas;
- plausibilidade física.

---

# 25. Análise de Sensibilidade

Para cada parâmetro:

$$
p_j'=p_j+\Delta p_j
$$

será recalculado:

$$
J(\mathbf{p}')
$$

Poderão ser utilizadas perturbações como:

$$
\pm0.1\%,\quad\pm1\%,\quad\pm5\%
$$

ou perturbações físicas específicas.

---

# 26. Validação e Generalização

## Leave-One-Out

Retirar um ponto experimental, ajustar nos restantes e avaliar o ponto removido.

## Bootstrap

Reamostrar os dados e observar a distribuição dos parâmetros recuperados.

Essas análises poderão auxiliar na avaliação da estabilidade e identificabilidade.

---

# 27. Estrutura do Projeto Python

```text
project_3/
│
├── AGENTS.md
├── README.md
├── pyproject.toml
│
├── docs/
│   ├── methodology.md
│   ├── equations.md
│   └── decisions.md
│
├── legacy_matlab/
│   ├── FIT_SHG_norm_MoS2_T_fit_4layers.m
│   ├── rij.m
│   ├── tij.m
│   └── nlimeglass.m
│
├── src/
│   ├── physics/
│   │   ├── fresnel.py
│   │   ├── glass.py
│   │   ├── transfer_matrix.py
│   │   └── simulator.py
│   │
│   ├── optimization/
│   │   ├── objective.py
│   │   ├── constraints.py
│   │   ├── random_search.py
│   │   ├── differential_evolution.py
│   │   ├── genetic_algorithm.py
│   │   ├── pso.py
│   │   └── cmaes.py
│   │
│   ├── experiments/
│   │   ├── runner.py
│   │   └── config.py
│   │
│   └── analysis/
│       ├── plots.py
│       ├── statistics.py
│       └── parameters.py
│
├── tests/
├── results/
└── notebooks/
```

---

# 28. Tecnologias Python

Preferências iniciais:

- NumPy;
- SciPy;
- pandas;
- matplotlib;
- pytest;
- type hints;
- dataclasses quando útil.

A lógica principal deverá permanecer em módulos Python testáveis.

Notebooks serão usados apenas para exploração, análise e visualização.

---

# 29. Organização dos Resultados

Exemplo:

```text
EXP001

algorithm: DE
seed: 1
budget: 50000

J: ...
J_T: ...
J_R: ...

log10_chi: ...
d2_nm: ...
n2_w: ...
n2_2w: ...
re_n3_w: ...
im_n3_w: ...
re_n3_2w: ...
im_n3_2w: ...

runtime_s: ...
n_evaluations: ...
valid_physics: true
```

---

# 30. Próximos Passos

Concluídos: organização do repositório, preservação do MATLAB, port físico,
validação MATLAB/Octave × Python, benchmark, função objetivo, constraints,
parametrização normalizada, Random Search e Differential Evolution.

1. Implementar Genetic Algorithm.
2. Implementar PSO.
3. Implementar CMA-ES.
4. Criar runner comum para o experimento comparativo.
5. Definir o budget final e executar 30 ou 50 seeds.
6. Comparar qualidade, robustez e eficiência.
7. Analisar estabilidade, identificabilidade, sensibilidade e reamostragem.
8. Só após a comparação principal, avaliar métodos híbridos e extensões.

---

# 31. Pontos Ainda em Aberto

- orçamento final de avaliações;
- uso definitivo de 30 ou 50 seeds;
- existência de incertezas experimentais por ponto;
- disponibilidade de outras amostras ou conjuntos experimentais;
- existência de valores de literatura ou experimentais para validação independente dos parâmetros recuperados.

---

# 32. Ideias Futuras

Após a consolidação da metodologia principal:

- otimização multiobjetivo de $J_T$ e $J_R$;
- NSGA-II;
- Bayesian Optimization;
- Surrogate Models;
- redes neurais substituindo parcialmente o simulador;
- análise de incerteza;
- métodos híbridos global-local;
- paralelização;
- execução em cluster;
- GPU computing, quando aplicável.

---

# 33. Resumo da Formulação Atual

## Vetor

$$
\mathbf{p}=
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
\boxed{
\mathbf{p}^{*}=\arg\min_{\mathbf{p}\in\Omega}[J_T(\mathbf{p})+J_R(\mathbf{p})]
}
$$

## Limites

$$
-10\leq\log_{10}(\chi)\leq10
$$

$$
0\leq d_2\leq20\text{ nm}
$$

$$
1.5\leq n_{\text{real}}\leq6
$$

$$
0\leq k\leq4
$$

## Dispersão normal

$$
n_{2,\omega}<n_{2,2\omega}
$$

$$
\operatorname{Re}(n_{3,\omega})<\operatorname{Re}(n_{3,2\omega})
$$

## Regra metodológica central

$$
\boxed{
\text{mesma física}
+
\text{mesma função objetivo}
+
\text{mesmas constraints}
+
\text{mesmo budget}
}
$$

A comparação final deverá considerar:

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
