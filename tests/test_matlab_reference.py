"""Regression check against the versioned MATLAB/Octave export."""

import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

from physics.simulator import simulate


REFERENCE_DIRECTORY = Path(__file__).parent / "reference"
RELATIVE_TOLERANCE = 1e-12
ABSOLUTE_TOLERANCE = 1e-28


def test_simulator_matches_versioned_matlab_transmission_and_reflection() -> None:
    with (REFERENCE_DIRECTORY / "matlab_reference_parameters.csv").open(newline="", encoding="utf-8") as stream:
        parameters = {
            row["case"]: np.array(
                [
                    float(row["log10_chi"]), float(row["d2_nm"]), float(row["n2_w"]), float(row["n2_2w"]),
                    float(row["re_n3_w"]), float(row["im_n3_w"]), float(row["re_n3_2w"]), float(row["im_n3_2w"]),
                ]
            )
            for row in csv.DictReader(stream)
        }
    references: dict[str, list[dict[str, float]]] = defaultdict(list)
    with (REFERENCE_DIRECTORY / "matlab_reference_cases.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            references[row["case"]].append(
                {name: float(row[name]) for name in ("thickness_nm", "T", "R")}
            )

    for case_name, rows in references.items():
        result = simulate(parameters[case_name], [row["thickness_nm"] for row in rows])
        np.testing.assert_allclose(
            result.T, [row["T"] for row in rows], rtol=RELATIVE_TOLERANCE, atol=ABSOLUTE_TOLERANCE
        )
        np.testing.assert_allclose(
            result.R, [row["R"] for row in rows], rtol=RELATIVE_TOLERANCE, atol=ABSOLUTE_TOLERANCE
        )
