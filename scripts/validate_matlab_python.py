"""Compare versioned MATLAB SHG exports against the Python physical simulator.

This utility deliberately has no built-in reference values. Run
``export_reference_cases`` in MATLAB/Octave first, then invoke this script.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from physics.simulator import SimulationDiagnostics, simulate  # noqa: E402


EPSILON = 1e-300


def _relative_error(absolute_error: float, reference_value: float) -> float:
    return absolute_error / max(abs(reference_value), EPSILON)


def _load_parameters(path: Path) -> dict[str, np.ndarray]:
    with path.open(newline="", encoding="utf-8") as stream:
        return {
            row["case"]: np.array(
                [
                    float(row["log10_chi"]),
                    float(row["d2_nm"]),
                    float(row["n2_w"]),
                    float(row["n2_2w"]),
                    float(row["re_n3_w"]),
                    float(row["im_n3_w"]),
                    float(row["re_n3_2w"]),
                    float(row["im_n3_2w"]),
                ],
                dtype=np.float64,
            )
            for row in csv.DictReader(stream)
        }


def _load_final_references(path: Path) -> dict[str, list[dict[str, float]]]:
    references: dict[str, list[dict[str, float]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            references[row["case"]].append(
                {
                    name: float(row[name])
                    for name in ("thickness_nm", "T", "R", "I_4", "I_1", "IMoS24", "IMoS21")
                }
            )
    return references


def _load_intermediate_references(path: Path) -> dict[tuple[str, str], np.ndarray]:
    entries: dict[tuple[str, str], list[tuple[int, int, complex]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            entries[(row["case"], row["name"])].append(
                (
                    int(row["row"]),
                    int(row["column"]),
                    complex(float(row["real"]), float(row["imag"])),
                )
            )

    arrays: dict[tuple[str, str], np.ndarray] = {}
    for key, values in entries.items():
        rows = max(row for row, _, _ in values)
        columns = max(column for _, column, _ in values)
        array = np.empty((rows, columns), dtype=np.complex128)
        for row, column, value in values:
            array[row - 1, column - 1] = value
        arrays[key] = array
    return arrays


def _diagnostic_values(diagnostic: SimulationDiagnostics) -> dict[str, np.ndarray]:
    values = asdict(diagnostic) if is_dataclass(diagnostic) else {}
    mapping = {
        "d2": "d2_m",
        "d3": "d3_m",
        "fase21w": "phase21w",
        "fase31w": "phase31w",
        "fase22w": "phase22w",
        "fase32w": "phase32w",
        "M211w": "m211w",
        "P21w": "p21w",
        "M321w": "m321w",
        "P31w": "p31w",
        "M431w": "m431w",
        "T1w": "t1w",
        "r": "reflection",
        "E31w": "e31w",
        "Emas": "emas",
        "Emen": "emen",
        "Es2k": "es2k",
        "Es0k": "es0k",
        "M212w": "m212w",
        "P22w": "p22w",
        "M322w": "m322w",
        "ML": "ml",
        "M342w": "m342w",
        "P3m2w": "p3m2w",
        "MR": "mr",
        "MfactEs": "mfact_es",
        "Ms2k": "ms2k",
        "Ps2k": "ps2k",
        "As2k": "as2k",
        "S2k": "s2k",
        "ESHG2k": "eshg_2k",
        "Ms0k": "ms0k",
        "Ps0k": "ps0k",
        "As0k": "as0k",
        "S0k": "s0k",
        "ESHG0k": "eshg_0k",
        "ESHG": "eshg",
        "I_4": "i_4",
        "I_1": "i_1",
        "n21w": "n21w",
        "n22w": "n22w",
        "n31w": "n31w",
        "n32w": "n32w",
    }
    return {
        matlab_name: np.asarray(values[python_name], dtype=np.complex128).reshape(-1, 1)
        if np.asarray(values[python_name]).ndim == 0
        else np.asarray(values[python_name], dtype=np.complex128)
        for matlab_name, python_name in mapping.items()
    }


def _write_final_comparison(
    parameters: dict[str, np.ndarray],
    references: dict[str, list[dict[str, float]]],
    output_path: Path,
) -> dict[str, float]:
    maxima = {"max_abs_error_T": 0.0, "max_rel_error_T": 0.0, "max_abs_error_R": 0.0, "max_rel_error_R": 0.0}
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        fieldnames = [
            "case", "thickness_nm", "T_matlab", "T_python", "abs_error_T", "rel_error_T",
            "R_matlab", "R_python", "abs_error_R", "rel_error_R", "I4_matlab", "I4_python",
            "I1_matlab", "I1_python", "IMoS24_matlab", "IMoS24_python", "IMoS21_matlab", "IMoS21_python",
        ]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for case_name, rows in references.items():
            thicknesses = np.array([row["thickness_nm"] for row in rows])
            result = simulate(parameters[case_name], thicknesses)
            for index, reference in enumerate(rows):
                abs_t = abs(result.T[index] - reference["T"])
                abs_r = abs(result.R[index] - reference["R"])
                rel_t = _relative_error(abs_t, reference["T"])
                rel_r = _relative_error(abs_r, reference["R"])
                maxima["max_abs_error_T"] = max(maxima["max_abs_error_T"], abs_t)
                maxima["max_rel_error_T"] = max(maxima["max_rel_error_T"], rel_t)
                maxima["max_abs_error_R"] = max(maxima["max_abs_error_R"], abs_r)
                maxima["max_rel_error_R"] = max(maxima["max_rel_error_R"], rel_r)
                writer.writerow({
                    "case": case_name, "thickness_nm": reference["thickness_nm"],
                    "T_matlab": reference["T"], "T_python": result.T[index], "abs_error_T": abs_t, "rel_error_T": rel_t,
                    "R_matlab": reference["R"], "R_python": result.R[index], "abs_error_R": abs_r, "rel_error_R": rel_r,
                    "I4_matlab": reference["I_4"], "I4_python": result.I_4[index],
                    "I1_matlab": reference["I_1"], "I1_python": result.I_1[index],
                    "IMoS24_matlab": reference["IMoS24"], "IMoS24_python": result.IMoS24,
                    "IMoS21_matlab": reference["IMoS21"], "IMoS21_python": result.IMoS21,
                })
    return maxima


def _write_intermediate_comparison(
    parameters: dict[str, np.ndarray],
    references: dict[tuple[str, str], np.ndarray],
    output_path: Path,
) -> dict[str, float]:
    maxima = {"max_intermediate_abs_error": 0.0, "max_intermediate_frobenius_error": 0.0}
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["case", "name", "max_abs_error", "frobenius_error"])
        writer.writeheader()
        for case_name, parameters_case in parameters.items():
            diagnostic = simulate(parameters_case, 150.0, diagnostics=True).diagnostics
            assert diagnostic is not None
            python_values = _diagnostic_values(diagnostic)
            for (reference_case, name), matlab_value in references.items():
                if reference_case != case_name:
                    continue
                python_value = python_values[name]
                if python_value.shape != matlab_value.shape:
                    raise ValueError(f"Shape mismatch for {case_name}/{name}: {python_value.shape} != {matlab_value.shape}")
                difference = python_value - matlab_value
                max_abs = float(np.max(np.abs(difference)))
                frobenius = float(np.linalg.norm(difference))
                maxima["max_intermediate_abs_error"] = max(maxima["max_intermediate_abs_error"], max_abs)
                maxima["max_intermediate_frobenius_error"] = max(maxima["max_intermediate_frobenius_error"], frobenius)
                writer.writerow({"case": case_name, "name": name, "max_abs_error": max_abs, "frobenius_error": frobenius})
    return maxima


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-dir", type=Path, default=REPOSITORY_ROOT / "tests" / "reference")
    parser.add_argument("--output-dir", type=Path, default=REPOSITORY_ROOT / "results" / "matlab_python_validation")
    arguments = parser.parse_args()

    parameters_path = arguments.reference_dir / "matlab_reference_parameters.csv"
    final_path = arguments.reference_dir / "matlab_reference_cases.csv"
    intermediate_path = arguments.reference_dir / "matlab_reference_intermediates.csv"
    missing = [path for path in (parameters_path, final_path, intermediate_path) if not path.is_file()]
    if missing:
        print("MATLAB reference files are missing. Run `export_reference_cases` in MATLAB or Octave first:")
        for path in missing:
            print(f"  missing: {path}")
        return 2

    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    parameters = _load_parameters(parameters_path)
    final_references = _load_final_references(final_path)
    intermediate_references = _load_intermediate_references(intermediate_path)
    final_maxima = _write_final_comparison(parameters, final_references, arguments.output_dir / "final_comparison.csv")
    intermediate_maxima = _write_intermediate_comparison(
        parameters, intermediate_references, arguments.output_dir / "intermediate_comparison.csv"
    )
    summary = {**final_maxima, **intermediate_maxima}
    (arguments.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
