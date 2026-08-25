# Decisões de preparação

Este registro documenta somente decisões de organização tomadas antes do
port. Ele não substitui nem modifica a formulação física.

## D-001 — Hierarquia de fontes

Para qualquer decisão física, a precedência é:

1. `Docs/00 - Research Notebook/methodology.md`;
2. `Docs/02 - Equacões/Equações.md`;
3. `Legacy_matlab/`.

Na prática, os arquivos MATLAB resolvem detalhes executáveis que a
documentação marcava como pendentes, por exemplo as expressões completas de
`rij`, `tij` e `nlimeglass`. Quando houver conflito real entre a documentação
e o comportamento MATLAB, o conflito deve ser registrado antes do port e não
resolvido silenciosamente.

## D-002 — Escopo desta etapa

Foram criados apenas pacotes vazios, configuração de ambiente, pytest e
documentação. Não há código Python do simulador, função objetivo, constraints
ou otimizadores. Portanto, nenhum resultado numérico Python deve ser
interpretado como validação do modelo.

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

## Ambiguidades abertas

1. A documentação pede os caminhos normalizados `docs/methodology.md`,
   `docs/equations.md` e `legacy_matlab/`, mas os arquivos preservados estão
   organizados como `Docs/...` e `Legacy_matlab/`. Em Windows, a diferença de
   maiúsculas não altera o acesso, mas a estrutura interna ainda diverge;
   nenhuma movimentação ou duplicação de fonte foi feita nesta etapa.
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
5. Ainda faltam vetores de saída MATLAB de referência, a tolerância de
   equivalência, as incertezas experimentais e a decisão final entre 30 e 50
   seeds.
