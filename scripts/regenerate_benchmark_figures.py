"""Regenerate standardized benchmark figures strictly from saved artifacts."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis.plotting import (  # noqa: E402
    default_algorithm_specs,
    load_benchmarks,
    regenerate_benchmark_figures,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_csv_hashes(directories: list[Path]) -> dict[Path, str]:
    return {
        path: _sha256(path)
        for directory in directories
        for path in sorted(directory.glob("*.csv"))
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-root",
        type=Path,
        default=ROOT / "results",
        help="Root containing the saved benchmark directories.",
    )
    parser.add_argument(
        "--no-vector",
        action="store_true",
        help="Skip PDF companions (useful only for a quick local smoke test).",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    specs = default_algorithm_specs(arguments.results_root)
    source_hashes = _source_csv_hashes([spec.directory for spec in specs])
    results = load_benchmarks(specs)
    written = regenerate_benchmark_figures(
        results,
        arguments.results_root / "comparisons",
        save_vector=not arguments.no_vector,
    )
    after_hashes = _source_csv_hashes([spec.directory for spec in specs])
    if source_hashes != after_hashes:
        raise RuntimeError("A source benchmark CSV changed during figure regeneration.")

    for result in results:
        best = result.best_run
        print(
            f"loaded={result.spec.name!r} seeds={len(result.runs)} budget={result.budget} "
            f"best_J={best.best_J:.17g} best_seed={best.seed}"
        )
    print(f"written_artifacts={len(written)}")
    print("source_benchmark_csv_sha256=UNCHANGED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
