from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

import pytest

from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestReloadFileReader,
    OptionalSolverPluginManifestReloadFileReaderStatus,
    OptionalSolverPluginManifestReloadFileReadRequest,
    OptionalSolverPluginManifestReloadFileReadResult,
    read_optional_solver_plugin_manifest_reload_file,
)
from osw.experimental.optional_solvers import (
    plugin_manifest_reload_file_reader as module_under_test,
)
from osw.experimental.optional_solvers.plugin_manifest_reload_file_reader import (
    OSPMG_RELOAD_READER_CONFLICT_REVIEW_REQUIRED,
    OSPMG_RELOAD_READER_DUPLICATE_KEY_BLOCKED,
    OSPMG_RELOAD_READER_EMPTY_FILE,
    OSPMG_RELOAD_READER_ENCODING_ERROR,
    OSPMG_RELOAD_READER_EVIDENCE_REFERENCE_ONLY,
    OSPMG_RELOAD_READER_FILE_MISSING,
    OSPMG_RELOAD_READER_FILE_TOO_LARGE,
    OSPMG_RELOAD_READER_JSON_PARSE_ERROR,
    OSPMG_RELOAD_READER_MIGRATION_REQUIRED,
    OSPMG_RELOAD_READER_NOT_REGULAR_FILE,
    OSPMG_RELOAD_READER_PAYLOAD_KIND_MISMATCH,
    OSPMG_RELOAD_READER_READY_FOR_VIEWMODEL,
    OSPMG_RELOAD_READER_ROOT_NOT_OBJECT,
    OSPMG_RELOAD_READER_SCHEMA_UNSUPPORTED,
    OSPMG_RELOAD_READER_SECRET_LIKE_VALUE_BLOCKED,
    OSPMG_RELOAD_READER_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_RELOAD_READER_SYMLINK_BLOCKED,
    OSPMG_RELOAD_READER_UNREDACTED_PATH_BLOCKED,
    OSPMG_RELOAD_READER_UNSAFE_CLAIM_BLOCKED,
)
from osw.experimental.optional_solvers.plugin_manifest_reload_viewmodel import (
    from_payload_mapping,
)
from osw.experimental.optional_solvers.plugin_manifest_state_writer import (
    build_optional_solver_plugin_manifest_state_writer_payload,
)

_Status = OptionalSolverPluginManifestReloadFileReaderStatus


def _valid_payload() -> dict:
    return build_optional_solver_plugin_manifest_state_writer_payload(
        {"summary": {"readiness": "ready_preview_only", "state_scope": "session_only"}}
    )


def _write(path: Path, obj: object) -> Path:
    path.write_text(json.dumps(obj), encoding="utf-8")
    return path


def _codes(result: OptionalSolverPluginManifestReloadFileReadResult) -> set[str]:
    return set(result.codes())


def _read(path: object, **kwargs) -> OptionalSolverPluginManifestReloadFileReadResult:
    return read_optional_solver_plugin_manifest_reload_file(str(path), **kwargs)


# ---------------------------------------------------------------------------
# 1. Imports / exports.
# ---------------------------------------------------------------------------
def test_module_imports_and_exports() -> None:
    module = importlib.import_module(
        "osw.experimental.optional_solvers.plugin_manifest_reload_file_reader"
    )
    assert hasattr(module, "OptionalSolverPluginManifestReloadFileReader")
    assert hasattr(module, "read_optional_solver_plugin_manifest_reload_file")
    reader = OptionalSolverPluginManifestReloadFileReader()
    assert hasattr(reader, "read")


# ---------------------------------------------------------------------------
# 2-9. File-level rejections.
# ---------------------------------------------------------------------------
def test_missing_file(tmp_path: Path) -> None:
    result = _read(tmp_path / "nope.json")
    assert result.status == _Status.UNREADABLE
    assert OSPMG_RELOAD_READER_FILE_MISSING in _codes(result)
    assert result.safe_mapping is None


def test_no_path_supplied() -> None:
    result = read_optional_solver_plugin_manifest_reload_file(None)
    assert OSPMG_RELOAD_READER_FILE_MISSING in _codes(result)
    assert result.safe_mapping is None


def test_directory_target(tmp_path: Path) -> None:
    result = _read(tmp_path)
    assert OSPMG_RELOAD_READER_NOT_REGULAR_FILE in _codes(result)
    assert result.safe_mapping is None


def test_symlink_blocked_by_default(tmp_path: Path) -> None:
    real = _write(tmp_path / "real.json", _valid_payload())
    link = tmp_path / "link.json"
    try:
        link.symlink_to(real)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this platform/privilege level")
    result = _read(link)
    assert OSPMG_RELOAD_READER_SYMLINK_BLOCKED in _codes(result)
    assert result.safe_mapping is None
    allowed = _read(link, allow_symlink=True)
    assert OSPMG_RELOAD_READER_SYMLINK_BLOCKED not in _codes(allowed)


def test_empty_file(tmp_path: Path) -> None:
    target = tmp_path / "empty.json"
    target.write_bytes(b"")
    assert OSPMG_RELOAD_READER_EMPTY_FILE in _codes(_read(target))


def test_oversized_file(tmp_path: Path) -> None:
    target = _write(tmp_path / "big.json", _valid_payload())
    result = _read(target, max_bytes=16)
    assert OSPMG_RELOAD_READER_FILE_TOO_LARGE in _codes(result)
    assert result.safe_mapping is None


def test_binary_looking_file(tmp_path: Path) -> None:
    target = tmp_path / "bin.json"
    target.write_bytes(b"{\x00\x01}")
    assert OSPMG_RELOAD_READER_ENCODING_ERROR in _codes(_read(target))


def test_malformed_json(tmp_path: Path) -> None:
    target = tmp_path / "bad.json"
    target.write_text("{not valid json", encoding="utf-8")
    assert OSPMG_RELOAD_READER_JSON_PARSE_ERROR in _codes(_read(target))


def test_root_array_rejected(tmp_path: Path) -> None:
    target = tmp_path / "arr.json"
    target.write_text("[1, 2, 3]", encoding="utf-8")
    assert OSPMG_RELOAD_READER_ROOT_NOT_OBJECT in _codes(_read(target))


def test_duplicate_keys_blocked(tmp_path: Path) -> None:
    target = tmp_path / "dup.json"
    target.write_text('{"payload_kind": "a", "payload_kind": "b"}', encoding="utf-8")
    assert OSPMG_RELOAD_READER_DUPLICATE_KEY_BLOCKED in _codes(_read(target))


# ---------------------------------------------------------------------------
# 11-19. Content blockers.
# ---------------------------------------------------------------------------
def test_payload_kind_mismatch(tmp_path: Path) -> None:
    payload = _valid_payload()
    payload["payload_kind"] = "something_else"
    result = _read(_write(tmp_path / "k.json", payload))
    assert OSPMG_RELOAD_READER_PAYLOAD_KIND_MISMATCH in _codes(result)
    assert result.safe_mapping is None


def test_unsupported_schema(tmp_path: Path) -> None:
    payload = _valid_payload()
    payload["payload_schema_version"] = "osw-exp-999-unknown"
    assert OSPMG_RELOAD_READER_SCHEMA_UNSUPPORTED in _codes(
        _read(_write(tmp_path / "s.json", payload))
    )


def test_migration_required(tmp_path: Path) -> None:
    payload = _valid_payload()
    payload["schema_migration"] = [{"migration_required": True, "migration_notes": "x"}]
    result = _read(_write(tmp_path / "m.json", payload))
    assert OSPMG_RELOAD_READER_MIGRATION_REQUIRED in _codes(result)
    assert result.safe_mapping is None


def test_unredacted_path_blocked(tmp_path: Path) -> None:
    payload = _valid_payload()
    payload["sources"] = [{"source_reference_display": "C:\\Users\\me\\manifest.json"}]
    result = _read(_write(tmp_path / "p.json", payload))
    assert OSPMG_RELOAD_READER_UNREDACTED_PATH_BLOCKED in _codes(result)
    assert result.safe_mapping is None


def test_secret_like_value_blocked(tmp_path: Path) -> None:
    payload = _valid_payload()
    payload["summary"] = {"note": "api_key=ABCDEF123456"}
    assert OSPMG_RELOAD_READER_SECRET_LIKE_VALUE_BLOCKED in _codes(
        _read(_write(tmp_path / "sec.json", payload))
    )


def test_unsafe_claim_blocked_via_flags(tmp_path: Path) -> None:
    payload = _valid_payload()
    payload["non_action_flags"] = {"validation_execution_performed": True}
    assert OSPMG_RELOAD_READER_UNSAFE_CLAIM_BLOCKED in _codes(
        _read(_write(tmp_path / "u.json", payload))
    )


def test_unsafe_claim_blocked_via_claims(tmp_path: Path) -> None:
    payload = _valid_payload()
    payload["unsafe_claims"] = [{"claim": "this solver is certified"}]
    assert OSPMG_RELOAD_READER_UNSAFE_CLAIM_BLOCKED in _codes(
        _read(_write(tmp_path / "uc.json", payload))
    )


def test_stale_source_surfaced(tmp_path: Path) -> None:
    payload = _valid_payload()
    payload["stale_sources"] = [{"source_id": "s1", "stale_source_state": "stale"}]
    assert OSPMG_RELOAD_READER_STALE_SOURCE_REPREVIEW_REQUIRED in _codes(
        _read(_write(tmp_path / "st.json", payload))
    )


def test_conflict_surfaced(tmp_path: Path) -> None:
    payload = _valid_payload()
    payload["conflicts"] = [{"stack_id": "shared"}]
    assert OSPMG_RELOAD_READER_CONFLICT_REVIEW_REQUIRED in _codes(
        _read(_write(tmp_path / "c.json", payload))
    )


def test_evidence_history_reference_only(tmp_path: Path) -> None:
    payload = _valid_payload()
    payload["evidence_history"] = [{"kind": "deactivation_history"}]
    result = _read(_write(tmp_path / "ev.json", payload))
    assert OSPMG_RELOAD_READER_EVIDENCE_REFERENCE_ONLY in _codes(result)
    # evidence retention is reference-only, not a blocker
    assert result.status == _Status.READY_FOR_VIEWMODEL


# ---------------------------------------------------------------------------
# 20-21. Valid payload + safe mapping feeds the reload view-model.
# ---------------------------------------------------------------------------
def test_valid_payload_ready_with_safe_mapping(tmp_path: Path) -> None:
    result = _read(_write(tmp_path / "state.json", _valid_payload()))
    assert result.status == _Status.READY_FOR_VIEWMODEL
    assert OSPMG_RELOAD_READER_READY_FOR_VIEWMODEL in _codes(result)
    assert result.safe_mapping is not None
    assert result.ready_for_viewmodel is True


def test_safe_mapping_feeds_reload_viewmodel(tmp_path: Path) -> None:
    result = _read(_write(tmp_path / "state.json", _valid_payload()))
    assert result.safe_mapping is not None
    view_model = from_payload_mapping(result.safe_mapping)
    assert (
        view_model.summary.payload_kind
        == "optional_solver_plugin_manifest_state_writer_state"
    )


# ---------------------------------------------------------------------------
# 22-23. No raw path leak, no file writes.
# ---------------------------------------------------------------------------
def test_no_raw_path_leak_in_diagnostics_or_text(tmp_path: Path) -> None:
    payload = _valid_payload()
    payload["sources"] = [{"source_reference_display": "C:\\Users\\secret\\m.json"}]
    target = _write(tmp_path / "leaky.json", payload)
    result = _read(target)
    raw = str(target)
    for diag in result.diagnostics:
        assert raw not in diag.message
        assert raw not in diag.related
    assert raw not in "\n".join(result.to_text_lines())
    assert result.redacted_target_display == "leaky.json"


def test_reader_writes_no_files(tmp_path: Path) -> None:
    target = _write(tmp_path / "state.json", _valid_payload())
    before = {p.name for p in tmp_path.iterdir()}
    _read(target)
    _read(tmp_path / "missing.json")
    after = {p.name for p in tmp_path.iterdir()}
    assert before == after


def test_non_action_flags_all_false(tmp_path: Path) -> None:
    result = _read(_write(tmp_path / "state.json", _valid_payload()))
    flags = result.non_action_flags.to_mapping()
    assert flags and all(value is False for value in flags.values())


# ---------------------------------------------------------------------------
# 24-31. Source purity (no scans / network / subprocess / GUI / CLI / schema).
# ---------------------------------------------------------------------------
def _module_source() -> str:
    return Path(module_under_test.__file__).read_text(encoding="utf-8")


def _imported_roots() -> set[str]:
    return {module.split(".", 1)[0] for module in _imported_modules_full()}


def _imported_modules_full() -> set[str]:
    tree = ast.parse(_module_source())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module)
    return modules


def test_source_has_no_directory_scan() -> None:
    source = _module_source()
    for phrase in (".glob(", ".rglob(", ".iterdir(", "os.walk", "os.scandir", "scandir("):
        assert phrase not in source, phrase


def test_source_has_no_network_or_subprocess() -> None:
    roots = _imported_roots()
    for forbidden in ("requests", "urllib", "http", "socket", "subprocess", "shutil"):
        assert forbidden not in roots, forbidden
    source = _module_source()
    for phrase in ("urlopen", "subprocess", "shutil.", "webbrowser", "QProcess"):
        assert phrase not in source, phrase


def test_source_has_no_gui_cli_or_schema_imports() -> None:
    # Inspect actual import statements, not prose mentions of boundaries.
    for module in _imported_modules_full():
        assert not module.startswith(
            ("osw.cli", "osw.gui", "osw.core", "osw.plugins", "osw.solvers", "osw.post")
        ), module
        assert not module.lower().startswith(("pyside", "pyqt"))
    lowered = _module_source().lower()
    for phrase in ("import pyside", "from pyside", "import pyqt", "from pyqt",
                   "qtwidgets", "from osw.cli", "import osw.cli", "from osw.gui",
                   "import osw.gui", "from osw.core", "from osw.plugins",
                   "from osw.solvers"):
        assert phrase not in lowered, phrase


def test_source_has_no_file_write_or_delete() -> None:
    source = _module_source()
    for phrase in (
        ".write_text(", ".write_bytes(", ".mkdir(", ".unlink(", ".rmdir(",
        ".replace(", "os.remove", "os.rename", '.open("w"', ".open('w'",
        '.open("a"', "makedirs",
    ):
        assert phrase not in source, phrase


# ---------------------------------------------------------------------------
# Request model / defaults.
# ---------------------------------------------------------------------------
def test_request_defaults_are_conservative() -> None:
    request = OptionalSolverPluginManifestReloadFileReadRequest(target_path="x.json")
    assert request.allow_symlink is False
    assert request.allow_migration is False
    assert request.allow_unredacted_paths is False
    assert request.allow_secret_like_values is False
    assert request.max_bytes > 0
    assert (
        request.expected_payload_kind
        == "optional_solver_plugin_manifest_state_writer_state"
    )
