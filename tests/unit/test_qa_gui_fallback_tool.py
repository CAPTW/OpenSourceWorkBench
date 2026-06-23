from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "qa" / "run_gui_per_file_fallback.py"
GUI_DIR = REPO_ROOT / "tests" / "gui"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def test_gui_fallback_tool_exists() -> None:
    assert SCRIPT.exists()


def test_list_only_returns_deterministic_gui_test_file_list() -> None:
    proc = run_tool("--list-only")
    expected = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in sorted(GUI_DIR.glob("test_*.py"), key=lambda item: item.name)
    ]

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.splitlines() == expected
    assert expected


def test_script_text_contains_no_direct_solver_commands() -> None:
    text = SCRIPT.read_text(encoding="utf-8").lower()

    for forbidden in ("ccx", "gmsh", "octave", "foam", "solveradapter"):
        assert forbidden not in text


def test_json_summary_argument_is_supported(tmp_path: Path) -> None:
    summary = tmp_path / "summary.json"
    proc = run_tool("--list-only", "--json-summary", str(summary))

    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(summary.read_text(encoding="utf-8"))
    assert data["mode"] == "list-only"
    assert data["total"] > 0
    assert data["results"] == []


def test_tool_does_not_write_without_json_summary(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--list-only"],
        cwd=tmp_path,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not any(tmp_path.iterdir())
