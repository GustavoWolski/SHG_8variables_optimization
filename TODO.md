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
- [ ] Executar `legacy_matlab/export_reference_cases.m` em MATLAB/Octave para gerar referências reais.
- [ ] Versionar as referências confirmadas em `tests/reference/` e criar o teste de regressão MATLAB × Python.
- [x] Portar as matrizes de interface e propagação em `transfer_matrix.py`.
- [x] Portar `shg_4layers` e `shg_mos2_ratios` em `simulator.py`, sem alterações de fórmula.
- [ ] Executar `scripts/validate_matlab_python.py` para comparar `T`, `R` e intermediários entre MATLAB/Octave e Python.
- [ ] Definir e justificar a tolerância numérica de equivalência.

## Formulação inversa

- [ ] Implementar dados experimentais e vetor de parâmetros em `experiments/config.py`.
- [ ] Implementar somente `J = J_T + J_R`, sem penalidade de pico.
- [ ] Implementar e testar limites e dispersão normal em `optimization/constraints.py`.
- [ ] Garantir que cada avaliação retorne `J`, `J_T`, `J_R`, `p`, `T` e `R`.

## Otimização — bloqueada até a equivalência numérica

- [ ] Random Search.
- [ ] Differential Evolution.
- [ ] Genetic Algorithm.
- [ ] Particle Swarm Optimization.
- [ ] CMA-ES.
- [ ] Runner comum com seeds, orçamento por avaliações e convergência.

## Experimentos e análise futuros

- [ ] Medir o custo de uma avaliação e definir orçamento comum.
- [ ] Executar 30 seeds (avaliar 50 quando viável).
- [ ] Salvar resultados reprodutíveis em `results/`.
- [ ] Produzir estatísticas, gráficos e análise de identificabilidade.
- [ ] Definir análise estatística adequada e correção de múltiplas comparações.
- [ ] Avaliar sensibilidade, bootstrap, leave-one-out e métodos híbridos somente após o benchmark principal.
