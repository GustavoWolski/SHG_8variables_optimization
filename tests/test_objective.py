"""Tests for the official joint transmission/reflection objective."""

import numpy as np
import pytest

from experiments.data import R_EXP, R_EXP_MAX, T_EXP, T_EXP_MAX
from optimization.objective import (
    InvalidParameterError,
    ObjectiveEvaluator,
    calculate_error_components,
    evaluate,
    objective,
)


VALID_PARAMETERS = np.array([0.0, 10.0, 2.0, 3.0, 2.5, 1.0, 3.5, 2.0])


def test_error_components_are_separate_sums_with_the_official_normalizations() -> None:
    theoretical_t = np.zeros_like(T_EXP)
    theoretical_r = np.zeros_like(R_EXP)

    j_t, j_r, j = calculate_error_components(theoretical_t, theoretical_r)

    expected_j_t = float(np.sum(((T_EXP - theoretical_t) / T_EXP_MAX) ** 2))
    expected_j_r = float(np.sum(((R_EXP - theoretical_r) / R_EXP_MAX) ** 2))
    assert j_t == expected_j_t
    assert j_r == expected_j_r
    assert j == j_t + j_r


def test_error_components_are_zero_for_artificial_perfect_data() -> None:
    j_t, j_r, j = calculate_error_components(T_EXP, R_EXP)

    assert j_t == 0.0
    assert j_r == 0.0
    assert j == 0.0


def test_detailed_evaluation_returns_nonnegative_components_and_ten_points() -> None:
    result = evaluate(VALID_PARAMETERS)

    assert result.J == result.J_T + result.J_R
    assert result.J >= 0.0
    assert result.J_T >= 0.0
    assert result.J_R >= 0.0
    assert result.T_theoretical.shape == (10,)
    assert result.R_theoretical.shape == (10,)
    assert result.valid_physics
    np.testing.assert_array_equal(result.p, VALID_PARAMETERS)


def test_same_input_produces_the_same_detailed_result() -> None:
    first = evaluate(VALID_PARAMETERS)
    second = evaluate(VALID_PARAMETERS)

    assert first.J == second.J
    assert first.J_T == second.J_T
    assert first.J_R == second.J_R
    np.testing.assert_array_equal(first.T_theoretical, second.T_theoretical)
    np.testing.assert_array_equal(first.R_theoretical, second.R_theoretical)


def test_invalid_vector_is_rejected_before_a_detailed_evaluation() -> None:
    invalid = VALID_PARAMETERS.copy()
    invalid[2] = invalid[3]

    with pytest.raises(InvalidParameterError, match="n2_w") as error:
        evaluate(invalid)

    assert {violation.code for violation in error.value.violations} == {"normal_dispersion_n2"}


def test_stateful_evaluator_counts_each_valid_physical_call() -> None:
    evaluator = ObjectiveEvaluator()

    detailed = evaluator.evaluate(VALID_PARAMETERS)
    scalar = evaluator.objective(VALID_PARAMETERS)

    assert detailed.J == scalar
    assert evaluator.n_evaluations == 2


def test_rejected_candidate_does_not_increment_physical_evaluation_count() -> None:
    evaluator = ObjectiveEvaluator()
    invalid = VALID_PARAMETERS.copy()
    invalid[4] = invalid[6]

    with pytest.raises(InvalidParameterError, match="re_n3_w"):
        evaluator.objective(invalid)

    assert evaluator.n_evaluations == 0


def test_scalar_objective_matches_complete_evaluation() -> None:
    assert objective(VALID_PARAMETERS) == evaluate(VALID_PARAMETERS).J
