"""Focused GUI project-file context and document lifecycle tests."""

from __future__ import annotations

import importlib.util
import inspect
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


def test_project_document_context_module_exists() -> None:
    assert importlib.util.find_spec("osw.gui.project_document_context") is not None


def _context_types() -> tuple[object, object]:
    from osw.gui.project_document_context import (
        ProjectDocumentContext,
        ProjectDocumentOrigin,
    )

    return ProjectDocumentContext, ProjectDocumentOrigin


def test_startup_context_is_unbound_with_generation_zero() -> None:
    context_type, origin_type = _context_types()

    context = context_type()

    assert context.project_file_path is None
    assert context.project_root is None
    assert context.origin is origin_type.STARTUP
    assert context.generation == 0
    assert context.is_bound is False


def test_absolute_context_path_is_verbatim_and_root_is_lexical(tmp_path: Path) -> None:
    context_type, origin_type = _context_types()
    selected = str(tmp_path / "folder" / ".." / "project.osw.json")

    context = context_type(
        project_file_path=selected,
        origin=origin_type.OPENED,
        generation=3,
    )

    assert context.project_file_path == selected
    assert context.project_root == Path(selected).parent
    assert context.generation == 3
    assert context.is_bound is True


def test_relative_context_path_is_verbatim_and_has_no_root() -> None:
    context_type, origin_type = _context_types()
    selected = "legacy/../project.osw.json"

    context = context_type(
        project_file_path=selected,
        origin=origin_type.SAVED_AS,
        generation=1,
    )

    assert context.project_file_path == selected
    assert context.project_root is None
    assert context.is_bound is True


def test_context_is_frozen() -> None:
    context_type, _origin_type = _context_types()
    context = context_type()

    with pytest.raises(FrozenInstanceError):
        context.generation = 1


@pytest.mark.parametrize(
    ("path", "generation", "error"),
    [
        ("", 0, ValueError),
        (None, -1, ValueError),
        (None, True, TypeError),
    ],
)
def test_context_rejects_invalid_state(
    path: str | None,
    generation: int,
    error: type[Exception],
) -> None:
    context_type, _origin_type = _context_types()

    with pytest.raises(error):
        context_type(project_file_path=path, generation=generation)


def _project(name: str, *, screenshot_path: str | None = None) -> object:
    from osw.core.project_schema import Project, ProjectMetadata

    screenshots = ()
    if screenshot_path is not None:
        from osw.core.report_asset import ReportScreenshotAsset

        screenshots = (
            ReportScreenshotAsset(
                id="legacy-shot",
                path=screenshot_path,
                caption="Legacy relative screenshot",
            ),
        )
    return Project(
        metadata=ProjectMetadata(name=name),
        report_screenshots=screenshots,
    )


def _window(qapp: object, **kwargs: object) -> object:
    from osw.gui.main_window import MainWindow

    return MainWindow(**kwargs)


def _seed_document_state(window: object) -> dict[str, object]:
    from osw.core.result_dataset import ResultDataset
    from osw.post.scene_model import SceneScreenshotRecord
    from osw.post.table_model import TablePreview
    from osw.scripts.mscript.figure_dataset import FigureDataset

    marker = object()
    result_dataset = ResultDataset(
        dataset_id="old-result",
        source="old-result.json",
        solver="fixture",
        analysis_type="summary",
    )
    figure_dataset = FigureDataset(dataset_id="old-figures", source="old")
    result_table = TablePreview(
        columns=("name", "value"),
        rows=(("old", "1"),),
        title="Old table",
    )
    window.workflow_session.items = {"old-item": marker}
    window.workflow_session.mesh_infos = [
        {
            "source": "old-mesh",
            "format": "vtk",
            "nodes": 1,
            "elements": 1,
            "cell_types": ("vertex",),
        }
    ]
    window.workflow_session.result_tables = [result_table]
    window.workflow_session.figure_datasets = [figure_dataset]
    window.workflow_session.warnings = ["old workflow warning"]
    window.last_imported_mesh_data = marker
    window.last_imported_mesh_ref = "old-mesh"
    window.selected_mesh_context = SimpleNamespace(mesh_ref="old-mesh")
    window._mesh_data_by_ref = {"old-mesh": marker}
    window.last_figure_dataset = figure_dataset
    window.last_result_datasets = (result_dataset,)
    window._scene_screenshot_candidates = (
        SceneScreenshotRecord(id="old-shot", path="old-shot.png"),
    )
    window._scene_screenshot_counter = 7
    window._metadata_mesh_load_state = SimpleNamespace(status="succeeded")
    window._last_persisted_report_screenshot_status = "old persisted status"
    window.run_monitor.set_log_lines(["old document log"])
    window.refresh_results_from_project(update_report=False)
    window.generate_report_preview(log=False)
    return _document_state(window)


def _document_state(window: object) -> dict[str, object]:
    return {
        "project": window.current_project,
        "context": window.project_document_context(),
        "workflow_project": window.workflow_session.project,
        "workflow_items": window.workflow_session.items,
        "workflow_mesh_infos": window.workflow_session.mesh_infos,
        "workflow_result_tables": window.workflow_session.result_tables,
        "workflow_figure_datasets": window.workflow_session.figure_datasets,
        "workflow_warnings": window.workflow_session.warnings,
        "last_imported_mesh_data": window.last_imported_mesh_data,
        "last_imported_mesh_ref": window.last_imported_mesh_ref,
        "selected_mesh_context": window.selected_mesh_context,
        "mesh_data_by_ref": window._mesh_data_by_ref,
        "result_catalog": window.result_catalog,
        "last_figure_dataset": window.last_figure_dataset,
        "last_result_datasets": window.last_result_datasets,
        "screenshots": window._scene_screenshot_candidates,
        "screenshot_counter": window._scene_screenshot_counter,
        "metadata_load_state": window._metadata_mesh_load_state,
        "persisted_status": window._last_persisted_report_screenshot_status,
        "run_log": window.run_monitor.toPlainText(),
        "report_summary": window.properties_panel.report_preview_panel.last_report_summary,
    }


def _assert_exact_state(window: object, expected: dict[str, object]) -> None:
    actual = _document_state(window)
    for key, value in expected.items():
        if key in {
            "project",
            "context",
            "workflow_project",
            "workflow_items",
            "workflow_mesh_infos",
            "workflow_result_tables",
            "workflow_figure_datasets",
            "workflow_warnings",
            "last_imported_mesh_data",
            "selected_mesh_context",
            "mesh_data_by_ref",
            "result_catalog",
            "last_figure_dataset",
            "report_summary",
        }:
            assert actual[key] is value, key
        else:
            assert actual[key] == value, key


def _assert_document_state_reset(window: object) -> None:
    assert window.workflow_session.items == {}
    assert window.workflow_session.mesh_infos == []
    assert window.workflow_session.result_tables == []
    assert window.workflow_session.figure_datasets == []
    assert window.workflow_session.warnings == []
    assert window.last_imported_mesh_data is None
    assert window.last_imported_mesh_ref is None
    assert window.selected_mesh_context is None
    assert window._mesh_data_by_ref == {}
    assert window.last_figure_dataset is None
    assert window.last_result_datasets == ()
    assert window._scene_screenshot_candidates == ()
    assert window._metadata_mesh_load_state is None
    assert window._last_persisted_report_screenshot_status == ""
    assert "old document log" not in window.run_monitor.toPlainText()


def test_two_main_windows_have_isolated_startup_contexts(qapp: object) -> None:
    first = _window(qapp)
    second = _window(qapp)

    assert first.project_document_context() is not second.project_document_context()
    assert first.current_project_file_path() is None
    assert second.current_project_root() is None
    assert first.has_bound_project_file() is False
    assert second.has_bound_project_file() is False


def test_ordinary_set_project_preserves_context_and_generation(qapp: object) -> None:
    selected = "relative/project.osw.json"
    window = _window(
        qapp,
        project_save_path_picker=lambda: selected,
        project_saver=lambda _project, _path: None,
    )
    assert window.save_project_as() is True
    context = window.project_document_context()

    replacement = _project("Same document update")
    window.set_project(replacement)

    assert window.current_project is replacement
    assert window.project_document_context() is context
    assert window.project_document_context().generation == 1


def test_workflow_same_document_update_preserves_context(qapp: object) -> None:
    selected = "relative/project.osw.json"
    window = _window(
        qapp,
        project_save_path_picker=lambda: selected,
        project_saver=lambda _project, _path: None,
    )
    assert window.save_project_as() is True
    context = window.project_document_context()
    replacement = _project("Workflow update")
    window.workflow_session.project = replacement

    window._apply_workflow_operation(SimpleNamespace(items=(), logs=()))

    assert window.current_project is replacement
    assert window.project_document_context() is context


def test_successful_open_binds_exact_path_after_load_and_resets_state(
    qapp: object,
) -> None:
    selected = "C:/Project Folder/../loaded.osw.json"
    loaded = _project("Loaded")
    load_calls: list[str] = []
    save_calls: list[tuple[object, str]] = []
    window = _window(
        qapp,
        project_open_path_picker=lambda: selected,
        project_loader=lambda path: load_calls.append(path) or loaded,
        project_saver=lambda project, path: save_calls.append((project, path)),
    )
    _seed_document_state(window)
    plugin_registry = window.plugin_registry
    executable_registry = window.executable_registry

    assert window.open_project() is True

    context = window.project_document_context()
    assert load_calls == [selected]
    assert save_calls == []
    assert window.current_project is loaded
    assert window.workflow_session.project is loaded
    assert context.project_file_path == selected
    assert context.origin.value == "opened"
    assert context.generation == 1
    assert context.project_root == Path(selected).parent
    assert window.plugin_registry is plugin_registry
    assert window.executable_registry is executable_registry
    assert window._scene_screenshot_counter == 7
    _assert_document_state_reset(window)


def test_cancelled_open_is_exact_no_op(qapp: object) -> None:
    loader_calls: list[str] = []
    window = _window(
        qapp,
        project_open_path_picker=lambda: None,
        project_loader=lambda path: loader_calls.append(path) or _project("Unexpected"),
    )
    expected = _seed_document_state(window)

    assert window.open_project() is False

    assert loader_calls == []
    _assert_exact_state(window, expected)


def test_failed_open_is_exact_no_op_and_does_not_disclose_selected_path(
    qapp: object,
) -> None:
    selected = "C:/Users/private/secret-project.osw.json"
    errors: list[str] = []

    def fail_load(_path: str) -> object:
        raise OSError(f"could not read {selected}")

    window = _window(
        qapp,
        project_open_path_picker=lambda: selected,
        project_loader=fail_load,
        project_error_reporter=errors.append,
    )
    expected = _seed_document_state(window)

    assert window.open_project() is False

    _assert_exact_state(window, expected)
    assert len(errors) == 1
    assert selected not in errors[0]


def test_open_validation_failure_is_exact_no_op(qapp: object) -> None:
    invalid = _project("")
    assert invalid.validate().has_errors
    errors: list[str] = []
    window = _window(
        qapp,
        project_open_path_picker=lambda: "invalid.osw.json",
        project_loader=lambda _path: invalid,
        project_error_reporter=errors.append,
    )
    expected = _seed_document_state(window)

    assert window.open_project() is False

    _assert_exact_state(window, expected)
    assert len(errors) == 1


def test_open_gui_refresh_failure_rolls_back_exact_state(
    qapp: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors: list[str] = []
    loaded = _project("Loaded")
    window = _window(
        qapp,
        project_open_path_picker=lambda: "loaded.osw.json",
        project_loader=lambda _path: loaded,
        project_error_reporter=errors.append,
    )
    expected = _seed_document_state(window)
    real_preview = window.generate_report_preview
    calls = 0

    def fail_once(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("forced refresh failure")
        return real_preview(*args, **kwargs)

    monkeypatch.setattr(window, "generate_report_preview", fail_once)

    assert window.open_project() is False

    _assert_exact_state(window, expected)
    assert len(errors) == 1


def test_open_restore_is_resilient_when_one_surface_keeps_failing(
    qapp: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors: list[str] = []
    window = _window(
        qapp,
        project_open_path_picker=lambda: "loaded.osw.json",
        project_loader=lambda _path: _project("Loaded"),
        project_error_reporter=errors.append,
    )
    expected = _seed_document_state(window)

    def fail_surface(_project: object) -> None:
        raise RuntimeError("forced persistent surface failure")

    monkeypatch.setattr(window.properties_panel, "set_project", fail_surface)

    assert window.open_project() is False

    _assert_exact_state(window, expected)
    assert len(errors) == 1


def test_successful_open_discards_document_viewers(qapp: object) -> None:
    loaded = _project("Loaded")
    window = _window(
        qapp,
        project_open_path_picker=lambda: "loaded.osw.json",
        project_loader=lambda _path: loaded,
        project_error_reporter=lambda _message: None,
    )
    window.open_result_viewer()
    window.open_plot_viewer()
    window.open_mesh_viewer()

    assert window.open_project() is True

    assert window.result_viewer_dialog is None
    assert window.result_viewer is None
    assert window.plot_viewer_dialog is None
    assert window.plot_viewer is None
    assert window.mesh_viewer_dialog is None
    assert window.mesh_viewer is None


def test_successful_open_retires_every_document_bound_surface(qapp: object) -> None:
    class Surface:
        def __init__(self) -> None:
            self.closed = 0
            self.deleted = 0

        def close(self) -> None:
            self.closed += 1

        def deleteLater(self) -> None:
            self.deleted += 1

    window = _window(
        qapp,
        project_open_path_picker=lambda: "loaded.osw.json",
        project_loader=lambda _path: _project("Loaded"),
    )
    document_dialog_names = (
        "script_preview_dialog",
        "mat_preview_dialog",
        "boundary_curve_dialog",
        "gmsh_mesh_dialog",
        "calculix_deck_dialog",
        "openfoam_template_dialog",
        "chm_property_dialog",
        "chm_reactor_dialog",
        "result_viewer_dialog",
        "plot_viewer_dialog",
        "mesh_viewer_dialog",
    )
    surfaces = {name: Surface() for name in document_dialog_names}
    for name, surface in surfaces.items():
        setattr(window, name, surface)
    window.result_viewer = object()
    window.plot_viewer = object()
    window.mesh_viewer = object()
    plugin_manager = object()
    preferences = object()
    window.plugin_manager_dialog = plugin_manager
    window.preferences_dialog = preferences

    assert window.open_project() is True

    for name, surface in surfaces.items():
        assert getattr(window, name) is None, name
        assert surface.closed == 1, name
        assert surface.deleted == 1, name
    assert window.result_viewer is None
    assert window.plot_viewer is None
    assert window.mesh_viewer is None
    assert window.plugin_manager_dialog is plugin_manager
    assert window.preferences_dialog is preferences


def test_document_generation_callback_ignores_stale_dialog_signal(qapp: object) -> None:
    calls: list[str] = []
    window = _window(qapp)
    guarded = window._guard_document_callback(calls.append)

    guarded("same document")
    assert window.new_project() is True
    guarded("stale document")

    assert calls == ["same document"]


def test_document_callback_remains_live_across_same_document_save_as(
    qapp: object,
) -> None:
    calls: list[str] = []
    window = _window(
        qapp,
        project_save_path_picker=lambda: "renamed.osw.json",
        project_saver=lambda _project, _path: None,
    )
    guarded = window._guard_document_callback(calls.append)

    assert window.save_project_as() is True
    guarded("same document after Save As")

    assert window.project_document_context().generation == 1
    assert calls == ["same document after Save As"]


def test_open_success_log_failure_rolls_back_before_surface_retirement(
    qapp: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors: list[str] = []
    window = _window(
        qapp,
        project_open_path_picker=lambda: "loaded.osw.json",
        project_loader=lambda _path: _project("Loaded"),
        project_error_reporter=errors.append,
    )
    expected = _seed_document_state(window)
    viewer_dialog = SimpleNamespace(close=lambda: None, deleteLater=lambda: None)
    viewer = object()
    window.result_viewer_dialog = viewer_dialog
    window.result_viewer = viewer

    def fail_log(_message: str) -> None:
        raise RuntimeError("forced success-log failure")

    monkeypatch.setattr(window, "_placeholder_action", fail_log)

    assert window.open_project() is False

    _assert_exact_state(window, expected)
    assert window.result_viewer_dialog is viewer_dialog
    assert window.result_viewer is viewer
    assert len(errors) == 1


def test_document_surface_close_failure_cannot_leave_a_partial_transition(
    qapp: object,
) -> None:
    class FailingSurface:
        def close(self) -> None:
            raise RuntimeError("forced close failure")

        def deleteLater(self) -> None:
            raise RuntimeError("forced delete failure")

    loaded = _project("Loaded")
    window = _window(
        qapp,
        project_open_path_picker=lambda: "loaded.osw.json",
        project_loader=lambda _path: loaded,
        project_error_reporter=lambda _message: None,
    )
    window.result_viewer_dialog = FailingSurface()
    window.result_viewer = object()

    assert window.open_project() is True

    assert window.current_project is loaded
    assert window.current_project_file_path() == "loaded.osw.json"
    assert window.result_viewer_dialog is None
    assert window.result_viewer is None


def test_successful_new_clears_binding_resets_state_and_does_not_save(
    qapp: object,
) -> None:
    selected = "C:/projects/original.osw.json"
    saves: list[tuple[object, str]] = []
    window = _window(
        qapp,
        project_save_path_picker=lambda: selected,
        project_saver=lambda project, path: saves.append((project, path)),
    )
    assert window.save_project_as() is True
    saves.clear()
    _seed_document_state(window)
    plugin_registry = window.plugin_registry
    executable_registry = window.executable_registry

    assert window.new_project() is True

    context = window.project_document_context()
    assert window.current_project.metadata.name == "HeatSink_Flow"
    assert context.project_file_path is None
    assert context.project_root is None
    assert context.origin.value == "new"
    assert context.generation == 2
    assert saves == []
    assert window.plugin_registry is plugin_registry
    assert window.executable_registry is executable_registry
    assert window._scene_screenshot_counter == 7
    _assert_document_state_reset(window)


def test_new_project_construction_failure_is_exact_no_op(
    qapp: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import osw.gui.main_window as main_window_module

    errors: list[str] = []
    window = _window(qapp, project_error_reporter=errors.append)
    expected = _seed_document_state(window)

    def fail_construction() -> object:
        raise RuntimeError("forced construction failure")

    monkeypatch.setattr(
        main_window_module,
        "create_heatsink_flow_demo_project",
        fail_construction,
    )

    assert window.new_project() is False

    _assert_exact_state(window, expected)
    assert len(errors) == 1


def test_bound_save_uses_exact_path_and_preserves_project_and_context(
    qapp: object,
) -> None:
    selected = "C:/Project Folder/../bound.osw.json"
    saves: list[tuple[object, str]] = []
    window = _window(
        qapp,
        project_save_path_picker=lambda: selected,
        project_saver=lambda project, path: saves.append((project, path)),
    )
    assert window.save_project_as() is True
    saves.clear()
    project = window.current_project
    context = window.project_document_context()

    assert window.save_project() is True

    assert saves == [(project, selected)]
    assert window.current_project is project
    assert window.project_document_context() is context


def test_bound_save_failure_preserves_project_and_context(qapp: object) -> None:
    selected = "bound.osw.json"
    fail = False
    errors: list[str] = []

    def saver(_project: object, _path: str) -> None:
        if fail:
            raise OSError("save failed")

    window = _window(
        qapp,
        project_save_path_picker=lambda: selected,
        project_saver=saver,
        project_error_reporter=errors.append,
    )
    assert window.save_project_as() is True
    project = window.current_project
    context = window.project_document_context()
    fail = True

    assert window.save_project() is False

    assert window.current_project is project
    assert window.project_document_context() is context
    assert len(errors) == 1


def test_unbound_save_delegates_to_save_as(qapp: object) -> None:
    selected = "relative/new-project.osw.json"
    saves: list[tuple[object, str]] = []
    window = _window(
        qapp,
        project_save_path_picker=lambda: selected,
        project_saver=lambda project, path: saves.append((project, path)),
    )

    assert window.save_project() is True

    assert saves == [(window.current_project, selected)]
    assert window.current_project_file_path() == selected
    assert window.current_project_root() is None
    assert window.project_document_context().generation == 1


def test_save_as_binds_only_after_saver_success_and_keeps_project_identity(
    qapp: object,
) -> None:
    selected = "C:/Project Folder/new.osw.json"
    context_seen_by_saver: list[object] = []
    project_seen_by_saver: list[object] = []
    window: Any

    def saver(project: object, _path: str) -> None:
        project_seen_by_saver.append(project)
        context_seen_by_saver.append(window.project_document_context())

    window = _window(
        qapp,
        project_save_path_picker=lambda: selected,
        project_saver=saver,
    )
    project = window.current_project
    prior_context = window.project_document_context()

    assert window.save_project_as() is True

    assert project_seen_by_saver == [project]
    assert context_seen_by_saver == [prior_context]
    assert window.current_project is project
    assert window.current_project_file_path() == selected
    assert window.project_document_context().origin.value == "saved_as"
    assert window.project_document_context().generation == 1


def test_cancelled_save_as_is_exact_no_op(qapp: object) -> None:
    saves: list[tuple[object, str]] = []
    window = _window(
        qapp,
        project_save_path_picker=lambda: None,
        project_saver=lambda project, path: saves.append((project, path)),
    )
    project = window.current_project
    context = window.project_document_context()

    assert window.save_project_as() is False

    assert saves == []
    assert window.current_project is project
    assert window.project_document_context() is context


def test_failed_save_as_is_exact_no_op_and_does_not_disclose_path(
    qapp: object,
) -> None:
    selected = "C:/Users/private/secret-project.osw.json"
    errors: list[str] = []

    def fail_save(_project: object, _path: str) -> None:
        raise OSError(f"could not write {selected}")

    window = _window(
        qapp,
        project_save_path_picker=lambda: selected,
        project_saver=fail_save,
        project_error_reporter=errors.append,
    )
    project = window.current_project
    context = window.project_document_context()

    assert window.save_project_as() is False

    assert window.current_project is project
    assert window.project_document_context() is context
    assert len(errors) == 1
    assert selected not in errors[0]


def _recording_window(qapp: object) -> object:
    from osw.gui.main_window import MainWindow

    class RecordingMainWindow(MainWindow):
        def __init__(self) -> None:
            self.lifecycle_calls: list[str] = []
            super().__init__()

        def new_project(self, _checked: bool = False) -> bool:
            self.lifecycle_calls.append("new")
            return True

        def open_project(self, _checked: bool = False) -> bool:
            self.lifecycle_calls.append("open")
            return True

        def save_project(self, _checked: bool = False) -> bool:
            self.lifecycle_calls.append("save")
            return True

        def save_project_as(self, _checked: bool = False) -> bool:
            self.lifecycle_calls.append("save_as")
            return True

    return RecordingMainWindow()


def test_file_menu_actions_invoke_each_lifecycle_once(qapp: object) -> None:
    window = _recording_window(qapp)

    for label in ("New Project", "Open Project", "Save Project", "Save Project As"):
        window.menu_actions[label].trigger()

    assert window.lifecycle_calls == ["new", "open", "save", "save_as"]


def test_toolbar_action_objects_invoke_each_lifecycle_once(qapp: object) -> None:
    window = _recording_window(qapp)

    for label in ("New", "Open", "Save", "Save As"):
        window.toolbar_actions[label].trigger()

    assert window.lifecycle_calls == ["new", "open", "save", "save_as"]


def test_visible_top_bar_buttons_invoke_each_lifecycle_once(qapp: object) -> None:
    window = _recording_window(qapp)

    for label in ("New", "Open", "Save", "Save As"):
        window.top_region.trigger_action(label)

    assert window.lifecycle_calls == ["new", "open", "save", "save_as"]


def test_context_does_not_change_project_serialization_or_schema(qapp: object) -> None:
    project = _project("Serialization")
    before = project.to_dict()
    window = _window(
        qapp,
        project=project,
        project_save_path_picker=lambda: "serialization.osw.json",
        project_saver=lambda _project, _path: None,
    )

    assert window.save_project_as() is True

    assert window.current_project is project
    assert window.current_project.to_dict() == before
    assert window.current_project.schema_version == "0.1"
    assert "project_file_path" not in window.current_project.to_dict()
    assert "document_context" not in window.current_project.to_dict()


def test_core_project_io_signatures_are_unchanged() -> None:
    from osw.core import project_io

    assert tuple(inspect.signature(project_io.load_project).parameters) == ("path",)
    assert tuple(inspect.signature(project_io.save_project).parameters) == (
        "project",
        "path",
    )


def test_legacy_relative_screenshot_path_is_not_reinterpreted_or_duplicated(
    qapp: object,
) -> None:
    relative_path = "legacy/../screenshots/scene.png"
    project = _project("Legacy", screenshot_path=relative_path)
    before = project.to_dict()
    window = _window(
        qapp,
        project=project,
        project_save_path_picker=lambda: "C:/projects/legacy.osw.json",
        project_saver=lambda _project, _path: None,
    )

    assert window.save_project_as() is True
    summary = window.build_current_report_summary()

    assert window.current_project.to_dict() == before
    assert window.current_project.report_screenshots[0].path == relative_path
    assert tuple(summary.figures) == ()
    assert [section.title for section in summary.sections].count("3D Scene Screenshots") == 1


def test_context_path_does_not_leak_into_preview_or_export(
    qapp: object,
    tmp_path: Path,
) -> None:
    selected = "C:/Users/private/context-only-project.osw.json"
    window = _window(
        qapp,
        project_save_path_picker=lambda: selected,
        project_saver=lambda _project, _path: None,
    )
    assert window.save_project_as() is True

    summary = window.build_current_report_summary()
    output = window.export_current_report(output_path=tmp_path / "report.html")

    assert selected not in repr(summary)
    assert selected not in output.read_text(encoding="utf-8")


def test_main_window_close_does_not_save_or_change_context(qapp: object) -> None:
    selected = "bound.osw.json"
    saves: list[tuple[object, str]] = []
    window = _window(
        qapp,
        project_save_path_picker=lambda: selected,
        project_saver=lambda project, path: saves.append((project, path)),
    )
    assert window.save_project_as() is True
    saves.clear()
    context = window.project_document_context()

    window.close()

    assert saves == []
    assert window.project_document_context() is context
