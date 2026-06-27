from __future__ import annotations

import ast
from pathlib import Path

from osw.experimental.optional_solvers import (
    OSPMG_DISCOVERY_REFRESH_DIAGNOSTIC_CODES,
    OptionalSolverPluginManifestDiscoveryRefreshAction,
    OptionalSolverPluginManifestDiscoveryRefreshReadiness,
    OptionalSolverPluginManifestDiscoveryRefreshSourceInput,
    OptionalSolverPluginManifestDiscoveryRefreshState,
    OptionalSolverPluginManifestDiscoveryRefreshViewModel,
    build_optional_solver_plugin_manifest_discovery_refresh_viewmodel,
    render_optional_solver_plugin_manifest_discovery_refresh_summary,
    summarize_optional_solver_plugin_manifest_discovery_refresh_viewmodel,
)
from osw.experimental.optional_solvers import (
    plugin_manifest_discovery_refresh_viewmodel as module_under_test,
)
from osw.experimental.optional_solvers.plugin_manifest_discovery_refresh_viewmodel import (
    ACK_NO_NETWORK_FETCH,
    ACK_NO_PLUGIN_PACKAGE_IMPORT,
    ACK_REFRESH_NOT_INSTALL,
    ACK_REFRESH_NOT_SOLVER_EXECUTION,
    DISCOVERY_REFRESH_REQUIRED_ACKS,
    OSPMG_DISCOVERY_REFRESH_ACTIVE_CANDIDATE_REQUIRED,
    OSPMG_DISCOVERY_REFRESH_CONFLICT_BLOCKED,
    OSPMG_DISCOVERY_REFRESH_DEACTIVATED_EXCLUDED,
    OSPMG_DISCOVERY_REFRESH_UNSAFE_CLAIM,
)

_ALL_ACKS = {ack: True for ack in DISCOVERY_REFRESH_REQUIRED_ACKS}
_Readiness = OptionalSolverPluginManifestDiscoveryRefreshReadiness
_Src = OptionalSolverPluginManifestDiscoveryRefreshSourceInput
_VM = OptionalSolverPluginManifestDiscoveryRefreshViewModel
_build = build_optional_solver_plugin_manifest_discovery_refresh_viewmodel

REPO_ROOT = Path(__file__).resolve().parents[2]


def _diag_codes(view_model) -> set[str]:
    return {d.code for d in view_model.diagnostics}


def _active_src(**kwargs):
    base = {"stack_id": "user_stack", "source_reference": "C:/secret/x/m.json"}
    base.update(kwargs)
    return _Src(**base)


# 1. Module import works without GUI extras.
def test_module_import_is_lightweight() -> None:
    vm = _build([_active_src()])
    text = summarize_optional_solver_plugin_manifest_discovery_refresh_viewmodel(vm)
    assert "discovery refresh" in text.lower()


# 2 & 3. No PySide/Qt / subprocess / network / plugin-import / discovery-execution.
def _module_source() -> str:
    return Path(module_under_test.__file__).read_text(encoding="utf-8")


def _imported_modules() -> set[str]:
    tree = ast.parse(_module_source())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return {m.lower() for m in modules}


def test_module_has_no_gui_or_unsafe_imports() -> None:
    for module in _imported_modules():
        assert "pyside" not in module
        assert "pyqt" not in module
        assert not module.startswith("qt")
        top = module.split(".", 1)[0]
        assert top not in {"subprocess", "shutil", "socket", "urllib", "requests", "http"}


def test_module_has_no_io_or_discovery_execution_paths() -> None:
    source = _module_source()
    for forbidden in (
        "open(",
        ".read_text(",
        ".read_bytes(",
        "json.load",
        "pathlib",
        ".exists(",
        "Path(",
        "os.system",
        "discover_builtin_optional_solvers",
        "discover_optional_solver_manifests",
        "discover_optional_solver_stack",
        "QProcess",
    ):
        assert forbidden not in source


# 4. Empty/no-activation state reports refresh unavailable.
def test_unavailable_no_activation_state() -> None:
    vm = _VM.unavailable()
    assert vm.summary.refresh_state == (
        OptionalSolverPluginManifestDiscoveryRefreshState.REFRESH_UNAVAILABLE.value
    )
    assert vm.summary.readiness == _Readiness.UNAVAILABLE_NO_ACTIVATION_STATE.value
    assert OSPMG_DISCOVERY_REFRESH_ACTIVE_CANDIDATE_REQUIRED in _diag_codes(vm)


# 5. Built-in-only mode does not require user/plugin trust.
def test_built_in_only_mode() -> None:
    vm = _VM.built_in_only(built_in_source_count=2)
    assert vm.summary.built_in_source_count == 2
    assert vm.summary.readiness == _Readiness.BUILT_IN_ONLY_READY.value
    assert vm.summary.refresh_ready is True
    assert all(not row.is_untrusted for row in vm.source_rows)


# 6. Active candidate is untrusted by default.
def test_active_candidate_untrusted_by_default() -> None:
    vm = _build([_active_src()], acknowledgements=_ALL_ACKS)
    assert vm.source_rows[0].is_untrusted is True
    assert "OSPMG_DISCOVERY_REFRESH_UNTRUSTED_SOURCE" in _diag_codes(vm)
    assert vm.summary.third_party_manifests_trusted_by_default is False


# 7 & 8 & 9. Deactivated candidate excluded; not validation failure; not uninstall.
def test_deactivated_candidate_excluded() -> None:
    vm = _build(
        [_active_src(stack_id="ds", activation_state="deactivated")],
        acknowledgements=_ALL_ACKS,
    )
    assert vm.deactivated_rows
    row = vm.deactivated_rows[0]
    assert row.excluded_by_default is True
    assert "not a validation failure" in row.not_validation_failure_text.lower()
    assert "not uninstall" in row.not_uninstall_text.lower()
    assert "not file deletion" in row.not_file_deletion_text.lower()
    assert OSPMG_DISCOVERY_REFRESH_DEACTIVATED_EXCLUDED in _diag_codes(vm)
    assert vm.source_rows[0].discovery_source_state == "deactivated_excluded"
    assert vm.source_rows[0].excluded is True


# 10. Required acknowledgements are visible.
def test_required_acknowledgements_visible() -> None:
    vm = _build([_active_src()])
    ack_ids = {row.acknowledgement_id for row in vm.acknowledgement_rows}
    assert DISCOVERY_REFRESH_REQUIRED_ACKS == tuple(
        row.acknowledgement_id for row in vm.acknowledgement_rows
    )
    assert len(ack_ids) == 10


# 11. Missing acknowledgements block refresh readiness.
def test_missing_acknowledgements_block_readiness() -> None:
    vm = _build([_active_src()], acknowledgements={}, refresh_requested=True)
    assert vm.summary.readiness == _Readiness.BLOCKED_ACKNOWLEDGEMENT.value
    assert vm.summary.refresh_state == (
        OptionalSolverPluginManifestDiscoveryRefreshState.REFRESH_BLOCKED.value
    )
    assert "OSPMG_DISCOVERY_REFRESH_ACK_REQUIRED" in _diag_codes(vm)


# 12 & 13. Satisfied acks allow ready_preview_only / ready (not validation evidence).
def test_satisfied_acknowledgements_allow_ready() -> None:
    vm = _build([_active_src()], acknowledgements=_ALL_ACKS, refresh_requested=False)
    assert vm.summary.readiness == _Readiness.READY_PREVIEW_ONLY.value
    assert vm.summary.included_candidate_count == 1
    assert vm.summary.refresh_ready is True
    assert vm.summary.not_validation_evidence is True
    assert vm.not_validation_evidence is True
    assert "not validation evidence" in vm.source_rows[0].not_validation_evidence_text.lower()


# 14. Refresh result preview is not validation evidence.
def test_result_preview_not_validation_evidence() -> None:
    vm = _VM.result_preview([_active_src()], acknowledgements=_ALL_ACKS)
    assert vm.summary.readiness == _Readiness.RESULT_PREVIEW.value
    assert vm.summary.refresh_state == (
        OptionalSolverPluginManifestDiscoveryRefreshState.REFRESH_RESULT_PREVIEW.value
    )
    assert vm.summary.not_validation_evidence is True


# 15. Trust label is not certification.
def test_trust_label_is_not_certification() -> None:
    vm = _build([_active_src()], acknowledgements=_ALL_ACKS)
    badge_text = " ".join(b.trust_label_is_not_certification for b in vm.trust_badges).lower()
    guidance = " ".join(vm.guidance_text).lower()
    assert "not certification" in badge_text or "not certification" in guidance


# 16-19. Required safety acknowledgements exist.
def test_safety_acknowledgements_exist() -> None:
    vm = _build([_active_src()])
    ack_ids = {row.acknowledgement_id for row in vm.acknowledgement_rows}
    assert ACK_REFRESH_NOT_INSTALL in ack_ids
    assert ACK_REFRESH_NOT_SOLVER_EXECUTION in ack_ids
    assert ACK_NO_NETWORK_FETCH in ack_ids
    assert ACK_NO_PLUGIN_PACKAGE_IMPORT in ack_ids


# 20. Conflict blocker produces OSPMG_DISCOVERY_REFRESH_CONFLICT_BLOCKED.
def test_conflict_blocker_diagnostic() -> None:
    vm = _build(
        [_active_src(stack_id="gmsh", has_conflict=True)],
        acknowledgements=_ALL_ACKS,
        refresh_requested=True,
    )
    assert OSPMG_DISCOVERY_REFRESH_CONFLICT_BLOCKED in _diag_codes(vm)
    assert vm.summary.readiness == _Readiness.BLOCKED_CONFLICT.value
    assert vm.conflict_rows


# 21. Unsafe claim produces OSPMG_DISCOVERY_REFRESH_UNSAFE_CLAIM.
def test_unsafe_claim_diagnostic() -> None:
    vm = _build(
        [_active_src(stack_id="u", has_unsafe_claim=True,
                     unsafe_claim_indicators=("certification claim",))],
        acknowledgements=_ALL_ACKS,
        refresh_requested=True,
    )
    assert OSPMG_DISCOVERY_REFRESH_UNSAFE_CLAIM in _diag_codes(vm)
    assert vm.summary.readiness == _Readiness.BLOCKED_UNSAFE_CLAIM.value
    assert vm.unsafe_claim_rows


# 22. Active candidate required diagnostic surfaces.
def test_active_candidate_required_diagnostic() -> None:
    vm = _build([], acknowledgements=_ALL_ACKS, activation_state_supplied=True)
    assert OSPMG_DISCOVERY_REFRESH_ACTIVE_CANDIDATE_REQUIRED in _diag_codes(vm)


# 23 & 24. Deactivated excluded diagnostic and built-ins-win policy visible.
def test_deactivated_excluded_and_builtins_win_policy() -> None:
    vm = _build(
        [_active_src(stack_id="gmsh", has_conflict=True)],
        acknowledgements=_ALL_ACKS,
        refresh_requested=True,
    )
    conflict = vm.conflict_rows[0]
    assert conflict.built_ins_win_default is True
    assert "built-ins win by default" in conflict.conflict_policy.lower()
    guidance = " ".join(vm.guidance_text).lower()
    assert "built-in manifests win by default" in guidance


# 25. Unsafe actions are disabled.
def test_unsafe_actions_disabled() -> None:
    vm = _build([_active_src()], acknowledgements=_ALL_ACKS)
    Action = OptionalSolverPluginManifestDiscoveryRefreshAction
    states = {a.action: a for a in vm.actions}
    for action in (
        Action.RUN_DISCOVERY,
        Action.RUN_VALIDATION,
        Action.INSTALL_DEPENDENCY,
        Action.EXECUTE_SOLVER,
        Action.CLOSE_ISSUE,
    ):
        assert states[action].enabled is False
        assert states[action].available is False


# 26. Summary counts are deterministic.
def test_summary_counts_deterministic() -> None:
    sources = [
        _active_src(stack_id="ready_one"),
        _active_src(stack_id="conflict_one", has_conflict=True),
        _active_src(stack_id="deact_one", activation_state="deactivated"),
    ]
    vm = _build(sources, acknowledgements=_ALL_ACKS, refresh_requested=True)
    assert vm.summary.active_candidate_count == 2
    assert vm.summary.deactivated_excluded_count == 1
    assert vm.summary.conflict_blocked_count == 1
    assert vm.reserved_diagnostic_codes == OSPMG_DISCOVERY_REFRESH_DIAGNOSTIC_CODES
    assert len(OSPMG_DISCOVERY_REFRESH_DIAGNOSTIC_CODES) == 14


# 27. Redacted source references.
def test_redacted_source_references() -> None:
    vm = _build([_active_src()], acknowledgements=_ALL_ACKS)
    row = vm.source_rows[0]
    assert "/" not in row.source_reference_display
    assert "\\" not in row.source_reference_display
    assert row.redacted_source_reference is True


# 28. In-memory summary writes no files.
def test_render_summary_writes_no_files(tmp_path: Path) -> None:
    vm = _build([_active_src()], acknowledgements=_ALL_ACKS)
    payload = render_optional_solver_plugin_manifest_discovery_refresh_summary(vm)
    assert isinstance(payload, dict)
    assert payload["not_validation_evidence"] is True
    assert payload["discovery_execution_performed"] is False
    assert payload["network_fetch_performed"] is False
    assert not list(tmp_path.iterdir())


# Honesty flags remain false across the summary.
def test_summary_honesty_flags_false() -> None:
    s = _build([_active_src()], acknowledgements=_ALL_ACKS).summary
    assert s.discovery_execution_performed is False
    assert s.validation_execution_performed is False
    assert s.solver_execution_performed is False
    assert s.dependency_installation_performed is False
    assert s.network_fetch_performed is False
    assert s.plugin_package_import_performed is False
    assert s.issue_mutation_performed is False
    assert s.release_mutation_performed is False
    assert s.certification_claimed is False


# 30. Docs mention non-actions and future gates.
def test_docs_mention_non_actions_and_future_gates() -> None:
    doc = (
        REPO_ROOT
        / "docs"
        / "experimental"
        / "optional_solver_plugin_manifest_discovery_refresh_viewmodel.md"
    )
    assert doc.exists()
    text = doc.read_text(encoding="utf-8").lower()
    assert "non-actions" in text
    assert "future gates" in text
    assert "pure" in text
    for phrase in (
        "no runtime discovery integration",
        "no passive discovery behavior change",
        "no discovery execution",
        "no validation execution",
        "no solver execution",
        "no dependency install",
        "certification",
    ):
        assert phrase in text
