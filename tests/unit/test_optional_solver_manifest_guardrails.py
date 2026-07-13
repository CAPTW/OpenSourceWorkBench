from __future__ import annotations

import ast
from pathlib import Path

import pytest

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
SUBPROCESS_CALLS = {
    "Popen",
    "call",
    "check_call",
    "check_output",
    "getoutput",
    "getstatusoutput",
    "run",
}
OS_PROCESS_CALLS = {"popen", "startfile", "system"}


def _source_files() -> list[Path]:
    return sorted(PACKAGE.glob("*.py"))


def _schema_source_files() -> list[Path]:
    return [
        path
        for path in _source_files()
        if not path.name.startswith("discovery_")
    ]


def _dotted_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _literal_import_target(node: ast.Call) -> str | None:
    if not node.args:
        return None
    target = node.args[0]
    if isinstance(target, ast.Constant) and isinstance(target.value, str):
        return target.value
    return None


def _is_os_process_call(name: str) -> bool:
    return name in OS_PROCESS_CALLS or name.startswith(("exec", "spawn"))


def _process_execution_violations(source: str) -> tuple[str, ...]:
    tree = ast.parse(source)
    subprocess_modules = {"subprocess"}
    subprocess_functions: set[str] = set()
    os_modules = {"os"}
    os_process_functions: set[str] = set()
    importlib_modules = {"importlib"}
    import_module_functions: set[str] = set()
    runner_modules = {"osw.solvers.runner"}
    runner_types = {"ExternalCommandRunner"}
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname or alias.name
                if alias.name == "subprocess":
                    subprocess_modules.add(local_name)
                    violations.append(f"line {node.lineno}: import subprocess")
                elif alias.name == "os":
                    os_modules.add(local_name)
                elif alias.name == "importlib":
                    importlib_modules.add(local_name)
                elif alias.name == "osw.solvers.runner":
                    runner_modules.add(local_name)
                    violations.append(f"line {node.lineno}: import external runner")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                local_name = alias.asname or alias.name
                if module == "subprocess":
                    subprocess_functions.add(local_name)
                    violations.append(f"line {node.lineno}: from subprocess import")
                elif module == "os" and _is_os_process_call(alias.name):
                    os_process_functions.add(local_name)
                    violations.append(f"line {node.lineno}: from os import process function")
                elif module == "importlib" and alias.name == "import_module":
                    import_module_functions.add(local_name)
                elif module == "osw.solvers.runner" or (
                    module == "osw.solvers" and alias.name == "runner"
                ):
                    runner_types.add(local_name)
                    violations.append(f"line {node.lineno}: import external runner")
                elif alias.name == "ExternalCommandRunner":
                    runner_types.add(local_name)
                    violations.append(f"line {node.lineno}: import ExternalCommandRunner")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        call_name = _dotted_name(node.func)
        target = _literal_import_target(node)
        if call_name == "__import__" and target in {"subprocess", "osw.solvers.runner"}:
            violations.append(f"line {node.lineno}: dynamic process-boundary import")
        if (
            call_name in import_module_functions
            or any(call_name == f"{module}.import_module" for module in importlib_modules)
        ) and target in {"subprocess", "osw.solvers.runner"}:
            violations.append(f"line {node.lineno}: dynamic process-boundary import")
        if call_name in subprocess_functions:
            violations.append(f"line {node.lineno}: subprocess function call")
        for module in subprocess_modules:
            if call_name in {f"{module}.{member}" for member in SUBPROCESS_CALLS}:
                violations.append(f"line {node.lineno}: subprocess call")
        if call_name in os_process_functions:
            violations.append(f"line {node.lineno}: os process call")
        for module in os_modules:
            prefix = f"{module}."
            if call_name.startswith(prefix) and _is_os_process_call(call_name[len(prefix) :]):
                violations.append(f"line {node.lineno}: os process call")
        if call_name in runner_types or call_name.endswith(".ExternalCommandRunner"):
            violations.append(f"line {node.lineno}: ExternalCommandRunner invocation")
        if any(call_name.startswith(f"{module}.") for module in runner_modules):
            violations.append(f"line {node.lineno}: external runner invocation")
    return tuple(violations)


def test_optional_solver_manifest_package_uses_no_subprocess() -> None:
    for path in _source_files():
        text = path.read_text(encoding="utf-8")
        assert not _process_execution_violations(text), path


@pytest.mark.parametrize(
    "source",
    (
        "import subprocess\nsubprocess.run(['tool'])",
        "from subprocess import Popen\nPopen(['tool'])",
        "__import__('subprocess')",
        "import importlib\nimportlib.import_module('subprocess')",
        "import os\nos.system('tool')",
        "import os as host_os\nhost_os.spawnv(0, 'tool', ())",
        "from os import popen as open_process\nopen_process('tool')",
        "from osw.solvers.runner import ExternalCommandRunner\nExternalCommandRunner()",
    ),
)
def test_subprocess_guard_detects_process_execution_semantics(source: str) -> None:
    assert _process_execution_violations(source)


def test_subprocess_guard_allows_non_action_field_names() -> None:
    source = '''
from dataclasses import dataclass

@dataclass
class Audit:
    subprocess_used: bool = False

payload = {"cli_subprocess_used": False}
note = "subprocess execution is forbidden"
'''

    assert _process_execution_violations(source) == ()


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
