"""Tests for read-only benchmark analysis and standardized figure generation."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import replace
from pathlib import Path

import matplotlib.image as mpimg
import numpy as np
import pytest

from analysis.plotting import (
    AlgorithmResults,
    AlgorithmSpec,
    BenchmarkRun,
    ConvergenceHistory,
    algorithm_summary_rows,
    align_stepwise_histories,
    calculate_convergence_summary,
    default_algorithm_specs,
    load_benchmarks,
    regenerate_benchmark_figures,
    should_plot_log_y,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def existing_results() -> tuple[AlgorithmResults, ...]:
    return load_benchmarks(default_algorithm_specs(ROOT / "results"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _minimal_run(seed: int, best_J: float) -> BenchmarkRun:
    return BenchmarkRun(
        seed=seed,
        budget=5,
        n_evaluations=5,
        best_J=best_J,
        best_J_T=best_J / 2.0,
        best_J_R=best_J / 2.0,
        best_p=np.zeros(8, dtype=np.float64),
        T_theoretical=np.zeros(10, dtype=np.float64),
        R_theoretical=np.zeros(10, dtype=np.float64),
    )


def test_loads_all_three_existing_benchmarks(existing_results: tuple[AlgorithmResults, ...]) -> None:
    assert [result.spec.short_name for result in existing_results] == ["RS", "DE", "GA"]
    for result in existing_results:
        assert len(result.runs) == 5
        assert result.budget == 50_000
        assert set(result.histories) == {1, 2, 3, 4, 5}
        assert all(history.evaluations[-1] == 50_000 for history in result.histories.values())


def test_v2_directory_layout_is_selected_when_present() -> None:
    specs = default_algorithm_specs(ROOT / "results" / "search_space_v2")

    expected = [
        "random_search",
        "differential_evolution",
        "genetic_algorithm",
    ]
    if (ROOT / "results" / "search_space_v2" / "particle_swarm").is_dir():
        expected.append("particle_swarm")
    assert [spec.directory.name for spec in specs] == expected


def test_stepwise_alignment_uses_forward_fill_without_linear_interpolation() -> None:
    histories = [
        ConvergenceHistory(
            seed=1,
            evaluations=np.asarray([1, 3, 5], dtype=np.int64),
            best_J=np.asarray([10.0, 4.0, 2.0], dtype=np.float64),
        ),
        ConvergenceHistory(
            seed=2,
            evaluations=np.asarray([1, 4, 5], dtype=np.int64),
            best_J=np.asarray([8.0, 3.0, 1.0], dtype=np.float64),
        ),
    ]
    grid = np.arange(1, 6, dtype=np.int64)
    aligned = align_stepwise_histories(histories, grid)
    np.testing.assert_array_equal(aligned[0], [10.0, 10.0, 4.0, 4.0, 2.0])
    np.testing.assert_array_equal(aligned[1], [8.0, 8.0, 8.0, 3.0, 1.0])


def test_pointwise_median_quartiles_and_iqr_are_correct() -> None:
    spec = AlgorithmSpec("Test", "T", Path("unused"), "#000000")
    terminal_values = (1.0, 2.0, 3.0, 4.0)
    runs = tuple(_minimal_run(seed, value) for seed, value in enumerate(terminal_values, start=1))
    histories = {
        run.seed: ConvergenceHistory(
            seed=run.seed,
            evaluations=np.asarray([1, 5], dtype=np.int64),
            best_J=np.asarray([run.best_J + 4.0, run.best_J], dtype=np.float64),
        )
        for run in runs
    }
    summary = calculate_convergence_summary(
        AlgorithmResults(spec, runs, histories),
        np.asarray([1, 2, 5], dtype=np.int64),
    )
    np.testing.assert_allclose(summary.median, [6.5, 6.5, 2.5])
    np.testing.assert_allclose(summary.q1, [5.75, 5.75, 1.75])
    np.testing.assert_allclose(summary.q3, [7.25, 7.25, 3.25])
    np.testing.assert_allclose(summary.iqr, [1.5, 1.5, 1.5])


def test_terminal_summary_is_derived_from_saved_runs(existing_results: tuple[AlgorithmResults, ...]) -> None:
    rows = algorithm_summary_rows(existing_results)
    by_algorithm = {str(row["algorithm"]): row for row in rows}
    assert by_algorithm["Random Search"]["best_seed"] == 2
    assert by_algorithm["Differential Evolution"]["best_seed"] == 3
    assert by_algorithm["Genetic Algorithm"]["best_seed"] == 2
    assert float(by_algorithm["Random Search"]["best_J"]) == pytest.approx(0.5841852495274906)
    assert float(by_algorithm["Differential Evolution"]["median_J"]) == pytest.approx(0.3818430194775517)
    assert float(by_algorithm["Genetic Algorithm"]["worst_J"]) == pytest.approx(0.4180227137750425)


def test_generates_all_figures_and_table_without_changing_source_csvs(
    existing_results: tuple[AlgorithmResults, ...],
    tmp_path: Path,
) -> None:
    source_csvs = sorted(
        path
        for result in existing_results
        for path in result.spec.directory.glob("*.csv")
    )
    hashes_before = {path: _sha256(path) for path in source_csvs}
    temporary_results = tuple(
        replace(
            result,
            spec=replace(result.spec, directory=tmp_path / result.spec.directory.name),
        )
        for result in existing_results
    )
    comparisons = tmp_path / "comparisons"
    written = regenerate_benchmark_figures(temporary_results, comparisons, save_vector=False)

    expected = {
        *(result.spec.directory / "best_fit.png" for result in temporary_results),
        *(result.spec.directory / "convergence.png" for result in temporary_results),
        comparisons / "best_fits_comparison.png",
        comparisons / "convergence_linear.png",
        comparisons / "convergence_logx.png",
        comparisons / "convergence_final_zoom.png",
        comparisons / "current_algorithm_summary.csv",
    }
    assert expected == set(written)
    assert all(path.is_file() and path.stat().st_size > 0 for path in expected)
    assert not should_plot_log_y(
        tuple(
            calculate_convergence_summary(result, next(iter(result.histories.values())).evaluations)
            for result in existing_results
        )
    )

    best_fit_shapes = {
        mpimg.imread(result.spec.directory / "best_fit.png").shape
        for result in temporary_results
    }
    assert len(best_fit_shapes) == 1
    with (comparisons / "current_algorithm_summary.csv").open(newline="", encoding="utf-8") as handle:
        table = list(csv.DictReader(handle))
    assert len(table) == 3
    assert set(table[0]) >= {
        "algorithm", "n_seeds", "budget", "best_J", "median_J", "worst_J",
        "Q1_J", "Q3_J", "IQR_J", "best_seed", "best_J_T", "best_J_R",
    }
    assert hashes_before == {path: _sha256(path) for path in source_csvs}
