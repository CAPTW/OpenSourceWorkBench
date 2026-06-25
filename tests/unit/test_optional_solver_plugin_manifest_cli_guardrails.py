from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path

from osw.cli.main import build_parser

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_MAIN = REPO_ROOT / "src" / "osw" / "cli" / "main.py"
COMMAND = "optional-solver-plugin-manifest-preview"
cli_module = importlib.import_module("osw.cli.main")
OPTIONAL_IMPORT_NAMES = {
    "gmsh",
    "meshio",
    "pyvista",
    "vtk",
    "CoolProp",
    "cantera",
}
FORBIDDEN_OPTIONS = {
    "--scan-dir",
    "--plugin-package",
    "--fetch",
    "--install",
    "--run-smoke",
    "--execute",
    "--close-issue",
}


def _command_options() -> set[str]:
    parser = build_parser()
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict):
            command_parser = choices[COMMAND]
            return {
                option
                for command_action in command_parser._actions
                for option in command_action.option_strings
            }
    return set()


def test_plugin_manifest_preview_command_has_no_forbidden_options() -> None:
    options = _command_options()

    assert "--manifest" in options
    assert "--format" in options
    assert options.isdisjoint(FORBIDDEN_OPTIONS)


def test_plugin_manifest_preview_help_has_no_forbidden_options(capsys) -> None:
    parser = build_parser()

    try:
        parser.parse_args([COMMAND, "--help"])
    except SystemExit as exc:
        assert exc.code == 0

    output = capsys.readouterr().out
    for option in FORBIDDEN_OPTIONS:
        assert option not in output


def test_plugin_manifest_cli_helpers_do_not_use_forbidden_runtime_words() -> None:
    helpers = (
        cli_module._optional_solver_plugin_manifest_preview_report,
        cli_module._optional_solver_plugin_manifest_preview_payload,
        cli_module._format_optional_solver_plugin_manifest_preview_text,
    )
    for helper in helpers:
        source = inspect.getsource(helper)
        for forbidden in ("os.system", "Popen", "check_call", "check_output"):
            assert forbidden not in source


def test_plugin_manifest_cli_imports_no_optional_solver_packages() -> None:
    tree = ast.parse(CLI_MAIN.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(OPTIONAL_IMPORT_NAMES)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in OPTIONAL_IMPORT_NAMES
