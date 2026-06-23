from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path

from osw.cli.main import build_parser

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_MAIN = REPO_ROOT / "src" / "osw" / "cli" / "main.py"
cli_module = importlib.import_module("osw.cli.main")
OPTIONAL_IMPORT_NAMES = {
    "gmsh",
    "meshio",
    "pyvista",
    "vtk",
    "CoolProp",
    "cantera",
}


def _optional_solver_command_options(command: str) -> set[str]:
    parser = build_parser()
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict):
            command_parser = choices[command]
            return {
                option
                for command_action in command_parser._actions
                for option in command_action.option_strings
            }
    return set()


def test_optional_solver_commands_have_no_install_or_smoke_options() -> None:
    for command in (
        "optional-solver-list",
        "optional-solver-doctor",
        "optional-solver-explain",
    ):
        options = _optional_solver_command_options(command)
        assert "--install" not in options
        assert "--run-smoke" not in options
        assert "--execute" not in options


def test_optional_solver_cli_helpers_do_not_use_command_process_module() -> None:
    helpers = (
        cli_module._optional_solver_manifest_summary,
        cli_module._format_optional_solver_list_text,
        cli_module._select_optional_solver_manifests,
        cli_module._optional_solver_doctor_report,
        cli_module._format_optional_solver_doctor_text,
        cli_module._format_optional_solver_explain_text,
        cli_module._optional_solver_explain_payload,
    )
    for helper in helpers:
        assert "subprocess" not in inspect.getsource(helper)


def test_optional_solver_cli_imports_no_optional_solver_packages() -> None:
    tree = ast.parse(CLI_MAIN.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(OPTIONAL_IMPORT_NAMES)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in OPTIONAL_IMPORT_NAMES
