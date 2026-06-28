from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

import pytest

from osw.cli.main import main
from osw.cli.optional_solver_manifest_persistence import (
    OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_COMMAND,
)

COMMAND = OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_COMMAND
MODULE_NAME = "osw.cli.optional_solver_manifest_persistence"


def _run(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main([COMMAND, *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _module_source() -> str:
    module = importlib.import_module(MODULE_NAME)
    return Path(module.__file__).read_text(encoding="utf-8")


def _imported_modules() -> set[str]:
    tree = ast.parse(_module_source())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return {module.lower() for module in modules}


def _flatten(value: object) -> list[object]:
    if isinstance(value, dict):
        items: list[object] = []
        for child in value.values():
            items.extend(_flatten(child))
        return items
    if isinstance(value, list):
        items = []
        for child in value:
            items.extend(_flatten(child))
        return items
    return [value]


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_cli_module_imports_without_gui_extras() -> None:
    module = importlib.import_module(MODULE_NAME)
    assert hasattr(module, "run_optional_solver_plugin_manifest_persistence_cli")
    for imported in _imported_modules():
        assert "pyside" not in imported
        assert "pyqt" not in imported
        assert not imported.startswith("qt")


def test_cli_module_avoids_forbidden_integration_imports() -> None:
    forbidden_roots = {
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "http",
        "shutil",
        "gmsh",
        "meshio",
        "pyvista",
        "vtk",
        "coolprop",
        "cantera",
    }
    for imported in _imported_modules():
        assert imported.split(".", 1)[0] not in forbidden_roots, imported
        assert not imported.startswith("osw.gui")
        assert not imported.startswith("osw.plugins")
        assert not imported.startswith("osw.solvers")
        assert not imported.startswith("osw.core")


def test_cli_source_has_no_discovery_validation_solver_or_release_calls() -> None:
    source = _module_source()
    for phrase in (
        "discover_optional_solver_manifests",
        "discover_local_plugin_manifests",
        "load_optional_solver_plugin_manifest_json",
        "run_discovery(",
        "run_validation(",
        "execute_solver(",
        "pip install",
        "pip uninstall",
        "gh issue",
        "gh release",
        "subprocess",
        "requests.",
        "urllib",
    ):
        assert phrase not in source, phrase


def test_explain_command_succeeds_and_states_boundaries(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["explain", "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    for phrase in (
        "Persisted state is not validation evidence.",
        "Persisted state is not trust restoration.",
        "Persisted state is not automatic activation.",
        "No discovery execution.",
        "No plugin package import.",
        "No solver execution.",
        "No issue closure.",
        "No release mutation.",
        "A trust label is not certification.",
        "User/plugin manifests remain untrusted by default.",
    ):
        assert phrase in out


@pytest.mark.parametrize(
    "subcommand",
    ["plan", "schema", "acknowledgements", "diagnostics", "actions"],
)
def test_review_commands_succeed(
    subcommand: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run([subcommand, "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    assert "Optional Solver Plugin Manifest Persistence CLI" in out


def test_write_without_output_path_is_blocked(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["write", "--sample-state"], capsys)
    assert code == 2
    assert out == ""
    assert "OSPMG_STATE_WRITER_TARGET_REQUIRED" in err
    assert "status: unavailable" in err


def test_write_without_write_flag_is_dry_run_and_does_not_write(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"
    code, out, err = _run(["write", "--sample-state", "--output", str(target)], capsys)
    assert code == 0
    assert err == ""
    assert target.exists() is False
    assert "mode: dry-run" in out
    assert "OSPMG_STATE_WRITER_WRITE_PLANNED" in out
    assert "file write performed: False" in out


def test_write_without_acknowledgement_is_blocked(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"
    code, out, err = _run(
        ["write", "--sample-state", "--output", str(target), "--write"],
        capsys,
    )
    assert code == 2
    assert out == ""
    assert target.exists() is False
    assert "OSPMG_STATE_WRITER_CALLER_ACK_REQUIRED" in err
    assert "OSPMG_STATE_WRITER_WRITE_BLOCKED" in err


def test_write_with_unavailable_state_is_blocked(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"
    code, out, err = _run(
        [
            "write",
            "--unavailable-state",
            "--output",
            str(target),
            "--write",
            "--acknowledge-state-write",
        ],
        capsys,
    )
    assert code == 2
    assert out == ""
    assert target.exists() is False
    assert "OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY" in err


def test_explicit_acknowledged_write_creates_one_tmp_path_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"
    before = set(tmp_path.iterdir())
    code, out, err = _run(
        [
            "write",
            "--sample-state",
            "--output",
            str(target),
            "--write",
            "--acknowledge-state-write",
        ],
        capsys,
    )
    after = set(tmp_path.iterdir())
    assert code == 0
    assert err == ""
    assert after - before == {target}
    payload = _load_json(target)
    assert payload["payload_kind"] == "optional_solver_plugin_manifest_state_writer_state"
    assert "safety_boundary" in payload
    assert "OSPMG_STATE_WRITER_WRITE_COMPLETED" in out
    assert "file write performed: True" in out


def test_written_file_preserves_safety_non_action_flags(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"
    code, _out, err = _run(
        [
            "write",
            "--sample-state",
            "--output",
            str(target),
            "--write",
            "--acknowledge-state-write",
        ],
        capsys,
    )
    assert code == 0
    assert err == ""
    payload = _load_json(target)
    flattened = _flatten(payload)
    assert "Persisted state is not validation evidence." in flattened
    assert True not in [
        payload.get("summary", {}).get("validation_success_claimed"),
        payload.get("summary", {}).get("validation_failure_claimed"),
        payload.get("summary", {}).get("issue_closure_claimed"),
        payload.get("summary", {}).get("certification_claimed"),
    ]
    assert payload["non_action_flags"]["validation_execution_performed"] is False
    assert payload["non_action_flags"]["solver_execution_performed"] is False
    assert payload["non_action_flags"]["project_schema_mutation_performed"] is False


def test_existing_target_requires_allow_replace(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"
    target.write_text("existing", encoding="utf-8")
    code, out, err = _run(
        [
            "write",
            "--sample-state",
            "--output",
            str(target),
            "--write",
            "--acknowledge-state-write",
        ],
        capsys,
    )
    assert code == 2
    assert out == ""
    assert target.read_text(encoding="utf-8") == "existing"
    assert "OSPMG_STATE_WRITER_TARGET_EXISTS" in err

    code, out, err = _run(
        [
            "write",
            "--sample-state",
            "--output",
            str(target),
            "--write",
            "--acknowledge-state-write",
            "--allow-replace",
        ],
        capsys,
    )
    assert code == 0
    assert err == ""
    assert "OSPMG_STATE_WRITER_WRITE_COMPLETED" in out
    assert _load_json(target)["payload_kind"] == (
        "optional_solver_plugin_manifest_state_writer_state"
    )


def test_missing_parent_is_blocked_and_not_created(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing_parent = tmp_path / "missing"
    target = missing_parent / "state.json"
    code, out, err = _run(
        [
            "write",
            "--sample-state",
            "--output",
            str(target),
            "--write",
            "--acknowledge-state-write",
        ],
        capsys,
    )
    assert code == 2
    assert out == ""
    assert missing_parent.exists() is False
    assert "OSPMG_STATE_WRITER_PARENT_MISSING" in err


def test_directory_target_is_blocked(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(
        [
            "write",
            "--sample-state",
            "--output",
            str(tmp_path),
            "--write",
            "--acknowledge-state-write",
        ],
        capsys,
    )
    assert code == 2
    assert out == ""
    assert "OSPMG_STATE_WRITER_TARGET_DIRECTORY_BLOCKED" in err


def test_symlink_target_is_blocked_when_supported(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    real_target = tmp_path / "real.json"
    real_target.write_text("existing", encoding="utf-8")
    link_target = tmp_path / "link.json"
    try:
        link_target.symlink_to(real_target)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    code, out, err = _run(
        [
            "write",
            "--sample-state",
            "--output",
            str(link_target),
            "--write",
            "--acknowledge-state-write",
            "--allow-replace",
        ],
        capsys,
    )
    assert code == 2
    assert out == ""
    assert "OSPMG_STATE_WRITER_TARGET_SYMLINK_BLOCKED" in err


def test_json_output_is_deterministic_and_redacted(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"
    code, out, err = _run(
        [
            "write",
            "--sample-state",
            "--output",
            str(target),
            "--format",
            "json",
        ],
        capsys,
    )
    assert code == 0
    assert err == ""
    assert target.exists() is False
    payload = json.loads(out)
    assert payload["mode"] == "dry-run"
    assert payload["target_reference_display"] == "state.json"
    assert str(tmp_path) not in out
    assert payload["writer_result"]["status"] == "dry_run_planned"


def test_cli_output_confirms_no_reload_clipboard_report_projectschema_or_execution(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"
    code, out, err = _run(
        [
            "write",
            "--sample-state",
            "--output",
            str(target),
            "--write",
            "--acknowledge-state-write",
        ],
        capsys,
    )
    assert code == 0
    assert err == ""
    for phrase in (
        "reload behavior added: False",
        "clipboard performed: False",
        "report attachment performed: False",
        "open output folder performed: False",
        "ProjectSchema mutation performed: False",
        "discovery execution performed: False",
        "validation execution performed: False",
        "solver execution performed: False",
        "issue mutation performed: False",
        "release mutation performed: False",
        "tag mutation performed: False",
        "asset mutation performed: False",
        "validation success claimed: False",
        "validation failure claimed: False",
        "issue closure claimed: False",
        "certification claimed: False",
    ):
        assert phrase in out
