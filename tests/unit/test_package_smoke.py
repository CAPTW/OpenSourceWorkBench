"""Smoke tests for the initial OSW package skeleton."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


def _python_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)
    return env


def test_package_exports_version() -> None:
    sys.path.insert(0, str(SRC_ROOT))

    import osw

    assert osw.__version__ == "0.1.0a0"


def test_cli_version_smoke() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "osw.cli", "--version"],
        cwd=REPO_ROOT,
        env=_python_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "osw 0.1.0a0"


def test_cli_doctor_smoke() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "osw.cli", "doctor"],
        cwd=REPO_ROOT,
        env=_python_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "OSW doctor" in result.stdout
    assert "python:" in result.stdout
    assert "external solver execution: disabled" in result.stdout
