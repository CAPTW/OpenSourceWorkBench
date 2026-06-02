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


def _add_gmsh_geometry_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--kind",
        default="box",
        choices=("rectangle", "box", "cylinder", "sphere", "plate_with_hole"),
        help="Primitive geometry kind.",
    )
    parser.add_argument("--length", type=float, default=1.0, help="Box length.")
    parser.add_argument("--width", type=float, default=1.0, help="Box/rectangle width.")
    parser.add_argument("--height", type=float, default=1.0, help="Box/cylinder height.")
    parser.add_argument("--radius", type=float, default=0.5, help="Cylinder/sphere radius.")
    parser.add_argument("--hole-radius", type=float, default=0.1, help="Plate hole radius.")
    parser.add_argument("--center-x", type=float, default=None, help="Plate hole center x.")
    parser.add_argument("--center-y", type=float, default=None, help="Plate hole center y.")
    parser.add_argument("--mesh-size", type=float, default=0.1, help="Global mesh size.")
    parser.add_argument(
        "--dimension",
        default="",
        choices=("", "dim2", "dim3", "2", "3"),
        help="Optional mesh dimension override.",
    )
    parser.add_argument("--units", default="", help="Geometry units metadata.")


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
    subparsers.add_parser(
        "gmsh-check",
        help="Resolve the Gmsh executable without executing it.",
    )
    subparsers.add_parser(
        "gmsh-formats",
        help="List bounded Gmsh primitive geometry templates.",
    )
    gmsh_write_parser = subparsers.add_parser(
        "gmsh-write-geo",
        help="Write a deterministic primitive Gmsh .geo script without running Gmsh.",
    )
    _add_gmsh_geometry_arguments(gmsh_write_parser)
    gmsh_write_parser.add_argument("--out", required=True, help="Output .geo path.")
    gmsh_generate_parser = subparsers.add_parser(
        "gmsh-generate",
        help="Explicitly run Gmsh through the backend runner for a primitive mesh.",
    )
    _add_gmsh_geometry_arguments(gmsh_generate_parser)
    gmsh_generate_parser.add_argument("--out-dir", required=True, help="Output directory.")
    gmsh_generate_parser.add_argument("--output-name", default="gmsh_mesh", help="Output stem.")
    gmsh_generate_parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout seconds.",
    )
    gmsh_generate_parser.add_argument(
        "--convert-to-vtu",
        action="store_true",
        help="Attempt meshio VTU conversion after .msh generation.",
    )
    calculix_write_parser = subparsers.add_parser(
        "calculix-write-inp",
        help="Write a deterministic CalculiX .inp deck without running ccx.",
    )
    calculix_write_parser.add_argument(
        "--demo",
        choices=("cantilever",),
        default="cantilever",
        help="Built-in demo deck to write.",
    )
    calculix_write_parser.add_argument("--out", required=True, help="Output .inp path.")
    calculix_preview_parser = subparsers.add_parser(
        "calculix-deck-preview",
        help="Preview a CalculiX input deck from ProjectSchema without running ccx.",
    )
    calculix_preview_parser.add_argument("project", help="Project JSON/YAML path.")
    calculix_validate_parser = subparsers.add_parser(
        "calculix-validate-project",
        help="Validate CalculiX deck readiness without running ccx.",
    )
    calculix_validate_parser.add_argument("project", help="Project JSON/YAML path.")
    subparsers.add_parser(
        "calculix-check",
        help="Resolve the CalculiX ccx executable without executing it.",
    )
    calculix_run_parser = subparsers.add_parser(
        "calculix-run-inp",
        help="Explicitly run a CalculiX .inp deck through the backend runner.",
    )
    calculix_run_parser.add_argument("path", help="CalculiX .inp deck path.")
    calculix_run_parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout seconds.",
    )
    calculix_run_parser.add_argument(
        "--case-dir",
        default="",
        help="Isolated CalculiX run directory.",
    )
    calculix_demo_run_parser = subparsers.add_parser(
        "calculix-run-demo",
        help="Generate the cantilever demo deck and explicitly attempt a ccx run.",
    )
    calculix_demo_run_parser.add_argument(
        "--demo",
        choices=("cantilever",),
        default="cantilever",
        help="Built-in demo deck to run.",
    )
    calculix_demo_run_parser.add_argument(
        "--out-dir",
        required=True,
        help="Output run directory.",
    )
    calculix_demo_run_parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout seconds.",
    )
    calculix_parse_results_parser = subparsers.add_parser(
        "calculix-parse-results",
        help="Parse existing CalculiX result artifacts without running ccx.",
    )
    calculix_parse_results_parser.add_argument("path", help="Case directory or run result JSON.")
    calculix_parse_dat_parser = subparsers.add_parser(
        "calculix-parse-dat",
        help="Parse a CalculiX .dat artifact without running ccx.",
    )
    calculix_parse_dat_parser.add_argument("path", help="CalculiX .dat path.")
    calculix_parse_sta_parser = subparsers.add_parser(
        "calculix-parse-sta",
        help="Parse a CalculiX .sta status artifact without running ccx.",
    )
    calculix_parse_sta_parser.add_argument("path", help="CalculiX .sta path.")
    calculix_results_summary_parser = subparsers.add_parser(
        "calculix-results-summary",
        help="Print parsed CalculiX result summaries without running ccx.",
    )
    calculix_results_summary_parser.add_argument(
        "path",
        help="Case directory, run result JSON, or result artifact path.",
    )
    calculix_validate_cantilever_parser = subparsers.add_parser(
        "calculix-validate-cantilever",
        help="Validate parsed CalculiX displacement against cantilever beam theory.",
    )
    calculix_validate_cantilever_parser.add_argument(
        "path",
        help="Case directory, run result JSON, or result artifact path.",
    )
    calculix_validate_cantilever_parser.add_argument("--force", type=float, required=True)
    calculix_validate_cantilever_parser.add_argument("--length", type=float, required=True)
    calculix_validate_cantilever_parser.add_argument(
        "--elastic-modulus",
        type=float,
        required=True,
    )
    calculix_validate_cantilever_parser.add_argument(
        "--second-moment-area",
        type=float,
        required=True,
    )
    calculix_validate_cantilever_parser.add_argument(
        "--tolerance",
        type=float,
        default=0.05,
        help="Allowed relative error fraction.",
    )
    subparsers.add_parser(
        "openfoam-check",
        help="Resolve OpenFOAM executables without executing them.",
    )
    openfoam_write_parser = subparsers.add_parser(
        "openfoam-write-case",
        help="Write a bounded OpenFOAM cavity or duct template case without running OpenFOAM.",
    )
    openfoam_write_parser.add_argument(
        "--template",
        choices=("cavity", "duct"),
        default="cavity",
        help="Template kind.",
    )
    openfoam_write_parser.add_argument("--out-dir", required=True, help="Output directory.")
    openfoam_write_parser.add_argument(
        "--inlet-velocity",
        type=float,
        default=1.0,
        help="Duct inlet x velocity.",
    )
    openfoam_write_parser.add_argument(
        "--outlet-pressure",
        type=float,
        default=0.0,
        help="Duct outlet pressure.",
    )
    openfoam_run_parser = subparsers.add_parser(
        "openfoam-run-case",
        help="Explicitly run an OpenFOAM template case through the backend runner.",
    )
    openfoam_run_parser.add_argument("case_dir", help="OpenFOAM case directory.")
    openfoam_run_parser.add_argument(
        "--solver",
        default="icoFoam",
        choices=("icoFoam", "simpleFoam"),
        help="OpenFOAM solver executable.",
    )
    openfoam_run_parser.add_argument("--timeout", type=float, default=30.0)
    openfoam_parse_log_parser = subparsers.add_parser(
        "openfoam-parse-log",
        help="Parse an OpenFOAM log file without running OpenFOAM.",
    )
    openfoam_parse_log_parser.add_argument("path", help="OpenFOAM log file path.")
    openfoam_results_summary_parser = subparsers.add_parser(
        "openfoam-results-summary",
        help="Parse residual summaries from an OpenFOAM case directory.",
    )
    openfoam_results_summary_parser.add_argument("case_dir", help="Case directory.")
    subparsers.add_parser(
        "coolprop-check",
        help="Check whether the optional CoolProp package is importable.",
    )
    coolprop_props_parser = subparsers.add_parser(
        "coolprop-props",
        help="Calculate bounded CoolProp properties at a T/P state.",
    )
    coolprop_props_parser.add_argument("--fluid", required=True, help="CoolProp fluid name.")
    coolprop_props_parser.add_argument("--T", type=float, required=True, help="Temperature [K].")
    coolprop_props_parser.add_argument("--P", type=float, required=True, help="Pressure [Pa].")
    coolprop_props_parser.add_argument(
        "--outputs",
        default="density,viscosity,enthalpy,entropy,cp,thermal_conductivity",
        help="Comma-separated output properties.",
    )
    coolprop_sweep_parser = subparsers.add_parser(
        "coolprop-sweep",
        help="Calculate a bounded CoolProp T/P property sweep and write ResultDataset JSON.",
    )
    coolprop_sweep_parser.add_argument("--fluid", required=True, help="CoolProp fluid name.")
    coolprop_sweep_parser.add_argument(
        "--sweep",
        choices=("T", "P"),
        required=True,
        help="Sweep variable.",
    )
    coolprop_sweep_parser.add_argument("--start", type=float, required=True)
    coolprop_sweep_parser.add_argument("--stop", type=float, required=True)
    coolprop_sweep_parser.add_argument("--count", type=int, required=True)
    coolprop_sweep_parser.add_argument("--T", type=float, default=None, help="Fixed T [K].")
    coolprop_sweep_parser.add_argument("--P", type=float, default=None, help="Fixed P [Pa].")
    coolprop_sweep_parser.add_argument("--out", required=True, help="Output ResultDataset JSON.")
    coolprop_sweep_parser.add_argument(
        "--outputs",
        default="density",
        help="Comma-separated output properties.",
    )
    subparsers.add_parser(
        "cantera-check",
        help="Check whether the optional Cantera package is importable.",
    )
    cantera_reactor_parser = subparsers.add_parser(
        "cantera-reactor",
        help="Run a bounded in-process Cantera 0D reactor and write ResultDataset JSON.",
    )
    cantera_reactor_parser.add_argument("--mechanism", default="gri30.yaml")
    cantera_reactor_parser.add_argument("--phase-name", default="")
    cantera_reactor_parser.add_argument("--composition", required=True)
    cantera_reactor_parser.add_argument("--T", type=float, required=True)
    cantera_reactor_parser.add_argument("--P", type=float, required=True)
    cantera_reactor_parser.add_argument("--end-time", type=float, required=True)
    cantera_reactor_parser.add_argument("--time-step", type=float, default=0.00025)
    cantera_reactor_parser.add_argument(
        "--tracked-species",
        default="CH4,O2,CO2,H2O",
        help="Comma-separated species names.",
    )
    cantera_reactor_parser.add_argument("--out", required=True, help="Output ResultDataset JSON.")
    chm_inspect_parser = subparsers.add_parser(
        "chm-result-inspect",
        help="Inspect CHM ResultDataset or raw CoolProp/Cantera result JSON.",
    )
    chm_inspect_parser.add_argument("path", help="CHM JSON path.")
    chm_inspect_parser.add_argument("--json", action="store_true", help="Emit ResultDataset JSON.")
    result_dataset_parser = subparsers.add_parser(
        "result-dataset-inspect",
        help="Inspect a ResultDataset/FigureDataset/MAT/BoundaryCurve JSON file.",
    )
    result_dataset_parser.add_argument("path", help="Dataset JSON path.")
    result_dataset_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    result_catalog_parser = subparsers.add_parser(
        "result-catalog-inspect",
        help="Inspect a ResultCatalog JSON file.",
    )
    result_catalog_parser.add_argument("path", help="ResultCatalog JSON path.")
    result_catalog_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    result_catalog_from_project_parser = subparsers.add_parser(
        "result-catalog-from-project",
        help="Build a ResultCatalog from ProjectSchema summaries without execution.",
    )
    result_catalog_from_project_parser.add_argument("project", help="Project JSON/YAML path.")
    result_catalog_from_project_parser.add_argument("--out", required=True, help="Output JSON.")
    result_dataset_export_parser = subparsers.add_parser(
        "result-dataset-export-json",
        help="Normalize supported result JSON input to ResultDataset JSON.",
    )
    result_dataset_export_parser.add_argument("input", help="Input JSON path.")
    result_dataset_export_parser.add_argument("--out", required=True, help="Output JSON path.")
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
    mat_info_parser = subparsers.add_parser(
        "mat-info",
        help="Inspect MATLAB MAT-file variables without running MATLAB or Octave.",
    )
    mat_info_parser.add_argument("path", help="MAT file path.")
    mat_info_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    mat_vars_parser = subparsers.add_parser(
        "mat-vars",
        help="List MATLAB MAT-file variable names without loading script code.",
    )
    mat_vars_parser.add_argument("path", help="MAT file path.")
    mat_vars_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    mat_export_parser = subparsers.add_parser(
        "mat-export-csv",
        help="Export a real numeric 1D/2D MAT variable to CSV.",
    )
    mat_export_parser.add_argument("path", help="MAT file path.")
    mat_export_parser.add_argument("variable", help="Variable name to export.")
    mat_export_parser.add_argument("--out", required=True, help="Output CSV path.")
    curve_from_csv_parser = subparsers.add_parser(
        "curve-from-csv",
        help="Create a BoundaryCurve JSON file from numeric CSV x/y columns.",
    )
    curve_from_csv_parser.add_argument("path", help="CSV file path.")
    curve_from_csv_parser.add_argument("--x-column", required=True, help="Independent column.")
    curve_from_csv_parser.add_argument("--y-column", required=True, help="Dependent column.")
    curve_from_csv_parser.add_argument("--x-unit", default="", help="Independent axis unit.")
    curve_from_csv_parser.add_argument("--y-unit", default="", help="Dependent axis unit.")
    curve_from_csv_parser.add_argument("--kind", default="generic_xy", help="Boundary curve kind.")
    curve_from_csv_parser.add_argument("--out", required=True, help="Output curve JSON path.")
    curve_from_mat_parser = subparsers.add_parser(
        "curve-from-mat",
        help="Create a BoundaryCurve JSON file from MAT variables when values are available.",
    )
    curve_from_mat_parser.add_argument("path", help="MAT file path.")
    curve_from_mat_parser.add_argument("--x", required=True, help="Independent MAT variable.")
    curve_from_mat_parser.add_argument("--y", required=True, help="Dependent MAT variable.")
    curve_from_mat_parser.add_argument("--x-unit", default="", help="Independent axis unit.")
    curve_from_mat_parser.add_argument("--y-unit", default="", help="Dependent axis unit.")
    curve_from_mat_parser.add_argument("--kind", default="generic_xy", help="Boundary curve kind.")
    curve_from_mat_parser.add_argument("--out", required=True, help="Output curve JSON path.")
    curve_inspect_parser = subparsers.add_parser(
        "curve-inspect",
        help="Inspect a BoundaryCurve JSON file.",
    )
    curve_inspect_parser.add_argument("path", help="BoundaryCurve JSON path.")
    curve_inspect_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    curve_export_parser = subparsers.add_parser(
        "curve-export-csv",
        help="Export a BoundaryCurve JSON file to CSV.",
    )
    curve_export_parser.add_argument("path", help="BoundaryCurve JSON path.")
    curve_export_parser.add_argument("--out", required=True, help="Output CSV path.")
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
    report_export_parser = subparsers.add_parser(
        "report-export",
        help="Export a deterministic project report without running solvers or scripts.",
    )
    report_export_parser.add_argument("project", help="Project JSON/YAML path.")
    report_export_parser.add_argument("--out", required=True, help="Output report path.")
    report_export_parser.add_argument(
        "--format",
        default="html",
        choices=("html", "markdown", "json_summary"),
        help="Report export format.",
    )
    report_summary_parser = subparsers.add_parser(
        "report-summary",
        help="Print a project report summary without writing report artifacts.",
    )
    report_summary_parser.add_argument("project", help="Project JSON/YAML path.")
    report_summary_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    report_export_demo_parser = subparsers.add_parser(
        "report-export-demo",
        help="Export the HeatSink_Flow demo report without running solvers.",
    )
    report_export_demo_parser.add_argument("--out", required=True, help="Output report path.")
    report_export_demo_parser.add_argument(
        "--format",
        default="html",
        choices=("html", "markdown", "json_summary"),
        help="Report export format.",
    )
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

    if args.command == "gmsh-check":
        from osw.mesh.gmsh_adapter import find_gmsh_executable

        resolution = find_gmsh_executable()
        print("Gmsh")
        print(f"Status: {'available' if resolution.found else 'missing'}")
        print(f"Source: {resolution.source}")
        if resolution.resolved_path:
            print(f"Path: {resolution.resolved_path}")
        print(resolution.diagnostics.summary())
        return 0 if resolution.found else 1

    if args.command == "gmsh-formats":
        from osw.mesh.gmsh_adapter import find_gmsh_executable

        resolution = find_gmsh_executable()
        print("OSW Gmsh primitive templates")
        print("geometry kinds: rectangle, box, cylinder, sphere, plate_with_hole")
        print("mesh dimensions: dim2, dim3")
        print("outputs: geo, msh, optional vtu via meshio")
        print("Gmsh executable: " + ("available" if resolution.found else "missing"))
        print("meshio dependency: " + ("available" if _module_available("meshio") else "missing"))
        return 0

    if args.command == "gmsh-write-geo":
        from osw.mesh.gmsh_geometry import write_geo_script

        request = _gmsh_request_from_args(args, output_dir=Path(args.out).parent)
        output_path = write_geo_script(request, Path(args.out))
        print(f"Wrote Gmsh .geo script: {output_path}")
        return 0

    if args.command == "gmsh-generate":
        from osw.mesh.gmsh_adapter import GmshAdapter, GmshMeshStatus

        request = _gmsh_request_from_args(
            args,
            output_dir=Path(args.out_dir),
            output_name=args.output_name,
            convert_to_vtu=args.convert_to_vtu,
            timeout_seconds=args.timeout,
        )
        result = GmshAdapter().generate_mesh(request)
        _print_gmsh_result(result)
        if result.status is GmshMeshStatus.OK:
            return 0
        if result.status is GmshMeshStatus.WARNING and result.msh_path and result.msh_path.exists():
            return 0
        return 2 if result.status is GmshMeshStatus.DEPENDENCY_MISSING else 1

    if args.command == "calculix-write-inp":
        from osw.solvers.calculix.adapter import create_cantilever_demo_case
        from osw.solvers.calculix.input_deck import (
            CalculixInputDeckGenerator,
            write_input_deck,
        )

        case = create_cantilever_demo_case()
        text = CalculixInputDeckGenerator().generate(case)
        output_path = write_input_deck(text, Path(args.out))
        print(f"Wrote CalculiX input deck: {output_path}")
        print("Execution: not run")
        return 0

    if args.command == "calculix-deck-preview":
        from osw.core.project_io import load_project
        from osw.core.validation import ProjectSchemaError
        from osw.solvers.calculix.adapter import project_to_calculix_deck

        project_path = Path(args.project)
        try:
            project = load_project(project_path)
        except ProjectSchemaError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        result = project_to_calculix_deck(project, base_path=project_path.parent)
        if result.input_text:
            print(result.input_text, end="")
        if result.diagnostics:
            _print_calculix_diagnostics(result.diagnostics, stream=sys.stderr)
        return 1 if result.status == "error" else 0

    if args.command == "calculix-validate-project":
        from osw.core.project_io import load_project
        from osw.core.validation import ProjectSchemaError
        from osw.solvers.calculix.validation import validate_calculix_readiness

        project_path = Path(args.project)
        try:
            project = load_project(project_path)
        except ProjectSchemaError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        report = validate_calculix_readiness(project, base_path=project_path.parent)
        print(report.friendly_summary())
        return 1 if report.has_errors else 0

    if args.command == "calculix-check":
        from osw.solvers.calculix.runner import find_ccx_executable

        resolution = find_ccx_executable()
        print("CalculiX ccx check")
        print(f"Executable: {resolution.resolved_path or 'not found'}")
        print(f"Source: {resolution.source}")
        if resolution.diagnostics.messages:
            print(resolution.diagnostics.summary(), file=sys.stderr)
        return 0 if resolution.found else 1

    if args.command == "calculix-run-inp":
        from osw.solvers.calculix.runner import (
            CalculiXRunner,
            CalculiXRunPolicy,
        )

        policy = CalculiXRunPolicy(timeout_seconds=args.timeout)
        result = CalculiXRunner().run_input_deck(
            Path(args.path),
            case_dir=Path(args.case_dir) if args.case_dir else None,
            policy=policy,
        )
        _print_calculix_run_result(result)
        status = getattr(getattr(result, "status", ""), "value", getattr(result, "status", ""))
        return 0 if status == "completed" else 2 if status == "missing_executable" else 1

    if args.command == "calculix-run-demo":
        from osw.solvers.calculix.adapter import create_cantilever_demo_case
        from osw.solvers.calculix.input_deck import (
            CalculixInputDeckGenerator,
            write_input_deck,
        )
        from osw.solvers.calculix.runner import (
            CalculiXRunner,
            CalculiXRunPolicy,
        )

        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        case = create_cantilever_demo_case()
        input_deck = write_input_deck(
            CalculixInputDeckGenerator().generate(case),
            out_dir / "cantilever.inp",
        )
        print(f"Wrote CalculiX input deck: {input_deck}")
        result = CalculiXRunner().run_input_deck(
            input_deck,
            case_dir=out_dir,
            policy=CalculiXRunPolicy(timeout_seconds=args.timeout),
        )
        _print_calculix_run_result(result)
        status = getattr(getattr(result, "status", ""), "value", getattr(result, "status", ""))
        return 0 if status == "completed" else 2 if status == "missing_executable" else 1

    if args.command == "calculix-parse-results":
        parsed = _load_calculix_parsed_results_source(Path(args.path))
        _print_calculix_parsed_results(parsed)
        status = getattr(getattr(parsed, "status", ""), "value", getattr(parsed, "status", ""))
        return 0 if status in {"parsed", "partial"} else 1

    if args.command == "calculix-parse-dat":
        from osw.solvers.calculix.dat_parser import parse_calculix_dat

        parsed = parse_calculix_dat(Path(args.path))
        _print_calculix_parsed_results(parsed)
        status = getattr(getattr(parsed, "status", ""), "value", getattr(parsed, "status", ""))
        return 0 if status in {"parsed", "partial"} else 1

    if args.command == "calculix-parse-sta":
        from osw.solvers.calculix.sta_parser import parse_calculix_sta

        summary = parse_calculix_sta(Path(args.path))
        print("CalculiX STA summary")
        print(f"Completed: {summary.completed}")
        print(f"Increments: {summary.increments}")
        print(f"Last step: {summary.last_step}")
        print(f"Last increment: {summary.last_increment}")
        for warning in summary.warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        for error in summary.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1 if summary.errors else 0

    if args.command == "calculix-results-summary":
        parsed = _load_calculix_parsed_results_source(Path(args.path))
        _print_calculix_parsed_results(parsed)
        status = getattr(getattr(parsed, "status", ""), "value", getattr(parsed, "status", ""))
        return 0 if status in {"parsed", "partial"} else 1

    if args.command == "calculix-validate-cantilever":
        from osw.solvers.calculix.validation import (
            CantileverValidationInput,
            validate_cantilever_displacement,
        )

        parsed = _load_calculix_parsed_results_source(Path(args.path))
        validation = validate_cantilever_displacement(
            parsed,
            CantileverValidationInput(
                force=args.force,
                length=args.length,
                elastic_modulus=args.elastic_modulus,
                second_moment_area=args.second_moment_area,
                tolerance_fraction=args.tolerance,
            ),
        )
        print("CalculiX cantilever validation")
        print(f"Expected max displacement: {validation.expected_displacement:.12g}")
        if validation.observed_displacement is not None:
            print(f"Observed max displacement: {validation.observed_displacement:.12g}")
        else:
            print("Observed max displacement: missing")
        print(f"Relative error: {validation.relative_error:.12g}")
        print(f"Tolerance: {validation.tolerance_ratio:.12g}")
        print(f"Passed: {validation.passed}")
        print(validation.message)
        for diagnostic in validation.diagnostics:
            print(f"WARNING: {diagnostic}", file=sys.stderr)
        return 0 if validation.passed else 1

    if args.command == "openfoam-check":
        from osw.solvers.openfoam.runner import OPENFOAM_EXECUTABLES, find_openfoam_executable

        print("OpenFOAM executable check")
        missing = False
        for executable in OPENFOAM_EXECUTABLES:
            resolution = find_openfoam_executable(executable)
            print(f"{executable}: {resolution.resolved_path or 'not found'}")
            print(f"  source: {resolution.source}")
            if not resolution.found:
                missing = True
                if resolution.diagnostics.messages:
                    print(resolution.diagnostics.summary(), file=sys.stderr)
        return 1 if missing else 0

    if args.command == "openfoam-write-case":
        from osw.solvers.openfoam.case_generator import (
            default_cavity_request,
            default_duct_request,
            generate_openfoam_case,
        )

        target_dir = Path(args.out_dir)
        if args.template == "duct":
            request = default_duct_request(
                target_dir.parent,
                inlet_velocity=args.inlet_velocity,
                outlet_pressure=args.outlet_pressure,
            )
        else:
            request = default_cavity_request(target_dir.parent)
        request = request.__class__(
            template_kind=request.template_kind,
            solver=request.solver,
            case_name=target_dir.name,
            output_dir=request.output_dir,
            dimensions=request.dimensions,
            mesh_settings=request.mesh_settings,
            boundaries=request.boundaries,
            transport=request.transport,
            control=request.control,
            metadata=request.metadata,
        )
        result = generate_openfoam_case(request)
        print(f"OpenFOAM case status: {result.status}")
        print(f"Case directory: {result.case_dir}")
        for path in result.generated_files:
            print(f"  - {path.relative_to(result.case_dir)}")
        if result.diagnostics.messages:
            print(result.diagnostics.summary(), file=sys.stderr)
        return 1 if result.status == "error" else 0

    if args.command == "openfoam-run-case":
        from osw.solvers.openfoam.model import OpenFOAMRunPolicy
        from osw.solvers.openfoam.runner import OpenFOAMRunner

        result = OpenFOAMRunner().run_case(
            Path(args.case_dir),
            args.solver,
            OpenFOAMRunPolicy(timeout_seconds=args.timeout),
        )
        _print_openfoam_run_result(result)
        status = getattr(getattr(result, "status", ""), "value", getattr(result, "status", ""))
        return 0 if status == "completed" else 2 if status == "missing_executable" else 1

    if args.command == "openfoam-parse-log":
        from osw.solvers.openfoam.residual_parser import parse_openfoam_log

        summary = parse_openfoam_log(Path(args.path))
        _print_openfoam_residual_summary(summary)
        return 1 if summary.diagnostics.has_errors else 0

    if args.command == "openfoam-results-summary":
        from osw.solvers.openfoam.residual_parser import parse_openfoam_case_logs

        summary = parse_openfoam_case_logs(Path(args.case_dir))
        _print_openfoam_residual_summary(summary)
        return 1 if summary.diagnostics.has_errors else 0

    if args.command == "coolprop-check":
        from osw.solvers.coolprop.property_adapter import coolprop_available

        available = coolprop_available()
        print("CoolProp")
        print(f"Status: {'available' if available else 'missing'}")
        if not available:
            print(
                "CoolProp is not installed. Install the CHM optional extra or install "
                "CoolProp to run thermophysical property calculations.",
                file=sys.stderr,
            )
        return 0 if available else 1

    if args.command == "coolprop-props":
        from osw.solvers.coolprop.model import CoolPropPropertyRequest, PropertyInputPair
        from osw.solvers.coolprop.property_adapter import calculate_properties

        request = CoolPropPropertyRequest(
            fluid=args.fluid,
            input_pair=PropertyInputPair("T", args.T, "P", args.P, "K", "Pa"),
            output_properties=_csv_items(args.outputs),
        )
        result = calculate_properties(request)
        _print_coolprop_property_result(result)
        return _chm_status_exit_code(result.status)

    if args.command == "coolprop-sweep":
        import json

        from osw.solvers.coolprop.model import CoolPropSweepRequest
        from osw.solvers.coolprop.property_adapter import sweep_properties
        from osw.solvers.coolprop.results import coolprop_sweep_to_result_dataset

        fixed_variable = "P" if args.sweep == "T" else "T"
        fixed_value = args.P if args.sweep == "T" else args.T
        if fixed_value is None:
            print(f"Fixed {fixed_variable} is required for a {args.sweep} sweep.", file=sys.stderr)
            return 1
        request = CoolPropSweepRequest(
            fluid=args.fluid,
            sweep_variable=args.sweep,
            sweep_values=_linspace(args.start, args.stop, args.count),
            sweep_unit="K" if args.sweep == "T" else "Pa",
            fixed_variable=fixed_variable,
            fixed_value=fixed_value,
            fixed_unit="Pa" if fixed_variable == "P" else "K",
            output_properties=_csv_items(args.outputs),
        )
        result = sweep_properties(request)
        _print_coolprop_sweep_result(result)
        if result.status in {"ok", "warning"}:
            output = Path(args.out)
            output.parent.mkdir(parents=True, exist_ok=True)
            dataset = coolprop_sweep_to_result_dataset(result)
            output.write_text(
                json.dumps(dataset.to_dict(), indent=2, sort_keys=True),
                encoding="utf-8",
            )
            print(f"Wrote CHM ResultDataset JSON: {output}")
        return _chm_status_exit_code(result.status)

    if args.command == "cantera-check":
        from osw.solvers.cantera.reactor_adapter import cantera_available

        available = cantera_available()
        print("Cantera")
        print(f"Status: {'available' if available else 'missing'}")
        if not available:
            print(
                "Cantera is not installed. Install the CHM optional extra or install "
                "Cantera to run reactor calculations.",
                file=sys.stderr,
            )
        return 0 if available else 1

    if args.command == "cantera-reactor":
        import json

        from osw.solvers.cantera.model import CanteraMixtureSpec, CanteraReactorRequest
        from osw.solvers.cantera.reactor_adapter import run_zero_d_reactor
        from osw.solvers.cantera.results import cantera_result_to_result_dataset

        request = CanteraReactorRequest(
            mixture=CanteraMixtureSpec(
                mechanism=args.mechanism,
                phase_name=args.phase_name,
                composition=args.composition,
                temperature=args.T,
                pressure=args.P,
            ),
            end_time=args.end_time,
            time_step=args.time_step,
            tracked_species=_csv_items(args.tracked_species),
        )
        result = run_zero_d_reactor(request)
        _print_cantera_reactor_result(result)
        if result.status in {"ok", "warning"}:
            output = Path(args.out)
            output.parent.mkdir(parents=True, exist_ok=True)
            dataset = cantera_result_to_result_dataset(result)
            output.write_text(
                json.dumps(dataset.to_dict(), indent=2, sort_keys=True),
                encoding="utf-8",
            )
            print(f"Wrote CHM ResultDataset JSON: {output}")
        return _chm_status_exit_code(result.status)

    if args.command == "chm-result-inspect":
        import json

        dataset = _load_chm_result_dataset_source(Path(args.path))
        if args.json:
            print(json.dumps(dataset.to_dict(), indent=2, sort_keys=True))
        else:
            _print_result_dataset_summary(dataset)
        return 0

    if args.command == "result-dataset-inspect":
        dataset = _load_result_dataset_source(Path(args.path))
        if args.json:
            import json

            print(json.dumps(dataset.to_dict(), indent=2, sort_keys=True))
        else:
            _print_result_dataset_summary(dataset)
        return 0

    if args.command == "result-catalog-inspect":
        import json

        from osw.core.result_dataset import ResultCatalog

        payload = json.loads(Path(args.path).read_text(encoding="utf-8"))
        catalog = ResultCatalog.from_dict(payload)
        if args.json:
            print(json.dumps(catalog.to_dict(), indent=2, sort_keys=True))
        else:
            _print_result_catalog_summary(catalog)
        return 0

    if args.command == "result-catalog-from-project":
        from osw.core.project_io import load_project
        from osw.core.validation import ProjectSchemaError
        from osw.post.result_view_model import result_catalog_from_project

        try:
            project = load_project(Path(args.project))
        except ProjectSchemaError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        catalog = result_catalog_from_project(project)
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        import json

        output.write_text(json.dumps(catalog.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        print(f"Wrote ResultCatalog JSON: {output}")
        _print_result_catalog_summary(catalog)
        return 0

    if args.command == "result-dataset-export-json":
        import json

        dataset = _load_result_dataset_source(Path(args.input))
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(dataset.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        print(f"Wrote ResultDataset JSON: {output}")
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

    if args.command == "mat-info":
        from osw.scripts.mscript.mat_model import MatReadStatus
        from osw.scripts.mscript.mat_reader import read_mat_file

        result = read_mat_file(Path(args.path))
        if args.json:
            import json

            print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        elif result.ok:
            _print_mat_summary(result)
            if result.diagnostics.messages:
                print(result.diagnostics.summary(), file=sys.stderr)
        else:
            print(result.diagnostics.summary(), file=sys.stderr)
        if result.ok:
            return 0
        return 2 if result.status == MatReadStatus.DEPENDENCY_MISSING.value else 1

    if args.command == "mat-vars":
        from osw.scripts.mscript.mat_model import MatReadStatus
        from osw.scripts.mscript.mat_reader import read_mat_file

        result = read_mat_file(Path(args.path))
        if args.json:
            import json

            print(
                json.dumps(
                    {
                        "status": result.status,
                        "variables": list(result.variable_names),
                        "diagnostics": result.diagnostics.to_dict(),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        elif result.ok:
            for name in result.variable_names:
                print(name)
        else:
            print(result.diagnostics.summary(), file=sys.stderr)
        if result.ok:
            return 0
        return 2 if result.status == MatReadStatus.DEPENDENCY_MISSING.value else 1

    if args.command == "mat-export-csv":
        from osw.scripts.mscript.mat_model import MatReadStatus
        from osw.scripts.mscript.mat_reader import export_variable_to_csv

        result = export_variable_to_csv(Path(args.path), args.variable, Path(args.out))
        if not result.ok:
            print(result.diagnostics.summary(), file=sys.stderr)
            return 2 if result.status == MatReadStatus.DEPENDENCY_MISSING.value else 1
        print(f"Wrote MAT variable CSV: {result.output_path}")
        if result.diagnostics.messages:
            print(result.diagnostics.summary(), file=sys.stderr)
        return 0

    if args.command == "curve-from-csv":
        from osw.core.boundary_curve import (
            BoundaryCurveError,
            boundary_curve_from_csv,
            save_boundary_curve_json,
        )

        try:
            curve = boundary_curve_from_csv(
                Path(args.path),
                args.x_column,
                args.y_column,
                x_unit=args.x_unit,
                y_unit=args.y_unit,
                kind=args.kind,
            )
        except BoundaryCurveError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        save_boundary_curve_json(curve, Path(args.out))
        _print_boundary_curve(curve)
        print(f"Wrote BoundaryCurve JSON: {args.out}")
        return 0

    if args.command == "curve-from-mat":
        from osw.core.boundary_curve import BoundaryCurveError, save_boundary_curve_json
        from osw.scripts.mscript.boundary_curve_bridge import boundary_curve_from_mat_summary
        from osw.scripts.mscript.mat_model import MatReadStatus
        from osw.scripts.mscript.mat_reader import read_mat_file

        result = read_mat_file(Path(args.path), variable_names=(args.x, args.y))
        if not result.ok:
            print(result.diagnostics.summary(), file=sys.stderr)
            return 2 if result.status == MatReadStatus.DEPENDENCY_MISSING.value else 1
        try:
            curve = boundary_curve_from_mat_summary(
                result,
                args.x,
                args.y,
                x_unit=args.x_unit,
                y_unit=args.y_unit,
                kind=args.kind,
            )
        except BoundaryCurveError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        save_boundary_curve_json(curve, Path(args.out))
        _print_boundary_curve(curve)
        print(f"Wrote BoundaryCurve JSON: {args.out}")
        return 0

    if args.command == "curve-inspect":
        from osw.core.boundary_curve import load_boundary_curve_json

        curve = load_boundary_curve_json(Path(args.path))
        if args.json:
            import json

            print(json.dumps(curve.to_dict(), indent=2, sort_keys=True))
        else:
            _print_boundary_curve(curve)
            report = curve.validate()
            if report.messages:
                print(report.friendly_summary(), file=sys.stderr)
        return 1 if curve.validate().has_errors else 0

    if args.command == "curve-export-csv":
        from osw.core.boundary_curve import export_boundary_curve_csv, load_boundary_curve_json

        curve = load_boundary_curve_json(Path(args.path))
        output_path = export_boundary_curve_csv(curve, Path(args.out))
        print(f"Wrote BoundaryCurve CSV: {output_path}")
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

    if args.command == "report-export":
        from osw.core.project_io import load_project
        from osw.core.validation import ProjectSchemaError
        from osw.post.report_generator import build_report
        from osw.post.report_model import ReportBuildRequest

        try:
            project = load_project(Path(args.project))
        except ProjectSchemaError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        result = build_report(
            ReportBuildRequest(
                project=project,
                output_path=Path(args.out),
                format=args.format,
            )
        )
        print(f"Report status: {result.status}")
        print(f"Wrote report: {result.output_path}")
        if result.diagnostics.messages:
            print(result.diagnostics.summary(), file=sys.stderr)
        return 1 if result.diagnostics.has_errors else 0

    if args.command == "report-summary":
        from osw.core.project_io import load_project
        from osw.core.validation import ProjectSchemaError
        from osw.post.report_sections import build_report_summary

        try:
            project = load_project(Path(args.project))
        except ProjectSchemaError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        summary = build_report_summary(project)
        if args.json:
            import json

            print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
        else:
            _print_report_summary(summary)
        return 0

    if args.command == "report-export-demo":
        from osw.core.demo_project import create_heatsink_flow_demo_project
        from osw.post.report_generator import build_report
        from osw.post.report_model import ReportBuildRequest

        result = build_report(
            ReportBuildRequest(
                project=create_heatsink_flow_demo_project(),
                output_path=Path(args.out),
                format=args.format,
            )
        )
        print(f"Report status: {result.status}")
        print(f"Wrote report: {result.output_path}")
        if result.diagnostics.messages:
            print(result.diagnostics.summary(), file=sys.stderr)
        return 1 if result.diagnostics.has_errors else 0

    parser.print_help(sys.stdout)
    return 0


def _gmsh_request_from_args(
    args: argparse.Namespace,
    *,
    output_dir: Path,
    output_name: str | None = None,
    convert_to_vtu: bool = False,
    timeout_seconds: float = 30.0,
) -> object:
    from osw.mesh.gmsh_model import (
        GmshGeometryKind,
        GmshGeometrySpec,
        GmshMeshDimension,
        GmshMeshRequest,
        GmshMeshSizeField,
    )

    kind = GmshGeometryKind(args.kind)
    if kind is GmshGeometryKind.BOX:
        parameters = {"length": args.length, "width": args.width, "height": args.height}
        default_dimension = GmshMeshDimension.DIM3
    elif kind is GmshGeometryKind.RECTANGLE:
        parameters = {"width": args.width, "height": args.height}
        default_dimension = GmshMeshDimension.DIM2
    elif kind is GmshGeometryKind.CYLINDER:
        parameters = {"radius": args.radius, "height": args.height}
        default_dimension = GmshMeshDimension.DIM3
    elif kind is GmshGeometryKind.SPHERE:
        parameters = {"radius": args.radius}
        default_dimension = GmshMeshDimension.DIM3
    else:
        center = None
        if args.center_x is not None and args.center_y is not None:
            center = (args.center_x, args.center_y)
        parameters = {
            "width": args.width,
            "height": args.height,
            "hole_radius": args.hole_radius,
        }
        if center is not None:
            parameters["center"] = center
        default_dimension = GmshMeshDimension.DIM2
    dimension = args.dimension or default_dimension
    resolved_output_name = output_name or Path(getattr(args, "out", "gmsh_mesh.geo")).stem
    return GmshMeshRequest(
        geometry=GmshGeometrySpec(
            kind,
            parameters,
            geometry_id=f"{kind.value}_primitive",
            units=args.units,
        ),
        mesh_dimension=dimension,
        mesh_size=GmshMeshSizeField(global_size=args.mesh_size),
        output_dir=output_dir,
        output_name=resolved_output_name,
        convert_to_vtu=convert_to_vtu,
        timeout_seconds=timeout_seconds,
    )


def _print_gmsh_result(result: object) -> None:
    status = getattr(getattr(result, "status", ""), "value", getattr(result, "status", ""))
    print(f"Gmsh mesh status: {status}")
    geo_path = getattr(result, "geo_path", None)
    msh_path = getattr(result, "msh_path", None)
    converted = getattr(result, "converted_mesh_path", None)
    if geo_path:
        print(f"Geo: {geo_path}")
    if msh_path:
        print(f"MSH: {msh_path}")
    if converted:
        print(f"Converted: {converted}")
    mesh_info = getattr(result, "mesh_info", None)
    if mesh_info is not None:
        print(f"Nodes: {getattr(mesh_info, 'node_count', 0)}")
        print(f"Elements: {getattr(mesh_info, 'element_count', 0)}")
    diagnostics = getattr(result, "diagnostics", None)
    if diagnostics is not None and getattr(diagnostics, "messages", ()):
        print(diagnostics.summary(), file=sys.stderr)


def _print_calculix_diagnostics(
    diagnostics: Sequence[object],
    *,
    stream: object = sys.stderr,
) -> None:
    for item in diagnostics:
        if isinstance(item, dict):
            severity = str(item.get("severity", "")).upper()
            path = str(item.get("path", ""))
            message = str(item.get("message", ""))
            print(f"{severity} {path}: {message}", file=stream)


def _print_calculix_run_result(result: object) -> None:
    status = getattr(getattr(result, "status", ""), "value", getattr(result, "status", ""))
    print(f"CalculiX run status: {status}")
    print(f"Case directory: {getattr(result, 'case_dir', '')}")
    print(f"Job name: {getattr(result, 'job_name', '')}")
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
    artifacts = getattr(result, "artifacts", ()) or ()
    if artifacts:
        print("Artifacts:")
        for artifact in artifacts:
            role = getattr(artifact, "role", getattr(artifact, "kind", "artifact"))
            print(f"  - {role}: {getattr(artifact, 'path', '')}")
    diagnostics = getattr(result, "diagnostics", None)
    if diagnostics is not None and getattr(diagnostics, "messages", ()):
        print(diagnostics.summary(), file=sys.stderr)


def _load_calculix_parsed_results_source(path: Path) -> object:
    from osw.solvers.calculix.result_parser import (
        parse_calculix_case_directory,
        parse_calculix_results,
        parse_calculix_run_artifacts,
    )
    from osw.solvers.calculix.results import CalculiXParsedResults
    from osw.solvers.calculix.runner import CalculiXRunResult

    source = path.expanduser()
    if source.is_dir():
        return parse_calculix_case_directory(source)
    if source.suffix.lower() == ".json":
        import json

        payload = json.loads(source.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "input_deck_path" in payload:
            return parse_calculix_run_artifacts(CalculiXRunResult.from_dict(payload))
        return CalculiXParsedResults.from_dict(payload)
    if source.suffix.lower() == ".dat":
        return parse_calculix_results(dat_path=source)
    if source.suffix.lower() == ".sta":
        return parse_calculix_results(sta_path=source)
    if source.suffix.lower() == ".frd":
        return parse_calculix_results(frd_path=source)
    return parse_calculix_case_directory(source)


def _print_calculix_parsed_results(parsed: object) -> None:
    status = getattr(getattr(parsed, "status", ""), "value", getattr(parsed, "status", ""))
    print(f"CalculiX result status: {status}")
    print(f"Job name: {getattr(parsed, 'job_name', '')}")
    displacement = getattr(parsed, "displacement_summary", None)
    stress = getattr(parsed, "stress_summary", None)
    if displacement is not None and getattr(displacement, "max_magnitude", None) is not None:
        node = getattr(displacement, "max_node_id", None)
        max_magnitude = displacement.max_magnitude
        unit = getattr(displacement, "unit", "")
        print(
            "Max displacement: "
            f"{max_magnitude} {unit}"
            f"{f' at node {node}' if node is not None else ''}"
        )
    else:
        print("Max displacement: not available")
    if stress is not None and getattr(stress, "max_von_mises", None) is not None:
        element = getattr(stress, "max_element_id", None)
        max_von_mises = stress.max_von_mises
        unit = getattr(stress, "unit", "")
        print(
            "Max von Mises stress: "
            f"{max_von_mises} {unit}"
            f"{f' at element {element}' if element is not None else ''}"
        )
    else:
        print("Max von Mises stress: not available")
    status_summary = getattr(parsed, "status_summary", None)
    if status_summary is not None:
        print(f"Completed: {getattr(status_summary, 'completed', None)}")
        print(f"Increments: {getattr(status_summary, 'increments', 0)}")
    artifacts = getattr(parsed, "artifacts", ()) or ()
    if artifacts:
        print("Artifacts:")
        for artifact in artifacts:
            print(f"  - {getattr(artifact, 'role', 'artifact')}: {getattr(artifact, 'path', '')}")
    diagnostics = getattr(parsed, "diagnostics", None)
    if diagnostics is not None and getattr(diagnostics, "messages", ()):
        print(diagnostics.summary(), file=sys.stderr)


def _print_openfoam_run_result(result: object) -> None:
    status = getattr(getattr(result, "status", ""), "value", getattr(result, "status", ""))
    print(f"OpenFOAM run status: {status}")
    print(f"Case directory: {getattr(result, 'case_dir', '')}")
    print(f"Solver: {getattr(result, 'solver', '')}")
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
    summary = getattr(result, "residual_summary", None)
    if summary is not None:
        _print_openfoam_residual_summary(summary)
    artifacts = getattr(result, "artifacts", ()) or ()
    if artifacts:
        print("Artifacts:")
        for artifact in artifacts:
            role = getattr(artifact, "role", getattr(artifact, "kind", "artifact"))
            print(f"  - {role}: {getattr(artifact, 'path', '')}")
    diagnostics = getattr(result, "diagnostics", None)
    if diagnostics is not None and getattr(diagnostics, "messages", ()):
        print(diagnostics.summary(), file=sys.stderr)


def _print_openfoam_residual_summary(summary: object) -> None:
    print("OpenFOAM residual summary")
    print(f"Iterations: {getattr(summary, 'iteration_count', 0)}")
    final_residuals = dict(getattr(summary, "final_residuals", {}) or {})
    if final_residuals:
        print("Final residuals:")
        for field, value in sorted(final_residuals.items()):
            print(f"  - {field}: {value:.12g}")
    else:
        print("Final residuals: not available")
    diagnostics = getattr(summary, "diagnostics", None)
    if diagnostics is not None and getattr(diagnostics, "messages", ()):
        print(diagnostics.summary(), file=sys.stderr)


def _print_coolprop_property_result(result: object) -> None:
    print(f"CoolProp property status: {getattr(result, 'status', '')}")
    request = getattr(result, "request", None)
    if request is not None:
        print(f"Fluid: {getattr(request, 'fluid', '')}")
    for value in getattr(result, "values", ()) or ():
        print(
            f"{getattr(value, 'name', '')}: "
            f"{getattr(value, 'value', '')} {getattr(value, 'unit', '')}".rstrip()
        )
    diagnostics = getattr(result, "diagnostics", None)
    if diagnostics is not None and getattr(diagnostics, "messages", ()):
        print(diagnostics.summary(), file=sys.stderr)


def _print_coolprop_sweep_result(result: object) -> None:
    print(f"CoolProp sweep status: {getattr(result, 'status', '')}")
    print(f"Rows: {len(getattr(result, 'rows', ()) or ())}")
    for name, values in dict(getattr(result, "series", {}) or {}).items():
        if values:
            print(f"{name}: first={values[0]:.12g}, last={values[-1]:.12g}")
    diagnostics = getattr(result, "diagnostics", None)
    if diagnostics is not None and getattr(diagnostics, "messages", ()):
        print(diagnostics.summary(), file=sys.stderr)


def _print_cantera_reactor_result(result: object) -> None:
    print(f"Cantera reactor status: {getattr(result, 'status', '')}")
    print(f"Samples: {len(getattr(result, 'times', ()) or ())}")
    temperatures = tuple(getattr(result, "temperature_series", ()) or ())
    if temperatures:
        print(f"Final temperature: {temperatures[-1]:.12g} K")
        print(f"Max temperature: {max(temperatures):.12g} K")
    for species, values in dict(getattr(result, "species_series", {}) or {}).items():
        if values:
            print(f"Final {species}: {values[-1]:.12g}")
    diagnostics = getattr(result, "diagnostics", None)
    if diagnostics is not None and getattr(diagnostics, "messages", ()):
        print(diagnostics.summary(), file=sys.stderr)


def _load_chm_result_dataset_source(path: Path) -> object:
    import json

    from osw.core.result_dataset import ResultDataset
    from osw.solvers.cantera.model import CanteraReactorResult
    from osw.solvers.cantera.results import cantera_result_to_result_dataset
    from osw.solvers.coolprop.model import CoolPropPropertyResult, CoolPropSweepResult
    from osw.solvers.coolprop.results import (
        coolprop_result_to_result_dataset,
        coolprop_sweep_to_result_dataset,
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        msg = "CHM result JSON must contain an object."
        raise SystemExit(msg)
    if "fields" in payload or "summaries" in payload:
        return ResultDataset.from_dict(payload)
    request = payload.get("request")
    if "values" in payload and isinstance(request, dict):
        return coolprop_result_to_result_dataset(CoolPropPropertyResult.from_dict(payload))
    if "series" in payload and isinstance(request, dict):
        return coolprop_sweep_to_result_dataset(CoolPropSweepResult.from_dict(payload))
    if "temperature_series" in payload and isinstance(request, dict):
        return cantera_result_to_result_dataset(CanteraReactorResult.from_dict(payload))
    return _load_result_dataset_source(path)


def _chm_status_exit_code(status: object) -> int:
    text = str(status)
    if text in {"ok", "warning"}:
        return 0
    if text == "dependency_missing":
        return 2
    return 1


def _csv_items(text: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in str(text).split(",") if item.strip())


def _linspace(start: float, stop: float, count: int) -> tuple[float, ...]:
    if count <= 0:
        return ()
    if count == 1:
        return (float(start),)
    step = (float(stop) - float(start)) / float(count - 1)
    return tuple(float(start) + step * index for index in range(count))


def _load_result_dataset_source(path: Path) -> object:
    import json

    from osw.core.boundary_curve import BoundaryCurve
    from osw.core.result_dataset import ResultCatalog, ResultDataset
    from osw.post.result_view_model import (
        boundary_curve_to_view_dataset,
        figure_dataset_to_view_dataset,
        mat_summary_to_view_dataset,
    )
    from osw.scripts.mscript.figure_dataset import FigureDataset
    from osw.scripts.mscript.mat_model import MatFileSummary, MatReadResult

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        msg = f"Could not read result dataset JSON: {path}"
        raise SystemExit(msg) from exc
    except json.JSONDecodeError as exc:
        msg = f"Invalid JSON result dataset: {path}: {exc}"
        raise SystemExit(msg) from exc
    if not isinstance(payload, dict):
        msg = "Result dataset JSON must contain an object."
        raise SystemExit(msg)
    if "datasets" in payload:
        selected = ResultCatalog.from_dict(payload).selected_dataset()
        if selected is None:
            msg = "ResultCatalog does not contain datasets."
            raise SystemExit(msg)
        return selected
    if "fields" in payload or "summaries" in payload:
        return ResultDataset.from_dict(payload)
    if "figures" in payload and "workspace_variables" in payload:
        return figure_dataset_to_view_dataset(FigureDataset.from_dict(payload))
    if "curve_id" in payload:
        return boundary_curve_to_view_dataset(BoundaryCurve.from_dict(payload))
    if "summary" in payload:
        return mat_summary_to_view_dataset(MatReadResult.from_dict(payload))
    if "variables" in payload and "version" in payload:
        return mat_summary_to_view_dataset(MatFileSummary.from_dict(payload))
    return ResultDataset.from_dict(payload)


def _print_result_dataset_summary(dataset: object) -> None:
    from osw.post.result_view_model import result_dataset_summary, result_dataset_to_view_model

    summary = result_dataset_summary(dataset)
    view_model = result_dataset_to_view_model(dataset)
    print(f"ResultDataset: {summary.dataset_id}")
    print(f"Title: {summary.title}")
    print(f"Kind: {summary.kind}")
    print(f"Source: {summary.source or 'Not recorded'}")
    print(f"Scalars: {summary.scalar_count}")
    for scalar in view_model.scalars:
        print(f"  - {scalar.name}: {scalar.value} {scalar.unit}".rstrip())
    print(f"Series: {summary.series_count}")
    for series in view_model.series:
        print(f"  - {series.name}: {len(series.y_values)} point(s)")
    print(f"Tables: {summary.table_count}")
    print(f"Figures: {summary.figure_count}")
    print(f"Artifacts: {summary.artifact_count}")
    for artifact in view_model.artifacts:
        state = "exists" if artifact.exists else "missing"
        print(f"  - {artifact.role}: {artifact.path} [{state}]")
    if view_model.diagnostics:
        print("Diagnostics:", file=sys.stderr)
        for diagnostic in view_model.diagnostics:
            print(f"  - {diagnostic}", file=sys.stderr)


def _print_result_catalog_summary(catalog: object) -> None:
    from osw.post.result_view_model import result_dataset_summary

    datasets = tuple(getattr(catalog, "datasets", ()) or ())
    print(f"ResultCatalog: {getattr(catalog, 'catalog_id', '')}")
    print(f"Project: {getattr(catalog, 'project_name', '') or 'Not recorded'}")
    print(f"Datasets: {len(datasets)}")
    selected = getattr(catalog, "selected_dataset_id", "")
    if selected:
        print(f"Selected: {selected}")
    for dataset in datasets:
        summary = result_dataset_summary(dataset)
        print(
            f"- {summary.dataset_id}: {summary.title} "
            f"({summary.kind}, {summary.scalar_count} scalar(s), "
            f"{summary.series_count} series)"
        )


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


def _print_mat_summary(result: object) -> None:
    summary = getattr(result, "summary", None)
    print(f"MAT file: {getattr(result, 'source_path', '')}")
    print(f"Version: {getattr(summary, 'version', 'unknown')}")
    variables = tuple(getattr(summary, "variables", ()))
    print(f"Variables: {len(variables)}")
    for variable in variables:
        shape = "x".join(str(item) for item in getattr(variable, "shape", ())) or "scalar"
        print(
            f"- {getattr(variable, 'name', '')}: "
            f"{getattr(variable, 'kind', '')} "
            f"{shape} "
            f"{getattr(variable, 'dtype', '')}"
        )


def _print_boundary_curve(curve: object) -> None:
    print(f"BoundaryCurve: {getattr(curve, 'name', '')}")
    print(f"ID: {getattr(curve, 'curve_id', '')}")
    print(f"Kind: {getattr(curve, 'kind', '')}")
    print(f"Points: {getattr(curve, 'point_count', 0)}")
    print(f"X unit: {getattr(curve, 'x_unit', '') or '<missing>'}")
    print(f"Y unit: {getattr(curve, 'y_unit', '') or '<missing>'}")
    print(f"Interpolation: {getattr(curve, 'interpolation', '')}")
    source = getattr(curve, "source", None)
    if source is not None:
        print(
            "Source: "
            f"{getattr(source, 'source_type', '')} "
            f"{getattr(source, 'source_file', '')}"
        )


def _print_report_summary(summary: object) -> None:
    print(f"Report: {getattr(summary, 'title', '')}")
    print(f"Project: {getattr(summary, 'project_name', '')}")
    print(f"Run label: {getattr(summary, 'run_label', '') or 'Not recorded'}")
    print(f"Sections: {len(getattr(summary, 'sections', ())) }")
    for section in getattr(summary, "sections", ()):
        print(f"- {getattr(section, 'title', '')}")
    print(f"Figures: {len(getattr(summary, 'figures', ())) }")
    print(f"Warnings: {len(getattr(summary, 'warnings', ())) }")


if __name__ == "__main__":
    raise SystemExit(main())
