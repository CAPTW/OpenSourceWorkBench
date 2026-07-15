#!/usr/bin/env python3
"""QA wrapper for identity-bound release-asset verification."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from _common import repo_root

TAG_RE = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)-rc([1-9]\d*)$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
WRAPPER_TIMEOUT_SECONDS = 600


class WrapperConfigurationError(RuntimeError):
    """Invalid wrapper input detected before child execution."""


class LegacyFlagResult:
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message


def detect_legacy_flags(argv: Sequence[str]) -> LegacyFlagResult | None:
    for flag in (
        "--download",
        "--offline-asset-dir",
        "--skip-download",
        "--full-smoke",
        "--skip-portable-exe",
    ):
        if any(item == flag or item.startswith(f"{flag}=") for item in argv):
            return LegacyFlagResult(
                "LEGACY_FLAG_MIGRATION_REQUIRED",
                f"{flag} is no longer accepted; select an explicit mode and verification level",
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


def _canonical_version(tag: str) -> str:
    match = TAG_RE.fullmatch(tag)
    if match is None:
        raise WrapperConfigurationError(
            "tag must use canonical form vMAJOR.MINOR.PATCH-rcN"
        )
    major, minor, patch, rc = match.groups()
    return f"{major}.{minor}.{patch}rc{rc}"


def validate_args(args: argparse.Namespace, *, root: Path) -> None:
    identity_values = (args.repo, args.tag, args.expected_version, args.expected_target)
    if args.mode in {"current-live", "offline-fixture"} and any(
        value is not None for value in identity_values
    ):
        raise WrapperConfigurationError("selected mode rejects identity overrides")
    if args.mode == "explicit-remote":
        if any(value is None for value in identity_values):
            raise WrapperConfigurationError(
                "explicit-remote requires one complete atomic identity tuple"
            )
        if REPO_RE.fullmatch(args.repo) is None:
            raise WrapperConfigurationError(
                "repository must be one literal OWNER/NAME value"
            )
        if _canonical_version(args.tag) != args.expected_version:
            raise WrapperConfigurationError(
                "expected version must derive exactly from the selected tag"
            )
        if SHA_RE.fullmatch(args.expected_target) is None:
            raise WrapperConfigurationError(
                "expected target must be one lowercase 40-character SHA"
            )
    if args.mode == "local-set":
        if args.repo is not None or any(
            value is None
            for value in (args.tag, args.expected_version, args.expected_target)
        ):
            raise WrapperConfigurationError(
                "local-set requires one complete atomic tag/version/target tuple"
            )
        if _canonical_version(args.tag) != args.expected_version:
            raise WrapperConfigurationError(
                "expected version must derive exactly from the selected tag"
            )
        if SHA_RE.fullmatch(args.expected_target) is None:
            raise WrapperConfigurationError(
                "expected target must be one lowercase 40-character SHA"
            )
    remote = args.mode in {"current-live", "explicit-remote"}
    if remote and (args.download_dir is None or args.asset_dir is not None):
        raise WrapperConfigurationError(
            "remote modes require --download-dir and reject --asset-dir"
        )
    if not remote and (args.asset_dir is None or args.download_dir is not None):
        raise WrapperConfigurationError(
            "local modes require --asset-dir and reject --download-dir"
        )
    if args.mode == "offline-fixture" and args.verification_level != "quick":
        raise WrapperConfigurationError("offline-fixture is intentionally quick-only")
    if args.mode == "offline-fixture":
        canonical_fixture = root / "tests" / "fixtures" / "release_assets"
        if _rooted(args.asset_dir, root).resolve() != canonical_fixture.resolve():
            raise WrapperConfigurationError(
                "offline-fixture requires the canonical fixture directory"
            )


def _rooted(path: Path | None, root: Path) -> Path | None:
    if path is None or path.is_absolute():
        return path
    return root / path


def build_child_command(
    args: argparse.Namespace, *, root: Path, python: Path
) -> list[str]:
    tool = root / "tools" / "release" / "check_release_assets.py"
    command = [
        str(python),
        str(tool),
        "--mode",
        args.mode,
        "--verification-level",
        args.verification_level,
    ]
    for option, value in (
        ("--repo", args.repo),
        ("--tag", args.tag),
        ("--expected-version", args.expected_version),
        ("--expected-target", args.expected_target),
    ):
        if value is not None:
            command.extend([option, value])
    for option, value in (
        ("--asset-dir", _rooted(args.asset_dir, root)),
        ("--download-dir", _rooted(args.download_dir, root)),
        ("--json-out", _rooted(args.json_out, root)),
    ):
        if value is not None:
            command.extend([option, str(value)])
    return command


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    legacy = detect_legacy_flags(raw)
    if legacy is not None:
        print(f"[{legacy.code}] {legacy.message}", file=sys.stderr)
        return 2
    parser = build_parser()
    args = parser.parse_args(raw)
    root = repo_root()
    try:
        validate_args(args, root=root)
    except WrapperConfigurationError as exc:
        print(f"[CONFIGURATION_ERROR] {exc}", file=sys.stderr)
        return 2
    command = build_child_command(
        args, root=root, python=Path(sys.executable).resolve()
    )
    try:
        proc = subprocess.run(
            command,
            cwd=root,
            text=True,
            check=False,
            timeout=WRAPPER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print("[WRAPPER_TIMEOUT] child verification timed out", file=sys.stderr)
        return 1
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
