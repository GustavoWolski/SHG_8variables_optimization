"""Checks de infraestrutura; não exercitam equações ou otimização."""

from pathlib import Path


def test_required_project_directories_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    for relative_path in (
        "src/physics",
        "src/optimization",
        "src/experiments",
        "src/analysis",
        "tests",
        "results",
        "notebooks",
    ):
        assert (root / relative_path).is_dir()
