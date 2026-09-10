"""Shared independent normalized-to-physical mapping for every optimizer."""

from __future__ import annotations

from typing import Final

import numpy as np
from numpy.typing import ArrayLike, NDArray

from optimization.constraints import PARAMETER_COUNT, is_physically_valid, validate_physical_parameters


NORMALIZED_PARAMETER_COUNT: Final[int] = PARAMETER_COUNT
ACTIVE_INDEX_LOWER_BOUND: Final[float] = 0.1
ACTIVE_INDEX_UPPER_BOUND: Final[float] = 10.0
ACTIVE_EXTINCTION_UPPER_BOUND: Final[float] = 10.0
DELTA_D3_LOWER_BOUND_NM: Final[float] = -20.0
DELTA_D3_UPPER_BOUND_NM: Final[float] = 20.0


def validate_normalized(z: ArrayLike) -> NDArray[np.float64]:
    """Return a finite real normalized vector in the closed unit cube ``[0, 1]^6``."""

    try:
        raw = np.asarray(z)
    except (TypeError, ValueError) as error:
        raise ValueError(f"z cannot be converted to an array: {error}") from error
    if raw.shape != (NORMALIZED_PARAMETER_COUNT,):
        raise ValueError(
            f"z must have shape ({NORMALIZED_PARAMETER_COUNT},); received shape {raw.shape}."
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


def to_physical(z: ArrayLike) -> NDArray[np.float64]:
    """Map independent ``z in [0, 1]^6`` coordinates to physical vector ``p``."""

    values = validate_normalized(z)
    parameters = np.array(
        [
            -10.0 + 20.0 * values[0],
            DELTA_D3_LOWER_BOUND_NM
            + (DELTA_D3_UPPER_BOUND_NM - DELTA_D3_LOWER_BOUND_NM) * values[1],
            ACTIVE_INDEX_LOWER_BOUND + (ACTIVE_INDEX_UPPER_BOUND - ACTIVE_INDEX_LOWER_BOUND) * values[2],
            ACTIVE_EXTINCTION_UPPER_BOUND * values[3],
            ACTIVE_INDEX_LOWER_BOUND + (ACTIVE_INDEX_UPPER_BOUND - ACTIVE_INDEX_LOWER_BOUND) * values[4],
            ACTIVE_EXTINCTION_UPPER_BOUND * values[5],
        ],
        dtype=np.float64,
    )
    if not is_physically_valid(parameters):
        raise RuntimeError("Internal parameterization error: generated an invalid physical vector.")
    return parameters


def to_normalized(p: ArrayLike) -> NDArray[np.float64]:
    """Recover the independent normalized coordinates of a valid physical vector."""

    parameters = validate_physical_parameters(p)
    normalized = np.array(
        [
            (parameters[0] + 10.0) / 20.0,
            (parameters[1] - DELTA_D3_LOWER_BOUND_NM)
            / (DELTA_D3_UPPER_BOUND_NM - DELTA_D3_LOWER_BOUND_NM),
            (parameters[2] - ACTIVE_INDEX_LOWER_BOUND)
            / (ACTIVE_INDEX_UPPER_BOUND - ACTIVE_INDEX_LOWER_BOUND),
            parameters[3] / ACTIVE_EXTINCTION_UPPER_BOUND,
            (parameters[4] - ACTIVE_INDEX_LOWER_BOUND)
            / (ACTIVE_INDEX_UPPER_BOUND - ACTIVE_INDEX_LOWER_BOUND),
            parameters[5] / ACTIVE_EXTINCTION_UPPER_BOUND,
        ],
        dtype=np.float64,
    )
    return validate_normalized(normalized)
