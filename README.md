# Identificação inversa de parâmetros ópticos

Este repositório preserva a implementação Python, validada contra MATLAB/Octave,
do modelo SHG histórico V2 em quatro meios: ar | óxido | camada ativa | vidro.
Também contém a configuração física V3, ainda sem referência MATLAB/Octave,
em três meios: ar | camada ativa/Nb | vidro.

## Model versions

O V2 é imutável para fins de regressão e dos benchmarks já salvos: seu vetor
tem oito parâmetros, incluindo espessura e índices independentes do óxido.

O V3 não representa o óxido como camada óptica. O vetor tem seis parâmetros:

```text
[log10_chi, d3_nb_nm, re_n3_w, im_n3_w, re_n3_2w, im_n3_2w]
```

`d3_nb_nm` é a espessura direta de Nb no total experimental de referência de
150 nm e está em `[130, 150] nm`; os dois índices reais de Nb são
independentes em `[1.5, 6]`. Não há parâmetro, interface ou matriz de
propagação independente para o óxido no V3. O objetivo permanece exatamente
`J = J_T + J_R`, e nenhum algoritmo ou benchmark V2 foi modificado.

## Current status

A validação MATLAB/Octave × Python cobre exclusivamente o V2. O V3 possui
testes internos de limites, ausência de dispersão normal, estrutura sem óxido,
finitude e determinismo; uma referência MATLAB/Octave V3 continua pendente.
O ponto de retomada, decisões invariantes e resultados reprodutíveis estão em
[Project State](docs/PROJECT_STATE.md).

## Fontes de referência

1. [Metodologia](docs/methodology.md)
2. [Equações](docs/equations.md)
3. [MATLAB original](legacy_matlab/)

As regras operacionais estão em [AGENTS.md](AGENTS.md) e as decisões
históricas em [docs/decisions.md](docs/decisions.md).

## Ambiente de desenvolvimento

O projeto requer Python 3.11 ou superior. Com `uv`:

```bash
uv sync --extra dev
uv run pytest
```

Os limites físicos, o vetor de parâmetros e as equações não devem ser
alterados sem discussão e validação. Consulte o Project State antes de iniciar
uma nova etapa.
