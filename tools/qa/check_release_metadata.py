#!/usr/bin/env python3
"""Check v0.1 release metadata without network or build artifacts."""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

from _common import repo_root

TARGET_VERSION = "0.1.0rc1"
TARGET_LICENSE = "GPL-3.0-or-later"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _project_license_text(project: dict[str, object]) -> str:
    value = project.get("license")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        text = value.get("text")
        if isinstance(text, str):
            return text
    return ""


def _contains_heading(text: str, heading: str) -> bool:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    return bool(pattern.search(text))


def check_release_metadata(root: Path, *, check_tags: bool = True) -> list[str]:
    failures: list[str] = []

    license_path = root / "LICENSE"
    if not license_path.exists():
        failures.append("LICENSE is missing.")
    else:
        license_text = _read(license_path)
        required_license_markers = [
            "GNU GENERAL PUBLIC LICENSE",
            "Version 3, 29 June 2007",
            "Free Software Foundation",
        ]
        if not all(marker in license_text for marker in required_license_markers):
            failures.append("LICENSE does not look like canonical GNU GPL version 3 text.")
        if "License placeholder" in license_text or "not the final license grant" in license_text:
            failures.append("LICENSE still contains placeholder wording.")

    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        failures.append("pyproject.toml is missing.")
    else:
        pyproject = tomllib.loads(_read(pyproject_path))
        project = pyproject.get("project", {})
        if not isinstance(project, dict):
            failures.append("pyproject.toml has no [project] table.")
        else:
            if project.get("version") != TARGET_VERSION:
                failures.append(f"pyproject project.version is not {TARGET_VERSION}.")
            if _project_license_text(project) != TARGET_LICENSE:
                failures.append(f"pyproject license metadata is not {TARGET_LICENSE}.")

    init_path = root / "src" / "osw" / "__init__.py"
    if not init_path.exists():
        failures.append("src/osw/__init__.py is missing.")
    elif f'__version__ = "{TARGET_VERSION}"' not in _read(init_path):
        failures.append(f"osw.__version__ is not {TARGET_VERSION}.")

    readme_path = root / "README.md"
    if not readme_path.exists():
        failures.append("README.md is missing.")
    else:
        readme = _read(readme_path)
        if not _contains_heading(readme, "License"):
            failures.append("README.md has no License section.")
        if TARGET_LICENSE not in readme:
            failures.append(f"README.md does not mention {TARGET_LICENSE}.")

    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.exists():
        failures.append("CHANGELOG.md is missing.")
    elif TARGET_VERSION not in _read(changelog_path):
        failures.append(f"CHANGELOG.md does not mention {TARGET_VERSION}.")

    for relative in [
        "docs/13_license_and_version_plan.md",
        "docs/14_third_party_notices.md",
    ]:
        if not (root / relative).exists():
            failures.append(f"{relative} is missing.")

    if check_tags:
        proc = subprocess.run(
            ["git", "tag", "--list", "v0.1*"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            failures.append(proc.stderr.strip() or "git tag check failed.")
        elif proc.stdout.strip():
            failures.append("Local v0.1* Git tags exist; this metadata step must not create tags.")

    return failures


def main() -> int:
    root = repo_root()
    failures = check_release_metadata(root)
    if failures:
        print("[fail] Release metadata check failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("[ok] Release metadata is aligned for 0.1.0rc1 and no local v0.1* tags exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
