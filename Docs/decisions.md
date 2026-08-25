# Decisões de preparação

Este registro documenta somente decisões de organização tomadas antes do
port. Ele não substitui nem modifica a formulação física.

## D-001 — Hierarquia de fontes

Para qualquer decisão física, a precedência é:

1. `docs/methodology.md`;
2. `docs/equations.md`;
3. `legacy_matlab/`.

Na prática, os arquivos MATLAB resolvem detalhes executáveis que a
documentação marcava como pendentes, por exemplo as expressões completas de
`rij`, `tij` e `nlimeglass`. Quando houver conflito real entre a documentação
e o comportamento MATLAB, o conflito deve ser registrado antes do port e não
resolvido silenciosamente.

## D-002 — Escopo desta etapa

Foram criados os pacotes, a configuração de ambiente, pytest, documentação,
os auxiliares `rij`, `tij` e `nlimeglass`, e o núcleo físico do simulador de
quatro camadas. A função objetivo e os baselines Random Search e Differential
Evolution estão separados da física; GA, PSO e CMA-ES ainda não existem. As constraints oficiais
pertencem exclusivamente a `optimization/constraints.py`; o simulador
permanece sem regras de otimização.

## D-003 — Inventário do modelo MATLAB

### Funções e fluxo

| Componente MATLAB | Papel | Destino Python futuro |
|---|---|---|
| `rij(n1,n2,sigS)` | reflexão de interface com condutividade superficial | `physics.fresnel` |
| `tij(n1,n2,sigS)` | transmissão de interface com condutividade superficial | `physics.fresnel` |
| `nlimeglass(lambda)` | índice do substrato soda-lime | `physics.glass` |
| `shg_4layers(Md3,p,lambda)` | campos, fontes SHG, intensidades e referência MoS2 | `physics.simulator` |
| `shg_mos2_ratios(Md3,p,lambda)` | normaliza intensidades em transmissão e reflexão | `physics.simulator` |
| `fit_error`, `fit_residuals` | objetivo legado ponderado, com pico | referência apenas; objetivo novo será separado |
| `best_chi_for_shape`, `fit_selected_parameters`, `bounded_fit_error` | ajuste local/multistart do legado | fora do escopo atual |

O fluxo físico executável é: construir matrizes na fundamental, obter a
reflexão total e os campos `E+`/`E-` na camada 3, construir fontes `2k` e
`0k`, propagá-las em `2ω`, calcular intensidades de saída e normalizá-las pela
referência de MoS2.

### Constantes, unidades e parâmetros preservados

- `lambda = 1560e-9 m`, `k0 = 2*pi/lambda` e `lambda_SHG = lambda/2`;
- `eps0 = 8.8541878176e-12 F/m`, `c = 3e8 m/s` e `Z0 = 1/(eps0*c)`;
- espessuras de entrada `Md3` e `d2` são dadas em nm e convertidas para m;
  a espessura ativa é `d3 = (Md3 - p(2))*1e-9`;
- `p = [log10(chi), d2_nm, n21w, n22w, Re(n31w), Im(n31w), Re(n32w), Im(n32w)]`;
  `chi2 = 10^p(1)`, `n31w = p(5)+i*p(6)` e `n32w = p(7)+i*p(8)`;
- ar: `n11w = n12w = 1`; vidro: `n41w = nlimeglass(lambda)` e
  `n42w = nlimeglass(lambda/2)`;
- referência MoS2: `dmos2 = 0.65e-9 m` e
  `sigS = -i*(4.97-1)*eps0*w1*dmos2`, com `w1 = 2*pi*c/lambda`.

As matrizes que precisam ser preservadas são interfaces
`M = (1/t)*[[1,r],[r,1]]`, propagações diagonais `P`, transferência total
`T1w = M431w*P31w*M321w*P21w*M211w`, e a matriz de acoplamento de fontes
`MfactEs`. As fontes são `[(E+)²,(E-)²]` e `[E+E-,E-E+]`; as contribuições
`ESHG2k` e `ESHG0k` são somadas coerentemente. As intensidades são módulos
quadrados reais e as saídas são `I4/IMoS24` e `I1/IMoS21`.

## D-004 — Formulação futura do projeto versus ajuste legado

O MATLAB atual usa limites amplos (`log10(chi)` de -12 a 12, `d2` de 1 a
100 nm e índices de 0.1 a 10), pesos `[1,1]` e penalidade de pico de 200. A
metodologia do projeto determina outro domínio físico e `J = J_T + J_R`, sem
penalidade de pico. Essa alteração será implementada somente depois de o
simulador Python reproduzir o simulador MATLAB para vetores conhecidos.

## D-005 — Pacotes e testes

Os pacotes são mantidos exatamente como `physics`, `optimization`,
`experiments` e `analysis` sob `src/`, como solicitado pela metodologia.
`pyproject.toml` declara NumPy, SciPy, pandas e Matplotlib; pytest é a
dependência opcional de desenvolvimento. A configuração adiciona `src/` ao
path de teste e restringe a descoberta a `tests/`.

## D-006 — Port fiel dos auxiliares MATLAB

`src/physics/fresnel.py` usa os valores literais
`eps0 = 8.8541878176e-12` e `c = 3e8`, com `Z0 = 1/(eps0*c)`, uma única vez
no módulo compartilhado por `rij` e `tij`. As duas funções preservam a
aritmética complexa da expressão MATLAB sem qualquer correção física.

`src/physics/glass.py` mantém a conversão de metros para micrômetros por
`lambda / 1e-6` antes da expressão de soda-lime glass. A operação é
elementwise para entradas NumPy por consequência direta da expressão, sem
ramificações ou aproximações adicionais.

## D-007 — Núcleo do simulador de quatro camadas

`src/physics/transfer_matrix.py` representa literalmente as matrizes de
interface `(1/t)[[1,r],[r,1]]` e de propagação diagonal. O simulador mantém
vetores-coluna 2×1 e a ordem de multiplicação MATLAB com `@` em
`src/physics/simulator.py`.

O laço explícito sobre `Md3` preserva `d3 = (dnm - p[1]) * 1e-9`. As fontes
`2k` e `0k` são calculadas separadamente; o termo cruzado permanece sem fator
2. As intensidades usam literalmente `real(E * conj(E))`, e a normalização
usa integralmente a referência MoS2 do MATLAB. Nenhuma dessas escolhas foi
reinterpretada fisicamente.

O diagnóstico é opcional e permitido para uma única espessura; ele expõe
fases, matrizes, campos e intensidades para o próximo checkpoint MATLAB ×
Python. Não há declaração de equivalência completa até essa comparação.

## D-008 — Infraestrutura de validação MATLAB × Python

Foram extraídas literalmente do arquivo MATLAB principal as funções globais
`legacy_matlab/shg_4layers.m` e `legacy_matlab/shg_mos2_ratios.m`, para que
`legacy_matlab/export_reference_cases.m` possa chamar a própria implementação
MATLAB sem reescrever a física. A única extensão é uma quinta saída opcional
de `shg_4layers`, usada exclusivamente para expor variáveis intermediárias já
calculadas; as quatro saídas físicas e suas expressões não foram alteradas.

O exportador cobre `p0` e dois vetores adicionais fisicamente válidos, as dez
espessuras experimentais, e todos os intermediários do ponto de 150 nm. O
validador `scripts/validate_matlab_python.py` produz comparações de `T`, `R`,
`I_4`, `I_1`, `IMoS24`, `IMoS21`, além de erro máximo absoluto e norma de
Frobenius por intermediário.

Os CSVs foram gerados por uma execução real de MATLAB/Octave e comparados com
o Python. Os máximos observados foram: erro relativo de `T` igual a
`1.6717503026056207e-14`, erro relativo de `R` igual a
`3.644239657078057e-15`, erro absoluto intermediário igual a
`8.881784197001252e-16` e norma de Frobenius intermediária igual a
`1.0878030299442186e-15`. Isso confirma equivalência numérica em precisão de
ponto flutuante; os CSVs em `tests/reference/` são a regressão versionada.
A regressão automática de `T` e `R` usa `rtol=1e-12` e `atol=1e-28`, margem
conservadora sobre os máximos observados sem mascarar uma divergência física.

## D-009 — Espaço oficial de parâmetros e constraints

`optimization/constraints.py` define, em uma única fonte reutilizável, a
ordem oficial dos oito parâmetros, unidades, limites fechados, validação de
vetor real finito e as duas desigualdades estritas de dispersão normal. A API
retorna todas as violações estruturadas e também mensagens legíveis; ela não é
chamada por `physics/simulator.py`, que precisa continuar avaliando vetores
legados durante validações.

Os limites escalares são inclusivos. Entretanto, por serem estritas as
condições `n2_w < n2_2w` e `re_n3_w < re_n3_2w`, os valores superiores de
`n2_w` e `re_n3_w` não podem compor uma solução globalmente válida quando as
respectivas frequências em `2w` também têm teto 6. Isso é consequência lógica
das regras oficiais, não um novo limite.

## D-010 — Estratégia futura para tratamento uniforme de constraints

Foram avaliadas quatro estratégias. *Rejection* é simples, mas desperdiça
avaliações e introduz eficiência dependente do algoritmo. *Repair* evita
avaliações inválidas, porém pode concentrar candidatos nas fronteiras e
distorcer operadores diferentes. *Penalty* exige calibrar pesos e ainda pode
permitir que o simulador receba pontos inválidos. *Reparameterization* mapeia
as coordenadas internas diretamente ao espaço viável e não consome avaliações
da função objetivo com candidatos inválidos.

A recomendação principal é uma reparametrização compartilhada, aplicada antes
de toda avaliação por GA, PSO, DE e CMA-ES: para cada par dispersivo, gerar o
índice de `w` e uma diferença positiva limitada até o teto 6. O mapeamento e
o tratamento dos limites abertos necessários à desigualdade estrita serão
definidos uma única vez antes do primeiro algoritmo. Rejection, repair e
penalty não serão usados como estratégia principal; qualquer uso auxiliar
deverá ser idêntico e contabilizado para todos os algoritmos.

## D-011 — Função objetivo oficial e contagem de avaliações

`optimization/objective.py` é a única camada entre futuros algoritmos e o
simulador. Os dados experimentais oficiais residem uma única vez em
`experiments/data.py`. Para um vetor fisicamente válido, a função usa
literalmente `J = J_T + J_R`, em que cada componente é a **soma** dos erros
quadráticos normalizados pelo máximo experimental correspondente. Não há
média dos pontos e não há penalização de pico do MATLAB legado.

Um candidato inválido gera `InvalidParameterError`, com as violações de
`constraints.py`, antes de qualquer chamada ao simulador. A API não converte
essa condição em uma penalização numérica artificial: a reparametrização
compartilhada planejada deve evitar candidatos inválidos nos experimentos.

`ObjectiveEvaluator` mantém `n_evaluations` sem estado global. Uma avaliação
é incrementada imediatamente antes de uma chamada efetiva ao simulador;
rejeições durante a validação não contam como avaliações físicas.

## D-012 — Baseline serial de desempenho da função objetivo

O benchmark reprodutível em `scripts/benchmark_objective.py` usou seed
`20260824`, 50 avaliações válidas de warm-up (excluídas das estatísticas) e
lotes de 100, 1.000 e 10.000 vetores válidos variados. No lote principal de
10.000, a média foi `0.000419043 s` por avaliação, a mediana
`0.000415600 s` e a taxa `2385.192` avaliações/s. O contador de cada lote
coincidiu exatamente com o número de chamadas físicas executadas.

Esses resultados são um baseline estritamente serial em CPython/Windows, sem
paralelização, GPU, cache ou alterações da física. As projeções para budgets,
5 algoritmos e 30/50 seeds estão registradas em `results/benchmark_objective.md`;
elas excluem overhead de algoritmos, I/O e startup. O benchmark não escolhe o
budget definitivo.

## D-013 — Parametrização normalizada comum e dispersão estrita

Todo algoritmo futuro trabalhará exclusivamente em `z ∈ [0, 1]^8` e chamará
`optimization/parameterization.py` para obter `p`. Os quatro parâmetros
independentes usam as transformações lineares acordadas. Cada par dispersivo
usa o triângulo em coordenadas `x = n_w - 1.5` e
`y = n_2w - n_w - DELTA_N`, com `x >= 0`, `y >= 0` e
`x + y <= S`, onde `S = 6 - 1.5 - DELTA_N`. Para duas coordenadas uniformes
`u, v`, a transformação é `x = S(1-sqrt(u))` e `y = S sqrt(u) v`.

`DELTA_N = 64 * spacing(6.0) = 5.684341886080802e-14` é uma margem numérica
nomeada e centralizada. Ela equivale a 64 ULPs no maior índice, é cerca de
`1.26e-14` da largura do intervalo óptico e garante que a soma float64
preserve `n_w + DELTA_N <= n_2w`, inclusive nas fronteiras fechadas de `z`.
Não é uma nova restrição física interpretativa: é o recorte numérico mínimo
necessário para representar a desigualdade física estrita em um cubo fechado.

A transformação é área-preservadora: `z[2], z[3]` e `z[4], z[5]` uniformes
induzem distribuição uniforme em cada triângulo físico recortado, não a
distribuição enviesada da interpolação sequencial simples. Na amostra fixa de
100.000 vetores (`seed=20260826`), todos foram finitos e fisicamente válidos;
as médias observadas de `x`/`y` foram `1.503598`/`1.492182` para `n2` e
`1.504588`/`1.497865` para `n3`, próximas da média teórica `S/3 = 1.5`.

`to_normalized` existe para debugging e análise. Ela é inversa no interior;
no vértice de medida zero `n_w = 6 - DELTA_N, n_2w = 6`, em que a borda de
`z` colapsa, retorna a convenção canônica de segunda coordenada igual a zero.
Vetores físicos com gap estrito menor que `DELTA_N` permanecem válidos pelas
constraints, mas não pertencem ao domínio normalizado recortado e não têm
inversa nessa API.

Esta mesma transformação será obrigatória para Random Search, DE, GA, PSO e
CMA-ES. Assim, nenhum algoritmo receberá espaço físico ou tratamento de
constraints mais favorável que outro.

## D-014 — Random Search como baseline global

`optimization/random_search.py` é o primeiro baseline global. Ele recebe
explicitamente `seed` e `budget`, usa `np.random.default_rng(seed)` e amostra
somente `z ~ U([0,1]^8)`. Cada `z` passa pela transformação compartilhada
`to_physical(z)` antes de uma única chamada de `ObjectiveEvaluator`; não há
repair, penalty, rejection ou regra adicional de constraints.

O budget é definido exclusivamente pelo contador físico
`ObjectiveEvaluator.n_evaluations`, e a execução termina exatamente nesse
valor. O histórico armazena o melhor valor após cada avaliação física. Em
caso de igualdade exata de `J`, a comparação estrita mantém a primeira
solução encontrada, tornando o desempate determinístico. Esta implementação
não estabelece um resultado científico nem altera o budget piloto planejado
de 50.000 avaliações.

## D-015 — Differential Evolution como segundo baseline global

optimization/differential_evolution.py implementa somente DE no espaço
normalizado z em [0,1]^8. Cada vetor proposto pelo solver é transformado por
to_physical e avaliado uma única vez por ObjectiveEvaluator; portanto, a
parametrização compartilhada preserva os bounds e a dispersão normal sem
rejection, repair ou penalty. Nenhuma regra de otimização foi adicionada ao
simulador ou às constraints.

O baseline usa SciPy 1.18.1 com strategy best1bin, popsize 15 (população
nominal 120), mutation (0.5, 1.0), recombination 0.7, init latinhypercube,
updating deferred, tol=0, atol=0, workers=1, vectorized=False e polish=False.
Não há paralelismo, refinamento local nem avaliação adicional ao término.

O limite de orçamento é rigoroso: a implementação usa DifferentialEvolutionSolver
do SciPy com maxfun igual ao budget, atualização deferred e avanço controlado
até ObjectiveEvaluator.n_evaluations alcançar o mesmo valor. A atualização
deferred permite que a última geração seja parcial quando necessário. O
contador privado nfev do solver também é verificado contra o budget. Essa
escolha foi necessária porque a função pública de conveniência do SciPy não
expõe maxfun. Trata-se de um detalhe de infraestrutura de contabilização, não
de uma alteração do algoritmo ou da função objetivo.

O smoke test com seed 1 e 1.000 avaliações terminou com
n_evaluations = nfev = 1.000 e J = 0.8054211344755735. O experimento
preliminar de cinco seeds, cada uma com 50.000 avaliações, está versionado em
results/differential_evolution_baseline/. A comparação com Random Search
naquele diretório é somente descritiva por avaliação física e não estabelece
uma conclusão científica entre algoritmos.

## D-016 — Política dos baselines preliminares e checkpoint

Random Search e Differential Evolution foram executados com as mesmas seeds
inteiras 1, 2, 3, 4 e 5, orçamento de 50.000 avaliações físicas por seed e
total de 250.000 avaliações por algoritmo. O Random Search obteve melhor,
mediana e pior J de 0.5841852495274906, 0.6852560724860886 e
0.8865663180429331; DE obteve 0.3818429946001101, 0.3818430194775517 e
0.3818430638493236, respectivamente.

Esses números e as curvas são um checkpoint reprodutível, não um resultado
estatístico final: cinco seeds não autorizam inferência de superioridade
estatística. O budget final e a escolha entre 30 e 50 seeds continuam
abertos. O estado consolidado para retomada está em docs/PROJECT_STATE.md;
ele deve ser atualizado após cada checkpoint experimental significativo.

## Ambiguidades abertas

1. Os caminhos foram normalizados para `docs/methodology.md`,
   `docs/equations.md` e `legacy_matlab/`. Os materiais suplementares foram
   preservados sob `docs/`; nenhuma equação ou arquivo MATLAB foi alterado.
2. A equação de documentação para a fonte de SHG é conceitual; o MATLAB é
   específico quanto aos termos `2k` e `0k`. O port deve seguir o MATLAB
   literalmente e validar contra ele antes de qualquer interpretação física.
3. A documentação de equações descreve o termo cruzado como parte de
   `(E+ + E-)²`, mas o MATLAB usa `E+*E-` em cada posição do vetor, sem um
   fator explícito 2. Isso deve ser preservado e apenas investigado depois da
   equivalência numérica.
4. O PDF `NonLTM.pdf` apresenta notas derivacionais com data de 2026 e, em
   uma expressão final, usa módulos quadrados para uma fonte onde o MATLAB
   usa quadrados complexos. Não foi adotada nenhuma alteração baseada nele.
5. Ainda faltam as incertezas experimentais e a decisão final entre 30 e 50
   seeds.
