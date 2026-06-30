from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

import pytest

from osw.cli.main import main
from osw.cli.optional_solver_manifest_reload import (
    OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_COMMAND,
)
from osw.experimental.optional_solvers import (
    build_optional_solver_plugin_manifest_state_writer_payload,
)

COMMAND = OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_COMMAND
MODULE_NAME = "osw.cli.optional_solver_manifest_reload"


def _run(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main([COMMAND, *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _valid_payload() -> dict[str, object]:
    return build_optional_solver_plugin_manifest_state_writer_payload(
        {"summary": {"readiness": "ready_preview_only", "state_scope": "session_only"}}
    )


def _write(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _load_json(text: str) -> dict[str, object]:
    payload = json.loads(text)
    assert isinstance(payload, dict)
    return payload


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


def test_load_preview_path_valid_text_output_has_reader_and_viewmodel_sections(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = _write(tmp_path / "state.json", _valid_payload())

    code, out, err = _run(["load-preview", "--path", str(target)], capsys)

    assert code == 0
    assert err == ""
    assert "Reader diagnostics:" in out
    assert "View-model preview:" in out
    assert "OSPMG_RELOAD_READER_READY_FOR_VIEWMODEL" in out
    assert "OSPMG_RELOAD_CLI_EXPLICIT_PATH_READER_ENABLED" in out
    assert "state.json" in out
    assert str(tmp_path) not in out


def test_load_preview_path_valid_json_contains_reader_and_viewmodel_keys(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = _write(tmp_path / "state.json", _valid_payload())

    code, out, err = _run(["load-preview", "--path", str(target), "--json"], capsys)

    assert code == 0
    assert err == ""
    payload = _load_json(out)
    assert payload["status"] == "ready"
    assert payload["reader"]["status"] == "ready_for_viewmodel"
    assert payload["reader"]["redacted_target_display"] == "state.json"
    assert payload["reader"]["safe_mapping_available"] is True
    assert payload["viewmodel"] is not None
    assert payload["non_action_flags"]["validation_success_claimed"] is False
    assert payload["non_action_flags"]["validation_failure_claimed"] is False
    assert payload["exit_semantics"]["code"] == 0
    assert payload["exit_semantics"]["validation_success"] is False
    assert payload["exit_semantics"]["validation_failure"] is False
    assert str(tmp_path) not in out


def test_load_preview_path_output_does_not_claim_unsafe_success_states(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = _write(tmp_path / "state.json", _valid_payload())

    code, out, err = _run(["load-preview", "--path", str(target)], capsys)

    assert code == 0
    assert err == ""
    unsafe_claims = (
        "validation_success: True",
        "validation_failure: True",
        "trust_restoration: True",
        "automatic_activation: True",
        "issue_closure: True",
        "release_mutation: True",
        "certification: True",
        "validation-pass evidence",
        "validation-fail evidence",
        "issue closure evidence",
        "certified",
    )
    for phrase in unsafe_claims:
        assert phrase not in out
    for required_denial in (
        "Explicit path preview is not validation evidence.",
        "Explicit path preview is not validation failure.",
        "Explicit path preview is not trust restoration.",
        "Explicit path preview is not automatic activation.",
        "Explicit path preview is not issue closure.",
        "Explicit path preview is not release mutation.",
        "Explicit path preview is not certification.",
    ):
        assert required_denial in out


def test_load_preview_missing_path_preserves_disabled_future_only_behavior(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["load-preview"], capsys)

    assert code == 2
    assert out == ""
    assert "load-preview: blocked" in err
    assert "OSPMG_RELOAD_CLI_FILE_READER_DISABLED" in err
    assert "without implying validation failure" in err


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        ("missing", "OSPMG_RELOAD_READER_FILE_MISSING"),
        ("directory", "OSPMG_RELOAD_READER_NOT_REGULAR_FILE"),
        ("malformed_json", "OSPMG_RELOAD_READER_JSON_PARSE_ERROR"),
        ("root_array", "OSPMG_RELOAD_READER_ROOT_NOT_OBJECT"),
        ("payload_kind", "OSPMG_RELOAD_READER_PAYLOAD_KIND_MISMATCH"),
        ("schema", "OSPMG_RELOAD_READER_SCHEMA_UNSUPPORTED"),
        ("unsafe_claim", "OSPMG_RELOAD_READER_UNSAFE_CLAIM_BLOCKED"),
        ("secret", "OSPMG_RELOAD_READER_SECRET_LIKE_VALUE_BLOCKED"),
    ],
)
def test_reader_blockers_return_two_and_suppress_viewmodel_preview(
    tmp_path: Path,
    payload: str,
    code: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"
    if payload == "missing":
        target = tmp_path / "missing.json"
    elif payload == "directory":
        target = tmp_path
    elif payload == "malformed_json":
        target.write_text("{not json", encoding="utf-8")
    elif payload == "root_array":
        target.write_text("[1, 2, 3]", encoding="utf-8")
    else:
        data = _valid_payload()
        if payload == "payload_kind":
            data["payload_kind"] = "wrong"
        elif payload == "schema":
            data["payload_schema_version"] = "osw-exp-999"
        elif payload == "unsafe_claim":
            data["unsafe_claims"] = [{"claim": "certification achieved"}]
        elif payload == "secret":
            data["summary"] = {"note": "api_key=secret-value"}
        _write(target, data)

    exit_code, out, err = _run(["load-preview", "--path", str(target)], capsys)

    assert exit_code == 2
    assert out == ""
    assert code in err
    assert "Reader blocked view-model preview:" in err
    assert "View-model preview:" not in err
    assert "validation failure" in err
    assert str(tmp_path) not in err


def test_warning_only_reader_diagnostic_remains_visible_when_preview_proceeds(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = _valid_payload()
    payload["acknowledgements"] = [
        {"acknowledgement_id": "reload_not_validation", "expired": True}
    ]
    target = _write(tmp_path / "warning.json", payload)

    code, out, err = _run(["load-preview", "--path", str(target)], capsys)

    assert code == 0
    assert err == ""
    assert "OSPMG_RELOAD_READER_ACKNOWLEDGEMENT_EXPIRED" in out
    assert "View-model preview:" in out


def test_reader_diagnostics_only_skips_viewmodel_preview_after_success(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = _write(tmp_path / "state.json", _valid_payload())

    code, out, err = _run(
        ["load-preview", "--path", str(target), "--reader-diagnostics-only"],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert "Reader diagnostics:" in out
    assert "View-model preview: skipped by --reader-diagnostics-only" in out
    assert "View-model preview:\n- readiness" not in out


def test_viewmodel_preview_only_still_requires_reader_success(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = _write(tmp_path / "state.json", _valid_payload())

    code, out, err = _run(
        ["load-preview", "--path", str(target), "--viewmodel-preview-only"],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert "OSPMG_RELOAD_CLI_VIEWMODEL_PREVIEW_ONLY" in out
    assert "Reader diagnostics:" in out
    assert "View-model preview:" in out


def test_max_bytes_is_passed_to_reader_and_oversized_file_blocks(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = _write(tmp_path / "state.json", _valid_payload())

    code, out, err = _run(
        ["load-preview", "--path", str(target), "--max-bytes", "8"],
        capsys,
    )

    assert code == 2
    assert out == ""
    assert "OSPMG_RELOAD_READER_FILE_TOO_LARGE" in err
    assert "View-model preview:" not in err


def test_unredacted_paths_and_secret_like_values_are_blocked_by_default(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path_payload = _valid_payload()
    path_payload["sources"] = [
        {"source_reference_display": "C:\\Users\\Research\\state.json"}
    ]
    secret_payload = _valid_payload()
    secret_payload["summary"] = {"note": "token=super-secret"}

    path_code, path_out, path_err = _run(
        ["load-preview", "--path", str(_write(tmp_path / "path.json", path_payload))],
        capsys,
    )
    secret_code, secret_out, secret_err = _run(
        [
            "load-preview",
            "--path",
            str(_write(tmp_path / "secret.json", secret_payload)),
        ],
        capsys,
    )

    assert path_code == 2
    assert secret_code == 2
    assert path_out == ""
    assert secret_out == ""
    assert "OSPMG_RELOAD_READER_UNREDACTED_PATH_BLOCKED" in path_err
    assert "C:\\Users\\Research" not in path_err
    assert "OSPMG_RELOAD_READER_SECRET_LIKE_VALUE_BLOCKED" in secret_err
    assert "super-secret" not in secret_err


def test_allow_unredacted_paths_and_secret_like_values_remain_explicit_options(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = _valid_payload()
    payload["summary"] = {"note": "token=allowed-for-test"}
    target = _write(tmp_path / "allowed.json", payload)

    code, out, err = _run(
        [
            "load-preview",
            "--path",
            str(target),
            "--allow-secret-like-values",
            "--json",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    parsed = _load_json(out)
    assert parsed["reader_request_policy"]["allow_secret_like_values"] is True
    assert "allowed-for-test" not in out


def test_allow_symlink_option_is_passed_when_platform_supports_symlinks(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = _write(tmp_path / "state.json", _valid_payload())
    link = tmp_path / "state-link.json"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")

    blocked_code, _blocked_out, blocked_err = _run(
        ["load-preview", "--path", str(link)],
        capsys,
    )
    allowed_code, allowed_out, allowed_err = _run(
        ["load-preview", "--path", str(link), "--allow-symlink"],
        capsys,
    )

    assert blocked_code == 2
    assert "OSPMG_RELOAD_READER_SYMLINK_BLOCKED" in blocked_err
    assert allowed_code == 0
    assert allowed_err == ""
    assert "View-model preview:" in allowed_out


def test_allow_migration_option_is_accepted_but_migration_stays_future_gated(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = _valid_payload()
    payload["payload_schema_version"] = "osw-exp-102-preview"
    target = _write(tmp_path / "migration.json", payload)

    code, out, err = _run(
        ["load-preview", "--path", str(target), "--allow-migration"],
        capsys,
    )

    assert code == 2
    assert out == ""
    assert "OSPMG_RELOAD_READER_MIGRATION_REQUIRED" in err
    assert "View-model preview:" not in err


def test_explicit_path_options_are_rejected_on_other_reload_commands(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = _write(tmp_path / "state.json", _valid_payload())

    code, out, err = _run(["preview", "--path", str(target)], capsys)

    assert code == 2
    assert out == ""
    assert "only supported for load-preview" in err


def test_cli_explicit_path_preview_creates_no_output_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = _write(tmp_path / "state.json", _valid_payload())
    before = {path.name for path in tmp_path.iterdir()}

    code, _out, err = _run(["load-preview", "--path", str(target)], capsys)

    assert code == 0
    assert err == ""
    assert {path.name for path in tmp_path.iterdir()} == before


def test_cli_source_has_no_directory_scan_network_gui_projectschema_or_solver_imports() -> None:
    source = _module_source()
    for phrase in (
        ".glob(",
        ".rglob(",
        ".iterdir(",
        "os.walk",
        "os.scandir",
        "requests.",
        "urllib",
        "urlopen",
        "QFileDialog",
        "PySide",
        "PyQt",
        "ProjectSchema(",
        "discover_optional_solver_manifests(",
        "discover_local_plugin_manifests(",
        "execute_solver(",
        "subprocess",
        ".write_text(",
        ".write_bytes(",
        ".mkdir(",
    ):
        assert phrase not in source, phrase
    for imported in _imported_modules():
        assert not imported.startswith("osw.gui"), imported
        assert not imported.startswith("osw.core"), imported
        assert not imported.startswith("osw.plugins"), imported
        assert not imported.startswith("osw.solvers"), imported
        assert not imported.startswith("osw.post"), imported
        assert not imported.startswith(("pyside", "pyqt")), imported
