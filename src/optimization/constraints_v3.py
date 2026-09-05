"""Search-space V3 bounds and feasibility checks.

V3 removes the oxide from the optical stack and from the optimization vector.
It deliberately has no normal-dispersion constraint: the two real active-layer
indices are independent closed-box coordinates.
"""

from __future__ import annotations

from typing import Final

import numpy as np
from numpy.typing import ArrayLike, NDArray

from optimization.constraints import ConstraintViolation, ParameterDefinition


PARAMETER_DEFINITIONS_V3: Final[tuple[ParameterDefinition, ...]] = (
    ParameterDefinition("log10_chi", -10.0, 10.0, "log10(chi)"),
    ParameterDefinition("d3_nb_nm", 130.0, 150.0, "nm"),
    ParameterDefinition("re_n3_w", 1.5, 6.0, "dimensionless"),
    ParameterDefinition("im_n3_w", 0.0, 4.0, "dimensionless"),
    ParameterDefinition("re_n3_2w", 1.5, 6.0, "dimensionless"),
    ParameterDefinition("im_n3_2w", 0.0, 4.0, "dimensionless"),
)
"""Official V3 vector order: chi, direct Nb thickness, and complex Nb indices."""

PARAMETER_NAMES_V3: Final[tuple[str, ...]] = tuple(item.name for item in PARAMETER_DEFINITIONS_V3)
LOWER_BOUNDS_V3: Final[tuple[float, ...]] = tuple(item.lower for item in PARAMETER_DEFINITIONS_V3)
UPPER_BOUNDS_V3: Final[tuple[float, ...]] = tuple(item.upper for item in PARAMETER_DEFINITIONS_V3)
PARAMETER_COUNT_V3: Final[int] = len(PARAMETER_DEFINITIONS_V3)


def lower_bounds_v3() -> NDArray[np.float64]:
    """Return a new array of V3 inclusive lower bounds."""

    return np.asarray(LOWER_BOUNDS_V3, dtype=np.float64)


def upper_bounds_v3() -> NDArray[np.float64]:
    """Return a new array of V3 inclusive upper bounds."""

    return np.asarray(UPPER_BOUNDS_V3, dtype=np.float64)


def _coerce_parameter_vector_v3(
    p: ArrayLike,
) -> tuple[NDArray[np.float64] | None, tuple[ConstraintViolation, ...]]:
    """Convert a V3 vector to finite, one-dimensional float64 data."""

    try:
        raw = np.asarray(p)
    except (TypeError, ValueError) as error:
        return None, (
            ConstraintViolation("not_array_like", f"p cannot be converted to an array: {error}"),
        )
    if raw.ndim != 1:
        return None, (
            ConstraintViolation("invalid_shape", f"p must be one-dimensional; received shape {raw.shape}."),
        )
    if raw.size != PARAMETER_COUNT_V3:
        return None, (
            ConstraintViolation(
                "invalid_length",
                f"p must contain exactly {PARAMETER_COUNT_V3} V3 parameters; received {raw.size}.",
            ),
        )
    if np.iscomplexobj(raw):
        return None, (ConstraintViolation("non_real", "p must contain only real-valued parameters."),)
    try:
        values = raw.astype(np.float64, copy=True)
    except (TypeError, ValueError) as error:
        return None, (
            ConstraintViolation("non_numeric", f"p must contain numeric values: {error}"),
        )
    if not np.all(np.isfinite(values)):
        invalid_names = tuple(PARAMETER_NAMES_V3[index] for index in np.flatnonzero(~np.isfinite(values)))
        return None, (
            ConstraintViolation(
                "non_finite",
                f"p contains NaN or infinity in: {', '.join(invalid_names)}.",
                invalid_names,
            ),
        )
    return values, ()


def validate_parameter_vector_v3(p: ArrayLike) -> NDArray[np.float64]:
    """Return a structurally valid V3 vector, without checking its bounds."""

    values, violations = _coerce_parameter_vector_v3(p)
    if violations:
        raise ValueError(" ".join(item.message for item in violations))
    assert values is not None
    return values


def constraint_violations_v3(p: ArrayLike) -> tuple[ConstraintViolation, ...]:
    """Return structural and box-bound violations for V3.

    All V3 bounds are inclusive.  No index-ordering constraint is evaluated.
    """

    values, violations = _coerce_parameter_vector_v3(p)
    if violations:
        return violations
    assert values is not None

    reasons: list[ConstraintViolation] = []
    for index, definition in enumerate(PARAMETER_DEFINITIONS_V3):
        if values[index] < definition.lower:
            reasons.append(
                ConstraintViolation(
                    "below_lower_bound",
                    f"{definition.name}={values[index]!r} is below {definition.lower!r}.",
                    (definition.name,),
                )
            )
        elif values[index] > definition.upper:
            reasons.append(
                ConstraintViolation(
                    "above_upper_bound",
                    f"{definition.name}={values[index]!r} is above {definition.upper!r}.",
                    (definition.name,),
                )
            )
    return tuple(reasons)


def invalid_reasons_v3(p: ArrayLike) -> tuple[str, ...]:
    """Return human-readable explanations for an invalid V3 candidate."""

    return tuple(violation.message for violation in constraint_violations_v3(p))


def is_physically_valid_v3(p: ArrayLike) -> bool:
    """Return whether a vector meets all V3 structural and box constraints."""

    return not constraint_violations_v3(p)


def validate_physical_parameters_v3(p: ArrayLike) -> NDArray[np.float64]:
    """Return a physical V3 vector or raise ``ValueError`` with every reason."""

    values = validate_parameter_vector_v3(p)
    violations = constraint_violations_v3(values)
    if violations:
        raise ValueError(" ".join(item.message for item in violations))
    return values
