# Baseline — Differential Evolution

## Configuração

- Seeds: 1, 2, 3, 4, 5
- Budget por seed: 50000 avaliações físicas
- Total de avaliações: 250000
- SciPy: 1.18.1
- Python: 3.12.13
- Sistema: Windows-11-10.0.26200-SP0
- Estratégia: best1bin
- População nominal: 15 × 8 = 120
- Mutation: (0.5, 1.0)
- Recombination: 0.7
- Inicialização: latinhypercube
- Atualização: deferred
- tol/atol: 0.0/0.0
- polish: False

O orçamento é imposto pelo contador de avaliações físicas e por maxfun no solver do SciPy. Não há polish nem avaliação final adicional.

## Estatísticas entre seeds

| Métrica | Melhor | Pior | Média | Mediana | Desvio padrão | IQR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| J | 0.3818429946001101 | 0.3818430638493236 | 0.381843025488795 | 0.3818430194775517 | 2.61996176167097e-08 | 2.378390706603284e-08 |
| J_T | 0.05699288623154902 | 0.05701102327444171 | 0.05700321763028467 | 0.05700346496957198 | 6.637527757313125e-06 | 3.436409036265686e-06 |
| J_R | 0.3248320133760065 | 0.3248501266349921 | 0.3248398078585103 | 0.3248395988797517 | 6.632220066244812e-06 | 3.461286477823844e-06 |

## Melhor execução global

- Seed: 3
- J: 0.3818429946001101
- J_T: 0.05700607504244844
- J_R: 0.3248369195576617
- Tempo desta execução: 23.372310 s
- Tempo total das cinco execuções: 113.437136 s

| Parâmetro | Valor |
| --- | ---: |
| log10_chi | 9.540644916150043 |
| d2_nm | 19.99999983369976 |
| n2_w | 2.567103143029925 |
| n2_2w | 2.567103171440757 |
| re_n3_w | 1.500000018020065 |
| im_n3_w | 1.156280448848984 |
| re_n3_2w | 3.098351557311543 |
| im_n3_2w | 0.7560948470435371 |

## Observações descritivas

- O gráfico de mediana/IQR foi criado a partir do histórico do Random Search.
- Referência usada para comparação: C:\Users\Gustavo\OneDrive\Documentos\Doutorado\SHG_8variables_optimization\results\random_search_baseline\runs.csv.
- As curvas registram o melhor J observado após cada avaliação física; não houve suavização.
- Este baseline é descritivo. Ele não estabelece ainda uma conclusão de superioridade entre algoritmos.
