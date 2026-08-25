# Identificação inversa de parâmetros ópticos

Este repositório prepara a migração, de MATLAB/Octave para Python, de um
modelo de geração de segundo harmônico (SHG) em quatro meios:
ar | óxido | camada ativa | vidro. O objetivo futuro é identificar oito
parâmetros físicos pelo ajuste simultâneo de transmissão e reflexão.

O estado atual é somente de preparação: a física MATLAB foi inventariada,
mas ainda não existe implementação Python do simulador, da função objetivo
ou de algoritmos de otimização.

## Fontes de referência

1. [Metodologia](<Docs/00 - Research Notebook/methodology.md>)
2. [Equações](<Docs/02 - Equacões/Equações.md>)
3. [MATLAB original](Legacy_matlab/)

As regras operacionais resumidas estão em [AGENTS.md](AGENTS.md), e as
decisões e ambiguidades desta preparação estão em
[Docs/decisions.md](Docs/decisions.md).

## Estrutura inicial

```text
src/
  physics/        # port físico futuro
  optimization/   # somente após validação MATLAB × Python
  experiments/    # execução reprodutível futura
  analysis/       # análise e visualização futuras
tests/            # testes pytest
results/          # artefatos de execuções futuras
notebooks/        # exploração, sem lógica de produção
```

## Ambiente de desenvolvimento

O projeto requer Python 3.11 ou superior. Com `uv`:

```bash
uv sync --extra dev
uv run pytest
```

Os limites físicos, o vetor de parâmetros e as equações não devem ser
alterados durante o port inicial. A próxima implementação permitida é o
port fiel de `rij.m`, seguido de `tij.m` e `nlimeglass.m`.
