from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_discovery_service_implementation.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_discovery_service_implementation_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_status_and_non_actions() -> None:
    text = _normalized()

    assert "experimental passive discovery implemented" in text
    assert "no cli" in text
    assert "no gui" in text
    assert "no solver execution" in text
    assert "no external command execution" in text
    assert "no dependency installation" in text
    assert "no plugin loading" in text


def test_doc_lists_relationship_and_public_api() -> None:
    text = _read()

    assert "Relationship to design and manifest schema" in text
    assert "Optional solver discovery service design" in text
    assert "Optional solver manifest schema model" in text
    for symbol in (
        "OptionalSolverExecutableDiscovery",
        "OptionalSolverPythonPackageDiscovery",
        "OptionalSolverEnvironmentHintDiscovery",
        "OptionalSolverStackDiscovery",
        "OptionalSolverDiscoveryReport",
        "OptionalSolverDiscoveryDiagnostic",
        "OptionalSolverDiscoveryOptions",
        "OptionalSolverPathRedactionMode",
        "discover_optional_solver_stack",
        "discover_optional_solver_manifests",
        "discover_builtin_optional_solvers",
        "explain_optional_solver_discovery",
        "optional_solver_discovery_report_to_dict",
        "optional_solver_discovery_report_from_dict",
    ):
        assert symbol in text


def test_doc_defines_passive_behavior_resolvers_and_defaults() -> None:
    text = _normalized()

    assert "passive discovery behavior" in text
    assert "resolver injection" in text
    assert "default resolvers" in text
    assert "executable_resolver" in text
    assert "python_package_resolver" in text
    assert "environment_resolver" in text
    assert "shutil.which" in text
    assert "importlib.util.find_spec" in text
    assert "importlib.metadata.version" in text
    assert "os.environ.get" in text
    assert "does not import optional solver packages" in text


def test_doc_defines_redaction_health_mapping_and_diagnostics() -> None:
    text = _normalized()

    assert "path and environment redaction" in text
    assert "redact sensitive local values by default" in text
    assert "health-state mapping" in text
    for state in ("unknown", "missing", "partially_installed", "discovered"):
        assert state in text
    for state in ("smoke_passed", "smoke_failed"):
        assert state in text
    for diagnostic in (
        "osd_missing_executable",
        "osd_missing_python_package",
        "osd_missing_environment_hint",
        "osd_partial_stack",
        "osd_manifest_error",
        "osd_path_redacted",
        "osd_passive_only",
    ):
        assert diagnostic in text


def test_doc_lists_builtin_manifest_discovery_and_issue_relationship() -> None:
    text = _read()

    for stack in (
        "gmsh",
        "octave",
        "calculix",
        "openfoam",
        "coolprop_cantera",
        "pyvista_meshio",
    ):
        assert stack in text
    for issue in ("#6", "#7", "#8", "#9", "#10", "#11"):
        assert issue in text
    assert "Issues remain open" in text


def test_doc_lists_future_gates() -> None:
    text = _read()

    for gate in (
        "OSW-EXP-059_OPTIONAL_SOLVER_CLI_DOCTOR_PREVIEW",
        "OSW-EXP-060_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_DESIGN",
        "OSW-VALID",
    ):
        assert gate in text


def test_doc_does_not_claim_cli_gui_validation_or_issue_closure() -> None:
    text = _normalized()

    for phrase in (
        "cli doctor exists",
        "gui health panel exists",
        "active smoke validation exists",
        "live validation passed",
        "#6 through #11 passed",
        "#8 can close",
        "issues remain ready for closure",
        "solvers are bundled",
        "external solvers are bundled",
        "industrial certification",
        "certified for production",
    ):
        assert phrase not in text
