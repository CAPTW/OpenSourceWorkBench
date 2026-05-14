from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_workflow_yaml_parses_when_pyyaml_is_available() -> None:
    yaml = pytest.importorskip("yaml")

    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))

    assert isinstance(workflow, dict)
    assert "jobs" in workflow
    assert "local-safe-qa" in workflow["jobs"]


def test_ci_workflow_runs_local_safe_default_checks() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")

    assert 'OSW_EXTERNAL_SOLVER_TESTS: "0"' in text
    assert "python -m pip install -e \".[dev]\"" in text
    assert "python -m osw.cli doctor" in text
    assert "ruff check src tests" in text
    assert "pytest tests/unit -q" in text
    assert 'pytest tests/integration -q -m "not external_solver"' in text
    assert "pytest tests/golden -q" in text
    assert "pytest tests/validation -q" in text
    assert "python tools/qa/run_fast_qa.py" in text
    assert "python tools/qa/check_scope_drift.py" in text
    assert "python tools/qa/check_architecture_boundaries.py" in text
    assert "python tools/qa/check_no_solver_artifacts_committed.py" in text
    assert "tools/qa/check_docs_links.py is not present" in text
    assert "License notice placeholder passed" in text
    assert "OSW_RUN_TYPE_CHECK is not set to 1; optional type check skipped" in text
    assert "mypy is not installed; optional type check skipped" in text


def test_external_solver_marker_is_registered_and_documented() -> None:
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "external_solver: requires a local external solver" in pyproject
    assert 'pytest tests/integration -q -m "not external_solver"' in readme
    assert "pytest tests/integration -q -m external_solver" in readme
