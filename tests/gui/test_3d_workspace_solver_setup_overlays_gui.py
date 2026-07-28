from __future__ import annotations

import os
from importlib import import_module

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")
from PySide6 import QtWidgets

from osw.core.materials import Material
from osw.core.project_schema import PhysicsSetup, Project, ProjectMetadata
from osw.core.selection import EntityKind, NamedSelection
from osw.gui.workspace_scene_controller import SceneRendererInitializationError


@pytest.fixture(scope="module")
def app() -> QtWidgets.QApplication:
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _panel_api() -> tuple[object, object]:
    try:
        return (
            import_module("osw.core.solver_setup"),
            import_module("osw.gui.widgets.setup_overlay_panel"),
        )
    except ModuleNotFoundError:
        pytest.fail("solver setup panel is missing", pytrace=False)


def test_panel_exposes_bounded_crud_visibility_filter_and_prepare_preview(app) -> None:
    api, panel_api = _panel_api()
    panel = panel_api.SetupOverlayPanel()
    selections = (
        NamedSelection("cells", "Cells", entity_kind=EntityKind.CELL),
        NamedSelection("nodes", "Nodes", entity_kind=EntityKind.NODE),
    )
    setup = PhysicsSetup(
        fixed_support_records=[
            api.FixedSupportRecord("fix-a", "Clamp", "nodes")
        ]
    )
    status = api.SetupRecordStatus(
        "fix-a",
        api.SetupRecordKind.FIXED_SUPPORT,
        api.SetupReadiness.READY,
        "READY",
        "Ready.",
    )

    panel.set_context(
        setup=setup,
        selections=selections,
        materials=(Material("steel", "Steel"),),
        statuses={"fix-a": status},
    )
    panel.set_selection_filter("nodes")

    assert panel.record_list.count() == 1
    assert panel.target_combo.count() == 2
    assert "pressure" in panel.deferred_scope_label.text().lower()
    assert "thermal" in panel.deferred_scope_label.text().lower()
    assert panel.findChildren(QtWidgets.QPushButton, "run") == []
    assert panel.prepare_preview_button.text() == "Prepare CalculiX Preview"

    created: list[dict[str, object]] = []
    panel.createRequested.connect(created.append)
    panel.record_kind_combo.setCurrentText("Force")
    panel.name_edit.setText("Tip load")
    panel.target_combo.setCurrentIndex(1)
    panel.create_button.click()
    assert created[0]["application_mode"] == "PER_NODE"
    assert created[0]["coordinate_system"] == "GLOBAL"
    assert panel.coordinate_system_label.text() == "GLOBAL"
    assert panel.application_mode_label.text() == "PER_NODE"

    panel.record_kind_combo.setCurrentText("Material")
    assert panel.material_combo.isEnabled()
    assert not panel.magnitude_spin.isEnabled()
    panel.record_kind_combo.setCurrentText("Force")
    assert not panel.material_combo.isEnabled()
    assert panel.magnitude_spin.isEnabled()


def test_panel_selection_populates_form_and_preserves_record_kind(app) -> None:
    api, panel_api = _panel_api()
    panel = panel_api.SetupOverlayPanel()
    selections = (
        NamedSelection("cells", "Cells", entity_kind=EntityKind.CELL),
        NamedSelection("nodes", "Nodes", entity_kind=EntityKind.NODE),
    )
    setup = PhysicsSetup(
        fixed_support_records=[
            api.FixedSupportRecord("fix-a", "Clamp", "nodes", (1, 2))
        ]
    )
    status = api.SetupRecordStatus(
        "fix-a",
        api.SetupRecordKind.FIXED_SUPPORT,
        api.SetupReadiness.READY,
        "READY",
        "Ready.",
    )
    panel.set_context(
        setup=setup,
        selections=selections,
        materials=(Material("steel", "Steel"),),
        statuses={"fix-a": status},
    )
    panel.record_list.setCurrentRow(0)

    assert panel.record_kind_combo.currentText() == "Fixed Support"
    assert not panel.record_kind_combo.isEnabled()
    assert panel.name_edit.text() == "Clamp"
    assert panel.target_combo.currentData() == "nodes"
    assert not panel.material_combo.isEnabled()
    assert not panel.magnitude_spin.isEnabled()

    edited: list[tuple[str, str, dict[str, object]]] = []
    panel.editRequested.connect(
        lambda kind, record_id, payload: edited.append(
            (kind, record_id, payload)
        )
    )
    panel.name_edit.setText("Updated clamp")
    panel.edit_button.click()

    assert edited[0][0:2] == ("fixed_support", "fix-a")
    assert edited[0][2]["kind"] == "Fixed Support"
    assert edited[0][2]["translational_dofs"] == (1, 2)


def test_panel_keeps_blocked_records_visible_with_reason(app) -> None:
    api, panel_api = _panel_api()
    panel = panel_api.SetupOverlayPanel()
    setup = PhysicsSetup(
        fixed_support_records=[
            api.FixedSupportRecord("fix-a", "Clamp", "missing")
        ]
    )
    blocked = api.SetupRecordStatus(
        "fix-a",
        api.SetupRecordKind.FIXED_SUPPORT,
        api.SetupReadiness.BLOCKED,
        "MISSING_SELECTION",
        "Target selection is missing.",
    )
    panel.set_context(
        setup=setup,
        selections=(),
        materials=(),
        statuses={"fix-a": blocked},
    )

    assert panel.record_list.count() == 1
    assert "MISSING_SELECTION" in panel.record_list.item(0).text()
    assert "missing" in panel.record_list.item(0).toolTip().lower()


class FailingFactory:
    backend_kind = "pyvistaqt"
    capabilities = frozenset()

    def set_host_parent(self, _parent: object) -> None:
        return None

    def create_session(self) -> object:
        raise SceneRendererInitializationError("renderer unavailable")


class VisibilitySpy:
    def __init__(self) -> None:
        self.calls: list[tuple[str, bool]] = []

    def set_setup_category_visible(self, category: str, visible: bool) -> bool:
        self.calls.append((category, visible))
        return True

    def close(self) -> None:
        return None


def test_main_window_routes_visibility_to_current_controller(app) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow(
        project=Project(metadata=ProjectMetadata(name="Visibility")),
        scene_renderer_factory=FailingFactory(),
    )
    old_controller = window.active_scene_controller
    spy = VisibilitySpy()
    window.active_scene_controller = spy

    try:
        window.setup_overlay_panel.visibility_checks["force"].setChecked(False)
        assert spy.calls == [("force", False)]

        spy.calls.clear()
        window._apply_setup_visibility_to_current_controller()
        assert spy.calls == [
            ("material", True),
            ("fixed_support", True),
            ("force", False),
        ]
    finally:
        window.active_scene_controller = old_controller
        window.close()


def test_main_window_rejects_unknown_kind_and_tracks_explicit_save(
    app,
) -> None:
    from osw.gui.main_window import MainWindow

    save_calls: list[tuple[object, str]] = []
    window = MainWindow(
        project=Project(metadata=ProjectMetadata(name="Dirty")),
        scene_renderer_factory=FailingFactory(),
        project_save_path_picker=lambda: "saved.osw.json",
        project_saver=lambda project, path: save_calls.append((project, path)),
    )
    initial = window.current_project

    window._on_create_setup_record(
        {
            "kind": "Pressure",
            "name": "Unsupported",
            "target_selection_id": "",
        }
    )
    assert window.current_project is initial
    assert window.project_dirty is False
    assert "unsupported" in window.setup_overlay_panel.preview_text.toPlainText().lower()

    window._on_create_setup_record(
        {
            "kind": "Fixed Support",
            "name": "Clamp",
            "target_selection_id": "",
            "translational_dofs": (1, 2, 3),
        }
    )
    assert window.project_dirty is True
    assert save_calls == []
    assert window.last_imported_mesh_data is None

    assert window.save_project_as() is True
    assert window.project_dirty is False
    assert len(save_calls) == 1
    assert window.last_imported_mesh_data is None
    window.close()
