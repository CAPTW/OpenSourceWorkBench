"""Minimal command line interface for OSW bootstrap checks."""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from osw import __version__
from osw.cli.optional_solver_manifest_export_summary import (
    OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_COMMAND,
    add_optional_solver_plugin_manifest_export_summary_parser,
    run_optional_solver_plugin_manifest_export_summary_cli,
)
from osw.cli.optional_solver_manifest_persistence import (
    OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_COMMAND,
    add_optional_solver_plugin_manifest_persistence_parser,
    run_optional_solver_plugin_manifest_persistence_cli,
)
from osw.cli.optional_solver_manifest_reload import (
    OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_COMMAND,
    add_optional_solver_plugin_manifest_reload_parser,
    run_optional_solver_plugin_manifest_reload_cli,
)
from osw.core.executables import ExecutablePathRegistry
from osw.experimental.optional_solvers import (
    OptionalSolverDiscoveryOptions,
    OptionalSolverDiscoveryReport,
    OptionalSolverManifest,
    OptionalSolverPathRedactionMode,
    OptionalSolverPluginManifestDocument,
    OptionalSolverPluginManifestLoaderOptions,
    OptionalSolverPluginManifestLoadReport,
    builtin_optional_solver_manifests,
    discover_optional_solver_manifests,
    get_builtin_optional_solver_manifest,
    load_optional_solver_plugin_manifest_documents,
    load_optional_solver_plugin_manifest_json,
    optional_solver_discovery_report_to_dict,
)
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
OPTIONAL_SOLVER_PLUGIN_MANIFEST_PREVIEW_COMMAND = (
    "optional-solver-plugin-manifest-preview"
)
OPTIONAL_SOLVER_PLUGIN_MANIFEST_LOAD_FAILURE_CODES = {
    "OSPL_NETWORK_SOURCE_UNSUPPORTED",
    "OSPL_DIRECTORY_SCAN_FORBIDDEN",
    "OSPL_JSON_EXTENSION_REQUIRED",
    "OSPL_JSON_READ_FAILED",
    "OSPL_JSON_INVALID",
    "OSPL_JSON_OBJECT_REQUIRED",
}


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


def _optional_solver_manifest_summary(
    manifest: OptionalSolverManifest,
    *,
    include_requirements: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "stack_id": manifest.stack_id,
        "display_name": manifest.display_name,
        "related_issue": manifest.related_issue,
        "support_status": manifest.support_status.value,
    }
    if include_requirements:
        payload["executable_requirements"] = [
            requirement.to_dict() for requirement in manifest.executable_requirements
        ]
        payload["python_package_requirements"] = [
            requirement.to_dict() for requirement in manifest.python_package_requirements
        ]
        payload["environment_variable_hints"] = list(manifest.environment_variable_hints)
    return payload


def _format_optional_solver_list_text(
    manifests: Sequence[OptionalSolverManifest],
    *,
    include_requirements: bool,
) -> str:
    lines = [
        "OSW optional solver stacks",
        "External solvers and optional science packages are not bundled.",
    ]
    for manifest in manifests:
        issue = f"#{manifest.related_issue}" if manifest.related_issue is not None else "none"
        lines.append(
            f"- {manifest.stack_id}: {manifest.display_name} "
            f"(issue {issue}, {manifest.support_status.value})"
        )
        if include_requirements:
            for requirement in manifest.executable_requirements:
                required = "required" if requirement.required else "optional"
                label = requirement.display_name or requirement.identifier
                lines.append(f"    executable: {requirement.identifier} ({label}, {required})")
            for requirement in manifest.python_package_requirements:
                required = "required" if requirement.required else "optional"
                label = requirement.display_name or requirement.identifier
                lines.append(f"    python package: {requirement.identifier} ({label}, {required})")
            for name in manifest.environment_variable_hints:
                lines.append(f"    environment hint: {name} (value redacted)")
    return "\n".join(lines)


def _select_optional_solver_manifests(
    stack_ids: Sequence[str] | None,
) -> tuple[OptionalSolverManifest, ...]:
    if not stack_ids:
        return builtin_optional_solver_manifests()
    manifests: list[OptionalSolverManifest] = []
    for stack_id in stack_ids:
        manifests.append(get_builtin_optional_solver_manifest(stack_id))
    return tuple(manifests)


def _optional_solver_doctor_report(
    manifests: Sequence[OptionalSolverManifest],
    *,
    show_full_paths: bool,
) -> OptionalSolverDiscoveryReport:
    path_redaction = (
        OptionalSolverPathRedactionMode.FULL
        if show_full_paths
        else OptionalSolverPathRedactionMode.REDACTED
    )
    return discover_optional_solver_manifests(
        manifests,
        options=OptionalSolverDiscoveryOptions(
            path_redaction=path_redaction,
            include_environment_values=False,
        ),
    )


def _format_optional_solver_doctor_text(
    report: OptionalSolverDiscoveryReport,
    *,
    include_diagnostics: bool,
) -> str:
    lines = [
        "OSW optional solver doctor",
        "Passive discovery only: no solver commands, smoke checks, or installs run.",
        "Paths are redacted by default unless full paths were explicitly requested.",
        "Environment values are always redacted in this preview.",
    ]
    for stack in report.stacks:
        issue = f"#{stack.related_issue}" if stack.related_issue is not None else "none"
        lines.append(f"- {stack.stack_id}: {stack.health_state.value} (issue {issue})")
        for executable in stack.executables:
            detail = executable.path or executable.redacted_path or "missing"
            lines.append(
                f"    executable {executable.identifier}: "
                f"{_found_text(executable.found)} ({detail})"
            )
        for package in stack.python_packages:
            version = f", version {package.version}" if package.version else ""
            lines.append(
                f"    python package {package.identifier}: {_found_text(package.found)}{version}"
            )
        for hint in stack.environment_hints:
            value = hint.redacted_value or ("present" if hint.present else "missing")
            lines.append(f"    environment hint {hint.name}: {value}")
        if include_diagnostics:
            for diagnostic in stack.diagnostics:
                lines.append(
                    f"    {diagnostic.severity.value}: {diagnostic.code}: {diagnostic.message}"
                )
    lines.append("Missing or discovered passive evidence is not validation-pass evidence.")
    lines.append("Issue closure requires separate validation and closure-review gates.")
    return "\n".join(lines)


def _format_optional_solver_explain_text(manifest: OptionalSolverManifest) -> str:
    issue = f"#{manifest.related_issue}" if manifest.related_issue is not None else "none"
    lines = [
        f"{manifest.display_name} ({manifest.stack_id})",
        f"related issue: {issue}",
        f"support status: {manifest.support_status.value}",
        f"non-bundled disclaimer: {manifest.non_bundled_disclaimer}",
        "capabilities:",
    ]
    for capability in manifest.capabilities:
        description = f" - {capability.description}" if capability.description else ""
        lines.append(f"  - {capability.capability_id}{description}")
    lines.append("requirements:")
    for requirement in manifest.executable_requirements:
        required = "required" if requirement.required else "optional"
        lines.append(f"  - executable {requirement.identifier} ({required})")
    for requirement in manifest.python_package_requirements:
        required = "required" if requirement.required else "optional"
        lines.append(f"  - python package {requirement.identifier} ({required})")
    for name in manifest.environment_variable_hints:
        lines.append(f"  - environment hint {name} (value redacted)")
    lines.append("prepared-machine notes:")
    for note in manifest.prepared_machine_notes:
        lines.append(f"  - {note}")
    lines.append("safety notes:")
    for note in manifest.safety_notes:
        lines.append(f"  - {note}")
    lines.append(
        "No solver execution, active smoke validation, dependency installation, "
        "or issue mutation is performed."
    )
    return "\n".join(lines)


def _optional_solver_explain_payload(manifest: OptionalSolverManifest) -> dict[str, object]:
    return {
        **manifest.to_dict(),
        "issue_reference": f"#{manifest.related_issue}" if manifest.related_issue else "",
        "passive_only": True,
        "no_solver_execution": True,
        "no_dependency_installation": True,
    }


def _optional_solver_plugin_manifest_preview_options(
    *,
    include_builtins: bool,
) -> OptionalSolverPluginManifestLoaderOptions:
    builtin_stack_ids = (
        tuple(manifest.stack_id for manifest in builtin_optional_solver_manifests())
        if include_builtins
        else ()
    )
    return OptionalSolverPluginManifestLoaderOptions(builtin_stack_ids=builtin_stack_ids)


def _optional_solver_plugin_manifest_preview_report(
    manifest_paths: Sequence[str],
    *,
    include_builtins: bool,
) -> OptionalSolverPluginManifestLoadReport:
    options = _optional_solver_plugin_manifest_preview_options(
        include_builtins=include_builtins,
    )
    reports = [
        load_optional_solver_plugin_manifest_json(path, options=options)
        for path in manifest_paths
    ]
    accepted_documents = tuple(
        OptionalSolverPluginManifestDocument(
            manifest_data=loaded.manifest.to_dict(),
            source=loaded.source,
            schema_version=loaded.schema_version,
            document_ref=loaded.source.reference,
        )
        for report in reports
        for loaded in report.accepted_manifests
    )
    accepted_report = (
        load_optional_solver_plugin_manifest_documents(
            accepted_documents,
            options=options,
        )
        if accepted_documents
        else OptionalSolverPluginManifestLoadReport()
    )
    rejected_reports = tuple(report for report in reports if report.rejected_manifests)
    return OptionalSolverPluginManifestLoadReport(
        accepted_manifests=accepted_report.accepted_manifests,
        rejected_manifests=tuple(
            rejected
            for report in rejected_reports
            for rejected in report.rejected_manifests
        )
        + accepted_report.rejected_manifests,
        conflicts=tuple(conflict for report in rejected_reports for conflict in report.conflicts)
        + accepted_report.conflicts,
        diagnostics=tuple(
            diagnostic for report in rejected_reports for diagnostic in report.diagnostics
        )
        + accepted_report.diagnostics,
    )


def _optional_solver_plugin_manifest_policy_payload(
    *,
    include_builtins: bool,
) -> dict[str, object]:
    return {
        "data_only_loading": True,
        "explicit_json_files_only": True,
        "plugin_package_loading": False,
        "directory_scan": False,
        "network_fetch": False,
        "solver_execution": False,
        "dependency_installation": False,
        "issue_mutation": False,
        "release_mutation": False,
        "include_builtins": include_builtins,
        "plugin_manifest_presence_is_validation_evidence": False,
        "third_party_plugin_manifests_trusted_by_default": False,
        "trust_label_is_certification": False,
    }


def _optional_solver_plugin_manifest_preview_payload(
    report: OptionalSolverPluginManifestLoadReport,
    *,
    include_builtins: bool,
) -> dict[str, object]:
    payload = report.to_dict()
    payload["command"] = OPTIONAL_SOLVER_PLUGIN_MANIFEST_PREVIEW_COMMAND
    payload["accepted"] = payload["accepted_manifests"]
    payload["rejected"] = payload["rejected_manifests"]
    payload["policy"] = _optional_solver_plugin_manifest_policy_payload(
        include_builtins=include_builtins,
    )
    return payload


def _format_optional_solver_plugin_manifest_preview_text(
    report: OptionalSolverPluginManifestLoadReport,
    *,
    include_builtins: bool,
    include_diagnostics: bool,
    show_policy: bool,
) -> str:
    lines = [
        "OSW optional solver plugin manifest preview",
        "Data-only preview for explicitly supplied JSON manifest files.",
        f"accepted count: {len(report.accepted_manifests)}",
        f"rejected count: {len(report.rejected_manifests)}",
        f"conflict count: {len(report.conflicts)}",
        (
            "built-in conflict context: enabled"
            if include_builtins
            else "built-in conflict context: disabled"
        ),
        "Plugin manifest presence is not validation evidence.",
        "Third-party/plugin manifests are not trusted by default.",
    ]
    if show_policy:
        lines.extend(
            (
                "policy: explicit JSON files only",
                "policy: no plugin package loading, directory scan, or network fetch",
                "policy: no solver execution, dependency installation, or issue mutation",
            )
        )

    lines.append("accepted manifests:")
    if report.accepted_manifests:
        for loaded in report.accepted_manifests:
            lines.append(
                f"  - {loaded.stack_id}: {loaded.manifest.display_name} "
                f"(source {loaded.source.source_type.value}, "
                f"trust {loaded.source.trust_label.value})"
            )
    else:
        lines.append("  - none")

    lines.append("rejected manifests:")
    if report.rejected_manifests:
        for rejected in report.rejected_manifests:
            stack_id = rejected.stack_id or "(unknown)"
            lines.append(
                f"  - {stack_id}: source {rejected.source.source_type.value}, "
                f"trust {rejected.source.trust_label.value}"
            )
    else:
        lines.append("  - none")

    lines.append("conflicts:")
    if report.conflicts:
        for conflict in report.conflicts:
            lines.append(f"  - {conflict.stack_id}: {conflict.message}")
    else:
        lines.append("  - none")

    diagnostics = report.diagnostics if include_diagnostics else tuple(report.diagnostics)
    lines.append("diagnostics:")
    if diagnostics:
        for diagnostic in diagnostics:
            stack_id = f", stack {diagnostic.stack_id}" if diagnostic.stack_id else ""
            source = f", source {diagnostic.source_ref}" if diagnostic.source_ref else ""
            lines.append(
                f"  - {diagnostic.severity.value}/{diagnostic.category.value}: "
                f"{diagnostic.code}{stack_id}{source}: {diagnostic.message}"
            )
    else:
        lines.append("  - none")
    return "\n".join(lines)


def _optional_solver_plugin_manifest_preview_failed(
    report: OptionalSolverPluginManifestLoadReport,
) -> bool:
    return any(
        diagnostic.code in OPTIONAL_SOLVER_PLUGIN_MANIFEST_LOAD_FAILURE_CODES
        for diagnostic in report.diagnostics
    )


def _optional_solver_plugin_manifest_preview_has_strict_failures(
    report: OptionalSolverPluginManifestLoadReport,
) -> bool:
    return bool(report.rejected_manifests or report.conflicts)


def _found_text(found: bool) -> str:
    return "found" if found else "missing"


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
    optional_solver_list_parser = subparsers.add_parser(
        "optional-solver-list",
        help="List built-in optional solver stack manifests.",
    )
    optional_solver_list_parser.add_argument(
        "--format",
        default="text",
        choices=("text", "json"),
        help="Output format.",
    )
    optional_solver_list_parser.add_argument(
        "--include-requirements",
        action="store_true",
        help="Include declared executable, Python package, and environment requirements.",
    )
    optional_solver_doctor_parser = subparsers.add_parser(
        "optional-solver-doctor",
        help="Run passive optional solver discovery without executing solvers.",
    )
    optional_solver_doctor_parser.add_argument(
        "--stack",
        action="append",
        default=[],
        help="Built-in optional solver stack id to inspect. May be repeated.",
    )
    optional_solver_doctor_parser.add_argument(
        "--all",
        action="store_true",
        help="Inspect all built-in optional solver stacks.",
    )
    optional_solver_doctor_parser.add_argument(
        "--format",
        default="text",
        choices=("text", "json"),
        help="Output format.",
    )
    optional_solver_doctor_parser.add_argument(
        "--show-full-paths",
        action="store_true",
        help="Include full executable paths instead of redacted paths.",
    )
    optional_solver_doctor_parser.add_argument(
        "--include-diagnostics",
        action="store_true",
        help="Include passive discovery diagnostics in text output.",
    )
    optional_solver_explain_parser = subparsers.add_parser(
        "optional-solver-explain",
        help="Explain one built-in optional solver stack manifest.",
    )
    optional_solver_explain_parser.add_argument(
        "--stack",
        required=True,
        help="Built-in optional solver stack id to explain.",
    )
    optional_solver_explain_parser.add_argument(
        "--format",
        default="text",
        choices=("text", "json"),
        help="Output format.",
    )
    optional_solver_plugin_manifest_preview_parser = subparsers.add_parser(
        OPTIONAL_SOLVER_PLUGIN_MANIFEST_PREVIEW_COMMAND,
        help="Preview explicit optional solver plugin manifest JSON files.",
        description=(
            "Preview data-only optional solver plugin manifest loading for explicit "
            "JSON files. This command does not load plugin packages, scan directories, "
            "fetch network manifests, execute solvers, or install dependencies."
        ),
    )
    optional_solver_plugin_manifest_preview_parser.add_argument(
        "--manifest",
        action="append",
        default=[],
        help="Explicit optional solver plugin manifest JSON file. May be repeated.",
    )
    optional_solver_plugin_manifest_preview_parser.add_argument(
        "--format",
        default="text",
        choices=("text", "json"),
        help="Output format.",
    )
    optional_solver_plugin_manifest_preview_parser.add_argument(
        "--include-builtins",
        action="store_true",
        help="Use built-in optional solver stack ids as trusted conflict context.",
    )
    optional_solver_plugin_manifest_preview_parser.add_argument(
        "--strict",
        action="store_true",
        help="Return exit code 2 when manifests are rejected or conflicts are present.",
    )
    optional_solver_plugin_manifest_preview_parser.add_argument(
        "--include-diagnostics",
        action="store_true",
        help="Include loader diagnostics in text output.",
    )
    optional_solver_plugin_manifest_preview_parser.add_argument(
        "--show-policy",
        action="store_true",
        help="Include detailed safety policy disclaimers in text output.",
    )
    add_optional_solver_plugin_manifest_persistence_parser(subparsers)
    add_optional_solver_plugin_manifest_export_summary_parser(subparsers)
    add_optional_solver_plugin_manifest_reload_parser(subparsers)
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

    # New Plugin Hardening Commands:
    plugins_install_folder_parser = subparsers.add_parser(
        "plugins-install-folder",
        help="Install a local plugin folder safely into the managed root.",
    )
    plugins_install_folder_parser.add_argument("path", help="Local plugin folder path.")
    plugins_install_folder_parser.add_argument(
        "--install-root", help="Managed install root directory."
    )
    plugins_install_folder_parser.add_argument(
        "--allow-replace",
        action="store_true",
        help="Replace existing plugin if it exists.",
    )

    plugins_install_zip_parser = subparsers.add_parser(
        "plugins-install-zip",
        help="Install a local plugin zip archive safely into the managed root.",
    )
    plugins_install_zip_parser.add_argument("path", help="Local plugin zip archive path.")
    plugins_install_zip_parser.add_argument(
        "--install-root", help="Managed install root directory."
    )
    plugins_install_zip_parser.add_argument(
        "--allow-replace",
        action="store_true",
        help="Replace existing plugin if it exists.",
    )

    plugins_installed_parser = subparsers.add_parser(
        "plugins-installed",
        help="List installed plugin receipts from the managed install root.",
    )
    plugins_installed_parser.add_argument("--install-root", help="Managed install root directory.")
    plugins_installed_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    plugins_uninstall_parser = subparsers.add_parser(
        "plugins-uninstall",
        help="Uninstall a managed plugin by ID.",
    )
    plugins_uninstall_parser.add_argument("plugin_id", help="Plugin ID to uninstall.")
    plugins_uninstall_parser.add_argument("--install-root", help="Managed install root directory.")

    plugins_quarantine_parser = subparsers.add_parser(
        "plugins-quarantine-list",
        help="List quarantined / rejected plugins.",
    )
    plugins_quarantine_parser.add_argument("--install-root", help="Managed install root directory.")
    plugins_quarantine_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

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
    feaspec_calculix_preview_parser = subparsers.add_parser(
        "feaspec-calculix-export-preview",
        help="Preview FEASpec CalculiX export readiness without writing files.",
        description=(
            "Preview experimental FEASpec-to-CalculiX no-run export readiness. "
            "The command writes no files, creates no directories, performs no solver "
            "execution, and keeps issue #8 live validation separate."
        ),
    )
    feaspec_calculix_preview_parser.add_argument(
        "--feaspec",
        required=True,
        help="FEASpec JSON path to preview.",
    )
    feaspec_calculix_preview_parser.add_argument(
        "--target-solver",
        default="calculix",
        choices=("calculix",),
        help="Target solver for preview planning.",
    )
    feaspec_calculix_preview_parser.add_argument(
        "--format",
        default="text",
        choices=("text", "json"),
        help="Preview output format.",
    )
    feaspec_calculix_preview_parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 2 when preview diagnostics block export readiness.",
    )
    feaspec_calculix_preview_parser.add_argument(
        "--basename",
        default="feaspec_calculix_case",
        help="Planned export bundle basename used only for previewed filenames.",
    )
    feaspec_calculix_preview_parser.add_argument(
        "--planned-output-dir",
        default="",
        help="Planned output directory used only for previewed filenames.",
    )
    feaspec_calculix_write_parser = subparsers.add_parser(
        "feaspec-calculix-export-write",
        help="Write a FEASpec CalculiX no-run export bundle.",
        description=(
            "Write an experimental FEASpec-to-CalculiX no-run export bundle to an "
            "explicit output directory. The command performs no solver execution, "
            "does not validate installed ccx, and keeps issue #8 live validation separate."
        ),
    )
    feaspec_calculix_write_input = feaspec_calculix_write_parser.add_mutually_exclusive_group(
        required=True
    )
    feaspec_calculix_write_input.add_argument(
        "--feaspec",
        help="FEASpec JSON path to validate, bridge, plan, render, and export.",
    )
    feaspec_calculix_write_input.add_argument(
        "--case-plan",
        help=(
            "Experimental FEASpecCalculiXCasePlan JSON path for already reviewed, "
            "writer-ready no-run export."
        ),
    )
    feaspec_calculix_write_parser.add_argument(
        "--output-dir",
        required=True,
        help="Existing output directory for the bundle, unless --create-dir is supplied.",
    )
    feaspec_calculix_write_parser.add_argument(
        "--target-solver",
        default="calculix",
        choices=("calculix",),
        help="Target solver for no-run export.",
    )
    feaspec_calculix_write_parser.add_argument(
        "--format",
        default="text",
        choices=("text", "json"),
        help="Write command output format.",
    )
    feaspec_calculix_write_parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Preserve blocked export exit code 2; exported-with-warnings remains "
            "exit code 0 for this write boundary."
        ),
    )
    feaspec_calculix_write_parser.add_argument(
        "--basename",
        default="feaspec_calculix_case",
        help="Export bundle basename.",
    )
    feaspec_calculix_write_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite only the expected export bundle target files.",
    )
    feaspec_calculix_write_parser.add_argument(
        "--create-dir",
        action="store_true",
        help="Create the final output directory if its parent already exists.",
    )
    feaspec_calculix_run_parser = subparsers.add_parser(
        "feaspec-calculix-run-installed-only",
        help="Run or dry-run an installed-only CalculiX gate for a FEASpec export bundle.",
        description=(
            "Inspect a FEASpec CalculiX no-run export bundle and optionally run "
            "installed ccx in an isolated runtime directory. The default mode is "
            "dry-run: no files are written, no solver process is started, no solver "
            "is installed, and issue #8 live validation remains separate."
        ),
    )
    feaspec_calculix_run_parser.add_argument(
        "--export-dir",
        required=True,
        help="FEASpec CalculiX no-run export bundle directory.",
    )
    feaspec_calculix_run_parser.add_argument(
        "--execute",
        action="store_true",
        help="Start installed ccx after all run-gate confirmations pass.",
    )
    feaspec_calculix_run_parser.add_argument(
        "--confirm-run",
        action="store_true",
        help="Confirm the user intentionally requests installed-only solver execution.",
    )
    feaspec_calculix_run_parser.add_argument(
        "--acknowledge-readme",
        action="store_true",
        help="Acknowledge README_RUN_FIRST.txt has been reviewed.",
    )
    feaspec_calculix_run_parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=10.0,
        help="Short bounded timeout for ccx execution; default 10 seconds.",
    )
    feaspec_calculix_run_parser.add_argument(
        "--run-dir",
        default="",
        help="Empty isolated runtime directory. Defaults to a child of --export-dir.",
    )
    feaspec_calculix_run_parser.add_argument(
        "--ccx",
        default="",
        help="Explicit installed ccx path. If omitted, PATH discovery is used.",
    )
    feaspec_calculix_run_parser.add_argument(
        "--format",
        default="text",
        choices=("text", "json"),
        help="Run gate output format.",
    )
    feaspec_calculix_result_import_parser = subparsers.add_parser(
        "feaspec-calculix-result-import-preview",
        help="Preview FEASpec CalculiX result import planning without writing files.",
        description=(
            "Inspect an explicit CalculiX result directory and preview the experimental "
            "FEASpec result-import plan. The command writes no files, performs no solver "
            "execution, parses only bounded explicit .dat candidates, does not parse "
            ".frd field values, and keeps issue #8 live validation separate."
        ),
    )
    feaspec_calculix_result_import_parser.add_argument(
        "--result-dir",
        required=True,
        help="Existing CalculiX result directory to inspect.",
    )
    feaspec_calculix_result_import_parser.add_argument(
        "--format",
        default="text",
        choices=("text", "json"),
        help="Preview output format.",
    )
    feaspec_calculix_result_import_parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Exit 2 when the result import plan is blocked, unsupported, or still "
            "requires a future parser slice."
        ),
    )
    feaspec_calculix_result_import_parser.add_argument(
        "--include-artifacts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include artifact records in output; default true.",
    )
    feaspec_calculix_result_import_parser.add_argument(
        "--include-diagnostics",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include diagnostic records in output; default true.",
    )
    feaspec_calculix_result_import_write_parser = subparsers.add_parser(
        "feaspec-calculix-result-import-write",
        help="Plan or explicitly write FEASpec CalculiX ResultDataset review files.",
        description=(
            "Review an explicit CalculiX result directory, build the experimental "
            "ResultDataset write plan, and optionally write the standard review "
            "files. The default mode is plan-only: no files are written, no solver "
            "is executed, and original solver artifacts are not copied."
        ),
    )
    feaspec_calculix_result_import_write_parser.add_argument(
        "--result-dir",
        required=True,
        help="Existing CalculiX result directory to inspect.",
    )
    feaspec_calculix_result_import_write_parser.add_argument(
        "--output-dir",
        required=True,
        help="Explicit target directory for the standard ResultDataset layout.",
    )
    feaspec_calculix_result_import_write_parser.add_argument(
        "--format",
        default="text",
        choices=("text", "json"),
        help="Write review output format.",
    )
    feaspec_calculix_result_import_write_mode = (
        feaspec_calculix_result_import_write_parser.add_mutually_exclusive_group()
    )
    feaspec_calculix_result_import_write_mode.add_argument(
        "--plan-only",
        action="store_true",
        help="Build and display the write plan without writing files. This is the default.",
    )
    feaspec_calculix_result_import_write_mode.add_argument(
        "--write",
        action="store_true",
        help=(
            "Write the standard ResultDataset review files. Requires both "
            "acknowledgement flags."
        ),
    )
    feaspec_calculix_result_import_write_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing standard ResultDataset files after review.",
    )
    feaspec_calculix_result_import_write_parser.add_argument(
        "--create-dir",
        action="store_true",
        help="Allow creation of the explicit output directory when parent policy allows it.",
    )
    feaspec_calculix_result_import_write_parser.add_argument(
        "--acknowledge-limitations",
        action="store_true",
        help="Acknowledge carried import and parser limitations before write mode.",
    )
    feaspec_calculix_result_import_write_parser.add_argument(
        "--acknowledge-review-required",
        action="store_true",
        help="Acknowledge the README_REVIEW_FIRST human-review workflow before write mode.",
    )
    human_review_create_parser = subparsers.add_parser(
        "feaspec-human-review-create",
        help="Create a FEASpec human review record JSON file.",
        description=(
            "Create an experimental FEASpec human review record. The command writes "
            "only the requested review JSON file, performs no solver execution, and "
            "keeps export, run, and result import gates separate."
        ),
    )
    human_review_create_parser.add_argument(
        "--output",
        required=True,
        help="Output human review JSON path.",
    )
    human_review_create_parser.add_argument(
        "--source-feaspec-id",
        required=True,
        help="Source FEASpec identifier reviewed by the user.",
    )
    human_review_create_parser.add_argument(
        "--reviewer",
        required=True,
        help="Reviewer name or identifier.",
    )
    human_review_create_parser.add_argument(
        "--reviewed-at",
        required=True,
        help="Deterministic ISO-style review timestamp supplied by the caller.",
    )
    human_review_create_parser.add_argument(
        "--action",
        required=True,
        choices=(
            "needs-changes",
            "reject",
            "approve-no-run-export",
            "request-installed-only-run",
        ),
        help="Human review action to record.",
    )
    human_review_create_parser.add_argument(
        "--notes",
        action="append",
        default=[],
        help="Reviewer note. May be repeated.",
    )
    human_review_create_parser.add_argument(
        "--validator-report-hash",
        default="",
        help="Validator report hash required for approval records.",
    )
    human_review_create_parser.add_argument(
        "--validator-summary",
        default="",
        help="Validator summary as inline JSON object or path to a JSON object.",
    )
    human_review_create_parser.add_argument(
        "--bridge-summary",
        default="",
        help="Bridge summary as inline JSON object or path to a JSON object.",
    )
    human_review_create_parser.add_argument(
        "--case-plan-summary",
        default="",
        help="Case-plan summary as inline JSON object or path to a JSON object.",
    )
    human_review_create_parser.add_argument(
        "--export-preview-summary",
        default="",
        help="Export preview summary as inline JSON object or path to a JSON object.",
    )
    human_review_create_parser.add_argument(
        "--export-write-summary",
        default="",
        help="Export write summary as inline JSON object or path to a JSON object.",
    )
    human_review_create_parser.add_argument(
        "--accept-warning",
        action="append",
        default=[],
        metavar="CODE:REASON",
        help="Accept a non-blocking warning with a reason. May be repeated.",
    )
    human_review_create_parser.add_argument(
        "--reject-diagnostic",
        action="append",
        default=[],
        metavar="CODE:REASON",
        help="Record a rejected diagnostic decision with a reason. May be repeated.",
    )
    human_review_create_parser.add_argument(
        "--acknowledge-limitations",
        action="store_true",
        help="Acknowledge README/export limitations for installed-only run requests.",
    )
    human_review_create_parser.add_argument(
        "--acknowledge-readme",
        action="store_true",
        help="Acknowledge reviewed no-run export README or equivalent review evidence.",
    )
    human_review_create_parser.add_argument(
        "--acknowledge-run-gate-separate",
        action="store_true",
        help="Acknowledge that the actual installed-only run gate remains separate.",
    )
    human_review_create_parser.add_argument(
        "--format",
        default="text",
        choices=("text", "json"),
        help="Command output format.",
    )
    human_review_create_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the output review JSON file if it already exists.",
    )
    human_review_validate_parser = subparsers.add_parser(
        "feaspec-human-review-validate",
        help="Validate a FEASpec human review record JSON file.",
        description=(
            "Validate an experimental FEASpec human review record. The command "
            "writes no files, performs no solver execution, and keeps the run gate "
            "separate."
        ),
    )
    human_review_validate_parser.add_argument(
        "--record",
        required=True,
        help="Human review JSON record path.",
    )
    human_review_validate_parser.add_argument(
        "--format",
        default="text",
        choices=("text", "json"),
        help="Validation output format.",
    )
    human_review_validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Accepted for CLI consistency; invalid records return exit code 2.",
    )
    human_review_summary_parser = subparsers.add_parser(
        "feaspec-human-review-summary",
        help="Summarize a FEASpec human review record JSON file.",
        description=(
            "Summarize an experimental FEASpec human review record. The command "
            "writes no files and performs no solver execution."
        ),
    )
    human_review_summary_parser.add_argument(
        "--record",
        required=True,
        help="Human review JSON record path.",
    )
    human_review_summary_parser.add_argument(
        "--format",
        default="text",
        choices=("text", "json"),
        help="Summary output format.",
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
    field_artifacts_parser = subparsers.add_parser(
        "field-artifacts-inspect",
        help="Inspect field artifacts without running solvers or visualization backends.",
    )
    field_artifacts_parser.add_argument("path", help="Field artifact file or directory.")
    field_artifacts_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    field_dataset_parser = subparsers.add_parser(
        "field-dataset-inspect",
        help="Inspect a field-capable ResultDataset or FieldDataset JSON file.",
    )
    field_dataset_parser.add_argument("path", help="Field dataset JSON path.")
    field_dataset_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
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
    global json

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        print("\n".join(doctor_lines()))
        return 0

    if args.command == "optional-solver-list":
        manifests = builtin_optional_solver_manifests()
        if args.format == "json":
            print(
                json.dumps(
                    {
                        "stacks": [
                            _optional_solver_manifest_summary(
                                manifest,
                                include_requirements=args.include_requirements,
                            )
                            for manifest in manifests
                        ],
                        "passive_only": True,
                        "external_solvers_bundled": False,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print(
                _format_optional_solver_list_text(
                    manifests,
                    include_requirements=args.include_requirements,
                )
            )
        return 0

    if args.command == "optional-solver-doctor":
        try:
            manifests = _select_optional_solver_manifests(
                () if args.all else tuple(args.stack)
            )
        except KeyError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        report = _optional_solver_doctor_report(
            manifests,
            show_full_paths=args.show_full_paths,
        )
        if args.format == "json":
            print(
                json.dumps(
                    optional_solver_discovery_report_to_dict(report),
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print(
                _format_optional_solver_doctor_text(
                    report,
                    include_diagnostics=args.include_diagnostics,
                )
            )
        return 0

    if args.command == "optional-solver-explain":
        try:
            manifest = get_builtin_optional_solver_manifest(args.stack)
        except KeyError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(_optional_solver_explain_payload(manifest), indent=2, sort_keys=True))
        else:
            print(_format_optional_solver_explain_text(manifest))
        return 0

    if args.command == OPTIONAL_SOLVER_PLUGIN_MANIFEST_PREVIEW_COMMAND:
        if not args.manifest:
            print(
                "At least one --manifest explicit JSON file is required.",
                file=sys.stderr,
            )
            return 1
        report = _optional_solver_plugin_manifest_preview_report(
            tuple(args.manifest),
            include_builtins=args.include_builtins,
        )
        if args.format == "json":
            print(
                json.dumps(
                    _optional_solver_plugin_manifest_preview_payload(
                        report,
                        include_builtins=args.include_builtins,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print(
                _format_optional_solver_plugin_manifest_preview_text(
                    report,
                    include_builtins=args.include_builtins,
                    include_diagnostics=args.include_diagnostics,
                    show_policy=args.show_policy,
                )
            )
        if _optional_solver_plugin_manifest_preview_failed(report):
            return 1
        if args.strict and _optional_solver_plugin_manifest_preview_has_strict_failures(
            report
        ):
            return 2
        return 0

    if args.command == OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_COMMAND:
        return run_optional_solver_plugin_manifest_persistence_cli(args)

    if args.command == OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_COMMAND:
        return run_optional_solver_plugin_manifest_export_summary_cli(args)

    if args.command == OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_COMMAND:
        return run_optional_solver_plugin_manifest_reload_cli(args)

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

    if args.command in (
        "plugins-install-folder",
        "plugins-install-zip",
        "plugins-installed",
        "plugins-uninstall",
        "plugins-quarantine-list",
    ):
        import json

        from osw.plugins.installer import PluginInstallManager
        
        install_root = (
            args.install_root
            if getattr(args, "install_root", None)
            else DEFAULT_PLUGIN_INSTALL_ROOT
        )
        manager = PluginInstallManager(install_root)

        if args.command == "plugins-install-folder":
            try:
                result = manager.install_from_folder(
                    args.path, allow_replace=args.allow_replace
                )
                print(
                    f"Successfully installed folder plugin: "
                    f"{result.manifest.name} ({result.plugin_id})"
                )
                print(f"Installed Path: {result.installed_path}")
                if result.warnings:
                    print("Warnings:")
                    for w in result.warnings:
                        print(f"  - {w}")
                return 0
            except Exception as exc:
                print(f"Error: {exc}", file=sys.stderr)
                return 1

        elif args.command == "plugins-install-zip":
            try:
                result = manager.install_from_zip(
                    args.path, allow_replace=args.allow_replace
                )
                print(
                    f"Successfully installed ZIP plugin: "
                    f"{result.manifest.name} ({result.plugin_id})"
                )
                print(f"Installed Path: {result.installed_path}")
                if result.warnings:
                    print("Warnings:")
                    for w in result.warnings:
                        print(f"  - {w}")
                return 0
            except Exception as exc:
                print(f"Error: {exc}", file=sys.stderr)
                return 1

        elif args.command == "plugins-installed":
            receipts = manager.list_receipts()
            if args.json:
                print(json.dumps([r.to_dict() for r in receipts], indent=2, sort_keys=True))
            else:
                print(f"Installed managed plugin receipts: {len(receipts)}")
                print(f"Managed install root: {manager.install_root}")
                if not receipts:
                    print("  No managed install receipts.")
                    print("  Built-in, entry-point, and unmanaged plugins are not listed here.")
                for r in receipts:
                    print(
                        f"  - {r.plugin_id} "
                        f"(version: {r.version}, source: {r.source_kind}, "
                        f"status: {r.status})"
                    )
                    print(f"    Installed path: {r.installed_path}")
            return 0

        elif args.command == "plugins-uninstall":
            try:
                manager.uninstall_plugin(args.plugin_id)
                print(f"Successfully uninstalled managed plugin: {args.plugin_id}")
                print("Only the managed-root receipt-owned plugin directory was removed.")
                return 0
            except Exception as exc:
                print(f"Error: {exc}", file=sys.stderr)
                return 1

        elif args.command == "plugins-quarantine-list":
            records = manager.list_quarantine()
            if args.json:
                print(json.dumps([r.to_dict() for r in records], indent=2, sort_keys=True))
            else:
                print(f"Quarantined/rejected plugin installs: {len(records)}")
                print(f"Managed install root: {manager.install_root}")
                if not records:
                    print("  No quarantined or rejected plugin installs.")
                for r in records:
                    print(f"  - Time: {r.created_at}")
                    print(f"    Source: {r.source_path}")
                    source_kind = r.metadata.get("source_kind", "unknown")
                    print(f"    Source kind: {source_kind}")
                    if r.quarantine_path:
                        print(f"    Quarantine path: {r.quarantine_path}")
                    print(f"    Reason: {r.reason}")
            return 0

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

    if args.command == "feaspec-calculix-export-preview":
        import json

        try:
            preview = _build_feaspec_calculix_export_preview(
                Path(args.feaspec),
                target_solver=args.target_solver,
                basename=args.basename,
                planned_output_dir=args.planned_output_dir,
            )
        except (OSError, TypeError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(preview, indent=2, sort_keys=True))
        else:
            _print_feaspec_calculix_export_preview(preview)
        if args.strict and preview["export_preview_status"] == "blocked":
            return 2
        return 0

    if args.command == "feaspec-calculix-export-write":
        try:
            export_record = _run_feaspec_calculix_export_write(
                feaspec_path=Path(args.feaspec) if args.feaspec else None,
                case_plan_path=Path(args.case_plan) if args.case_plan else None,
                output_dir=Path(args.output_dir),
                target_solver=args.target_solver,
                basename=args.basename,
                overwrite=args.overwrite,
                create_dir=args.create_dir,
            )
        except (OSError, TypeError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(export_record, indent=2, sort_keys=True))
        else:
            _print_feaspec_calculix_export_write(export_record)
        if export_record["export_status"] == "blocked":
            return 2
        return 0

    if args.command == "feaspec-calculix-run-installed-only":
        export_dir = Path(args.export_dir).expanduser()
        if not export_dir.is_dir():
            print(f"Error: export bundle directory is not readable: {export_dir}", file=sys.stderr)
            return 1
        try:
            run_result = _run_feaspec_calculix_installed_only(args)
        except (OSError, TypeError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(run_result.to_dict(), indent=2, sort_keys=True))
        else:
            _print_feaspec_calculix_installed_run(run_result)
        return _feaspec_calculix_installed_run_exit_code(run_result)

    if args.command == "feaspec-calculix-result-import-preview":
        try:
            preview = _build_feaspec_calculix_result_import_preview(args)
        except (OSError, TypeError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(preview, indent=2, sort_keys=True))
        else:
            _print_feaspec_calculix_result_import_preview(preview)
        return _feaspec_calculix_result_import_preview_exit_code(
            preview,
            strict=args.strict,
        )

    if args.command == "feaspec-calculix-result-import-write":
        try:
            record = _build_feaspec_calculix_result_import_write(args)
        except (OSError, TypeError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(record, indent=2, sort_keys=True))
        else:
            _print_feaspec_calculix_result_import_write(record)
        return _feaspec_calculix_result_import_write_exit_code(record)

    if args.command == "feaspec-human-review-create":
        try:
            payload, exit_code = _run_feaspec_human_review_create(args)
        except (OSError, TypeError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _print_feaspec_human_review_payload(payload)
        return exit_code

    if args.command == "feaspec-human-review-validate":
        try:
            payload, exit_code = _run_feaspec_human_review_validate(Path(args.record))
        except (OSError, TypeError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _print_feaspec_human_review_payload(payload)
        return exit_code

    if args.command == "feaspec-human-review-summary":
        try:
            payload = _run_feaspec_human_review_summary(Path(args.record))
        except (OSError, TypeError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _print_feaspec_human_review_payload(payload)
        return 0

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

    if args.command == "field-dataset-inspect":
        import json

        from osw.post.field_dataset import field_dataset_from_json_file
        from osw.post.field_view_model import field_view_model_from_field_dataset

        field_dataset = field_dataset_from_json_file(Path(args.path))
        view_model = field_view_model_from_field_dataset(field_dataset)
        if args.json:
            print(json.dumps(view_model.to_dict(), indent=2, sort_keys=True))
        else:
            _print_field_view_model(view_model)
        return 0

    if args.command == "field-artifacts-inspect":
        import json

        from osw.post.field_view_model import field_view_model_from_artifacts

        view_model = field_view_model_from_artifacts(Path(args.path))
        if args.json:
            print(json.dumps(view_model.to_dict(), indent=2, sort_keys=True))
        else:
            _print_field_view_model(view_model, artifact_heading=True)
        return 1 if any("Missing field artifact" in item for item in view_model.diagnostics) else 0

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


def _build_feaspec_calculix_export_preview(
    feaspec_path: Path,
    *,
    target_solver: str,
    basename: str,
    planned_output_dir: str,
) -> dict[str, object]:
    from osw.experimental.feaspec.calculix_case_plan import (
        plan_calculix_case_from_bridge,
    )
    from osw.experimental.feaspec.calculix_inp_renderer import render_calculix_inp
    from osw.experimental.feaspec.io import load_feaspec
    from osw.experimental.feaspec.project_bridge import plan_project_from_feaspec
    from osw.experimental.feaspec.validator import validate_for_solver

    source = feaspec_path.expanduser()
    if not source.is_file():
        msg = f"FEASpec JSON path is not readable: {source}"
        raise FileNotFoundError(msg)

    spec = load_feaspec(source, allow_diagnostics=True)
    validation_report = validate_for_solver(spec, target_solver)
    bridge_plan = plan_project_from_feaspec(spec, target_solver=target_solver)
    case_plan = plan_calculix_case_from_bridge(bridge_plan)
    render_result = None
    if case_plan.ready_for_inp_writer and not case_plan.is_blocked:
        render_result = render_calculix_inp(case_plan)

    diagnostics = [
        *_diagnostic_records("validation", validation_report.diagnostics),
        *_diagnostic_records("bridge", bridge_plan.diagnostics),
        *_diagnostic_records("case_plan", case_plan.diagnostics),
    ]
    render_status = "not-attempted"
    if render_result is not None:
        render_status = str(render_result.status)
        diagnostics.extend(_diagnostic_records("inp_renderer", render_result.diagnostics))

    blocked = (
        validation_report.has_blockers
        or validation_report.has_errors
        or bridge_plan.is_blocked
        or case_plan.is_blocked
        or not case_plan.ready_for_inp_writer
        or (render_result is not None and render_result.is_blocked)
    )
    export_status = "blocked" if blocked else _ready_preview_status(render_status, diagnostics)

    return {
        "version": __version__,
        "input_path": str(source.resolve()),
        "target_solver": target_solver,
        "spec_type": getattr(getattr(spec, "spec_type", ""), "value", ""),
        "validation_status": validation_report.validation_state.value,
        "bridge_status": bridge_plan.status.value,
        "case_plan_status": case_plan.status.value,
        "render_status": render_status,
        "export_preview_status": export_status,
        "planned_files": _planned_feaspec_calculix_files(
            basename=basename,
            planned_output_dir=planned_output_dir,
        ),
        "diagnostics": diagnostics,
        "solver_execution_performed": False,
        "files_written": False,
        "limitations": [
            "Preview only; no export files were written.",
            "No CalculiX solver execution was performed.",
            "External solvers are optional and not bundled.",
            "Issue #8 live CalculiX validation remains separate.",
            "FEASpec CalculiX export remains experimental.",
        ],
    }


def _planned_feaspec_calculix_files(
    *,
    basename: str,
    planned_output_dir: str,
) -> list[dict[str, str]]:
    output_dir = Path(planned_output_dir) if planned_output_dir else Path("")
    filenames = (
        ("inp", f"{basename}.inp"),
        ("manifest", f"{basename}.manifest.json"),
        ("diagnostics", f"{basename}.diagnostics.json"),
        ("readme", "README_RUN_FIRST.txt"),
    )
    return [
        {
            "role": role,
            "filename": filename,
            "path": str(output_dir / filename),
        }
        for role, filename in filenames
    ]


def _diagnostic_records(
    source: str,
    diagnostics: Sequence[object],
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for diagnostic in diagnostics:
        to_dict = getattr(diagnostic, "to_dict", None)
        payload = dict(to_dict()) if callable(to_dict) else {"message": str(diagnostic)}
        payload["source"] = source
        records.append(payload)
    return records


def _ready_preview_status(
    render_status: str,
    diagnostics: Sequence[dict[str, object]],
) -> str:
    if render_status.endswith("warnings") or any(
        str(item.get("severity", "")).casefold() == "warning" for item in diagnostics
    ):
        return "ready-with-warnings"
    return "ready"


def _print_feaspec_calculix_export_preview(preview: dict[str, object]) -> None:
    print("FEASpec CalculiX export preview")
    print(f"Input: {preview['input_path']}")
    print(f"Target solver: {preview['target_solver']}")
    print(f"Validation status: {preview['validation_status']}")
    print(f"Bridge status: {preview['bridge_status']}")
    print(f"Case-plan status: {preview['case_plan_status']}")
    print(f"Render status: {preview['render_status']}")
    print(f"Export preview status: {preview['export_preview_status']}")
    print("Files written: false")
    print("Solver execution performed: false")
    print("No files written; no output directories were created.")
    print("No solver execution was performed.")
    print("External solvers are optional and not bundled.")
    print("Issue #8 live CalculiX validation remains separate.")
    print("Planned files:")
    for item in preview["planned_files"]:
        if isinstance(item, dict):
            print(f"  - {item['role']}: {item['path']}")
    print("Diagnostics:")
    diagnostics = preview["diagnostics"]
    if diagnostics:
        for item in diagnostics:
            if not isinstance(item, dict):
                continue
            code = item.get("code", "diagnostic")
            severity = str(item.get("severity", "")).upper() or "INFO"
            source = item.get("source", "preview")
            target = item.get("target_ref", item.get("path", ""))
            suffix = f" [{target}]" if target else ""
            print(f"  - {source}: {severity} {code}{suffix}: {item.get('message', '')}")
    else:
        print("  - none")
    print("Limitations:")
    for item in preview["limitations"]:
        print(f"  - {item}")


def _run_feaspec_calculix_export_write(
    *,
    feaspec_path: Path | None,
    case_plan_path: Path | None,
    output_dir: Path,
    target_solver: str,
    basename: str,
    overwrite: bool,
    create_dir: bool,
) -> dict[str, object]:
    from osw.experimental.feaspec.calculix_exporter import (
        export_calculix_case,
        export_calculix_case_from_feaspec,
    )

    if target_solver != "calculix":
        msg = "FEASpec CalculiX export write currently supports only target solver 'calculix'."
        raise ValueError(msg)
    if feaspec_path is None and case_plan_path is None:
        msg = "Provide either --feaspec or --case-plan."
        raise ValueError(msg)

    if case_plan_path is not None:
        source = case_plan_path.expanduser()
        if not source.is_file():
            msg = f"FEASpec CalculiX case-plan JSON path is not readable: {source}"
            raise FileNotFoundError(msg)
        result = export_calculix_case(
            _load_feaspec_calculix_case_plan_json(source),
            output_dir,
            basename=basename,
            overwrite=overwrite,
            create_dir=create_dir,
        )
        input_kind = "case_plan"
    else:
        source = Path(feaspec_path).expanduser()
        if not source.is_file():
            msg = f"FEASpec JSON path is not readable: {source}"
            raise FileNotFoundError(msg)
        result = export_calculix_case_from_feaspec(
            source,
            output_dir,
            basename=basename,
            overwrite=overwrite,
            create_dir=create_dir,
        )
        input_kind = "feaspec"

    return {
        "version": __version__,
        "input_path": str(source.resolve()),
        "input_kind": input_kind,
        "output_dir": str(output_dir.expanduser().resolve()),
        "target_solver": target_solver,
        "export_status": result.status,
        "files_written": bool(result.files),
        "solver_execution_performed": False,
        "written_files": [item.to_dict() for item in result.files],
        "diagnostics": _feaspec_calculix_export_diagnostic_records(result),
        "limitations": _feaspec_calculix_export_write_limitations(),
    }


def _run_feaspec_calculix_installed_only(args: argparse.Namespace) -> object:
    from osw.experimental.feaspec.calculix_run_gate import (
        run_calculix_installed_only,
    )

    return run_calculix_installed_only(
        Path(args.export_dir),
        ccx_path=Path(args.ccx) if args.ccx else None,
        run_dir=Path(args.run_dir) if args.run_dir else None,
        timeout_seconds=args.timeout_seconds,
        execute=args.execute,
        confirm_run=args.confirm_run,
        acknowledge_readme=args.acknowledge_readme,
    )


def _print_feaspec_calculix_installed_run(result: object) -> None:
    from osw.experimental.feaspec.calculix_run_gate import (
        explain_calculix_run_result,
    )

    for line in explain_calculix_run_result(result):
        print(line)
    print("Limitations:")
    metadata = getattr(result, "metadata", None)
    for limitation in tuple(getattr(metadata, "limitations", ()) or ()):
        print(f"  - {limitation}")


def _feaspec_calculix_installed_run_exit_code(result: object) -> int:
    status = str(getattr(getattr(result, "status", ""), "value", getattr(result, "status", "")))
    metadata = getattr(result, "metadata", None)
    execute_requested = bool(getattr(metadata, "execute_requested", False))
    if not execute_requested:
        return 1 if status == "blocked" else 0
    return 0 if status in {"ran", "ran-with-warnings"} else 2


def _build_feaspec_calculix_result_import_preview(
    args: argparse.Namespace,
) -> dict[str, object]:
    from osw.experimental.feaspec.calculix_result_dataset_draft_mapping import (
        build_calculix_result_dataset_draft_mapping,
        summarize_calculix_result_dataset_draft_mapping,
    )
    from osw.experimental.feaspec.calculix_result_diagnostics import (
        CalculiXResultImportDiagnosticCode,
    )
    from osw.experimental.feaspec.calculix_result_import import (
        FEASpecCalculiXResultImportStatus,
        build_calculix_result_dataset_draft,
        explain_calculix_result_import_plan,
        inspect_calculix_result_directory,
        plan_calculix_result_import,
    )

    result_dir = Path(args.result_dir).expanduser()
    inspection = inspect_calculix_result_directory(result_dir)
    plan = plan_calculix_result_import(result_dir)
    dataset_draft = build_calculix_result_dataset_draft(plan)
    dataset_draft_mapping = build_calculix_result_dataset_draft_mapping(plan)
    dataset_draft_mapping_summary = (
        summarize_calculix_result_dataset_draft_mapping(dataset_draft_mapping)
    )
    diagnostic_records = [item.to_dict() for item in plan.diagnostics]
    parse_not_implemented = any(
        item.code is CalculiXResultImportDiagnosticCode.FI_PARSE_NOT_IMPLEMENTED
        for item in plan.diagnostics
    )
    status_summary = _feaspec_calculix_result_import_status_summary(plan.artifacts)
    dat_section_summary = _feaspec_calculix_result_import_dat_section_summary(
        plan.artifacts
    )
    dat_minimal_parse_summary = (
        _feaspec_calculix_result_import_dat_minimal_parse_summary(plan.artifacts)
    )
    frd_block_summary = _feaspec_calculix_result_import_frd_block_summary(
        plan.artifacts
    )
    status_value = plan.status.value
    strict_blocked = (
        plan.status
        in {
            FEASpecCalculiXResultImportStatus.BLOCKED,
            FEASpecCalculiXResultImportStatus.UNSUPPORTED,
            FEASpecCalculiXResultImportStatus.PARSE_NOT_IMPLEMENTED,
        }
        or parse_not_implemented
    )

    return {
        "command": "feaspec-calculix-result-import-preview",
        "version": __version__,
        "status": status_value,
        "result_dir": str(result_dir.resolve()),
        "result_dir_readable": bool(inspection.exists and inspection.is_directory),
        "artifact_count": len(plan.artifacts),
        "artifacts": (
            [artifact.to_dict() for artifact in plan.artifacts]
            if args.include_artifacts
            else []
        ),
        "diagnostics": diagnostic_records if args.include_diagnostics else [],
        "diagnostic_count": len(diagnostic_records),
        "provenance": plan.provenance.to_dict(),
        "dataset_draft": dataset_draft.to_dict(),
        "dataset_draft_mapping": dataset_draft_mapping.to_dict(),
        "dataset_draft_mapping_summary": dataset_draft_mapping_summary.to_dict(),
        "status_summary": status_summary,
        "dat_section_summary": dat_section_summary,
        "dat_minimal_parse_summary": dat_minimal_parse_summary,
        "frd_block_summary": frd_block_summary,
        "parse_not_implemented": parse_not_implemented,
        "solver_execution_performed": False,
        "source_run_solver_execution_performed": (
            plan.provenance.solver_execution_performed
        ),
        "files_written": False,
        "strict_blocked": strict_blocked,
        "explanation": explain_calculix_result_import_plan(plan),
        "limitations": [
            "Preview only; no files are written.",
            "No solver execution is performed by this command.",
            "No free-form .dat parser or .frd numerical field parser is implemented.",
            "Minimal .dat parsing is bounded to explicit scalar/table candidates.",
            ".dat section summaries are metadata-only when present.",
            ".frd block summaries are metadata-only when present.",
            "Status summaries from .sta/.cvg are text-only when present.",
            "No ResultDataset persistence or ProjectSchema mutation is performed.",
            "Issue #8 live CalculiX validation remains separate.",
            "External solvers are optional and not bundled.",
            "FEASpec CalculiX result import remains experimental.",
        ],
    }


def _feaspec_calculix_result_import_dat_section_summary(
    artifacts: Sequence[object],
) -> dict[str, object]:
    dat_artifacts: list[dict[str, object]] = []
    aggregate_counts: dict[str, int] = {}
    numeric_tokens_not_parsed = False
    unsupported_section_count = 0
    unknown_section_count = 0
    section_count = 0

    for artifact in artifacts:
        metadata = getattr(artifact, "metadata", {})
        if not isinstance(metadata, Mapping):
            continue
        summary = metadata.get("dat_section_summary")
        if not isinstance(summary, Mapping):
            continue
        counts = summary.get("kind_counts")
        if isinstance(counts, Mapping):
            for key, value in counts.items():
                if isinstance(key, str) and isinstance(value, int):
                    aggregate_counts[key] = aggregate_counts.get(key, 0) + value
        section_count += _int_value(summary.get("section_count"))
        unsupported_section_count += _int_value(summary.get("unsupported_section_count"))
        unknown_section_count += _int_value(summary.get("unknown_section_count"))
        numeric_tokens_not_parsed = numeric_tokens_not_parsed or bool(
            summary.get("numeric_tokens_not_parsed", False)
        )
        kind = getattr(artifact, "kind", "")
        kind_value = getattr(kind, "value", str(kind))
        dat_artifacts.append(
            {
                "filename": getattr(artifact, "filename", ""),
                "kind": kind_value,
                "summary": dict(summary),
            }
        )

    return {
        "available": bool(dat_artifacts),
        "file_count": len(dat_artifacts),
        "section_count": section_count,
        "kind_counts": aggregate_counts,
        "unsupported_section_count": unsupported_section_count,
        "unknown_section_count": unknown_section_count,
        "numeric_tokens_not_parsed": numeric_tokens_not_parsed,
        "files": dat_artifacts,
        "numerical_values_parsed": False,
        "numeric_values_extracted": False,
        "tables_extracted": False,
        "units_inferred": False,
        "writes_files": False,
    }


def _feaspec_calculix_result_import_dat_minimal_parse_summary(
    artifacts: Sequence[object],
) -> dict[str, object]:
    dat_artifacts: list[dict[str, object]] = []
    scalar_count = 0
    table_count = 0
    unsupported_content_count = 0
    parsed_numeric_value_count = 0

    for artifact in artifacts:
        metadata = getattr(artifact, "metadata", {})
        if not isinstance(metadata, Mapping):
            continue
        summary = metadata.get("dat_minimal_parse_summary")
        if not isinstance(summary, Mapping):
            continue
        scalar_count += _int_value(summary.get("scalar_candidate_count"))
        table_count += _int_value(summary.get("table_candidate_count"))
        unsupported_content_count += _int_value(summary.get("unsupported_content_count"))
        parsed_numeric_value_count += _int_value(
            summary.get("parsed_numeric_value_count")
        )
        kind = getattr(artifact, "kind", "")
        kind_value = getattr(kind, "value", str(kind))
        dat_artifacts.append(
            {
                "filename": getattr(artifact, "filename", ""),
                "kind": kind_value,
                "summary": dict(summary),
            }
        )

    return {
        "available": bool(dat_artifacts),
        "file_count": len(dat_artifacts),
        "scalar_candidate_count": scalar_count,
        "table_candidate_count": table_count,
        "unsupported_content_count": unsupported_content_count,
        "parsed_numeric_value_count": parsed_numeric_value_count,
        "files": dat_artifacts,
        "minimal_parser": bool(dat_artifacts),
        "freeform_parser": False,
        "frd_parser": False,
        "units_inferred": False,
        "writes_files": False,
    }


def _feaspec_calculix_result_import_frd_block_summary(
    artifacts: Sequence[object],
) -> dict[str, object]:
    frd_artifacts: list[dict[str, object]] = []
    aggregate_counts: dict[str, int] = {}
    reference_counts: dict[str, int] = {}
    block_count = 0
    reference_candidate_count = 0
    field_reference_candidate_count = 0
    mesh_reference_candidate_count = 0
    unsupported_block_count = 0
    unknown_block_count = 0
    numeric_tokens_not_parsed = False

    for artifact in artifacts:
        metadata = getattr(artifact, "metadata", {})
        if not isinstance(metadata, Mapping):
            continue
        summary = metadata.get("frd_block_summary")
        if not isinstance(summary, Mapping):
            continue
        counts = summary.get("kind_counts")
        if isinstance(counts, Mapping):
            for key, value in counts.items():
                if isinstance(key, str) and isinstance(value, int):
                    aggregate_counts[key] = aggregate_counts.get(key, 0) + value
        refs = summary.get("reference_kind_counts")
        if isinstance(refs, Mapping):
            for key, value in refs.items():
                if isinstance(key, str) and isinstance(value, int):
                    reference_counts[key] = reference_counts.get(key, 0) + value
        block_count += _int_value(summary.get("block_count"))
        reference_candidate_count += _int_value(
            summary.get("reference_candidate_count")
        )
        field_reference_candidate_count += _int_value(
            summary.get("field_reference_candidate_count")
        )
        mesh_reference_candidate_count += _int_value(
            summary.get("mesh_reference_candidate_count")
        )
        unsupported_block_count += _int_value(summary.get("unsupported_block_count"))
        unknown_block_count += _int_value(summary.get("unknown_block_count"))
        numeric_tokens_not_parsed = numeric_tokens_not_parsed or bool(
            summary.get("numeric_tokens_not_parsed", False)
        )
        kind = getattr(artifact, "kind", "")
        kind_value = getattr(kind, "value", str(kind))
        frd_artifacts.append(
            {
                "filename": getattr(artifact, "filename", ""),
                "kind": kind_value,
                "summary": dict(summary),
            }
        )

    return {
        "available": bool(frd_artifacts),
        "file_count": len(frd_artifacts),
        "block_count": block_count,
        "kind_counts": aggregate_counts,
        "reference_kind_counts": reference_counts,
        "reference_candidate_count": reference_candidate_count,
        "field_reference_candidate_count": field_reference_candidate_count,
        "mesh_reference_candidate_count": mesh_reference_candidate_count,
        "unsupported_block_count": unsupported_block_count,
        "unknown_block_count": unknown_block_count,
        "numeric_tokens_not_parsed": numeric_tokens_not_parsed,
        "files": frd_artifacts,
        "numerical_values_parsed": False,
        "field_values_parsed": False,
        "numeric_values_extracted": False,
        "mesh_reconstructed": False,
        "visualization_arrays_built": False,
        "units_inferred": False,
        "writes_files": False,
    }


def _int_value(value: object) -> int:
    return value if isinstance(value, int) else 0


def _feaspec_calculix_result_import_status_summary(
    artifacts: Sequence[object],
) -> dict[str, object]:
    status_artifacts: list[dict[str, object]] = []
    aggregate_counts: dict[str, int] = {}
    completion_indicated = False
    failure_indicated = False
    numeric_tokens_not_parsed = False

    for artifact in artifacts:
        metadata = getattr(artifact, "metadata", {})
        if not isinstance(metadata, Mapping):
            continue
        summary = metadata.get("status_summary")
        if not isinstance(summary, Mapping):
            continue
        counts = summary.get("category_counts")
        if isinstance(counts, Mapping):
            for key, value in counts.items():
                if isinstance(key, str) and isinstance(value, int):
                    aggregate_counts[key] = aggregate_counts.get(key, 0) + value
        completion_indicated = completion_indicated or bool(
            summary.get("completion_indicated", False)
        )
        failure_indicated = failure_indicated or bool(
            summary.get("failure_indicated", False)
        )
        numeric_tokens_not_parsed = numeric_tokens_not_parsed or bool(
            summary.get("numeric_tokens_not_parsed", False)
        )
        kind = getattr(artifact, "kind", "")
        kind_value = getattr(kind, "value", str(kind))
        status_artifacts.append(
            {
                "filename": getattr(artifact, "filename", ""),
                "kind": kind_value,
                "summary": dict(summary),
            }
        )

    return {
        "available": bool(status_artifacts),
        "file_count": len(status_artifacts),
        "category_counts": aggregate_counts,
        "completion_indicated": completion_indicated,
        "failure_indicated": failure_indicated,
        "numeric_tokens_not_parsed": numeric_tokens_not_parsed,
        "files": status_artifacts,
        "numerical_values_parsed": False,
        "writes_files": False,
    }


def _print_feaspec_calculix_result_import_preview(
    preview: Mapping[str, object],
) -> None:
    print("FEASpec CalculiX result import preview")
    print(f"Result directory: {preview['result_dir']}")
    print(f"Status: {preview['status']}")
    print(f"Artifacts inspected: {preview['artifact_count']}")
    print("Preview only: true")
    print("Files written: false")
    print("Solver execution performed by this command: false")
    print("Broad numerical parser implemented: false")
    print("ResultDataset persistence: false")
    print("ProjectSchema mutation: false")
    print("Issue #8 remains separate.")
    print("External solvers are optional and not bundled.")
    print(f"Parse not implemented: {str(preview['parse_not_implemented']).lower()}")
    status_summary = preview.get("status_summary", {})
    if isinstance(status_summary, Mapping) and status_summary.get("available"):
        print("Status summary: available")
        print(f"Status files scanned: {status_summary.get('file_count', 0)}")
        print(
            "Status numeric values parsed: "
            f"{str(status_summary.get('numerical_values_parsed', False)).lower()}"
        )
        counts = status_summary.get("category_counts", {})
        if isinstance(counts, Mapping) and counts:
            rendered = ", ".join(
                f"{key}={value}" for key, value in sorted(counts.items())
            )
            print(f"Status category counts: {rendered}")
    dat_section_summary = preview.get("dat_section_summary", {})
    if isinstance(dat_section_summary, Mapping) and dat_section_summary.get("available"):
        print("DAT section summary: available")
        print(f"DAT files scanned: {dat_section_summary.get('file_count', 0)}")
        print(f"DAT sections scanned: {dat_section_summary.get('section_count', 0)}")
        print(
            "DAT numeric values parsed: "
            f"{str(dat_section_summary.get('numerical_values_parsed', False)).lower()}"
        )
        print(
            "DAT tables extracted: "
            f"{str(dat_section_summary.get('tables_extracted', False)).lower()}"
        )
        counts = dat_section_summary.get("kind_counts", {})
        if isinstance(counts, Mapping) and counts:
            rendered = ", ".join(
                f"{key}={value}" for key, value in sorted(counts.items())
            )
            print(f"DAT section kind counts: {rendered}")
    dat_minimal_parse_summary = preview.get("dat_minimal_parse_summary", {})
    if (
        isinstance(dat_minimal_parse_summary, Mapping)
        and dat_minimal_parse_summary.get("available")
    ):
        print("DAT minimal parse summary: available")
        print(
            "DAT scalar candidates: "
            f"{dat_minimal_parse_summary.get('scalar_candidate_count', 0)}"
        )
        print(
            "DAT table candidates: "
            f"{dat_minimal_parse_summary.get('table_candidate_count', 0)}"
        )
        print(
            "DAT parsed numeric values: "
            f"{dat_minimal_parse_summary.get('parsed_numeric_value_count', 0)}"
        )
        print(
            "DAT free-form parser: "
            f"{str(dat_minimal_parse_summary.get('freeform_parser', False)).lower()}"
        )
        print(
            "DAT units inferred: "
            f"{str(dat_minimal_parse_summary.get('units_inferred', False)).lower()}"
        )
    frd_block_summary = preview.get("frd_block_summary", {})
    if isinstance(frd_block_summary, Mapping) and frd_block_summary.get("available"):
        print("FRD block summary: available")
        print(f"FRD files scanned: {frd_block_summary.get('file_count', 0)}")
        print(f"FRD blocks scanned: {frd_block_summary.get('block_count', 0)}")
        print(
            "FRD field values parsed: "
            f"{str(frd_block_summary.get('field_values_parsed', False)).lower()}"
        )
        print(
            "FRD mesh reconstructed: "
            f"{str(frd_block_summary.get('mesh_reconstructed', False)).lower()}"
        )
        counts = frd_block_summary.get("kind_counts", {})
        if isinstance(counts, Mapping) and counts:
            rendered = ", ".join(
                f"{key}={value}" for key, value in sorted(counts.items())
            )
            print(f"FRD block kind counts: {rendered}")
    draft_mapping_summary = preview.get("dataset_draft_mapping_summary", {})
    if (
        isinstance(draft_mapping_summary, Mapping)
        and draft_mapping_summary.get("artifact_count", 0)
    ):
        print("ResultDataset draft mapping: available")
        print(
            "Draft mapping artifacts: "
            f"{draft_mapping_summary.get('artifact_count', 0)}"
        )
        print(
            "Draft mapping scalar candidates: "
            f"{draft_mapping_summary.get('scalar_candidate_count', 0)}"
        )
        print(
            "Draft mapping table candidates: "
            f"{draft_mapping_summary.get('table_candidate_count', 0)}"
        )
        print(
            "Draft mapping field references: "
            f"{draft_mapping_summary.get('field_reference_count', 0)}"
        )
        print(
            "Draft mapping writes files: "
            f"{str(draft_mapping_summary.get('writes_files', False)).lower()}"
        )
    print(
        "Source run solver execution performed: "
        f"{str(preview['source_run_solver_execution_performed']).lower()}"
    )
    print("Explanation:")
    for line in preview["explanation"]:
        print(f"  - {line}")
    print("Artifacts:")
    artifacts = preview["artifacts"]
    if artifacts:
        for item in artifacts:
            if not isinstance(item, Mapping):
                continue
            print(
                f"  - {item.get('kind', 'artifact')}: "
                f"{item.get('filename', '')} ({item.get('size_bytes', 0)} bytes)"
            )
    else:
        print("  - none")
    print("Diagnostics:")
    diagnostics = preview["diagnostics"]
    if diagnostics:
        for item in diagnostics:
            if not isinstance(item, Mapping):
                continue
            severity = str(item.get("severity", "")).upper() or "INFO"
            path = f" [{item.get('path')}]" if item.get("path") else ""
            print(
                f"  - {severity} {item.get('code', 'diagnostic')}{path}: "
                f"{item.get('message', '')}"
            )
    else:
        print("  - none")
    print("Limitations:")
    for item in preview["limitations"]:
        print(f"  - {item}")


def _feaspec_calculix_result_import_preview_exit_code(
    preview: Mapping[str, object],
    *,
    strict: bool,
) -> int:
    if not bool(preview.get("result_dir_readable", False)):
        return 1
    if strict and bool(preview.get("strict_blocked", False)):
        return 2
    return 0


def _build_feaspec_calculix_result_import_write(
    args: argparse.Namespace,
) -> dict[str, object]:
    from osw.experimental.feaspec.calculix_result_dataset_draft_mapping import (
        build_calculix_result_dataset_draft_mapping,
        summarize_calculix_result_dataset_draft_mapping,
    )
    from osw.experimental.feaspec.calculix_result_dataset_schema import (
        build_calculix_result_dataset_schema_payload,
        validate_calculix_result_dataset_schema_payload,
    )
    from osw.experimental.feaspec.calculix_result_dataset_write_plan import (
        plan_calculix_result_dataset_write,
        validate_calculix_result_dataset_write_plan,
    )
    from osw.experimental.feaspec.calculix_result_dataset_writer import (
        write_calculix_result_dataset,
    )
    from osw.experimental.feaspec.calculix_result_import import (
        plan_calculix_result_import,
    )

    result_dir = Path(args.result_dir).expanduser()
    output_dir = Path(args.output_dir).expanduser()
    mode = "write" if bool(args.write) else "plan-only"
    import_plan = plan_calculix_result_import(result_dir)
    draft_mapping = build_calculix_result_dataset_draft_mapping(import_plan)
    draft_summary = summarize_calculix_result_dataset_draft_mapping(draft_mapping)
    limitations_acknowledged_for_plan = (
        bool(args.acknowledge_limitations) if args.write else True
    )
    write_plan = plan_calculix_result_dataset_write(
        draft_mapping,
        output_dir=output_dir,
        overwrite=bool(args.overwrite),
        create_dir=bool(args.create_dir),
        acknowledge_limitations=limitations_acknowledged_for_plan,
        copy_artifacts=False,
    )
    write_plan_validation = validate_calculix_result_dataset_write_plan(write_plan)
    schema_payload = build_calculix_result_dataset_schema_payload(
        draft_mapping,
        write_plan,
    )
    schema_validation = validate_calculix_result_dataset_schema_payload(schema_payload)
    cli_diagnostics = _feaspec_calculix_result_import_write_cli_diagnostics(
        args,
        import_status=import_plan.status,
    )

    pre_write_diagnostics = [
        *_result_import_write_diagnostic_records(
            import_plan.diagnostics,
            source="result_import",
        ),
        *_result_import_write_diagnostic_records(
            write_plan_validation.diagnostics,
            source="write_plan",
        ),
        *_result_import_write_diagnostic_records(
            schema_validation.diagnostics,
            source="schema_payload",
        ),
        *cli_diagnostics,
    ]
    pre_write_blocked = any(_diagnostic_blocks_write(item) for item in pre_write_diagnostics)
    writer_result = None
    if args.write and not pre_write_blocked:
        writer_result = write_calculix_result_dataset(
            write_plan,
            schema_payload,
            overwrite=bool(args.overwrite),
        )

    writer_diagnostics = (
        _result_import_write_diagnostic_records(
            writer_result.diagnostics,
            source="library_writer",
        )
        if writer_result is not None
        else []
    )
    diagnostics = _dedupe_cli_diagnostics([*pre_write_diagnostics, *writer_diagnostics])
    written_files = (
        [item.to_dict() for item in writer_result.written_files]
        if writer_result is not None
        else []
    )
    write_status = _feaspec_calculix_result_import_write_status(
        mode=mode,
        blocked=pre_write_blocked,
        writer_result=writer_result,
    )
    limitations = _feaspec_calculix_result_import_write_limitations(
        import_plan.limitations,
        getattr(draft_mapping, "limitations", ()),
    )

    return {
        "command": "feaspec-calculix-result-import-write",
        "version": __version__,
        "mode": mode,
        "result_dir": str(result_dir.resolve()),
        "result_dir_readable": bool(result_dir.is_dir()),
        "output_dir": str(output_dir),
        "import_status": import_plan.status.value,
        "draft_mapping_status": draft_mapping.status.value,
        "draft_mapping_summary": draft_summary.to_dict(),
        "plan_status": write_plan_validation.status.value,
        "schema_status": schema_validation.status.value,
        "write_status": write_status,
        "planned_files": [item.to_dict() for item in write_plan.planned_files],
        "written_files": written_files,
        "diagnostics": diagnostics,
        "diagnostic_count": len(diagnostics),
        "blocker_count": sum(1 for item in diagnostics if _diagnostic_blocks_write(item)),
        "limitations": limitations,
        "acknowledgements": {
            "limitations": bool(args.acknowledge_limitations),
            "review_required": bool(args.acknowledge_review_required),
        },
        "files_written": bool(written_files),
        "solver_execution_performed": False,
        "source_run_solver_execution_performed": (
            import_plan.provenance.solver_execution_performed
        ),
        "artifact_copy_performed": False,
        "issue_mutation_performed": False,
        "release_mutation_performed": False,
        "tag_mutation_performed": False,
        "projectschema_mutation_performed": False,
        "gui_write_command_added": False,
        "cli_write_command_added": True,
    }


def _feaspec_calculix_result_import_write_cli_diagnostics(
    args: argparse.Namespace,
    *,
    import_status: object,
) -> list[dict[str, object]]:
    diagnostics: list[dict[str, object]] = []
    status_text = str(getattr(import_status, "value", import_status))
    if status_text in {"blocked", "unsupported"}:
        diagnostics.append(
            _cli_write_diagnostic(
                "FCW_IMPORT_NOT_READY",
                "blocker",
                "Result import plan is not ready for ResultDataset write review.",
                suggested_fix="Resolve result import blockers before write planning.",
            )
        )
    if args.write and not bool(args.acknowledge_limitations):
        diagnostics.append(
            _cli_write_diagnostic(
                "FCW_LIMITATIONS_ACKNOWLEDGEMENT_REQUIRED",
                "blocker",
                "Write mode requires --acknowledge-limitations.",
                suggested_fix="Review limitations, then pass --acknowledge-limitations.",
            )
        )
    if args.write and not bool(args.acknowledge_review_required):
        diagnostics.append(
            _cli_write_diagnostic(
                "FCW_REVIEW_ACKNOWLEDGEMENT_REQUIRED",
                "blocker",
                "Write mode requires --acknowledge-review-required.",
                suggested_fix="Review the README_REVIEW_FIRST workflow before writing.",
            )
        )
    return diagnostics


def _cli_write_diagnostic(
    code: str,
    severity: str,
    message: str,
    *,
    path: str = "",
    suggested_fix: str = "",
) -> dict[str, object]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "path": path,
        "suggested_fix": suggested_fix,
        "blocks_write": severity == "blocker",
        "source": "cli",
    }


def _result_import_write_diagnostic_records(
    diagnostics: object,
    *,
    source: str,
) -> list[dict[str, object]]:
    if not isinstance(diagnostics, Sequence) or isinstance(diagnostics, (str, bytes)):
        return []
    records: list[dict[str, object]] = []
    for diagnostic in diagnostics:
        record: dict[str, object]
        if isinstance(diagnostic, Mapping):
            record = dict(diagnostic)
        else:
            to_dict = getattr(diagnostic, "to_dict", None)
            payload = to_dict() if callable(to_dict) else {"message": str(diagnostic)}
            record = dict(payload) if isinstance(payload, Mapping) else {"message": str(payload)}
        record.setdefault("source", source)
        records.append(record)
    return records


def _diagnostic_blocks_write(record: Mapping[str, object]) -> bool:
    severity = str(record.get("severity", "")).lower()
    return bool(
        severity == "blocker"
        or record.get("blocks_write")
        or record.get("blocks_import")
        or record.get("blocks_mapping")
        or record.get("blocks_payload")
    )


def _dedupe_cli_diagnostics(
    diagnostics: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    seen: set[tuple[str, str, str, str]] = set()
    unique: list[dict[str, object]] = []
    for diagnostic in diagnostics:
        record = dict(diagnostic)
        key = (
            str(record.get("code", "")),
            str(record.get("path", "")),
            str(record.get("message", "")),
            str(record.get("source", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


def _feaspec_calculix_result_import_write_status(
    *,
    mode: str,
    blocked: bool,
    writer_result: object | None,
) -> str:
    if writer_result is not None:
        return str(getattr(getattr(writer_result, "status", ""), "value", ""))
    if blocked:
        return "blocked"
    return "plan-only" if mode == "plan-only" else "blocked"


def _feaspec_calculix_result_import_write_limitations(
    import_limitations: object,
    draft_limitations: object,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    if isinstance(import_limitations, Sequence) and not isinstance(
        import_limitations,
        (str, bytes),
    ):
        records.extend(
            {"message": str(item), "source": "result-import-plan"}
            for item in import_limitations
        )
    if isinstance(draft_limitations, Sequence) and not isinstance(
        draft_limitations,
        (str, bytes),
    ):
        for item in draft_limitations:
            if isinstance(item, Mapping):
                records.append(dict(item))
            else:
                to_dict = getattr(item, "to_dict", None)
                payload = to_dict() if callable(to_dict) else None
                records.append(
                    dict(payload)
                    if isinstance(payload, Mapping)
                    else {"message": str(item), "source": "draft-mapping"}
                )
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, object]] = []
    for record in records:
        key = (str(record.get("message", "")), str(record.get("source", "")))
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


def _print_feaspec_calculix_result_import_write(
    record: Mapping[str, object],
) -> None:
    print("FEASpec CalculiX result import write")
    print(f"Mode: {record['mode']}")
    print(f"Result directory: {record['result_dir']}")
    print(f"Output directory: {record['output_dir']}")
    print(f"Import status: {record['import_status']}")
    print(f"Plan status: {record['plan_status']}")
    print(f"Schema status: {record['schema_status']}")
    print(f"Write status: {record['write_status']}")
    print(f"Files written: {str(record['files_written']).lower()}")
    print("Solver execution performed by this command: false")
    print("Artifact copying performed by this command: false")
    print("Issue/release/tag mutation performed: false")
    print("Issue #8 remains separate and open.")
    print("Planned files:")
    planned_files = record.get("planned_files", ())
    if isinstance(planned_files, Sequence) and planned_files:
        for item in planned_files:
            if isinstance(item, Mapping):
                print(
                    f"  - {item.get('relative_path', '')}: "
                    f"{item.get('target_path', '')}"
                )
    else:
        print("  - none")
    written_files = record.get("written_files", ())
    if isinstance(written_files, Sequence) and written_files:
        print("Written files:")
        for item in written_files:
            if isinstance(item, Mapping):
                print(
                    f"  - {item.get('relative_path', '')} "
                    f"({item.get('payload_kind', '')}, "
                    f"{item.get('size_bytes', 0)} bytes, "
                    f"sha256={item.get('sha256', '')})"
                )
    print(f"Diagnostics: {record.get('diagnostic_count', 0)}")
    diagnostics = record.get("diagnostics", ())
    if isinstance(diagnostics, Sequence) and diagnostics:
        for item in diagnostics:
            if not isinstance(item, Mapping):
                continue
            severity = str(item.get("severity", "")).upper() or "INFO"
            path = f" [{item.get('path')}]" if item.get("path") else ""
            print(
                f"  - {severity} {item.get('code', 'diagnostic')}{path}: "
                f"{item.get('message', '')}"
            )
    else:
        print("  - none")
    print(f"Limitations: {len(record.get('limitations', ()) or ())}")
    limitations = record.get("limitations", ())
    if isinstance(limitations, Sequence):
        for item in limitations:
            if isinstance(item, Mapping):
                print(f"  - {item.get('message', '')}")
            else:
                print(f"  - {item}")


def _feaspec_calculix_result_import_write_exit_code(
    record: Mapping[str, object],
) -> int:
    write_status = str(record.get("write_status", ""))
    if write_status in {"failed", "partial-cleanup-failed"}:
        return 1
    if not bool(record.get("result_dir_readable", False)):
        return 2
    if _int_value(record.get("blocker_count")) > 0 or write_status == "blocked":
        return 2
    return 0


def _load_feaspec_calculix_case_plan_json(path: Path) -> object:
    import json

    from osw.experimental.feaspec.calculix_case_plan import (
        CalculiXCaseBoundaryConditionPlan,
        CalculiXCaseElementPlan,
        CalculiXCaseLoadPlan,
        CalculiXCaseMaterialPlan,
        CalculiXCaseNodePlan,
        CalculiXCaseOutputRequestPlan,
        CalculiXCaseSectionPlan,
        CalculiXCaseStatus,
        CalculiXCaseStepPlan,
        FEASpecCalculiXCasePlan,
    )
    from osw.experimental.feaspec.calculix_diagnostics import (
        CalculiXPlanDiagnosticCode,
        CalculiXPlanSeverity,
        FEASpecCalculiXPlanDiagnostic,
    )
    from osw.experimental.feaspec.project_bridge import (
        BridgeStatus,
        FEASpecProjectExtensionNeed,
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        msg = "FEASpec CalculiX case-plan JSON must contain an object."
        raise ValueError(msg)

    diagnostics = tuple(
        FEASpecCalculiXPlanDiagnostic.make(
            CalculiXPlanDiagnosticCode(str(item.get("code", "FC_BRIDGE_BLOCKED"))),
            CalculiXPlanSeverity(str(item.get("severity", "blocker"))),
            str(item.get("message", "")),
            target_ref=str(item.get("target_ref", "")),
            source_field=str(item.get("source_field", "")),
            suggested_fix=str(item.get("suggested_fix", "")),
            blocks_case_plan=bool(item.get("blocks_case_plan", True)),
            blocks_solver_handoff=bool(item.get("blocks_solver_handoff", True)),
        )
        for item in _mapping_items(payload.get("diagnostics", ()))
    )
    extension_needs = tuple(
        FEASpecProjectExtensionNeed(
            source_field=str(item.get("source_field", "")),
            reason=str(item.get("reason", "")),
            suggested_target=str(item.get("suggested_target", "")),
            required_before_solver_handoff=bool(
                item.get("required_before_solver_handoff", False)
            ),
        )
        for item in _mapping_items(payload.get("extension_needs", ()))
    )
    bridge_status_text = str(payload.get("bridge_status", ""))
    bridge_status = BridgeStatus(bridge_status_text) if bridge_status_text else None

    return FEASpecCalculiXCasePlan(
        status=CalculiXCaseStatus(str(payload.get("status", "blocked"))),
        case_id=str(payload.get("case_id", "")),
        source_feaspec_id=str(payload.get("source_feaspec_id", "")),
        target_solver=str(payload.get("target_solver", "calculix")),
        unit_context=dict(_mapping_value(payload.get("unit_context", {}))),
        nodes=tuple(
            CalculiXCaseNodePlan(
                node_id=str(item.get("node_id", "")),
                coordinates=tuple(_sequence_value(item.get("coordinates", ()))),
                coordinate_frame=str(item.get("coordinate_frame", "")),
                source_ref=str(item.get("source_ref", "")),
                metadata=dict(_mapping_value(item.get("metadata", {}))),
            )
            for item in _mapping_items(payload.get("nodes", ()))
        ),
        elements=tuple(
            CalculiXCaseElementPlan(
                element_id=str(item.get("element_id", "")),
                element_type=str(item.get("element_type", "")),
                node_refs=tuple(str(ref) for ref in _sequence_value(item.get("node_refs", ()))),
                source_ref=str(item.get("source_ref", "")),
                metadata=dict(_mapping_value(item.get("metadata", {}))),
            )
            for item in _mapping_items(payload.get("elements", ()))
        ),
        materials=tuple(
            CalculiXCaseMaterialPlan(
                material_id=str(item.get("material_id", "")),
                name=str(item.get("name", "")),
                model=str(item.get("model", "")),
                properties=dict(_mapping_value(item.get("properties", {}))),
                units=dict(_mapping_value(item.get("units", {}))),
                source_ref=str(item.get("source_ref", "")),
                metadata=dict(_mapping_value(item.get("metadata", {}))),
            )
            for item in _mapping_items(payload.get("materials", ()))
        ),
        sections=tuple(
            CalculiXCaseSectionPlan(
                section_id=str(item.get("section_id", "")),
                material_ref=str(item.get("material_ref", "")),
                target_refs=tuple(
                    str(ref) for ref in _sequence_value(item.get("target_refs", ()))
                ),
                section_type=str(item.get("section_type", "")),
                properties=dict(_mapping_value(item.get("properties", {}))),
                units=dict(_mapping_value(item.get("units", {}))),
                source_ref=str(item.get("source_ref", "")),
                metadata=dict(_mapping_value(item.get("metadata", {}))),
            )
            for item in _mapping_items(payload.get("sections", ()))
        ),
        boundary_conditions=tuple(
            CalculiXCaseBoundaryConditionPlan(
                bc_id=str(item.get("bc_id", "")),
                kind=str(item.get("kind", "")),
                target_refs=tuple(
                    str(ref) for ref in _sequence_value(item.get("target_refs", ()))
                ),
                degrees_of_freedom=tuple(
                    str(ref) for ref in _sequence_value(item.get("degrees_of_freedom", ()))
                ),
                values=tuple(_sequence_value(item.get("values", ()))),
                units=dict(_mapping_value(item.get("units", {}))),
                coordinate_frame=str(item.get("coordinate_frame", "")),
                source_ref=str(item.get("source_ref", "")),
                metadata=dict(_mapping_value(item.get("metadata", {}))),
            )
            for item in _mapping_items(payload.get("boundary_conditions", ()))
        ),
        loads=tuple(
            CalculiXCaseLoadPlan(
                load_id=str(item.get("load_id", "")),
                kind=str(item.get("kind", "")),
                target_refs=tuple(
                    str(ref) for ref in _sequence_value(item.get("target_refs", ()))
                ),
                magnitude=dict(_mapping_value(item.get("magnitude", {}))),
                direction=str(item.get("direction", "")),
                vector=tuple(_sequence_value(item.get("vector", ()))),
                units=dict(_mapping_value(item.get("units", {}))),
                coordinate_frame=str(item.get("coordinate_frame", "")),
                source_ref=str(item.get("source_ref", "")),
                metadata=dict(_mapping_value(item.get("metadata", {}))),
            )
            for item in _mapping_items(payload.get("loads", ()))
        ),
        steps=tuple(
            CalculiXCaseStepPlan(
                step_id=str(item.get("step_id", "linear_static")),
                analysis_type=str(item.get("analysis_type", "static")),
                nonlinear=bool(item.get("nonlinear", False)),
                metadata=dict(_mapping_value(item.get("metadata", {}))),
            )
            for item in _mapping_items(payload.get("steps", ()))
        ),
        output_requests=tuple(
            CalculiXCaseOutputRequestPlan(
                request_id=str(item.get("request_id", "")),
                kind=str(item.get("kind", "field")),
                target=str(item.get("target", "all")),
                variables=tuple(str(ref) for ref in _sequence_value(item.get("variables", ()))),
                metadata=dict(_mapping_value(item.get("metadata", {}))),
            )
            for item in _mapping_items(payload.get("output_requests", ()))
        ),
        provenance_comments=tuple(
            str(item) for item in _sequence_value(payload.get("provenance_comments", ()))
        ),
        diagnostics=diagnostics,
        unmapped_fields=tuple(
            str(item) for item in _sequence_value(payload.get("unmapped_fields", ()))
        ),
        extension_needs=extension_needs,
        bridge_status=bridge_status,
        validator_report=dict(_mapping_value(payload.get("validator_report", {}))),
        ready_for_inp_writer=bool(payload.get("ready_for_inp_writer", False)),
        ready_for_solver_execution=False,
        inp_writer_performed=bool(payload.get("inp_writer_performed", False)),
        solver_execution_performed=False,
    )


def _mapping_value(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence_value(value: object) -> Sequence[Any]:
    if value is None or isinstance(value, str) or not isinstance(value, Sequence):
        return ()
    return value


def _mapping_items(value: object) -> list[Mapping[str, Any]]:
    return [item for item in _sequence_value(value) if isinstance(item, Mapping)]


def _feaspec_calculix_export_diagnostic_records(result: object) -> list[dict[str, object]]:
    records = _diagnostic_records("exporter", getattr(result, "diagnostics", ()))
    render_result = getattr(result, "render_result", None)
    if render_result is not None:
        records.extend(
            _diagnostic_records(
                "inp_renderer",
                getattr(render_result, "diagnostics", ()),
            )
        )
    return records


def _feaspec_calculix_export_write_limitations() -> list[str]:
    return [
        "No CalculiX solver execution was performed.",
        "External solvers are optional and not bundled.",
        "Issue #8 live CalculiX validation remains separate.",
        "The write command creates a local no-run bundle only.",
        "FEASpec CalculiX export remains experimental.",
    ]


def _print_feaspec_calculix_export_write(export_record: dict[str, object]) -> None:
    print("FEASpec CalculiX export write")
    print(f"Input: {export_record['input_path']}")
    print(f"Input kind: {export_record['input_kind']}")
    print(f"Output dir: {export_record['output_dir']}")
    print(f"Target solver: {export_record['target_solver']}")
    print(f"Export status: {export_record['export_status']}")
    print(f"Files written: {str(export_record['files_written']).lower()}")
    print("Solver execution performed: false")
    print("No solver execution was performed.")
    print("External solvers are optional and not bundled.")
    print("Issue #8 live CalculiX validation remains separate.")
    print("Written files:")
    written_files = export_record["written_files"]
    if written_files:
        for item in written_files:
            if isinstance(item, dict):
                print(f"  - {item['role']}: {item['path']}")
    else:
        print("  - none")
    print("Diagnostics:")
    diagnostics = export_record["diagnostics"]
    if diagnostics:
        for item in diagnostics:
            if not isinstance(item, dict):
                continue
            code = item.get("code", "diagnostic")
            severity = str(item.get("severity", "")).upper() or "INFO"
            source = item.get("source", "exporter")
            target = item.get("target_ref", item.get("path", ""))
            suffix = f" [{target}]" if target else ""
            print(f"  - {source}: {severity} {code}{suffix}: {item.get('message', '')}")
    else:
        print("  - none")
    print("Limitations:")
    for item in export_record["limitations"]:
        print(f"  - {item}")


def _run_feaspec_human_review_create(
    args: argparse.Namespace,
) -> tuple[dict[str, object], int]:
    from osw.experimental.feaspec.human_review import (
        create_human_review_record,
        validate_human_review_record,
    )
    from osw.experimental.feaspec.human_review_io import dump_human_review_record

    output_path = Path(args.output).expanduser()
    record = create_human_review_record(
        source_feaspec_id=args.source_feaspec_id,
        reviewer=args.reviewer,
        reviewed_at=args.reviewed_at,
        action=_feaspec_human_review_action(args.action),
        notes=tuple(args.notes or ()),
        accepted_warnings=tuple(
            _human_review_warning_from_cli(item) for item in args.accept_warning
        ),
        diagnostic_decisions=tuple(
            _human_review_rejected_diagnostic_from_cli(item)
            for item in args.reject_diagnostic
        ),
        validator_report_summary=_load_human_review_mapping_arg(
            args.validator_summary,
            "validator-summary",
        ),
        validator_report_hash=args.validator_report_hash,
        bridge_summary=_load_human_review_mapping_arg(args.bridge_summary, "bridge-summary"),
        case_plan_summary=_load_human_review_mapping_arg(
            args.case_plan_summary,
            "case-plan-summary",
        ),
        export_preview_summary=_load_human_review_mapping_arg(
            args.export_preview_summary,
            "export-preview-summary",
        ),
        export_write_summary=_load_human_review_mapping_arg(
            args.export_write_summary,
            "export-write-summary",
        ),
        limitations_acknowledged=args.acknowledge_limitations,
        no_run_export_review_acknowledged=args.acknowledge_readme,
        run_gate_separation_acknowledged=args.acknowledge_run_gate_separate,
        provenance={
            "created_by": "feaspec-human-review-create",
            "solver_execution_performed": False,
        },
    )
    validation = validate_human_review_record(record)
    payload = _human_review_record_payload(
        command="feaspec-human-review-create",
        status="validation-blocked" if not validation.is_valid else "ready-to-write",
        record_path=output_path,
        record=record,
        validation=validation,
        files_written=False,
    )
    if not validation.is_valid:
        return payload, 2

    dump_human_review_record(record, output_path, overwrite=args.overwrite)
    return (
        _human_review_record_payload(
            command="feaspec-human-review-create",
            status="written",
            record_path=output_path,
            record=record,
            validation=validation,
            files_written=True,
        ),
        0,
    )


def _run_feaspec_human_review_validate(
    record_path: Path,
) -> tuple[dict[str, object], int]:
    from osw.experimental.feaspec.human_review import validate_human_review_record
    from osw.experimental.feaspec.human_review_io import load_human_review_record

    source = record_path.expanduser()
    record = load_human_review_record(source)
    validation = validate_human_review_record(record)
    status = "valid" if validation.is_valid else "invalid"
    return (
        _human_review_record_payload(
            command="feaspec-human-review-validate",
            status=status,
            record_path=source,
            record=record,
            validation=validation,
            files_written=False,
        ),
        0 if validation.is_valid else 2,
    )


def _run_feaspec_human_review_summary(record_path: Path) -> dict[str, object]:
    from osw.experimental.feaspec.human_review import validate_human_review_record
    from osw.experimental.feaspec.human_review_io import load_human_review_record

    source = record_path.expanduser()
    record = load_human_review_record(source)
    validation = validate_human_review_record(record)
    return _human_review_record_payload(
        command="feaspec-human-review-summary",
        status="summary",
        record_path=source,
        record=record,
        validation=validation,
        files_written=False,
    )


def _feaspec_human_review_action(action: str) -> str:
    mapping = {
        "needs-changes": "mark_needs_changes",
        "reject": "reject",
        "approve-no-run-export": "approve_no_run_export",
        "request-installed-only-run": "request_installed_only_run",
    }
    return mapping[action]


def _human_review_warning_from_cli(value: str) -> object:
    from osw.experimental.feaspec.human_review import (
        AcceptedWarning,
        ReviewDiagnosticReference,
    )

    code, reason = _split_human_review_code_reason(value)
    return AcceptedWarning(
        diagnostic=ReviewDiagnosticReference(code=code, severity="warning"),
        reason=reason,
    )


def _human_review_rejected_diagnostic_from_cli(value: str) -> object:
    from osw.experimental.feaspec.human_review import (
        DiagnosticDecision,
        HumanReviewAction,
        ReviewDiagnosticReference,
    )

    code, reason = _split_human_review_code_reason(value)
    return DiagnosticDecision(
        diagnostic=ReviewDiagnosticReference(
            code=code,
            severity="error",
            blocks_approval=True,
            blocks_solver_handoff=True,
        ),
        action=HumanReviewAction.REJECT_DIAGNOSTIC,
        reason=reason,
    )


def _split_human_review_code_reason(value: str) -> tuple[str, str]:
    code, separator, reason = value.partition(":")
    if not code.strip():
        msg = "Diagnostic code is required."
        raise ValueError(msg)
    return code.strip(), reason.strip() if separator else ""


def _load_human_review_mapping_arg(value: str, label: str) -> dict[str, Any]:
    if not value:
        return {}
    source = Path(value).expanduser()
    if source.is_file():
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            msg = f"{label} JSON path is invalid: {source}"
            raise ValueError(msg) from exc
    else:
        try:
            payload = json.loads(value)
        except json.JSONDecodeError as exc:
            msg = f"{label} must be an existing JSON file path or inline JSON object."
            raise ValueError(msg) from exc
    if not isinstance(payload, Mapping):
        msg = f"{label} must resolve to a JSON object."
        raise ValueError(msg)
    return dict(payload)


def _human_review_record_payload(
    *,
    command: str,
    status: str,
    record_path: Path,
    record: object,
    validation: object,
    files_written: bool,
) -> dict[str, object]:
    summary = _human_review_summary_dict(record)
    return {
        "command": command,
        "status": status,
        "valid": bool(getattr(validation, "is_valid", False)),
        "record_path": str(record_path),
        "source_feaspec_id": summary["source_feaspec_id"],
        "reviewer": summary["reviewer"],
        "reviewed_at": summary["reviewed_at"],
        "state": summary["state"],
        "action": summary["action"],
        "solver_execution_performed": False,
        "solver_execution_authorized": summary["solver_execution_authorized"],
        "files_written": files_written,
        "diagnostics": _human_review_validation_diagnostics(validation),
        "limitations": _feaspec_human_review_limitations(record),
    }


def _human_review_summary_dict(record: object) -> dict[str, object]:
    from osw.experimental.feaspec.human_review import summarize_human_review_record

    return summarize_human_review_record(record).to_dict()


def _human_review_validation_diagnostics(validation: object) -> list[dict[str, str]]:
    errors = getattr(validation, "errors", ()) or ()
    warnings = getattr(validation, "warnings", ()) or ()
    return [
        {"severity": "error", "message": str(item)}
        for item in errors
    ] + [
        {"severity": "warning", "message": str(item)}
        for item in warnings
    ]


def _feaspec_human_review_limitations(record: object) -> list[str]:
    raw_state = getattr(record, "state", "")
    state = str(getattr(raw_state, "value", raw_state))
    return [
        "No solver execution was performed.",
        "Run gate remains separate.",
        "No-run export remains separate.",
        "Result import remains separate.",
        "External solvers are optional and not bundled.",
        "Issue #8 live CalculiX validation remains separate.",
        f"Review state: {state}.",
    ]


def _print_feaspec_human_review_payload(payload: dict[str, object]) -> None:
    print("FEASpec human review")
    print(f"Command: {payload['command']}")
    print(f"Status: {payload['status']}")
    print(f"Record: {payload['record_path']}")
    print(f"Valid: {str(payload['valid']).lower()}")
    print(f"Source FEASpec: {payload['source_feaspec_id']}")
    print(f"Reviewer: {payload['reviewer']}")
    print(f"Reviewed at: {payload['reviewed_at']}")
    print(f"State: {payload['state']}")
    print(f"Action: {payload['action']}")
    print(
        "Solver execution authorized: "
        f"{str(payload['solver_execution_authorized']).lower()}"
    )
    print("Solver execution performed: false")
    print(f"Files written: {str(payload['files_written']).lower()}")
    print("No solver execution was performed.")
    print("Run gate remains separate.")
    print("No-run export remains separate.")
    print("Result import remains separate.")
    print("External solvers are optional and not bundled.")
    print("Issue #8 live CalculiX validation remains separate.")
    print("Diagnostics:")
    diagnostics = payload["diagnostics"]
    if diagnostics:
        for item in diagnostics:
            if isinstance(item, Mapping):
                severity = str(item.get("severity", "info")).upper()
                print(f"  - {severity}: {item.get('message', '')}")
    else:
        print("  - none")
    print("Limitations:")
    for item in payload["limitations"]:
        print(f"  - {item}")


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
    from osw.post.field_view_model import field_view_model_from_result_dataset
    from osw.post.result_view_model import (
        result_dataset_summary,
        result_dataset_to_view_model,
        summarize_result_dataset_for_view,
    )

    summary = result_dataset_summary(dataset)
    view_model = result_dataset_to_view_model(dataset)
    field_view_model = field_view_model_from_result_dataset(dataset)
    details = summarize_result_dataset_for_view(
        dataset,
        field_count=len(field_view_model.arrays),
    )
    print(f"ResultDataset: {summary.dataset_id}")
    print(f"Title: {summary.title}")
    print(f"Kind: {summary.kind}")
    print(f"Source kind: {details.source_kind}")
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
    print(f"Field arrays: {details.field_count}")
    print("Viewer handoff:")
    for hint in details.handoff_hints:
        print(f"  - {hint}")
    print("Limitations:")
    for limitation in details.limitations:
        print(f"  - {limitation}")
    for artifact in view_model.artifacts:
        state = "exists" if artifact.exists else "missing"
        print(f"  - {artifact.role}: {artifact.path} [{state}]")
    if view_model.diagnostics:
        print("Diagnostics:", file=sys.stderr)
        for diagnostic in view_model.diagnostics:
            print(f"  - {diagnostic}", file=sys.stderr)


def _print_result_catalog_summary(catalog: object) -> None:
    from osw.post.result_view_model import result_dataset_summary, summarize_result_catalog_for_view

    datasets = tuple(getattr(catalog, "datasets", ()) or ())
    catalog_summary = summarize_result_catalog_for_view(catalog)
    print(f"ResultCatalog: {getattr(catalog, 'catalog_id', '')}")
    print(f"Project: {getattr(catalog, 'project_name', '') or 'Not recorded'}")
    print(f"Datasets: {len(datasets)}")
    kind_counts = ", ".join(
        f"{kind}: {count}" for kind, count in catalog_summary.kind_counts
    )
    print(f"Dataset types: {kind_counts or 'none'}")
    selected = getattr(catalog, "selected_dataset_id", "")
    if selected:
        print(f"Selected: {selected}")
    print(f"Sources: {catalog_summary.source_summary}")
    print(f"Diagnostics: {catalog_summary.diagnostics_count}")
    for dataset in datasets:
        summary = result_dataset_summary(dataset)
        print(
            f"- {summary.dataset_id}: {summary.title} "
            f"({summary.kind}, {summary.scalar_count} scalar(s), "
            f"{summary.series_count} series)"
        )


def _print_field_view_model(view_model: object, *, artifact_heading: bool = False) -> None:
    from osw.post.field_view_model import summarize_field_dataset_for_view

    workflow = summarize_field_dataset_for_view(view_model)
    title = getattr(view_model, "title", "") or getattr(view_model, "dataset_id", "")
    print(("Field artifacts" if artifact_heading else "Field Dataset") + f": {title}")
    print(f"Dataset: {getattr(view_model, 'dataset_id', '')}")
    print(f"Source: {getattr(view_model, 'source', '') or 'Not recorded'}")
    print(f"PyVista: {workflow.pyvista_state} (optional)")
    print(f"Fallback: {workflow.fallback_reason}")
    scalar_fields = tuple(getattr(view_model, "scalar_fields", ()) or ())
    vector_fields = tuple(getattr(view_model, "vector_fields", ()) or ())
    print("Scalar fields: " + (", ".join(scalar_fields) or "none"))
    print("Vector fields: " + (", ".join(vector_fields) or "none"))
    arrays = tuple(getattr(view_model, "arrays", ()) or ())
    print(f"Field arrays: {len(arrays)}")
    for array in arrays:
        components = ", ".join(getattr(array, "components", ()) or ())
        print(
            f"  - {array.name} ({array.location}, {array.field_type}, "
            f"{components or 'no components'}, {array.value_count} value(s))"
        )
    artifacts = tuple(getattr(view_model, "artifacts", ()) or ())
    print(f"Artifacts: {len(artifacts)}")
    for artifact in artifacts:
        state = "exists" if artifact.exists else "missing"
        print(f"  - {artifact.path} [{artifact.format or 'unknown'}, {state}]")
    diagnostics = tuple(getattr(view_model, "diagnostics", ()) or ())
    if diagnostics:
        print("Diagnostics:", file=sys.stderr)
        for diagnostic in diagnostics:
            print(f"  - {diagnostic}", file=sys.stderr)
    print("Limitations:")
    for limitation in workflow.limitations:
        print(f"  - {limitation}")


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
