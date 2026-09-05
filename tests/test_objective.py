"""Tests for the official joint transmission/reflection objective."""

import numpy as np
import pytest

from experiments.data import R_EXP, R_EXP_MAX, T_EXP, T_EXP_MAX
from optimization.objective import (
    DEFAULT_OBJECTIVE_WEIGHTS,
    InvalidParameterError,
    ObjectiveEvaluator,
    ObjectiveWeights,
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
    invalid[4] = invalid[6]

    with pytest.raises(InvalidParameterError, match="re_n3_w") as error:
        evaluate(invalid)

    assert {violation.code for violation in error.value.violations} == {"normal_dispersion_n3"}


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


def test_default_weights_preserve_the_scientific_unweighted_objective_exactly() -> None:
    result = evaluate(VALID_PARAMETERS)

    assert result.J_weighted == result.J
    assert objective(VALID_PARAMETERS, weights=DEFAULT_OBJECTIVE_WEIGHTS) == result.J


def test_weighted_objective_preserves_components_and_exposes_both_totals() -> None:
    weights = ObjectiveWeights(transmission=1.0, reflection=5.0)
    result = evaluate(VALID_PARAMETERS, weights=weights)
    evaluator = ObjectiveEvaluator(weights=weights)

    assert result.J == result.J_T + result.J_R
    assert result.J_weighted == result.J_T + 5.0 * result.J_R
    assert objective(VALID_PARAMETERS, weights=weights) == result.J_weighted
    assert evaluator.objective(VALID_PARAMETERS) == result.J_weighted
    assert evaluator.n_evaluations == 1


@pytest.mark.parametrize(
    "weights",
    [
        ObjectiveWeights(transmission=-1.0, reflection=1.0),
        ObjectiveWeights(transmission=1.0, reflection=float("nan")),
        ObjectiveWeights(transmission=0.0, reflection=0.0),
    ],
)
def test_invalid_objective_weights_are_rejected(weights: ObjectiveWeights) -> None:
    with pytest.raises(ValueError):
        evaluate(VALID_PARAMETERS, weights=weights)
