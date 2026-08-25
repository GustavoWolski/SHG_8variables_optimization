# Baseline — Genetic Algorithm

## Configuração

- Seeds: 1, 2, 3, 4, 5
- Budget por seed: 50000 avaliações físicas
- Total de avaliações: 250000
- population_size: 100
- selection: tournament (tamanho 3)
- crossover: simulated_binary; probabilidade 0.9; eta 15.0
- mutation: polynomial; probabilidade 0.125; eta 20.0
- elitism: 1
- initialization: uniform em z
- boundary handling: clip em z

Elites carregam o resultado físico já obtido e não são reavaliados. A última geração pode ser parcial para encerrar exatamente no budget.

## Estatísticas finais

| Métrica | Melhor | Pior | Média | Mediana | Desvio padrão | IQR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| best_J | 0.3838408040675216 | 0.4180227137750425 | 0.3981939423880584 | 0.3887575468305548 | 0.0167742887340202 | 0.02930613979665059 |
| best_J_T | 0.05681867610718783 | 0.2279764682392424 | 0.1230783041029087 | 0.05873530857614295 | 0.08994727883157488 | 0.1580993867539732 |
| best_J_R | 0.1868509252926696 | 0.3318767064115562 | 0.2751156382851497 | 0.3267859451591184 | 0.0734355531927105 | 0.1239796413582631 |

## Execuções individuais

| Seed | J | J_T | J_R | Tempo (s) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0.3887575468305548 | 0.0568808404189986 | 0.3318767064115562 | 23.543836 |
| 2 | 0.3838408040675216 | 0.05681867610718783 | 0.3270221279603338 | 23.250749 |
| 3 | 0.4148273935319119 | 0.2279764682392424 | 0.1868509252926696 | 23.058313 |
| 4 | 0.4180227137750425 | 0.2149802271729718 | 0.2030424866020706 | 23.099860 |
| 5 | 0.3855212537352614 | 0.05873530857614295 | 0.3267859451591184 | 23.075194 |

## Melhor execução global

- Seed: 2
- J: 0.3838408040675216
- J_T: 0.05681867610718783
- J_R: 0.3270221279603338
- Runtime: 23.250749 s
- Runtime total: 116.029422 s

| Parâmetro | Valor |
| --- | ---: |
| log10_chi | 9.52877737115147 |
| d2_nm | 19.99999638111071 |
| n2_w | 2.529927342995089 |
| n2_2w | 2.529933579076557 |
| re_n3_w | 1.500000030869841 |
| im_n3_w | 1.027925056760741 |
| re_n3_2w | 3.086736962547977 |
| im_n3_2w | 0.8685870203369332 |

## Comparação descritiva

- Random Search, DE e GA receberam 50.000 avaliações físicas por seed e as mesmas cinco seeds.
- As curvas mostram medianas e IQR brutos por avaliação física, sem suavização.
- O gráfico de três algoritmos foi gerado a partir dos históricos existentes.
- Cinco seeds não permitem inferência estatística ou afirmação de superioridade entre algoritmos.
