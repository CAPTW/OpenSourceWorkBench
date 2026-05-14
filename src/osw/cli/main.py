"""Minimal command line interface for OSW bootstrap checks."""

from __future__ import annotations

import argparse
import importlib.util
import platform
import sys
from collections.abc import Sequence
from pathlib import Path

from osw import __version__
from osw.plugins.health import (
    collect_plugin_health_records,
    plugin_health_records_as_json,
    plugin_health_records_as_text,
)

OPTIONAL_MODULES = {
    "PySide6": "gui",
    "meshio": "mesh",
    "gmsh": "mesh",
    "pyvista": "viz",
    "matplotlib": "viz",
    "cantera": "chm",
    "CoolProp": "chm",
    "scipy": "mscript",
    "hdf5storage": "mscript",
}

DEFAULT_PLUGIN_INSTALL_ROOT = Path.home() / ".osw" / "plugins"


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def doctor_lines() -> list[str]:
    lines = [
        "OSW doctor",
        f"version: {__version__}",
        f"python: {platform.python_version()}",
        f"platform: {platform.platform()}",
        "external solver execution: disabled",
        "optional modules:",
    ]
    for module_name, extra_name in OPTIONAL_MODULES.items():
        state = "available" if _module_available(module_name) else "missing"
        lines.append(f"  - {module_name} ({extra_name}): {state}")
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osw", description="OpenSolver Workbench CLI")
    parser.add_argument("--version", action="version", version=f"osw {__version__}")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="Report local bootstrap environment status.")
    plugin_health_parser = subparsers.add_parser(
        "plugin-health",
        help="Report local plugin manifest, dependency, and executable status.",
        description=(
            "Report local plugin health from manifest files only. "
            "This command does not execute plugins, solvers, or network checks."
        ),
    )
    plugin_health_parser.add_argument(
        "--plugin-path",
        action="append",
        default=[],
        help="Additional local plugin directory to scan. May be repeated.",
    )
    plugin_health_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON health records.",
    )
    subparsers.add_parser(
        "gui",
        help="Launch the optional PySide6 GUI shell.",
        description="Launch the optional PySide6 GUI shell.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        print("\n".join(doctor_lines()))
        return 0

    if args.command == "plugin-health":
        plugin_paths = [DEFAULT_PLUGIN_INSTALL_ROOT, *(Path(path) for path in args.plugin_path)]
        records = collect_plugin_health_records(plugin_paths)
        if args.json:
            print(plugin_health_records_as_json(records))
        else:
            print(plugin_health_records_as_text(records))
        return 0

    if args.command == "gui":
        from osw.gui.main_window import PySide6UnavailableError, run_gui

        try:
            return run_gui([])
        except PySide6UnavailableError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    parser.print_help(sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
