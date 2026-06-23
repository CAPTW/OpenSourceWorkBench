from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE = REPO_ROOT / "src" / "osw" / "experimental" / "optional_solvers"
DISCOVERY_FILES = (
    PACKAGE / "discovery_models.py",
    PACKAGE / "discovery_service.py",
)
OPTIONAL_IMPORT_NAMES = {
    "gmsh",
    "meshio",
    "pyvista",
    "vtk",
    "CoolProp",
    "cantera",
}
INSTALLER_COMMAND_PHRASES = (
    "pip install",
    "conda install",
    "apt install",
    "apt-get install",
    "choco install",
    "winget install",
    "brew install",
    "sudo ",
    "curl ",
    "wget ",
)


def test_discovery_source_uses_no_command_process_module() -> None:
    for path in DISCOVERY_FILES:
        assert "subprocess" not in path.read_text(encoding="utf-8")


def test_discovery_source_imports_no_optional_solver_packages() -> None:
    for path in DISCOVERY_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name.split(".")[0] for alias in node.names}
                assert imported.isdisjoint(OPTIONAL_IMPORT_NAMES)
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in OPTIONAL_IMPORT_NAMES


def test_discovery_source_does_not_include_installer_commands() -> None:
    for path in DISCOVERY_FILES:
        text = path.read_text(encoding="utf-8").lower()
        for phrase in INSTALLER_COMMAND_PHRASES:
            assert phrase not in text


def test_shutil_which_is_limited_to_discovery_service_default_resolver() -> None:
    source = (PACKAGE / "discovery_service.py").read_text(encoding="utf-8")

    assert "shutil.which(name)" in source
    assert "from shutil import which" not in source
    for path in PACKAGE.glob("*.py"):
        if path.name == "discovery_service.py":
            continue
        text = path.read_text(encoding="utf-8")
        assert "shutil.which" not in text
        assert "from shutil import which" not in text
