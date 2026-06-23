from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / "optional_solver_discovery_service_design.md"


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_discovery_service_design_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_design_only_non_actions() -> None:
    text = _normalized()

    assert "design-only" in text
    assert "no implementation in this gate" in text
    assert "no discovery service source" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text
    assert "no external command execution" in text


def test_doc_records_current_baseline() -> None:
    text = _read()
    normalized = text.lower()

    assert "v0.1.5-rc1" in text
    assert "public prerelease" in normalized
    assert "optional solver manifest schema/model exists" in normalized
    assert "#6" in text
    assert "#11" in text
    assert "remain open" in normalized
    assert "OSW-VALID-005" in text
    assert "skipped-missing" in normalized


def test_doc_defines_relationship_to_manifest_schema() -> None:
    text = _read()

    assert "Relationship to manifest schema" in text
    assert "OptionalSolverManifest" in text
    assert "declarative requirements" in text
    assert "maps evidence to the manifest health states" in text
    assert "must never mutate manifests during discovery" in text


def test_doc_defines_discovery_modes_and_passive_active_boundary() -> None:
    text = _normalized()

    assert "discovery modes" in text
    assert "passive metadata inspection" in text
    assert "path or executable presence check, future implementation only" in text
    assert "python package presence check, future implementation only" in text
    assert "active smoke validation reserved for explicit validation gates" in text
    assert "passive versus active boundary" in text
    assert "cli and gui doctor surfaces must not run solvers by default" in text
    assert "no hidden solver execution" in text


def test_doc_defines_result_concept_diagnostics_and_health_mapping() -> None:
    text = _normalized()

    assert "discovery result concept" in text
    for field in (
        "stack id",
        "manifest version or manifest reference",
        "discovered executables",
        "discovered python packages",
        "environment hints considered",
        "health state",
        "diagnostics",
        "confidence",
        "privacy redactions",
        "timestamp",
        "source of evidence",
    ):
        assert field in text

    for diagnostic in (
        "missing executable",
        "missing python package",
        "partial stack",
        "unsupported platform",
        "blocked probe",
        "unsafe probe skipped",
        "stale cache",
        "manifest error",
        "permission or path issue",
    ):
        assert diagnostic in text

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


def test_doc_defines_privacy_security_and_future_handoffs() -> None:
    text = _normalized()

    assert "privacy/security" in text
    assert "no telemetry" in text
    assert "do not expose the full `path` by default" in text
    assert "redact user paths" in text
    assert "do not collect secrets" in text
    assert "do not store credentials" in text
    assert "do not run installer commands" in text
    assert "do not download solvers" in text
    assert "future cli handoff" in text
    assert "`optional-solver list`" in text
    assert "`optional-solver doctor`" in text
    assert "`optional-solver explain`" in text
    assert "json output" in text
    assert "future gui handoff" in text
    assert "optional solver health panel" in text
    assert "per-stack cards" in text
    assert "no install buttons in initial scope" in text


def test_doc_defines_plugin_validation_and_cache_relationships() -> None:
    text = _normalized()

    assert "plugin ecosystem" in text
    assert "built-in manifests" in text
    assert "future plugins may provide manifests" in text
    assert "trust boundary" in text
    assert "schema validation is required" in text
    assert "untrusted plugin manifests cannot execute code" in text
    assert "validation relationship" in text
    assert "osw-valid gates can use discovery results as precheck evidence" in text
    assert "skipped-missing remains neither pass nor failure" in text
    assert "caching and freshness" in text
    assert "stale cache data cannot justify issue closure" in text


def test_doc_lists_future_implementation_slices() -> None:
    text = _read()

    for gate in (
        "OSW-EXP-058_OPTIONAL_SOLVER_DISCOVERY_SERVICE_IMPLEMENTATION",
        "OSW-EXP-059_OPTIONAL_SOLVER_CLI_DOCTOR_PREVIEW",
        "OSW-EXP-060_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_DESIGN",
        "OSW-VALID",
    ):
        assert gate in text


def test_doc_does_not_claim_implemented_surfaces_or_validation_success() -> None:
    text = _normalized()

    for phrase in (
        "cli doctor is implemented",
        "cli doctor exists",
        "gui health panel is implemented",
        "live validation passed",
        "live optional validation passed",
        "#6 through #11 passed",
    ):
        assert phrase not in text


def test_doc_does_not_claim_issue_closure_bundled_solvers_or_certification() -> None:
    text = _normalized()

    for phrase in (
        "#6 can close",
        "#8 can close",
        "#6 through #11 can close",
        "issues #6 through #11 can close",
        "closure ready",
        "ready for closure",
        "solvers are bundled",
        "external solvers are bundled",
        "industrial certification",
        "certified for production",
        "certification is provided",
    ):
        assert phrase not in text
