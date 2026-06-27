from __future__ import annotations

import ast
import importlib
from pathlib import Path

from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestDeactivationCandidateInput,
    build_optional_solver_plugin_manifest_deactivation_viewmodel,
)
from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestReactivationCandidateInput as Cand,
)
from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestReactivationViewModel as VM,
)
from osw.experimental.optional_solvers import (
    build_optional_solver_plugin_manifest_reactivation_viewmodel as build,
)
from osw.experimental.optional_solvers import (
    render_optional_solver_plugin_manifest_reactivation_summary as render_summary,
)
from osw.experimental.optional_solvers.plugin_manifest_reactivation_viewmodel import (
    ACK_CONFLICT_OR_SHARED_STACK_WARNING,
    ACK_NO_DISCOVERY_EXECUTION,
    ACK_NO_PLUGIN_PACKAGE_IMPORT,
    ACK_REACTIVATION_HISTORY_RETAINED,
    ACK_REACTIVATION_NO_SOLVER_EXECUTION,
    ACK_REACTIVATION_NOT_INSTALL,
    ACK_REACTIVATION_NOT_ISSUE_CLOSURE,
    ACK_REACTIVATION_NOT_RELEASE_MUTATION,
    ACK_REACTIVATION_NOT_TRUST_RESTORATION,
    ACK_REACTIVATION_NOT_VALIDATION,
    ACK_REACTIVATION_REQUIRES_ACTIVATION_REVIEW,
    ACK_STALE_SOURCE_REQUIRES_REPREVIEW,
    ACK_TRUST_LABEL_NOT_CERTIFICATION,
    ACK_UNTRUSTED_SOURCE,
    REACTIVATION_ALWAYS_REQUIRED_ACKS,
)

MODULE_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "osw"
    / "experimental"
    / "optional_solvers"
    / "plugin_manifest_reactivation_viewmodel.py"
)
DOC = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reactivation_viewmodel.md"
)

_ALL_ACKS = {ack: True for ack in REACTIVATION_ALWAYS_REQUIRED_ACKS}
_ALL_ACKS_SHARED = {**_ALL_ACKS, ACK_CONFLICT_OR_SHARED_STACK_WARNING: True}
_ALL_ACKS_STALE = {**_ALL_ACKS, ACK_STALE_SOURCE_REQUIRES_REPREVIEW: True}


def _codes(view_model) -> set[str]:
    return {d.code for d in view_model.diagnostics}


# 1. Module import works without GUI extras.
def test_module_imports_without_gui_extras() -> None:
    module = importlib.import_module(
        "osw.experimental.optional_solvers.plugin_manifest_reactivation_viewmodel"
    )
    assert hasattr(module, "OptionalSolverPluginManifestReactivationViewModel")


# 2 + 3 + 46. No PySide/Qt, file IO, restore/rewrite/delete, subprocess, network,
# plugin import, discovery execution, install/uninstall, solver execution, pathlib.
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
        "pip install",
        "pip uninstall",
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


# 4. Empty/no-deactivation state reports reactivation unavailable.
def test_unavailable_when_no_deactivation_state() -> None:
    vm = VM.unavailable()
    assert vm.summary.readiness == "unavailable_no_deactivation_state"
    assert vm.summary.reactivation_candidate_count == 0


# 5 + 35. No deactivated candidates reports deactivated-required diagnostic.
def test_no_deactivated_candidates_reports_deactivated_required() -> None:
    vm = build(
        [Cand(stack_id="x", deactivated=False, activation_state="active_candidate")],
        acknowledgements=_ALL_ACKS,
    )
    assert vm.summary.readiness == "unavailable_no_deactivated_candidates"
    assert "OSPMG_REACTIVATION_DEACTIVATED_REQUIRED" in _codes(vm)


# 6 + 44. Deactivated candidate from supplied data is untrusted by default; redacted.
def test_deactivated_candidate_untrusted_by_default_and_redacted() -> None:
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


# 7 + 22-33. Required acknowledgements are visible (all categories present).
def test_required_acknowledgements_are_visible() -> None:
    vm = build(
        [Cand(stack_id="user", has_shared_stack=True, stale_source=True)],
        acknowledgements={},
    )
    ack_ids = {row.acknowledgement_id for row in vm.acknowledgement_rows}
    for ack in (
        ACK_REACTIVATION_NOT_VALIDATION,
        ACK_REACTIVATION_NOT_TRUST_RESTORATION,
        ACK_REACTIVATION_NOT_INSTALL,
        ACK_REACTIVATION_NO_SOLVER_EXECUTION,
        ACK_REACTIVATION_NOT_ISSUE_CLOSURE,
        ACK_REACTIVATION_NOT_RELEASE_MUTATION,
        ACK_REACTIVATION_HISTORY_RETAINED,
        ACK_REACTIVATION_REQUIRES_ACTIVATION_REVIEW,
        ACK_UNTRUSTED_SOURCE,
        ACK_CONFLICT_OR_SHARED_STACK_WARNING,
        ACK_STALE_SOURCE_REQUIRES_REPREVIEW,
        ACK_NO_DISCOVERY_EXECUTION,
        ACK_NO_PLUGIN_PACKAGE_IMPORT,
        ACK_TRUST_LABEL_NOT_CERTIFICATION,
    ):
        assert ack in ack_ids


# 8 + 36. Missing acknowledgements block readiness + ack-required diagnostic.
def test_missing_acknowledgements_block_readiness() -> None:
    vm = build([Cand(stack_id="user")], acknowledgements={})
    assert vm.summary.readiness == "blocked_acknowledgement"
    assert "OSPMG_REACTIVATION_ACK_REQUIRED" in _codes(vm)
    assert any(r.blocking for r in vm.acknowledgement_rows)


# 9 + 10 + 11 + 12. Satisfied acks -> ready; not persisted, not auto-activation,
# not trust restoration.
def test_satisfied_acknowledgements_allow_ready_non_persistent() -> None:
    vm = build([Cand(stack_id="user")], acknowledgements=_ALL_ACKS)
    assert vm.summary.readiness == "ready_non_persistent"
    assert vm.candidate_rows[0].readiness == "ready_non_persistent"
    assert vm.summary.reactivation_performed is False
    assert vm.summary.automatic_activation_performed is False
    assert vm.summary.trust_restoration_performed is False
    row = vm.candidate_rows[0]
    assert "not automatic activation" in row.not_automatic_activation_text.lower()
    assert "not trust restoration" in row.not_trust_restoration_text.lower()


# 13 + 14 + 15. Reactivation is not validation evidence/success/failure-reversal.
def test_reactivation_is_not_validation() -> None:
    vm = build(
        [Cand(stack_id="user", historical_evidence_state="skipped_missing")],
        acknowledgements=_ALL_ACKS,
    )
    assert vm.not_validation_evidence is True
    assert vm.summary.not_validation_evidence is True
    assert any(
        "not validation evidence" in b.reactivation_is_not_validation_evidence.lower()
        for b in vm.trust_badges
    )
    assert "OSPMG_REACTIVATION_NOT_VALIDATION" in _codes(vm)
    ev = vm.evidence_rows[0]
    assert "not validation success" in ev.not_validation_success_text.lower()
    assert "not validation failure reversal" in ev.not_validation_failure_reversal_text.lower()


# 16 + 17. Reactivation is not dependency installation / solver execution.
def test_reactivation_is_not_install_or_solver_execution() -> None:
    vm = build([Cand(stack_id="user")], acknowledgements=_ALL_ACKS)
    assert "OSPMG_REACTIVATION_NO_INSTALL" in _codes(vm)
    assert "OSPMG_REACTIVATION_NO_SOLVER_EXECUTION" in _codes(vm)
    assert vm.summary.dependency_installation_performed is False
    assert vm.summary.solver_execution_performed is False
    assert "No dependency installation." in vm.safety_text
    assert "No solver execution." in vm.safety_text


# 18 + 19 + 20. Deactivation history + historical evidence retained, skipped-missing.
def test_history_and_evidence_retained_visible() -> None:
    vm = build(
        [Cand(stack_id="user", historical_evidence_state="skipped_missing")],
        acknowledgements=_ALL_ACKS,
    )
    assert vm.summary.deactivation_history_retained is True
    assert vm.summary.evidence_retained is True
    assert "OSPMG_REACTIVATION_HISTORY_RETAINED" in _codes(vm)
    ev = vm.evidence_rows[0]
    assert ev.deactivation_history_retained is True
    assert "skipped-missing" in ev.skipped_missing_remains_text.lower()
    assert "not deleted or rewritten" in ev.evidence_not_deleted_text.lower()


# 21. Trust label is not certification.
def test_trust_label_is_not_certification() -> None:
    vm = build([Cand(stack_id="user")], acknowledgements=_ALL_ACKS)
    assert vm.trust_badges
    assert all(
        "not certification" in b.trust_label_is_not_certification.lower()
        for b in vm.trust_badges
    )
    assert any("trust label is not certification" in g.lower() for g in vm.guidance_text)


# 34. Stale source produces stale-source-repreview diagnostic; ack clears it.
def test_stale_source_blocks_and_diagnoses() -> None:
    vm = build(
        [Cand(stack_id="s", stale_source=True, source_reference="C:/x/m.json")],
        acknowledgements=_ALL_ACKS,
    )
    assert vm.summary.readiness == "blocked_stale_source_repreview"
    assert "OSPMG_REACTIVATION_STALE_SOURCE_REPREVIEW_REQUIRED" in _codes(vm)
    assert vm.stale_source_rows
    stale = vm.stale_source_rows[0]
    assert stale.repreview_required is True
    assert "not silently trusted" in stale.not_silently_trusted_text.lower()
    assert "no file io" in stale.no_file_io_text.lower()
    vm2 = build([Cand(stack_id="s", stale_source=True)], acknowledgements=_ALL_ACKS_STALE)
    assert vm2.summary.readiness == "ready_non_persistent"


# 37 + 41. Conflict blocker + built-ins-win/shared-stack policy.
def test_conflict_blocks_and_builtins_win_policy() -> None:
    vm = build([Cand(stack_id="gmsh", has_conflict=True)], acknowledgements=_ALL_ACKS)
    assert vm.summary.readiness == "blocked_conflict"
    assert "OSPMG_REACTIVATION_CONFLICT_BLOCKED" in _codes(vm)
    assert vm.shared_stack_rows
    shared = vm.shared_stack_rows[0]
    assert shared.built_ins_win_default is True
    assert "does not override built-ins" in (
        shared.reactivating_user_source_keeps_built_ins.lower()
    )


# 38. Shared-stack warning produces shared-stack diagnostic; ack clears block.
def test_shared_stack_warning_and_ack() -> None:
    vm = build(
        [Cand(stack_id="gmsh", has_shared_stack=True, shared_stack_indicators=("dup",))],
        acknowledgements=_ALL_ACKS,
    )
    assert vm.summary.readiness == "blocked_shared_stack_warning"
    assert "OSPMG_REACTIVATION_SHARED_STACK_WARNING" in _codes(vm)
    vm2 = build([Cand(stack_id="gmsh", has_shared_stack=True)], acknowledgements=_ALL_ACKS_SHARED)
    assert vm2.summary.readiness == "ready_non_persistent"


# 39 + 40. Persistence-not-implemented + future-gate diagnostics surfaced.
def test_persistence_and_future_gate_diagnostics_surfaced() -> None:
    vm = build([Cand(stack_id="user")], acknowledgements=_ALL_ACKS)
    assert "OSPMG_REACTIVATION_PERSISTENCE_NOT_IMPLEMENTED" in _codes(vm)
    assert "OSPMG_REACTIVATION_FUTURE_GATE" in _codes(vm)
    assert "OSPMG_REACTIVATION_REVIEW_REQUIRED" in _codes(vm)


def test_future_activation_required_state() -> None:
    vm = VM.all_future_activation_required([Cand(stack_id="user")], acknowledgements=_ALL_ACKS)
    assert vm.summary.readiness == "future_activation_required"
    assert vm.summary.future_activation_required_count == 1


# 42. Action states disable unsafe + activation/route actions; none enabled.
def test_unsafe_action_states_disabled_and_unavailable() -> None:
    vm = build([Cand(stack_id="user")], acknowledgements=_ALL_ACKS)
    actions = {a.action.value: a for a in vm.actions}
    for name in (
        "run_discovery",
        "run_validation",
        "install_dependency",
        "uninstall_dependency",
        "uninstall_solver",
        "execute_solver",
        "close_issue",
    ):
        assert actions[name].enabled is False
        assert actions[name].available is False
    # Reactivate/route remain future-only (disabled) — no automatic activation.
    assert actions["reactivate_candidate"].enabled is False
    assert actions["route_to_activation_review"].enabled is False
    assert all(not a.enabled for a in vm.actions)


# 43. Summary counts are deterministic.
def test_summary_counts_are_deterministic() -> None:
    candidates = [
        Cand(stack_id="a"),
        Cand(stack_id="b"),
        Cand(stack_id="bi", built_in=True, is_untrusted=False, trust_label="built_in"),
    ]
    vm1 = build(candidates, acknowledgements=_ALL_ACKS)
    vm2 = build(candidates, acknowledgements=_ALL_ACKS)
    assert vm1.summary == vm2.summary
    assert vm1.summary.deactivated_candidate_count == 2
    assert vm1.summary.reactivation_candidate_count == 2  # excludes built-in
    assert vm1.summary.reactivation_ready_count == 2


# 45. In-memory summary writes no files and stays honest.
def test_render_summary_writes_no_files_and_is_honest() -> None:
    vm = build([Cand(stack_id="user", source_reference="C:/x/m.json")], acknowledgements=_ALL_ACKS)
    payload = render_summary(vm)
    assert isinstance(payload, dict)
    for flag in (
        "automatic_activation_performed",
        "trust_restoration_performed",
        "file_restore_performed",
        "file_rewrite_performed",
        "file_deletion_performed",
        "dependency_installation_performed",
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
    for cand in payload["candidates"]:
        assert "/" not in cand["source_reference_display"]
        assert chr(92) not in cand["source_reference_display"]


# 49. Adapts the OSW-EXP-085 deactivation view-model without mutating it.
def test_from_deactivation_viewmodel_adapter() -> None:
    deactivation = build_optional_solver_plugin_manifest_deactivation_viewmodel(
        [
            OptionalSolverPluginManifestDeactivationCandidateInput(
                stack_id="user",
                source_reference="C:/x/m.json",
                deactivated=True,
                activation_state="deactivated",
            )
        ],
    )
    before = deactivation.candidate_rows
    vm = VM.from_deactivation_viewmodel(deactivation, acknowledgements=_ALL_ACKS)
    # Deactivation view-model is unchanged (no mutation).
    assert deactivation.candidate_rows is before
    assert vm.candidate_rows
    assert vm.candidate_rows[0].stack_id == "user"
    assert vm.candidate_rows[0].is_untrusted is True
    assert vm.summary.readiness == "ready_non_persistent"


# 47. Docs mention non-actions and future gates.
def test_docs_mention_non_actions_and_future_gates() -> None:
    assert DOC.exists()
    text = DOC.read_text(encoding="utf-8").lower()
    assert "non-actions" in text
    assert "future gates" in text
    for phrase in (
        "no reactivation persistence",
        "no automatic activation",
        "no trust restoration",
        "no file restore",
        "no discovery execution",
        "no validation execution",
        "no solver execution",
        "reactivation is not automatic activation",
        "reactivation is not trust restoration",
        "trust label is not certification",
    ):
        assert phrase in text
