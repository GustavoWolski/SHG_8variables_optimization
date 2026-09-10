# Identificação inversa de parâmetros ópticos

Este repositório contém a implementação Python, validada contra MATLAB/Octave,
de um modelo de geração de segundo harmônico (SHG) em quatro meios:
ar | óxido | camada ativa | vidro. A configuração final identifica seis
parâmetros físicos por ajuste simultâneo de transmissão e reflexão, com
óxido fixo em 10 nm e índices unitários e uma correção global da espessura
nominal da camada ativa.

## Current status

A física final, constraints e parametrização comum usam
`p = [log10_chi, delta_d3_nm, n3_w, k3_w, n3_2w, k3_2w]` e `z ∈ [0,1]^6`.
O ponto de retomada, decisões invariantes e resultados
reprodutíveis estão em [Project State](docs/PROJECT_STATE.md).

O MATLAB versionado representa a formulação anterior de oito parâmetros e é
preservado como referência histórica; ele não contém a correção `p(9)` da
versão final comunicada pelo professor.

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
