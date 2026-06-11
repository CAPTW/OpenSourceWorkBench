from __future__ import annotations

import ast
import json
from pathlib import Path

from osw.experimental.feaspec import (
    DiagnosticCode,
    ValidationState,
    dump_feaspec,
    explain_diagnostics,
    load_feaspec,
    validate_feaspec,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples" / "feaspec"
VALIDATOR_SOURCE = REPO_ROOT / "src" / "osw" / "experimental" / "feaspec" / "validator.py"
IMPLEMENTATION_DOC = REPO_ROOT / "docs" / "experimental" / "feaspec_validator_implementation.md"


def _load_example(name: str) -> dict[str, object]:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def _codes(report) -> set[DiagnosticCode]:  # type: ignore[no-untyped-def]
    return report.diagnostic_codes


def test_validate_feaspec_imports_and_returns_report() -> None:
    report = validate_feaspec(EXAMPLES / "cantilever_beam_candidate.json")

    assert report.diagnostics
    assert report.validation_state in {ValidationState.INVALID, ValidationState.VALID_WITH_WARNINGS}


def test_approved_cantilever_example_has_no_blockers() -> None:
    report = validate_feaspec(EXAMPLES / "cantilever_beam_approved.json")

    assert report.validation_state is ValidationState.APPROVED
    assert not report.has_blockers
    assert not report.has_errors
    assert report.can_be_approved
    assert not report.can_handoff_to_solver


def test_approved_truss_example_has_no_blockers() -> None:
    report = validate_feaspec(EXAMPLES / "truss_2d_approved.json")

    assert report.validation_state is ValidationState.APPROVED
    assert not report.has_blockers
    assert not report.has_errors


def test_candidate_examples_are_not_solver_ready() -> None:
    for filename in (
        "cantilever_beam_candidate.json",
        "truss_2d_candidate.json",
        "plate_with_hole_candidate.json",
    ):
        report = validate_feaspec(EXAMPLES / filename)
        assert not report.can_handoff_to_solver
        assert DiagnosticCode.FS_REVIEW_MISSING in _codes(report)


def test_invalid_missing_units_emits_units_or_load_units_diagnostic() -> None:
    report = validate_feaspec(EXAMPLES / "invalid_missing_units.json")

    assert not report.is_valid
    assert _codes(report) & {
        DiagnosticCode.FS_UNITS_MISSING_SYSTEM,
        DiagnosticCode.FS_UNITS_AMBIGUOUS,
        DiagnosticCode.FS_LOAD_MISSING_UNITS,
    }


def test_invalid_unconnected_graph_emits_geometry_diagnostic() -> None:
    report = validate_feaspec(EXAMPLES / "invalid_unconnected_graph.json")

    assert DiagnosticCode.FS_GEOM_DISCONNECTED_GRAPH in _codes(report)


def test_invalid_load_target_emits_load_target_diagnostic() -> None:
    report = validate_feaspec(EXAMPLES / "invalid_load_target.json")

    assert DiagnosticCode.FS_LOAD_INVALID_TARGET in _codes(report)


def test_approved_spec_without_human_review_is_blocked() -> None:
    payload = _load_example("cantilever_beam_approved.json")
    payload.pop("human_review")

    report = validate_feaspec(payload, require_approval=True)

    assert report.has_blockers
    assert DiagnosticCode.FS_REVIEW_MISSING in _codes(report)


def test_approved_spec_with_unapproved_validation_state_is_blocked() -> None:
    payload = _load_example("cantilever_beam_approved.json")
    payload["validation"]["state"] = "valid-with-warnings"  # type: ignore[index]

    report = validate_feaspec(payload, require_approval=True)

    assert report.has_blockers
    assert DiagnosticCode.FS_REVIEW_NOT_APPROVED in _codes(report)


def test_missing_material_and_load_units_are_reported() -> None:
    payload = _load_example("cantilever_beam_approved.json")
    payload["materials"] = []  # type: ignore[index]
    payload["loads"][0]["magnitude"] = {"value": 5.0}  # type: ignore[index]

    report = validate_feaspec(payload)

    assert DiagnosticCode.FS_MATERIAL_MISSING in _codes(report)
    assert DiagnosticCode.FS_LOAD_MISSING_UNITS in _codes(report)


def test_explain_diagnostics_returns_user_readable_strings() -> None:
    report = validate_feaspec(EXAMPLES / "invalid_load_target.json")

    explanations = explain_diagnostics(report)

    assert explanations
    assert any("FS_LOAD_INVALID_TARGET" in item for item in explanations)


def test_round_trip_dump_load_examples_still_work(tmp_path: Path) -> None:
    spec = load_feaspec(EXAMPLES / "cantilever_beam_approved.json")
    output_path = tmp_path / "round_trip.json"

    dump_feaspec(spec, output_path)
    restored = load_feaspec(output_path)

    assert restored.to_dict()["schema_version"] == spec.to_dict()["schema_version"]


def test_validator_does_not_import_gui_solver_network_or_provider_modules() -> None:
    tree = ast.parse(VALIDATOR_SOURCE.read_text(encoding="utf-8"))
    forbidden_roots = {
        "osw.gui",
        "osw.solvers",
        "osw.core.project_schema",
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


def test_validator_does_not_execute_commands() -> None:
    tree = ast.parse(VALIDATOR_SOURCE.read_text(encoding="utf-8"))
    forbidden_calls = {"run", "Popen", "system", "spawn", "execve"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            name = func.attr
        elif isinstance(func, ast.Name):
            name = func.id
        else:
            name = ""
        assert name not in forbidden_calls


def test_validator_implementation_doc_preserves_non_goals() -> None:
    text = IMPLEMENTATION_DOC.read_text(encoding="utf-8").lower()

    assert "no full projectschema persistence" in text
    assert "schema mutation" in text
    assert "no vlm api" in text
    assert "no solver execution" in text
    assert "no topology optimization implementation" in text
    assert "no industrial certification" in text
    for forbidden_claim in (
        "vfea is implemented",
        "full projectschema persistence is implemented",
        "projectschema mutation is implemented",
        "solver execution is implemented",
        "abaqus is mandatory",
        "industrial certification is provided",
    ):
        assert forbidden_claim not in text
