"""Shared optimization infrastructure; algorithms remain intentionally absent."""

from optimization.constraints import (
    LOWER_BOUNDS,
    PARAMETER_COUNT,
    PARAMETER_DEFINITIONS,
    PARAMETER_NAMES,
    UPPER_BOUNDS,
    ConstraintViolation,
    ParameterDefinition,
    constraint_violations,
    invalid_reasons,
    is_physically_valid,
    lower_bounds,
    upper_bounds,
    validate_parameter_vector,
    validate_physical_parameters,
)
from optimization.objective import (
    InvalidParameterError,
    ObjectiveEvaluator,
    ObjectiveResult,
    calculate_error_components,
    evaluate,
    objective,
)

__all__ = [
    "LOWER_BOUNDS",
    "PARAMETER_COUNT",
    "PARAMETER_DEFINITIONS",
    "PARAMETER_NAMES",
    "UPPER_BOUNDS",
    "ConstraintViolation",
    "ParameterDefinition",
    "constraint_violations",
    "invalid_reasons",
    "is_physically_valid",
    "lower_bounds",
    "upper_bounds",
    "validate_parameter_vector",
    "validate_physical_parameters",
    "InvalidParameterError",
    "ObjectiveEvaluator",
    "ObjectiveResult",
    "calculate_error_components",
    "evaluate",
    "objective",
]
