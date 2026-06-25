from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_explicit_import_gui_design.md"
)
DECISION_LOG = REPO_ROOT / "docs" / "07_decision_log.md"
GUARDRAILS = REPO_ROOT / "docs" / "08_scope_guardrails.md"
RISK_REGISTER = REPO_ROOT / "docs" / "09_risk_register.md"
VALIDATION_MATRIX = REPO_ROOT / "docs" / "04_validation_matrix.md"
RELEASE_CHECKLIST = REPO_ROOT / "docs" / "10_release_checklist.md"

DOC_LINK = "optional_solver_plugin_manifest_explicit_import_gui_design.md"


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


# 1. The new design doc exists.
def test_design_doc_exists() -> None:
    assert DOC.exists()


# 2. It is design-only and adds no runtime behavior in this gate.
def test_doc_is_design_only() -> None:
    text = _normalized()

    assert "design-only" in text
    assert "no runtime source behavior is added in this gate" in text
    assert "not implementation authorization" in text


# 3-13. Forbidden runtime actions are explicitly disclaimed as non-actions.
def test_doc_disclaims_forbidden_runtime_actions() -> None:
    text = _normalized()

    # 3. no file dialog implementation / 15. no QFileDialog
    assert "no file dialog implementation" in text
    assert "no qfiledialog implementation" in text
    assert "implement qfiledialog" in text
    # 4. no file loading implementation
    assert "no file loading implementation" in text
    assert "implement file loading" in text
    # parsing JSON from GUI source is disclaimed
    assert "no json parsing from gui source" in text
    assert "parse json from gui source" in text
    # 5. no plugin activation
    assert "no plugin activation" in text
    assert "activate plugin manifests" in text
    # 6. no plugin package import
    assert "no plugin package import" in text
    assert "import plugin packages" in text
    # 7. no directory scan
    assert "no directory scan" in text
    assert "scan directories" in text
    # 8. no network fetch
    assert "no network fetch" in text
    assert "fetch network manifests" in text
    # 9. no discovery execution
    assert "no discovery execution" in text
    assert "run discovery" in text
    # 10. no solver execution
    assert "no solver execution" in text
    assert "execute solvers" in text
    # 11. no dependency installation
    assert "no dependency installation" in text
    assert "install dependencies" in text
    # 12. no issue mutation / no issue closure
    assert "no issue mutation" in text
    assert "mutate issues" in text
    assert "issue-closure claim" in text
    # 13. no release mutation
    assert "no release mutation" in text
    assert "mutate releases" in text


# 14 & 15. No validation-pass claim and no certification claim.
def test_doc_disclaims_validation_and_certification_claims() -> None:
    text = _normalized()

    assert "validation-pass claim" in text
    assert "certification claim" in text
    assert "claim live optional validation success" in text
    assert "claim certification" in text
    assert "bundled-solver claim" in text
    # Preview must be distinct from validation, activation, and installation.
    assert "preview is not validation" in text
    assert "preview is not activation" in text
    assert "preview is not installation" in text

    # Must NOT make positive success/closure/certification/trust claims.
    for forbidden in (
        "validation passed",
        "#6 through #11 passed",
        "issues can close",
        "issue closure readiness",
        "solvers are bundled",
        "industrial certification",
        "certified for production",
        "manifests are trusted by default",
        "plugin manifests are trusted by default",
    ):
        assert forbidden not in text


# 16. Cancel / no-op behavior is described.
def test_doc_describes_cancel_noop() -> None:
    text = _normalized()

    assert "cancel is a no-op" in text
    assert "cancelled selection" in text


# 17. Invalid JSON handling is described.
def test_doc_describes_invalid_json() -> None:
    text = _normalized()

    assert "invalid json" in text


# 18. Schema-invalid manifests are described.
def test_doc_describes_schema_invalid() -> None:
    text = _normalized()

    assert "schema-invalid" in text


# 19. Conflict handling is described.
def test_doc_describes_conflict_handling() -> None:
    text = _normalized()

    assert "duplicate stack id" in text
    assert "built-ins win by default" in text or "built-ins-win" in text
    assert "conflicts must be previewed, not hidden" in text


# 20. Source / trust labels are described.
def test_doc_describes_source_and_trust_labels() -> None:
    text = _normalized()

    assert "source and trust labeling" in text
    assert "source_type: user_selected_json_file" in text
    assert "trust_label: untrusted_user_file" in text
    assert "a trust label is not certification" in text
    for label in (
        "built-in trusted",
        "third-party plugin",
        "untrusted",
        "invalid",
    ):
        assert label in text
    assert "not trusted by default" in text


# Diagnostic code reservations are present (design-only names).
def test_doc_reserves_import_diagnostic_codes() -> None:
    raw = _read()

    for code in (
        "OSPMG_IMPORT_CANCELLED",
        "OSPMG_IMPORT_FILE_MISSING",
        "OSPMG_IMPORT_UNREADABLE",
        "OSPMG_IMPORT_UNSUPPORTED_EXTENSION",
        "OSPMG_IMPORT_FILE_TOO_LARGE",
        "OSPMG_IMPORT_INVALID_JSON",
        "OSPMG_IMPORT_SCHEMA_INVALID",
        "OSPMG_IMPORT_CONFLICT",
        "OSPMG_IMPORT_UNTRUSTED_SOURCE",
        "OSPMG_IMPORT_PREVIEW_ONLY",
    ):
        assert code in raw


# Explicit JSON file chooser behavior and entry points are defined.
def test_doc_defines_chooser_and_entry_points() -> None:
    text = _normalized()

    assert "user-initiated only" in text
    assert "json files only" in text
    assert "*.json" in text
    assert "reject unsupported extensions" in text
    assert "no automatic directory recursion" in text
    assert "no remote url input" in text
    assert "no automatic startup prompt" in text
    assert "preview plugin manifest json" in text


# OSW-EXP-074 display-only boundary is preserved and referenced.
def test_doc_preserves_osw_exp_074_boundary() -> None:
    raw = _read()
    text = raw.lower()

    assert "OptionalSolverPluginManifestPanel" in raw
    assert "OptionalSolverPluginManifestGuiViewModel" in raw
    assert "the current panel is display-only" in text
    assert "the current panel does not choose files or load files" in text


# Relationship sections preserve separation from CLI / health / export.
def test_doc_defines_relationships() -> None:
    text = _normalized()

    assert "optional-solver-plugin-manifest-preview" in text
    assert "this design does not change the cli" in text
    assert "previewing a manifest is not health validation" in text
    assert "does not alter passive discovery" in text
    assert "this design does not implement export behavior" in text
    assert "built-in manifests remain authoritative by default" in text


# Future implementation test plan is defined for a later gate.
def test_doc_defines_future_implementation_test_plan() -> None:
    text = _normalized()

    assert "future implementation test plan" in text
    assert "cancel is a no-op and preserves prior state" in text
    assert "no activation action is triggered by preview" in text
    assert "no discovery execution occurs" in text
    assert "no solver execution occurs" in text
    assert "no dependency installation occurs" in text
    assert "no issue mutation occurs" in text
    assert "no release mutation occurs" in text


# Future gates are proposed without being implemented.
def test_doc_proposes_future_gates() -> None:
    raw = _read()

    for gate in (
        "OSW-EXP-076_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPLICIT_IMPORT_GUI_VIEWMODEL",
        "OSW-EXP-077_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPLICIT_IMPORT_GUI_IMPLEMENTATION",
        "OSW-EXP-078_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_DESIGN",
        "OSW-VALID",
    ):
        assert gate in raw
    # The numbering divergence from the prior reservation is explained.
    assert "numbering note" in raw.lower()


# 21. Decision log records ADR-0109.
def test_decision_log_records_adr_0109() -> None:
    raw = DECISION_LOG.read_text(encoding="utf-8")

    assert "ADR-0109" in raw
    text = raw.lower()
    assert "explicit import" in text
    assert "design-only" in text


# 22. Guardrails, risk register, validation matrix, and release checklist
#     all reference this design gate.
def test_supporting_docs_reference_this_gate() -> None:
    guardrails = GUARDRAILS.read_text(encoding="utf-8").lower()
    risk = RISK_REGISTER.read_text(encoding="utf-8").lower()
    matrix = VALIDATION_MATRIX.read_text(encoding="utf-8")
    checklist = RELEASE_CHECKLIST.read_text(encoding="utf-8")

    assert "explicit import gui design" in guardrails
    assert "explicit import gui design" in risk
    assert DOC_LINK in matrix
    assert DOC_LINK in checklist
