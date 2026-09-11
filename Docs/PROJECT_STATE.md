# Project State

## 1. Objetivo científico

Identificar os seis parâmetros físicos da configuração final que reproduzem simultaneamente as
curvas experimentais de transmissão e reflexão:

    p* = argmin J(p),   J = J_T + J_R

A função principal não usa a penalização de pico do MATLAB legado.

## 2. Formulação atual

O modelo físico é uma pilha de quatro meios: ar | óxido | camada ativa |
vidro, sob fundamental de 1560 nm. Python é a implementação principal; o
MATLAB/Octave preservado é a referência física e numérica.

## 3. Vetor de parâmetros

    p = [log10_chi, delta_d3_nm, n3_w, k3_w, n3_2w, k3_2w]

chi = 10 ** log10_chi, delta_d3_nm está em nm, e os índices da camada 3
são n3 + 1j * k3. O óxido permanece na física com d2 = 10 nm e índices
n2_w = n2_2w = 1, fora do vetor de otimização.

## 4. Bounds e restrições físicas

    -10 <= log10_chi <= 10
    -50 <= delta_d3_nm <= 50
    0.1 <= n3_w, n3_2w <= 10
    0 <= k3_w, k3_2w <= 10

Os índices reais da camada ativa são independentes; `n3_w >= n3_2w` é
permitido. Esta é a **configuração final de seis variáveis, óxido fixo e
correção global de d3**. Os baselines históricos abaixo pertencem a espaços
anteriores de oito variáveis, incluindo o **Search-space version 1**, que exigia
`n2_w < n2_2w` e `1.5 <= n2_w, n2_2w <= 6`; eles são preservados apenas como
histórico e não são diretamente comparáveis aos benchmarks v2.

## 5. Função objetivo

J_T e J_R são as somas dos quadrados dos resíduos de transmissão e reflexão,
normalizados separadamente por max(T_exp) e max(R_exp). J = J_T + J_R. A
penalização de pico do ajuste MATLAB legado não pertence à análise principal.

## 6. Arquitetura implementada

- src/physics/: fresnel.py, glass.py, transfer_matrix.py e simulator.py.
- src/optimization/: constraints.py, objective.py, parameterization.py,
  random_search.py, differential_evolution.py, genetic_algorithm.py e
  particle_swarm.py.
- src/experiments/data.py: dados experimentais oficiais.
- src/analysis/plotting.py: carregamento read-only, estatísticas e plotting
  comum dos benchmarks.
- scripts/: validação MATLAB/Python, benchmark, runners dos baselines e
  regenerador único de figuras salvas.
- tests/: testes unitários e regressão; results/: artefatos reprodutíveis.

## 7. Validação histórica MATLAB/Octave × Python

    max_rel_error_T = 1.6717503026056207e-14
    max_rel_error_R = 3.644239657078057e-15
    max_intermediate_frobenius_error = 1.0878030299442186e-15

    MATLAB/Octave × Python (modelo antigo de oito parâmetros): PASS

As fixtures em tests/reference/ registram a equivalência da implementação
anterior. Elas não são uma referência numérica para a configuração final,
pois o MATLAB versionado não contém `p(9)`/`delta_d3_nm` nem o óxido fixo.

## 8. Parametrização normalizada

Todos os algoritmos trabalham no mesmo cubo z ∈ [0,1]^6 e usam a transformação
z → p de src/optimization/parameterization.py. `delta_d3_nm = -50 + 100*z[1]`;
as demais coordenadas são mapeadas independentemente entre seus bounds. Não há
transformação triangular, `DELTA_N` nem restrição de dispersão normal.

Para cada ponto experimental, o simulador usa
`d3_effective_nm = max(d3_nominal_nm + delta_d3_nm, 0)`. O mesmo offset é
aplicado globalmente e os dados experimentais não são modificados.

## 9. Benchmark computacional

    10000 avaliações físicas: 4.192534 s
    média: 0.000419043 s/avaliação
    throughput: aproximadamente 2385 avaliações/s

Ambiente medido: Python 3.12.13, Windows 11, AMD64, 8 CPUs lógicas, baseline
serial. O budget científico final ainda não foi decidido. Os baselines atuais
usaram 50000 avaliações por seed.

## 10. Algoritmos implementados — Search-space version 1 (histórico)

### Random Search

Status: implementado e testado. Cinco seeds (1 a 5), 50000 avaliações por
seed e 250000 no total.

    melhor J = 0.5841852495274906
    mediana J = 0.6852560724860886
    pior J = 0.8865663180429331
    melhor seed = 2

Melhor solução: J_T = 0.1652336637150435, J_R = 0.4189515858124471 e
p = [9.558241528334502, 14.638645197723788, 1.9245971716044772,
3.0739695246678553, 1.5002756980322782, 1.6019837621258533,
2.7647710610323006, 0.4322388347104993].

Há diferença entre o menor J_R isolado dentre as seeds e o J_R da melhor
solução global; não os confundir. Artefatos: results/random_search_baseline/.

### Differential Evolution

Status: implementado e testado. SciPy 1.18.1; best1bin, popsize 15,
mutation (0.5, 1.0), recombination 0.7, latinhypercube, deferred, tol=0,
atol=0 e polish=False. Cinco seeds (1 a 5), 50000 avaliações físicas por
seed e 250000 no total.

    seed 1: 0.3818430128665412
    seed 2: 0.3818430638493236
    seed 3: 0.3818429946001101
    seed 4: 0.3818430194775517
    seed 5: 0.3818430366504482

    melhor J = 0.3818429946001101
    mediana J = 0.3818430194775517
    pior J = 0.3818430638493236
    melhor seed = 3

Melhor p = [9.540644916150043, 19.99999983369976, 2.567103143029925,
2.567103171440757, 1.500000018020065, 1.156280448848984,
3.098351557311543, 0.7560948470435371]. Para ela, J_T =
0.05700607504244844, J_R = 0.3248369195576617 e J =
0.3818429946001101. Tempo total das cinco seeds: 113.437136 s. Artefatos:
results/differential_evolution_baseline/.

### Genetic Algorithm

Status: implementado e testado. Implementação própria real-coded com NumPy:
população 100, torneio 3, SBX (0.9, eta 15), mutação polinomial (1/8 por
gene, eta 20), elitismo 1, inicialização uniforme e clipping em z. Cinco
seeds (1 a 5), 50000 avaliações físicas por seed e 250000 no total.

    seed 1: 0.3887575468305548
    seed 2: 0.3838408040675216
    seed 3: 0.4148273935319119
    seed 4: 0.4180227137750425
    seed 5: 0.3855212537352614

    melhor J = 0.3838408040675216
    mediana J = 0.3887575468305548
    pior J = 0.4180227137750425
    melhor seed = 2

Melhor p = [9.52877737115147, 19.99999638111071, 2.529927342995089,
2.529933579076557, 1.500000030869841, 1.027925056760741,
3.086736962547977, 0.868587020336933]. Para ela, J_T =
0.05681867610718783, J_R = 0.3270221279603338 e J =
0.3838408040675216. Tempo total: 116.029422 s. Artefatos:
results/genetic_algorithm_baseline/.

## 11. Resultados do Search-space version 1 (histórico)

Sob o mesmo orçamento, as medianas foram 0.6852560724860886 (Random Search),
0.3818430194775517 (DE) e 0.3887575468305548 (GA). Esta é uma comparação
descritiva das cinco seeds; não houve inferência estatística formal nem
alegação de superioridade estatística.

Ponto de atenção: a melhor solução DE está próxima de d2_nm ≈ 20,
re_n3_w ≈ 1.5 e n2_w ≈ n2_2w. Isso não deve ser interpretado ainda como
resultado físico definitivo: investigar ótimo em fronteira, influência dos
bounds, sensibilidade, identificabilidade e eventual discussão dos limites
com o orientador.

## 11.1. Rebenchmark concluído — Search-space version 2

Os baselines foram executados sem alteração de hiperparâmetros, com
seeds 1–5 e 50.000 avaliações físicas por seed (250.000 por algoritmo). Os
artefatos foram gravados separadamente em `results/search_space_v2/`; a
regeneração padronizada não modificou seus CSVs de origem.

| Algoritmo | J seed 1 | J seed 2 | J seed 3 | J seed 4 | J seed 5 | melhor | mediana | pior |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Random Search | 0.8040634083560697 | 0.9572795005488242 | 0.8020238622100739 | 0.7699993100460996 | 0.8515962452818939 | 0.7699993100460996 | 0.8040634083560697 | 0.9572795005488242 |
| Differential Evolution | 0.2289452841009371 | 0.2289447012953141 | 0.2289455857387721 | 0.2289449083201715 | 0.2289449226936709 | 0.2289447012953141 | 0.2289449226936709 | 0.2289455857387721 |
| Genetic Algorithm | 0.2295586394292559 | 0.2464181162987 | 0.4170103266888674 | 0.2867114735957359 | 0.3052652472667555 | 0.2295586394292559 | 0.2867114735957359 | 0.4170103266888674 |
| Particle Swarm Optimization | 0.2289453001128831 | 0.2289454923444444 | 0.2290055047100253 | 0.2289703924041102 | 0.2289446836404906 | 0.2289446836404906 | 0.2289454923444444 | 0.2290055047100253 |

Melhores vetores v2, na ordem oficial de `p`:

- Random Search, seed 4: `J_T = 0.4250677478621953`, `J_R = 0.3449315621839043`, `p = [9.547710706515243, 3.686002204795598, 2.079369015811906, 1.754644230469224, 1.717849994752797, 1.001766592387957, 2.198877734162601, 1.489090335322588]`.
- Differential Evolution, seed 2: `J_T = 0.07164101301487766`, `J_R = 0.1573036882804364`, `p = [9.694355922910546, 19.99999978200804, 5.999999992862717, 1.352185962623454, 1.837811686768519, 0.664047087445284, 1.837812231198259, 2.070816084177408]`.
- Genetic Algorithm, seed 1: `J_T = 0.07169590086434673`, `J_R = 0.1578627385649092`, `p = [9.677986839048025, 19.99999979359033, 5.999999865120634, 1.259737986643408, 1.811233567739495, 0.6747873073945851, 1.811388418928967, 2.008944703893034]`.
- Particle Swarm Optimization, seed 5: `J_T = 0.07164151321255152`, `J_R = 0.157303170427939`, `p = [9.694329522497039, 19.99999999547781, 5.999999986469084, 1.351685776815688, 1.837702214402779, 0.6640782801736113, 1.83770226507933, 2.070765137012947]`.

Esta é somente uma comparação descritiva entre cinco seeds no espaço v2; não
autoriza inferência estatística de superioridade.

## 11.2. Weighted-reflection sensitivity experiment (complementar)

O objetivo científico principal continua `J = J_T + J_R`. O estudo
complementar otimizou `J_weighted = J_T + w_R J_R`, mantendo explicitamente
`J_T`, `J_R`, `J_unweighted` e `J_weighted` para a análise. Foram executadas
80 buscas: RS, DE, GA e PSO; `w_R = 1, 2, 5, 10`; seeds 1–5; 50.000
avaliações físicas por seed; total de 4.000.000 avaliações físicas.

As medianas `(J_T, J_R, J_unweighted)` mostram o trade-off W1→W10:

| Algoritmo | W1 | W2 | W5 | W10 |
|---|---|---|---|---|
| DE | (0.07164, 0.15730, 0.22894) | (0.09400, 0.14141, 0.23541) | (0.13215, 0.12916, 0.26131) | (0.16912, 0.12390, 0.29302) |
| GA | (0.07565, 0.18376, 0.28671) | (0.09824, 0.15140, 0.24566) | (0.14687, 0.12941, 0.27629) | (0.24933, 0.12270, 0.36805) |
| PSO | (0.07165, 0.15729, 0.22895) | (0.09401, 0.14140, 0.23541) | (0.13212, 0.12916, 0.26128) | (0.19498, 0.12374, 0.31702) |
| RS | (0.42145, 0.38262, 0.80406) | (0.51727, 0.30246, 0.81973) | (0.75217, 0.28852, 1.00876) | (0.75217, 0.28852, 1.00876) |

Nos métodos convergentes DE e PSO, W10 reduziu a mediana de `J_R` em cerca de
21% frente a W1, ao custo de aumento de `J_T` de 136% e 172%, respectivamente.
GA reduziu `J_R` em 33%, mas elevou `J_T` em 230% e exibiu maior dispersão. W2
é um compromisso provisório para investigação futura: já reduz `J_R` em torno
de 10% em DE/PSO, com custo de transmissão menor que W5/W10. Não é uma escolha
definitiva nem substitui o baseline W1.

Os vetores por seed, melhores soluções, trade-off `J_T` × `J_R`, curvas de
mediana+IQR e best-fits padronizados estão em `results/weighted_reflection/`.

## 11.3. Rebenchmark — Search Space 2, óxido 1.0–1.2

Os quatro algoritmos foram reexecutados no espaço da D-022, mantendo seeds
1–5, budget de 50.000 avaliações físicas por seed e hiperparâmetros dos
benchmarks anteriores. Foram 1.000.000 avaliações físicas no total. Os novos
artefatos são independentes dos resultados anteriores e estão em
`results/search_space_v2_oxide_1_1p2/`.

| Algoritmo | Melhor J | Mediana J | Pior J | Melhor seed | J_T/J_R da melhor execução |
|---|---:|---:|---:|---:|---:|
| Random Search | 0.7908501272158618 | 0.9285015884229715 | 1.0523644657139095 | 1 | 0.3323245886707624 / 0.4585255385450994 |
| Differential Evolution | 0.4825021358925249 | 0.4825021637743911 | 0.4825022826305730 | 2 | 0.1524089836947110 / 0.3300931521978139 |
| Genetic Algorithm | 0.4857178323122006 | 0.6877105036327225 | 1.8527406527030210 | 1 | 0.1525573841347026 / 0.3331604481774980 |
| Particle Swarm Optimization | 0.4825021116472447 | 0.4825021119439207 | 0.4825021124499362 | 1 | 0.1524013169661818 / 0.3301007946810628 |

O menor J global foi obtido pelo PSO (seed 1), com
`p = [9.449232008153444, 19.999999999831008, 1.1999999999309354,
1.1999999997903479, 1.5000000000068365, 0.8188089620085308,
2.3332593451599237, 1.3195661710414202]`. As figuras foram regeneradas
somente a partir dos CSVs; a verificação SHA-256 confirmou que nenhum CSV foi
alterado durante essa etapa.

Uma primeira execução do Random Search concluiu as 250.000 avaliações, mas
falhou ao serializar o histórico por incompatibilidade do writer CSV com
campos ponderados já presentes na estrutura de convergência. O exportador foi
corrigido e o algoritmo foi repetido com as mesmas seeds e budget; a tentativa
incompleta foi preservada fora da análise em
`random_search_failed_serialization_attempt/`. Portanto, o conjunto científico
reportado contém 1.000.000 avaliações; houve 250.000 avaliações adicionais de
tentativa técnica não incluídas nas estatísticas.

## 11.4. Rebenchmark — Search Space 2, óxido 1.0–1.1

Os quatro algoritmos foram executados no espaço da D-024, com seeds 1–5,
50.000 avaliações físicas por seed e os mesmos hiperparâmetros dos baselines.
O conjunto contém 20 execuções e 1.000.000 avaliações físicas. Os artefatos
foram gravados separadamente em `results/search_space_v2_oxide_fixed/`.

| Algoritmo | Melhor J | Mediana J | Pior J | Melhor seed | J_T/J_R da melhor execução |
|---|---:|---:|---:|---:|---:|
| Random Search | 0.8025944496691104 | 0.9309826762257616 | 1.0537840200511019 | 1 | 0.3401989986702860 / 0.4623954509988244 |
| Differential Evolution | 0.4882871562121017 | 0.4882871736283140 | 0.4882871849880713 | 4 | 0.1600533623786276 / 0.3282337938334741 |
| Genetic Algorithm | 0.4984919114831330 | 0.6789917362449082 | 1.8527406528660211 | 1 | 0.1595202448190916 / 0.3389716666640414 |
| Particle Swarm Optimization | 0.4882871383451756 | 0.4882871384098018 | 0.4882871384524209 | 5 | 0.1600598984371068 / 0.3282272399080688 |

O menor J global foi do PSO, seed 5, com
`p = [9.440234600414467, 19.999999999669175, 1.0999999999714871,
1.099999999999221, 1.5000000000109477, 0.8180586516071238,
2.261999893927211, 1.3246283677042552]`. As figuras foram regeneradas a
partir dos CSVs salvos, sem alterar seus hashes SHA-256.

## 12. Estado dos testes

    pytest: 164 passed

A suíte cobre Fresnel, vidro, simulador, regressão MATLAB/Octave, constraints,
objective, parameterization, Random Search, Differential Evolution, Genetic
Algorithm e a infraestrutura comum de análise/plotting.

## 12.1. Visualização padronizada dos benchmarks

Random Search, DE, GA e PSO usam agora o mesmo best-fit 1×2, com limites comuns
calculados dos dados experimentais e das melhores curvas salvas. A comparação
v2 4×2, convergência linear, convergência log-x, zoom das últimas 20% do budget e
tabela final estão em `results/comparisons/` para o histórico v1. Para v2,
os mesmos artefatos estão em `results/search_space_v2/comparisons/`. As curvas principais mostram
mediana e IQR em função de avaliações físicas.

O alinhamento entre seeds é stepwise por forward-fill, sem interpolação
linear. PNGs são salvos a 320 DPI e PDFs preservam linhas e texto vetoriais.
Todas as figuras podem ser reconstruídas com:

    python scripts/regenerate_benchmark_figures.py --results-root results/search_space_v2

O regenerador usa somente resultados salvos e a fonte oficial dos dados
experimentais; não chama nenhum algoritmo. Os hashes SHA-256 dos CSVs dos
benchmarks foram verificados antes e depois da regeneração e permaneceram
idênticos.

## 12.2. Visualização do estudo de pesos

`results/weighted_reflection/` contém `tradeoff_JT_JR.png`, as três figuras
weight × erro com mediana+IQR, 16 best-fits padronizados (quatro algoritmos ×
quatro pesos) e quatro comparações visuais do efeito do peso. O relatório e
`best_solutions.csv` usam as métricas sem peso para interpretar o trade-off;
`J_weighted` não é comparado diretamente entre pesos como métrica científica.

## 12.3. Visualização combinada T/R da configuração final

`analysis.plotting.plot_combined_tr_fit` produz um único eixo com os dez pontos
experimentais de T/R e as duas curvas teóricas calculadas pelo mesmo vetor
físico. Para visualização, usa exclusivamente o grid nominal de 601 valores
`0:1:600` nm; `delta_d3_nm` é aplicado uma única vez, dentro do simulador.
Não há incertezas experimentais armazenadas, portanto nenhuma barra de erro é
inventada. A API suporta incertezas opcionais para uso futuro.

O preview de infraestrutura usa um vetor físico válido de teste, não uma nova
solução otimizada, e está em `results/preview_combined_tr/` nos formatos PNG e
PDF. Nenhum algoritmo ou benchmark foi executado para criá-lo.

Validação direcionada do checkpoint: 30 testes de plotting, simulador e
objetivo passaram. A suíte completa com testes smoke dos otimizadores não foi
reexecutada, em respeito à instrução de não rodar Random Search, DE, GA ou PSO.

## 12.4. Benchmark final do modelo de 6 parâmetros

O benchmark final autorizado foi concluído em `results/final_6parameter_model/`.
Random Search, Differential Evolution, Genetic Algorithm e Particle Swarm
Optimization foram executados com seeds 1–5 e budget exato de 50.000 avaliações
físicas por seed: 20 runs e 1.000.000 de avaliações no total. O preflight
direcionado passou em 141 testes, incluindo constraints, parametrização,
objetivo, simulador, plotting e smoke tests dos quatro algoritmos.

A melhor solução global veio da Differential Evolution, seed 3:

    J   = 0.4933365610782263
    J_T = 0.1666529398522359
    J_R = 0.3266836212259904
    p   = [9.431688774846851, -19.999999999999904,
           1.5000000000000013, 0.8195054138470563,
           2.1957897720412665, 1.3242101261547625]

Os 20 resultados foram reavaliados independentemente; todos conservaram
`J = J_T + J_R`, respeitaram os bounds e consumiram exatamente o budget salvo.
Cada algoritmo possui histórico bruto, agregado Q1/mediana/Q3 por avaliação,
best-fit e gráfico combinado T/R denso em PNG/PDF. As tabelas comparativas,
variabilidade dos parâmetros, validação e melhor global estão em
`results/final_6parameter_model/comparisons/`; o relatório principal é
`results/final_6parameter_model/final_report.md`.

Comportamentos observados: DE foi praticamente idêntico entre as cinco seeds;
DE e três seeds de PSO chegaram à mesma bacia numérica; a melhor solução usa
os limites inferiores de `delta_d3_nm` e `n3_w`; o GA apresentou uma seed
substancialmente pior. Nenhum resultado foi repetido ou ajustado por isso.
Resultados históricos fora da nova raiz não foram sobrescritos.

## 12.5. Correção dos bounds ópticos da camada ativa

Em 10 de setembro de 2026, os quatro bounds ópticos foram corrigidos para
`n3_w ∈ [0.1,10.0]`, `k3_w ∈ [0.0,10.0]`,
`n3_2w ∈ [0.1,10.0]` e `k3_2w ∈ [0.0,10.0]`. Constraints,
parametrização normalizada, testes e o gerador de vetores do benchmark de
custo foram atualizados sem alterar simulador, objetivo ou algoritmos.

Validação direcionada: 54 testes de constraints, parametrização e objetivo
passaram. Nenhum otimizador ou benchmark científico foi executado. Os
resultados existentes foram produzidos com os limites anteriores e permanecem
preservados como históricos.

## 12.6. Benchmark com bounds ópticos corrigidos

Após autorização explícita, foi executado o benchmark completo em
`results/benchmark_bounds_0p1_10_run01/`, com Random Search, Differential
Evolution, Genetic Algorithm e Particle Swarm Optimization, seeds 1–5 e
50.000 avaliações físicas por seed. São 20 runs e 1.000.000 avaliações no
total; os resultados anteriores não foram sobrescritos.

| Algoritmo | Melhor J | Mediana J | Pior J | Melhor seed |
|---|---:|---:|---:|---:|
| Random Search | 1.0854690966837481 | 1.2333787914047556 | 2.3087509767536254 | 4 |
| Differential Evolution | 0.4125867577229127 | 0.4197060799904004 | 0.4197060799904005 | 1 |
| Genetic Algorithm | 0.4523284944037635 | 0.4834647674176606 | 0.5107421112407384 | 3 |
| Particle Swarm Optimization | 0.4197060799905111 | 0.4197060799912715 | 0.4197060847612271 | 4 |

O melhor vetor global foi o DE, seed 1:

    p = [9.117483500679445, -19.99999999999996,
         0.1000000000000011, 2.084349321411794,
         1.837919368782185, 0.2391579663878279]

Para ele, `J_T = 0.2530784417068134` e
`J_R = 0.1595083160160993`. A regeneração padronizada produziu 25 artefatos
PNG/PDF/CSV em `comparisons/` e confirmou que os CSVs de origem permaneceram
inalterados por hash SHA-256. Em complemento, foram gerados e inspecionados os
gráficos combinados T/R densos de cada algoritmo e do melhor global, todos em
PNG e PDF, sem reexecutar os otimizadores.

## 12.7. Sensibilidade 1D da solução de referência PSO seed 4

Foi implementada e executada a análise one-at-a-time em
`results/benchmark_bounds_0p1_10_run01/sensitivity/`, usando exatamente o
vetor PSO seed 4 solicitado. A reavaliação com `delta_d3_nm = -20.0` produziu
`J = 0.41970607999048304`, `J_T = 0.06542398510382935` e
`J_R = 0.3542820948866537`. Esse vetor é tratado como referência da análise;
a melhor solução global do benchmark corrente continua sendo DE seed 1.

Foram realizadas 1.212 avaliações físicas: seis parâmetros, duas escalas e
101 pontos por escala. Nenhum otimizador foi executado e as outras cinco
coordenadas permaneceram fixas em cada sweep. Foram salvos seis CSVs com as
duas escalas, resumo de métricas, relatório e figuras local/global em PNG/PDF.

Pelas larguras normalizadas do vale local a 1%, com amplitude global de J como
desempate, `log10_chi` e `n3_w` foram classificados como mais sensíveis;
`k3_w` e `k3_2w`, intermediários; `delta_d3_nm` e `n3_2w`, menos sensíveis.
Não houve indício de múltiplos mínimos resolvidos pela grade global de 101
pontos. `delta_d3_nm` permaneceu no limite inferior, sem extrapolação abaixo
de -20 nm. Validação direcionada: 44 testes passaram.

## 12.8. Benchmark com `delta_d3_nm` em [-50,50] nm

Por autorização explícita, o bound de `delta_d3_nm` foi ampliado para
`[-50,50]` nm, sem alterar qualquer outra constraint, a física, o objetivo ou
os hiperparâmetros. O benchmark completo foi executado em
`results/benchmark_delta_d3_m50_p50_run01/`: quatro algoritmos, seeds 1–5 e
50.000 avaliações físicas por seed, totalizando 20 runs e 1.000.000 de
avaliações.

| Algoritmo | Melhor J | Mediana J | Pior J | Melhor seed |
|---|---:|---:|---:|---:|
| Random Search | 0.9648379040865533 | 1.464010869057766 | 2.187652558477957 | 2 |
| Differential Evolution | 0.3223303953492892 | 0.3223303953492894 | 0.3223303953492895 | 4 |
| Genetic Algorithm | 0.3868807865990599 | 0.3998652679722692 | 0.7501826606349705 | 3 |
| Particle Swarm Optimization | 0.3223303953508441 | 0.3223304999765833 | 0.3223308880820240 | 5 |

A melhor solução global foi DE, seed 4, com `J_T = 0.09661596943066969`,
`J_R = 0.2257144259186195` e
`p = [9.497146298611646, -45.295433031560876, 0.7094312273848625,
1.7489327919955444, 3.221630915589135, 0.37472749107016146]`. O novo melhor
J é 21,8757% menor que no benchmark anterior com `delta_d3_nm ∈ [-20,20]`.
A solução migrou da antiga fronteira para o interior do novo espaço.

Os 20 vetores passaram na reavaliação independente, nos bounds e na contagem
exata do budget. A suíte completa passou com 164 testes. A regeneração criou
35 artefatos derivados e manteve os hashes dos CSVs de origem inalterados.
Há gráficos combinados T/R por algoritmo e para o melhor global em PNG/PDF.

## 12.9. Sensibilidade 1D do melhor global com bound ampliado

A análise one-at-a-time da melhor solução DE seed 4 foi executada em
`results/benchmark_delta_d3_m50_p50_run01/sensitivity/`, com as mesmas grades
da D-029 e 1.212 avaliações físicas. `delta_d3_nm = -45.295433031560876` está
no interior do intervalo; o mínimo de sua grade global ocorreu em -45 nm.

Pela largura normalizada do vale local a 1%, `log10_chi` e `n3_w` foram mais
sensíveis; `k3_w` e `k3_2w`, intermediários; `delta_d3_nm` e `n3_2w`, menos
sensíveis. A grade resolveu também um mínimo de extremidade em +50 nm no eixo
de `delta_d3_nm`; é um indício 1D dependente da resolução, não uma solução
reotimizada. A análise não estabelece correlações nem identificabilidade
formal.

## 13. Decisões que NÃO devem ser alteradas sem discussão

### Do not change without discussion

- Python é a implementação principal; MATLAB/Octave legado é a referência
  física.
- Não alterar silenciosamente o simulador validado, equações, unidades ou
  convenções.
- J = J_T + J_R, sem penalidade de pico na análise principal.
- Comparar algoritmos por avaliações físicas, não por iterações.
- Todos usam os mesmos dados, bounds, constraints, espaço z e transformação
  z → p.
- Sempre salvar J, J_T, J_R, p, curvas e contagem de avaliações.
- Não ajustar um algoritmo com vantagem de informação não declarada.
- Não concluir superioridade estatística com apenas cinco seeds.

## 14. Próximos passos

1. Preservar explicitamente a identificação do espaço de busca em todos os
   benchmarks futuros.
2. Não promover W2 ou qualquer peso complementar a objetivo definitivo sem
   discussão científica e experimento confirmatório.
3. Implementar CMA-ES sob as mesmas regras, somente após autorização
   explícita.
4. Executar experimento piloto comparativo, decidir budget final e executar
   30 ou 50 seeds.

## 15. Ponto exato de retomada

O checkpoint atual contém a configuração final de seis variáveis, óxido fixo,
bounds ópticos `[0.1,10]`/`[0,10]` e `delta_d3_nm ∈ [-50,50]`. O benchmark
corrente está em `results/benchmark_delta_d3_m50_p50_run01/`; os benchmarks
anteriores permanecem preservados como históricos.

A melhor solução corrente é DE seed 4, com `J = 0.3223303953492892` e
`delta_d3_nm = -45.295433031560876`, no interior do novo bound. Os gráficos
combinados T/R estão em cada pasta de algoritmo como
`best_fit_combined_tr.png/.pdf`, e o melhor global está em
`comparisons/global_best_combined_tr.png/.pdf`. O relatório principal está em
`benchmark_report.md`; a sensibilidade global/local do melhor vetor está em
`sensitivity/`.
