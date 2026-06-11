from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from osw.experimental.feaspec import plan_calculix_case_from_feaspec

REPO_ROOT = Path(__file__).resolve().parents[2]
CASE_PLAN_SOURCE = (
    REPO_ROOT / "src" / "osw" / "experimental" / "feaspec" / "calculix_case_plan.py"
)
DIAGNOSTICS_SOURCE = (
    REPO_ROOT / "src" / "osw" / "experimental" / "feaspec" / "calculix_diagnostics.py"
)
PROJECT_SCHEMA = REPO_ROOT / "src" / "osw" / "core" / "project_schema.py"
CASE_PLAN_DOC = REPO_ROOT / "docs" / "experimental" / "feaspec_to_calculix_case_plan_model.md"
EXAMPLES = REPO_ROOT / "examples" / "feaspec"


def _case_plan_source() -> str:
    return CASE_PLAN_SOURCE.read_text(encoding="utf-8")


def test_case_plan_does_not_write_files(tmp_path: Path) -> None:
    payload = json.loads((EXAMPLES / "cantilever_beam_approved.json").read_text(encoding="utf-8"))

    plan = plan_calculix_case_from_feaspec(payload)

    assert plan.ready_for_solver_execution is False
    assert list(tmp_path.iterdir()) == []


def test_case_plan_does_not_import_command_gui_solver_or_network_modules() -> None:
    tree = ast.parse(_case_plan_source())
    forbidden_roots = {
        "osw.gui",
        "osw.solvers",
        "osw.runners",
        "subprocess",
        "socket",
        "requests",
        "httpx",
        "urllib",
        "openai",
        "anthropic",
        "google.generativeai",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [node.module or ""]
        else:
            continue
        for module in modules:
            assert not any(
                module == root or module.startswith(f"{root}.")
                for root in forbidden_roots
            )


def test_case_plan_does_not_introduce_writer_export_or_command_helpers() -> None:
    text = _case_plan_source()
    forbidden_function_patterns = (
        r"def\s+write_",
        r"def\s+export_",
        r"def\s+generate_.*deck",
        r"def\s+run_",
        r"def\s+execute_",
        r"def\s+call_",
    )
    for pattern in forbidden_function_patterns:
        assert re.search(pattern, text) is None


def test_case_plan_does_not_add_vlm_api_or_credentials() -> None:
    combined = (
        _case_plan_source().lower()
        + "\n"
        + DIAGNOSTICS_SOURCE.read_text(encoding="utf-8").lower()
    )
    forbidden_tokens = (
        "openai_api_key",
        "anthropic_api_key",
        "gemini_api_key",
        "api_key",
        "credentials",
        "vlmprovider",
    )
    for token in forbidden_tokens:
        assert token not in combined


def test_case_plan_does_not_mutate_project_schema_source() -> None:
    text = PROJECT_SCHEMA.read_text(encoding="utf-8")

    assert "FEASpecCalculiXCasePlan" not in text
    assert "CalculiXCaseStatus" not in text


def test_case_plan_docs_avoid_forbidden_positive_claims() -> None:
    text = CASE_PLAN_DOC.read_text(encoding="utf-8").lower()
    forbidden_claims = (
        "inp writer exists",
        "calculix export exists",
        "solver execution exists",
        "ccx validation passed",
        "abaqus export exists",
        "vfea implementation is complete",
        "automatic solver execution is allowed",
        "industrial certification is provided",
        "stable production",
    )
    for claim in forbidden_claims:
        assert claim not in text
