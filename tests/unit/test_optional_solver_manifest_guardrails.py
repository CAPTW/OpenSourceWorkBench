from __future__ import annotations

import ast
from pathlib import Path

from osw.experimental.optional_solvers import (
    parse_optional_solver_manifest_dict,
    validate_optional_solver_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE = REPO_ROOT / "src" / "osw" / "experimental" / "optional_solvers"
OPTIONAL_IMPORT_NAMES = {
    "gmsh",
    "meshio",
    "pyvista",
    "vtk",
    "CoolProp",
    "cantera",
}


def _source_files() -> list[Path]:
    return sorted(PACKAGE.glob("*.py"))


def _schema_source_files() -> list[Path]:
    return [
        path
        for path in _source_files()
        if not path.name.startswith("discovery_")
    ]


def test_optional_solver_manifest_package_uses_no_subprocess() -> None:
    for path in _source_files():
        text = path.read_text(encoding="utf-8")
        assert "subprocess" not in text


def test_optional_solver_manifest_package_uses_no_shutil_which() -> None:
    for path in _schema_source_files():
        text = path.read_text(encoding="utf-8")
        assert "shutil.which" not in text
        assert "from shutil import which" not in text


def test_optional_solver_manifest_package_imports_no_optional_solver_packages() -> None:
    for path in _source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name.split(".")[0] for alias in node.names}
                assert imported.isdisjoint(OPTIONAL_IMPORT_NAMES)
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in OPTIONAL_IMPORT_NAMES


def test_probe_declarations_are_not_executed_by_validation() -> None:
    manifest = parse_optional_solver_manifest_dict(
        {
            "stack_id": "example",
            "display_name": "Example",
            "related_issue": 6,
            "capabilities": ["example"],
            "executable_requirements": ["definitely-not-a-real-command"],
            "version_probe": {
                "name": "impossible probe",
                "command": ["definitely-not-a-real-command", "--version"],
            },
            "smoke_test_description": "Declarative smoke.",
            "prepared_machine_notes": ["Prepared only."],
            "documentation_refs": ["docs/example.md"],
            "support_status": "experimental",
            "non_bundled_disclaimer": "External solvers are not bundled.",
            "safety_notes": [
                "No solver install.",
                "No dependency install.",
                "No bundled solver.",
            ],
        }
    )

    report = validate_optional_solver_manifest(manifest)

    assert report.is_valid
