from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_discovery_refresh_integration_design.md"
)
DECISION_LOG = REPO_ROOT / "docs" / "07_decision_log.md"
GUARDRAILS = REPO_ROOT / "docs" / "08_scope_guardrails.md"
RISK_REGISTER = REPO_ROOT / "docs" / "09_risk_register.md"
VALIDATION_MATRIX = REPO_ROOT / "docs" / "04_validation_matrix.md"
RELEASE_CHECKLIST = REPO_ROOT / "docs" / "10_release_checklist.md"

DOC_LINK = "optional_solver_plugin_manifest_discovery_refresh_integration_design.md"


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


# 4-21. Non-actions / safety boundaries are explicitly disclaimed.
def test_doc_disclaims_non_actions() -> None:
    text = _normalized()
    for phrase in (
        "no discovery integration implementation",
        "no passive discovery behavior change",
        "no activation persistence",
        "no deactivation persistence",
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
    assert "refresh is not validation" in text


# 22 & 23. Defines discovery-refresh integration and what it does not mean.
def test_doc_defines_integration_and_non_meaning() -> None:
    text = _normalized()
    assert "definition of discovery-refresh integration" in text
    assert "discovery-refresh integration is a future explicit workflow" in text
    assert "it must not mean" in text
    assert "discovery refresh is not validation success" in text
    assert "discovery refresh is not dependency installation" in text
    assert "discovery refresh is not solver execution" in text


# 24. Discovery refresh modes.
def test_doc_describes_refresh_modes() -> None:
    text = _normalized()
    assert "discovery refresh modes" in text
    for mode in (
        "built_in_only_refresh",
        "activated_candidates_preview_refresh",
        "activated_candidates_user_initiated_refresh",
        "deactivated_candidates_excluded",
        "deactivated_candidates_visible_but_inactive",
        "blocked_due_to_untrusted_or_conflicting_sources",
    ):
        assert mode in text


# 25. Acknowledgements.
def test_doc_describes_acknowledgements() -> None:
    text = _normalized()
    assert "user acknowledgement model" in text
    # Assert the backticked bullet form so these do not match the (uppercase)
    # OSPMG_DISCOVERY_REFRESH_* diagnostic codes that embed the same words.
    for ack in (
        "refresh_not_validation",
        "refresh_not_install",
        "refresh_not_solver_execution",
        "refresh_not_issue_closure",
        "refresh_not_certification",
        "untrusted_manifest_source",
        "conflict_or_override_visible",
        "deactivated_candidates_excluded",
        "no_network_fetch",
        "no_plugin_package_import",
    ):
        assert f"`{ack}`" in text


# 26. Source/trust/provenance labels.
def test_doc_describes_source_trust_provenance() -> None:
    text = _normalized()
    assert "source/trust/provenance model" in text
    for label in (
        "source_type",
        "trust_label",
        "discovery_source_state",
        "activated_user_selected_json_file",
        "activated_plugin_manifest",
        "deactivated_manifest",
        "untrusted_user_file",
        "untrusted_plugin_manifest",
    ):
        assert label in text
    assert "a trust label is not certification" in text
    assert "discovery inclusion is not validation evidence" in text
    assert "untrusted by default" in text


# 27. Built-in precedence and conflict policy.
def test_doc_describes_builtin_precedence_and_conflict() -> None:
    text = _normalized()
    assert "built-in precedence and conflict policy" in text
    assert "built-ins win by default" in text
    assert "duplicate stack ids must be visible" in text
    assert "must not hide conflicts" in text


# 28. Deactivated candidate policy.
def test_doc_describes_deactivated_candidate_policy() -> None:
    text = _normalized()
    assert "deactivated candidate policy" in text
    assert "not active discovery inputs by default" in text
    assert "not a validation failure" in text


# 29. Unsafe claim policy.
def test_doc_describes_unsafe_claim_policy() -> None:
    text = _normalized()
    assert "unsafe claim policy" in text
    assert "bundled solver binaries" in text
    assert "block or refresh-with-blockers" in text


# 30. Refresh state machine.
def test_doc_describes_state_machine() -> None:
    text = _normalized()
    assert "refresh state machine" in text
    for state in (
        "refresh_unavailable",
        "refresh_requested",
        "refresh_blocked",
        "refresh_ready",
        "refresh_running_future_gate",
        "refresh_result_preview",
        "refresh_error",
    ):
        assert state in text
    assert "allowed transitions" in text
    assert "blocked transitions" in text


# 31. Reserved OSPMG_DISCOVERY_REFRESH_* diagnostics.
def test_doc_reserves_discovery_refresh_diagnostics() -> None:
    raw = _read()
    for code in (
        "OSPMG_DISCOVERY_REFRESH_ACTIVE_CANDIDATE_REQUIRED",
        "OSPMG_DISCOVERY_REFRESH_DEACTIVATED_EXCLUDED",
        "OSPMG_DISCOVERY_REFRESH_ACK_REQUIRED",
        "OSPMG_DISCOVERY_REFRESH_UNTRUSTED_SOURCE",
        "OSPMG_DISCOVERY_REFRESH_CONFLICT_BLOCKED",
        "OSPMG_DISCOVERY_REFRESH_UNSAFE_CLAIM",
        "OSPMG_DISCOVERY_REFRESH_NOT_VALIDATION",
        "OSPMG_DISCOVERY_REFRESH_NO_INSTALL",
        "OSPMG_DISCOVERY_REFRESH_NO_SOLVER_EXECUTION",
        "OSPMG_DISCOVERY_REFRESH_NO_NETWORK_FETCH",
        "OSPMG_DISCOVERY_REFRESH_NO_PLUGIN_IMPORT",
        "OSPMG_DISCOVERY_REFRESH_NOT_ISSUE_CLOSURE",
        "OSPMG_DISCOVERY_REFRESH_NOT_CERTIFICATION",
        "OSPMG_DISCOVERY_REFRESH_INTEGRATION_NOT_IMPLEMENTED",
    ):
        assert code in raw


# 32. Relationship to live optional validation issues.
def test_doc_describes_live_validation_issue_boundary() -> None:
    text = _normalized()
    assert "relationship to live optional validation issues" in text
    assert "discovery refresh is not live optional validation" in text
    assert "skipped-missing remains skipped-missing" in text
    assert "#6 through #11" in _read().replace("`", "")


# 33. Future gates.
def test_doc_lists_future_gates() -> None:
    raw = _read()
    for gate in (
        "OSW-EXP-083_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DISCOVERY_REFRESH_VIEWMODEL",
        "OSW-EXP-084_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DISCOVERY_REFRESH_GUI_IMPLEMENTATION",
        "OSW-EXP-085_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_VIEWMODEL_EXTENSION",
        "OSW-EXP-086_OPTIONAL_SOLVER_PLUGIN_MANIFEST_DEACTIVATION_GUI_IMPLEMENTATION",
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


# 34. Decision log records ADR-0116.
def test_decision_log_records_adr_0116() -> None:
    raw = DECISION_LOG.read_text(encoding="utf-8")
    assert "ADR-0116" in raw
    text = _collapse(raw)
    assert "discovery refresh" in text or "discovery-refresh" in text
    assert "design-only" in text


# 35. Guardrails, risk, validation matrix, and release checklist references.
def test_supporting_docs_reference_this_gate() -> None:
    guardrails = _collapse(GUARDRAILS.read_text(encoding="utf-8"))
    risk = _collapse(RISK_REGISTER.read_text(encoding="utf-8"))
    matrix = VALIDATION_MATRIX.read_text(encoding="utf-8")
    checklist = RELEASE_CHECKLIST.read_text(encoding="utf-8")

    assert "discovery-refresh integration design into" in guardrails
    assert "discovery-refresh integration design overreach" in risk
    assert DOC_LINK in matrix
    assert DOC_LINK in checklist
