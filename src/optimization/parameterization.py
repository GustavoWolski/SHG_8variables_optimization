"""Shared normalized-to-physical mapping for every future optimizer.

The oxide indices are independent uniform coordinates. Only the layer-3
real-index pair is sampled over its feasible triangle, with the documented
floating-point separation ``DELTA_N`` for its strict physical inequality.
"""

from __future__ import annotations

from typing import Final

import numpy as np
from numpy.typing import ArrayLike, NDArray

from optimization.constraints import PARAMETER_COUNT, is_physically_valid, validate_physical_parameters


NORMALIZED_PARAMETER_COUNT: Final[int] = PARAMETER_COUNT
OXIDE_INDEX_LOWER_BOUND: Final[float] = 1.0
OXIDE_INDEX_UPPER_BOUND: Final[float] = 6.0
# Backward-compatible name for the lower bound of the triangular layer-3 pair.
INDEX_LOWER_BOUND: Final[float] = 1.5
INDEX_UPPER_BOUND: Final[float] = 6.0
# 64 ULP at the upper bound protects strict ordering through float64 arithmetic.
DELTA_N: Final[float] = float(64 * np.spacing(INDEX_UPPER_BOUND))
INDEX_TRIANGLE_SIDE: Final[float] = INDEX_UPPER_BOUND - INDEX_LOWER_BOUND - DELTA_N


def validate_normalized(z: ArrayLike) -> NDArray[np.float64]:
    """Return a finite real normalized vector in the closed unit cube ``[0, 1]^8``."""

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


def _uniform_triangle_pair(first: float, second: float) -> tuple[float, float]:
    """Map two unit coordinates to a uniform point in one strict-order triangle."""

    radius = float(np.sqrt(first))
    lower_index = INDEX_LOWER_BOUND + INDEX_TRIANGLE_SIDE * (1.0 - radius)
    gap_after_margin = INDEX_TRIANGLE_SIDE * radius * second
    upper_index = lower_index + DELTA_N + gap_after_margin
    return lower_index, upper_index


def to_physical(z: ArrayLike) -> NDArray[np.float64]:
    """Map ``z in [0, 1]^8`` deterministically to a physically valid vector ``p``.

    The oxide coordinates are independent: ``n2_w = 1 + 5*z[2]`` and
    ``n2_2w = 1 + 5*z[3]``. ``z[4:6]`` uses the area-preserving
    square-to-triangle map ``x = S * (1 - sqrt(z_a))`` and
    ``y = S * sqrt(z_a) * z_b``, where ``S = 6 - 1.5 - DELTA_N``. The
    latter keeps only the layer-3 pair strictly ordered.
    """

    values = validate_normalized(z)
    re_n3_w, re_n3_2w = _uniform_triangle_pair(values[4], values[5])
    parameters = np.array(
        [
            -10.0 + 20.0 * values[0],
            20.0 * values[1],
            OXIDE_INDEX_LOWER_BOUND + (OXIDE_INDEX_UPPER_BOUND - OXIDE_INDEX_LOWER_BOUND) * values[2],
            OXIDE_INDEX_LOWER_BOUND + (OXIDE_INDEX_UPPER_BOUND - OXIDE_INDEX_LOWER_BOUND) * values[3],
            re_n3_w,
            4.0 * values[6],
            re_n3_2w,
            4.0 * values[7],
        ],
        dtype=np.float64,
    )
    if not is_physically_valid(parameters):
        raise RuntimeError("Internal parameterization error: generated an invalid physical vector.")
    return parameters


def _inverse_triangle_pair(lower_index: float, upper_index: float) -> tuple[float, float]:
    """Recover canonical unit coordinates for one point in the trimmed triangle."""

    largest_lower_index = INDEX_UPPER_BOUND - DELTA_N
    if lower_index > largest_lower_index:
        raise ValueError(
            "The lower index is physically valid but outside the DELTA_N-trimmed parameterization domain."
        )
    gap_after_margin = upper_index - lower_index - DELTA_N
    if gap_after_margin < 0.0:
        raise ValueError("The index gap is smaller than DELTA_N and cannot be represented in normalized space.")

    radius = (largest_lower_index - lower_index) / INDEX_TRIANGLE_SIDE
    z_first = float(np.clip(radius * radius, 0.0, 1.0))
    if radius == 0.0:
        # The collapsed triangle vertex has a canonical inverse despite its non-unique z edge.
        return z_first, 0.0
    z_second = gap_after_margin / (INDEX_TRIANGLE_SIDE * radius)
    if z_second < 0.0 or z_second > 1.0:
        raise ValueError("The index pair is outside the DELTA_N-trimmed triangle.")
    return z_first, float(np.clip(z_second, 0.0, 1.0))


def to_normalized(p: ArrayLike) -> NDArray[np.float64]:
    """Recover normalized coordinates for a vector produced by :func:`to_physical`.

    Oxide coordinates use the independent affine inverse. The layer-3
    triangle inverse is unique in its interior; at the single vertex
    ``n_w = 6 - DELTA_N, n_2w = 6``, it returns canonical second coordinate
    zero. Physically valid layer-3 vectors with a gap smaller than ``DELTA_N``
    are outside that deliberately trimmed normalized domain and raise
    ``ValueError``.
    """

    parameters = validate_physical_parameters(p)
    n3_first, n3_second = _inverse_triangle_pair(parameters[4], parameters[6])
    normalized = np.array(
        [
            (parameters[0] + 10.0) / 20.0,
            parameters[1] / 20.0,
            (parameters[2] - OXIDE_INDEX_LOWER_BOUND)
            / (OXIDE_INDEX_UPPER_BOUND - OXIDE_INDEX_LOWER_BOUND),
            (parameters[3] - OXIDE_INDEX_LOWER_BOUND)
            / (OXIDE_INDEX_UPPER_BOUND - OXIDE_INDEX_LOWER_BOUND),
            n3_first,
            n3_second,
            parameters[5] / 4.0,
            parameters[7] / 4.0,
        ],
        dtype=np.float64,
    )
    return validate_normalized(normalized)
