#!/usr/bin/env python3
"""QA wrapper for release asset download smoke verification."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from _common import repo_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="CAPTW/OpenSourceWorkBench")
    parser.add_argument("--tag", default="v0.1.3-rc1")
    parser.add_argument(
        "--download-dir",
        type=Path,
        default=Path("artifacts/release/download_smoke/v0.1.3-rc1_auto"),
    )
    parser.add_argument("--offline-asset-dir", type=Path)
    parser.add_argument("--full-smoke", action="store_true")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--skip-portable-exe", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = repo_root()
    tool = root / "tools" / "release" / "check_release_assets.py"

    command = [sys.executable, str(tool), "--tag", args.tag]
    if args.offline_asset_dir:
        command.extend(["--asset-dir", str(args.offline_asset_dir)])
    elif args.skip_download:
        print("[skip] release asset smoke download disabled and no offline asset dir provided")
        return 2
    else:
        if shutil.which("gh") is None:
            print("[skip] GitHub CLI 'gh' is unavailable and no offline asset dir was provided")
            return 2
        command.extend(
            [
                "--repo",
                args.repo,
                "--download",
                "--download-dir",
                str(root / args.download_dir),
            ]
        )

    if args.full_smoke:
        command.append("--full-smoke")
    if args.skip_portable_exe:
        command.append("--skip-portable-exe")

    proc = subprocess.run(command, cwd=root, text=True, check=False)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
