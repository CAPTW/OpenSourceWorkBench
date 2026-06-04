#!/usr/bin/env python3
"""Verify OSW GitHub Release assets without mutating the release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import venv
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

EXPECTED_TAG_TARGETS = {
    "v0.1.3-rc1": "a6e8d3a8211e02359841d10e1947e16ab847b132",
}

FORBIDDEN_ARCHIVE_PARTS = {".git", ".codex", ".venv"}
SECRET_NAME_PATTERN = re.compile(
    r"(^id_rsa$|^id_ed25519$|\.pem$|\.key$|password|token|secret)",
    re.IGNORECASE,
)
PORTABLE_README_NAME = "README_RUN_FIRST.txt"
PORTABLE_README_CHECKS = {
    "unsigned_warning": ("unsigned",),
    "no_msi_warning": ("no msi", "not an msi"),
    "no_code_signing_warning": ("no code signing", "not code-signed", "not code signed"),
    "no_bundled_solver_warning": (
        "no bundled external solvers",
        "external solvers are not bundled",
        "external solver executables are not bundled",
    ),
    "checksum_reference": ("sha256sums.txt", "sha256", "checksum"),
}


class AssetSmokeError(RuntimeError):
    """Raised for unsafe archives or failed smoke checks."""


@dataclass(frozen=True)
class AssetFile:
    path: Path
    asset_type: str

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def size(self) -> int:
        return self.path.stat().st_size


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_sha256sums(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
            raise AssetSmokeError(f"invalid SHA256SUMS line {line_number}: {raw_line!r}")
        filename = parts[1].strip()
        if filename.startswith("*"):
            filename = filename[1:]
        entries[Path(filename).name] = parts[0].lower()
    return entries


def _normalized_archive_name(name: str) -> str:
    normalized = name.replace("\\", "/")
    if not normalized or normalized.startswith("/"):
        raise AssetSmokeError(f"archive entry is absolute or empty: {name!r}")
    if re.match(r"^[A-Za-z]:", normalized):
        raise AssetSmokeError(f"archive entry uses a drive path: {name!r}")
    parts = PurePosixPath(normalized).parts
    if any(part == ".." for part in parts):
        raise AssetSmokeError(f"archive entry uses path traversal: {name!r}")
    return normalized


def _reject_forbidden_portable_entry(name: str) -> None:
    normalized = _normalized_archive_name(name)
    parts = [part.lower() for part in PurePosixPath(normalized).parts]
    if any(part in FORBIDDEN_ARCHIVE_PARTS for part in parts):
        raise AssetSmokeError(f"portable ZIP contains forbidden entry: {name!r}")
    if parts and SECRET_NAME_PATTERN.search(parts[-1]):
        raise AssetSmokeError(f"portable ZIP contains secret-like entry: {name!r}")


def validate_zip_entries(path: Path, *, portable: bool = False) -> None:
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            _normalized_archive_name(info.filename)
            if portable:
                _reject_forbidden_portable_entry(info.filename)


def safe_extract_zip(path: Path, destination: Path, *, portable: bool = False) -> None:
    validate_zip_entries(path, portable=portable)
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as archive:
        archive.extractall(destination)


def _has_any_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def inspect_portable_zip_ux(path: Path) -> dict[str, Any]:
    """Inspect portable ZIP user-facing files and warnings."""

    validate_zip_entries(path, portable=True)
    result: dict[str, Any] = {
        "asset": path.name,
        "top_level_entries": [],
        "executable_paths": [],
        "has_readme_run_first": False,
        "readme_run_first_path": None,
        "has_license": False,
        "license_paths": [],
        "checks": {},
        "warnings": [],
    }

    with zipfile.ZipFile(path) as archive:
        names = [info.filename for info in archive.infolist() if not info.is_dir()]
        top_levels = sorted(
            {
                PurePosixPath(name.replace("\\", "/")).parts[0]
                for name in names
                if PurePosixPath(name.replace("\\", "/")).parts
            }
        )
        result["top_level_entries"] = top_levels
        result["executable_paths"] = [
            name
            for name in names
            if PurePosixPath(name.replace("\\", "/")).name == "OpenSolverWorkbench.exe"
        ]
        license_paths = [
            name
            for name in names
            if PurePosixPath(name.replace("\\", "/")).name.upper().startswith("LICENSE")
        ]
        result["license_paths"] = license_paths
        result["has_license"] = bool(license_paths)

        readme_names = [
            name
            for name in names
            if PurePosixPath(name.replace("\\", "/")).name.casefold()
            == PORTABLE_README_NAME.casefold()
        ]
        if not readme_names:
            result["warnings"].append(
                "portable ZIP does not include README_RUN_FIRST.txt; "
                "future builds should include it"
            )
        else:
            result["has_readme_run_first"] = True
            result["readme_run_first_path"] = readme_names[0]
            raw_text = archive.read(readme_names[0]).decode("utf-8", errors="replace")
            text = raw_text.lower()
            for key, phrases in PORTABLE_README_CHECKS.items():
                passed = _has_any_phrase(text, phrases)
                result["checks"][key] = passed
                if not passed:
                    result["warnings"].append(
                        f"README_RUN_FIRST.txt missing {key.replace('_', ' ')}"
                    )

        if not result["has_license"]:
            result["warnings"].append("portable ZIP does not include a LICENSE file")
        if len(top_levels) != 1:
            result["warnings"].append("portable ZIP should use one top-level folder")
        if not result["executable_paths"]:
            result["warnings"].append("portable ZIP does not include OpenSolverWorkbench.exe")

    return result


def validate_tar_entries(path: Path) -> None:
    with tarfile.open(path, "r:*") as archive:
        for member in archive.getmembers():
            _normalized_archive_name(member.name)
            if member.issym() or member.islnk():
                raise AssetSmokeError(f"tar archive contains link entry: {member.name!r}")


def safe_extract_tar(path: Path, destination: Path) -> None:
    validate_tar_entries(path)
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "r:*") as archive:
        archive.extractall(destination, filter="data")


def classify_asset(path: Path) -> str | None:
    name = path.name
    lower = name.lower()
    if name == "SHA256SUMS.txt":
        return "checksums"
    if name == "release_asset_manifest.json":
        return "manifest"
    if lower.endswith(".whl"):
        return "wheel"
    if lower.endswith(".tar.gz"):
        return "sdist"
    if lower.endswith(".zip") and ("portable" in lower or "opensolverworkbench" in lower):
        return "portable_zip"
    return None


def find_assets(asset_dir: Path) -> dict[str, list[AssetFile]]:
    assets: dict[str, list[AssetFile]] = {
        "wheel": [],
        "sdist": [],
        "portable_zip": [],
        "checksums": [],
        "manifest": [],
    }
    for path in sorted(asset_dir.iterdir()):
        if not path.is_file():
            continue
        asset_type = classify_asset(path)
        if asset_type is not None:
            assets[asset_type].append(AssetFile(path=path, asset_type=asset_type))
    return assets


def _first_asset(assets: dict[str, list[AssetFile]], asset_type: str) -> AssetFile | None:
    matches = assets.get(asset_type, [])
    return matches[0] if matches else None


def _run(
    args: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _run_python_smoke(
    python_exe: Path,
    *,
    expected_version: str | None,
    summary: dict[str, Any],
) -> None:
    version_proc = _run([str(python_exe), "-m", "osw.cli", "--version"])
    if version_proc.returncode != 0:
        raise AssetSmokeError(
            "installed package CLI --version failed: "
            f"{version_proc.stderr.strip() or version_proc.stdout.strip()}"
        )
    version_output = version_proc.stdout.strip()
    summary["smoke"]["cli_version"] = version_output
    if expected_version and version_output != f"osw {expected_version}":
        raise AssetSmokeError(
            f"expected CLI version osw {expected_version}, got {version_output!r}"
        )
    help_proc = _run([str(python_exe), "-m", "osw.cli", "--help"])
    if help_proc.returncode != 0:
        raise AssetSmokeError(
            "installed package CLI --help failed: "
            f"{help_proc.stderr.strip() or help_proc.stdout.strip()}"
        )


def smoke_wheel(
    wheel: Path,
    *,
    asset_dir: Path,
    expected_version: str | None,
    summary: dict[str, Any],
) -> None:
    with tempfile.TemporaryDirectory(prefix="osw-wheel-smoke-", dir=asset_dir) as tmp:
        venv_dir = Path(tmp) / ".venv"
        venv.create(venv_dir, with_pip=True)
        python_exe = _venv_python(venv_dir)
        install_proc = _run(
            [str(python_exe), "-m", "pip", "install", str(wheel)],
            timeout=180,
        )
        if install_proc.returncode != 0:
            raise AssetSmokeError(
                "wheel install failed: "
                f"{install_proc.stderr.strip() or install_proc.stdout.strip()}"
            )
        _run_python_smoke(
            python_exe,
            expected_version=expected_version,
            summary=summary,
        )
    summary["smoke"]["wheel"] = "passed"


def smoke_sdist(
    sdist: Path,
    *,
    asset_dir: Path,
    expected_version: str | None,
    full_smoke: bool,
    summary: dict[str, Any],
) -> None:
    with tempfile.TemporaryDirectory(prefix="osw-sdist-smoke-", dir=asset_dir) as tmp:
        extract_dir = Path(tmp) / "extract"
        safe_extract_tar(sdist, extract_dir)
        pyprojects = list(extract_dir.rglob("pyproject.toml"))
        init_files = list(extract_dir.rglob("src/osw/__init__.py"))
        if not pyprojects:
            raise AssetSmokeError("sdist does not contain pyproject.toml")
        if not init_files:
            raise AssetSmokeError("sdist does not contain src/osw/__init__.py")
        if full_smoke:
            venv_dir = Path(tmp) / ".venv"
            venv.create(venv_dir, with_pip=True)
            python_exe = _venv_python(venv_dir)
            install_proc = _run(
                [str(python_exe), "-m", "pip", "install", str(sdist)],
                timeout=180,
            )
            if install_proc.returncode != 0:
                raise AssetSmokeError(
                    "sdist install failed: "
                    f"{install_proc.stderr.strip() or install_proc.stdout.strip()}"
                )
            _run_python_smoke(
                python_exe,
                expected_version=expected_version,
                summary=summary,
            )
    summary["smoke"]["sdist"] = "passed"


def smoke_portable_zip(
    portable_zip: Path,
    *,
    asset_dir: Path,
    skip_portable_exe: bool,
    summary: dict[str, Any],
) -> None:
    with tempfile.TemporaryDirectory(prefix="osw-portable-smoke-", dir=asset_dir) as tmp:
        extract_dir = Path(tmp) / "portable"
        safe_extract_zip(portable_zip, extract_dir, portable=True)
        exe_candidates = list(extract_dir.rglob("OpenSolverWorkbench.exe"))
        if platform.system() != "Windows":
            summary["warnings"].append("portable executable smoke skipped on non-Windows")
        elif skip_portable_exe:
            summary["warnings"].append("portable executable smoke skipped by request")
        else:
            if not exe_candidates:
                raise AssetSmokeError("portable ZIP does not contain OpenSolverWorkbench.exe")
            proc = _run([str(exe_candidates[0]), "--help"], timeout=90)
            if proc.returncode != 0:
                raise AssetSmokeError(
                    "portable executable --help failed: "
                    f"{proc.stderr.strip() or proc.stdout.strip()}"
                )
    summary["smoke"]["portable_zip"] = "passed"


def _manifest_assets(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    raw_assets = manifest.get("assets", [])
    if not isinstance(raw_assets, list):
        raise AssetSmokeError("release_asset_manifest.json assets must be a list")
    return [item for item in raw_assets if isinstance(item, dict)]


def verify_manifest(
    manifest_path: Path,
    *,
    asset_dir: Path,
    tag: str | None,
    actual_hashes: dict[str, str],
    summary: dict[str, Any],
) -> None:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssetSmokeError(f"release_asset_manifest.json is invalid JSON: {exc}") from exc

    manifest_tag = manifest.get("tag")
    if tag and manifest_tag and manifest_tag != tag:
        raise AssetSmokeError(f"manifest tag {manifest_tag!r} does not match {tag!r}")

    expected_target = EXPECTED_TAG_TARGETS.get(tag or "")
    manifest_target = manifest.get("tag_target")
    if expected_target and manifest_target and manifest_target != expected_target:
        raise AssetSmokeError(
            f"manifest tag target {manifest_target!r} does not match {expected_target!r}"
        )

    for item in _manifest_assets(manifest):
        filename = str(item.get("filename") or item.get("name") or "")
        if not filename:
            raise AssetSmokeError("manifest asset is missing filename")
        filename = Path(filename).name
        path = asset_dir / filename
        if not path.exists():
            raise AssetSmokeError(f"manifest asset is missing from asset dir: {filename}")

        expected_size = item.get("size_bytes", item.get("size"))
        if expected_size is not None and int(expected_size) != path.stat().st_size:
            raise AssetSmokeError(f"manifest size mismatch for {filename}")

        expected_hash = str(item.get("sha256") or "").lower()
        if expected_hash:
            actual_hash = actual_hashes.get(filename) or sha256_file(path)
            actual_hashes[filename] = actual_hash
            if actual_hash != expected_hash:
                raise AssetSmokeError(f"manifest SHA256 mismatch for {filename}")

    summary["manifest"] = {
        "tag": manifest_tag,
        "tag_target": manifest_target,
        "assets": [
            str(item.get("filename") or item.get("name"))
            for item in _manifest_assets(manifest)
        ],
    }


def verify_asset_dir(
    asset_dir: Path,
    *,
    tag: str | None,
    expected_version: str | None,
    full_smoke: bool,
    skip_portable_exe: bool,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "status": "passed",
        "asset_dir": str(asset_dir),
        "tag": tag,
        "expected_version": expected_version,
        "assets": [],
        "warnings": [],
        "failures": [],
        "smoke": {},
    }

    if not asset_dir.exists() or not asset_dir.is_dir():
        raise AssetSmokeError(f"asset directory does not exist: {asset_dir}")

    assets = find_assets(asset_dir)
    for asset_type, matches in assets.items():
        if not matches:
            summary["failures"].append(f"missing expected asset type: {asset_type}")
        for asset in matches:
            digest = sha256_file(asset.path) if asset.path.is_file() else ""
            summary["assets"].append(
                {
                    "filename": asset.name,
                    "type": asset.asset_type,
                    "size_bytes": asset.size,
                    "sha256": digest,
                }
            )
            if asset.size <= 0:
                summary["failures"].append(f"asset has zero size: {asset.name}")

    if summary["failures"]:
        summary["status"] = "failed"
        return summary

    actual_hashes = {
        item["filename"]: item["sha256"]
        for item in summary["assets"]
        if isinstance(item, dict)
    }

    checksum_asset = _first_asset(assets, "checksums")
    if checksum_asset is None:
        raise AssetSmokeError("SHA256SUMS.txt was not found")
    checksum_entries = parse_sha256sums(checksum_asset.path)
    for filename, expected_hash in checksum_entries.items():
        path = asset_dir / filename
        if not path.exists():
            raise AssetSmokeError(f"SHA256SUMS lists missing file: {filename}")
        actual_hash = actual_hashes.get(filename) or sha256_file(path)
        actual_hashes[filename] = actual_hash
        if actual_hash != expected_hash:
            raise AssetSmokeError(f"SHA256 mismatch for {filename}")
    summary["checksums"] = {"entries": sorted(checksum_entries)}

    manifest_asset = _first_asset(assets, "manifest")
    if manifest_asset is None:
        raise AssetSmokeError("release_asset_manifest.json was not found")
    verify_manifest(
        manifest_asset.path,
        asset_dir=asset_dir,
        tag=tag,
        actual_hashes=actual_hashes,
        summary=summary,
    )

    sdist = _first_asset(assets, "sdist")
    portable_zip = _first_asset(assets, "portable_zip")
    if sdist is not None:
        validate_tar_entries(sdist.path)
    if portable_zip is not None:
        validate_zip_entries(portable_zip.path, portable=True)
        portable_ux = inspect_portable_zip_ux(portable_zip.path)
        summary["portable_ux"] = portable_ux
        summary["warnings"].extend(portable_ux["warnings"])

    if full_smoke:
        wheel = _first_asset(assets, "wheel")
        if wheel is not None:
            smoke_wheel(
                wheel.path,
                asset_dir=asset_dir,
                expected_version=expected_version,
                summary=summary,
            )
        if sdist is not None:
            smoke_sdist(
                sdist.path,
                asset_dir=asset_dir,
                expected_version=expected_version,
                full_smoke=True,
                summary=summary,
            )
        if portable_zip is not None:
            smoke_portable_zip(
                portable_zip.path,
                asset_dir=asset_dir,
                skip_portable_exe=skip_portable_exe,
                summary=summary,
            )
    elif sdist is not None:
        summary["warnings"].append("sdist install smoke skipped; pass --full-smoke to run it")
    if not full_smoke:
        summary["warnings"].append(
            "wheel and portable executable smoke skipped without --full-smoke"
        )

    summary["status"] = "passed_with_warnings" if summary["warnings"] else "passed"
    return summary


def resolve_download_dir(download_dir: Path, *, reuse_dir: bool, tag: str) -> Path:
    if download_dir.exists() and any(download_dir.iterdir()) and not reuse_dir:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        safe_tag = re.sub(r"[^A-Za-z0-9_.-]+", "_", tag)
        download_dir = download_dir / f"{safe_tag}_{stamp}"
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


def download_assets(
    *,
    repo: str,
    tag: str,
    download_dir: Path,
    pattern: str,
    reuse_dir: bool,
) -> Path:
    target_dir = resolve_download_dir(download_dir, reuse_dir=reuse_dir, tag=tag)
    gh = shutil.which("gh")
    if gh is None:
        raise AssetSmokeError("GitHub CLI 'gh' is not available")
    cmd = [
        gh,
        "release",
        "download",
        tag,
        "--repo",
        repo,
        "--dir",
        str(target_dir),
        "--pattern",
        pattern,
    ]
    proc = _run(cmd, timeout=300)
    if proc.returncode != 0:
        raise AssetSmokeError(
            "gh release download failed: "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )
    return target_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download and/or verify OSW release assets without mutation."
    )
    parser.add_argument("--asset-dir", type=Path, help="Existing asset directory to verify.")
    parser.add_argument("--repo", help="GitHub repository slug for download mode.")
    parser.add_argument("--tag", default="v0.1.3-rc1", help="Release tag to verify.")
    parser.add_argument(
        "--expected-version",
        default="0.1.3rc1",
        help="Expected installed package version for full smoke.",
    )
    parser.add_argument("--download", action="store_true", help="Download assets using gh.")
    parser.add_argument("--download-dir", type=Path, help="Directory for downloaded assets.")
    parser.add_argument("--pattern", default="*", help="gh release download pattern.")
    parser.add_argument("--reuse-dir", action="store_true", help="Reuse non-empty download dir.")
    parser.add_argument("--full-smoke", action="store_true", help="Run install/executable smoke.")
    parser.add_argument(
        "--skip-portable-exe",
        action="store_true",
        help="Skip portable executable --help smoke.",
    )
    parser.add_argument("--json-out", type=Path, help="Write JSON verification summary.")
    return parser


def run_from_args(args: argparse.Namespace) -> dict[str, Any]:
    if args.download:
        if not args.repo or not args.download_dir:
            raise AssetSmokeError("--download requires --repo and --download-dir")
        asset_dir = download_assets(
            repo=args.repo,
            tag=args.tag,
            download_dir=args.download_dir,
            pattern=args.pattern,
            reuse_dir=args.reuse_dir,
        )
    else:
        if args.asset_dir is None:
            raise AssetSmokeError("local verification requires --asset-dir")
        asset_dir = args.asset_dir

    return verify_asset_dir(
        asset_dir,
        tag=args.tag,
        expected_version=args.expected_version,
        full_smoke=args.full_smoke,
        skip_portable_exe=args.skip_portable_exe,
    )


def write_json_summary(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        summary = run_from_args(args)
    except (AssetSmokeError, subprocess.TimeoutExpired) as exc:
        summary = {
            "status": "failed",
            "failures": [str(exc)],
            "warnings": [],
            "assets": [],
        }
        if args.json_out:
            write_json_summary(args.json_out, summary)
        print(f"[fail] {exc}", file=sys.stderr)
        return 1

    if args.json_out:
        write_json_summary(args.json_out, summary)

    for warning in summary.get("warnings", []):
        print(f"[warn] {warning}")
    if summary["status"] == "failed":
        for failure in summary.get("failures", []):
            print(f"[fail] {failure}", file=sys.stderr)
        return 1
    print(f"[ok] Release asset verification {summary['status']}: {summary['asset_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
