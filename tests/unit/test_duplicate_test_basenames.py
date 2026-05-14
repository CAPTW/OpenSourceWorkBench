from __future__ import annotations

import sys
from pathlib import Path

TOOLS_QA = Path(__file__).resolve().parents[2] / "tools" / "qa"
if str(TOOLS_QA) not in sys.path:
    sys.path.insert(0, str(TOOLS_QA))

from check_duplicate_test_basenames import (  # noqa: E402
    find_duplicate_test_basenames,
    format_duplicate_report,
)


def _write(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")


def test_duplicate_basename_fails(tmp_path: Path) -> None:
    _write(tmp_path / "unit" / "test_same.py")
    _write(tmp_path / "gui" / "test_same.py")

    duplicates = find_duplicate_test_basenames(tmp_path)

    assert "test_same.py" in duplicates
    assert len(duplicates["test_same.py"]) == 2


def test_unique_basenames_pass(tmp_path: Path) -> None:
    _write(tmp_path / "unit" / "test_unit_name.py")
    _write(tmp_path / "gui" / "test_gui_name.py")

    assert find_duplicate_test_basenames(tmp_path) == {}


def test_nested_duplicate_paths_are_reported(tmp_path: Path) -> None:
    _write(tmp_path / "unit" / "nested" / "test_same.py")
    _write(tmp_path / "gui" / "nested" / "test_same.py")

    report = format_duplicate_report(
        find_duplicate_test_basenames(tmp_path),
        root=tmp_path,
    )

    assert "test_same.py" in report
    assert "unit/nested/test_same.py" in report
    assert "gui/nested/test_same.py" in report


def test_init_py_is_ignored(tmp_path: Path) -> None:
    _write(tmp_path / "unit" / "__init__.py")
    _write(tmp_path / "gui" / "__init__.py")

    assert find_duplicate_test_basenames(tmp_path) == {}
