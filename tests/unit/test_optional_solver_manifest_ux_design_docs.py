from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / "optional_solver_manifest_ux_design.md"


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_manifest_ux_design_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_design_only_non_actions() -> None:
    text = _normalized()

    assert "design-only" in text
    assert "no source implementation" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text


def test_doc_records_current_baseline() -> None:
    text = _read()
    normalized = text.lower()

    assert "v0.1.5-rc1" in text
    assert "public prerelease" in normalized
    assert "#6" in text
    assert "#11" in text
    assert "remain open" in normalized
    assert "OSW-VALID-005" in text
    assert "skipped-missing" in normalized


def test_doc_lists_all_target_optional_stacks() -> None:
    text = _read()

    for stack in (
        "Gmsh",
        "GNU Octave",
        "CalculiX",
        "OpenFOAM",
        "CoolProp / Cantera",
        "PyVista / meshio",
    ):
        assert stack in text


def test_doc_defines_manifest_concept() -> None:
    text = _normalized()

    assert "manifest concept" in text
    for field in (
        "stable stack id",
        "display name",
        "related issue number",
        "capabilities",
        "executable requirements",
        "python package requirements",
        "environment variable hints",
        "version/help probes",
        "safe smoke-test description",
        "prepared-machine validation notes",
        "platform notes",
        "support status",
        "non-bundled solver disclaimer",
    ):
        assert field in text


def test_doc_defines_ux_health_states() -> None:
    text = _normalized()

    for state in (
        "unknown",
        "missing",
        "partially installed",
        "discovered",
        "smoke passed",
        "smoke failed",
        "blocked no safe case",
        "unsupported platform",
        "skipped by user",
    ):
        assert state in text


def test_doc_defines_future_cli_and_gui_ux() -> None:
    text = _normalized()

    assert "future cli ux" in text
    assert "optional solver list" in text
    assert "optional solver doctor" in text
    assert "optional solver explain" in text
    assert "json output" in text
    assert "no install command in initial scope" in text
    assert "future gui ux" in text
    assert "optional solver health panel" in text
    assert "per-stack status cards" in text
    assert "prepared-environment guidance" in text
    assert "no install buttons in initial scope" in text


def test_doc_defines_plugin_ecosystem_relationship() -> None:
    text = _normalized()

    assert "plugin ecosystem relationship" in text
    assert "core built-in manifests" in text
    assert "plugin-provided manifests" in text
    assert "manifest validation" in text
    assert "trust boundary" in text
    assert "no credentials or provider secrets" in text


def test_doc_defines_validation_relationship() -> None:
    text = _normalized()

    assert "validation relationship" in text
    assert "osw-valid gates" in text
    assert "skipped-missing is not failure and not pass" in text
    assert "issue closure remains separate" in text
    assert "prepared-machine validation requires already installed" in text


def test_doc_defines_safety_and_privacy() -> None:
    text = _normalized()

    assert "safety and privacy" in text
    assert "no solver install" in text
    assert "no dependency install" in text
    assert "no bundled solvers" in text
    assert "no telemetry" in text
    assert "no leaking full environment" in text
    assert "no certification claim" in text


def test_doc_lists_future_implementation_slices() -> None:
    text = _read()

    for gate in (
        "OSW-EXP-056_OPTIONAL_SOLVER_MANIFEST_SCHEMA_MODEL",
        "OSW-EXP-057_OPTIONAL_SOLVER_DISCOVERY_SERVICE_DESIGN",
        "OSW-EXP-058_OPTIONAL_SOLVER_DISCOVERY_SERVICE_IMPLEMENTATION",
        "OSW-EXP-059_OPTIONAL_SOLVER_CLI_DOCTOR_PREVIEW",
        "OSW-EXP-060_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_DESIGN",
    ):
        assert gate in text


def test_doc_does_not_claim_validation_passed() -> None:
    text = _normalized()

    forbidden = (
        "live validation passed",
        "live optional validation passed",
        "calculix validation passed",
        "#8 passed",
        "#6 through #11 passed",
    )
    for phrase in forbidden:
        assert phrase not in text


def test_doc_does_not_claim_issue_closure_readiness() -> None:
    text = _normalized()

    forbidden = (
        "#6 can close",
        "#8 can close",
        "#6 through #11 can close",
        "issues #6 through #11 can close",
        "closure ready",
        "ready for closure",
    )
    for phrase in forbidden:
        assert phrase not in text


def test_doc_does_not_claim_bundled_solvers_or_certification() -> None:
    text = _normalized()

    forbidden = (
        "solvers are bundled",
        "external solvers are bundled",
        "industrial certification",
        "certified for production",
        "certification is provided",
    )
    for phrase in forbidden:
        assert phrase not in text
