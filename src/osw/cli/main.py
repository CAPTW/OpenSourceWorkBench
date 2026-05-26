"""Minimal command line interface for OSW bootstrap checks."""

from __future__ import annotations

import argparse
import importlib.util
import platform
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from osw import __version__
from osw.core.executables import ExecutablePathRegistry
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
    runner_check_parser = subparsers.add_parser(
        "runner-check",
        help="Resolve an executable path without executing it.",
    )
    runner_check_parser.add_argument("name", help="Executable name or configured path to check.")
    runner_fake_parser = subparsers.add_parser(
        "runner-fake-smoke",
        help="Run a safe Python one-line smoke test through the backend runner.",
    )
    runner_fake_parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Timeout in seconds for the safe smoke command.",
    )
    subparsers.add_parser(
        "mesh-formats",
        help="List standard/exported mesh formats recognized by OSW.",
    )
    mesh_info_parser = subparsers.add_parser(
        "mesh-info",
        help="Inspect mesh metadata through the optional meshio bridge.",
    )
    mesh_info_parser.add_argument("path", help="Mesh file path.")
    mesh_convert_parser = subparsers.add_parser(
        "mesh-convert",
        help="Convert one standard mesh file to another through meshio.",
    )
    mesh_convert_parser.add_argument("input", help="Input mesh file path.")
    mesh_convert_parser.add_argument("output", help="Output mesh file path.")
    mesh_convert_parser.add_argument(
        "--format",
        dest="output_format",
        default=None,
        help="Optional output format override such as vtu, vtk, msh, inp, or xdmf.",
    )
    mscript_preview_parser = subparsers.add_parser(
        "mscript-preview",
        help="Preview a MATLAB/Octave .m file without executing it.",
    )
    mscript_preview_parser.add_argument("path", help="M-script .m file path.")
    mscript_preview_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    mscript_scan_parser = subparsers.add_parser(
        "mscript-scan",
        help="Run the MATLAB/Octave .m safety scanner without executing code.",
    )
    mscript_scan_parser.add_argument("path", help="M-script .m file path.")
    mscript_scan_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    subparsers.add_parser(
        "octave-check",
        help="Resolve GNU Octave without executing it.",
    )
    mscript_run_parser = subparsers.add_parser(
        "mscript-run",
        help="Run a previewed .m script through GNU Octave after safety checks.",
    )
    mscript_run_parser.add_argument("path", help="M-script .m file path.")
    mscript_run_parser.add_argument("--timeout", type=float, default=30.0, help="Timeout seconds.")
    mscript_run_parser.add_argument(
        "--allow-high-risk",
        action="store_true",
        help="Allow high-risk safety findings in an isolated workspace.",
    )
    mscript_run_parser.add_argument(
        "--allow-blocked",
        action="store_true",
        help="Allow blocked findings. Intended only for trusted local test fixtures.",
    )
    mscript_run_parser.add_argument("--workspace", default="", help="Optional run workspace root.")
    mscript_run_parser.add_argument(
        "--capture-figures",
        action="store_true",
        help="Normalize generated PNG/SVG/PDF/CSV artifacts into a FigureDataset.",
    )
    mscript_run_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    figure_artifacts_parser = subparsers.add_parser(
        "figure-artifacts-inspect",
        help="Inspect figure artifacts in a file or directory without executing scripts.",
    )
    figure_artifacts_parser.add_argument("path", help="Artifact file or directory.")
    figure_artifacts_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    figure_dataset_parser = subparsers.add_parser(
        "figure-dataset-inspect",
        help="Inspect a FigureDataset JSON file.",
    )
    figure_dataset_parser.add_argument("path", help="FigureDataset JSON path.")
    figure_dataset_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    figure_from_run_parser = subparsers.add_parser(
        "figure-dataset-from-run",
        help="Convert an OctaveRunResult JSON file to a FigureDataset JSON file.",
    )
    figure_from_run_parser.add_argument("run_result_json", help="OctaveRunResult JSON path.")
    figure_from_run_parser.add_argument("--out", required=True, help="Output dataset JSON path.")
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

    if args.command == "runner-check":
        resolution = ExecutablePathRegistry().resolve(args.name)
        print(f"Executable: {args.name}")
        print(f"Status: {'available' if resolution.found else 'missing'}")
        print(f"Source: {resolution.source}")
        if resolution.resolved_path:
            print(f"Path: {resolution.resolved_path}")
        print(resolution.diagnostics.summary())
        return 0 if resolution.found else 1

    if args.command == "runner-fake-smoke":
        from osw.solvers.runner import ExternalCommandRunner, TimeoutPolicy

        with tempfile.TemporaryDirectory(prefix="osw-runner-smoke-") as temp_dir:
            runner = ExternalCommandRunner()
            result = runner.run(
                sys.executable,
                ["-c", "print('OSW runner smoke OK')"],
                cwd=temp_dir,
                artifact_dir=Path(temp_dir) / "artifacts",
                timeout_policy=TimeoutPolicy(timeout_seconds=args.timeout),
            )
            print(f"Status: {result.status.value}")
            print(result.log.stdout.strip())
            if result.diagnostics.messages:
                print(result.diagnostics.summary())
            return 0 if result.status.value == "completed" else 1

    if args.command == "mesh-formats":
        from osw.mesh.meshio_bridge import supported_mesh_extensions, supported_mesh_formats

        print("OSW mesh formats")
        print("formats: " + ", ".join(supported_mesh_formats()))
        print("extensions: " + ", ".join(supported_mesh_extensions()))
        print("meshio dependency: " + ("available" if _module_available("meshio") else "missing"))
        return 0

    if args.command == "mesh-info":
        from osw.mesh.meshio_bridge import read_mesh

        result = read_mesh(Path(args.path))
        if result.mesh is None:
            print(result.diagnostics.summary(), file=sys.stderr)
            return 2 if result.status.value == "dependency_missing" else 1
        info = result.mesh.info
        print(f"Mesh: {Path(info.source_path).name}")
        print(f"Format: {info.format}")
        print(f"Nodes: {info.node_count}")
        print(f"Elements: {info.element_count}")
        print("Cell types: " + (", ".join(info.cell_types) or "none"))
        print(f"Bounds: {info.bounds.minimum} -> {info.bounds.maximum}")
        if info.point_data_names:
            print("Point data: " + ", ".join(info.point_data_names))
        if info.cell_data_names:
            print("Cell data: " + ", ".join(info.cell_data_names))
        if result.diagnostics.messages:
            print(result.diagnostics.summary(), file=sys.stderr)
        return 0

    if args.command == "mesh-convert":
        from osw.mesh.meshio_bridge import read_mesh, write_mesh

        import_result = read_mesh(Path(args.input))
        if import_result.mesh is None:
            print(import_result.diagnostics.summary(), file=sys.stderr)
            return 2 if import_result.status.value == "dependency_missing" else 1
        export_result = write_mesh(
            import_result.mesh,
            Path(args.output),
            file_format=args.output_format,
        )
        if not export_result.ok:
            print(export_result.diagnostics.summary(), file=sys.stderr)
            return 2 if export_result.status.value == "dependency_missing" else 1
        print(f"Wrote mesh: {export_result.output_path}")
        return 0

    if args.command == "mscript-preview":
        from osw.scripts.mscript.importer import preview_mscript

        result = preview_mscript(Path(args.path))
        if args.json:
            import json

            print(
                json.dumps(
                    {
                        "status": result.status.value,
                        "preview": result.preview.to_dict() if result.preview else None,
                        "diagnostics": result.diagnostics.to_dict(),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        elif result.preview is not None:
            _print_mscript_preview(result.preview)
            if result.diagnostics.messages:
                print(result.diagnostics.summary(), file=sys.stderr)
        else:
            print(result.diagnostics.summary(), file=sys.stderr)
        return 1 if result.status.value == "error" else 0

    if args.command == "mscript-scan":
        from osw.scripts.mscript.importer import read_mscript_text
        from osw.scripts.mscript.safety_scan import scan_mscript_text

        read_result = read_mscript_text(Path(args.path))
        if not read_result.ok:
            if args.json:
                import json

                print(
                    json.dumps(
                        {
                            "status": read_result.status.value,
                            "diagnostics": read_result.diagnostics.to_dict(),
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
            else:
                print(read_result.diagnostics.summary(), file=sys.stderr)
            return 1
        scan = scan_mscript_text(read_result.text, source=read_result.source_path)
        if args.json:
            import json

            print(json.dumps(scan.to_dict(), indent=2, sort_keys=True))
        else:
            print(f"Safety findings: {len(scan.findings)}")
            for finding in scan.findings:
                print(
                    f"- {finding.severity}: line {finding.line_no} "
                    f"{finding.token} ({finding.code}) - {finding.message}"
                )
        return 0

    if args.command == "octave-check":
        from osw.scripts.mscript.octave_runner import find_octave_executable

        resolution = find_octave_executable()
        print("GNU Octave")
        print(f"Status: {'available' if resolution.found else 'missing'}")
        print(f"Source: {resolution.source}")
        if resolution.resolved_path:
            print(f"Path: {resolution.resolved_path}")
        print(resolution.diagnostics.summary())
        return 0 if resolution.found else 1

    if args.command == "mscript-run":
        from osw.scripts.mscript.execution_policy import OctaveExecutionPolicy
        from osw.scripts.mscript.octave_runner import (
            OctaveRunner,
            OctaveRunRequest,
            OctaveRunStatus,
        )

        policy = OctaveExecutionPolicy(
            timeout_seconds=args.timeout,
            allow_high_risk=args.allow_high_risk,
            allow_blocked=args.allow_blocked,
        )
        request = OctaveRunRequest(
            Path(args.path),
            working_directory=Path(args.workspace) if args.workspace else None,
            policy=policy,
        )
        result = OctaveRunner().run(request)
        dataset = None
        if args.capture_figures:
            from osw.scripts.mscript.figure_capture import figure_dataset_from_octave_result

            dataset = figure_dataset_from_octave_result(result)
        if args.json:
            import json

            if dataset is None:
                payload = result.to_dict()
            else:
                payload = {"run": result.to_dict()}
                payload["figure_dataset"] = dataset.to_dict()
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _print_octave_run_result(result)
            if dataset is not None:
                print(
                    "Captured "
                    f"{len(dataset.figures)} figure artifact(s), "
                    f"{len(dataset.workspace_variables)} workspace variable summary item(s)."
                )
        return 0 if result.status is OctaveRunStatus.COMPLETED else 1

    if args.command == "figure-artifacts-inspect":
        from osw.scripts.mscript.figure_capture import (
            discover_figure_artifacts,
            figure_dataset_from_artifacts,
        )

        source = Path(args.path)
        paths = discover_figure_artifacts(source) if source.is_dir() else (source,)
        dataset = figure_dataset_from_artifacts(paths, source_script=str(source))
        if args.json:
            import json

            print(json.dumps(dataset.to_dict(), indent=2, sort_keys=True))
        else:
            _print_figure_dataset(dataset)
            if dataset.diagnostics.messages:
                print(dataset.diagnostics.summary(), file=sys.stderr)
        return 1 if dataset.diagnostics.has_errors else 0

    if args.command == "figure-dataset-inspect":
        from osw.scripts.mscript.figure_capture import load_figure_dataset_json

        dataset = load_figure_dataset_json(Path(args.path))
        if args.json:
            import json

            print(json.dumps(dataset.to_dict(), indent=2, sort_keys=True))
        else:
            _print_figure_dataset(dataset)
        return 0

    if args.command == "figure-dataset-from-run":
        import json

        from osw.scripts.mscript.figure_capture import (
            export_figure_dataset_json,
            figure_dataset_from_octave_result,
        )
        from osw.scripts.mscript.octave_runner import OctaveRunResult

        payload = json.loads(Path(args.run_result_json).read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "run" in payload:
            payload = payload["run"]
        result = OctaveRunResult.from_dict(payload)
        dataset = figure_dataset_from_octave_result(result)
        output_path = export_figure_dataset_json(dataset, Path(args.out))
        print(f"Wrote FigureDataset JSON: {output_path}")
        return 0

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


def _print_mscript_preview(preview: object) -> None:
    signature = getattr(preview, "function_signature", None)
    print(f"M-script: {getattr(preview, 'name', '')}")
    print(f"Kind: {getattr(getattr(preview, 'kind', ''), 'value', getattr(preview, 'kind', ''))}")
    if signature is not None:
        print(f"Function: {signature.raw_signature or signature.name}")
    print(f"Lines: {getattr(preview, 'line_count', 0)}")
    print(f"Safety: {preview.safety_summary()}")
    print(f"Plot hints: {len(getattr(preview, 'plot_hints', ()))}")
    high = [
        finding
        for finding in getattr(preview, "safety_findings", ())
        if finding.severity in {"high", "blocked"}
    ]
    for finding in high:
        print(
            f"{finding.severity.upper()} line {finding.line_no}: "
            f"{finding.token} - {finding.message}"
        )


def _print_octave_run_result(result: object) -> None:
    status = getattr(getattr(result, "status", ""), "value", getattr(result, "status", ""))
    print(f"Octave run status: {status}")
    print(f"Workspace: {getattr(result, 'workspace_dir', '')}")
    return_code = getattr(result, "return_code", None)
    if return_code is not None:
        print(f"Return code: {return_code}")
    stdout = str(getattr(result, "stdout", "") or "").strip()
    stderr = str(getattr(result, "stderr", "") or "").strip()
    if stdout:
        print("stdout:")
        print(stdout)
    if stderr:
        print("stderr:", file=sys.stderr)
        print(stderr, file=sys.stderr)
    diagnostics = getattr(result, "diagnostics", None)
    if diagnostics is not None and getattr(diagnostics, "messages", ()):
        print(diagnostics.summary(), file=sys.stderr)


def _print_figure_dataset(dataset: object) -> None:
    print(f"FigureDataset: {getattr(dataset, 'dataset_id', '')}")
    print(f"Engine: {getattr(dataset, 'engine', 'unknown')}")
    print(f"Figures: {len(getattr(dataset, 'figures', ())) }")
    print(f"Workspace variables: {len(getattr(dataset, 'workspace_variables', ())) }")
    for record in getattr(dataset, "figures", ()):
        path = getattr(record, "primary_path", None)
        print(
            f"- {getattr(record, 'figure_id', '')}: "
            f"{getattr(record, 'title', '')} "
            f"[{getattr(record, 'image_format', '')}] {path or ''}"
        )
    for variable in getattr(dataset, "workspace_variables", ()):
        shape = "x".join(str(item) for item in getattr(variable, "shape", ()))
        print(
            f"- variable {getattr(variable, 'name', '')}: "
            f"{getattr(variable, 'type_name', '')} {shape}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
