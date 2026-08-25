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
    1.5 <= n2_w, n2_2w, re_n3_w, re_n3_2w <= 6
    0 <= im_n3_w, im_n3_2w <= 4

Dispersão normal estrita:

    n2_w < n2_2w
    re_n3_w < re_n3_2w

## 5. Função objetivo

J_T e J_R são as somas dos quadrados dos resíduos de transmissão e reflexão,
normalizados separadamente por max(T_exp) e max(R_exp). J = J_T + J_R. A
penalização de pico do ajuste MATLAB legado não pertence à análise principal.

## 6. Arquitetura implementada

- src/physics/: fresnel.py, glass.py, transfer_matrix.py e simulator.py.
- src/optimization/: constraints.py, objective.py, parameterization.py,
  random_search.py e differential_evolution.py.
- src/experiments/data.py: dados experimentais oficiais.
- scripts/: validação MATLAB/Python, benchmark e runners dos baselines.
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
z → p de src/optimization/parameterization.py. Os pares dispersivos são
amostrados uniformemente no triângulo físico permitido. DELTA_N =
5.684341886080802e-14 mantém a desigualdade estrita representável em float64.
Detalhes da derivação estão em docs/decisions.md.

## 9. Benchmark computacional

    10000 avaliações físicas: 4.192534 s
    média: 0.000419043 s/avaliação
    throughput: aproximadamente 2385 avaliações/s

Ambiente medido: Python 3.12.13, Windows 11, AMD64, 8 CPUs lógicas, baseline
serial. O budget científico final ainda não foi decidido. Os baselines atuais
usaram 50000 avaliações por seed.

## 10. Algoritmos implementados

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

## 11. Resultados atuais

Sob o mesmo orçamento, a mediana de Random Search foi 0.6852560724860886 e a
de DE foi 0.3818430194775517. Descritivamente, DE terminou com menor erro e
menor dispersão nas cinco seeds. Não houve inferência estatística formal e
cinco seeds não sustentam alegação de superioridade estatística.

Ponto de atenção: a melhor solução DE está próxima de d2_nm ≈ 20,
re_n3_w ≈ 1.5 e n2_w ≈ n2_2w. Isso não deve ser interpretado ainda como
resultado físico definitivo: investigar ótimo em fronteira, influência dos
bounds, sensibilidade, identificabilidade e eventual discussão dos limites
com o orientador.

## 12. Estado dos testes

    pytest: 97 passed

A suíte cobre Fresnel, vidro, simulador, regressão MATLAB/Octave, constraints,
objective, parameterization, Random Search e Differential Evolution.

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

1. Implementar Genetic Algorithm no mesmo espaço z e com budget físico exato.
2. Implementar PSO e CMA-ES sob as mesmas regras.
3. Executar experimento piloto comparativo, decidir budget final e executar
   30 ou 50 seeds.
4. Só então conduzir análise estatística, estabilidade, identificabilidade,
   sensibilidade e possíveis métodos híbridos.

## 15. Ponto exato de retomada

O checkpoint encerra após DE validado, seus testes e o baseline de cinco
seeds. O próximo trabalho de implementação é Genetic Algorithm; não iniciar
experimentos comparativos finais nem análises científicas antes de todos os
algoritmos planejados e da decisão do budget final.
