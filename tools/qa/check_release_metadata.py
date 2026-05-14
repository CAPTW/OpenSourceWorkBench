#!/usr/bin/env python3
"""Check v0.1 release metadata without network or build artifacts."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from _common import repo_root

TARGET_VERSION = "0.1.0rc1"
TARGET_LICENSE = "GPL-3.0-or-later"
DEFAULT_RC_TAG = "v0.1.0-rc1"
FINAL_TAG = "v0.1.0"
RELEASE_TAG_PATTERN = "v0.1*"


@dataclass(frozen=True)
class ReleaseTagPolicy:
    """Release tag validation policy for pre-tag and RC-aware gates."""

    forbid_release_tags: bool = False
    expected_rc_tag: str | None = DEFAULT_RC_TAG
    expected_rc_target: str | None = None
    require_annotated_rc_tag: bool = True
    require_expected_rc_tag: bool = False


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


def _git_stdout(root: Path, args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _local_release_tags(root: Path) -> tuple[list[str] | None, str | None]:
    returncode, stdout, stderr = _git_stdout(root, ["tag", "--list", RELEASE_TAG_PATTERN])
    if returncode != 0:
        return None, stderr or "git tag check failed."
    if not stdout:
        return [], None
    return [line.strip() for line in stdout.splitlines() if line.strip()], None


def _validate_release_tags(root: Path, policy: ReleaseTagPolicy) -> list[str]:
    failures: list[str] = []
    tags, error = _local_release_tags(root)
    if error is not None:
        return [error]
    assert tags is not None

    if policy.forbid_release_tags:
        if tags:
            failures.append(
                "Local v0.1* Git tags exist; strict pre-tag mode forbids release tags."
            )
        return failures

    if FINAL_TAG in tags:
        failures.append(
            f"Final {FINAL_TAG} tag exists; final tag creation requires a separate release gate."
        )

    expected = policy.expected_rc_tag
    allowed_tags = {expected} if expected else set()
    unexpected_tags = sorted(tag for tag in tags if tag not in allowed_tags)
    if unexpected_tags:
        failures.append(
            "Unexpected local v0.1* Git tags exist: " + ", ".join(unexpected_tags) + "."
        )

    if not expected:
        return failures

    if expected not in tags:
        if policy.require_expected_rc_tag:
            failures.append(f"Expected RC tag {expected} is missing.")
        return failures

    returncode, object_type, stderr = _git_stdout(root, ["cat-file", "-t", f"refs/tags/{expected}"])
    if returncode != 0:
        failures.append(stderr or f"Could not inspect expected RC tag {expected}.")
    elif policy.require_annotated_rc_tag and object_type != "tag":
        failures.append(f"Expected RC tag {expected} is not an annotated tag object.")

    if policy.expected_rc_target:
        returncode, commit, stderr = _git_stdout(root, ["rev-parse", f"{expected}^{{commit}}"])
        if returncode != 0:
            failures.append(stderr or f"Could not peel expected RC tag {expected}.")
        elif commit != policy.expected_rc_target:
            failures.append(
                f"Expected RC tag {expected} points to {commit}, not {policy.expected_rc_target}."
            )

    return failures


def check_release_metadata(
    root: Path,
    *,
    check_tags: bool = True,
    tag_policy: ReleaseTagPolicy | None = None,
) -> list[str]:
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
        failures.extend(_validate_release_tags(root, tag_policy or ReleaseTagPolicy()))

    return failures


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _tag_policy_from_args(args: argparse.Namespace) -> ReleaseTagPolicy:
    forbid_release_tags = bool(args.forbid_release_tags) or _truthy_env("OSW_RELEASE_FORBID_TAGS")
    expected_rc_tag = (
        args.expected_rc_tag
        or os.environ.get("OSW_RELEASE_EXPECTED_RC_TAG")
        or DEFAULT_RC_TAG
    )
    expected_rc_target = args.expected_rc_target or os.environ.get("OSW_RELEASE_EXPECTED_RC_TARGET")
    require_annotated = bool(args.require_annotated_rc_tag) or _truthy_env(
        "OSW_RELEASE_REQUIRE_ANNOTATED_RC_TAG"
    )

    return ReleaseTagPolicy(
        forbid_release_tags=forbid_release_tags,
        expected_rc_tag=expected_rc_tag,
        expected_rc_target=expected_rc_target,
        require_annotated_rc_tag=require_annotated or expected_rc_tag == DEFAULT_RC_TAG,
        require_expected_rc_tag=bool(args.expected_rc_tag),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--forbid-release-tags",
        action="store_true",
        help="strict pre-tag mode: fail if any local v0.1* tag exists",
    )
    parser.add_argument(
        "--expected-rc-tag",
        help="RC-aware mode: expected local release-candidate tag name",
    )
    parser.add_argument(
        "--expected-rc-target",
        help="RC-aware mode: expected peeled commit for the release-candidate tag",
    )
    parser.add_argument(
        "--require-annotated-rc-tag",
        action="store_true",
        help="require the expected RC tag to be an annotated tag object",
    )
    args = parser.parse_args()

    root = repo_root()
    failures = check_release_metadata(root, tag_policy=_tag_policy_from_args(args))
    if failures:
        print("[fail] Release metadata check failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("[ok] Release metadata is aligned for 0.1.0rc1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
