from __future__ import annotations

from pathlib import Path

from osw.experimental.optional_solvers import (
    OSPMG_IMPORT_DIAGNOSTIC_CODES,
    OptionalSolverPluginManifestExplicitImportAction,
    OptionalSolverPluginManifestExplicitImportDiagnosticViewModel,
    OptionalSolverPluginManifestExplicitImportGuiViewModel,
    OptionalSolverPluginManifestExplicitImportState,
    build_optional_solver_plugin_manifest_explicit_import_cancelled_viewmodel,
    build_optional_solver_plugin_manifest_explicit_import_empty_viewmodel,
    build_optional_solver_plugin_manifest_explicit_import_error_viewmodel,
    build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel,
    explain_optional_solver_plugin_manifest_explicit_import_gui_viewmodel,
    redact_optional_solver_plugin_manifest_source_reference,
    render_optional_solver_plugin_manifest_explicit_import_summary,
    summarize_optional_solver_plugin_manifest_explicit_import_gui_viewmodel,
)
from osw.experimental.optional_solvers import (
    plugin_manifest_explicit_import_gui_viewmodel as module_under_test,
)
from osw.experimental.optional_solvers.plugin_manifest_explicit_import_gui_viewmodel import (
    OSPMG_IMPORT_CANCELLED,
    OSPMG_IMPORT_CONFLICT,
    OSPMG_IMPORT_FILE_MISSING,
    OSPMG_IMPORT_INVALID_JSON,
    OSPMG_IMPORT_PREVIEW_ONLY,
    OSPMG_IMPORT_SCHEMA_INVALID,
    OSPMG_IMPORT_UNSUPPORTED_EXTENSION,
    OSPMG_IMPORT_UNTRUSTED_SOURCE,
)
from osw.experimental.optional_solvers.plugin_manifest_loader import (
    load_optional_solver_plugin_manifest_documents,
    load_optional_solver_plugin_manifest_json,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "optional_solvers" / "plugin_manifests"
VALID_PROJECT = FIXTURES / "valid_project_local_manifest.json"
VALID_USER = FIXTURES / "valid_user_local_manifest.json"
DUPLICATE_STACK = FIXTURES / "duplicate_stack_plugin_manifest.json"
INVALID_BUNDLED = FIXTURES / "invalid_bundled_solver_claim.json"


def _valid_project_vm():
    report = load_optional_solver_plugin_manifest_json(VALID_PROJECT)
    return build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(report)


def _user_local_vm():
    report = load_optional_solver_plugin_manifest_json(VALID_USER)
    return build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(report)


def _duplicate_vm():
    report = load_optional_solver_plugin_manifest_json(DUPLICATE_STACK)
    return build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(report)


def _bundled_vm():
    report = load_optional_solver_plugin_manifest_json(INVALID_BUNDLED)
    return build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(report)


def _action_state(view_model, action):
    for state in view_model.actions:
        if state.action == action:
            return state
    raise AssertionError(f"action not found: {action}")


# 1. Empty/no-source state.
def test_empty_view_model() -> None:
    vm = build_optional_solver_plugin_manifest_explicit_import_empty_viewmodel()

    assert vm.state == OptionalSolverPluginManifestExplicitImportState.NO_SOURCES_SELECTED.value
    assert vm.summary.selected_sources == 0
    assert vm.source_rows == ()
    assert vm.accepted_rows == ()
    assert vm.rejected_rows == ()
    assert vm.cancelled is False
    assert OSPMG_IMPORT_PREVIEW_ONLY in {d.code for d in vm.import_diagnostics}


# 2. Cancelled selection state (cancel is a no-op).
def test_cancelled_view_model() -> None:
    vm = build_optional_solver_plugin_manifest_explicit_import_cancelled_viewmodel()

    assert vm.state == OptionalSolverPluginManifestExplicitImportState.CANCELLED.value
    assert vm.cancelled is True
    assert vm.source_rows == ()
    codes = {d.code for d in vm.import_diagnostics}
    assert OSPMG_IMPORT_CANCELLED in codes
    # Cancel did not read or parse anything.
    assert vm.summary.accepted_count == 0
    assert vm.summary.rejected_count == 0
    from_classmethod = (
        OptionalSolverPluginManifestExplicitImportGuiViewModel.from_cancelled_selection()
    )
    assert from_classmethod.cancelled is True


# 3. Summary counts.
def test_summary_counts() -> None:
    vm = _valid_project_vm()

    assert vm.summary.selected_sources == 1
    assert vm.summary.accepted_count == 1
    assert vm.summary.rejected_count == 0
    assert vm.summary.conflict_count == 0
    assert vm.summary.diagnostic_count >= 0
    assert vm.summary.preview_only is True
    # Honesty flags must remain false.
    assert vm.summary.activation_performed is False
    assert vm.summary.discovery_execution_performed is False
    assert vm.summary.solver_execution_performed is False
    assert vm.summary.dependency_installation_performed is False
    assert vm.summary.third_party_manifests_trusted_by_default is False
    assert vm.summary.external_solvers_bundled is False


# 4. Accepted row rendering from supplied loader data.
def test_accepted_rows() -> None:
    vm = _valid_project_vm()

    assert len(vm.accepted_rows) == 1
    row = vm.accepted_rows[0]
    assert row.stack_id == "project_local_stack"
    assert row.not_validation_evidence_text


# 5. Rejected row rendering from supplied loader data.
def test_rejected_rows() -> None:
    vm = _bundled_vm()

    assert vm.rejected_rows
    assert vm.summary.rejected_count >= 1
    assert any(row.diagnostics for row in vm.rejected_rows)


# 6. Conflict row rendering.
def test_conflict_rows() -> None:
    vm = _duplicate_vm()

    assert vm.conflict_rows
    assert vm.summary.conflict_count >= 1
    conflict = vm.conflict_rows[0]
    assert conflict.built_in_wins_text
    assert conflict.plugin_override_disabled_text


# 7. Diagnostic row rendering.
def test_diagnostic_rows() -> None:
    vm = _bundled_vm()

    assert vm.diagnostic_rows
    assert all(row.code for row in vm.diagnostic_rows)


# 8. OSPMG_IMPORT_* diagnostic exposure.
def test_import_diagnostic_vocabulary_exposed() -> None:
    vm = _valid_project_vm()

    assert vm.reserved_import_diagnostic_codes == OSPMG_IMPORT_DIAGNOSTIC_CODES
    assert len(OSPMG_IMPORT_DIAGNOSTIC_CODES) == 10
    for code in (
        OSPMG_IMPORT_CANCELLED,
        OSPMG_IMPORT_FILE_MISSING,
        OSPMG_IMPORT_INVALID_JSON,
        OSPMG_IMPORT_SCHEMA_INVALID,
        OSPMG_IMPORT_CONFLICT,
        OSPMG_IMPORT_UNTRUSTED_SOURCE,
        OSPMG_IMPORT_PREVIEW_ONLY,
    ):
        assert code in OSPMG_IMPORT_DIAGNOSTIC_CODES


def test_import_diagnostics_for_conflict_and_rejection() -> None:
    dup_codes = {d.code for d in _duplicate_vm().import_diagnostics}
    assert OSPMG_IMPORT_CONFLICT in dup_codes
    assert OSPMG_IMPORT_PREVIEW_ONLY in dup_codes

    bad_codes = {d.code for d in _bundled_vm().import_diagnostics}
    assert OSPMG_IMPORT_SCHEMA_INVALID in bad_codes


def test_import_diagnostics_invalid_json_and_extension(tmp_path: Path) -> None:
    invalid = tmp_path / "broken.json"
    invalid.write_text("{not valid json", encoding="utf-8")
    invalid_report = load_optional_solver_plugin_manifest_json(invalid)
    invalid_vm = build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(
        invalid_report
    )
    assert OSPMG_IMPORT_INVALID_JSON in {d.code for d in invalid_vm.import_diagnostics}

    wrong_ext = tmp_path / "manifest.txt"
    wrong_ext.write_text("{}", encoding="utf-8")
    ext_report = load_optional_solver_plugin_manifest_json(wrong_ext)
    ext_vm = build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(ext_report)
    assert OSPMG_IMPORT_UNSUPPORTED_EXTENSION in {
        d.code for d in ext_vm.import_diagnostics
    }


def test_error_view_model_from_supplied_diagnostics() -> None:
    diagnostic = OptionalSolverPluginManifestExplicitImportDiagnosticViewModel(
        code=OSPMG_IMPORT_FILE_MISSING,
        severity="error",
        message="Selected manifest file does not exist.",
    )
    vm = build_optional_solver_plugin_manifest_explicit_import_error_viewmodel(
        (diagnostic,)
    )
    assert vm.state == OptionalSolverPluginManifestExplicitImportState.ERROR.value
    codes = {d.code for d in vm.import_diagnostics}
    assert OSPMG_IMPORT_FILE_MISSING in codes
    assert OSPMG_IMPORT_PREVIEW_ONLY in codes
    assert vm.summary.error_count == 1


# 9. Trust/source badges.
def test_trust_badges() -> None:
    vm = _valid_project_vm()

    assert vm.trust_badges
    badge = vm.trust_badges[0]
    assert badge.source_type
    assert badge.trust_label


# 10. Redacted source references.
def test_source_reference_redaction() -> None:
    display, redacted = redact_optional_solver_plugin_manifest_source_reference(
        "C:/Users/secret/workspace/manifest.json"
    )
    assert display == "manifest.json"
    assert redacted is True

    display2, redacted2 = redact_optional_solver_plugin_manifest_source_reference(
        "/home/secret/manifest.json"
    )
    assert display2 == "manifest.json"
    assert redacted2 is True

    display3, redacted3 = redact_optional_solver_plugin_manifest_source_reference(
        "builtin:gmsh"
    )
    assert display3 == "builtin:gmsh"
    assert redacted3 is False

    label, label_redacted = redact_optional_solver_plugin_manifest_source_reference(
        "C:/secret/x.json", provided_label="Example manifest"
    )
    assert label == "Example manifest"
    assert label_redacted is False

    vm = _valid_project_vm()
    assert vm.source_rows
    row = vm.source_rows[0]
    assert "/" not in row.source_reference_display
    assert "\\" not in row.source_reference_display
    assert row.redacted is True


# 11. Third-party/user-selected manifests are untrusted by default.
def test_user_local_source_is_untrusted_by_default() -> None:
    vm = _user_local_vm()

    assert vm.source_rows
    assert any(row.is_untrusted for row in vm.source_rows)
    assert vm.summary.untrusted_source_count >= 1
    assert OSPMG_IMPORT_UNTRUSTED_SOURCE in {d.code for d in vm.import_diagnostics}
    assert vm.summary.third_party_manifests_trusted_by_default is False


# 12. Trust label is not certification.
def test_trust_label_is_not_certification() -> None:
    vm = _valid_project_vm()
    guidance = " ".join(vm.guidance_text).lower()
    warnings = " ".join(row.warning_text for row in vm.source_rows).lower()
    combined = guidance + " " + warnings
    assert "not certification" in combined or "not validation evidence" in combined


# 13/14/15. Preview is not activation/validation/installation.
def test_preview_is_not_activation_validation_or_installation() -> None:
    vm = _valid_project_vm()
    guidance = " ".join(vm.guidance_text).lower()

    assert "preview is not activation" in guidance
    assert "validation" in guidance
    assert "installation" in guidance


# 16-20. Unsafe actions disabled / future-only.
def test_activation_action_disabled() -> None:
    state = _action_state(
        _valid_project_vm(),
        OptionalSolverPluginManifestExplicitImportAction.ACTIVATE_MANIFEST,
    )
    assert state.enabled is False


def test_discovery_action_disabled() -> None:
    state = _action_state(
        _valid_project_vm(),
        OptionalSolverPluginManifestExplicitImportAction.RUN_DISCOVERY_WITH_PLUGIN_MANIFESTS,
    )
    assert state.enabled is False
    assert state.available is False


def test_validation_action_disabled() -> None:
    state = _action_state(
        _valid_project_vm(),
        OptionalSolverPluginManifestExplicitImportAction.RUN_VALIDATION,
    )
    assert state.enabled is False
    assert state.available is False


def test_install_action_disabled() -> None:
    state = _action_state(
        _valid_project_vm(),
        OptionalSolverPluginManifestExplicitImportAction.INSTALL_SOLVER,
    )
    assert state.enabled is False
    assert state.available is False


def test_close_issue_action_disabled() -> None:
    state = _action_state(
        _valid_project_vm(),
        OptionalSolverPluginManifestExplicitImportAction.CLOSE_ISSUE,
    )
    assert state.enabled is False
    assert state.available is False


def test_choose_files_action_is_future_only() -> None:
    state = _action_state(
        _valid_project_vm(),
        OptionalSolverPluginManifestExplicitImportAction.CHOOSE_EXPLICIT_JSON_FILES,
    )
    assert state.enabled is False
    assert state.future_action is True


# 21-24. Side-effect-free module boundary (source-level guarantees).
def _module_source() -> str:
    return Path(module_under_test.__file__).read_text(encoding="utf-8")


def _imported_modules() -> set[str]:
    import ast

    tree = ast.parse(_module_source())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return {name.lower() for name in modules}


def test_module_has_no_file_io() -> None:
    # Substring checks here are prose-safe: these tokens do not appear in
    # descriptive text, only in real calls.
    source = _module_source()
    for forbidden in ("open(", ".read_text(", ".read_bytes(", "json.load", "json.loads"):
        assert forbidden not in source


def test_module_has_no_pathlib_existence_checks() -> None:
    source = _module_source()
    assert "pathlib" not in source
    assert ".exists(" not in source
    assert "Path(" not in source


def test_module_has_no_pyside_or_qt_import() -> None:
    # Inspect actual imports via AST so docstring prose does not cause false
    # positives.
    for module in _imported_modules():
        assert "pyside" not in module
        assert "pyqt" not in module
        assert not module.startswith("qt")
        assert module != "qtpy"


def test_module_has_no_subprocess_or_network_import() -> None:
    forbidden = {"subprocess", "shutil", "socket", "urllib", "requests", "http"}
    for module in _imported_modules():
        top = module.split(".", 1)[0]
        assert top not in forbidden
    # Defensive substring guard against indirect command execution.
    assert "os.system" not in _module_source()


# 25. In-memory export/summary writes no files.
def test_render_summary_is_in_memory_dict(tmp_path: Path) -> None:
    vm = _valid_project_vm()
    payload = render_optional_solver_plugin_manifest_explicit_import_summary(vm)

    assert isinstance(payload, dict)
    assert payload["preview_only"] is True
    assert payload["activation_performed"] is False
    assert payload["plugin_manifest_presence_is_validation_evidence"] is False
    assert "sources" in payload
    # Rendering wrote nothing to disk.
    assert not list(tmp_path.iterdir())


# 26. Module import works without optional heavy dependencies.
def test_module_import_is_lightweight() -> None:
    # The module must not depend on PySide6/Qt to import or build view-models.
    # (The precise no-Qt-import guarantee is enforced by the AST import test;
    # a global sys.modules check would be order-dependent in the full suite.)
    assert module_under_test.__name__.endswith(
        "plugin_manifest_explicit_import_gui_viewmodel"
    )
    text = summarize_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(
        _valid_project_vm()
    )
    assert "preview" in text.lower()
    explanation = explain_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(
        _valid_project_vm()
    )
    assert "does not" in explanation.lower()


def test_multi_document_report_summary() -> None:
    import json

    documents = (
        json.loads(VALID_PROJECT.read_text(encoding="utf-8")),
        json.loads(VALID_USER.read_text(encoding="utf-8")),
    )
    report = load_optional_solver_plugin_manifest_documents(documents)
    vm = build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(
        report, selected_source_count=2
    )
    assert vm.summary.selected_sources == 2
    assert vm.summary.accepted_count == 2
    assert OSPMG_IMPORT_PREVIEW_ONLY in {d.code for d in vm.import_diagnostics}


# 27. Docs mention non-actions and future gates.
def test_docs_mention_non_actions_and_future_gates() -> None:
    doc = (
        REPO_ROOT
        / "docs"
        / "experimental"
        / "optional_solver_plugin_manifest_explicit_import_gui_viewmodel.md"
    )
    assert doc.exists()
    text = doc.read_text(encoding="utf-8").lower()
    assert "non-actions" in text
    assert "future gates" in text
    assert "pure" in text
    assert "no file" in text
    assert "no qfiledialog" in text or "no file dialog" in text
    for phrase in (
        "no plugin activation",
        "no discovery",
        "no solver execution",
        "no dependency install",
        "validation-pass claim",
        "certification claim",
    ):
        assert phrase in text
