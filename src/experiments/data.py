"""Official experimental data for the Projeto 3 objective function."""

from __future__ import annotations

from typing import Final

import numpy as np
from numpy.typing import NDArray


D_NM: Final[NDArray[np.float64]] = np.array(
    [65.0, 80.0, 100.0, 150.0, 190.0, 250.0, 300.0, 400.0, 500.0, 600.0],
    dtype=np.float64,
)
"""Measured total thicknesses in nm, in the official experimental order."""

T_EXP: Final[NDArray[np.float64]] = np.array(
    [2192.89, 2133.53, 2522.53, 3857.56, 3649.85, 1988.13, 359.05, 59.64, 37.68, 16.17],
    dtype=np.float64,
)
"""Official experimental normalized transmission values."""

R_EXP: Final[NDArray[np.float64]] = np.array(
    [621.17, 876.81, 1137.68, 731.88, 1021.73, 920.289, 1521.73, 1072.46, 1057.97, 1028.98],
    dtype=np.float64,
)
"""Official experimental normalized reflection values."""

T_EXP_MAX: Final[float] = float(np.max(T_EXP))
R_EXP_MAX: Final[float] = float(np.max(R_EXP))
