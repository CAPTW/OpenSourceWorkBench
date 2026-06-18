from __future__ import annotations

import json
import os
from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXRuntimeDiscovery,
    FEASpecCalculiXRunResult,
    FEASpecCalculiXRunStatus,
    discover_calculix_executable,
    inspect_calculix_export_bundle,
    plan_calculix_installed_run,
    run_calculix_installed_only,
)
from osw.experimental.feaspec.calculix_run_diagnostics import (
    CalculiXRunDiagnosticCode,
)
from osw.experimental.feaspec.calculix_run_gate import (
    explain_calculix_run_result,
)


def _write_bundle(root: Path, *, basename: str = "ready_case") -> Path:
    root.mkdir()
    inp = root / f"{basename}.inp"
    diagnostics = root / f"{basename}.diagnostics.json"
    readme = root / "README_RUN_FIRST.txt"
    manifest = root / f"{basename}.manifest.json"
    inp.write_text("*NODE\n1, 0., 0., 0.\n", encoding="utf-8")
    diagnostics.write_text(
        json.dumps(
            {
                "status": "exported",
                "solver_execution_performed": False,
                "ready_for_solver_execution": False,
            }
        ),
        encoding="utf-8",
    )
    readme.write_text(
        "Review before installed-only run. Issue #8 remains separate.\n",
        encoding="utf-8",
    )
    manifest.write_text(
        json.dumps(
            {
                "exporter_module": "osw.experimental.feaspec.calculix_exporter",
                "osw_version": "0.1.4rc1",
                "release_tag": "v0.1.4-rc1",
                "target_solver": "calculix",
                "source_feaspec_id": "test_ready",
                "case_id": "ready_case",
                "solver_execution_performed": False,
                "ready_for_solver_execution": False,
                "files": [
                    {"role": "inp", "filename": inp.name, "sha256": "", "size_bytes": 1},
                    {
                        "role": "diagnostics",
                        "filename": diagnostics.name,
                        "sha256": "",
                        "size_bytes": 1,
                    },
                    {
                        "role": "readme",
                        "filename": readme.name,
                        "sha256": "",
                        "size_bytes": 1,
                    },
                ],
                "limitations": [
                    "No solver run was performed by this exporter.",
                    "External CalculiX solver binaries are not bundled.",
                ],
            }
        ),
        encoding="utf-8",
    )
    return root


def _write_fake_ccx(tmp_path: Path, mode: str) -> Path:
    if os.name == "nt":
        path = tmp_path / f"fake_ccx_{mode}.cmd"
        if mode == "success":
            body = (
                "@echo off\r\n"
                "echo fake ccx success %*\r\n"
                "echo fake ccx stderr 1>&2\r\n"
                "echo fake dat> \"%~1.dat\"\r\n"
                "exit /b 0\r\n"
            )
        elif mode == "nonzero":
            body = (
                "@echo off\r\n"
                "echo fake ccx failed %*\r\n"
                "echo fake failure 1>&2\r\n"
                "exit /b 7\r\n"
            )
        else:
            body = "@echo off\r\necho fake ccx timeout\r\n:again\r\ngoto again\r\n"
        path.write_text(body, encoding="utf-8")
        return path

    path = tmp_path / f"fake_ccx_{mode}"
    if mode == "success":
        body = (
            "#!/bin/sh\n"
            "echo fake ccx success \"$@\"\n"
            "echo fake ccx stderr >&2\n"
            "printf 'fake dat\\n' > \"$1.dat\"\n"
            "exit 0\n"
        )
    elif mode == "nonzero":
        body = (
            "#!/bin/sh\n"
            "echo fake ccx failed \"$@\"\n"
            "echo fake failure >&2\n"
            "exit 7\n"
        )
    else:
        body = "#!/bin/sh\necho fake ccx timeout\nwhile :; do :; done\n"
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def _codes(result: FEASpecCalculiXRunResult) -> set[CalculiXRunDiagnosticCode]:
    return {diagnostic.code for diagnostic in result.diagnostics}


def test_module_imports_and_public_api_exports_required_types() -> None:
    assert discover_calculix_executable
    assert inspect_calculix_export_bundle
    assert plan_calculix_installed_run
    assert run_calculix_installed_only
    assert explain_calculix_run_result
    assert CalculiXRuntimeDiscovery
    assert FEASpecCalculiXRunResult


def test_dry_run_without_execute_does_not_write_or_start_process(tmp_path: Path) -> None:
    export_dir = _write_bundle(tmp_path / "bundle")
    run_dir = tmp_path / "run"
    fake_ccx = _write_fake_ccx(tmp_path, "success")

    result = run_calculix_installed_only(
        export_dir,
        ccx_path=fake_ccx,
        run_dir=run_dir,
        execute=False,
    )

    assert result.status is FEASpecCalculiXRunStatus.DRY_RUN_READY
    assert result.solver_execution_performed is False
    assert not run_dir.exists()
    assert result.metadata.run_metadata_path is None


def test_execute_without_confirm_run_is_blocked(tmp_path: Path) -> None:
    export_dir = _write_bundle(tmp_path / "bundle")
    fake_ccx = _write_fake_ccx(tmp_path, "success")

    result = run_calculix_installed_only(
        export_dir,
        ccx_path=fake_ccx,
        run_dir=tmp_path / "run",
        execute=True,
        confirm_run=False,
        acknowledge_readme=True,
    )

    assert result.status is FEASpecCalculiXRunStatus.BLOCKED
    assert CalculiXRunDiagnosticCode.FR_CONFIRMATION_REQUIRED in _codes(result)
    assert result.solver_execution_performed is False


def test_execute_without_readme_acknowledgement_is_blocked(tmp_path: Path) -> None:
    export_dir = _write_bundle(tmp_path / "bundle")
    fake_ccx = _write_fake_ccx(tmp_path, "success")

    result = run_calculix_installed_only(
        export_dir,
        ccx_path=fake_ccx,
        run_dir=tmp_path / "run",
        execute=True,
        confirm_run=True,
        acknowledge_readme=False,
    )

    assert result.status is FEASpecCalculiXRunStatus.BLOCKED
    assert CalculiXRunDiagnosticCode.FR_README_NOT_ACKNOWLEDGED in _codes(result)
    assert result.solver_execution_performed is False


def test_missing_ccx_is_skipped_missing_with_diagnostic(tmp_path: Path) -> None:
    export_dir = _write_bundle(tmp_path / "bundle")

    result = run_calculix_installed_only(
        export_dir,
        ccx_path=tmp_path / "missing_ccx",
        run_dir=tmp_path / "run",
        execute=True,
        confirm_run=True,
        acknowledge_readme=True,
    )

    assert result.status is FEASpecCalculiXRunStatus.SKIPPED_MISSING
    assert CalculiXRunDiagnosticCode.FR_CCX_MISSING in _codes(result)
    assert result.solver_execution_performed is False


def test_invalid_bundle_missing_manifest_inp_and_readme_is_blocked(tmp_path: Path) -> None:
    export_dir = tmp_path / "bundle"
    export_dir.mkdir()

    result = run_calculix_installed_only(export_dir, ccx_path=tmp_path / "missing_ccx")

    assert result.status is FEASpecCalculiXRunStatus.BLOCKED
    assert CalculiXRunDiagnosticCode.FR_MANIFEST_MISSING in _codes(result)
    assert CalculiXRunDiagnosticCode.FR_INP_MISSING in _codes(result)
    assert CalculiXRunDiagnosticCode.FR_README_MISSING in _codes(result)
    assert result.solver_execution_performed is False


def test_unsafe_run_dir_and_nonempty_run_dir_are_blocked(tmp_path: Path) -> None:
    export_dir = _write_bundle(tmp_path / "bundle")
    fake_ccx = _write_fake_ccx(tmp_path, "success")
    nonempty = tmp_path / "nonempty"
    nonempty.mkdir()
    (nonempty / "old.txt").write_text("old", encoding="utf-8")

    unsafe = run_calculix_installed_only(
        export_dir,
        ccx_path=fake_ccx,
        run_dir=export_dir,
        execute=True,
        confirm_run=True,
        acknowledge_readme=True,
    )
    not_empty = run_calculix_installed_only(
        export_dir,
        ccx_path=fake_ccx,
        run_dir=nonempty,
        execute=True,
        confirm_run=True,
        acknowledge_readme=True,
    )

    assert CalculiXRunDiagnosticCode.FR_RUN_DIR_UNSAFE in _codes(unsafe)
    assert CalculiXRunDiagnosticCode.FR_RUN_DIR_NOT_EMPTY in _codes(not_empty)
    assert unsafe.solver_execution_performed is False
    assert not_empty.solver_execution_performed is False


def test_empty_existing_run_dir_is_allowed(tmp_path: Path) -> None:
    export_dir = _write_bundle(tmp_path / "bundle")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    fake_ccx = _write_fake_ccx(tmp_path, "success")

    result = run_calculix_installed_only(
        export_dir,
        ccx_path=fake_ccx,
        run_dir=run_dir,
        execute=True,
        confirm_run=True,
        acknowledge_readme=True,
    )

    assert result.status is FEASpecCalculiXRunStatus.RAN
    assert result.solver_execution_performed is True
    assert (run_dir / "run_metadata.json").is_file()


def test_fake_ccx_success_writes_logs_and_run_metadata(tmp_path: Path) -> None:
    export_dir = _write_bundle(tmp_path / "bundle")
    run_dir = tmp_path / "run"
    fake_ccx = _write_fake_ccx(tmp_path, "success")

    result = run_calculix_installed_only(
        export_dir,
        ccx_path=fake_ccx,
        run_dir=run_dir,
        execute=True,
        confirm_run=True,
        acknowledge_readme=True,
    )

    assert result.status is FEASpecCalculiXRunStatus.RAN
    assert result.exit_code == 0
    assert result.solver_execution_performed is True
    assert (run_dir / "ready_case.inp").is_file()
    assert (run_dir / "stdout.txt").read_text(encoding="utf-8")
    assert (run_dir / "stderr.txt").read_text(encoding="utf-8")
    payload = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    assert payload["solver_execution_performed"] is True
    assert payload["exit_code"] == 0
    assert payload["timed_out"] is False
    assert result.metadata.run_metadata_path == run_dir / "run_metadata.json"


def test_fake_ccx_nonzero_returns_failed_and_captures_exit(tmp_path: Path) -> None:
    export_dir = _write_bundle(tmp_path / "bundle")
    fake_ccx = _write_fake_ccx(tmp_path, "nonzero")

    result = run_calculix_installed_only(
        export_dir,
        ccx_path=fake_ccx,
        run_dir=tmp_path / "run",
        execute=True,
        confirm_run=True,
        acknowledge_readme=True,
    )

    assert result.status is FEASpecCalculiXRunStatus.FAILED
    assert result.exit_code == 7
    assert result.solver_execution_performed is True
    assert CalculiXRunDiagnosticCode.FR_NONZERO_EXIT in _codes(result)


def test_fake_ccx_timeout_returns_timed_out(tmp_path: Path) -> None:
    export_dir = _write_bundle(tmp_path / "bundle")
    fake_ccx = _write_fake_ccx(tmp_path, "timeout")

    result = run_calculix_installed_only(
        export_dir,
        ccx_path=fake_ccx,
        run_dir=tmp_path / "run",
        timeout_seconds=0.1,
        execute=True,
        confirm_run=True,
        acknowledge_readme=True,
    )

    assert result.status is FEASpecCalculiXRunStatus.TIMED_OUT
    assert result.timed_out is True
    assert result.solver_execution_performed is True
    assert CalculiXRunDiagnosticCode.FR_TIMEOUT in _codes(result)
    payload = json.loads((tmp_path / "run" / "run_metadata.json").read_text())
    assert payload["solver_execution_performed"] is True
    assert payload["timed_out"] is True
