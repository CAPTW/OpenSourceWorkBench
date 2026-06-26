from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_activation_design.md"
)
DECISION_LOG = REPO_ROOT / "docs" / "07_decision_log.md"
GUARDRAILS = REPO_ROOT / "docs" / "08_scope_guardrails.md"
RISK_REGISTER = REPO_ROOT / "docs" / "09_risk_register.md"
VALIDATION_MATRIX = REPO_ROOT / "docs" / "04_validation_matrix.md"
RELEASE_CHECKLIST = REPO_ROOT / "docs" / "10_release_checklist.md"

DOC_LINK = "optional_solver_plugin_manifest_activation_design.md"


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _collapse(text: str) -> str:
    # Collapse all whitespace runs (including newlines) to single spaces so
    # substring checks are robust to Markdown line wrapping.
    return " ".join(text.lower().split())


def _normalized() -> str:
    return _collapse(_read())


# 1. The new design doc exists.
def test_design_doc_exists() -> None:
    assert DOC.exists()


# 2 & 3. Design-only, no runtime behavior.
def test_doc_is_design_only_no_runtime() -> None:
    text = _normalized()
    assert "design-only" in text
    assert "no runtime behavior" in text
    assert "not implementation authorization" in text


# 4-18. Non-actions / safety boundaries are explicitly disclaimed.
def test_doc_disclaims_non_actions() -> None:
    text = _normalized()
    for phrase in (
        "no activation implementation",
        "no plugin package import",
        "no directory scan",
        "no network fetch",
        "no discovery execution",
        "no validation execution",
        "no solver execution",
        "no dependency installation",
        "no issue mutation",
        "no release mutation",
        "no tag mutation",
        "no asset mutation",
        "no version bump",
        "no validation-pass claim",
        "no certification claim",
    ):
        assert phrase in text
    # Issue closure and validation distinctions.
    assert "no issue mutation" in text or "no issue closure" in text
    assert "activation is not validation" in text


# 19 & 20. Defines activation and what it does not mean.
def test_doc_defines_activation_and_non_meaning() -> None:
    text = _normalized()
    assert "definition of activation" in text
    assert "activation is a future explicit user acknowledgement" in text
    assert "activation must not mean" in text
    # Distinctions from trust/validation/install/execution.
    assert "activation is not solver execution" in text
    assert "activation is not dependency installation" in text


# 21. Acknowledgements.
def test_doc_describes_acknowledgements() -> None:
    text = _normalized()
    assert "user acknowledgement model" in text
    assert "untrusted source acknowledgement" in text
    assert "no validation-pass acknowledgement" in text
    assert "no solver-execution acknowledgement" in text


# 22. Source/trust/provenance labels.
def test_doc_describes_source_trust_provenance() -> None:
    text = _normalized()
    assert "source/trust/provenance model" in text
    for label in (
        "source_type",
        "trust_label",
        "activation_state",
        "user_selected_json_file",
        "plugin_provided_manifest",
        "untrusted_user_file",
        "untrusted_plugin_manifest",
    ):
        assert label in text
    assert "a trust label is not certification" in text
    assert "untrusted by default" in text


# 23. Conflict and built-in precedence.
def test_doc_describes_conflict_and_builtin_precedence() -> None:
    text = _normalized()
    assert "conflict and built-in precedence" in text
    assert "win by default" in text
    assert "duplicate stack id" in text


# 24. Unsafe claim policy.
def test_doc_describes_unsafe_claim_policy() -> None:
    text = _normalized()
    assert "unsafe claim policy" in text
    assert "bundled solver binaries" in text
    assert "block or active-with-blockers" in text


# 25. Activation state machine.
def test_doc_describes_state_machine() -> None:
    text = _normalized()
    assert "activation state machine" in text
    for state in (
        "inactive_preview",
        "activation_requested",
        "activation_blocked",
        "activation_ready",
        "active_candidate",
        "deactivated",
        "activation_error",
    ):
        assert state in text
    assert "allowed transitions" in text
    assert "blocked transitions" in text


# 26. Reserved OSPMG_ACTIVATION_* diagnostics.
def test_doc_reserves_activation_diagnostics() -> None:
    raw = _read()
    for code in (
        "OSPMG_ACTIVATION_PREVIEW_REQUIRED",
        "OSPMG_ACTIVATION_SCHEMA_BLOCKED",
        "OSPMG_ACTIVATION_CONFLICT_BLOCKED",
        "OSPMG_ACTIVATION_UNTRUSTED_SOURCE",
        "OSPMG_ACTIVATION_UNSAFE_CLAIM",
        "OSPMG_ACTIVATION_ACK_REQUIRED",
        "OSPMG_ACTIVATION_NOT_VALIDATION",
        "OSPMG_ACTIVATION_NO_INSTALL",
        "OSPMG_ACTIVATION_NO_SOLVER_EXECUTION",
        "OSPMG_ACTIVATION_NOT_CERTIFICATION",
        "OSPMG_ACTIVATION_DEACTIVATED",
        "OSPMG_ACTIVATION_PREVIEW_ONLY_GATE",
    ):
        assert code in raw


# 27. Future gates.
def test_doc_lists_future_gates() -> None:
    raw = _read()
    for gate in (
        "OSW-EXP-079_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_VIEWMODEL",
        "OSW-EXP-080_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_GUI_IMPLEMENTATION",
        "OSW-EXP-081_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_DESIGN",
        "OSW-EXP-082_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DISCOVERY_REFRESH_INTEGRATION_DESIGN",
    ):
        assert gate in raw


# Must NOT make positive success/trust/certification claims.
def test_doc_makes_no_forbidden_claims() -> None:
    text = _normalized()
    for forbidden in (
        "validation passed",
        "activation closes issues",
        "solvers are bundled",
        "manifests are trusted by default",
        "plugin manifests are trusted by default",
        "industrial certification provided",
        "certified for production",
    ):
        assert forbidden not in text


# 28. Decision log records ADR-0112.
def test_decision_log_records_adr_0112() -> None:
    raw = DECISION_LOG.read_text(encoding="utf-8")
    assert "ADR-0112" in raw
    text = _collapse(raw)
    assert "activation" in text
    assert "design-only" in text


# 29. Guardrails, risk, validation matrix, and release checklist references.
def test_supporting_docs_reference_this_gate() -> None:
    guardrails = _collapse(GUARDRAILS.read_text(encoding="utf-8"))
    risk = _collapse(RISK_REGISTER.read_text(encoding="utf-8"))
    matrix = VALIDATION_MATRIX.read_text(encoding="utf-8")
    checklist = RELEASE_CHECKLIST.read_text(encoding="utf-8")

    assert "activation design into" in guardrails
    assert "activation design overreach" in risk
    assert DOC_LINK in matrix
    assert DOC_LINK in checklist
