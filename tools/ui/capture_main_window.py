"""Capture OpenSolver Workbench main window screenshots for visual QA."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

THEMES = ("dark", "light", "system")
DEFAULT_OUT_DIR = Path("artifacts/ui")
DEFAULT_REFERENCE = Path("docs/ui/reference/osw_run_screen.png")


class CaptureError(RuntimeError):
    """Friendly capture failure that should not produce a raw traceback."""

    def __init__(self, message: str, *, return_code: int = 2) -> None:
        super().__init__(message)
        self.return_code = return_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture OpenSolver Workbench main window screenshots.",
    )
    parser.add_argument("--theme", choices=THEMES, default="dark")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--all", dest="all_themes", action="store_true")
    parser.add_argument("--width", type=int, default=2048)
    parser.add_argument("--height", type=int, default=1152)
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--offscreen", action="store_true")
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=2000)
    parser.add_argument("--compare-reference", type=Path)
    parser.add_argument("--json-report", type=Path)
    return parser


def capture_theme(
    *,
    theme: str,
    out: Path,
    width: int = 2048,
    height: int = 1152,
    scale: float = 1.0,
    offscreen: bool = False,
    show: bool = False,
    timeout_ms: int = 2000,
) -> Path:
    """Capture one theme to a PNG file."""

    if theme not in THEMES:
        expected = ", ".join(THEMES)
        raise CaptureError(f"Unknown theme {theme!r}; expected one of {expected}.", return_code=1)

    if offscreen or _looks_headless():
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    _ensure_project_paths()
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
    except ModuleNotFoundError as exc:
        raise CaptureError(
            "PySide6 is not installed. Install the GUI optional extra to capture screenshots.",
            return_code=2,
        ) from exc

    try:
        from osw.gui.main_window import MainWindow
        from osw.gui.theme import ThemeManager
    except ModuleNotFoundError as exc:
        raise CaptureError(
            f"Could not import the OSW GUI modules: {exc}",
            return_code=2,
        ) from exc

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.setApplicationName("OpenSolver Workbench")
    _load_capture_fonts(QtGui, app)
    theme_manager = ThemeManager(mode=theme, auto_load=False)
    window = MainWindow(theme_manager=theme_manager)
    theme_manager.set_mode(theme, save=False)
    theme_manager.apply_to_app(app)
    capture_width = max(1, int(width * scale))
    capture_height = max(1, int(height * scale))
    window.resize(capture_width, capture_height)
    if show:
        window.show()
    window.ensurePolished()
    _process_events(app, timeout_ms)

    pixmap = QtGui.QPixmap(window.size())
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)
    window.render(pixmap)
    if pixmap.isNull():
        raise CaptureError("Qt returned a null screenshot pixmap.", return_code=2)

    out.parent.mkdir(parents=True, exist_ok=True)
    if not pixmap.save(str(out), "PNG"):
        raise CaptureError(f"Could not save screenshot to {out}.", return_code=2)
    window.close()
    _process_events(app, 50)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    themes = list(THEMES) if args.all_themes else [args.theme]
    report: dict[str, Any] = {"captures": [], "comparisons": []}

    try:
        for theme in themes:
            output_path = _output_path_for_theme(args, theme)
            capture_theme(
                theme=theme,
                out=output_path,
                width=args.width,
                height=args.height,
                scale=args.scale,
                offscreen=args.offscreen,
                show=args.show,
                timeout_ms=args.timeout_ms,
            )
            capture_record = {
                "theme": theme,
                "path": str(output_path),
                "bytes": output_path.stat().st_size,
            }
            report["captures"].append(capture_record)
            print(f"Captured {theme}: {output_path}")

            if args.compare_reference:
                comparison = _compare_capture(args.compare_reference, output_path, theme)
                report["comparisons"].append(comparison)
                if comparison.get("status") == "pillow-unavailable":
                    print("Pillow is unavailable; comparison skipped.")
        if args.json_report:
            args.json_report.parent.mkdir(parents=True, exist_ok=True)
            args.json_report.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 0
    except CaptureError as exc:
        print(str(exc), file=sys.stderr)
        if args.json_report:
            args.json_report.parent.mkdir(parents=True, exist_ok=True)
            args.json_report.write_text(
                json.dumps({"error": str(exc), "captures": report["captures"]}, indent=2),
                encoding="utf-8",
            )
        return exc.return_code
    except RuntimeError as exc:
        print(f"Qt screenshot capture failed: {exc}", file=sys.stderr)
        return 2


def _compare_capture(reference: Path, candidate: Path, theme: str) -> dict[str, Any]:
    from tools.ui.compare_reference import compare_images

    out_json = candidate.with_name(f"{candidate.stem}_compare.json")
    out_diff = candidate.with_name(f"{candidate.stem}_diff.png")
    result = compare_images(
        reference=reference,
        candidate=candidate,
        out_json=out_json,
        out_diff=out_diff,
        resize_candidate=True,
    )
    return {
        "theme": theme,
        "status": result.status,
        "return_code": result.return_code,
        "json": str(out_json),
        "diff": str(out_diff) if out_diff.exists() else None,
        "metrics": result.metrics,
    }


def _output_path_for_theme(args: argparse.Namespace, theme: str) -> Path:
    if args.all_themes:
        return args.out_dir / f"osw_{theme}.png"
    if args.out is not None:
        return args.out
    return args.out_dir / f"osw_{theme}.png"


def _ensure_project_paths() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    src_path = repo_root / "src"
    for path in (repo_root, src_path):
        path_text = str(path)
        if path_text not in sys.path:
            sys.path.insert(0, path_text)


def _process_events(app: object, timeout_ms: int) -> None:
    deadline = time.monotonic() + max(0, timeout_ms) / 1000.0
    while time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
        if timeout_ms <= 50:
            break


def _looks_headless() -> bool:
    return bool(os.environ.get("CI") or os.environ.get("PYTEST_CURRENT_TEST"))


def _load_capture_fonts(QtGui: object, app: object) -> None:
    """Register local fonts for Qt offscreen captures with an empty font DB."""

    windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    candidates = (
        windir / "Fonts" / "segoeui.ttf",
        windir / "Fonts" / "segoeuib.ttf",
        windir / "Fonts" / "seguisym.ttf",
        windir / "Fonts" / "segmdl2.ttf",
        windir / "Fonts" / "arial.ttf",
        windir / "Fonts" / "consola.ttf",
        windir / "Fonts" / "consolab.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    )
    loaded_families: list[str] = []
    for path in candidates:
        if not path.exists():
            continue
        font_id = QtGui.QFontDatabase.addApplicationFont(str(path))
        if font_id < 0:
            continue
        loaded_families.extend(QtGui.QFontDatabase.applicationFontFamilies(font_id))

    families = set(QtGui.QFontDatabase.families()) | set(loaded_families)
    for family in ("Segoe UI", "Arial", "DejaVu Sans"):
        if family in families:
            app.setFont(QtGui.QFont(family, 9))
            break


if __name__ == "__main__":
    sys.exit(main())
