#!/usr/bin/env python3
"""Check OSW architecture boundaries that can be verified statically."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

from _common import repo_root

GUI_FORBIDDEN_IMPORTS = {"subprocess", "osw.solvers"}
GUI_FORBIDDEN_DYNAMIC_IMPORTS = {
    "osw.solvers.calculix.runner",
    "osw.solvers.openfoam.runner",
    "osw.solvers.runner",
    "osw.scripts.mscript.octave_runner",
}
GUI_FORBIDDEN_CALL_NAMES = {
    "CalculiXRunner",
    "ExternalCommandRunner",
    "OctaveRunner",
    "OpenFOAMRunner",
    "Popen",
    "QProcess",
    "RunManager",
}
GUI_FORBIDDEN_CALL_ATTRS = {"run_case", "run_command", "run_input_deck"}
CORE_FORBIDDEN_IMPORTS = {"PySide6", "pyvista", "gmsh", "meshio", "cantera", "CoolProp"}


def imported_names(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return set()

    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def contains_forbidden(imports: set[str], forbidden: set[str]) -> set[str]:
    found: set[str] = set()
    for item in imports:
        for banned in forbidden:
            if item == banned or item.startswith(f"{banned}."):
                found.add(item)
    return found


def gui_boundary_violations(path: Path) -> list[str]:
    """Return static GUI runner-boundary violations for one Python file."""

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return []

    violations: list[str] = []
    for item in sorted(contains_forbidden(imported_names(path), GUI_FORBIDDEN_IMPORTS)):
        violations.append(f"imports forbidden GUI dependency {item}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name in GUI_FORBIDDEN_CALL_NAMES:
                violations.append(
                    f"line {node.lineno} calls forbidden GUI runner/external process {call_name}"
                )
            if isinstance(node.func, ast.Attribute) and node.func.attr in GUI_FORBIDDEN_CALL_ATTRS:
                violations.append(
                    f"line {node.lineno} calls forbidden GUI runner method {node.func.attr}"
                )
            if _is_forbidden_dynamic_import(node):
                target = _first_string_arg(node)
                violations.append(
                    f"line {node.lineno} dynamically imports forbidden GUI runner {target}"
                )
    return violations


def _call_name(func: ast.expr) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _first_string_arg(node: ast.Call) -> str:
    if not node.args:
        return ""
    first = node.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return ""


def _is_forbidden_dynamic_import(node: ast.Call) -> bool:
    call_name = _call_name(node.func)
    if call_name not in {"import_module", "__import__"}:
        return False
    target = _first_string_arg(node)
    return any(
        target == banned or target.startswith(f"{banned}.")
        for banned in GUI_FORBIDDEN_DYNAMIC_IMPORTS
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    root = repo_root()
    failures: list[str] = []

    for path in (root / "src" / "osw" / "gui").rglob("*.py"):
        for violation in gui_boundary_violations(path):
            failures.append(f"{path.relative_to(root)} {violation}")

    for path in (root / "src" / "osw" / "core").rglob("*.py"):
        found = contains_forbidden(imported_names(path), CORE_FORBIDDEN_IMPORTS)
        for item in sorted(found):
            failures.append(f"{path.relative_to(root)} imports optional/heavy dependency {item}")

    if failures:
        print("[fail] Architecture boundary violations:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("[ok] Architecture boundaries respected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
