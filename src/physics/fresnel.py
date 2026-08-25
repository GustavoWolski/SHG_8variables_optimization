"""Coeficientes de interface preservados da implementação MATLAB."""

from typing import TypeAlias


Scalar: TypeAlias = float | complex

# Valores usados literalmente em rij.m e tij.m.
EPS0 = 8.8541878176e-12
C = 3e8
Z0 = 1 / (EPS0 * C)


def rij(n1: Scalar, n2: Scalar, sig_s: Scalar) -> Scalar:
    """Return the MATLAB ``rij`` interface reflection coefficient.

    This is the literal expression from ``legacy_matlab/rij.m``. Inputs may
    be real or complex; Python's native arithmetic preserves a complex result
    whenever one is required.
    """

    return (n1 - n2 - Z0 * sig_s) / (n1 + n2 + Z0 * sig_s)


def tij(n1: Scalar, n2: Scalar, sig_s: Scalar) -> Scalar:
    """Return the MATLAB ``tij`` interface transmission coefficient.

    This is the literal expression from ``legacy_matlab/tij.m``. Inputs may
    be real or complex; Python's native arithmetic preserves a complex result
    whenever one is required.
    """

    return 2 * n1 / (n1 + n2 + Z0 * sig_s)
