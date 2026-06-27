from __future__ import annotations

import ast
import importlib
from pathlib import Path

from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestActivationCandidateInput,
    build_optional_solver_plugin_manifest_activation_viewmodel,
)
from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestDeactivationCandidateInput as Cand,
)
from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestDeactivationViewModel as VM,
)
from osw.experimental.optional_solvers import (
    build_optional_solver_plugin_manifest_deactivation_viewmodel as build,
)
from osw.experimental.optional_solvers import (
    render_optional_solver_plugin_manifest_deactivation_summary as render_summary,
)
from osw.experimental.optional_solvers.plugin_manifest_deactivation_viewmodel import (
    ACK_CONFLICT_OR_SHARED_STACK_WARNING,
    ACK_DEACTIVATION_HISTORY_VISIBLE,
    ACK_NOT_DEPENDENCY_UNINSTALL,
    ACK_NOT_FILE_DELETION,
    ACK_NOT_ISSUE_CLOSURE,
    ACK_NOT_RELEASE_MUTATION,
    ACK_NOT_SOLVER_UNINSTALL,
    ACK_NOT_VALIDATION_EVIDENCE_DELETION,
    DEACTIVATION_ALWAYS_REQUIRED_ACKS,
)

MODULE_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "osw"
    / "experimental"
    / "optional_solvers"
    / "plugin_manifest_deactivation_viewmodel.py"
)
DOC = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_deactivation_viewmodel.md"
)

_ALL_ACKS = {ack: True for ack in DEACTIVATION_ALWAYS_REQUIRED_ACKS}
_ALL_ACKS_WITH_SHARED = {**_ALL_ACKS, ACK_CONFLICT_OR_SHARED_STACK_WARNING: True}


def _codes(view_model) -> set[str]:
    return {d.code for d in view_model.diagnostics}


# 1. Module import works without GUI extras.
def test_module_imports_without_gui_extras() -> None:
    module = importlib.import_module(
        "osw.experimental.optional_solvers.plugin_manifest_deactivation_viewmodel"
    )
    assert hasattr(module, "OptionalSolverPluginManifestDeactivationViewModel")


# 2 + 3 + 34. No PySide/Qt, file IO, deletion, subprocess, network, plugin import,
# discovery execution, uninstall, solver execution, or pathlib existence path.
def test_module_has_no_pyside_qt_or_unsafe_imports() -> None:
    tree = ast.parse(MODULE_SOURCE.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    forbidden_roots = {
        "subprocess", "socket", "requests", "urllib", "http", "pathlib", "os",
        "shutil", "gmsh", "meshio", "pyvista", "vtk", "CoolProp", "cantera",
    }
    for module in modules:
        root = module.split(".")[0]
        assert root not in forbidden_roots, module
        assert "pyside" not in module.lower()
        assert "pyqt" not in module.lower()
        assert not module.lower().startswith("qt")


def test_module_source_has_no_unsafe_or_mutation_paths() -> None:
    source = MODULE_SOURCE.read_text(encoding="utf-8")
    for phrase in (
        "QProcess",
        "subprocess",
        "os.system",
        "discover_builtin_optional_solvers",
        "discover_optional_solver_manifests",
        "pip uninstall",
        "pip install",
        "conda remove",
        "gh issue",
        "gh release",
        ".unlink(",
        ".rmdir(",
        "shutil.rmtree",
        ".write_text(",
        ".write_bytes(",
        ".exists(",
        "open(",
    ):
        assert phrase not in source


# 4. Empty/no-activation state reports deactivation unavailable.
def test_unavailable_when_no_activation_state() -> None:
    vm = VM.unavailable()
    assert vm.summary.readiness == "unavailable_no_activation_state"
    assert vm.summary.state == "deactivation_blocked" or vm.summary.state
    assert vm.summary.deactivation_candidate_count == 0


# 5 + 26. No active candidates reports active-required diagnostic.
def test_no_active_candidates_reports_active_required() -> None:
    vm = build(
        [Cand(stack_id="x", activation_state="inactive_preview")],
        acknowledgements=_ALL_ACKS,
    )
    assert vm.summary.readiness == "unavailable_no_active_candidates"
    assert "OSPMG_DEACTIVATION_ACTIVE_REQUIRED" in _codes(vm)


# 6 + 32. Active candidate from supplied data is untrusted by default; refs redacted.
def test_active_candidate_untrusted_by_default_and_redacted() -> None:
    vm = build(
        [Cand(stack_id="user", source_reference="C:/secret/x/m.json")],
        acknowledgements={},
    )
    row = vm.candidate_rows[0]
    assert row.is_untrusted is True
    assert row.redacted_source_reference is True
    assert "/" not in row.source_reference_display
    assert chr(92) not in row.source_reference_display
    assert row.source_reference_display == "m.json"


# 7 + 19-24. Required acknowledgements are visible (all categories present).
def test_required_acknowledgements_are_visible() -> None:
    vm = build([Cand(stack_id="user")], acknowledgements={})
    ack_ids = {row.acknowledgement_id for row in vm.acknowledgement_rows}
    for ack in (
        ACK_NOT_FILE_DELETION,
        ACK_NOT_DEPENDENCY_UNINSTALL,
        ACK_NOT_SOLVER_UNINSTALL,
        ACK_NOT_ISSUE_CLOSURE,
        ACK_NOT_RELEASE_MUTATION,
        ACK_NOT_VALIDATION_EVIDENCE_DELETION,
        ACK_DEACTIVATION_HISTORY_VISIBLE,
    ):
        assert ack in ack_ids


# 8 + 27. Missing acknowledgements block deactivation readiness + ack-required diag.
def test_missing_acknowledgements_block_readiness() -> None:
    vm = build([Cand(stack_id="user")], acknowledgements={})
    assert vm.summary.readiness == "blocked_acknowledgement"
    assert "OSPMG_DEACTIVATION_ACK_REQUIRED" in _codes(vm)
    blocking = [r for r in vm.acknowledgement_rows if r.blocking]
    assert blocking, "missing required acknowledgements must be blocking"


# 9 + 10. Satisfied acknowledgements allow ready_non_persistent; ready is not persisted.
def test_satisfied_acknowledgements_allow_ready_non_persistent() -> None:
    vm = build([Cand(stack_id="user")], acknowledgements=_ALL_ACKS)
    assert vm.summary.readiness == "ready_non_persistent"
    assert vm.candidate_rows[0].readiness == "ready_non_persistent"
    # Ready is not persisted and performs no deactivation.
    assert vm.summary.deactivation_performed is False


# 11. Deactivated state is not validation evidence.
def test_deactivated_is_not_validation_evidence() -> None:
    vm = VM.all_deactivated([Cand(stack_id="user")])
    assert vm.not_validation_evidence is True
    assert vm.summary.not_validation_evidence is True
    assert any(
        "not validation evidence" in b.deactivated_is_not_validation_evidence.lower()
        for b in vm.trust_badges
    )


# 12. Deactivated state is not validation failure.
def test_deactivated_is_not_validation_failure() -> None:
    vm = VM.all_deactivated([Cand(stack_id="user")])
    assert "OSPMG_DEACTIVATION_NOT_VALIDATION" in _codes(vm)
    assert "not a validation failure" in vm.candidate_rows[0].not_validation_failure_text.lower()


# 13. Deactivated state is not file deletion.
def test_deactivation_is_not_file_deletion() -> None:
    vm = VM.all_deactivated([Cand(stack_id="user")])
    assert "OSPMG_DEACTIVATION_NOT_FILE_DELETE" in _codes(vm)
    assert "not file deletion" in vm.candidate_rows[0].not_file_deletion_text.lower()
    assert vm.summary.file_deletion_performed is False


# 14 + 15. Deactivation is not dependency uninstall and not solver uninstall.
def test_deactivation_is_not_uninstall() -> None:
    vm = VM.all_deactivated([Cand(stack_id="user")])
    assert "OSPMG_DEACTIVATION_NOT_UNINSTALL" in _codes(vm)
    assert vm.summary.dependency_uninstall_performed is False
    assert vm.summary.solver_uninstall_performed is False
    assert "not uninstall" in vm.candidate_rows[0].not_uninstall_text.lower()
    assert "No dependency uninstall." in vm.safety_text
    assert "No solver uninstall." in vm.safety_text


# 16 + 17. Historical evidence retained is visible; skipped-missing remains.
def test_historical_evidence_retained_visible() -> None:
    vm = build(
        [Cand(stack_id="user", historical_evidence_state="skipped_missing")],
        acknowledgements=_ALL_ACKS,
    )
    assert vm.evidence_rows
    row = vm.evidence_rows[0]
    assert row.historical_evidence_state == "skipped_missing"
    assert row.evidence_retained is True
    assert "skipped-missing" in row.skipped_missing_remains_text.lower()
    assert "OSPMG_DEACTIVATION_EVIDENCE_RETAINED" in _codes(vm)
    assert vm.summary.evidence_retained is True


# 18. Trust label is not certification.
def test_trust_label_is_not_certification() -> None:
    vm = build([Cand(stack_id="user")], acknowledgements=_ALL_ACKS)
    assert vm.trust_badges
    assert all(
        "not certification" in b.trust_label_is_not_certification.lower()
        for b in vm.trust_badges
    )
    assert any("trust label is not certification" in g.lower() for g in vm.guidance_text)


# 25 + 29. Shared-stack warning diagnostic + built-ins-win policy visible.
def test_shared_stack_warning_and_builtins_win_policy() -> None:
    vm = build(
        [Cand(stack_id="gmsh", has_shared_stack=True, shared_stack_indicators=("dup",))],
        acknowledgements=_ALL_ACKS,
    )
    assert vm.summary.readiness == "blocked_shared_stack_warning"
    assert "OSPMG_DEACTIVATION_SHARED_STACK_WARNING" in _codes(vm)
    assert vm.shared_stack_rows
    shared = vm.shared_stack_rows[0]
    assert shared.built_ins_win_default is True
    assert "does not deactivate built-ins" in (
        shared.deactivating_user_source_keeps_built_ins.lower()
    )
    # The shared-stack ack clears the block.
    vm2 = build(
        [Cand(stack_id="gmsh", has_shared_stack=True)],
        acknowledgements=_ALL_ACKS_WITH_SHARED,
    )
    assert vm2.summary.readiness == "ready_non_persistent"
    # The conditional ack becomes required when a shared stack exists.
    ack_required = {
        r.acknowledgement_id: r.required for r in vm.acknowledgement_rows
    }
    assert ack_required[ACK_CONFLICT_OR_SHARED_STACK_WARNING] is True


def test_state_conflict_blocks_and_diagnoses() -> None:
    vm = build(
        [Cand(stack_id="x", has_state_conflict=True)],
        acknowledgements=_ALL_ACKS_WITH_SHARED,
    )
    assert vm.summary.readiness == "blocked_state_conflict"
    assert "OSPMG_DEACTIVATION_STATE_CONFLICT" in _codes(vm)


# 28. Persistence-not-implemented diagnostic is surfaced.
def test_persistence_not_implemented_diagnostic_surfaced() -> None:
    vm = build([Cand(stack_id="user")], acknowledgements=_ALL_ACKS)
    assert "OSPMG_DEACTIVATION_PERSISTENCE_NOT_IMPLEMENTED" in _codes(vm)


# 30. Action states disable file deletion, uninstall, discovery, validation,
# solver execution, close issue, release mutation.
def test_unsafe_action_states_disabled_and_unavailable() -> None:
    vm = build([Cand(stack_id="user")], acknowledgements=_ALL_ACKS)
    actions = {a.action.value: a for a in vm.actions}
    for name in (
        "run_discovery",
        "run_validation",
        "uninstall_dependency",
        "uninstall_solver",
        "execute_solver",
        "close_issue",
    ):
        assert actions[name].enabled is False
        assert actions[name].available is False
    # Deactivate/reactivate remain future-only (available but disabled).
    assert actions["deactivate_candidate"].enabled is False
    assert actions["reactivate_candidate"].enabled is False
    # No action is enabled in this pure view-model gate.
    assert all(not a.enabled for a in vm.actions)


# 31. Summary counts are deterministic.
def test_summary_counts_are_deterministic() -> None:
    candidates = [
        Cand(stack_id="a"),
        Cand(stack_id="b"),
        Cand(stack_id="c", deactivated=True, activation_state="deactivated"),
        Cand(stack_id="bi", built_in=True, is_untrusted=False, trust_label="built_in"),
    ]
    vm1 = build(candidates, acknowledgements=_ALL_ACKS)
    vm2 = build(candidates, acknowledgements=_ALL_ACKS)
    assert vm1.summary == vm2.summary
    assert vm1.summary.active_candidate_count == 2
    assert vm1.summary.deactivated_count == 1
    # built-in is excluded from the deactivation candidate universe.
    assert vm1.summary.deactivation_candidate_count == 3
    assert vm1.summary.deactivation_ready_count == 2


# 33. In-memory summary writes no files and stays honest.
def test_render_summary_writes_no_files_and_is_honest() -> None:
    vm = build([Cand(stack_id="user", source_reference="C:/x/m.json")], acknowledgements=_ALL_ACKS)
    payload = render_summary(vm)
    assert isinstance(payload, dict)
    for flag in (
        "file_deletion_performed",
        "dependency_uninstall_performed",
        "solver_uninstall_performed",
        "discovery_execution_performed",
        "validation_execution_performed",
        "solver_execution_performed",
        "issue_mutation_performed",
        "release_mutation_performed",
        "certification_claimed",
    ):
        assert payload[flag] is False
    assert payload["not_validation_evidence"] is True
    # references in the redacted payload carry no path separators
    for cand in payload["candidates"]:
        assert "/" not in cand["source_reference_display"]
        assert chr(92) not in cand["source_reference_display"]


# 36. Adapts the OSW-EXP-079 activation view-model without mutating it.
def test_from_activation_viewmodel_adapter() -> None:
    activation = build_optional_solver_plugin_manifest_activation_viewmodel(
        [
            OptionalSolverPluginManifestActivationCandidateInput(
                stack_id="user", source_reference="C:/x/m.json"
            )
        ],
        active_stack_ids=["user"],
    )
    before = activation.candidate_rows
    vm = VM.from_activation_viewmodel(activation, acknowledgements=_ALL_ACKS)
    # Activation view-model is unchanged (no mutation).
    assert activation.candidate_rows is before
    assert vm.candidate_rows
    assert vm.candidate_rows[0].stack_id == "user"
    assert vm.candidate_rows[0].is_untrusted is True


# 35. Docs mention non-actions and future gates.
def test_docs_mention_non_actions_and_future_gates() -> None:
    assert DOC.exists()
    text = DOC.read_text(encoding="utf-8").lower()
    assert "non-actions" in text
    assert "future gates" in text
    for phrase in (
        "no deactivation persistence",
        "no file deletion",
        "no dependency uninstall",
        "no solver uninstall",
        "no discovery execution",
        "no validation execution",
        "no solver execution",
        "deactivation is not deletion",
        "deactivation is not uninstall",
        "trust label is not certification",
    ):
        assert phrase in text
