"""Persisted 3D report screenshot management tests (GUI-only, no render).

The suite uses Project-owned ``ReportScreenshotAsset`` fixtures, temporary
local files, and injected prompt/picker/confirmation seams. It never renders a
PyVista/VTK scene, runs a solver/parser/mesh tool, or saves a Project file.
"""

from __future__ import annotations

import builtins
import importlib.util
import os
from dataclasses import replace
from pathlib import Path

import pytest

from osw.core.demo_project import create_heatsink_flow_demo_project
from osw.core.project_schema import (
    CURRENT_SCHEMA_VERSION,
    DEFAULT_PROJECT_SCHEMA_VERSION,
    Project,
    ProjectMetadata,
)
from osw.core.report_asset import ReportAssetPathKind, ReportScreenshotAsset
from osw.post.scene_model import SceneScreenshotRecord

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None
pytestmark = pytest.mark.skipif(
    not PYSIDE6_AVAILABLE,
    reason="PySide6 optional GUI extra is not installed.",
)

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class NoRenderSceneAdapter:
    def load_mesh(self, mesh: object, scene_input: object, scene_state: object) -> None:
        return None

    def set_view_state(self, scene_state: object) -> None:
        return None


def _asset(
    record_id: str,
    path: str,
    caption: str,
    *,
    marker: str,
    path_kind: ReportAssetPathKind | None = None,
) -> ReportScreenshotAsset:
    return ReportScreenshotAsset(
        id=record_id,
        path=path,
        caption=caption,
        mesh_ref=f"mesh-{marker}",
        result_dataset_ref=f"result-{marker}",
        field_id=f"field-{marker}",
        selection_ids=(f"selection-{marker}",),
        scene_state={"marker": marker, "camera": {"view_preset": "iso"}},
        glyph_options={"marker": marker, "enabled": True},
        diagnostics=(f"diagnostic-{marker}",),
        metadata={"marker": marker, "created_by": "test"},
        path_kind=path_kind,
    )


def _project_with_assets(assets: list[ReportScreenshotAsset]) -> Project:
    from osw.gui.main_window import _project_replacing_report_screenshots

    base = create_heatsink_flow_demo_project()
    if any(asset.path_kind is not None for asset in assets):
        payload = base.to_dict()
        payload["schema_version"] = "0.2"
        base = Project.from_dict(payload)
    return _project_replacing_report_screenshots(base, assets)


def _window(app: object, assets: list[ReportScreenshotAsset]) -> object:
    from osw.gui.main_window import MainWindow

    assert app is not None
    return MainWindow(
        project=_project_with_assets(assets),
        mesh_scene_adapter_factory=NoRenderSceneAdapter,
    )


def _target(
    asset: ReportScreenshotAsset,
    *,
    index: int = 0,
    expected_id: str | None = None,
    expected_asset: ReportScreenshotAsset | None = None,
) -> object:
    from osw.gui.widgets.persisted_report_screenshot_manager import (
        PersistedReportScreenshotTarget,
    )

    return PersistedReportScreenshotTarget(
        index=index,
        expected_id=asset.id if expected_id is None else expected_id,
        expected_asset=asset if expected_asset is None else expected_asset,
    )


def _scene_section(summary: object) -> object | None:
    for section in getattr(summary, "sections", ()):
        if getattr(section, "section_id", "") == "scene-screenshots":
            return section
    return None


def _spy_set_project(window: object, monkeypatch: pytest.MonkeyPatch) -> list[Project]:
    calls: list[Project] = []
    original = window.set_project

    def _record(project: Project, *, sync_workflow: bool = True) -> None:
        calls.append(project)
        original(project, sync_workflow=sync_workflow)

    monkeypatch.setattr(window, "set_project", _record)
    return calls


def _controlled_tree_snapshot(
    root: Path,
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, bytes]]:
    """Snapshot only a test-controlled tree, including paths, dirs, and bytes."""
    entries = tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob("*")))
    directories = tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_dir()
        )
    )
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    return entries, directories, files


def test_panel_and_manager_keep_persisted_and_staged_rows_separate(
    app: object, tmp_path: Path
) -> None:
    persisted_path = tmp_path / "persisted.png"
    persisted_path.write_bytes(b"persisted")
    asset = _asset("persisted-1", str(persisted_path), "Persisted", marker="p")
    window = _window(app, [asset])
    window.open_mesh_viewer()
    panel = window.mesh_viewer
    window._scene_screenshot_candidates = (
        SceneScreenshotRecord(id="staged-1", path=str(tmp_path / "staged.png")),
    )
    panel.refresh_scene_screenshot_status()

    assert panel.screenshot_status_label.text() == "Report screenshots staged: 1"
    assert panel.staged_screenshots_list.count() == 1
    assert "staged-1" in panel.staged_screenshots_list.item(0).text()
    assert panel.persisted_screenshots_status_label.text() == (
        "Persisted report screenshots: 1"
    )
    assert panel.manage_persisted_screenshots_button.isEnabled()
    caveat = panel.screenshot_caveat_label.text()
    assert "local report artifacts only" in caveat
    assert "not validation evidence" in caveat
    assert "release assets" in caveat

    panel.manage_persisted_screenshots_button.click()
    manager = window.persisted_report_screenshot_manager
    assert manager is not None
    assert manager.isModal()
    assert manager.records_table.rowCount() == 1
    assert manager.records_table.item(0, 1).text() == "persisted-1"
    assert "staged-1" not in manager.records_table.item(0, 1).text()


def test_empty_manager_and_no_selection_are_friendly(app: object) -> None:
    window = _window(app, [])
    window.open_mesh_viewer()
    panel = window.mesh_viewer

    assert panel.persisted_screenshots_status_label.text() == (
        "Persisted report screenshots: 0"
    )
    assert not panel.manage_persisted_screenshots_button.isEnabled()

    manager = window.open_persisted_report_screenshot_manager()
    assert manager.records_table.rowCount() == 0
    assert not manager.edit_button.isEnabled()
    assert not manager.remove_button.isEnabled()
    assert not manager.relink_button.isEnabled()
    manager._dispatch_edit()
    assert manager.status_label.text() == "Select a persisted scene screenshot first."


def test_target_tokens_capture_index_id_and_complete_snapshot(
    app: object, tmp_path: Path
) -> None:
    first = _asset("duplicate", str(tmp_path / "a.png"), "A", marker="a")
    second = _asset("duplicate", str(tmp_path / "b.png"), "B", marker="b")
    manager = _window(app, [first, second]).open_persisted_report_screenshot_manager()

    targets = manager.targets()
    assert [target.index for target in targets] == [0, 1]
    assert [target.expected_id for target in targets] == ["duplicate", "duplicate"]
    assert targets[0].expected_asset == first
    assert targets[1].expected_asset == second
    assert targets[0].expected_asset is not first
    assert targets[0].expected_asset.scene_state is not first.scene_state
    assert targets[0].expected_asset.scene_state["camera"] is not first.scene_state["camera"]


def test_manager_states_report_paths_duplicates_and_shadowing(tmp_path: Path) -> None:
    from osw.gui.widgets.persisted_report_screenshot_manager import (
        persisted_report_screenshot_states,
    )

    available = tmp_path / "available.png"
    available.write_bytes(b"available")
    assets = (
        _asset("dup", str(available), "First", marker="1"),
        _asset("dup", str(tmp_path / "missing.png"), "Second", marker="2"),
        _asset("no-path", "", "No path", marker="3"),
    )

    states = persisted_report_screenshot_states(assets)
    assert states[0] == "available; duplicate id; first persisted record wins"
    assert states[1] == (
        "missing; duplicate id; shadowed by earlier persisted record"
    )
    assert states[2] == "no path"

    shadowed = persisted_report_screenshot_states(assets, ("dup",))
    assert shadowed[0] == "available; shadowed by transient; duplicate id"
    assert shadowed[1] == "missing; shadowed by transient; duplicate id"


@pytest.mark.parametrize(
    ("path_kind", "stored_path", "expected_state"),
    [
        (
            ReportAssetPathKind.LEGACY_RAW,
            "legacy/../private.png",
            "legacy_raw — explicit legacy/raw reference; availability not checked",
        ),
        (
            ReportAssetPathKind.EXTERNAL_ABSOLUTE,
            r"\\server\share\private.png",
            "external_absolute; Unresolved — path resolver unavailable.",
        ),
        (
            ReportAssetPathKind.PROJECT_RELATIVE,
            "screenshots/private.png",
            "project_relative; Unresolved — path resolver unavailable.",
        ),
    ],
)
def test_manager_states_do_not_probe_explicitly_classified_paths(
    monkeypatch: pytest.MonkeyPatch,
    path_kind: ReportAssetPathKind,
    stored_path: str,
    expected_state: str,
) -> None:
    from osw.gui.widgets.persisted_report_screenshot_manager import (
        persisted_report_screenshot_states,
    )

    def _unexpected_probe(*_args: object, **_kwargs: object) -> object:
        pytest.fail(
            "explicitly classified manager rows must not probe the filesystem"
        )

    for method_name in ("is_file", "exists", "stat", "resolve"):
        monkeypatch.setattr(Path, method_name, _unexpected_probe)
    monkeypatch.setattr(os.path, "realpath", _unexpected_probe)
    monkeypatch.setattr(builtins, "open", _unexpected_probe)
    asset = _asset(
        "classified",
        stored_path,
        "Classified",
        marker="classified",
        path_kind=path_kind,
    )

    state = persisted_report_screenshot_states((asset,))[0]

    assert state == expected_state
    assert stored_path not in state


@pytest.mark.parametrize("stale_kind", ["index", "id", "snapshot"])
def test_caption_edit_rejects_each_stale_target_shape(
    app: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stale_kind: str,
) -> None:
    asset = _asset("shot-1", str(tmp_path / "old.png"), "Old", marker="a")
    window = _window(app, [asset])
    before = window.current_project
    if stale_kind == "index":
        target = _target(asset, index=7)
    elif stale_kind == "id":
        target = _target(asset, expected_id="different")
    else:
        target = _target(asset, expected_asset=replace(asset, caption="stale"))

    monkeypatch.setattr(
        window,
        "set_project",
        lambda *_args, **_kwargs: pytest.fail("stale target called set_project"),
    )
    assert window.update_persisted_report_screenshot_caption(target, "New") is False
    assert window.current_project is before


def test_remove_and_relink_reject_stale_targets_before_user_interaction(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    asset = _asset("shot-1", str(tmp_path / "old.png"), "Old", marker="a")
    window = _window(app, [asset])
    stale = _target(asset, index=3)
    new_path = tmp_path / "new.png"
    new_path.write_bytes(b"new")
    monkeypatch.setattr(
        window,
        "_confirm_remove_persisted_report_screenshot",
        lambda _asset: pytest.fail("stale remove requested confirmation"),
    )
    monkeypatch.setattr(
        window,
        "_confirm_relink_persisted_report_screenshot",
        lambda _asset, _path: pytest.fail("stale relink requested confirmation"),
    )
    monkeypatch.setattr(
        window,
        "set_project",
        lambda *_args, **_kwargs: pytest.fail("stale target called set_project"),
    )

    assert window.remove_persisted_report_screenshot(stale) is False
    assert window.relink_persisted_report_screenshot(stale, str(new_path)) is False


def test_complete_snapshot_detects_nested_provenance_mutation(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    asset = _asset("shot-1", str(tmp_path / "old.png"), "Old", marker="a")
    window = _window(app, [asset])
    manager = window.open_persisted_report_screenshot_manager()
    target = manager.targets()[0]
    window.current_project.report_screenshots[0].scene_state["camera"][
        "view_preset"
    ] = "xy"
    monkeypatch.setattr(
        window,
        "set_project",
        lambda *_args, **_kwargs: pytest.fail("nested stale target called set_project"),
    )

    assert window.update_persisted_report_screenshot_caption(target, "New") is False
    assert target.expected_asset.scene_state["camera"]["view_preset"] == "iso"


def test_caption_edit_changes_one_row_preserves_project_and_refreshes_report(
    app: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_path = tmp_path / "first.png"
    second_path = tmp_path / "second.png"
    first_path.write_bytes(b"first")
    second_path.write_bytes(b"second")
    first = _asset("first", str(first_path), "First caption", marker="1")
    second = _asset("second", str(second_path), "Second caption", marker="2")
    window = _window(app, [first, second])
    before_payload = window.current_project.to_dict()
    calls = _spy_set_project(window, monkeypatch)

    assert window.update_persisted_report_screenshot_caption(
        _target(second, index=1), "Edited caption"
    )

    after = window.current_project.report_screenshots
    assert len(calls) == 1
    assert after[0] == first
    assert replace(after[1], caption=second.caption) == second
    expected_payload = before_payload
    expected_payload["report_screenshots"][1]["caption"] = "Edited caption"
    assert window.current_project.to_dict() == expected_payload

    preview = window.build_current_report_summary()
    section = _scene_section(preview)
    assert section is not None
    assert any("Edited caption" in block for block in section.content_blocks)
    output = window.export_current_report(output_path=tmp_path / "caption-report.html")
    assert "Edited caption" in output.read_text(encoding="utf-8")
    assert not any(
        getattr(figure, "metadata", {}).get("kind") == "scene_screenshot"
        for figure in preview.figures
    )


def test_empty_caption_is_valid_and_prompt_cancel_is_atomic(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    asset = _asset("shot-1", str(tmp_path / "old.png"), "Old", marker="a")
    window = _window(app, [asset])

    assert window.update_persisted_report_screenshot_caption(_target(asset), "")
    assert window.current_project.report_screenshots[0].caption == ""

    current = window.current_project.report_screenshots[0]
    before = window.current_project
    calls = _spy_set_project(window, monkeypatch)
    monkeypatch.setattr(
        window, "_prompt_persisted_report_screenshot_caption", lambda _current: None
    )
    assert window.update_persisted_report_screenshot_caption(_target(current)) is False
    assert window.current_project is before
    assert calls == []


def test_caption_revalidates_after_prompt_before_mutation(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    asset = _asset("shot-1", str(tmp_path / "old.png"), "Old", marker="a")
    window = _window(app, [asset])

    def _replace_during_prompt(_current: str) -> str:
        window.current_project = _project_with_assets(
            [replace(asset, caption="External replacement")]
        )
        return "User caption"

    monkeypatch.setattr(
        window, "_prompt_persisted_report_screenshot_caption", _replace_during_prompt
    )
    assert window.update_persisted_report_screenshot_caption(_target(asset)) is False
    assert window.current_project.report_screenshots[0].caption == "External replacement"


def test_modal_dispatches_caption_request_to_main_window(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    asset = _asset("shot-1", str(tmp_path / "old.png"), "Old", marker="a")
    window = _window(app, [asset])
    manager = window.open_persisted_report_screenshot_manager()
    monkeypatch.setattr(
        window,
        "_prompt_persisted_report_screenshot_caption",
        lambda current: f"{current} via modal",
    )
    manager.records_table.selectRow(0)
    manager.edit_button.click()

    assert window.current_project.report_screenshots[0].caption == "Old via modal"
    assert manager.status_label.text() == "Updated persisted scene screenshot caption."


def test_remove_changes_metadata_only_and_never_deletes_file(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_path = tmp_path / "first.png"
    second_path = tmp_path / "second.png"
    first_path.write_bytes(b"first-bytes")
    second_path.write_bytes(b"second-bytes")
    first = _asset("first", str(first_path), "Remove me", marker="1")
    second = _asset("second", str(second_path), "Keep me", marker="2")
    window = _window(app, [first, second])
    before_payload = window.current_project.to_dict()
    before_tree = _controlled_tree_snapshot(tmp_path)
    saves: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        window,
        "_project_saver",
        lambda *args: saves.append(args),
    )
    monkeypatch.setattr(
        window, "_confirm_remove_persisted_report_screenshot", lambda _asset: True
    )
    monkeypatch.setattr(
        Path,
        "unlink",
        lambda *_args, **_kwargs: pytest.fail("remove called Path.unlink"),
    )
    calls = _spy_set_project(window, monkeypatch)

    assert window.remove_persisted_report_screenshot(_target(first))
    assert len(calls) == 1
    assert window.current_project.report_screenshots == [second]
    assert first_path.is_file()
    assert first_path.read_bytes() == b"first-bytes"
    assert second_path.read_bytes() == b"second-bytes"
    assert _controlled_tree_snapshot(tmp_path) == before_tree
    assert saves == []
    expected_payload = before_payload
    expected_payload["report_screenshots"] = [second.to_dict()]
    assert window.current_project.to_dict() == expected_payload

    preview = window.build_current_report_summary()
    section = _scene_section(preview)
    assert section is not None
    assert not any("Remove me" in block for block in section.content_blocks)
    output = window.export_current_report(output_path=tmp_path / "remove-report.html")
    html = output.read_text(encoding="utf-8")
    assert "Remove me" not in html
    assert "Keep me" in html


def test_remove_cancel_and_post_confirmation_staleness_are_atomic(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    asset = _asset("shot-1", str(tmp_path / "old.png"), "Old", marker="a")
    window = _window(app, [asset])
    before = window.current_project
    calls = _spy_set_project(window, monkeypatch)
    monkeypatch.setattr(
        window, "_confirm_remove_persisted_report_screenshot", lambda _asset: False
    )
    assert window.remove_persisted_report_screenshot(_target(asset)) is False
    assert window.current_project is before
    assert calls == []

    replacement = replace(asset, caption="External")

    def _replace_during_confirmation(_asset: object) -> bool:
        window.current_project = _project_with_assets([replacement])
        return True

    monkeypatch.setattr(
        window,
        "_confirm_remove_persisted_report_screenshot",
        _replace_during_confirmation,
    )
    assert window.remove_persisted_report_screenshot(_target(asset)) is False
    assert window.current_project.report_screenshots == [replacement]
    assert calls == []


def test_relink_changes_one_path_verbatim_and_preserves_files_and_fields(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old_path = tmp_path / "old.png"
    new_path = tmp_path / "new.PNG"
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    old_path.write_bytes(b"old-bytes")
    new_path.write_bytes(b"new-bytes")
    selected = str(subdir / ".." / "new.PNG")
    first = _asset("first", str(old_path), "Relink me", marker="1")
    second = _asset("second", str(tmp_path / "second.png"), "Keep", marker="2")
    window = _window(app, [first, second])
    before_payload = window.current_project.to_dict()
    before_tree = _controlled_tree_snapshot(tmp_path)
    saves: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        window,
        "_project_saver",
        lambda *args: saves.append(args),
    )
    monkeypatch.setattr(
        window,
        "_confirm_relink_persisted_report_screenshot",
        lambda _asset, _path: True,
    )
    calls = _spy_set_project(window, monkeypatch)

    assert window.relink_persisted_report_screenshot(_target(first), selected)
    after = window.current_project.report_screenshots
    assert len(calls) == 1
    assert after[0].path == selected
    assert after[0].path_kind is None
    assert replace(after[0], path=first.path) == first
    assert after[1] == second
    assert old_path.read_bytes() == b"old-bytes"
    assert new_path.read_bytes() == b"new-bytes"
    assert _controlled_tree_snapshot(tmp_path) == before_tree
    assert saves == []
    expected_payload = before_payload
    expected_payload["report_screenshots"][0]["path"] = selected
    assert window.current_project.to_dict() == expected_payload

    preview = window.build_current_report_summary()
    section = _scene_section(preview)
    assert section is not None
    assert any("new.PNG" in block for block in section.content_blocks)
    output = window.export_current_report(output_path=tmp_path / "relink-report.html")
    html = output.read_text(encoding="utf-8")
    assert "new.PNG" in html
    assert "old.png" not in html


@pytest.mark.parametrize(
    ("current_kind", "expected_kind"),
    [
        (ReportAssetPathKind.LEGACY_RAW, ReportAssetPathKind.LEGACY_RAW),
        (
            ReportAssetPathKind.EXTERNAL_ABSOLUTE,
            ReportAssetPathKind.EXTERNAL_ABSOLUTE,
        ),
        (
            ReportAssetPathKind.PROJECT_RELATIVE,
            ReportAssetPathKind.EXTERNAL_ABSOLUTE,
        ),
    ],
)
def test_relink_updates_explicit_path_and_kind_atomically(
    app: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    current_kind: ReportAssetPathKind,
    expected_kind: ReportAssetPathKind,
) -> None:
    new_path = tmp_path / "new.png"
    new_path.write_bytes(b"new")
    old_path = (
        "screenshots/old.png"
        if current_kind is ReportAssetPathKind.PROJECT_RELATIVE
        else str(tmp_path / "old.png")
    )
    asset = _asset(
        "shot-1",
        old_path,
        "Old",
        marker="classified",
        path_kind=current_kind,
    )
    window = _window(app, [asset])
    calls = _spy_set_project(window, monkeypatch)
    monkeypatch.setattr(
        window,
        "_confirm_relink_persisted_report_screenshot",
        lambda _asset, _path: True,
    )

    assert window.relink_persisted_report_screenshot(
        _target(asset), str(new_path)
    )

    assert len(calls) == 1
    replacement = window.current_project.report_screenshots[0]
    assert replacement.path == str(new_path)
    assert replacement.path_kind is expected_kind
    assert replacement.caption == asset.caption
    assert replacement.metadata == asset.metadata
    assert window.current_project.schema_version == "0.2"


@pytest.mark.parametrize(
    ("current_kind", "expected_kind", "expected_sentence", "changes_kind"),
    [
        (None, None, "Path reference kind remains unmarked.", False),
        (
            ReportAssetPathKind.LEGACY_RAW,
            ReportAssetPathKind.LEGACY_RAW,
            "Path reference kind remains legacy_raw.",
            False,
        ),
        (
            ReportAssetPathKind.EXTERNAL_ABSOLUTE,
            ReportAssetPathKind.EXTERNAL_ABSOLUTE,
            "Path reference kind remains external_absolute.",
            False,
        ),
        (
            ReportAssetPathKind.PROJECT_RELATIVE,
            ReportAssetPathKind.EXTERNAL_ABSOLUTE,
            (
                "Path reference kind will change from project_relative to "
                "external_absolute."
            ),
            True,
        ),
    ],
)
def test_relink_confirmation_discloses_exact_path_kind_outcome(
    app: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    current_kind: ReportAssetPathKind | None,
    expected_kind: ReportAssetPathKind | None,
    expected_sentence: str,
    changes_kind: bool,
) -> None:
    assert QtWidgets is not None
    old_path = (
        "screenshots/old.png"
        if current_kind is ReportAssetPathKind.PROJECT_RELATIVE
        else str(tmp_path / "old.png")
    )
    new_path = tmp_path / "new.png"
    new_path.write_bytes(b"new")
    asset = _asset(
        "shot-confirm",
        old_path,
        "Confirm relink",
        marker="confirm",
        path_kind=current_kind,
    )
    window = _window(app, [asset])
    calls = _spy_set_project(window, monkeypatch)
    questions: list[tuple[str, str]] = []

    def _capture_question(
        _parent: object,
        title: str,
        message: str,
        *_args: object,
    ) -> object:
        questions.append((title, message))
        return QtWidgets.QMessageBox.StandardButton.Yes

    monkeypatch.setattr(QtWidgets.QMessageBox, "question", _capture_question)

    assert window.relink_persisted_report_screenshot(
        _target(asset), str(new_path)
    )

    assert len(questions) == 1
    title, message = questions[0]
    assert title == "Relink persisted scene screenshot"
    assert expected_sentence in message
    assert "may change" not in message
    assert "No file will be copied or moved." in message
    assert "Saving the Project remains a separate explicit action." in message
    if changes_kind:
        assert (
            "The selected file will be stored as an external absolute reference."
            in message
        )
    else:
        assert "will change from" not in message
    assert len(calls) == 1
    replacement = window.current_project.report_screenshots[0]
    assert replacement.path == str(new_path)
    assert replacement.path_kind is expected_kind
    assert replace(
        replacement,
        path=asset.path,
        path_kind=current_kind,
    ) == asset


def test_modal_relink_uses_main_window_picker_and_confirmation(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old_path = tmp_path / "old.png"
    new_path = tmp_path / "new.webp"
    old_path.write_bytes(b"old")
    new_path.write_bytes(b"new")
    asset = _asset("shot-1", str(old_path), "Old", marker="a")
    window = _window(app, [asset])
    manager = window.open_persisted_report_screenshot_manager()
    monkeypatch.setattr(
        window,
        "_pick_persisted_report_screenshot_relink_path",
        lambda: str(new_path),
    )
    monkeypatch.setattr(
        window,
        "_confirm_relink_persisted_report_screenshot",
        lambda _asset, _path: True,
    )
    manager.records_table.selectRow(0)
    manager.relink_button.click()

    assert window.current_project.report_screenshots[0].path == str(new_path)
    assert manager.status_label.text() == "Relinked persisted scene screenshot."


def test_relink_cancel_invalid_and_same_path_cases_never_replace_project(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old_path = tmp_path / "old.png"
    old_path.write_bytes(b"old")
    asset = _asset("shot-1", str(old_path), "Old", marker="a")
    window = _window(app, [asset])
    calls = _spy_set_project(window, monkeypatch)
    target = _target(asset)

    monkeypatch.setattr(
        window, "_pick_persisted_report_screenshot_relink_path", lambda: None
    )
    assert window.relink_persisted_report_screenshot(target) is False
    assert "cancelled" in window._last_persisted_report_screenshot_status.lower()

    missing = tmp_path / "missing.png"
    assert window.relink_persisted_report_screenshot(target, str(missing)) is False
    assert "Select an existing PNG" in window._last_persisted_report_screenshot_status

    assert window.relink_persisted_report_screenshot(target, str(tmp_path)) is False
    unsupported = tmp_path / "image.tif"
    unsupported.write_bytes(b"tif")
    assert window.relink_persisted_report_screenshot(target, str(unsupported)) is False
    assert window.relink_persisted_report_screenshot(target, str(old_path)) is False
    assert "already linked" in window._last_persisted_report_screenshot_status

    valid = tmp_path / "valid.gif"
    valid.write_bytes(b"gif")
    monkeypatch.setattr(
        window,
        "_confirm_relink_persisted_report_screenshot",
        lambda _asset, _path: False,
    )
    assert window.relink_persisted_report_screenshot(target, str(valid)) is False
    assert calls == []
    assert window.current_project.report_screenshots == [asset]


def test_relink_revalidates_after_confirmation(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old_path = tmp_path / "old.png"
    new_path = tmp_path / "new.png"
    old_path.write_bytes(b"old")
    new_path.write_bytes(b"new")
    asset = _asset("shot-1", str(old_path), "Old", marker="a")
    replacement = replace(asset, caption="External")
    window = _window(app, [asset])

    def _replace_during_confirmation(_asset: object, _path: str) -> bool:
        window.current_project = _project_with_assets([replacement])
        return True

    monkeypatch.setattr(
        window,
        "_confirm_relink_persisted_report_screenshot",
        _replace_during_confirmation,
    )
    assert window.relink_persisted_report_screenshot(
        _target(asset), str(new_path)
    ) is False
    assert window.current_project.report_screenshots == [replacement]
    assert old_path.read_bytes() == b"old"
    assert new_path.read_bytes() == b"new"


def test_relink_revalidates_file_after_confirmation_before_project_replacement(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old_path = tmp_path / "old.png"
    new_path = tmp_path / "new.png"
    old_path.write_bytes(b"old")
    new_path.write_bytes(b"new")
    asset = _asset("shot-1", str(old_path), "Old", marker="a")
    window = _window(app, [asset])
    before = window.current_project
    calls = _spy_set_project(window, monkeypatch)
    original_is_file = Path.is_file
    selected_path_checks: list[str] = []

    def _selected_path_is_file(candidate: Path) -> bool:
        if candidate == new_path:
            selected_path_checks.append(str(candidate))
            return len(selected_path_checks) == 1
        return original_is_file(candidate)

    monkeypatch.setattr(Path, "is_file", _selected_path_is_file)
    monkeypatch.setattr(
        window,
        "_confirm_relink_persisted_report_screenshot",
        lambda _asset, _path: True,
    )

    assert window.relink_persisted_report_screenshot(
        _target(asset), str(new_path)
    ) is False
    assert selected_path_checks == [str(new_path), str(new_path)]
    assert calls == []
    assert window.current_project is before
    assert window.current_project.report_screenshots == [asset]
    assert window._last_persisted_report_screenshot_status == (
        "Select an existing PNG, JPG, JPEG, WEBP, or GIF file."
    )
    assert old_path.read_bytes() == b"old"
    assert new_path.read_bytes() == b"new"


def test_duplicate_rows_remain_independently_manageable_and_first_still_wins(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = _asset("dup", str(tmp_path / "first.png"), "First", marker="1")
    second = _asset("dup", str(tmp_path / "second.png"), "Second", marker="2")
    window = _window(app, [first, second])

    assert [record.caption for record in window._report_scene_screenshots()] == ["First"]
    manager = window.open_persisted_report_screenshot_manager()
    assert "first persisted record wins" in manager.records_table.item(0, 4).text()
    assert "shadowed by earlier persisted record" in (
        manager.records_table.item(1, 4).text()
    )

    assert window.update_persisted_report_screenshot_caption(
        _target(second, index=1), "Edited second"
    )
    assert window.current_project.report_screenshots[1].caption == "Edited second"
    assert [record.caption for record in window._report_scene_screenshots()] == ["First"]

    current_second = window.current_project.report_screenshots[1]
    monkeypatch.setattr(
        window, "_confirm_remove_persisted_report_screenshot", lambda _asset: True
    )
    assert window.remove_persisted_report_screenshot(
        _target(current_second, index=1)
    )
    assert window.current_project.report_screenshots == [first]


def test_identical_duplicate_snapshots_are_disambiguated_by_index(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    asset = _asset("dup", str(tmp_path / "same.png"), "Same", marker="x")
    window = _window(app, [asset, asset])
    monkeypatch.setattr(
        window, "_confirm_remove_persisted_report_screenshot", lambda _asset: True
    )

    assert window.remove_persisted_report_screenshot(_target(asset, index=1))
    assert window.current_project.report_screenshots == [asset]


def test_transient_conflict_is_diagnosed_and_remains_report_winner(
    app: object, tmp_path: Path
) -> None:
    persisted = _asset(
        "shared", str(tmp_path / "persisted.png"), "Persisted", marker="p"
    )
    window = _window(app, [persisted])
    window._scene_screenshot_candidates = (
        SceneScreenshotRecord(
            id="shared", path=str(tmp_path / "transient.png"), caption="Transient"
        ),
    )
    manager = window.open_persisted_report_screenshot_manager()

    assert "shadowed by transient" in manager.records_table.item(0, 4).text()
    assert [record.caption for record in window._report_scene_screenshots()] == [
        "Transient"
    ]
    assert window.update_persisted_report_screenshot_caption(
        _target(persisted), "Persisted edited"
    )
    assert [record.caption for record in window._report_scene_screenshots()] == [
        "Transient"
    ]
    preview = window.build_current_report_summary()
    assert not any(
        getattr(figure, "metadata", {}).get("kind") == "scene_screenshot"
        for figure in preview.figures
    )


def test_manager_and_panel_refresh_after_project_replacement(
    app: object, tmp_path: Path
) -> None:
    first = _asset("first", str(tmp_path / "first.png"), "First", marker="1")
    second = _asset("second", str(tmp_path / "second.png"), "Second", marker="2")
    window = _window(app, [first])
    window.open_mesh_viewer()
    manager = window.open_persisted_report_screenshot_manager()

    window.set_project(_project_with_assets([first, second]))

    assert window.mesh_viewer.persisted_screenshots_status_label.text() == (
        "Persisted report screenshots: 2"
    )
    assert manager.records_table.rowCount() == 2


def test_management_never_auto_saves_and_preserves_schema_compatibility(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import osw.core.project_io as project_io

    asset = _asset("shot-1", str(tmp_path / "old.png"), "Old", marker="a")
    window = _window(app, [asset])
    saves: list[object] = []
    monkeypatch.setattr(
        project_io, "save_project", lambda project, path: saves.append((project, path))
    )

    assert window.update_persisted_report_screenshot_caption(_target(asset), "Changed")
    assert saves == []
    assert window.current_project.schema_version == "0.1"
    assert DEFAULT_PROJECT_SCHEMA_VERSION == "0.1"
    assert CURRENT_SCHEMA_VERSION == "0.2"

    legacy_payload = Project(metadata=ProjectMetadata(name="Legacy")).to_dict()
    legacy_payload.pop("report_screenshots", None)
    restored = Project.from_dict(legacy_payload)
    assert restored.report_screenshots == []
    assert restored.schema_version == "0.1"


def test_changed_gui_sources_contain_no_file_mutation_or_save_contract() -> None:
    from osw.gui.widgets import persisted_report_screenshot_manager as manager_module

    manager_source = Path(manager_module.__file__).read_text(encoding="utf-8")
    for forbidden in (
        ".unlink(",
        "os.remove",
        "shutil",
        "copy2",
        "copyfile",
        ".rename(",
        ".resolve(",
        ".relative_to(",
        "normpath",
        "save_project",
        "subprocess",
        "import pyvista",
        "import vtk",
    ):
        assert forbidden not in manager_source
