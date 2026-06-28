from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reload_gui_design.md"
)
DECISION_LOG = REPO_ROOT / "docs" / "07_decision_log.md"
GUARDRAILS = REPO_ROOT / "docs" / "08_scope_guardrails.md"
RISK_REGISTER = REPO_ROOT / "docs" / "09_risk_register.md"
VALIDATION_MATRIX = REPO_ROOT / "docs" / "04_validation_matrix.md"
RELEASE_CHECKLIST = REPO_ROOT / "docs" / "10_release_checklist.md"


def _collapse(text: str) -> str:
    """Lowercase and collapse whitespace so wrapped markdown still matches."""

    return re.sub(r"\s+", " ", text.lower())


def _doc() -> str:
    return _collapse(DOC.read_text(encoding="utf-8"))


def test_design_doc_exists() -> None:
    assert DOC.exists()


def test_design_doc_is_design_only_and_non_runtime() -> None:
    doc = _doc()
    for phrase in (
        "design-only",
        "no reload gui implementation",
        "no gui source edits",
        "no runtime behavior",
        "no runtime behavior added",
    ):
        assert phrase in doc, phrase


def test_design_doc_states_required_non_actions() -> None:
    doc = _doc()
    required = (
        "no file dialog",
        "no file reading",
        "no file parsing",
        "no runtime reload",
        "no default reload path",
        "no background reload",
        "no reloadable bundle creation",
        "no export file creation",
        "no report file creation",
        "no clipboard behavior",
        "no report attachment",
        "no open-output-folder behavior",
        "no cli behavior",
        "no projectschema mutation",
        "no live discovery",
        "no passive refresh",
        "no plugin package import",
        "no directory scan",
        "no network fetch",
        "no validation execution",
        "no solver execution",
        "no dependency uninstall",
        "no solver uninstall",
        "no automatic activation",
        "no trust restoration",
        "no release mutation",
        "no tag mutation",
        "no asset mutation",
        "no version bump",
        "no validation-pass claim",
        "no certification claim",
    )
    for phrase in required:
        assert phrase in doc, phrase


def test_design_doc_states_alternate_required_non_actions() -> None:
    doc = _doc()
    assert "no file reader" in doc or "no file reading" in doc
    assert "no parser" in doc or "no file parsing" in doc
    assert "no reloadable bundles" in doc or "no reloadable bundle creation" in doc
    assert "no export files" in doc or "no export file creation" in doc
    assert "no report files" in doc or "no report file creation" in doc
    assert "no dependency installation" in doc or "no dependency install" in doc
    assert "no issue mutation" in doc or "no issue closure" in doc
    assert "no validation-fail claim" in doc or "no validation failure claim" in doc
    assert "no bundled-solver claim" in doc or "no bundled solver claim" in doc


def test_design_doc_defines_reload_gui_and_non_meaning() -> None:
    doc = _doc()
    assert "definition of reload gui" in doc
    assert "read-only, preview-first review surface" in doc
    assert "already-built reload view-model records" in doc
    assert "non-meaning of gui reload review" in doc
    for phrase in (
        "gui reload review is not validation success",
        "gui reload review is not validation failure",
        "gui reload review is not trust restoration",
        "gui reload review is not automatic activation",
        "gui reload review is not discovery success",
        "gui reload review is not dependency installation",
        "gui reload review is not solver execution",
        "gui reload review is not projectschema mutation",
        "gui reload review is not issue closure",
        "gui reload review is not release mutation",
        "gui reload review is not certification",
        "gui reload review is not report generation",
        "gui reload review is not reloadable bundle creation",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_flow_input_and_layout() -> None:
    doc = _doc()
    for phrase in (
        "future user flow",
        "no_reload_request",
        "no_payload",
        "target_not_selected",
        "schema_unsupported",
        "schema_migration_required",
        "payload_kind_mismatch",
        "redaction_review_required",
        "acknowledgement_review_required",
        "stale_source_repreview_required",
        "conflict_review_required",
        "unsafe_claim_blocked",
        "reload_preview_ready",
        "future_activation_review_required",
        "future_discovery_refresh_required",
        "data input policy",
        "future panel receives already-built reload view-model objects",
        "no direct file path opening",
        "no json parsing in panel",
        "layout and rendered sections",
        "summary",
        "source / provenance",
        "schema / migration",
        "acknowledgements / expiry",
        "safety guidance",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_rendered_displays() -> None:
    doc = _doc()
    for phrase in (
        "summary/readiness display",
        "source/provenance display",
        "schema/migration display",
        "candidate lifecycle display",
        "acknowledgement and expiry display",
        "redaction/privacy display",
        "stale-source/re-preview display",
        "conflict/shared-stack display",
        "unsafe-claim display",
        "evidence/history display",
        "diagnostics display",
        "action-state model",
        "future file-dialog boundary",
        "future reload acceptance boundary",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_safety_specifics() -> None:
    doc = _doc()
    for phrase in (
        "honesty flags must be visible and false",
        "user/plugin sources are untrusted by default",
        "built-ins are authoritative by default",
        "trust label is not certification",
        "schema mismatch is not validation failure",
        "persisted active requires future activation review",
        "fingerprints are not trust signals",
        "old preview is not silently trusted",
        "stale-source state is not validation failure",
        "persisted state does not override built-ins",
        "unsafe claims are visible and blocked",
        "unsafe claims include validation success",
        "unsafe claims include validation failure",
        "skipped-missing remains skipped-missing",
        "reload is not validation evidence",
    ):
        assert phrase in doc, phrase


def test_design_doc_lists_acknowledgements_and_expiry() -> None:
    doc = _doc()
    for ack in (
        "reload_not_validation",
        "reload_not_trust_restoration",
        "reload_not_automatic_activation",
        "reload_not_discovery_success",
        "reload_not_dependency_install",
        "reload_no_solver_execution",
        "reload_not_issue_closure",
        "reload_not_release_mutation",
        "reload_not_certification",
        "redaction_reviewed",
        "unredacted_paths_blocked",
        "stale_source_requires_repreview",
        "untrusted_source_remains_untrusted",
        "activation_review_required_after_reload",
        "no_discovery_execution",
        "no_plugin_package_import",
        "no_validation_execution",
        "no_solver_execution",
        "trust_label_not_certification",
        "persisted_acknowledgements_may_expire",
    ):
        assert ack in doc, ack
    for phrase in (
        "source fingerprint change",
        "schema version change",
        "unsafe claim appearance",
        "trust policy change",
        "future discovery-refresh result",
    ):
        assert phrase in doc, phrase


def test_design_doc_renders_reload_diagnostics() -> None:
    text = DOC.read_text(encoding="utf-8")
    for code in (
        "OSPMG_RELOAD_NOT_IMPLEMENTED",
        "OSPMG_RELOAD_DESIGN_ONLY",
        "OSPMG_RELOAD_TARGET_REQUIRED",
        "OSPMG_RELOAD_PAYLOAD_KIND_MISMATCH",
        "OSPMG_RELOAD_SCHEMA_UNSUPPORTED",
        "OSPMG_RELOAD_SCHEMA_MIGRATION_REQUIRED",
        "OSPMG_RELOAD_REDACTION_REQUIRED",
        "OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED",
        "OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED",
        "OSPMG_RELOAD_ACK_REQUIRED",
        "OSPMG_RELOAD_ACK_EXPIRED",
        "OSPMG_RELOAD_STALE_SOURCE_REPREVIEW_REQUIRED",
        "OSPMG_RELOAD_UNTRUSTED_SOURCE",
        "OSPMG_RELOAD_CONFLICT_VISIBLE",
        "OSPMG_RELOAD_SHARED_STACK_VISIBLE",
        "OSPMG_RELOAD_UNSAFE_CLAIM_BLOCKED",
        "OSPMG_RELOAD_EVIDENCE_RETAINED",
        "OSPMG_RELOAD_HISTORY_RETAINED",
        "OSPMG_RELOAD_NOT_VALIDATION",
        "OSPMG_RELOAD_NOT_TRUST_RESTORE",
        "OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION",
        "OSPMG_RELOAD_NO_DISCOVERY_EXECUTION",
        "OSPMG_RELOAD_NO_PLUGIN_IMPORT",
        "OSPMG_RELOAD_NO_VALIDATION_EXECUTION",
        "OSPMG_RELOAD_NO_SOLVER_EXECUTION",
        "OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED",
        "OSPMG_RELOAD_FUTURE_GATE",
    ):
        assert code in text, code


def test_design_doc_describes_relationships() -> None:
    doc = _doc()
    for phrase in (
        "relationship to reload view-model",
        "future gui consumes osw-exp-107 view-model records",
        "relationship to persistence gui and state writer",
        "reload gui does not write files",
        "relationship to export summary gui/cli",
        "export summaries are not reloadable bundles",
        "relationship to projectschema",
        "reloaded state is not projectschema state",
        "relationship to live optional validation issues",
        "issues #6 through #11 remain open",
    ):
        assert phrase in doc, phrase


def test_design_doc_lists_future_test_plan_and_gates() -> None:
    doc = _doc()
    assert "future implementation test plan" in doc
    assert "future gates" in doc
    for phrase in (
        "panel imports are guarded by pyside availability",
        "panel consumes an existing reload view-model",
        "all sections render",
        "no file dialog",
        "no file reader/parser",
        "no raw path leak",
        "disabled/future actions displayed",
        "diagnostics visible",
        "source/provenance/trust visible",
        "osw-exp-109_optional_solver_plugin_manifest_reload_gui_implementation",
        "osw-exp-110_optional_solver_plugin_manifest_reload_cli_design",
        "osw-exp-111_optional_solver_plugin_manifest_reload_cli_implementation",
        "osw-exp-112_optional_solver_plugin_manifest_reload_file_reader_design",
        "osw-exp-113_optional_solver_plugin_manifest_reload_file_reader_implementation",
    ):
        assert phrase in doc, phrase


def test_meta_docs_reference_reload_gui_design() -> None:
    assert "ADR-0142" in DECISION_LOG.read_text(encoding="utf-8")
    for path in (GUARDRAILS, RISK_REGISTER, VALIDATION_MATRIX, RELEASE_CHECKLIST):
        text = path.read_text(encoding="utf-8").lower()
        assert "reload gui" in text, path.name
        assert "file dialog" in text, path.name
