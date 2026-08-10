"""Smoke test: the harness runs before any application code exists."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_pytest_reads_project_configuration() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "pytest" in config["tool"]
    assert config["tool"]["ruff"]["line-length"] == 100
