"""V3 objective tests: unchanged J = J_T + J_R with V3 validation."""

import numpy as np
import pytest

from optimization.objective_v3 import InvalidParameterErrorV3, ObjectiveEvaluatorV3, evaluate_v3, objective_v3


P_V3 = np.array([0.0, 140.0, 5.0, 0.7, 2.0, 0.8])


def test_v3_objective_keeps_the_unweighted_joint_definition() -> None:
    result = evaluate_v3(P_V3)

    assert result.J == result.J_T + result.J_R
    assert objective_v3(P_V3) == result.J
    assert result.valid_physics
    assert result.T_theoretical.shape == (10,)
    assert result.R_theoretical.shape == (10,)


def test_v3_objective_accepts_inverse_real_index_order_without_penalty() -> None:
    result = evaluate_v3(P_V3)

    assert np.isfinite(result.J)
    assert np.isfinite(result.J_T)
    assert np.isfinite(result.J_R)


def test_v3_evaluator_does_not_count_a_rejected_thickness() -> None:
    evaluator = ObjectiveEvaluatorV3()
    invalid = P_V3.copy()
    invalid[1] = 129.0

    with pytest.raises(InvalidParameterErrorV3, match="d3_nb_nm"):
        evaluator.objective(invalid)

    assert evaluator.n_evaluations == 0
