"""Shared, publication-oriented plotting for saved optimization benchmarks.

This module is deliberately read-only with respect to benchmark CSV files.  It
loads saved runs and best-so-far histories, validates their internal
consistency, and writes only derived figures and comparison tables.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterable, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import EngFormatter
from numpy.typing import NDArray

from experiments.data import D_NM, R_EXP, T_EXP


FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]

PNG_DPI: Final[int] = 320
BEST_FIT_MARGIN_FRACTION: Final[float] = 0.05
FINAL_ZOOM_FRACTION: Final[float] = 0.20

EXPERIMENTAL_COLOR: Final[str] = "#333333"
MODEL_COLOR: Final[str] = "#0072B2"

# Okabe-Ito-derived, color-vision-deficiency-friendly semantic mapping.
ALGORITHM_COLORS: Final[dict[str, str]] = {
    "Random Search": "#E69F00",
    "Differential Evolution": "#0072B2",
    "Genetic Algorithm": "#009E73",
    "Particle Swarm Optimization": "#CC79A7",
    "CMA-ES": "#D55E00",
}

PLOT_RC_PARAMS: Final[dict[str, object]] = {
    "font.family": "DejaVu Sans",
    "font.size": 9.5,
    "axes.titlesize": 10.5,
    "axes.labelsize": 9.5,
    "axes.linewidth": 0.8,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "legend.frameon": False,
    "lines.linewidth": 1.8,
    "lines.markersize": 4.8,
    "grid.color": "#B8B8B8",
    "grid.linewidth": 0.55,
    "grid.alpha": 0.35,
    "savefig.dpi": PNG_DPI,
    "savefig.bbox": "tight",
}


@dataclass(frozen=True)
class AlgorithmSpec:
    """Display metadata and artifact directory for one algorithm."""

    name: str
    short_name: str
    directory: Path
    color: str


@dataclass(frozen=True)
class BenchmarkRun:
    """One saved terminal result, parsed from ``runs.csv``."""

    seed: int
    budget: int
    n_evaluations: int
    best_J: float
    best_J_T: float
    best_J_R: float
    best_p: FloatArray
    T_theoretical: FloatArray
    R_theoretical: FloatArray


@dataclass(frozen=True)
class ConvergenceHistory:
    """Best-so-far history for one seed."""

    seed: int
    evaluations: IntArray
    best_J: FloatArray


@dataclass(frozen=True)
class AlgorithmResults:
    """All saved data required to analyze one algorithm."""

    spec: AlgorithmSpec
    runs: tuple[BenchmarkRun, ...]
    histories: Mapping[int, ConvergenceHistory]

    @property
    def budget(self) -> int:
        return self.runs[0].budget

    @property
    def best_run(self) -> BenchmarkRun:
        return min(self.runs, key=lambda run: run.best_J)


@dataclass(frozen=True)
class BestFitAxisLimits:
    """Shared limits that make all best-fit panels directly comparable."""

    x: tuple[float, float]
    transmission: tuple[float, float]
    reflection: tuple[float, float]


@dataclass(frozen=True)
class ConvergenceSummary:
    """Pointwise median and interquartile band on a common evaluation grid."""

    algorithm: str
    color: str
    evaluations: IntArray
    median: FloatArray
    q1: FloatArray
    q3: FloatArray

    @property
    def iqr(self) -> FloatArray:
        return self.q3 - self.q1


def default_algorithm_specs(results_root: Path) -> tuple[AlgorithmSpec, ...]:
    """Return the centralized registry of current benchmark artifacts."""

    # Version 1 used historical ``*_baseline`` directory names. Version 2
    # intentionally uses concise algorithm names below ``search_space_v2``.
    # Select by the artifact layout so figure regeneration remains read-only.
    random_search_directory = results_root / "random_search"
    differential_evolution_directory = results_root / "differential_evolution"
    genetic_algorithm_directory = results_root / "genetic_algorithm"
    if not random_search_directory.is_dir():
        random_search_directory = results_root / "random_search_baseline"
        differential_evolution_directory = results_root / "differential_evolution_baseline"
        genetic_algorithm_directory = results_root / "genetic_algorithm_baseline"

    specifications: list[AlgorithmSpec] = [
        AlgorithmSpec(
            "Random Search",
            "RS",
            random_search_directory,
            ALGORITHM_COLORS["Random Search"],
        ),
        AlgorithmSpec(
            "Differential Evolution",
            "DE",
            differential_evolution_directory,
            ALGORITHM_COLORS["Differential Evolution"],
        ),
        AlgorithmSpec(
            "Genetic Algorithm",
            "GA",
            genetic_algorithm_directory,
            ALGORITHM_COLORS["Genetic Algorithm"],
        ),
    ]
    particle_swarm_directory = results_root / "particle_swarm"
    if particle_swarm_directory.is_dir():
        specifications.append(
            AlgorithmSpec(
                "Particle Swarm Optimization",
                "PSO",
                particle_swarm_directory,
                ALGORITHM_COLORS["Particle Swarm Optimization"],
            )
        )
    return tuple(specifications)


def _read_dict_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Required benchmark artifact does not exist: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Benchmark artifact is empty: {path}")
    return rows


def _require_columns(rows: Sequence[Mapping[str, str]], required: set[str], path: Path) -> None:
    missing = required.difference(rows[0])
    if missing:
        raise ValueError(f"Missing columns in {path}: {sorted(missing)}")


def _json_float_array(value: str, field: str, path: Path) -> FloatArray:
    try:
        array = np.asarray(json.loads(value), dtype=np.float64)
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise ValueError(f"Invalid JSON float array in {field} of {path}") from error
    if array.ndim != 1 or not np.all(np.isfinite(array)):
        raise ValueError(f"{field} must be a finite one-dimensional array in {path}")
    return array


def load_algorithm_results(spec: AlgorithmSpec) -> AlgorithmResults:
    """Load and validate one benchmark without modifying any source artifact."""

    runs_path = spec.directory / "runs.csv"
    history_path = spec.directory / "convergence_history.csv"
    run_rows = _read_dict_rows(runs_path)
    _require_columns(
        run_rows,
        {
            "seed",
            "budget",
            "n_evaluations",
            "best_J",
            "best_J_T",
            "best_J_R",
            "best_p",
            "T_theoretical",
            "R_theoretical",
        },
        runs_path,
    )

    runs: list[BenchmarkRun] = []
    for row in run_rows:
        run = BenchmarkRun(
            seed=int(row["seed"]),
            budget=int(row["budget"]),
            n_evaluations=int(row["n_evaluations"]),
            best_J=float(row["best_J"]),
            best_J_T=float(row["best_J_T"]),
            best_J_R=float(row["best_J_R"]),
            best_p=_json_float_array(row["best_p"], "best_p", runs_path),
            T_theoretical=_json_float_array(row["T_theoretical"], "T_theoretical", runs_path),
            R_theoretical=_json_float_array(row["R_theoretical"], "R_theoretical", runs_path),
        )
        if run.budget <= 0 or run.n_evaluations != run.budget:
            raise ValueError(f"Seed {run.seed} has an inconsistent physical-evaluation budget in {runs_path}")
        if run.best_p.size != 8:
            raise ValueError(f"Seed {run.seed} does not contain eight physical parameters in {runs_path}")
        if run.T_theoretical.size != D_NM.size or run.R_theoretical.size != D_NM.size:
            raise ValueError(f"Seed {run.seed} curve length differs from experimental data in {runs_path}")
        if not np.isclose(run.best_J, run.best_J_T + run.best_J_R, rtol=1e-12, atol=1e-14):
            raise ValueError(f"Seed {run.seed} has inconsistent J components in {runs_path}")
        runs.append(run)

    seeds = [run.seed for run in runs]
    if len(seeds) != len(set(seeds)):
        raise ValueError(f"Duplicate seeds in {runs_path}")
    if len({run.budget for run in runs}) != 1:
        raise ValueError(f"All seeds must use the same physical-evaluation budget in {runs_path}")

    history_rows = _read_dict_rows(history_path)
    _require_columns(history_rows, {"seed", "evaluation", "best_J"}, history_path)
    grouped: dict[int, list[tuple[int, float]]] = {}
    for row in history_rows:
        grouped.setdefault(int(row["seed"]), []).append((int(row["evaluation"]), float(row["best_J"])))

    histories: dict[int, ConvergenceHistory] = {}
    run_by_seed = {run.seed: run for run in runs}
    if set(grouped) != set(run_by_seed):
        raise ValueError(f"Seeds in runs and convergence history differ for {spec.name}")
    for seed, records in grouped.items():
        records.sort(key=lambda item: item[0])
        evaluations = np.asarray([item[0] for item in records], dtype=np.int64)
        values = np.asarray([item[1] for item in records], dtype=np.float64)
        run = run_by_seed[seed]
        if evaluations[0] < 1 or evaluations[-1] != run.budget or np.any(np.diff(evaluations) <= 0):
            raise ValueError(f"Seed {seed} has an invalid evaluation grid in {history_path}")
        if not np.all(np.isfinite(values)) or np.any(np.diff(values) > 1e-12):
            raise ValueError(f"Seed {seed} is not a finite best-so-far history in {history_path}")
        if not np.isclose(values[-1], run.best_J, rtol=1e-12, atol=1e-14):
            raise ValueError(f"Seed {seed} terminal history value differs from runs.csv")
        histories[seed] = ConvergenceHistory(seed, evaluations, values)

    return AlgorithmResults(spec=spec, runs=tuple(runs), histories=histories)


def load_benchmarks(specs: Iterable[AlgorithmSpec]) -> tuple[AlgorithmResults, ...]:
    """Load an arbitrary collection of algorithms in the requested display order."""

    results = tuple(load_algorithm_results(spec) for spec in specs)
    if not results:
        raise ValueError("At least one algorithm is required.")
    return results


def _padded_bounds(
    values: Iterable[FloatArray],
    margin_fraction: float = BEST_FIT_MARGIN_FRACTION,
    *,
    nonnegative: bool = False,
) -> tuple[float, float]:
    concatenated = np.concatenate([np.ravel(value) for value in values])
    finite = concatenated[np.isfinite(concatenated)]
    if finite.size == 0:
        raise ValueError("Cannot derive limits from an empty or non-finite collection.")
    minimum = float(np.min(finite))
    maximum = float(np.max(finite))
    span = maximum - minimum
    if span == 0.0:
        span = max(abs(maximum), 1.0)
    margin = margin_fraction * span
    lower = minimum - margin
    if nonnegative:
        lower = max(0.0, lower)
    return lower, maximum + margin


def determine_best_fit_axis_limits(results: Sequence[AlgorithmResults]) -> BestFitAxisLimits:
    """Use experimental data and all current best curves, with a 5% range margin."""

    transmission = [T_EXP, *(result.best_run.T_theoretical for result in results)]
    reflection = [R_EXP, *(result.best_run.R_theoretical for result in results)]
    return BestFitAxisLimits(
        x=_padded_bounds([D_NM], nonnegative=True),
        transmission=_padded_bounds(transmission, nonnegative=True),
        reflection=_padded_bounds(reflection, nonnegative=True),
    )


def align_stepwise_histories(
    histories: Sequence[ConvergenceHistory],
    common_evaluations: IntArray,
) -> FloatArray:
    """Forward-fill best-so-far values on a common grid without interpolation."""

    grid = np.asarray(common_evaluations, dtype=np.int64)
    if grid.ndim != 1 or grid.size == 0 or np.any(np.diff(grid) <= 0) or grid[0] < 1:
        raise ValueError("common_evaluations must be a positive, strictly increasing vector.")
    aligned = np.full((len(histories), grid.size), np.nan, dtype=np.float64)
    for row_index, history in enumerate(histories):
        source_evaluations = np.asarray(history.evaluations, dtype=np.int64)
        source_values = np.asarray(history.best_J, dtype=np.float64)
        if source_evaluations.size != source_values.size or source_evaluations.size == 0:
            raise ValueError(f"Seed {history.seed} has inconsistent history arrays.")
        indices = np.searchsorted(source_evaluations, grid, side="right") - 1
        available = indices >= 0
        aligned[row_index, available] = source_values[indices[available]]
    return aligned


def common_evaluation_grid(results: Sequence[AlgorithmResults]) -> IntArray:
    """Build the union grid up to the smallest complete budget."""

    if not results:
        raise ValueError("At least one algorithm is required.")
    common_budget = min(result.budget for result in results)
    evaluations: list[IntArray] = [np.asarray([1, common_budget], dtype=np.int64)]
    for result in results:
        for history in result.histories.values():
            evaluations.append(history.evaluations[history.evaluations <= common_budget])
    return np.unique(np.concatenate(evaluations)).astype(np.int64, copy=False)


def calculate_convergence_summary(
    result: AlgorithmResults,
    common_evaluations: IntArray,
) -> ConvergenceSummary:
    """Calculate pointwise median, Q1 and Q3 across aligned seeds."""

    histories = [result.histories[run.seed] for run in result.runs]
    aligned = align_stepwise_histories(histories, common_evaluations)
    if np.any(np.all(np.isnan(aligned), axis=0)):
        raise ValueError(f"The common evaluation grid precedes every history for {result.spec.name}.")
    median = np.nanmedian(aligned, axis=0)
    q1, q3 = np.nanpercentile(aligned, [25.0, 75.0], axis=0)
    return ConvergenceSummary(
        algorithm=result.spec.name,
        color=result.spec.color,
        evaluations=np.asarray(common_evaluations, dtype=np.int64),
        median=np.asarray(median, dtype=np.float64),
        q1=np.asarray(q1, dtype=np.float64),
        q3=np.asarray(q3, dtype=np.float64),
    )


def calculate_convergence_summaries(
    results: Sequence[AlgorithmResults],
) -> tuple[ConvergenceSummary, ...]:
    grid = common_evaluation_grid(results)
    return tuple(calculate_convergence_summary(result, grid) for result in results)


def _save_figure(figure: Figure, output_path: Path, *, save_vector: bool = True) -> tuple[Path, ...]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=PNG_DPI, facecolor="white")
    written = [output_path]
    if save_vector and output_path.suffix.lower() != ".pdf":
        pdf_path = output_path.with_suffix(".pdf")
        figure.savefig(
            pdf_path,
            facecolor="white",
            metadata={"Creator": "SHG benchmark plotting", "CreationDate": None, "ModDate": None},
        )
        written.append(pdf_path)
    plt.close(figure)
    return tuple(written)


def _draw_best_fit_panel(
    axis: Axes,
    experimental: FloatArray,
    theoretical: FloatArray,
    title: str,
    ylabel: str,
    limits: tuple[float, float],
) -> None:
    axis.plot(
        D_NM,
        experimental,
        linestyle="none",
        marker="o",
        markerfacecolor="white",
        markeredgecolor=EXPERIMENTAL_COLOR,
        markeredgewidth=1.2,
        color=EXPERIMENTAL_COLOR,
        label="Experimental",
        zorder=3,
    )
    axis.plot(
        D_NM,
        theoretical,
        linestyle="-",
        marker="s",
        color=MODEL_COLOR,
        label="Model",
        zorder=2,
    )
    axis.set(title=title, xlabel="Thickness (nm)", ylabel=ylabel)
    axis.set_ylim(*limits)
    axis.grid(True)
    axis.legend(loc="best")


def plot_best_fit(
    result: AlgorithmResults,
    output_path: Path,
    axis_limits: BestFitAxisLimits,
    *,
    save_vector: bool = True,
) -> tuple[Path, ...]:
    """Write the standard 1x2 best-fit layout for one algorithm."""

    best = result.best_run
    with plt.rc_context(PLOT_RC_PARAMS):
        figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.5), sharex=True, layout="constrained")
        _draw_best_fit_panel(
            axes[0], T_EXP, best.T_theoretical, "Transmission", "Normalized transmission", axis_limits.transmission
        )
        _draw_best_fit_panel(
            axes[1], R_EXP, best.R_theoretical, "Reflection", "Normalized reflection", axis_limits.reflection
        )
        for axis in axes:
            axis.set_xlim(*axis_limits.x)
        figure.suptitle(f"{result.spec.name} — Best fit\nJ = {best.best_J:.6f} | seed = {best.seed}")
        return _save_figure(figure, output_path, save_vector=save_vector)


def plot_best_fits_comparison(
    results: Sequence[AlgorithmResults],
    output_path: Path,
    axis_limits: BestFitAxisLimits,
    *,
    save_vector: bool = True,
) -> tuple[Path, ...]:
    """Write a dynamically sized N-algorithm by two-response comparison."""

    if not results:
        raise ValueError("At least one algorithm is required.")
    with plt.rc_context(PLOT_RC_PARAMS):
        figure, axes = plt.subplots(
            len(results),
            2,
            figsize=(10.8, 2.55 * len(results) + 0.8),
            sharex="col",
            sharey="col",
            squeeze=False,
            layout="constrained",
        )
        for row, result in enumerate(results):
            best = result.best_run
            for column, (experimental, theoretical, ylabel, limits) in enumerate(
                (
                    (T_EXP, best.T_theoretical, "Normalized transmission", axis_limits.transmission),
                    (R_EXP, best.R_theoretical, "Normalized reflection", axis_limits.reflection),
                )
            ):
                axis = axes[row, column]
                axis.plot(
                    D_NM,
                    experimental,
                    linestyle="none",
                    marker="o",
                    markerfacecolor="white",
                    markeredgecolor=EXPERIMENTAL_COLOR,
                    markeredgewidth=1.1,
                    color=EXPERIMENTAL_COLOR,
                    label="Experimental",
                    zorder=3,
                )
                axis.plot(D_NM, theoretical, "-s", color=MODEL_COLOR, label="Model", zorder=2)
                axis.set_xlim(*axis_limits.x)
                axis.set_ylim(*limits)
                axis.set_ylabel(ylabel)
                axis.grid(True)
                if row == len(results) - 1:
                    axis.set_xlabel("Thickness (nm)")
            axes[row, 0].annotate(
                result.spec.short_name,
                xy=(-0.23, 0.5),
                xycoords="axes fraction",
                ha="center",
                va="center",
                rotation=90,
                fontsize=10,
                fontweight="bold",
            )
            axes[row, 1].text(
                0.98,
                0.95,
                f"J = {best.best_J:.6f} | seed = {best.seed}",
                transform=axes[row, 1].transAxes,
                ha="right",
                va="top",
                fontsize=8,
            )
        axes[0, 0].set_title("Transmission")
        axes[0, 1].set_title("Reflection")
        handles, labels = axes[0, 0].get_legend_handles_labels()
        figure.legend(handles, labels, loc="outside lower center", ncol=2)
        figure.suptitle("Best-fit comparison")
        return _save_figure(figure, output_path, save_vector=save_vector)


def convergence_axis_limits(
    summaries: Sequence[ConvergenceSummary],
    *,
    x_window: tuple[int, int] | None = None,
) -> tuple[float, float]:
    """Derive a common J range from medians and IQR bounds with a 5% margin."""

    values: list[FloatArray] = []
    for summary in summaries:
        mask = np.ones(summary.evaluations.size, dtype=bool)
        if x_window is not None:
            mask = (summary.evaluations >= x_window[0]) & (summary.evaluations <= x_window[1])
        values.extend((summary.median[mask], summary.q1[mask], summary.q3[mask]))
    return _padded_bounds(values, nonnegative=True)


def budget_markers(budget: int) -> tuple[int, ...]:
    """Return restrained, reusable milestones, including 50k and future 100k."""

    canonical = (1_000, 5_000, 10_000, 25_000, 50_000, 100_000, 250_000, 500_000, 1_000_000)
    return tuple(marker for marker in canonical if marker <= budget)


def _format_budget(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:g}M"
    if value >= 1_000:
        return f"{value / 1_000:g}k"
    return str(value)


def plot_convergence(
    summaries: Sequence[ConvergenceSummary],
    output_path: Path,
    *,
    title: str,
    xscale: str = "linear",
    yscale: str = "linear",
    x_window: tuple[int, int] | None = None,
    y_limits: tuple[float, float] | None = None,
    save_vector: bool = True,
) -> tuple[Path, ...]:
    """Plot solid medians and shaded IQRs for any algorithm collection."""

    if not summaries:
        raise ValueError("At least one convergence summary is required.")
    if xscale not in {"linear", "log"}:
        raise ValueError("xscale must be 'linear' or 'log'.")
    if yscale not in {"linear", "log"}:
        raise ValueError("yscale must be 'linear' or 'log'.")
    common_budget = min(int(summary.evaluations[-1]) for summary in summaries)
    x_limits = x_window if x_window is not None else (1, common_budget)
    if xscale == "log" and x_limits[0] <= 0:
        raise ValueError("A logarithmic evaluation axis cannot include zero.")
    if y_limits is None:
        y_limits = convergence_axis_limits(summaries, x_window=x_window)

    with plt.rc_context(PLOT_RC_PARAMS):
        figure, axis = plt.subplots(figsize=(8.8, 5.2), layout="constrained")
        for summary in summaries:
            axis.plot(
                summary.evaluations,
                summary.median,
                color=summary.color,
                drawstyle="steps-post",
                label=summary.algorithm,
                zorder=3,
            )
            axis.fill_between(
                summary.evaluations,
                summary.q1,
                summary.q3,
                step="post",
                color=summary.color,
                alpha=0.18,
                linewidth=0,
                zorder=2,
            )
        for marker in budget_markers(common_budget):
            if x_limits[0] <= marker <= x_limits[1]:
                axis.axvline(marker, color="#777777", linestyle=":", linewidth=0.7, alpha=0.28, zorder=1)
                axis.text(
                    marker,
                    0.985,
                    _format_budget(marker),
                    transform=axis.get_xaxis_transform(),
                    ha="right",
                    va="top",
                    rotation=90,
                    fontsize=7,
                    color="#666666",
                )
        axis.set_xscale(xscale)
        axis.set_yscale(yscale)
        axis.set_xlim(*x_limits)
        axis.set_ylim(*y_limits)
        axis.set_xlabel("Physical evaluations")
        axis.set_ylabel("Best objective J")
        axis.set_title(title)
        axis.grid(True)
        axis.xaxis.set_major_formatter(EngFormatter(sep=""))
        axis.legend(title="Median (shaded band: IQR)", loc="best")
        return _save_figure(figure, output_path, save_vector=save_vector)


def final_zoom_window(summaries: Sequence[ConvergenceSummary]) -> tuple[int, int]:
    """Return the final 20% of the shared physical-evaluation budget."""

    budget = min(int(summary.evaluations[-1]) for summary in summaries)
    start = max(1, int(np.floor((1.0 - FINAL_ZOOM_FRACTION) * budget)) + 1)
    return start, budget


def should_plot_log_y(summaries: Sequence[ConvergenceSummary]) -> bool:
    """Use log-y only when the visible robust envelope spans at least 100x."""

    positive = np.concatenate(
        [np.concatenate((summary.q1, summary.median, summary.q3)) for summary in summaries]
    )
    positive = positive[positive > 0.0]
    return bool(positive.size and np.max(positive) / np.min(positive) >= 100.0)


SUMMARY_FIELDS: Final[tuple[str, ...]] = (
    "algorithm",
    "n_seeds",
    "budget",
    "best_J",
    "median_J",
    "worst_J",
    "Q1_J",
    "Q3_J",
    "IQR_J",
    "best_seed",
    "best_J_T",
    "best_J_R",
)


def algorithm_summary_rows(results: Sequence[AlgorithmResults]) -> list[dict[str, object]]:
    """Derive the requested terminal statistics directly from saved runs."""

    rows: list[dict[str, object]] = []
    for result in results:
        values = np.asarray([run.best_J for run in result.runs], dtype=np.float64)
        q1, q3 = np.percentile(values, [25.0, 75.0])
        best = result.best_run
        rows.append(
            {
                "algorithm": result.spec.name,
                "n_seeds": len(result.runs),
                "budget": result.budget,
                "best_J": float(np.min(values)),
                "median_J": float(np.median(values)),
                "worst_J": float(np.max(values)),
                "Q1_J": float(q1),
                "Q3_J": float(q3),
                "IQR_J": float(q3 - q1),
                "best_seed": best.seed,
                "best_J_T": best.best_J_T,
                "best_J_R": best.best_J_R,
            }
        )
    return rows


def write_algorithm_summary(results: Sequence[AlgorithmResults], output_path: Path) -> Path:
    """Write the derived one-row-per-algorithm comparison table."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for row in algorithm_summary_rows(results):
            writer.writerow(
                {
                    key: f"{value:.17g}" if isinstance(value, float) else value
                    for key, value in row.items()
                }
            )
    return output_path


def regenerate_benchmark_figures(
    results: Sequence[AlgorithmResults],
    comparisons_directory: Path,
    *,
    save_vector: bool = True,
) -> tuple[Path, ...]:
    """Regenerate every standardized artifact without running an optimizer."""

    if not results:
        raise ValueError("At least one algorithm is required.")
    written: list[Path] = []
    best_fit_limits = determine_best_fit_axis_limits(results)
    summaries = calculate_convergence_summaries(results)
    main_y_limits = convergence_axis_limits(summaries)

    for result, summary in zip(results, summaries, strict=True):
        written.extend(
            plot_best_fit(
                result,
                result.spec.directory / "best_fit.png",
                best_fit_limits,
                save_vector=save_vector,
            )
        )
        written.extend(
            plot_convergence(
                [summary],
                result.spec.directory / "convergence.png",
                title=f"{result.spec.name} — Convergence",
                y_limits=main_y_limits,
                save_vector=save_vector,
            )
        )

    written.extend(
        plot_best_fits_comparison(
            results,
            comparisons_directory / "best_fits_comparison.png",
            best_fit_limits,
            save_vector=save_vector,
        )
    )
    written.extend(
        plot_convergence(
            summaries,
            comparisons_directory / "convergence_linear.png",
            title="Algorithm convergence — full budget",
            y_limits=main_y_limits,
            save_vector=save_vector,
        )
    )
    written.extend(
        plot_convergence(
            summaries,
            comparisons_directory / "convergence_logx.png",
            title="Algorithm convergence — early phase",
            xscale="log",
            y_limits=main_y_limits,
            save_vector=save_vector,
        )
    )
    zoom_window = final_zoom_window(summaries)
    written.extend(
        plot_convergence(
            summaries,
            comparisons_directory / "convergence_final_zoom.png",
            title="Algorithm convergence — final 20% of budget",
            x_window=zoom_window,
            y_limits=convergence_axis_limits(summaries, x_window=zoom_window),
            save_vector=save_vector,
        )
    )
    if should_plot_log_y(summaries):
        log_y_path = comparisons_directory / "convergence_logy.png"
        positive = np.concatenate(
            [np.concatenate((summary.q1, summary.median, summary.q3)) for summary in summaries]
        )
        positive = positive[positive > 0.0]
        written.extend(
            plot_convergence(
                summaries,
                log_y_path,
                title="Algorithm convergence — logarithmic objective scale",
                yscale="log",
                y_limits=(float(np.min(positive) / 1.10), float(np.max(positive) * 1.10)),
                save_vector=save_vector,
            )
        )

    written.append(write_algorithm_summary(results, comparisons_directory / "current_algorithm_summary.csv"))
    return tuple(written)
