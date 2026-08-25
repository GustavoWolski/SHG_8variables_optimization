# AGENTS.md — regras essenciais

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

Não implementar nesta fase GA, PSO, DE, CMA-ES, Random Search, busca local,
surrogates, redes neurais, Bayesian Optimization, NSGA-II, RL ou PINNs.

## Parâmetros e unidades

`p = [log10_chi, d2_nm, n2_w, n2_2w, re_n3_w, im_n3_w, re_n3_2w, im_n3_2w]`.

- `chi = 10 ** log10_chi`;
- `d2_nm` está em nm; internamente, o MATLAB converte espessuras para m;
- `lambda = 1560 nm` no experimento e `1560e-9 m` no MATLAB;
- índices de camada 3 são complexos: `re + 1j * im`;
- preservar `eps0 = 8.8541878176e-12 F/m` e `c = 3e8 m/s`.

## Limites e validade física futura

- `-10 <= log10_chi <= 10`;
- `0 <= d2_nm <= 20`;
- `1.5 <=` partes reais dos índices `<= 6`;
- `0 <=` partes imaginárias `<= 4`;
- dispersão normal estrita: `n2_w < n2_2w` e
  `re_n3_w < re_n3_2w`.

## Objetivo e experimentos futuros

A formulação do projeto será `J = J_T + J_R`, com erros normalizados pelos
máximos experimentais de cada resposta, sem a penalidade de pico do MATLAB.
Toda avaliação deverá recuperar `J`, `J_T`, `J_R`, `p`, `T` e `R`.

Todos os algoritmos futuros usarão os mesmos dados, limites, constraints,
função objetivo e orçamento em número de avaliações — nunca apenas em número
de iterações. Registre seed, tempo, avaliações, curva de convergência e
validade física.

## Critério de avanço

Antes de otimizar, comparar o mesmo vetor de parâmetros em MATLAB e Python
para todos os pontos de `T` e `R`, além de `J_T`, `J_R` e `J`, com tolerância
numérica justificada. A lógica de produção deve ficar em módulos Python com
type hints e testes pytest; notebooks são apenas exploratórios.
