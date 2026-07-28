"""Smoke tests for the initial OSW package skeleton."""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
EXPECTED_VERSION = "0.1.5rc1"


def _python_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)
    return env


def _pyproject() -> dict[str, object]:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _has_requirement(requirements: list[str], package_name: str) -> bool:
    normalized = package_name.lower()
    return any(requirement.lower().startswith(normalized) for requirement in requirements)


def test_package_exports_version() -> None:
    sys.path.insert(0, str(SRC_ROOT))

    import osw

    assert osw.__version__ == EXPECTED_VERSION


def test_cli_version_smoke() -> None:
    result = subprocess.run(
        [sys.executable, "-B", "-m", "osw.cli", "--version"],
        cwd=REPO_ROOT,
        env=_python_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"osw {EXPECTED_VERSION}"


def test_cli_doctor_smoke() -> None:
    result = subprocess.run(
        [sys.executable, "-B", "-m", "osw.cli", "doctor"],
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


def test_cli_doctor_reports_packaging_extras() -> None:
    result = subprocess.run(
        [sys.executable, "-B", "-m", "osw.cli", "doctor"],
        cwd=REPO_ROOT,
        env=_python_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "PySide6 (gui):" in result.stdout
    assert "pyvista (viz):" in result.stdout
    assert "meshio (mesh):" in result.stdout
    assert "hdf5storage (mscript):" in result.stdout
    assert "cantera (chm):" in result.stdout
    assert "CoolProp (chm):" in result.stdout


def test_pyproject_base_install_is_lightweight() -> None:
    project = _pyproject()["project"]

    assert project["requires-python"] == ">=3.11"
    assert project.get("dependencies", []) == []


def test_pyproject_optional_extras_cover_v0_1_stacks() -> None:
    extras = _pyproject()["project"]["optional-dependencies"]

    assert {"gui", "viz", "mesh", "mscript", "chm", "dev", "all"} <= set(extras)
    assert _has_requirement(extras["gui"], "PySide6")
    assert _has_requirement(extras["viz"], "pyvista")
    assert extras["viz"].count("pyvistaqt>=0.12.0") == 1
    assert _has_requirement(extras["viz"], "matplotlib")
    assert _has_requirement(extras["mesh"], "meshio")
    assert _has_requirement(extras["mesh"], "gmsh")
    assert _has_requirement(extras["mscript"], "scipy")
    assert _has_requirement(extras["mscript"], "hdf5storage")
    assert _has_requirement(extras["chm"], "cantera")
    assert _has_requirement(extras["chm"], "CoolProp")


def test_pyvistaqt_is_optional_unique_and_not_installed_by_workflows() -> None:
    project = _pyproject()["project"]
    extras = project["optional-dependencies"]
    all_requirements = [
        requirement
        for requirements in extras.values()
        for requirement in requirements
    ]

    assert project.get("dependencies", []) == []
    assert all_requirements.count("pyvistaqt>=0.12.0") == 1

    workflow_root = REPO_ROOT / ".github" / "workflows"
    workflow_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(workflow_root.glob("*.yml"))
    )
    assert "pyvistaqt" not in workflow_text.lower()
