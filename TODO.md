# TODO — roteiro de implementação

## Etapa atual: preparação concluída

- [x] Inventariar documentação, artigos de referência e MATLAB original.
- [x] Criar esqueleto de pacotes Python e configuração pytest.
- [x] Registrar decisões, dependências e ambiguidades iniciais.

## Port físico e validação (ordem obrigatória)

- [x] Portar fielmente `rij.m` para `src/physics/fresnel.py`.
- [x] Portar fielmente `tij.m` para `src/physics/fresnel.py`.
- [x] Portar fielmente `nlimeglass.m` para `src/physics/glass.py`.
- [x] Criar testes unitários para essas três funções com entradas reais e complexas.
- [x] Executar `legacy_matlab/export_reference_cases.m` em MATLAB/Octave para gerar referências reais.
- [x] Versionar as referências confirmadas em `tests/reference/` e criar o teste de regressão MATLAB × Python.
- [x] Portar as matrizes de interface e propagação em `transfer_matrix.py`.
- [x] Portar `shg_4layers` e `shg_mos2_ratios` em `simulator.py`, sem alterações de fórmula.
- [x] Executar `scripts/validate_matlab_python.py` para comparar `T`, `R` e intermediários entre MATLAB/Octave e Python.
- [x] Confirmar equivalência numérica MATLAB × Python (erros observados de ordem `1e-14` a `1e-15`).

## Formulação inversa

- [x] Centralizar os dados experimentais oficiais em `experiments/data.py`.
- [x] Implementar somente `J = J_T + J_R`, sem penalidade de pico.
- [x] Implementar e testar os limites individuais em `optimization/constraints.py`.
- [x] Garantir que cada avaliação detalhada retorne `J`, `J_T`, `J_R`, `p`, `T` e `R`.
- [x] Implementar a parametrização final independente `z ∈ [0,1]^6 → p`.
- [x] Fixar o óxido em `d2 = 10 nm` e `n2_w = n2_2w = 1` fora do search space.
- [x] Aplicar `d3_effective_nm = max(d3_nominal_nm + delta_d3_nm, 0)`.
- [x] Registrar que o MATLAB versionado é anterior e não contém `p(9)`.

## Otimização — baselines e algoritmos

- [x] Random Search no espaço normalizado, com seed e budget por avaliações físicas.
- [x] Differential Evolution no espaço normalizado, com seed, configuração documentada e budget exato por avaliações físicas.
- [x] Executar e salvar os baselines preliminares de Random Search e DE com 5 seeds e 50.000 avaliações físicas por seed.
- [x] Genetic Algorithm real-coded no espaço normalizado, com budget físico exato e baseline de 5 seeds.
- [ ] Particle Swarm Optimization (próxima implementação).
- [ ] CMA-ES.
- [ ] Runner comum com seeds, orçamento por avaliações e convergência.

## Experimentos e análise futuros

- [x] Medir o custo serial de uma avaliação completa da função objetivo (10.000 em 4,192534 s).
- [ ] Definir orçamento comum de avaliações a partir do baseline e dos custos dos algoritmos.
- [ ] Executar 30 seeds (avaliar 50 quando viável).
- [ ] Executar e salvar o experimento comparativo final em `results/`.
- [ ] Produzir estatísticas, gráficos e análise de identificabilidade.
- [ ] Definir análise estatística adequada e correção de múltiplas comparações.
- [ ] Avaliar sensibilidade, bootstrap, leave-one-out e métodos híbridos somente após o benchmark principal.
