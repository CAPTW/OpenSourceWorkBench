from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PYPROJECT = REPO_ROOT / "pyproject.toml"


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


def test_ci_workflow_uses_exact_shared_ruff_toolchain_contract() -> None:
    config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    dev_dependencies = config["project"]["optional-dependencies"]["dev"]
    ruff_dependencies = [
        dependency
        for dependency in dev_dependencies
        if dependency.strip().lower().startswith("ruff")
    ]
    ruff_config = config["tool"]["ruff"]
    lint_config = ruff_config["lint"]
    required_version = ruff_config.get("required-version")
    workflow_text = CI_WORKFLOW.read_text(encoding="utf-8")
    problems: list[str] = []

    if ruff_dependencies != ["ruff==0.14.14"]:
        problems.append(
            "dev extra must contain only ruff==0.14.14; "
            f"found {ruff_dependencies!r}"
        )
    if required_version != "==0.14.14":
        problems.append(
            "tool.ruff.required-version must be ==0.14.14; "
            f"found {required_version!r}"
        )
    if isinstance(required_version, str):
        if ruff_dependencies != [f"ruff{required_version}"]:
            problems.append("Ruff dependency and runtime guard must name the same exact version")
    else:
        problems.append("Ruff dependency and runtime guard cannot be compared without the guard")

    if ruff_config["target-version"] != "py311":
        problems.append("tool.ruff.target-version must remain py311")
    if lint_config["select"] != ["E", "F", "I", "UP", "B"]:
        problems.append("tool.ruff.lint.select changed from the approved rule set")

    ignored_rules = [
        *lint_config.get("ignore", []),
        *lint_config.get("extend-ignore", []),
    ]
    per_file_ignored_rules = [
        rule
        for rules in lint_config.get("per-file-ignores", {}).values()
        for rule in rules
    ]
    if "UP042" in ignored_rules or "UP042" in per_file_ignored_rules:
        problems.append("UP042 must not be ignored globally or per file")
    if ruff_config.get("preview", False) or lint_config.get("preview", False):
        problems.append("Ruff preview mode must remain disabled")

    if workflow_text.count('python -m pip install -e ".[dev]"') != 2:
        problems.append("both CI jobs must install the shared .[dev] dependency authority")
    lowered_workflow = workflow_text.lower()
    if "pip install ruff" in lowered_workflow or "ruff==" in lowered_workflow:
        problems.append("CI must not install a workflow-specific Ruff version")
    if "--constraint" in lowered_workflow:
        problems.append("CI must not introduce an alternate constraints authority")

    assert not problems, "\n".join(problems)


def test_external_solver_marker_is_registered_and_documented() -> None:
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "external_solver: requires a local external solver" in pyproject
    assert 'pytest tests/integration -q -m "not external_solver"' in readme
    assert "pytest tests/integration -q -m external_solver" in readme
