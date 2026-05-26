"""Minimal command line interface for OSW bootstrap checks."""

from __future__ import annotations

import argparse
import importlib.util
import platform
import sys
from collections.abc import Sequence
from pathlib import Path

from osw import __version__
from osw.plugins.discovery import discover_local_plugin_manifests
from osw.plugins.errors import PluginDiagnosticSeverity
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
        "--plugins-dir",
        action="append",
        default=[],
        help="Alias for --plugin-path.",
    )
    plugin_health_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON health records.",
    )
    plugins_list_parser = subparsers.add_parser(
        "plugins-list",
        help="List plugin manifests from local directories without loading plugin code.",
    )
    plugins_list_parser.add_argument(
        "--plugins-dir",
        action="append",
        default=[],
        help="Local plugin directory or manifest path to scan. May be repeated.",
    )
    plugins_list_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    plugins_validate_parser = subparsers.add_parser(
        "plugins-validate",
        help="Validate local plugin manifests without loading plugin code.",
    )
    plugins_validate_parser.add_argument(
        "path",
        help="Plugin manifest, plugin folder, or parent plugin directory to validate.",
    )
    plugins_validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON validation output.",
    )
    plugins_health_parser = subparsers.add_parser(
        "plugins-health",
        help="Alias for plugin-health using --plugins-dir.",
    )
    plugins_health_parser.add_argument(
        "--plugins-dir",
        action="append",
        default=[],
        help="Local plugin directory or manifest path to scan. May be repeated.",
    )
    plugins_health_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    subparsers.add_parser(
        "gui",
        help="Launch the optional PySide6 GUI shell.",
        description="Launch the optional PySide6 GUI shell.",
    )
    demo_parser = subparsers.add_parser(
        "project-demo-json",
        help="Write the HeatSink_Flow demo ProjectSchema JSON file.",
    )
    demo_parser.add_argument("--out", required=True, help="Output JSON project path.")
    validate_parser = subparsers.add_parser(
        "project-validate",
        help="Validate an OSW ProjectSchema JSON/YAML file without running solvers.",
    )
    validate_parser.add_argument("path", help="Project file path.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        print("\n".join(doctor_lines()))
        return 0

    if args.command == "plugin-health":
        plugin_paths = [
            DEFAULT_PLUGIN_INSTALL_ROOT,
            *(Path(path) for path in args.plugin_path),
            *(Path(path) for path in args.plugins_dir),
        ]
        records = collect_plugin_health_records(plugin_paths)
        if args.json:
            print(plugin_health_records_as_json(records))
        else:
            print(plugin_health_records_as_text(records))
        return 0

    if args.command == "plugins-health":
        plugin_paths = [DEFAULT_PLUGIN_INSTALL_ROOT, *(Path(path) for path in args.plugins_dir)]
        records = collect_plugin_health_records(plugin_paths)
        if args.json:
            print(plugin_health_records_as_json(records))
        else:
            print(plugin_health_records_as_text(records))
        return 0

    if args.command == "plugins-list":
        plugin_paths = [DEFAULT_PLUGIN_INSTALL_ROOT, *(Path(path) for path in args.plugins_dir)]
        result = discover_local_plugin_manifests(plugin_paths)
        if args.json:
            import json

            print(
                json.dumps(
                    {
                        "plugins": [
                            manifest.to_dict() for manifest in result.manifests
                        ],
                        "diagnostics": [
                            diagnostic.to_dict() for diagnostic in result.diagnostics
                        ],
                        "duplicate_ids": result.duplicate_ids,
                        "skipped_paths": result.skipped_paths,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        print("OSW plugins")
        if not result.manifests:
            print("No local plugin manifests discovered.")
        for manifest in result.manifests:
            print(f"- {manifest.id}: {manifest.name} ({manifest.type.value})")
        for diagnostic in result.diagnostics:
            print(f"{diagnostic.severity.value}: {diagnostic.message}", file=sys.stderr)
        return 0

    if args.command == "plugins-validate":
        result = discover_local_plugin_manifests([Path(args.path)])
        has_errors = any(
            diagnostic.severity is PluginDiagnosticSeverity.ERROR
            for diagnostic in result.diagnostics
        ) or bool(result.duplicate_ids)
        if args.json:
            import json

            print(
                json.dumps(
                    {
                        "plugins": [manifest.id for manifest in result.manifests],
                        "diagnostics": [
                            diagnostic.to_dict() for diagnostic in result.diagnostics
                        ],
                        "duplicate_ids": result.duplicate_ids,
                        "skipped_paths": result.skipped_paths,
                        "valid": not has_errors,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 1 if has_errors else 0
        print("OSW plugin validation")
        for manifest in result.manifests:
            print(f"ok: {manifest.id}")
        for duplicate_id in result.duplicate_ids:
            print(f"error: Duplicate plugin id: {duplicate_id}", file=sys.stderr)
        for diagnostic in result.diagnostics:
            print(f"{diagnostic.severity.value}: {diagnostic.message}", file=sys.stderr)
        return 1 if has_errors else 0

    if args.command == "gui":
        from osw.gui.main_window import PySide6UnavailableError, run_gui

        try:
            return run_gui([])
        except PySide6UnavailableError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    if args.command == "project-demo-json":
        from osw.core.demo_project import create_heatsink_flow_demo_project
        from osw.core.project_io import save_project_json

        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_project_json(create_heatsink_flow_demo_project(), output_path)
        print(f"Wrote demo project JSON: {args.out}")
        return 0

    if args.command == "project-validate":
        from osw.core.project_io import load_project
        from osw.core.validation import ProjectSchemaError

        try:
            project = load_project(Path(args.path))
        except ProjectSchemaError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        report = project.validate()
        print(report.friendly_summary())
        return 1 if report.has_errors else 0

    parser.print_help(sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
