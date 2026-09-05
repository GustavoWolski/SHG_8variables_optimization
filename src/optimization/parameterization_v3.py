"""Normalized direct-box parameterization for search-space V3."""

from __future__ import annotations

from typing import Final

import numpy as np
from numpy.typing import ArrayLike, NDArray

from optimization.constraints_v3 import (
    PARAMETER_COUNT_V3,
    is_physically_valid_v3,
    validate_physical_parameters_v3,
)


NORMALIZED_PARAMETER_COUNT_V3: Final[int] = PARAMETER_COUNT_V3


def validate_normalized_v3(z: ArrayLike) -> NDArray[np.float64]:
    """Return a finite real V3 point in the closed unit cube ``[0, 1]^6``."""

    try:
        raw = np.asarray(z)
    except (TypeError, ValueError) as error:
        raise ValueError(f"z cannot be converted to an array: {error}") from error
    if raw.shape != (NORMALIZED_PARAMETER_COUNT_V3,):
        raise ValueError(
            f"z must have shape ({NORMALIZED_PARAMETER_COUNT_V3},); received shape {raw.shape}."
        )
    if np.iscomplexobj(raw):
        raise ValueError("z must contain only real-valued coordinates.")
    try:
        values = raw.astype(np.float64, copy=True)
    except (TypeError, ValueError) as error:
        raise ValueError(f"z must contain numeric values: {error}") from error
    if not np.all(np.isfinite(values)):
        raise ValueError("z must contain only finite values.")
    if np.any(values < 0.0) or np.any(values > 1.0):
        raise ValueError("Every z coordinate must satisfy 0 <= z_i <= 1.")
    return values


def to_physical_v3(z: ArrayLike) -> NDArray[np.float64]:
    """Map ``z in [0, 1]^6`` to the six independent V3 parameters.

    Both real Nb indices are affine, independent coordinates; no margin,
    ordering, repair, or reparameterization is applied between them.
    """

    values = validate_normalized_v3(z)
    parameters = np.array(
        [
            -10.0 + 20.0 * values[0],
            130.0 + 20.0 * values[1],
            1.5 + 4.5 * values[2],
            4.0 * values[3],
            1.5 + 4.5 * values[4],
            4.0 * values[5],
        ],
        dtype=np.float64,
    )
    if not is_physically_valid_v3(parameters):
        raise RuntimeError("Internal V3 parameterization error: generated an invalid physical vector.")
    return parameters


def to_normalized_v3(p: ArrayLike) -> NDArray[np.float64]:
    """Recover V3 unit-cube coordinates by the exact affine inverse."""

    parameters = validate_physical_parameters_v3(p)
    normalized = np.array(
        [
            (parameters[0] + 10.0) / 20.0,
            (parameters[1] - 130.0) / 20.0,
            (parameters[2] - 1.5) / 4.5,
            parameters[3] / 4.0,
            (parameters[4] - 1.5) / 4.5,
            parameters[5] / 4.0,
        ],
        dtype=np.float64,
    )
    return validate_normalized_v3(normalized)
