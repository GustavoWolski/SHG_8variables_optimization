"""Search-space V3 constraints: direct Nb thickness and independent real indices."""

import numpy as np

from optimization.constraints_v3 import (
    LOWER_BOUNDS_V3,
    PARAMETER_COUNT_V3,
    PARAMETER_NAMES_V3,
    UPPER_BOUNDS_V3,
    constraint_violations_v3,
    is_physically_valid_v3,
    validate_physical_parameters_v3,
)


VALID_V3_PARAMETERS = np.array([0.0, 140.0, 2.5, 1.0, 3.5, 2.0])


def _codes(parameters: np.ndarray) -> set[str]:
    return {violation.code for violation in constraint_violations_v3(parameters)}


def test_v3_has_exactly_six_non_oxide_parameters() -> None:
    assert PARAMETER_COUNT_V3 == 6
    assert PARAMETER_NAMES_V3 == (
        "log10_chi",
        "d3_nb_nm",
        "re_n3_w",
        "im_n3_w",
        "re_n3_2w",
        "im_n3_2w",
    )
    assert not any("oxide" in name or name.startswith("n2_") or name == "d2_nm" for name in PARAMETER_NAMES_V3)


def test_v3_accepts_the_130_nm_nb_thickness_boundary() -> None:
    parameters = VALID_V3_PARAMETERS.copy()
    parameters[1] = 130.0

    np.testing.assert_array_equal(validate_physical_parameters_v3(parameters), parameters)
    assert is_physically_valid_v3(parameters)


def test_v3_accepts_the_150_nm_nb_thickness_boundary() -> None:
    parameters = VALID_V3_PARAMETERS.copy()
    parameters[1] = 150.0

    np.testing.assert_array_equal(validate_physical_parameters_v3(parameters), parameters)
    assert is_physically_valid_v3(parameters)


def test_v3_rejects_nb_thickness_below_130_nm() -> None:
    parameters = VALID_V3_PARAMETERS.copy()
    parameters[1] = 129.999

    assert "below_lower_bound" in _codes(parameters)
    assert not is_physically_valid_v3(parameters)


def test_v3_rejects_nb_thickness_above_150_nm() -> None:
    parameters = VALID_V3_PARAMETERS.copy()
    parameters[1] = 150.001

    assert "above_upper_bound" in _codes(parameters)
    assert not is_physically_valid_v3(parameters)


def test_v3_accepts_inverse_real_index_order() -> None:
    parameters = VALID_V3_PARAMETERS.copy()
    parameters[2], parameters[4] = 5.5, 2.0

    assert is_physically_valid_v3(parameters)
    assert constraint_violations_v3(parameters) == ()


def test_v3_accepts_normal_real_index_order() -> None:
    parameters = VALID_V3_PARAMETERS.copy()
    parameters[2], parameters[4] = 2.0, 5.5

    assert is_physically_valid_v3(parameters)
    assert constraint_violations_v3(parameters) == ()


def test_v3_applies_no_normal_dispersion_constraint() -> None:
    equal_real_indices = VALID_V3_PARAMETERS.copy()
    equal_real_indices[2] = equal_real_indices[4]

    assert is_physically_valid_v3(equal_real_indices)
    assert not any("dispersion" in code for code in _codes(equal_real_indices))


def test_v3_exposes_the_specified_individual_bounds() -> None:
    np.testing.assert_array_equal(LOWER_BOUNDS_V3, [-10.0, 130.0, 1.5, 0.0, 1.5, 0.0])
    np.testing.assert_array_equal(UPPER_BOUNDS_V3, [10.0, 150.0, 6.0, 4.0, 6.0, 4.0])


def test_v3_rejects_the_legacy_eight_parameter_vector() -> None:
    assert _codes(np.zeros(8)) == {"invalid_length"}
