# Identificação inversa de parâmetros ópticos

Este repositório contém a implementação Python, validada contra MATLAB/Octave,
de um modelo de geração de segundo harmônico (SHG) em quatro meios:
ar | óxido | camada ativa | vidro. O objetivo científico é identificar oito
parâmetros físicos por ajuste simultâneo de transmissão e reflexão.

## Current status

A física, a validação MATLAB/Octave × Python, constraints, função objetivo,
parametrização comum, benchmark serial, Random Search e Differential Evolution
estão concluídos. O ponto de retomada, decisões invariantes e resultados
reprodutíveis estão em [Project State](docs/PROJECT_STATE.md).

O próximo algoritmo planejado é Genetic Algorithm. PSO, CMA-ES, experimento
comparativo final, análise estatística e identificabilidade ainda não foram
implementados.

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
