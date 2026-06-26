from __future__ import annotations

import ast
from pathlib import Path

from osw.experimental.optional_solvers import (
    OSPMG_ACTIVATION_DIAGNOSTIC_CODES,
    OptionalSolverPluginManifestActivationAction,
    OptionalSolverPluginManifestActivationCandidateInput,
    OptionalSolverPluginManifestActivationReadiness,
    OptionalSolverPluginManifestActivationState,
    OptionalSolverPluginManifestActivationViewModel,
    build_optional_solver_plugin_manifest_activation_viewmodel,
    render_optional_solver_plugin_manifest_activation_summary,
    summarize_optional_solver_plugin_manifest_activation_viewmodel,
)
from osw.experimental.optional_solvers import (
    plugin_manifest_activation_viewmodel as module_under_test,
)
from osw.experimental.optional_solvers.plugin_manifest_activation_viewmodel import (
    ACK_NO_CERTIFICATION,
    ACK_NO_DEPENDENCY_INSTALL,
    ACK_NO_ISSUE_CLOSURE,
    ACK_NO_SOLVER_EXECUTION,
    ACK_NO_VALIDATION_PASS,
    ACK_UNTRUSTED_SOURCE,
    OSPMG_ACTIVATION_CONFLICT_BLOCKED,
    OSPMG_ACTIVATION_DEACTIVATED,
    OSPMG_ACTIVATION_PREVIEW_REQUIRED,
    OSPMG_ACTIVATION_SCHEMA_BLOCKED,
    OSPMG_ACTIVATION_UNSAFE_CLAIM,
    OSPMG_ACTIVATION_UNTRUSTED_SOURCE,
)
from osw.experimental.optional_solvers.plugin_manifest_loader import (
    load_optional_solver_plugin_manifest_json,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "optional_solvers" / "plugin_manifests"
VALID_USER = FIXTURES / "valid_user_local_manifest.json"

_ALL_ACKS = {
    ACK_UNTRUSTED_SOURCE: True,
    ACK_NO_VALIDATION_PASS: True,
    ACK_NO_DEPENDENCY_INSTALL: True,
    ACK_NO_SOLVER_EXECUTION: True,
    ACK_NO_ISSUE_CLOSURE: True,
    ACK_NO_CERTIFICATION: True,
}

_Readiness = OptionalSolverPluginManifestActivationReadiness
_State = OptionalSolverPluginManifestActivationState
_VM = OptionalSolverPluginManifestActivationViewModel


def _candidate(**kwargs) -> OptionalSolverPluginManifestActivationCandidateInput:
    base = {"stack_id": "user_stack", "source_reference": "C:/secret/x/manifest.json"}
    base.update(kwargs)
    return OptionalSolverPluginManifestActivationCandidateInput(**base)


def _diag_codes(view_model) -> set[str]:
    codes = {d.code for d in view_model.diagnostics}
    for row in view_model.candidate_rows:
        codes.update(row.diagnostics)
    return codes


def _action(view_model, action) -> object:
    for state in view_model.actions:
        if state.action == action:
            return state
    raise AssertionError(f"action not found: {action}")


# 1. Module import works without GUI extras.
def test_module_import_is_lightweight() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel([_candidate()])
    text = summarize_optional_solver_plugin_manifest_activation_viewmodel(vm)
    assert "activation" in text.lower()


# 2. Module has no PySide/Qt / subprocess / network import.
def _imported_modules() -> set[str]:
    tree = ast.parse(Path(module_under_test.__file__).read_text(encoding="utf-8"))
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


def test_module_has_no_file_io_or_pathlib() -> None:
    source = Path(module_under_test.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "open(",
        ".read_text(",
        ".read_bytes(",
        "json.load",
        "pathlib",
        ".exists(",
        "Path(",
        "os.system",
    ):
        assert forbidden not in source


# 3 & 4. Empty/no-preview reports preview required + OSPMG_ACTIVATION_PREVIEW_REQUIRED.
def test_empty_reports_preview_required() -> None:
    vm = OptionalSolverPluginManifestActivationViewModel.empty()
    assert vm.preview_available is False
    assert vm.summary.preview_required_count == 1
    assert vm.candidate_rows == ()
    assert OSPMG_ACTIVATION_PREVIEW_REQUIRED in _diag_codes(vm)
    # preview_required() is an alias.
    assert _VM.preview_required().preview_available is False


# 5. Candidate from supplied preview data is untrusted by default.
def test_candidate_from_loader_is_untrusted_by_default() -> None:
    report = load_optional_solver_plugin_manifest_json(VALID_USER)
    vm = OptionalSolverPluginManifestActivationViewModel.from_loader_report(report)
    assert vm.candidate_rows
    assert any(row.is_untrusted for row in vm.candidate_rows)
    assert OSPMG_ACTIVATION_UNTRUSTED_SOURCE in _diag_codes(vm)
    assert vm.summary.third_party_manifests_trusted_by_default is False


# 6. Required acknowledgements are visible.
def test_required_acknowledgements_visible() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel([_candidate()])
    ack_ids = {row.acknowledgement_id for row in vm.acknowledgement_rows}
    assert ACK_UNTRUSTED_SOURCE in ack_ids
    assert ACK_NO_VALIDATION_PASS in ack_ids
    assert vm.summary.acknowledgement_required_count >= 5


# 7. Missing acknowledgements block activation readiness.
def test_missing_acknowledgements_block_readiness() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel(
        [_candidate()], acknowledgements={}, requested_stack_ids=["user_stack"]
    )
    row = vm.candidate_rows[0]
    assert row.readiness == _Readiness.BLOCKED_ACKNOWLEDGEMENT.value
    assert row.activation_state == _State.ACTIVATION_BLOCKED.value


# 8 & 9. Satisfied acks allow activation_ready, which is not validation evidence.
def test_satisfied_acknowledgements_allow_ready() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel(
        [_candidate()], acknowledgements=_ALL_ACKS, requested_stack_ids=["user_stack"]
    )
    row = vm.candidate_rows[0]
    assert row.readiness == OptionalSolverPluginManifestActivationReadiness.READY.value
    assert vm.summary.activation_ready_count == 1
    # Ready is not validation evidence.
    assert vm.summary.not_validation_evidence is True
    assert vm.not_validation_evidence is True
    assert "not validation evidence" in row.not_validation_evidence_text.lower()


# 10. Active candidate is not validation evidence.
def test_active_candidate_is_not_validation_evidence() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel(
        [_candidate()], active_stack_ids=["user_stack"]
    )
    row = vm.candidate_rows[0]
    assert row.readiness == OptionalSolverPluginManifestActivationReadiness.ACTIVE_CANDIDATE.value
    assert vm.summary.activation_performed is True
    assert vm.summary.not_validation_evidence is True
    badge_texts = " ".join(
        b.active_candidate_is_not_validation_evidence for b in vm.trust_badges
    ).lower()
    assert "not validation evidence" in badge_texts


# 11. Trust label is not certification.
def test_trust_label_is_not_certification() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel([_candidate()])
    badge_text = " ".join(b.trust_label_is_not_certification for b in vm.trust_badges).lower()
    guidance = " ".join(vm.guidance_text).lower()
    assert "not certification" in badge_text or "not certification" in guidance


# 12-14. No-install / no-solver-execution / no-certification acknowledgements exist.
def test_safety_acknowledgements_exist() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel([_candidate()])
    ack_ids = {row.acknowledgement_id for row in vm.acknowledgement_rows}
    assert ACK_NO_DEPENDENCY_INSTALL in ack_ids
    assert ACK_NO_SOLVER_EXECUTION in ack_ids
    assert ACK_NO_CERTIFICATION in ack_ids


# 15. Conflict blocker produces OSPMG_ACTIVATION_CONFLICT_BLOCKED.
def test_conflict_blocker_diagnostic() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel(
        [_candidate(stack_id="gmsh", has_conflict=True)], requested_stack_ids=["gmsh"]
    )
    assert OSPMG_ACTIVATION_CONFLICT_BLOCKED in _diag_codes(vm)
    assert vm.candidate_rows[0].readiness == (
        OptionalSolverPluginManifestActivationReadiness.BLOCKED_CONFLICT.value
    )


# 16. Schema blocker produces OSPMG_ACTIVATION_SCHEMA_BLOCKED.
def test_schema_blocker_diagnostic() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel(
        [_candidate(has_schema_blocker=True)], requested_stack_ids=["user_stack"]
    )
    assert OSPMG_ACTIVATION_SCHEMA_BLOCKED in _diag_codes(vm)


# 17. Unsafe claim produces OSPMG_ACTIVATION_UNSAFE_CLAIM.
def test_unsafe_claim_diagnostic() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel(
        [_candidate(has_unsafe_claim=True, unsafe_claim_indicators=("certification claim",))],
        requested_stack_ids=["user_stack"],
    )
    assert OSPMG_ACTIVATION_UNSAFE_CLAIM in _diag_codes(vm)


# 18. Built-ins-win / conflict policy is visible.
def test_builtins_win_policy_visible() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel(
        [_candidate(stack_id="gmsh", has_conflict=True)], requested_stack_ids=["gmsh"]
    )
    assert vm.conflict_rows
    conflict = vm.conflict_rows[0]
    assert conflict.built_ins_win_default is True
    assert "built-in" in conflict.conflict_policy.lower()
    guidance = " ".join(vm.guidance_text).lower()
    assert "built-in manifests win by default" in guidance


# 19. Deactivated state is represented.
def test_deactivated_state() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel(
        [_candidate()], deactivated_stack_ids=["user_stack"]
    )
    row = vm.candidate_rows[0]
    assert row.readiness == OptionalSolverPluginManifestActivationReadiness.DEACTIVATED.value
    assert row.activation_state == OptionalSolverPluginManifestActivationState.DEACTIVATED.value
    assert OSPMG_ACTIVATION_DEACTIVATED in _diag_codes(vm)
    assert vm.summary.deactivated_count == 1


# 20. Action states disable discovery, validation, install, solver execution, close issue.
def test_unsafe_actions_disabled() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel([_candidate()])
    Action = OptionalSolverPluginManifestActivationAction
    for action in (
        Action.RUN_DISCOVERY_WITH_ACTIVATED_MANIFESTS,
        Action.RUN_VALIDATION,
        Action.INSTALL_DEPENDENCY,
        Action.EXECUTE_SOLVER,
        Action.CLOSE_ISSUE,
    ):
        state = _action(vm, action)
        assert state.enabled is False
        assert state.available is False
    # Activation itself is also disabled in this view-model gate.
    assert _action(vm, Action.ACTIVATE_CANDIDATE).enabled is False


# 21. Summary counts are deterministic.
def test_summary_counts_deterministic() -> None:
    candidates = [
        _candidate(stack_id="ready_one"),
        _candidate(stack_id="schema_one", has_schema_blocker=True),
    ]
    vm = build_optional_solver_plugin_manifest_activation_viewmodel(
        candidates, acknowledgements=_ALL_ACKS, requested_stack_ids=["ready_one", "schema_one"]
    )
    assert vm.summary.activation_candidates_count == 2
    assert vm.summary.activation_ready_count == 1
    assert vm.summary.activation_blocked_count == 1
    # Diagnostic codes reserved tuple is exposed and complete.
    assert vm.reserved_activation_diagnostic_codes == OSPMG_ACTIVATION_DIAGNOSTIC_CODES
    assert len(OSPMG_ACTIVATION_DIAGNOSTIC_CODES) == 12


# 22. Redacted source references are exposed safely.
def test_redacted_source_references() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel([_candidate()])
    row = vm.candidate_rows[0]
    assert "/" not in row.source_reference_display
    assert "\\" not in row.source_reference_display
    assert row.redacted_source_reference is True


# 23. In-memory summary writes no files.
def test_render_summary_writes_no_files(tmp_path: Path) -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel(
        [_candidate()], acknowledgements=_ALL_ACKS, requested_stack_ids=["user_stack"]
    )
    payload = render_optional_solver_plugin_manifest_activation_summary(vm)
    assert isinstance(payload, dict)
    assert payload["preview_only"] is True
    assert payload["activation_performed"] is False
    assert payload["validation_execution_performed"] is False
    assert payload["certification_claimed"] is False
    assert not list(tmp_path.iterdir())


# State machine: no direct activation without preview (unavailable_before_preview).
def test_unavailable_before_preview() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel(
        [_candidate()], preview_available=False
    )
    row = vm.candidate_rows[0]
    assert row.readiness == (
        OptionalSolverPluginManifestActivationReadiness.UNAVAILABLE_BEFORE_PREVIEW.value
    )
    assert row.activation_state == (
        OptionalSolverPluginManifestActivationState.INACTIVE_PREVIEW.value
    )


# Honesty flags remain false across the summary.
def test_summary_honesty_flags_false() -> None:
    vm = build_optional_solver_plugin_manifest_activation_viewmodel([_candidate()])
    s = vm.summary
    assert s.validation_execution_performed is False
    assert s.discovery_execution_performed is False
    assert s.solver_execution_performed is False
    assert s.dependency_installation_performed is False
    assert s.issue_mutation_performed is False
    assert s.release_mutation_performed is False
    assert s.certification_claimed is False


# 27. Docs mention non-actions and future gates.
def test_docs_mention_non_actions_and_future_gates() -> None:
    doc = (
        REPO_ROOT
        / "docs"
        / "experimental"
        / "optional_solver_plugin_manifest_activation_viewmodel.md"
    )
    assert doc.exists()
    text = doc.read_text(encoding="utf-8").lower()
    assert "non-actions" in text
    assert "future gates" in text
    assert "pure" in text
    for phrase in (
        "no activation persistence",
        "no discovery",
        "no validation",
        "no solver execution",
        "no dependency install",
        "certification",
    ):
        assert phrase in text
