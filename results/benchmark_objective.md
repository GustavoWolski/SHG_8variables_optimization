# Benchmark serial da função objetivo

Este é o baseline serial da avaliação completa `p → validação → simulador → T/R → J_T/J_R → J`. Não usa paralelização, multiprocessing, GPU, cache ou vetorização adicional.

## Ambiente

- python: 3.12.13 (main, Aug  7 2026, 02:26:41) [MSC v.1944 64 bit (AMD64)]
- python_implementation: CPython
- operating_system: Windows-11-10.0.26200-SP0
- processor: AMD64 Family 26 Model 68 Stepping 0, AuthenticAMD
- cpu_count_logical: 8
- parallelization: none (serial baseline)
- seed dos vetores: 20260824
- warm-up não medido: 50 avaliações físicas válidas
- geração: amostragem uniforme dos bounds e geração condicional dos pares dispersivos estritos

## Medições primárias

| Avaliações | Tempo total (s) | Média (s) | Mediana (s) | Desvio padrão (s) | Mínimo (s) | Máximo (s) | Avaliações/s |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 0.042752 | 0.000427270 | 0.000414900 | 0.000058522 | 0.000412500 | 0.000894300 | 2339.094 |
| 1000 | 0.421465 | 0.000421253 | 0.000414800 | 0.000037191 | 0.000410800 | 0.001010400 | 2372.674 |
| 10000 | 4.192534 | 0.000419043 | 0.000415600 | 0.000025923 | 0.000411100 | 0.001051900 | 2385.192 |

## Projeções seriais

As projeções usam a média por avaliação da maior etapa executada (10000 avaliações: 0.000419043 s/avaliação). Elas excluem startup, I/O e overhead de algoritmos.

| Budget por execução | Uma execução serial | 5 algoritmos × 30 seeds | 5 algoritmos × 50 seeds |
|---:|---:|---:|---:|
| 10,000 | 4.190429 s / 0.069840 min / 0.001164 h | 628.564275 s / 10.476071 min / 0.174601 h | 1047.607125 s / 17.460119 min / 0.291002 h |
| 25,000 | 10.476071 s / 0.174601 min / 0.002910 h | 1571.410688 s / 26.190178 min / 0.436503 h | 2619.017813 s / 43.650297 min / 0.727505 h |
| 50,000 | 20.952143 s / 0.349202 min / 0.005820 h | 3142.821375 s / 52.380356 min / 0.873006 h | 5238.035625 s / 87.300594 min / 1.455010 h |
| 100,000 | 41.904285 s / 0.698405 min / 0.011640 h | 6285.642750 s / 104.760713 min / 1.746012 h | 10476.071250 s / 174.601188 min / 2.910020 h |

## Definição de avaliação

Cada medição usa `ObjectiveEvaluator`; seu `n_evaluations` foi verificado exatamente contra o tamanho de cada lote. Rejeições não ocorrem: todos os vetores já satisfazem as constraints antes do benchmark.

Este relatório não seleciona o budget definitivo; ele apenas fornece o custo serial de referência.
