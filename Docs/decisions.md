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
quatro camadas. Não há função objetivo ou otimizadores. As constraints
oficiais pertencem exclusivamente a `optimization/constraints.py`; o
simulador permanece sem regras de otimização.

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
