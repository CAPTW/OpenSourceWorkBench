from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / "optional_solver_manifest_schema_model.md"


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_manifest_schema_model_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_status_and_non_actions() -> None:
    text = _normalized()

    assert "experimental schema/model implemented" in text
    assert "no discovery implementation" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text
    assert "no cli command implementation" in text
    assert "no gui panel implementation" in text


def test_doc_lists_public_api() -> None:
    text = _read()

    for symbol in (
        "OptionalSolverManifest",
        "OptionalSolverRequirement",
        "OptionalSolverCapability",
        "OptionalSolverProbe",
        "OptionalSolverStackId",
        "OptionalSolverHealthState",
        "OptionalSolverSupportStatus",
        "OptionalSolverManifestDiagnostic",
        "OptionalSolverManifestValidationReport",
        "parse_optional_solver_manifest_dict",
        "validate_optional_solver_manifest",
        "load_optional_solver_manifest_json",
        "dump_optional_solver_manifest_json",
        "builtin_optional_solver_manifests",
        "get_builtin_optional_solver_manifest",
        "explain_optional_solver_manifest",
    ):
        assert symbol in text


def test_doc_lists_manifest_fields_and_builtin_stacks() -> None:
    text = _normalized()

    for field in (
        "stack_id",
        "display_name",
        "related_issue",
        "capabilities",
        "executable_requirements",
        "python_package_requirements",
        "environment_variable_hints",
        "version_probe",
        "help_probe",
        "smoke_test_description",
        "prepared_machine_notes",
        "platform_notes",
        "documentation_refs",
        "support_status",
        "non_bundled_disclaimer",
        "safety_notes",
    ):
        assert field in text

    for stack in (
        "gmsh",
        "octave",
        "calculix",
        "openfoam",
        "coolprop_cantera",
        "pyvista_meshio",
    ):
        assert stack in text


def test_doc_lists_health_states_and_diagnostics() -> None:
    text = _normalized()

    for state in (
        "unknown",
        "missing",
        "partially_installed",
        "discovered",
        "smoke_passed",
        "smoke_failed",
        "blocked_no_safe_case",
        "unsupported_platform",
        "skipped_by_user",
    ):
        assert state in text

    for severity in ("info", "warning", "error", "blocker"):
        assert severity in text


def test_doc_lists_json_helpers_and_future_gates() -> None:
    text = _read()

    assert "parse_optional_solver_manifest_dict" in text
    assert "load_optional_solver_manifest_json" in text
    assert "dump_optional_solver_manifest_json" in text
    for gate in (
        "OSW-EXP-057_OPTIONAL_SOLVER_DISCOVERY_SERVICE_DESIGN",
        "OSW-EXP-058_OPTIONAL_SOLVER_DISCOVERY_SERVICE_IMPLEMENTATION",
        "OSW-EXP-059_OPTIONAL_SOLVER_CLI_DOCTOR_PREVIEW",
        "OSW-EXP-060_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_DESIGN",
    ):
        assert gate in text


def test_doc_does_not_claim_validation_passed_or_issue_closure() -> None:
    text = _normalized()

    for phrase in (
        "live validation passed",
        "live optional validation passed",
        "calculix validation passed",
        "#6 through #11 passed",
        "#8 can close",
        "issues #6 through #11 can close",
        "closure ready",
        "ready for closure",
    ):
        assert phrase not in text


def test_doc_does_not_claim_bundled_solvers_or_certification() -> None:
    text = _normalized()

    for phrase in (
        "solvers are bundled",
        "external solvers are bundled",
        "industrial certification",
        "certified for production",
        "certification is provided",
    ):
        assert phrase not in text
