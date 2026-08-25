# Random Search — baseline preliminar

## Configuração

- algoritmo: `Random Search`
- seeds: `1, 2, 3, 4, 5`
- budget por seed: `50000` avaliações físicas
- total de avaliações físicas: `250000`
- espaço: `z ∈ [0,1]^8`, mapeado pela transformação compartilhada `z → p`

## Estatísticas dos resultados finais

| Métrica | Melhor | Pior | Média | Mediana | Desvio padrão amostral | IQR |
|---|---:|---:|---:|---:|---:|---:|
| best_J | 0.584185249527 | 0.886566318043 | 0.724217730746 | 0.685256072486 | 0.115596797238 | 0.107960830998 |
| best_J_T | 0.165233663715 | 0.359260287806 | 0.301450049463 | 0.327706861649 | 0.0774374794693 | 0.00895865332766 |
| best_J_R | 0.319299803532 | 0.558859456394 | 0.422767681284 | 0.418951585812 | 0.0920818891621 | 0.0923061965226 |

## Melhor execução global

- seed: `2`
- J: `0.5841852495274906`
- J_T: `0.1652336637150435`
- J_R: `0.4189515858124471`
- vetor p:
- `log10_chi`: 9.558241528334502
- `d2_nm`: 14.63864519772379
- `n2_w`: 1.924597171604477
- `n2_2w`: 3.073969524667855
- `re_n3_w`: 1.500275698032278
- `im_n3_w`: 1.601983762125853
- `re_n3_2w`: 2.764771061032301
- `im_n3_2w`: 0.4322388347104993

## Tempo

- soma dos runtimes das cinco buscas: `106.851796 s` (`1.780863 min`)

## Observações descritivas

- As cinco seeds fornecem uma primeira medida de variabilidade de J e dos parâmetros; a tabela `best_parameters.csv` preserva os oito vetores para inspeção inicial.
- As curvas usam valores best-so-far brutos, sem suavização.
- Este experimento é apenas um baseline preliminar; ele não classifica a qualidade do Random Search e não constitui análise de identificabilidade.
