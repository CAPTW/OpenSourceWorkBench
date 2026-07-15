#!/usr/bin/env python3
"""Verify an explicitly selected OSW release-asset identity without execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

TAG_RE = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)-rc([1-9]\d*)$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
REMOTE_API_TIMEOUT_SECONDS = 60
REMOTE_DOWNLOAD_TIMEOUT_SECONDS = 300
MANIFEST_NAME = "release_asset_manifest.json"
CHECKSUM_NAME = "SHA256SUMS.txt"
FIXTURE_TARGET = "a6e8d3a8211e02359841d10e1947e16ab847b132"


class AssetSmokeError(RuntimeError):
    """A fail-closed release-asset verification failure."""

    def __init__(self, code: str, message: str, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_code = exit_code


class ConfigurationError(AssetSmokeError):
    """A usage or configuration error detected before operational work."""

    def __init__(self, message: str, *, code: str = "CONFIGURATION_ERROR") -> None:
        super().__init__(code, message, exit_code=2)


@dataclass(frozen=True)
class LegacyFlagResult:
    code: str
    message: str


@dataclass(frozen=True)
class ReleaseIdentity:
    repo: str | None
    tag: str
    version: str
    target: str
    tag_object: str | None = None
    release_id: int | None = None
    asset_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class VerificationRequest:
    mode: str
    verification_level: str
    identity: ReleaseIdentity
    asset_dir: Path | None
    download_dir: Path | None
    json_out: Path | None
    authority_source: str
    assurance: str


@dataclass(frozen=True)
class RemoteSnapshot:
    repo: str
    tag: str
    version: str
    target: str
    tag_object: str
    release_id: int
    release_target_context: str
    asset_names: tuple[str, ...]


def expected_asset_names(version: str) -> tuple[str, ...]:
    return (
        f"open_solver_workbench-{version}-py3-none-any.whl",
        f"open_solver_workbench-{version}.tar.gz",
        f"OpenSolverWorkbench-v{version}-windows-x64-portable.zip",
        MANIFEST_NAME,
        CHECKSUM_NAME,
    )


CURRENT_PROFILE = ReleaseIdentity(
    repo="CAPTW/OpenSourceWorkBench",
    tag="v0.1.5-rc1",
    version="0.1.5rc1",
    target="85c8144f7ff19159ab02c40adb6483ce6b13c017",
    tag_object="88d683c2e08265c86ee419d0c70c55d93f023893",
    release_id=343292075,
    asset_names=expected_asset_names("0.1.5rc1"),
)
FIXTURE_IDENTITY = ReleaseIdentity(
    repo=None,
    tag="v0.1.3-rc1",
    version="0.1.3rc1",
    target=FIXTURE_TARGET,
)


def version_from_tag(tag: str) -> str:
    match = TAG_RE.fullmatch(tag)
    if match is None:
        raise ConfigurationError(
            "release tag must use canonical form vMAJOR.MINOR.PATCH-rcN"
        )
    major, minor, patch, rc = match.groups()
    return f"{major}.{minor}.{patch}rc{rc}"


def _validate_repo(repo: str) -> None:
    if REPO_RE.fullmatch(repo) is None:
        raise ConfigurationError("repository must be one literal OWNER/NAME value")


def _validate_identity(identity: ReleaseIdentity) -> None:
    derived = version_from_tag(identity.tag)
    if identity.version != derived:
        raise ConfigurationError(
            "expected version must derive exactly from the selected canonical tag"
        )
    if SHA_RE.fullmatch(identity.target) is None:
        raise ConfigurationError("expected target must be one lowercase 40-character SHA")
    if identity.repo is not None:
        _validate_repo(identity.repo)
    if identity.tag_object is not None and SHA_RE.fullmatch(identity.tag_object) is None:
        raise ConfigurationError("tag object must be one lowercase 40-character SHA")
    if identity.release_id is not None and identity.release_id <= 0:
        raise ConfigurationError("release id must be a positive integer")


def detect_legacy_flags(argv: Sequence[str]) -> LegacyFlagResult | None:
    for flag in ("--pattern", "--reuse-dir"):
        if any(item == flag or item.startswith(f"{flag}=") for item in argv):
            return LegacyFlagResult(
                "LEGACY_FLAG_MIGRATION_REQUIRED",
                f"{flag} is no longer accepted; select an explicit mode and identity",
            )
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        required=True,
        choices=("current-live", "explicit-remote", "local-set", "offline-fixture"),
    )
    parser.add_argument(
        "--verification-level", required=True, choices=("quick", "full-static")
    )
    parser.add_argument("--repo")
    parser.add_argument("--tag")
    parser.add_argument("--expected-version")
    parser.add_argument("--expected-target")
    parser.add_argument("--asset-dir", type=Path)
    parser.add_argument("--download-dir", type=Path)
    parser.add_argument("--json-out", type=Path)
    return parser


def _require_no_identity_overrides(args: argparse.Namespace) -> None:
    if any(
        value is not None
        for value in (args.repo, args.tag, args.expected_version, args.expected_target)
    ):
        raise ConfigurationError("current profile and fixture modes reject identity overrides")


def _atomic_identity(args: argparse.Namespace, *, require_repo: bool) -> ReleaseIdentity:
    values = (args.tag, args.expected_version, args.expected_target)
    if require_repo:
        values = (args.repo, *values)
    if any(value is None for value in values):
        raise ConfigurationError("the selected mode requires one complete atomic identity tuple")
    if not require_repo and args.repo is not None:
        raise ConfigurationError("local-set does not accept a repository identity")
    identity = ReleaseIdentity(
        repo=args.repo if require_repo else None,
        tag=args.tag,
        version=args.expected_version,
        target=args.expected_target,
        asset_names=expected_asset_names(args.expected_version),
    )
    _validate_identity(identity)
    return identity


def resolve_request(args: argparse.Namespace) -> VerificationRequest:
    mode = args.mode
    level = args.verification_level
    if mode == "current-live":
        _require_no_identity_overrides(args)
        if args.asset_dir is not None or args.download_dir is None:
            raise ConfigurationError("current-live requires only --download-dir")
        identity = CURRENT_PROFILE
        authority = "pinned_current_release_profile"
        assurance = "pinned_remote_identity_with_pre_and_post_observation"
    elif mode == "explicit-remote":
        identity = _atomic_identity(args, require_repo=True)
        if args.asset_dir is not None or args.download_dir is None:
            raise ConfigurationError("explicit-remote requires --download-dir and no asset dir")
        authority = "caller_supplied_remote_identity"
        assurance = "caller_supplied_remote_identity_with_pre_and_post_observation"
    elif mode == "local-set":
        identity = _atomic_identity(args, require_repo=False)
        if args.asset_dir is None or args.download_dir is not None:
            raise ConfigurationError("local-set requires --asset-dir and no download dir")
        authority = "caller_supplied_local_set"
        assurance = "unpinned_local_asset_identity"
    else:
        _require_no_identity_overrides(args)
        if level != "quick":
            raise ConfigurationError("offline-fixture is intentionally quick-only")
        if args.asset_dir is None or args.download_dir is not None:
            raise ConfigurationError("offline-fixture requires --asset-dir and no download dir")
        canonical_fixture = (
            Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "release_assets"
        )
        if args.asset_dir.resolve() != canonical_fixture:
            raise ConfigurationError(
                "offline-fixture requires the canonical fixture directory"
            )
        identity = FIXTURE_IDENTITY
        authority = "frozen_offline_fixture"
        assurance = "frozen_fixture_bytes_with_no_remote_provenance"
    return VerificationRequest(
        mode=mode,
        verification_level=level,
        identity=identity,
        asset_dir=args.asset_dir,
        download_dir=args.download_dir,
        json_out=args.json_out,
        authority_source=authority,
        assurance=assurance,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_sha256sums(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise AssetSmokeError("CHECKSUM_READ_FAILED", "could not read SHA256SUMS.txt") from exc
    result: dict[str, str] = {}
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  ([^/\\]+)", line)
        if match is None or match.group(2) in result:
            raise AssetSmokeError(
                "CHECKSUM_FORMAT_INVALID", "SHA256SUMS.txt has an invalid or duplicate entry"
            )
        result[match.group(2)] = match.group(1)
    if not result:
        raise AssetSmokeError("CHECKSUM_FORMAT_INVALID", "SHA256SUMS.txt is empty")
    return result


def _load_manifest(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AssetSmokeError("MANIFEST_INVALID", "release manifest is not valid JSON") from exc
    if not isinstance(value, dict):
        raise AssetSmokeError("MANIFEST_INVALID", "release manifest must be an object")
    return value


def _payload_names(version: str) -> tuple[str, str, str]:
    names = expected_asset_names(version)
    return names[0], names[1], names[2]


def _validate_inventory(
    asset_dir: Path,
    *,
    mode: str,
    expected_names: set[str],
) -> None:
    try:
        actual = {path.name for path in asset_dir.iterdir() if path.is_file()}
        non_files = [path.name for path in asset_dir.iterdir() if not path.is_file()]
    except OSError as exc:
        raise AssetSmokeError("ASSET_DIRECTORY_INVALID", "asset directory is unreadable") from exc
    allowed = set(expected_names)
    if mode in {"offline-fixture", "local-set"}:
        allowed.add("README.md")
    if actual != allowed or non_files:
        raise AssetSmokeError(
            "ASSET_INVENTORY_MISMATCH",
            "asset directory inventory does not exactly match the selected identity",
        )


def _validate_manifest(
    manifest: Mapping[str, Any], identity: ReleaseIdentity
) -> dict[str, Mapping[str, Any]]:
    if manifest.get("tag") != identity.tag:
        raise AssetSmokeError("MANIFEST_TAG_MISMATCH", "manifest tag does not match identity")
    if manifest.get("release_version") != identity.version:
        raise AssetSmokeError(
            "MANIFEST_VERSION_MISMATCH", "manifest version does not match identity"
        )
    if manifest.get("tag_target") != identity.target:
        raise AssetSmokeError(
            "MANIFEST_TARGET_MISMATCH", "manifest target does not match identity"
        )
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise AssetSmokeError("MANIFEST_ASSETS_INVALID", "manifest assets must be a list")
    indexed: dict[str, Mapping[str, Any]] = {}
    for value in assets:
        if not isinstance(value, dict) or not isinstance(value.get("filename"), str):
            raise AssetSmokeError(
                "MANIFEST_ASSETS_INVALID", "manifest contains an invalid asset observation"
            )
        name = value["filename"]
        if name in indexed:
            raise AssetSmokeError("MANIFEST_ASSETS_INVALID", "manifest asset names must be unique")
        indexed[name] = value
    if set(indexed) != set(_payload_names(identity.version)):
        raise AssetSmokeError(
            "MANIFEST_ASSET_INVENTORY_MISMATCH",
            "manifest asset inventory does not exactly match the selected identity",
        )
    return indexed


def _safe_archive_name(name: str) -> None:
    normalized = name.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if (
        not normalized
        or normalized.startswith("/")
        or re.match(r"^[A-Za-z]:", normalized)
        or ".." in pure.parts
    ):
        raise AssetSmokeError(
            "ARCHIVE_PATH_TRAVERSAL", "archive contains a path traversal entry"
        )


def inspect_zip_static(path: Path, *, portable: bool) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                _safe_archive_name(info.filename)
                unix_mode = (info.external_attr >> 16) & 0o170000
                if unix_mode == 0o120000:
                    raise AssetSmokeError(
                        "ARCHIVE_LINK_UNSAFE", "archive contains a symbolic link entry"
                    )
            if portable:
                required = {
                    "OpenSolverWorkbench/OpenSolverWorkbench.exe",
                    "OpenSolverWorkbench/README_RUN_FIRST.txt",
                    "OpenSolverWorkbench/LICENSE",
                }
                if not required.issubset(set(archive.namelist())):
                    raise AssetSmokeError(
                        "PORTABLE_LAYOUT_INVALID", "portable archive layout is incomplete"
                    )
                readme = archive.read(
                    "OpenSolverWorkbench/README_RUN_FIRST.txt"
                ).decode("utf-8", errors="strict")
                required_phrases = (
                    "unsigned portable build",
                    "not an MSI installer",
                    "not code-signed",
                    "External solver executables are not bundled",
                    "Verify SHA256SUMS.txt",
                )
                if any(phrase not in readme for phrase in required_phrases):
                    raise AssetSmokeError(
                        "PORTABLE_DISCLOSURE_INVALID",
                        "portable README_RUN_FIRST disclosure is incomplete",
                    )
    except AssetSmokeError:
        raise
    except (OSError, UnicodeError, zipfile.BadZipFile) as exc:
        raise AssetSmokeError("ZIP_INVALID", "asset is not a valid ZIP archive") from exc


def inspect_tar_static(path: Path) -> None:
    try:
        with tarfile.open(path, "r:gz") as archive:
            for member in archive.getmembers():
                _safe_archive_name(member.name)
                if member.issym() or member.islnk() or member.isdev():
                    raise AssetSmokeError(
                        "ARCHIVE_LINK_UNSAFE", "archive contains a link or device entry"
                    )
    except AssetSmokeError:
        raise
    except (OSError, tarfile.TarError) as exc:
        raise AssetSmokeError("TAR_INVALID", "asset is not a valid tar archive") from exc


def _base_summary(
    *, mode: str, verification_level: str, identity: ReleaseIdentity
) -> dict[str, Any]:
    remote = mode.endswith("remote") or mode == "current-live"
    authority = {
        "offline-fixture": "frozen_offline_fixture",
        "local-set": "caller_supplied_local_set",
        "current-live": "pinned_current_release_profile",
        "explicit-remote": "caller_supplied_remote_identity",
    }[mode]
    assurance = {
        "offline-fixture": "frozen_fixture_bytes_with_no_remote_provenance",
        "local-set": "unpinned_local_asset_identity",
        "current-live": "pinned_remote_identity_with_pre_and_post_observation",
        "explicit-remote": "caller_supplied_remote_identity_with_pre_and_post_observation",
    }[mode]
    return {
        "schema_version": 1,
        "status": "passed",
        "result_kind": (
            "IDENTITY_BOUND_QUICK"
            if verification_level == "quick"
            else "IDENTITY_BOUND_FULL_STATIC"
        ),
        "release_readiness": False,
        "mode": mode,
        "verification_level": verification_level,
        "authority_source": authority,
        "assurance": assurance,
        "identity": asdict(identity),
        "repo": identity.repo,
        "tag": identity.tag,
        "expected_version": identity.version,
        "expected_target": identity.target,
        "tag_object": identity.tag_object,
        "release_id": identity.release_id,
        "network_status": "used" if remote else "not_used",
        "download_status": "downloaded" if remote else "not_applicable",
        "asset_inventory_source": "manifest+sha256sums+identity",
        "asset_dir": None,
        "warnings": [],
        "failures": [],
    }


def verify_asset_dir(
    asset_dir: Path,
    *,
    identity: ReleaseIdentity,
    mode: str,
    verification_level: str,
) -> dict[str, Any]:
    _validate_identity(identity)
    if mode not in {"current-live", "explicit-remote", "local-set", "offline-fixture"}:
        raise ConfigurationError("unknown verification mode")
    if verification_level not in {"quick", "full-static"}:
        raise ConfigurationError("unknown verification level")
    if not asset_dir.is_dir():
        raise AssetSmokeError("ASSET_DIRECTORY_INVALID", "asset directory does not exist")

    expected_names = set(expected_asset_names(identity.version))
    _validate_inventory(asset_dir, mode=mode, expected_names=expected_names)
    manifest = _load_manifest(asset_dir / MANIFEST_NAME)
    manifest_assets = _validate_manifest(manifest, identity)
    sums = parse_sha256sums(asset_dir / CHECKSUM_NAME)
    expected_sum_names = set(_payload_names(identity.version)) | {MANIFEST_NAME}
    if set(sums) != expected_sum_names:
        raise AssetSmokeError(
            "CHECKSUM_INVENTORY_MISMATCH",
            "SHA256 inventory does not exactly match manifest and selected identity",
        )
    observations: dict[str, dict[str, Any]] = {}
    for name in sorted(expected_sum_names):
        path = asset_dir / name
        if not path.is_file():
            raise AssetSmokeError("ASSET_MISSING", f"required asset is missing: {name}")
        digest = sha256_file(path)
        if digest != sums[name]:
            raise AssetSmokeError("SHA256_MISMATCH", f"SHA256 mismatch for {name}")
        observations[name] = {"sha256": digest, "size_bytes": path.stat().st_size}
        if name != MANIFEST_NAME:
            entry = manifest_assets[name]
            if entry.get("sha256") != digest or entry.get("size_bytes") != path.stat().st_size:
                raise AssetSmokeError(
                    "MANIFEST_ASSET_MISMATCH",
                    f"manifest hash or size does not match {name}",
                )

    summary = _base_summary(
        mode=mode, verification_level=verification_level, identity=identity
    )
    summary["asset_dir"] = str(asset_dir)
    summary["assets"] = observations
    if verification_level == "full-static":
        wheel, sdist, portable = _payload_names(identity.version)
        inspect_zip_static(asset_dir / wheel, portable=False)
        inspect_tar_static(asset_dir / sdist)
        inspect_zip_static(asset_dir / portable, portable=True)
        summary["static_inspection"] = {
            "wheel": "passed",
            "sdist": "passed",
            "portable_zip": "passed",
        }
    else:
        summary["static_inspection"] = "not_requested"
    return summary


def gh_api_json(endpoint: str) -> Mapping[str, Any]:
    gh = shutil.which("gh")
    if gh is None:
        raise AssetSmokeError("GH_UNAVAILABLE", "GitHub CLI is unavailable")
    try:
        proc = subprocess.run(
            [gh, "api", endpoint],
            text=True,
            capture_output=True,
            check=False,
            timeout=REMOTE_API_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssetSmokeError("REMOTE_API_TIMEOUT", "remote API operation timed out") from exc
    if proc.returncode != 0:
        raise AssetSmokeError("REMOTE_API_FAILED", "remote API operation failed")
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssetSmokeError("REMOTE_API_INVALID", "remote API returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise AssetSmokeError("REMOTE_API_INVALID", "remote API response must be an object")
    return value


def _require_mapping(value: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise AssetSmokeError("REMOTE_IDENTITY_INVALID", f"remote {label} is malformed")
    return value


def observe_remote_identity(identity: ReleaseIdentity) -> RemoteSnapshot:
    if identity.repo is None:
        raise ConfigurationError("remote identity requires a repository")
    _validate_identity(identity)
    repo = identity.repo
    release = gh_api_json(f"repos/{repo}/releases/tags/{identity.tag}")
    ref = gh_api_json(f"repos/{repo}/git/ref/tags/{identity.tag}")
    ref_object = _require_mapping(ref.get("object"), label="tag reference")
    if ref_object.get("type") != "tag" or not isinstance(ref_object.get("sha"), str):
        raise AssetSmokeError(
            "REMOTE_TAG_NOT_ANNOTATED", "selected remote tag is not an annotated tag"
        )
    tag_object = ref_object["sha"]
    if SHA_RE.fullmatch(tag_object) is None:
        raise AssetSmokeError(
            "REMOTE_TAG_OBJECT_INVALID", "annotated tag object SHA is malformed"
        )
    tag_data = gh_api_json(f"repos/{repo}/git/tags/{tag_object}")
    peeled = _require_mapping(tag_data.get("object"), label="annotated tag target")
    if peeled.get("type") != "commit" or not isinstance(peeled.get("sha"), str):
        raise AssetSmokeError(
            "REMOTE_TAG_TARGET_INVALID", "annotated tag does not peel directly to a commit"
        )
    target = peeled["sha"]
    if SHA_RE.fullmatch(target) is None:
        raise AssetSmokeError(
            "REMOTE_TAG_TARGET_INVALID", "peeled tag target SHA is malformed"
        )
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise AssetSmokeError("REMOTE_RELEASE_INVALID", "release assets observation is malformed")
    asset_names: list[str] = []
    for asset in assets:
        if not isinstance(asset, dict) or not isinstance(asset.get("name"), str):
            raise AssetSmokeError("REMOTE_RELEASE_INVALID", "release asset is malformed")
        asset_names.append(asset["name"])
    expected_names = identity.asset_names or expected_asset_names(identity.version)
    if len(asset_names) != len(set(asset_names)) or set(asset_names) != set(expected_names):
        raise AssetSmokeError(
            "REMOTE_ASSET_INVENTORY_MISMATCH",
            "remote asset inventory does not exactly match the selected identity",
        )
    release_id = release.get("id")
    if type(release_id) is not int or release_id <= 0:
        raise AssetSmokeError("REMOTE_RELEASE_INVALID", "release id is malformed")
    if release.get("tag_name") != identity.tag:
        raise AssetSmokeError("REMOTE_RELEASE_TAG_MISMATCH", "release tag changed")
    target_context = release.get("target_commitish")
    if not isinstance(target_context, str):
        raise AssetSmokeError("REMOTE_RELEASE_INVALID", "release target context is malformed")
    if target != identity.target:
        raise AssetSmokeError("REMOTE_TARGET_MISMATCH", "peeled tag target does not match identity")
    if identity.tag_object is not None and tag_object != identity.tag_object:
        raise AssetSmokeError("REMOTE_TAG_OBJECT_MISMATCH", "annotated tag object changed")
    if identity.release_id is not None and release_id != identity.release_id:
        raise AssetSmokeError("REMOTE_RELEASE_ID_MISMATCH", "release id changed")
    return RemoteSnapshot(
        repo=repo,
        tag=identity.tag,
        version=identity.version,
        target=target,
        tag_object=tag_object,
        release_id=release_id,
        release_target_context=target_context,
        asset_names=tuple(sorted(asset_names)),
    )


def require_unchanged_remote_snapshot(
    before: RemoteSnapshot, after: RemoteSnapshot
) -> None:
    if before != after:
        raise AssetSmokeError(
            "REMOTE_IDENTITY_CHANGED",
            "remote release identity changed during verification",
        )


def prepare_remote_destination(
    download_root: Path, snapshot: RemoteSnapshot
) -> tuple[Path, Path]:
    run_root = download_root / f"{snapshot.tag}__release-{snapshot.release_id}"
    if run_root.exists():
        raise AssetSmokeError(
            "DOWNLOAD_DESTINATION_EXISTS", "identity-scoped download destination already exists"
        )
    assets = run_root / "assets"
    try:
        assets.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise AssetSmokeError(
            "DOWNLOAD_DESTINATION_FAILED", "could not create identity-scoped destination"
        ) from exc
    return run_root, assets


def _download_remote_assets(snapshot: RemoteSnapshot, assets: Path) -> None:
    gh = shutil.which("gh")
    if gh is None:
        raise AssetSmokeError("GH_UNAVAILABLE", "GitHub CLI is unavailable")
    command = [
        gh,
        "release",
        "download",
        snapshot.tag,
        "--repo",
        snapshot.repo,
        "--dir",
        str(assets),
    ]
    try:
        proc = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=REMOTE_DOWNLOAD_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssetSmokeError("REMOTE_DOWNLOAD_TIMEOUT", "release download timed out") from exc
    if proc.returncode != 0:
        raise AssetSmokeError("REMOTE_DOWNLOAD_FAILED", "release download failed")


def _identity_from_snapshot(snapshot: RemoteSnapshot) -> ReleaseIdentity:
    return ReleaseIdentity(
        repo=snapshot.repo,
        tag=snapshot.tag,
        version=snapshot.version,
        target=snapshot.target,
        tag_object=snapshot.tag_object,
        release_id=snapshot.release_id,
        asset_names=snapshot.asset_names,
    )


def run_from_args(args: argparse.Namespace) -> dict[str, Any]:
    request = resolve_request(args)
    if request.mode in {"local-set", "offline-fixture"}:
        assert request.asset_dir is not None
        return verify_asset_dir(
            request.asset_dir,
            identity=request.identity,
            mode=request.mode,
            verification_level=request.verification_level,
        )

    assert request.download_dir is not None
    before = observe_remote_identity(request.identity)
    run_root, assets = prepare_remote_destination(request.download_dir, before)
    _download_remote_assets(before, assets)
    summary = verify_asset_dir(
        assets,
        identity=_identity_from_snapshot(before),
        mode=request.mode,
        verification_level=request.verification_level,
    )
    after = observe_remote_identity(request.identity)
    require_unchanged_remote_snapshot(before, after)
    summary["remote_snapshot"] = asdict(before)
    summary["run_root"] = str(run_root)
    summary["asset_dir"] = str(assets)
    _write_json(run_root / "summary.json", summary)
    return summary


def _sanitize_failure_message(error: AssetSmokeError) -> str:
    if error.code.startswith("REMOTE_") or error.code == "GH_UNAVAILABLE":
        return "remote operation failed"
    return error.message.replace("\r", " ").replace("\n", " ")


def failure_summary(
    error: AssetSmokeError, *, mode: str, verification_level: str
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "failed",
        "result_kind": "VERIFICATION_FAILED",
        "release_readiness": False,
        "mode": mode,
        "verification_level": verification_level,
        "authority_source": None,
        "assurance": "verification_failed",
        "repo": None,
        "tag": None,
        "expected_version": None,
        "expected_target": None,
        "tag_object": None,
        "release_id": None,
        "asset_inventory_source": None,
        "network_status": "unknown",
        "download_status": "unknown",
        "asset_dir": None,
        "warnings": [],
        "failures": [
            {"code": error.code, "message": _sanitize_failure_message(error)}
        ],
    }


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    legacy = detect_legacy_flags(raw)
    if legacy is not None:
        print(f"[{legacy.code}] {legacy.message}", file=sys.stderr)
        return 2
    parser = build_parser()
    args = parser.parse_args(raw)
    try:
        summary = run_from_args(args)
    except AssetSmokeError as error:
        summary = failure_summary(
            error, mode=args.mode, verification_level=args.verification_level
        )
        if args.json_out is not None:
            _write_json(args.json_out, summary)
        print(f"[{error.code}] {_sanitize_failure_message(error)}", file=sys.stderr)
        return error.exit_code
    if args.json_out is not None:
        _write_json(args.json_out, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
