"""Official optimization parameter space and physical feasibility checks.

The functions in this module intentionally do not call, wrap, or alter the
physical simulator. They define the admissible inputs expected from future
optimization algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
from numpy.typing import ArrayLike, NDArray


@dataclass(frozen=True, slots=True)
class ParameterDefinition:
    """Name, closed box bounds, and unit of one optimization coordinate."""

    name: str
    lower: float
    upper: float
    unit: str


@dataclass(frozen=True, slots=True)
class ConstraintViolation:
    """One reason why a candidate does not belong to the physical space."""

    code: str
    message: str
    parameter_names: tuple[str, ...] = ()


PARAMETER_DEFINITIONS: Final[tuple[ParameterDefinition, ...]] = (
    ParameterDefinition("log10_chi", -10.0, 10.0, "log10(chi)"),
    ParameterDefinition("d2_nm", 0.0, 20.0, "nm"),
    ParameterDefinition("n2_w", 1.5, 6.0, "dimensionless"),
    ParameterDefinition("n2_2w", 1.5, 6.0, "dimensionless"),
    ParameterDefinition("re_n3_w", 1.5, 6.0, "dimensionless"),
    ParameterDefinition("im_n3_w", 0.0, 4.0, "dimensionless"),
    ParameterDefinition("re_n3_2w", 1.5, 6.0, "dimensionless"),
    ParameterDefinition("im_n3_2w", 0.0, 4.0, "dimensionless"),
)
"""Official parameter order, bounds, and units for every future optimizer."""

PARAMETER_NAMES: Final[tuple[str, ...]] = tuple(item.name for item in PARAMETER_DEFINITIONS)
LOWER_BOUNDS: Final[tuple[float, ...]] = tuple(item.lower for item in PARAMETER_DEFINITIONS)
UPPER_BOUNDS: Final[tuple[float, ...]] = tuple(item.upper for item in PARAMETER_DEFINITIONS)
PARAMETER_COUNT: Final[int] = len(PARAMETER_DEFINITIONS)


def lower_bounds() -> NDArray[np.float64]:
    """Return a new array of the official inclusive lower bounds."""

    return np.asarray(LOWER_BOUNDS, dtype=np.float64)


def upper_bounds() -> NDArray[np.float64]:
    """Return a new array of the official inclusive upper bounds."""

    return np.asarray(UPPER_BOUNDS, dtype=np.float64)


def _coerce_parameter_vector(p: ArrayLike) -> tuple[NDArray[np.float64] | None, tuple[ConstraintViolation, ...]]:
    """Convert one-dimensional real input to float64 while retaining validation reasons."""

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
    if raw.size != PARAMETER_COUNT:
        return None, (
            ConstraintViolation(
                "invalid_length",
                f"p must contain exactly {PARAMETER_COUNT} parameters; received {raw.size}.",
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
        invalid_names = tuple(PARAMETER_NAMES[index] for index in np.flatnonzero(~np.isfinite(values)))
        return None, (
            ConstraintViolation(
                "non_finite",
                f"p contains NaN or infinity in: {', '.join(invalid_names)}.",
                invalid_names,
            ),
        )
    return values, ()


def validate_parameter_vector(p: ArrayLike) -> NDArray[np.float64]:
    """Return ``p`` as a finite, real, one-dimensional vector of length eight.

    This function checks vector structure only. Use
    :func:`validate_physical_parameters` when box bounds and normal dispersion
    must also be enforced.
    """

    values, violations = _coerce_parameter_vector(p)
    if violations:
        raise ValueError(" ".join(item.message for item in violations))
    assert values is not None
    return values


def constraint_violations(p: ArrayLike) -> tuple[ConstraintViolation, ...]:
    """Return every structural or physical reason that ``p`` is invalid.

    Box bounds are inclusive. The two normal-dispersion inequalities are
    strict: ``n2_w < n2_2w`` and ``re_n3_w < re_n3_2w``.
    """

    values, violations = _coerce_parameter_vector(p)
    if violations:
        return violations
    assert values is not None

    reasons: list[ConstraintViolation] = []
    for index, definition in enumerate(PARAMETER_DEFINITIONS):
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

    if not values[2] < values[3]:
        reasons.append(
            ConstraintViolation(
                "normal_dispersion_n2",
                f"n2_w={values[2]!r} must be strictly smaller than n2_2w={values[3]!r}.",
                ("n2_w", "n2_2w"),
            )
        )
    if not values[4] < values[6]:
        reasons.append(
            ConstraintViolation(
                "normal_dispersion_n3",
                f"re_n3_w={values[4]!r} must be strictly smaller than re_n3_2w={values[6]!r}.",
                ("re_n3_w", "re_n3_2w"),
            )
        )
    return tuple(reasons)


def invalid_reasons(p: ArrayLike) -> tuple[str, ...]:
    """Return human-readable explanations for an invalid candidate vector."""

    return tuple(violation.message for violation in constraint_violations(p))


def is_physically_valid(p: ArrayLike) -> bool:
    """Return whether ``p`` satisfies the official bounds and dispersion rules."""

    return not constraint_violations(p)


def validate_physical_parameters(p: ArrayLike) -> NDArray[np.float64]:
    """Return a valid parameter vector or raise ``ValueError`` with all reasons."""

    values = validate_parameter_vector(p)
    violations = constraint_violations(values)
    if violations:
        raise ValueError(" ".join(item.message for item in violations))
    return values
