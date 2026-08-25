"""Índice de refração do vidro soda-lime preservado do MATLAB."""

import numpy as np
from numpy.typing import NDArray
from typing import TypeAlias


WavelengthInput: TypeAlias = float | np.floating | NDArray[np.floating]
WavelengthOutput: TypeAlias = float | np.floating | NDArray[np.floating]


def nlimeglass(lambda_m: WavelengthInput) -> WavelengthOutput:
    """Return the MATLAB ``nlimeglass`` refractive index for meters input.

    ``lambda_m`` is first converted to micrometers through ``lambda / 1e-6``.
    The expression is intentionally kept identical to
    ``legacy_matlab/nlimeglass.m`` and also operates elementwise on NumPy
    arrays.
    """

    l = lambda_m / 1e-6
    return 1.5130 - 0.003169 * l**2 + 0.003962 / (l**2)
