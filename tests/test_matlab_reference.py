"""Document the intentional incompatibility with the versioned legacy MATLAB fixtures."""

import csv
from pathlib import Path

import numpy as np
import pytest

from physics.simulator import simulate


REFERENCE_DIRECTORY = Path(__file__).parent / "reference"


def test_versioned_matlab_fixture_is_the_previous_eight_parameter_model() -> None:
    with (REFERENCE_DIRECTORY / "matlab_reference_parameters.csv").open(newline="", encoding="utf-8") as stream:
        fieldnames = csv.DictReader(stream).fieldnames

    assert fieldnames is not None
    assert "d2_nm" in fieldnames
    assert "n2_w" in fieldnames
    assert "n2_2w" in fieldnames
    assert "delta_d3_nm" not in fieldnames


def test_final_simulator_rejects_legacy_eight_parameter_vector() -> None:
    legacy_p = np.array([0.0, 10.0, 2.10, 2.43, 2.04, 0.70, 1.42, 0.80])
    with pytest.raises(ValueError, match="exactly the six final-model parameters"):
        simulate(legacy_p, [65.0])
