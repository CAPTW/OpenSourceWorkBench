#!/usr/bin/env python3
"""Check OSW architecture boundaries that can be verified statically."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

from _common import repo_root


GUI_FORBIDDEN_IMPORTS = {"subprocess", "osw.solvers"}
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    root = repo_root()
    failures: list[str] = []

    for path in (root / "src" / "osw" / "gui").rglob("*.py"):
        found = contains_forbidden(imported_names(path), GUI_FORBIDDEN_IMPORTS)
        for item in sorted(found):
            failures.append(f"{path.relative_to(root)} imports forbidden GUI dependency {item}")

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
