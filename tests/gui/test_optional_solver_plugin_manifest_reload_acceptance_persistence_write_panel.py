from __future__ import annotations

import ast
import builtins
import importlib.util
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[2]
PANEL_SOURCE = REPO_ROOT / "src" / "osw" / "gui" / "dialogs" / (
    "optional_solver_plugin_manifest_reload_acceptance_persistence_write_panel.py"
)

PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None


@pytest.fixture()
def qapp():
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")
    from PySide6 import QtWidgets

    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _source() -> str:
    return PANEL_SOURCE.read_text(encoding="utf-8")


def _ready_view_model():
    from osw.experimental.optional_solvers.plugin_manifest_reload_acceptance_persistence_viewmodel import (  # noqa: E501
        OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel,
    )
    from osw.experimental.optional_solvers.plugin_manifest_reload_acceptance_viewmodel import (  # noqa: E501
        OptionalSolverPluginManifestReloadAcceptanceViewModel,
    )
    from osw.experimental.optional_solvers.plugin_manifest_reload_viewmodel import (
        OptionalSolverPluginManifestReloadViewModel,
    )

    acceptance = (
        OptionalSolverPluginManifestReloadAcceptanceViewModel.ready_for_future_acceptance(
            OptionalSolverPluginManifestReloadViewModel.sample_ready_for_review()
        )
    )
    return OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.ready_for_future_writer(  # noqa: E501
        acceptance
    )


class RecordingWriter:
    def __init__(self, result_factory=None):
        self.calls = []
        self.result_factory = result_factory

    def write(self, request):
        self.calls.append(request)
        if self.result_factory is not None:
            return self.result_factory(request)
        from osw.experimental.optional_solvers.plugin_manifest_reload_acceptance_persistence_writer import (  # noqa: E501
            OptionalSolverPluginManifestReloadAcceptancePersistenceWriter,
        )

        return OptionalSolverPluginManifestReloadAcceptancePersistenceWriter().write(
            request
        )


def _mapping_result(*, status: str, dry_run: bool, target: str = "state.json"):
    return {
        "status": status,
        "target_display": target,
        "target_redacted": True,
        "dry_run": dry_run,
        "planned": status == "planned",
        "written": status == "completed",
        "bytes_count": 12,
        "sha256": "abc123",
        "payload_kind": "optional_solver_plugin_manifest_reload_acceptance_persistence_record",
        "payload_schema_version": "osw-exp-126-reload-acceptance-persistence-writer-1",
        "diagnostics": (
            {
                "severity": "error" if status in {"blocked", "error"} else "info",
                "code": f"OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_{status.upper()}",
                "message": f"writer {status}",
                "section": "writer",
                "blocker": status in {"blocked", "error"},
                "suggested_fix": "review writer result",
            },
        ),
        "blockers": ("blocked",) if status == "blocked" else (),
        "warnings": (),
        "non_action_flags": {
            "runtime_reload_acceptance_performed": False,
            "project_schema_mutated": False,
            "validation_executed": False,
            "solver_executed": False,
            "issue_mutated": False,
            "release_mutated": False,
            "certification_claimed": False,
            "persistence_write_performed": status == "completed",
        },
        "payload": {},
        "write_performed": status == "completed",
        "persistence_write_performed": status == "completed",
        "runtime_reload_acceptance_performed": False,
        "project_schema_mutated": False,
    }


def _panel(qapp, **kwargs):
    from osw.gui.dialogs.optional_solver_plugin_manifest_reload_acceptance_persistence_write_panel import (  # noqa: E501
        OptionalSolverPluginManifestReloadAcceptancePersistenceWritePanel,
    )

    return OptionalSolverPluginManifestReloadAcceptancePersistenceWritePanel(
        view_model=_ready_view_model(),
        **kwargs,
    )


def test_module_imports_lazy_export_and_construction_is_inert(
    qapp,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs import (
        OptionalSolverPluginManifestReloadAcceptancePersistenceWritePanel,
    )
    from osw.gui.dialogs.optional_solver_plugin_manifest_reload_acceptance_persistence_write_panel import (  # noqa: E501
        OptionalSolverPluginManifestReloadAcceptancePersistenceWritePanel as DirectPanel,
    )

    writer = RecordingWriter()
    original_open = builtins.open

    def blocked_open(*args, **kwargs):
        raise AssertionError("construction attempted file IO")

    builtins.open = blocked_open
    try:
        panel = DirectPanel(view_model=_ready_view_model(), writer=writer)
    finally:
        builtins.open = original_open

    try:
        assert OptionalSolverPluginManifestReloadAcceptancePersistenceWritePanel is DirectPanel  # noqa: E501
        assert panel.objectName() == (
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceWritePanel"
        )
        assert writer.calls == []
        assert list(tmp_path.iterdir()) == []
        assert "target_required=yes" in panel.target_text()
        assert "write_ready=no" in panel.write_gate_text()
    finally:
        panel.close()
        panel.deleteLater()


def test_target_assignment_clear_and_view_model_change_invalidate_dry_run(
    qapp,
    tmp_path: Path,
) -> None:
    target = tmp_path / "state.json"
    writer = RecordingWriter()
    panel = _panel(qapp, writer=writer)
    try:
        panel.set_target_path(target)
        assert "target_required=no" in panel.target_text()
        assert "state.json" in panel.target_text()
        assert str(tmp_path) not in panel.rendered_text()
        assert not target.exists()

        panel.run_dry_run()
        assert len(writer.calls) == 1
        assert writer.calls[-1].dry_run is True
        assert "dry_run_fresh=yes" in panel.write_gate_text()
        assert not target.exists()

        panel.set_target_path(tmp_path / "other.json")
        assert "dry_run_fresh=no" in panel.write_gate_text()
        panel.run_dry_run()
        assert len(writer.calls) == 2
        panel.set_view_model(_ready_view_model())
        assert "dry_run_fresh=no" in panel.write_gate_text()
        panel.clear_target()
        assert "target_required=yes" in panel.target_text()
    finally:
        panel.close()
        panel.deleteLater()


def test_dry_run_without_target_blocks_without_writer_or_file(
    qapp,
    tmp_path: Path,
) -> None:
    writer = RecordingWriter()
    panel = _panel(qapp, writer=writer)
    try:
        result = panel.run_dry_run()
        assert result["status"] == "blocked"
        assert "TARGET_REQUIRED" in panel.diagnostics_text()
        assert writer.calls == []
        assert list(tmp_path.iterdir()) == []
    finally:
        panel.close()
        panel.deleteLater()


def test_dry_run_with_explicit_target_calls_writer_and_creates_no_file(
    qapp,
    tmp_path: Path,
) -> None:
    target = tmp_path / "state.json"
    writer = RecordingWriter()
    panel = _panel(qapp, writer=writer)
    try:
        panel.set_target_path(target)
        result = panel.run_dry_run()
        assert len(writer.calls) == 1
        assert writer.calls[-1].target_path == str(target)
        assert writer.calls[-1].dry_run is True
        assert result["status"] == "planned"
        assert result["planned"] is True
        assert result["written"] is False
        assert not target.exists()
        assert "bytes_count" in panel.writer_result_text()
        assert "sha256" in panel.writer_result_text()
        assert "payload_kind" in panel.dry_run_write_plan_text()
    finally:
        panel.close()
        panel.deleteLater()


@pytest.mark.parametrize(
    ("configure", "expected_code"),
    (
        (lambda panel, target: None, "TARGET_REQUIRED"),
        (
            lambda panel, target: panel.set_target_path(target),
            "DRY_RUN_REQUIRED",
        ),
        (
            lambda panel, target: (
                panel.set_target_path(target),
                panel.run_dry_run(),
                panel.set_target_path(target.with_name("other.json")),
            ),
            "STALE_DRY_RUN",
        ),
        (
            lambda panel, target: (
                panel.set_target_path(target),
                panel.run_dry_run(),
            ),
            "ACK_REQUIRED",
        ),
        (
            lambda panel, target: (
                panel.set_target_path(target),
                panel.run_dry_run(),
                panel.set_acknowledged(True),
            ),
            "CONFIRM_REQUIRED",
        ),
    ),
)
def test_write_blocks_until_target_fresh_dry_run_ack_and_confirmation(
    qapp,
    tmp_path: Path,
    configure,
    expected_code: str,
) -> None:
    target = tmp_path / "state.json"
    writer = RecordingWriter()
    panel = _panel(qapp, writer=writer)
    try:
        configure(panel, target)
        before = len(writer.calls)
        result = panel.write_persistence_record()
        assert result["status"] == "blocked"
        assert expected_code in panel.diagnostics_text()
        assert len(writer.calls) == before
        assert not target.exists()
    finally:
        panel.close()
        panel.deleteLater()


def test_successful_write_creates_only_explicit_target_and_renders_safety(
    qapp,
    tmp_path: Path,
) -> None:
    target = tmp_path / "state.json"
    writer = RecordingWriter()
    panel = _panel(qapp, writer=writer)
    try:
        panel.set_target_path(target)
        panel.run_dry_run()
        panel.set_acknowledged(True)
        panel.set_confirmed(True)
        result = panel.write_persistence_record()
        assert len(writer.calls) == 2
        assert writer.calls[-1].dry_run is False
        assert writer.calls[-1].caller_acknowledged_persistence_write is True
        assert result["status"] == "completed"
        assert target.exists()
        assert sorted(item.name for item in tmp_path.iterdir()) == ["state.json"]
        assert "written | yes" in panel.write_result_text()
        assert "local_review_record_only" in panel.write_result_text()
        safety = panel.safety_guidance_text()
        assert "not runtime reload acceptance" in safety
        assert "not validation evidence" in safety
        assert "not validation failure" in safety
        assert "not ProjectSchema mutation" in safety
        assert "not trust restoration or automatic activation" in safety
        assert "does not close issues or mutate releases" in safety
        assert "Trust label is not certification" in safety
    finally:
        panel.close()
        panel.deleteLater()


def test_existing_target_blocks_unless_allow_replace_is_explicit(
    qapp,
    tmp_path: Path,
) -> None:
    target = tmp_path / "state.json"
    target.write_text("old", encoding="utf-8")
    writer = RecordingWriter()
    panel = _panel(qapp, writer=writer)
    try:
        panel.set_target_path(target)
        blocked = panel.run_dry_run()
        assert blocked["status"] == "blocked"
        assert writer.calls[-1].allow_replace is False
        assert "TARGET_EXISTS" in panel.diagnostics_text()

        panel.set_allow_replace(True)
        planned = panel.run_dry_run()
        assert planned["status"] == "planned"
        assert writer.calls[-1].allow_replace is True
        panel.set_acknowledged(True)
        panel.set_confirmed(True)
        completed = panel.write_persistence_record()
        assert completed["status"] == "completed"
        assert writer.calls[-1].allow_replace is True
    finally:
        panel.close()
        panel.deleteLater()


def test_writer_blocked_and_error_results_render_without_downstream_claims(
    qapp,
    tmp_path: Path,
) -> None:
    for status in ("blocked", "error"):
        writer = RecordingWriter(
            result_factory=lambda request, status=status: _mapping_result(
                status=status,
                dry_run=request.dry_run,
            )
        )
        panel = _panel(qapp, writer=writer)
        try:
            panel.set_target_path(tmp_path / f"{status}.json")
            result = panel.run_dry_run()
            assert result["status"] == status
            assert f"WRITE_{status.upper()}" in panel.diagnostics_text()
            flags = panel.write_non_action_flags()
            assert flags["runtime_reload_acceptance_performed"] is False
            assert flags["project_schema_mutated"] is False
            assert flags["validation_executed"] is False
            assert flags["solver_executed"] is False
            assert flags["issue_mutated"] is False
            assert flags["release_mutated"] is False
            assert flags["certification_claimed"] is False
        finally:
            panel.close()
            panel.deleteLater()


def test_source_keeps_write_boundaries() -> None:
    source = _source()
    forbidden_text = (
        "plugin_manifest_state_writer",
        "plugin_manifest_reload_file_reader",
        "optional_solver_manifest_reload_acceptance_persistence",
        "QFileDialog",
        "glob(",
        "iterdir(",
        "rglob(",
        "mkdir(",
        "open(",
        "write_text(",
        "write_bytes(",
        "os.replace",
        "NamedTemporaryFile",
    )
    for token in forbidden_text:
        assert token not in source

    tree = ast.parse(source)
    imports: set[str] = set()
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)

    lowered_imports = {item.lower() for item in imports}
    assert "subprocess" not in lowered_imports
    assert not any("plugin_manifest_state_writer" in item for item in lowered_imports)
    assert not any("plugin_manifest_reload_file_reader" in item for item in lowered_imports)
    assert not any("project_schema" in item for item in lowered_imports)
    assert "open" not in calls
    assert "write_text" not in calls
    assert "write_bytes" not in calls
    assert calls.count("write") == 2
