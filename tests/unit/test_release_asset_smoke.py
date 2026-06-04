from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tarfile
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_RELEASE = REPO_ROOT / "tools" / "release"
if str(TOOLS_RELEASE) not in sys.path:
    sys.path.insert(0, str(TOOLS_RELEASE))

import check_release_assets as release_assets  # noqa: E402

FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "release_assets"


def _fixture_copy(tmp_path: Path) -> Path:
    target = tmp_path / "assets"
    shutil.copytree(FIXTURE_DIR, target)
    return target


def _verify(asset_dir: Path) -> dict[str, object]:
    return release_assets.verify_asset_dir(
        asset_dir,
        tag="v0.1.3-rc1",
        expected_version="0.1.3rc1",
        full_smoke=False,
        skip_portable_exe=True,
    )


def _write_tar(path: Path, entries: dict[str, bytes]) -> None:
    with tarfile.open(path, "w:gz") as archive:
        for name, payload in entries.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, BytesIO(payload))


def _write_zip(path: Path, entries: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in entries.items():
            archive.writestr(name, payload)


def test_parses_sha256sums_and_verifies_matching_files(tmp_path: Path) -> None:
    summary = _verify(_fixture_copy(tmp_path))

    assert summary["status"] == "passed_with_warnings"
    assert "release_asset_manifest.json" in summary["checksums"]["entries"]


def test_detects_checksum_mismatch(tmp_path: Path) -> None:
    asset_dir = _fixture_copy(tmp_path)
    (asset_dir / "open_solver_workbench-0.1.3rc1-py3-none-any.whl").write_text(
        "tampered\n",
        encoding="utf-8",
    )

    with pytest.raises(release_assets.AssetSmokeError, match="SHA256 mismatch"):
        _verify(asset_dir)


def test_parses_manifest_and_validates_size_hash(tmp_path: Path) -> None:
    summary = _verify(_fixture_copy(tmp_path))

    manifest = summary["manifest"]
    assert manifest["tag"] == "v0.1.3-rc1"
    assert "open_solver_workbench-0.1.3rc1-py3-none-any.whl" in manifest["assets"]


def test_detects_missing_expected_asset(tmp_path: Path) -> None:
    asset_dir = _fixture_copy(tmp_path)
    (asset_dir / "OpenSolverWorkbench-v0.1.3rc1-windows-x64-portable.zip").unlink()

    summary = _verify(asset_dir)

    assert summary["status"] == "failed"
    assert "missing expected asset type: portable_zip" in summary["failures"]


def test_safe_zip_extraction_rejects_path_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    _write_zip(archive, {"../escape.txt": b"no"})

    with pytest.raises(release_assets.AssetSmokeError, match="path traversal"):
        release_assets.safe_extract_zip(archive, tmp_path / "out")


def test_safe_tar_extraction_rejects_path_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "bad.tar.gz"
    _write_tar(archive, {"../escape.txt": b"no"})

    with pytest.raises(release_assets.AssetSmokeError, match="path traversal"):
        release_assets.safe_extract_tar(archive, tmp_path / "out")


def test_portable_zip_inspection_rejects_forbidden_entries(tmp_path: Path) -> None:
    archive = tmp_path / "portable.zip"
    _write_zip(archive, {"OpenSolverWorkbench/.git/config": b"no"})

    with pytest.raises(release_assets.AssetSmokeError, match="forbidden entry"):
        release_assets.validate_zip_entries(archive, portable=True)


def test_summary_json_contains_asset_status_and_warnings(tmp_path: Path) -> None:
    asset_dir = _fixture_copy(tmp_path)
    json_out = tmp_path / "summary.json"

    proc = subprocess.run(
        [
            sys.executable,
            str(TOOLS_RELEASE / "check_release_assets.py"),
            "--asset-dir",
            str(asset_dir),
            "--tag",
            "v0.1.3-rc1",
            "--json-out",
            str(json_out),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    summary = json.loads(json_out.read_text(encoding="utf-8"))
    assert summary["status"] == "passed_with_warnings"
    assert summary["assets"]
    assert summary["warnings"]


def test_local_directory_mode_returns_nonzero_on_failed_verification(tmp_path: Path) -> None:
    asset_dir = _fixture_copy(tmp_path)
    (asset_dir / "release_asset_manifest.json").write_text("{bad json", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            str(TOOLS_RELEASE / "check_release_assets.py"),
            "--asset-dir",
            str(asset_dir),
            "--tag",
            "v0.1.3-rc1",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode != 0
    assert "SHA256 mismatch" in proc.stderr


def test_local_directory_mode_returns_zero_on_valid_fake_fixture(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(TOOLS_RELEASE / "check_release_assets.py"),
            "--asset-dir",
            str(_fixture_copy(tmp_path)),
            "--tag",
            "v0.1.3-rc1",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert "[ok] Release asset verification" in proc.stdout
