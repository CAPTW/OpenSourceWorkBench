from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tarfile
import zipfile
from dataclasses import replace
from io import BytesIO
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_RELEASE = REPO_ROOT / "tools" / "release"
TOOLS_QA = REPO_ROOT / "tools" / "qa"
for tools_dir in (TOOLS_RELEASE, TOOLS_QA):
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))

import check_release_assets as release_assets  # noqa: E402

_wrapper_spec = importlib.util.spec_from_file_location(
    "release_asset_smoke_wrapper",
    TOOLS_QA / "check_release_asset_smoke.py",
)
assert _wrapper_spec is not None and _wrapper_spec.loader is not None
release_wrapper = importlib.util.module_from_spec(_wrapper_spec)
_wrapper_spec.loader.exec_module(release_wrapper)

FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "release_assets"
PORTABLE_NAME = "OpenSolverWorkbench-v0.1.3rc1-windows-x64-portable.zip"
WHEEL_NAME = "open_solver_workbench-0.1.3rc1-py3-none-any.whl"
SDIST_NAME = "open_solver_workbench-0.1.3rc1.tar.gz"
MANIFEST_NAME = "release_asset_manifest.json"
CHECKSUM_NAME = "SHA256SUMS.txt"
FIXTURE_TARGET = "a6e8d3a8211e02359841d10e1947e16ab847b132"

FIXTURE_HASHES = {
    WHEEL_NAME: "9c1874eae533cbc51a306431fedf71159499d6ac8e1de535175799d0f59ac4a5",
    SDIST_NAME: "034c0bf46d237b3c797fec7499cfc09dbf10da96b1cd6146acdd15e9d7022a38",
    PORTABLE_NAME: "cf8a938c22b9ed0652bfc743012b42c760db274c24bfab8be743a9f1f73b1b2c",
    MANIFEST_NAME: "a60449f6f1f97c7c94959cb40fd4c70c6cabcd23ce5718b54d0f0fa144d4545a",
    CHECKSUM_NAME: "554bf7cd45c13476dc5b240dea6f764e190098e8f6f5fc2e5cee1bf82150575e",
    "README.md": "348c2f2a6600b692393885cdcd59c0a5d4825956aa679fbcc85a7131da19434d",
}

README_RUN_FIRST = """OpenSolver Workbench

This is an unsigned portable build.
It is not an MSI installer.
It has no code signing and is not code-signed.
External solver executables are not bundled.
Verify SHA256SUMS.txt before use.
"""


def _fixture_copy(tmp_path: Path) -> Path:
    target = tmp_path / "assets"
    shutil.copytree(FIXTURE_DIR, target)
    return target


def _identity() -> release_assets.ReleaseIdentity:
    return release_assets.ReleaseIdentity(
        repo=None,
        tag="v0.1.3-rc1",
        version="0.1.3rc1",
        target=FIXTURE_TARGET,
    )


def _verify(
    asset_dir: Path,
    *,
    mode: str = "offline-fixture",
    verification_level: str = "quick",
) -> dict[str, object]:
    return release_assets.verify_asset_dir(
        asset_dir,
        identity=_identity(),
        mode=mode,
        verification_level=verification_level,
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


def _replace_portable_zip(asset_dir: Path, entries: dict[str, bytes]) -> None:
    _write_zip(asset_dir / PORTABLE_NAME, entries)
    _refresh_asset_metadata(asset_dir)


def _refresh_asset_metadata(asset_dir: Path) -> None:
    asset_paths = [
        asset_dir / WHEEL_NAME,
        asset_dir / SDIST_NAME,
        asset_dir / PORTABLE_NAME,
    ]
    manifest = {
        "release_version": "0.1.3rc1",
        "tag": "v0.1.3-rc1",
        "tag_target": FIXTURE_TARGET,
        "assets": [
            {
                "filename": path.name,
                "sha256": release_assets.sha256_file(path),
                "size_bytes": path.stat().st_size,
                "type": (
                    "wheel"
                    if path.name.endswith(".whl")
                    else "sdist"
                    if path.name.endswith(".tar.gz")
                    else "portable_zip"
                ),
            }
            for path in asset_paths
        ],
    }
    manifest_path = asset_dir / MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    checksum_paths = [*asset_paths, manifest_path]
    (asset_dir / CHECKSUM_NAME).write_text(
        "".join(
            f"{release_assets.sha256_file(path)}  {path.name}\n"
            for path in checksum_paths
        ),
        encoding="utf-8",
    )


def _child_args(*items: str) -> argparse.Namespace:
    return release_assets.build_parser().parse_args(list(items))


def _wrapper_args(*items: str) -> argparse.Namespace:
    return release_wrapper.build_parser().parse_args(list(items))


def test_release_asset_fixture_git_attributes_and_hashes_are_frozen() -> None:
    git = shutil.which("git")
    if git is None:
        pytest.skip("git is required to inspect fixture attributes")

    paths = [
        "tests/fixtures/release_assets/release_asset_manifest.json",
        "tests/fixtures/release_assets/SHA256SUMS.txt",
        "tests/fixtures/release_assets/README.md",
    ]
    proc = subprocess.run(
        [git, "check-attr", "text", "--", *paths],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    output = proc.stdout.replace("\\", "/")
    for path in paths:
        assert f"{path}: text: unset" in output
    for name, expected in FIXTURE_HASHES.items():
        assert release_assets.sha256_file(FIXTURE_DIR / name) == expected


def test_fixture_manifest_bytes_match_sha256sums_entry() -> None:
    checksums = release_assets.parse_sha256sums(FIXTURE_DIR / CHECKSUM_NAME)
    assert checksums[MANIFEST_NAME] == release_assets.sha256_file(
        FIXTURE_DIR / MANIFEST_NAME
    )


def test_line_ending_normalized_manifest_would_not_match_fixture_checksum() -> None:
    checksums = release_assets.parse_sha256sums(FIXTURE_DIR / CHECKSUM_NAME)
    raw_manifest = (FIXTURE_DIR / MANIFEST_NAME).read_bytes()
    crlf_manifest = raw_manifest.replace(b"\n", b"\r\n")

    assert b"\r\n" not in raw_manifest
    assert hashlib.sha256(crlf_manifest).hexdigest() != checksums[MANIFEST_NAME]


def test_current_profile_matches_v015_release_authority() -> None:
    profile = release_assets.CURRENT_PROFILE

    assert profile.repo == "CAPTW/OpenSourceWorkBench"
    assert profile.tag == "v0.1.5-rc1"
    assert profile.version == "0.1.5rc1"
    assert profile.target == "85c8144f7ff19159ab02c40adb6483ce6b13c017"
    assert profile.tag_object == "88d683c2e08265c86ee419d0c70c55d93f023893"
    assert profile.release_id == 343292075


@pytest.mark.parametrize(
    ("tag", "version"),
    [("v0.1.5-rc1", "0.1.5rc1"), ("v12.34.56-rc7", "12.34.56rc7")],
)
def test_tag_version_derivation_is_canonical(tag: str, version: str) -> None:
    assert release_assets.version_from_tag(tag) == version


@pytest.mark.parametrize(
    "tag",
    ["0.1.5rc1", "v01.1.5-rc1", "v0.1.5-rc0", "v0.1.5", "v0.1.5-rc01"],
)
def test_noncanonical_tags_fail_closed(tag: str) -> None:
    with pytest.raises(release_assets.ConfigurationError, match="canonical"):
        release_assets.version_from_tag(tag)


def test_child_parser_requires_explicit_mode_and_verification_level() -> None:
    with pytest.raises(SystemExit) as exc:
        release_assets.build_parser().parse_args([])
    assert exc.value.code == 2

    args = _child_args("--mode", "current-live", "--verification-level", "quick")
    assert args.repo is None
    assert args.tag is None
    assert args.expected_version is None
    assert args.expected_target is None


def test_current_live_rejects_conflicting_identity_overrides_before_side_effects(
    tmp_path: Path,
) -> None:
    args = _child_args(
        "--mode",
        "current-live",
        "--verification-level",
        "quick",
        "--download-dir",
        str(tmp_path / "downloads"),
        "--tag",
        "v0.1.5-rc1",
    )

    with pytest.raises(release_assets.ConfigurationError, match="overrides"):
        release_assets.resolve_request(args)
    assert not (tmp_path / "downloads").exists()


def test_explicit_remote_requires_one_complete_atomic_tuple(tmp_path: Path) -> None:
    args = _child_args(
        "--mode",
        "explicit-remote",
        "--verification-level",
        "quick",
        "--download-dir",
        str(tmp_path / "downloads"),
        "--repo",
        "CAPTW/OpenSourceWorkBench",
        "--tag",
        "v0.1.5-rc1",
    )

    with pytest.raises(release_assets.ConfigurationError, match="atomic"):
        release_assets.resolve_request(args)
    assert not (tmp_path / "downloads").exists()


def test_local_set_rejects_mixed_tag_and_version_before_filesystem_access(
    tmp_path: Path,
) -> None:
    args = _child_args(
        "--mode",
        "local-set",
        "--verification-level",
        "quick",
        "--tag",
        "v0.1.5-rc1",
        "--expected-version",
        "0.1.4rc1",
        "--expected-target",
        release_assets.CURRENT_PROFILE.target,
        "--asset-dir",
        str(tmp_path / "missing"),
    )

    with pytest.raises(release_assets.ConfigurationError, match="derive"):
        release_assets.resolve_request(args)


def test_offline_fixture_is_exact_quick_only_and_has_no_remote_provenance() -> None:
    args = _child_args(
        "--mode",
        "offline-fixture",
        "--verification-level",
        "quick",
        "--asset-dir",
        str(FIXTURE_DIR),
    )
    request = release_assets.resolve_request(args)

    assert request.identity == _identity()
    assert request.authority_source == "frozen_offline_fixture"
    assert "no_remote_provenance" in request.assurance

    bad = _child_args(
        "--mode",
        "offline-fixture",
        "--verification-level",
        "full-static",
        "--asset-dir",
        str(FIXTURE_DIR),
    )
    with pytest.raises(release_assets.ConfigurationError, match="quick"):
        release_assets.resolve_request(bad)

    wrong_path = _child_args(
        "--mode",
        "offline-fixture",
        "--verification-level",
        "quick",
        "--asset-dir",
        str(FIXTURE_DIR.parent),
    )
    with pytest.raises(release_assets.ConfigurationError, match="canonical fixture"):
        release_assets.resolve_request(wrong_path)


def test_wrapper_validates_partial_and_unsafe_identity_before_child_execution(
    tmp_path: Path,
) -> None:
    partial = _wrapper_args(
        "--mode",
        "explicit-remote",
        "--verification-level",
        "quick",
        "--download-dir",
        str(tmp_path),
        "--repo",
        "CAPTW/OpenSourceWorkBench",
    )
    with pytest.raises(release_wrapper.WrapperConfigurationError, match="atomic"):
        release_wrapper.validate_args(partial, root=REPO_ROOT)

    unsafe = _wrapper_args(
        "--mode",
        "explicit-remote",
        "--verification-level",
        "quick",
        "--download-dir",
        str(tmp_path),
        "--repo",
        "CAPTW/OpenSourceWorkBench\n--help",
        "--tag",
        "v0.1.5-rc1",
        "--expected-version",
        "0.1.5rc1",
        "--expected-target",
        release_assets.CURRENT_PROFILE.target,
    )
    with pytest.raises(release_wrapper.WrapperConfigurationError, match="repository"):
        release_wrapper.validate_args(unsafe, root=REPO_ROOT)


def test_wrapper_current_live_forwards_no_identity_overrides(tmp_path: Path) -> None:
    args = _wrapper_args(
        "--mode",
        "current-live",
        "--verification-level",
        "quick",
        "--download-dir",
        str(tmp_path),
    )
    release_wrapper.validate_args(args, root=REPO_ROOT)
    command = release_wrapper.build_child_command(
        args,
        root=REPO_ROOT,
        python=Path(sys.executable),
    )

    assert "--mode" in command and "current-live" in command
    for option in ("--repo", "--tag", "--expected-version", "--expected-target"):
        assert option not in command


def test_wrapper_explicit_remote_forwards_atomic_tuple_as_separate_args(
    tmp_path: Path,
) -> None:
    args = _wrapper_args(
        "--mode",
        "explicit-remote",
        "--verification-level",
        "quick",
        "--download-dir",
        str(tmp_path),
        "--repo",
        "CAPTW/OpenSourceWorkBench",
        "--tag",
        "v0.1.5-rc1",
        "--expected-version",
        "0.1.5rc1",
        "--expected-target",
        release_assets.CURRENT_PROFILE.target,
    )
    release_wrapper.validate_args(args, root=REPO_ROOT)
    command = release_wrapper.build_child_command(
        args,
        root=REPO_ROOT,
        python=Path(sys.executable),
    )

    for value in (
        "CAPTW/OpenSourceWorkBench",
        "v0.1.5-rc1",
        "0.1.5rc1",
        release_assets.CURRENT_PROFILE.target,
    ):
        assert command.count(value) == 1


def test_quick_fixture_verification_is_identity_bound_and_structured(
    tmp_path: Path,
) -> None:
    summary = _verify(_fixture_copy(tmp_path))

    assert summary["status"] == "passed"
    assert summary["result_kind"] == "IDENTITY_BOUND_QUICK"
    assert summary["release_readiness"] is False
    assert summary["mode"] == "offline-fixture"
    assert summary["verification_level"] == "quick"
    assert summary["authority_source"] == "frozen_offline_fixture"
    assert summary["network_status"] == "not_used"
    assert summary["download_status"] == "not_applicable"
    assert summary["failures"] == []
    assert summary["asset_inventory_source"] == "manifest+sha256sums+identity"
    assert summary["repo"] is None
    assert summary["tag"] == "v0.1.3-rc1"
    assert summary["expected_version"] == "0.1.3rc1"
    assert summary["expected_target"] == FIXTURE_TARGET
    assert summary["tag_object"] is None
    assert summary["release_id"] is None
    assert summary["asset_dir"] == str(asset_dir := tmp_path / "assets")
    assert asset_dir.is_dir()
    assert summary["warnings"] == []


def test_manifest_checksum_and_directory_inventory_are_exactly_closed(
    tmp_path: Path,
) -> None:
    asset_dir = _fixture_copy(tmp_path)
    (asset_dir / "unexpected.bin").write_bytes(b"extra")

    with pytest.raises(release_assets.AssetSmokeError, match="inventory"):
        _verify(asset_dir)


def test_checksum_or_manifest_mismatch_fails_closed(tmp_path: Path) -> None:
    asset_dir = _fixture_copy(tmp_path)
    (asset_dir / WHEEL_NAME).write_text("tampered\n", encoding="utf-8")

    with pytest.raises(release_assets.AssetSmokeError, match="SHA256"):
        _verify(asset_dir)


def test_manifest_identity_must_match_selected_tuple(tmp_path: Path) -> None:
    asset_dir = _fixture_copy(tmp_path)
    manifest = json.loads((asset_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
    manifest["tag_target"] = "0" * 40
    (asset_dir / MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
    checksums = release_assets.parse_sha256sums(asset_dir / CHECKSUM_NAME)
    checksums[MANIFEST_NAME] = release_assets.sha256_file(asset_dir / MANIFEST_NAME)
    (asset_dir / CHECKSUM_NAME).write_text(
        "".join(f"{digest}  {name}\n" for name, digest in checksums.items()),
        encoding="utf-8",
    )

    with pytest.raises(release_assets.AssetSmokeError, match="target"):
        _verify(asset_dir)


def test_static_archive_inspection_rejects_traversal_without_extraction(
    tmp_path: Path,
) -> None:
    bad_zip = tmp_path / "bad.zip"
    bad_tar = tmp_path / "bad.tar.gz"
    _write_zip(bad_zip, {"../escape.txt": b"no"})
    _write_tar(bad_tar, {"../escape.txt": b"no"})

    with pytest.raises(release_assets.AssetSmokeError, match="path traversal"):
        release_assets.inspect_zip_static(bad_zip, portable=False)
    with pytest.raises(release_assets.AssetSmokeError, match="path traversal"):
        release_assets.inspect_tar_static(bad_tar)
    assert not (tmp_path / "escape.txt").exists()


def test_full_static_never_runs_subprocess_or_extracts_assets(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    asset_dir = _fixture_copy(tmp_path)

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("full-static must not execute subprocesses")

    monkeypatch.setattr(subprocess, "run", forbidden)
    summary = _verify(
        asset_dir,
        mode="local-set",
        verification_level="full-static",
    )

    assert summary["result_kind"] == "IDENTITY_BOUND_FULL_STATIC"
    assert summary["release_readiness"] is False
    assert summary["static_inspection"]["wheel"] == "passed"
    assert summary["static_inspection"]["sdist"] == "passed"
    assert summary["static_inspection"]["portable_zip"] == "passed"
    assert not any(path.name.startswith("extract") for path in tmp_path.iterdir())


def test_local_set_reports_unpinned_local_assurance(tmp_path: Path) -> None:
    asset_dir = _fixture_copy(tmp_path)
    args = _child_args(
        "--mode",
        "local-set",
        "--verification-level",
        "quick",
        "--tag",
        "v0.1.3-rc1",
        "--expected-version",
        "0.1.3rc1",
        "--expected-target",
        FIXTURE_TARGET,
        "--asset-dir",
        str(asset_dir),
    )

    summary = release_assets.run_from_args(args)

    assert summary["authority_source"] == "caller_supplied_local_set"
    assert "unpinned" in summary["assurance"]
    assert summary["network_status"] == "not_used"


def test_remote_snapshot_binds_annotated_tag_and_peeled_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = release_assets.CURRENT_PROFILE
    responses = {
        f"repos/{profile.repo}/releases/tags/{profile.tag}": {
            "id": profile.release_id,
            "tag_name": profile.tag,
            "target_commitish": "develop",
            "assets": [{"name": name} for name in profile.asset_names],
        },
        f"repos/{profile.repo}/git/ref/tags/{profile.tag}": {
            "object": {"type": "tag", "sha": profile.tag_object}
        },
        f"repos/{profile.repo}/git/tags/{profile.tag_object}": {
            "object": {"type": "commit", "sha": profile.target}
        },
    }
    monkeypatch.setattr(release_assets, "gh_api_json", responses.__getitem__)

    snapshot = release_assets.observe_remote_identity(profile)

    assert snapshot.tag_object == profile.tag_object
    assert snapshot.target == profile.target
    assert snapshot.release_id == profile.release_id
    assert snapshot.release_target_context == "develop"


def test_remote_snapshot_change_fails_closed() -> None:
    before = release_assets.RemoteSnapshot(
        repo="CAPTW/OpenSourceWorkBench",
        tag="v0.1.5-rc1",
        version="0.1.5rc1",
        target=release_assets.CURRENT_PROFILE.target,
        tag_object=release_assets.CURRENT_PROFILE.tag_object,
        release_id=343292075,
        release_target_context="develop",
        asset_names=release_assets.CURRENT_PROFILE.asset_names,
    )
    after = replace(before, asset_names=before.asset_names[:-1])

    with pytest.raises(release_assets.AssetSmokeError, match="changed"):
        release_assets.require_unchanged_remote_snapshot(before, after)


def test_remote_directory_is_identity_scoped_new_and_has_assets_leaf(
    tmp_path: Path,
) -> None:
    snapshot = release_assets.RemoteSnapshot(
        repo="CAPTW/OpenSourceWorkBench",
        tag="v0.1.5-rc1",
        version="0.1.5rc1",
        target=release_assets.CURRENT_PROFILE.target,
        tag_object=release_assets.CURRENT_PROFILE.tag_object,
        release_id=343292075,
        release_target_context="develop",
        asset_names=release_assets.CURRENT_PROFILE.asset_names,
    )

    run_root, assets = release_assets.prepare_remote_destination(tmp_path, snapshot)

    assert run_root == tmp_path / "v0.1.5-rc1__release-343292075"
    assert assets == run_root / "assets"
    with pytest.raises(release_assets.AssetSmokeError, match="already exists"):
        release_assets.prepare_remote_destination(tmp_path, snapshot)


@pytest.mark.parametrize("flag", ["--pattern", "--reuse-dir"])
def test_child_legacy_flags_fail_with_migration_result(flag: str) -> None:
    result = release_assets.detect_legacy_flags([flag])
    assert result is not None
    assert result.code == "LEGACY_FLAG_MIGRATION_REQUIRED"
    assert flag in result.message


@pytest.mark.parametrize(
    "flag",
    [
        "--download",
        "--offline-asset-dir",
        "--skip-download",
        "--full-smoke",
        "--skip-portable-exe",
    ],
)
def test_wrapper_legacy_flags_fail_with_migration_result(flag: str) -> None:
    result = release_wrapper.detect_legacy_flags([flag])
    assert result is not None
    assert result.code == "LEGACY_FLAG_MIGRATION_REQUIRED"
    assert flag in result.message


def test_failure_summary_is_structured_and_sanitized() -> None:
    summary = release_assets.failure_summary(
        release_assets.AssetSmokeError(
            "REMOTE_API_FAILED",
            "Authorization: Bearer secret-token",
        ),
        mode="explicit-remote",
        verification_level="quick",
    )

    assert summary["schema_version"] == 1
    assert summary["status"] == "failed"
    assert summary["release_readiness"] is False
    assert summary["failures"] == [
        {"code": "REMOTE_API_FAILED", "message": "remote operation failed"}
    ]
    assert "secret-token" not in json.dumps(summary)


def test_checker_source_contains_no_install_import_or_executable_smoke_path() -> None:
    source = (TOOLS_RELEASE / "check_release_assets.py").read_text(encoding="utf-8")

    for forbidden in (
        "pip install",
        "OpenSolverWorkbench.exe\", \"--help",
        "importlib.import_module",
        "venv.EnvBuilder",
        "archive.extractall",
    ):
        assert forbidden not in source
