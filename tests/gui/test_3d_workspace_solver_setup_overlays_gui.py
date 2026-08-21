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
from osw.core.units import Quantity
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
    setup = PhysicsSetup(fixed_support_records=[api.FixedSupportRecord("fix-a", "Clamp", "nodes")])
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
    assert [
        panel.record_kind_combo.itemText(index) for index in range(panel.record_kind_combo.count())
    ] == [
        "Material Region",
        "Fixed Support",
        "Prescribed Displacement",
        "Force",
        "Pressure",
        "Temperature",
        "Heat Flux",
    ]
    assert set(panel.visibility_checks) == {
        "material",
        "fixed_support",
        "prescribed_displacement",
        "force",
        "pressure",
        "temperature",
        "heat_flux",
    }
    assert "face identity" in panel.deferred_scope_label.text().lower()
    assert "solver execution" in panel.deferred_scope_label.text().lower()
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

    panel.record_kind_combo.setCurrentText("Material Region")
    assert panel.material_combo.isEnabled()
    assert not panel.magnitude_spin.isEnabled()
    panel.record_kind_combo.setCurrentText("Force")
    assert not panel.material_combo.isEnabled()
    assert panel.magnitude_spin.isEnabled()

    panel.record_kind_combo.setCurrentText("Prescribed Displacement")
    panel.displacement_enabled_checks[0].setChecked(True)
    panel.displacement_spins[0].setValue(0.0)
    payload = panel._form_payload()
    assert payload["ux"] == 0.0
    assert payload["uy"] is None
    assert payload["displacement_unit"] == "m"

    panel.record_kind_combo.setCurrentText("Pressure")
    panel.scalar_spin.setValue(-12.5)
    payload = panel._form_payload()
    assert payload["value"] == -12.5
    assert payload["unit"] == "Pa"
    assert panel.scalar_spin.accessibleName() == "Pressure value"


def test_panel_selection_populates_form_and_preserves_record_kind(app) -> None:
    api, panel_api = _panel_api()
    panel = panel_api.SetupOverlayPanel()
    selections = (
        NamedSelection("cells", "Cells", entity_kind=EntityKind.CELL),
        NamedSelection("nodes", "Nodes", entity_kind=EntityKind.NODE),
    )
    setup = PhysicsSetup(
        fixed_support_records=[api.FixedSupportRecord("fix-a", "Clamp", "nodes", (1, 2))]
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
        lambda kind, record_id, payload: edited.append((kind, record_id, payload))
    )
    panel.name_edit.setText("Updated clamp")
    panel.edit_button.click()

    assert edited[0][0:2] == ("fixed_support", "fix-a")
    assert edited[0][2]["kind"] == "Fixed Support"
    assert edited[0][2]["translational_dofs"] == (1, 2)

    panel.new_button.click()
    assert panel.current_record_id() == ""
    assert panel.record_kind_combo.isEnabled()
    panel.name_edit.setText("clamp")
    assert panel.create_button.isEnabled() is False
    assert "unique" in panel.kind_controls_diagnostic.text().lower()
    panel.name_edit.setText("Second support")
    assert panel.create_button.isEnabled() is True


def test_panel_keeps_blocked_records_visible_with_reason(app) -> None:
    api, panel_api = _panel_api()
    panel = panel_api.SetupOverlayPanel()
    setup = PhysicsSetup(
        fixed_support_records=[api.FixedSupportRecord("fix-a", "Clamp", "missing")]
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


def test_panel_disables_surface_load_apply_for_volume_cell_selection(app) -> None:
    api, panel_api = _panel_api()
    panel = panel_api.SetupOverlayPanel()
    selections = (
        NamedSelection("surface", "Surface", entity_kind=EntityKind.CELL),
        NamedSelection("volume", "Volume", entity_kind=EntityKind.CELL),
    )
    panel.set_context(
        setup=PhysicsSetup(),
        selections=selections,
        materials=(),
        statuses={},
        resolved_selection_ids=("surface", "volume"),
        surface_selection_ids=("surface",),
    )
    panel.record_kind_combo.setCurrentText("Pressure")
    panel.name_edit.setText("Pressure")
    panel.target_combo.setCurrentIndex(panel.target_combo.findData("volume"))

    assert panel.create_button.isEnabled() is False
    assert "triangle, quad, or polygon" in panel.kind_controls_diagnostic.text()

    panel.target_combo.setCurrentIndex(panel.target_combo.findData("surface"))
    assert panel.create_button.isEnabled() is True

    stale_record = api.PressureLoadRecord(
        "stale-pressure",
        "Stale pressure",
        "surface",
        Quantity(1.0, "Pa"),
    )
    stale_status = api.SetupRecordStatus(
        stale_record.id,
        api.SetupRecordKind.PRESSURE,
        api.SetupReadiness.BLOCKED,
        "MESH_FINGERPRINT_MISMATCH",
        "The exact mesh fingerprint differs.",
        api.SetupValidity.STALE_SELECTION,
        False,
    )
    panel.set_context(
        setup=PhysicsSetup(pressure_load_records=[stale_record]),
        selections=selections,
        materials=(),
        statuses={stale_record.id: stale_status},
        resolved_selection_ids=(),
        surface_selection_ids=(),
    )
    panel.record_list.setCurrentRow(0)
    assert panel.edit_button.isEnabled() is True

    volume_status = api.SetupRecordStatus(
        stale_record.id,
        api.SetupRecordKind.PRESSURE,
        api.SetupReadiness.BLOCKED,
        "REQUIRES_EXPLICIT_SURFACE_SELECTION",
        "A tetra volume cell is not an explicit surface.",
        api.SetupValidity.INCOMPATIBLE,
        False,
    )
    panel.set_context(
        setup=PhysicsSetup(pressure_load_records=[stale_record]),
        selections=selections,
        materials=(),
        statuses={stale_record.id: volume_status},
        resolved_selection_ids=("surface",),
        surface_selection_ids=(),
    )
    panel.record_list.setCurrentRow(0)
    assert panel.edit_button.isEnabled() is False


def test_panel_populates_extended_typed_record_and_enable_state(app) -> None:
    api, panel_api = _panel_api()
    panel = panel_api.SetupOverlayPanel()
    selections = (NamedSelection("surface", "Surface", entity_kind=EntityKind.CELL),)
    setup = PhysicsSetup(
        heat_flux_records=[
            api.HeatFluxRecord(
                "flux-a",
                "Cooling flux",
                "surface",
                Quantity(-25.0, "W/m^2"),
                enabled=False,
            )
        ]
    )
    status = api.SetupRecordStatus(
        "flux-a",
        api.SetupRecordKind.HEAT_FLUX,
        api.SetupReadiness.DISABLED,
        "DISABLED",
        "Record is disabled.",
        api.SetupValidity.DISABLED,
        False,
    )
    panel.set_context(
        setup=setup,
        selections=selections,
        materials=(),
        statuses={"flux-a": status},
    )
    panel.record_list.setCurrentRow(0)

    assert panel.record_kind_combo.currentText() == "Heat Flux"
    assert panel.scalar_spin.value() == -25.0
    assert panel.scalar_unit_label.text() == "W/m^2"
    assert panel.enabled_checkbox.isChecked() is False
    assert panel.validity_label.text() == "DISABLED"
    assert "adapter" in panel.adapter_readiness_label.accessibleName().lower()


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
            ("prescribed_displacement", True),
            ("force", False),
            ("pressure", True),
            ("temperature", True),
            ("heat_flux", True),
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
            "kind": "Contact",
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


def test_main_window_creates_extended_setup_and_syncs_tree_scene_properties(
    app,
) -> None:
    from osw.core.selection import EntityLocator, SelectionTargetRef
    from osw.core.selection_resolution import NODE_ORDINAL_NAMESPACE
    from osw.gui.main_window import MainWindow

    selection = NamedSelection(
        "nodes",
        "Tip nodes",
        entity_kind=EntityKind.NODE,
        targets=(
            SelectionTargetRef(
                EntityKind.NODE,
                (0,),
                "mesh-1",
                locator=EntityLocator(
                    "osw.mesh_identity.v1",
                    "mesh-1",
                    "different-mesh",
                    EntityKind.NODE,
                    NODE_ORDINAL_NAMESPACE,
                    (0,),
                ),
            ),
        ),
    )
    window = MainWindow(
        project=Project(
            metadata=ProjectMetadata(name="Extended setup"),
            selections=[selection],
        ),
        scene_renderer_factory=FailingFactory(),
    )
    try:
        window._on_create_setup_record(
            {
                "kind": "Prescribed Displacement",
                "name": "Move tip",
                "target_selection_id": "nodes",
                "ux": 0.0,
                "uy": None,
                "uz": None,
                "displacement_unit": "m",
                "enabled": True,
            }
        )
        record = window.current_project.primary_physics.prescribed_displacement_records[0]
        assert record.ux.value == 0.0
        assert window.project_dirty is True

        item = window.project_tree_panel.setup_item(record.id)
        window.project_tree.setCurrentItem(item)

        assert window.active_scene_controller.active_setup_id == record.id
        assert window.project_tree_panel.current_setup_id() == record.id
        assert window.properties_panel.row_value("Setup ID") == record.id
        assert window.properties_panel.row_value("Kind") == "prescribed_displacement"
        assert window.properties_panel.row_value("UX") == "0 m"
        assert "mesh" in window.properties_panel.row_value("Status reason").lower()

        window.setup_overlay_panel.new_button.click()
        assert window.active_scene_controller.active_setup_id == ""
        window.project_tree.setCurrentItem(item)
        assert window.active_scene_controller.active_setup_id == record.id

        named_item = window.project_tree_panel.named_selection_item("nodes")
        window.project_tree.setCurrentItem(named_item)
        assert window.active_scene_controller.active_setup_id == ""
        assert window.project_tree_panel.current_named_selection_id() == "nodes"
    finally:
        window.close()
