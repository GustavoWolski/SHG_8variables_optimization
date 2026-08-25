"""Building blocks for the MATLAB 2-by-2 transfer-matrix convention."""

import numpy as np
from numpy.typing import NDArray

from physics.fresnel import rij, tij


ComplexMatrix = NDArray[np.complex128]


def interface_matrix(n1: complex, n2: complex, sig_s: complex = 0) -> ComplexMatrix:
    """Return ``(1 / tij) * [[1, rij], [rij, 1]]`` from the MATLAB model."""

    reflection = rij(n1, n2, sig_s)
    transmission = tij(n1, n2, sig_s)
    return (1 / transmission) * np.array(
        [[1, reflection], [reflection, 1]], dtype=np.complex128
    )


def propagation_matrix(phase: complex) -> ComplexMatrix:
    """Return the MATLAB propagation matrix ``diag(exp(i*phase), exp(-i*phase))``."""

    return np.array(
        [[np.exp(1j * phase), 0], [0, np.exp(-1j * phase)]],
        dtype=np.complex128,
    )


def column_vector(first: complex, second: complex) -> NDArray[np.complex128]:
    """Return a 2-by-1 field/source vector, matching MATLAB's column vectors."""

    return np.array([[first], [second]], dtype=np.complex128)
