# Project State

## 1. Objetivo científico

Identificar os oito parâmetros físicos que reproduzem simultaneamente as
curvas experimentais de transmissão e reflexão:

    p* = argmin J(p),   J = J_T + J_R

A função principal não usa a penalização de pico do MATLAB legado.

## 2. Formulação atual

O modelo físico é uma pilha de quatro meios: ar | óxido | camada ativa |
vidro, sob fundamental de 1560 nm. Python é a implementação principal; o
MATLAB/Octave preservado é a referência física e numérica.

## 3. Vetor de parâmetros

    p = [
        log10_chi, d2_nm, n2_w, n2_2w,
        re_n3_w, im_n3_w, re_n3_2w, im_n3_2w,
    ]

chi = 10 ** log10_chi, d2_nm está em nm, e os índices da camada 3 são
re_n3 + 1j * im_n3.

## 4. Bounds e restrições físicas

    -10 <= log10_chi <= 10
    0 <= d2_nm <= 20
    1.0 <= n2_w, n2_2w <= 6
    1.5 <= re_n3_w, re_n3_2w <= 6
    0 <= im_n3_w, im_n3_2w <= 4

Dispersão normal estrita:

    re_n3_w < re_n3_2w

Os índices reais do óxido são independentes; inclusive `n2_w >= n2_2w` é
permitido. Este é o **Search-space version 2**. Os baselines históricos
abaixo pertencem ao **Search-space version 1**, que exigia
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

## 7. Validação física MATLAB/Octave × Python

    max_rel_error_T = 1.6717503026056207e-14
    max_rel_error_R = 3.644239657078057e-15
    max_intermediate_frobenius_error = 1.0878030299442186e-15

    MATLAB/Octave × Python: PASS

As fixtures de regressão estão em tests/reference/. Mudanças futuras na
física devem continuar passando essa regressão.

## 8. Parametrização normalizada

Todos os algoritmos trabalham no mesmo cubo z ∈ [0,1]^8 e usam a transformação
z → p de src/optimization/parameterization.py. Para o óxido,
`n2_w = 1 + 5*z2` e `n2_2w = 1 + 5*z3`: são variáveis uniformes e
independentes em `[1,6]`. Somente o par real da camada 3 é amostrado
uniformemente no triângulo físico permitido. DELTA_N =
5.684341886080802e-14 mantém a desigualdade estrita da camada 3 representável
em float64. Detalhes da derivação estão em docs/decisions.md.

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

## 12. Estado dos testes

    pytest: 159 passed

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

O checkpoint encerra após a atualização das constraints e parametrização para
Search-space version 2, validação pytest/MATLAB × Python, reexecução de RS,
DE e GA, implementação/testes/benchmark do PSO (cinco seeds, 50.000 avaliações
por seed), e screening complementar de pesos de reflexão (80 buscas, 4 milhões
de avaliações) com figuras e relatório. Não iniciar CMA-ES, promover pesos a
objetivo definitivo, nem iniciar experimentos comparativos finais sem
autorização explícita e sem a decisão do budget final.
