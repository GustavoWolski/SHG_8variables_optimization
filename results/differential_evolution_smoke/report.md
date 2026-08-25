# Baseline — Differential Evolution

## Configuração

- Seeds: 1
- Budget por seed: 1000 avaliações físicas
- Total de avaliações: 1000
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
| J | 0.8054211344755735 | 0.8054211344755735 | 0.8054211344755735 | 0.8054211344755735 | 0 | 0 |
| J_T | 0.2638092248914278 | 0.2638092248914278 | 0.2638092248914278 | 0.2638092248914278 | 0 | 0 |
| J_R | 0.5416119095841456 | 0.5416119095841456 | 0.5416119095841456 | 0.5416119095841456 | 0 | 0 |

## Melhor execução global

- Seed: 1
- J: 0.8054211344755735
- J_T: 0.2638092248914278
- J_R: 0.5416119095841456
- Tempo desta execução: 0.437842 s
- Tempo total das cinco execuções: 0.439601 s

| Parâmetro | Valor |
| --- | ---: |
| log10_chi | 9.508253045857764 |
| d2_nm | 6.542167036816899 |
| n2_w | 1.538608841672515 |
| n2_2w | 3.014492175387963 |
| re_n3_w | 1.652515523960222 |
| im_n3_w | 1.058684867827349 |
| re_n3_2w | 2.043408031196968 |
| im_n3_2w | 1.246927231230729 |

## Observações descritivas

- O gráfico de mediana/IQR foi criado a partir do histórico do Random Search.
- Referência usada para comparação: C:\Users\Gustavo\OneDrive\Documentos\Doutorado\SHG_8variables_optimization\results\random_search_baseline\runs.csv.
- As curvas registram o melhor J observado após cada avaliação física; não houve suavização.
- Este baseline é descritivo. Ele não estabelece ainda uma conclusão de superioridade entre algoritmos.
