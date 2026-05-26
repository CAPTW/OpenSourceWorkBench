"""Visual QA tool smoke tests for UI-009."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None
PILLOW_AVAILABLE = importlib.util.find_spec("PIL") is not None


def test_visual_tool_modules_import_without_optional_gui_or_pillow() -> None:
    from tools.ui import capture_main_window, compare_reference

    assert callable(capture_main_window.build_parser)
    assert callable(capture_main_window.main)
    assert callable(compare_reference.build_parser)
    assert callable(compare_reference.main)


def test_capture_parser_exposes_required_arguments() -> None:
    from tools.ui.capture_main_window import build_parser

    parser = build_parser()
    options = {action.dest for action in parser._actions}

    assert {
        "theme",
        "out",
        "out_dir",
        "all_themes",
        "width",
        "height",
        "scale",
        "offscreen",
        "show",
        "timeout_ms",
        "compare_reference",
        "json_report",
    }.issubset(options)


def test_compare_parser_exposes_required_arguments() -> None:
    from tools.ui.compare_reference import build_parser

    parser = build_parser()
    options = {action.dest for action in parser._actions}

    assert {
        "reference",
        "candidate",
        "out_json",
        "out_diff",
        "resize_candidate",
        "threshold",
        "quiet",
    }.issubset(options)


def test_capture_tool_reports_missing_pyside6_cleanly_when_unavailable(tmp_path: Path) -> None:
    if PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 is installed; missing-dependency path is not active.")

    from tools.ui.capture_main_window import main

    out_path = tmp_path / "osw_dark.png"
    result = main(["--theme", "dark", "--out", str(out_path), "--offscreen"])

    assert result == 2
    assert not out_path.exists()


def test_compare_tool_reports_missing_pillow_cleanly_when_unavailable(tmp_path: Path) -> None:
    if PILLOW_AVAILABLE:
        pytest.skip("Pillow is installed; missing-dependency path is not active.")

    from tools.ui.compare_reference import compare_images

    reference = tmp_path / "reference.png"
    candidate = tmp_path / "candidate.png"
    reference.write_bytes(b"not-a-real-png")
    candidate.write_bytes(b"not-a-real-png")

    result = compare_images(reference=reference, candidate=candidate)

    assert result.status == "pillow-unavailable"
    assert result.return_code == 2


def test_compare_tool_generates_metrics_when_pillow_is_available(tmp_path: Path) -> None:
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow optional dependency is not installed.")

    from PIL import Image
    from tools.ui.compare_reference import compare_images

    reference = tmp_path / "reference.png"
    candidate = tmp_path / "candidate.png"
    out_json = tmp_path / "compare.json"
    out_diff = tmp_path / "diff.png"
    Image.new("RGB", (3, 3), (10, 20, 30)).save(reference)
    Image.new("RGB", (3, 3), (13, 24, 31)).save(candidate)

    result = compare_images(
        reference=reference,
        candidate=candidate,
        out_json=out_json,
        out_diff=out_diff,
    )

    assert result.return_code == 0
    assert out_json.exists()
    assert out_diff.exists()
    assert "mean_absolute_error" in result.metrics
    assert "normalized_mean_absolute_error" in result.metrics


def test_capture_dark_and_light_when_pyside6_is_available(tmp_path: Path) -> None:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")

    from tools.ui.capture_main_window import capture_theme

    dark = tmp_path / "dark.png"
    light = tmp_path / "light.png"
    capture_theme(theme="dark", out=dark, width=800, height=450, offscreen=True)
    capture_theme(theme="light", out=light, width=800, height=450, offscreen=True)

    assert dark.exists()
    assert dark.stat().st_size > 0
    assert light.exists()
    assert light.stat().st_size > 0


def test_main_window_still_instantiates_when_pyside6_is_available() -> None:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")

    from PySide6 import QtWidgets

    from osw.gui.main_window import MainWindow

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    window = MainWindow()

    assert window.objectName() == "oswMainWindow"
    assert app is not None
