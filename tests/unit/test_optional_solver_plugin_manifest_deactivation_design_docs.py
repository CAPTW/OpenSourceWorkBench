from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_deactivation_design.md"
)
DECISION_LOG = REPO_ROOT / "docs" / "07_decision_log.md"
GUARDRAILS = REPO_ROOT / "docs" / "08_scope_guardrails.md"
RISK_REGISTER = REPO_ROOT / "docs" / "09_risk_register.md"
VALIDATION_MATRIX = REPO_ROOT / "docs" / "04_validation_matrix.md"
RELEASE_CHECKLIST = REPO_ROOT / "docs" / "10_release_checklist.md"

DOC_LINK = "optional_solver_plugin_manifest_deactivation_design.md"


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


# 4-22. Non-actions / safety boundaries are explicitly disclaimed.
def test_doc_disclaims_non_actions() -> None:
    text = _normalized()
    for phrase in (
        "no deactivation implementation",
        "no deactivation persistence",
        "no gui deactivation behavior",
        "no cli deactivation",
        "no file deletion",
        "no dependency uninstall",
        "no solver uninstall",
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
    assert "no issue mutation" in text or "no issue closure" in text
    assert "deactivation is not validation" in text


# 23 & 24. Defines deactivation and what it does not mean.
def test_doc_defines_deactivation_and_non_meaning() -> None:
    text = _normalized()
    assert "definition of deactivation" in text
    assert "deactivation is a future explicit user action" in text
    assert "deactivation must not mean" in text
    # Distinctions from deletion/uninstall.
    assert "deactivation is not deletion" in text
    assert "deactivation is not uninstall" in text


# 25. Acknowledgements.
def test_doc_describes_acknowledgements() -> None:
    text = _normalized()
    assert "user acknowledgement model" in text
    for ack in (
        "not_file_deletion",
        "not_dependency_uninstall",
        "not_solver_uninstall",
        "not_issue_closure",
        "not_release_mutation",
        "not_validation_evidence_deletion",
        "deactivation_history_visible",
    ):
        assert ack in text


# 26. Source/trust/provenance labels.
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


# 27. Deactivation state machine.
def test_doc_describes_state_machine() -> None:
    text = _normalized()
    assert "deactivation state machine" in text
    for state in (
        "active_candidate",
        "deactivation_requested",
        "deactivation_blocked",
        "deactivated",
        "deactivation_error",
    ):
        assert state in text
    assert "allowed transitions" in text
    assert "blocked transitions" in text


# 28. Validation / evidence policy.
def test_doc_describes_validation_evidence_policy() -> None:
    text = _normalized()
    assert "validation and evidence policy" in text
    assert "must not delete or rewrite validation evidence" in text
    assert "skipped-missing" in text
    assert "historical evidence" in text


# 29. Reserved OSPMG_DEACTIVATION_* diagnostics.
def test_doc_reserves_deactivation_diagnostics() -> None:
    raw = _read()
    for code in (
        "OSPMG_DEACTIVATION_ACTIVE_REQUIRED",
        "OSPMG_DEACTIVATION_ACK_REQUIRED",
        "OSPMG_DEACTIVATION_NOT_FILE_DELETE",
        "OSPMG_DEACTIVATION_NOT_UNINSTALL",
        "OSPMG_DEACTIVATION_NOT_VALIDATION",
        "OSPMG_DEACTIVATION_NO_DISCOVERY_EXECUTION",
        "OSPMG_DEACTIVATION_NO_SOLVER_EXECUTION",
        "OSPMG_DEACTIVATION_NOT_ISSUE_CLOSURE",
        "OSPMG_DEACTIVATION_NOT_RELEASE_MUTATION",
        "OSPMG_DEACTIVATION_EVIDENCE_RETAINED",
        "OSPMG_DEACTIVATION_SHARED_STACK_WARNING",
        "OSPMG_DEACTIVATION_STATE_CONFLICT",
        "OSPMG_DEACTIVATION_PERSISTENCE_NOT_IMPLEMENTED",
        "OSPMG_DEACTIVATION_DEACTIVATED",
    ):
        assert code in raw


# 30. Future gates.
def test_doc_lists_future_gates() -> None:
    raw = _read()
    for gate in (
        "OSW-EXP-082_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DISCOVERY_REFRESH_INTEGRATION_DESIGN",
        "OSW-EXP-083_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_VIEWMODEL_EXTENSION",
        "OSW-EXP-084_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_GUI_IMPLEMENTATION",
        "OSW-EXP-085_OPTIONAL_SOLVER_PLUGIN_MANIFEST_REACTIVATION_DESIGN",
    ):
        assert gate in raw


# Must NOT make positive success/trust/certification claims.
def test_doc_makes_no_forbidden_claims() -> None:
    text = _normalized()
    for forbidden in (
        "validation passed",
        "validation failed",
        "manifests are trusted by default",
        "plugin manifests are trusted by default",
        "industrial certification provided",
        "certified for production",
        "solvers are bundled",
    ):
        assert forbidden not in text


# 31. Decision log records ADR-0115.
def test_decision_log_records_adr_0115() -> None:
    raw = DECISION_LOG.read_text(encoding="utf-8")
    assert "ADR-0115" in raw
    text = _collapse(raw)
    assert "deactivation" in text
    assert "design-only" in text


# 32. Guardrails, risk, validation matrix, and release checklist references.
def test_supporting_docs_reference_this_gate() -> None:
    guardrails = _collapse(GUARDRAILS.read_text(encoding="utf-8"))
    risk = _collapse(RISK_REGISTER.read_text(encoding="utf-8"))
    matrix = VALIDATION_MATRIX.read_text(encoding="utf-8")
    checklist = RELEASE_CHECKLIST.read_text(encoding="utf-8")

    assert "deactivation design into" in guardrails
    assert "deactivation design overreach" in risk
    assert DOC_LINK in matrix
    assert DOC_LINK in checklist
