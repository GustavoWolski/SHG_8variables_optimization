# AGENTS.md — regras essenciais

## Retomada operacional

Antes de qualquer nova tarefa significativa:

1. leia docs/PROJECT_STATE.md;
2. leia docs/decisions.md;
3. consulte docs/methodology.md quando a decisão for científica.

Após cada novo checkpoint experimental significativo, atualize
docs/PROJECT_STATE.md.

## Fontes de verdade

Antes de modificar a física, leia nesta ordem:

1. `docs/methodology.md`;
2. `docs/equations.md`;
3. todos os arquivos em `legacy_matlab/`.

O MATLAB/Octave é a referência física e numérica. Não alterar, simplificar
ou “melhorar” equações, convenções de sinais, unidades ou normalizações sem
uma decisão documentada e uma validação explícita.

## Regra de implementação

O primeiro port Python deve reproduzir numericamente o MATLAB. A ordem é:

1. `rij.m`;
2. `tij.m`;
3. `nlimeglass.m`;
4. simulador de quatro camadas;
5. testes unitários e comparação MATLAB × Python;
6. função objetivo;
7. somente então, algoritmos de otimização.

Não implementar algoritmos além da etapa explicitamente autorizada. Random
Search, Differential Evolution e Genetic Algorithm já existem; PSO, CMA-ES, busca local,
surrogates, redes neurais, Bayesian Optimization, NSGA-II, RL ou PINNs
dependem de autorização explícita.

## Parâmetros e unidades

`p = [log10_chi, delta_d3_nm, n3_w, k3_w, n3_2w, k3_2w]`.

- `chi = 10 ** log10_chi`;
- `d2_nm = 10.0`, `n2_w = 1.0` e `n2_2w = 1.0` são constantes fora do search space;
- `d3_effective_nm = max(d3_nominal_nm + delta_d3_nm, 0.0)`;
- `lambda = 1560 nm` no experimento e `1560e-9 m` no MATLAB;
- índices de camada 3 são complexos: `n3 + 1j * k3`;
- preservar `eps0 = 8.8541878176e-12 F/m` e `c = 3e8 m/s`.

## Limites e validade física futura

- `-10 <= log10_chi <= 10`;
- `-20 <= delta_d3_nm <= 20`;
- `1.5 <= n3_w, n3_2w <= 6`;
- `0 <= k3_w, k3_2w <= 4`;
- `n3_w` e `n3_2w` são independentes, sem ordenação ou restrição de dispersão.

## Objetivo e experimentos futuros

A formulação do projeto será `J = J_T + J_R`, com erros normalizados pelos
máximos experimentais de cada resposta, sem a penalidade de pico do MATLAB.
Toda avaliação deverá recuperar `J`, `J_T`, `J_R`, `p`, `T` e `R`.

Todos os algoritmos futuros usarão os mesmos dados, limites, constraints,
função objetivo e orçamento em número de avaliações — nunca apenas em número
de iterações. Registre seed, tempo, avaliações, curva de convergência e
validade física.

## Critério de avanço

O MATLAB versionado é anterior à configuração final: usa oito parâmetros e
não contém `p(9)`. Sua regressão permanece histórica e não deve ser apresentada
como validação literal do modelo final. A configuração corrente segue a
orientação final do professor e deve ser validada por testes determinísticos
até que uma referência MATLAB final seja disponibilizada. A lógica de produção
deve ficar em módulos Python com type hints e testes pytest; notebooks são
apenas exploratórios.
