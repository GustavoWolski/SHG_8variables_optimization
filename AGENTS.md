# AGENTS.md — Projeto 3

## Objetivo do projeto

Este projeto implementa em Python um modelo originalmente escrito em MATLAB/Octave para identificação inversa de parâmetros ópticos.

O objetivo é encontrar 8 parâmetros físicos que minimizem simultaneamente o erro entre transmissão e reflexão teóricas e experimentais.

Antes de modificar qualquer formulação física, leia:

- `docs/metodologia.md`
- `docs/equacoes.md`
- arquivos em `legacy_matlab/`

Os arquivos MATLAB são a referência da implementação física original.

---

## Regra principal

A primeira versão Python deve reproduzir numericamente o comportamento do MATLAB antes da implementação dos algoritmos de otimização.

Não alterar, simplificar ou "melhorar" a física sem documentar e justificar explicitamente a mudança.

---

## Vetor de parâmetros

O vetor de parâmetros é:

p = [
    log10_chi,
    d2_nm,
    n2_w,
    n2_2w,
    re_n3_w,
    im_n3_w,
    re_n3_2w,
    im_n3_2w
]

Correspondência com MATLAB:

- p[0] = log10(chi)
- p[1] = d2 em nm
- p[2] = n21w
- p[3] = n22w
- p[4] = real(n31w)
- p[5] = imag(n31w)
- p[6] = real(n32w)
- p[7] = imag(n32w)

A transformação é:

chi = 10 ** log10_chi

---

## Limites físicos

log10(chi):
- intervalo inicial: [-10, 10]

espessura do óxido:
- 0 <= d2_nm <= 20

partes reais dos índices:
- 1.5 <= n <= 6

partes imaginárias:
- 0 <= k <= 4

---

## Restrição de dispersão normal

Obrigatoriamente:

n(omega) < n(2omega)

Portanto:

n2_w < n2_2w

e:

re_n3_w < re_n3_2w

Nenhuma solução que viole essas condições deve ser considerada fisicamente válida.

Preferir uma implementação de constraints que evite avaliações inválidas ou faça reparo de forma consistente entre todos os algoritmos.

---

## Dados experimentais atuais

lambda = 1560 nm

Dados:

d_nm, T_exp, R_exp

65, 2192.89, 621.17
80, 2133.53, 876.81
100, 2522.53, 1137.68
150, 3857.56, 731.88
190, 3649.85, 1021.73
250, 1988.13, 920.289
300, 359.05, 1521.73
400, 59.64, 1072.46
500, 37.68, 1057.97
600, 16.17, 1028.98

---

## Função objetivo

Não utilizar inicialmente a penalização especial do pico presente no MATLAB original.

Usar:

J = J_T + J_R

com:

J_T = sum(
    ((T_exp - T_theoretical) / max(T_exp)) ** 2
)

J_R = sum(
    ((R_exp - R_theoretical) / max(R_exp)) ** 2
)

Salvar separadamente:

- J
- J_T
- J_R
- vetor p
- T teórico
- R teórico

---

## Funções físicas

A função de reflexão original é:

rij = (n1 - n2 - Z0*sigS) / (n1 + n2 + Z0*sigS)

com:

Z0 = 1 / (eps0*c)

A função de transmissão original é:

tij = 2*n1 / (n1 + n2 + Z0*sigS)

O índice do vidro é:

l = lambda / 1e-6

nglass = 1.5130 - 0.003169*l**2 + 0.003962/l**2

Preservar exatamente essas convenções na primeira implementação Python.

---

## Estrutura desejada

Criar:

src/
    physics/
        fresnel.py
        glass.py
        transfer_matrix.py
        simulator.py

    optimization/
        objective.py
        constraints.py
        random_search.py
        differential_evolution.py
        genetic_algorithm.py
        pso.py
        cmaes.py

    experiments/
        runner.py
        config.py

    analysis/
        plots.py
        statistics.py
        parameters.py

tests/

results/

---

## Ordem obrigatória de implementação

1. Portar `rij.m` para Python.
2. Portar `tij.m`.
3. Portar `nlimeglass.m`.
4. Portar o simulador MATLAB principal.
5. Criar testes unitários das funções auxiliares.
6. Comparar Python e MATLAB para parâmetros conhecidos.
7. Somente após equivalência numérica, implementar a função objetivo.
8. Implementar Random Search.
9. Implementar Differential Evolution.
10. Depois GA, PSO e CMA-ES.
11. Criar runner comum para múltiplas seeds.
12. Registrar convergência e resultados.

---

## Validação MATLAB x Python

Antes da otimização, executar o mesmo vetor p em MATLAB e Python.

Comparar:

- T em todos os pontos;
- R em todos os pontos;
- J_T;
- J_R;
- J total.

Criar testes com tolerância numérica.

Não considerar o port concluído enquanto Python e MATLAB não forem equivalentes dentro de uma tolerância apropriada.

---

## Regras de experimentação

Todos os algoritmos devem utilizar:

- mesma função objetivo;
- mesmos limites;
- mesmas constraints;
- mesmo conjunto experimental;
- mesmo orçamento máximo de avaliações da função.

Não comparar algoritmos por número de iterações.

Comparar por número de avaliações da função objetivo.

Cada algoritmo deverá ser executado posteriormente com múltiplas seeds.

Salvar em cada execução:

- algoritmo
- seed
- número de avaliações
- tempo
- J
- J_T
- J_R
- parâmetros p
- curva de convergência
- validade física

---

## Qualidade de código

Usar Python moderno.

Preferências:

- NumPy
- SciPy
- pandas
- matplotlib
- dataclasses quando útil
- type hints
- pytest

Evitar notebooks como implementação principal.

Notebooks podem ser usados para exploração e visualização, mas a lógica deve ficar em módulos Python testáveis.

---

## Não fazer ainda

Não implementar inicialmente:

- redes neurais
- surrogate models
- Bayesian Optimization
- NSGA-II
- reinforcement learning
- PINNs

Esses métodos são extensões futuras.

O foco inicial é validar a física e estabelecer o benchmark dos algoritmos clássicos.