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

TARGET_VERSION = "0.1.0rc2"
TARGET_LICENSE = "GPL-3.0-or-later"
DEFAULT_RC_TAG = "v0.1.0-rc2"
DEFAULT_PRIOR_RC_TAG = "v0.1.0-rc1"
DEFAULT_PRIOR_RC_TARGET = "29c5c8bec8df30c7f7be72fc9be5e5409794968e"
FINAL_TAG = "v0.1.0"
RELEASE_TAG_PATTERN = "v0.1*"


@dataclass(frozen=True)
class ReleaseTagExpectation:
    """Expected local release tag identity."""

    name: str
    target: str | None = None
    require_annotated: bool = True


@dataclass(frozen=True)
class ReleaseTagPolicy:
    """Release tag validation policy for pre-tag and RC-aware gates."""

    forbid_release_tags: bool = False
    expected_rc_tag: str | None = DEFAULT_RC_TAG
    expected_rc_target: str | None = None
    require_annotated_rc_tag: bool = True
    require_expected_rc_tag: bool = False
    allowed_prior_rc_tags: tuple[ReleaseTagExpectation, ...] = (
        ReleaseTagExpectation(DEFAULT_PRIOR_RC_TAG, DEFAULT_PRIOR_RC_TARGET),
    )


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


def _resolve_expected_target(root: Path, target: str | None) -> tuple[str | None, str | None]:
    if target != "HEAD":
        return target, None
    returncode, stdout, stderr = _git_stdout(root, ["rev-parse", "HEAD"])
    if returncode != 0:
        return None, stderr or "Could not resolve HEAD for expected release tag target."
    return stdout, None


def _validate_known_tag(
    root: Path,
    tags: list[str],
    expectation: ReleaseTagExpectation,
    *,
    required: bool,
) -> list[str]:
    failures: list[str] = []
    if expectation.name not in tags:
        if required:
            failures.append(f"Expected RC tag {expectation.name} is missing.")
        return failures

    returncode, object_type, stderr = _git_stdout(
        root,
        ["cat-file", "-t", f"refs/tags/{expectation.name}"],
    )
    if returncode != 0:
        failures.append(stderr or f"Could not inspect expected RC tag {expectation.name}.")
    elif expectation.require_annotated and object_type != "tag":
        failures.append(f"Expected RC tag {expectation.name} is not an annotated tag object.")

    expected_target, target_error = _resolve_expected_target(root, expectation.target)
    if target_error is not None:
        failures.append(target_error)
    elif expected_target:
        returncode, commit, stderr = _git_stdout(
            root,
            ["rev-parse", f"{expectation.name}^{{commit}}"],
        )
        if returncode != 0:
            failures.append(stderr or f"Could not peel expected RC tag {expectation.name}.")
        elif commit != expected_target:
            failures.append(
                f"Expected RC tag {expectation.name} points to {commit}, not {expected_target}."
            )

    return failures


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
    prior_tags = {item.name for item in policy.allowed_prior_rc_tags}
    allowed_tags = prior_tags | ({expected} if expected else set())
    unexpected_tags = sorted(tag for tag in tags if tag not in allowed_tags)
    if unexpected_tags:
        failures.append(
            "Unexpected local v0.1* Git tags exist: " + ", ".join(unexpected_tags) + "."
        )

    for prior in policy.allowed_prior_rc_tags:
        failures.extend(_validate_known_tag(root, tags, prior, required=False))

    if expected:
        failures.extend(
            _validate_known_tag(
                root,
                tags,
                ReleaseTagExpectation(
                    expected,
                    policy.expected_rc_target,
                    policy.require_annotated_rc_tag,
                ),
                required=policy.require_expected_rc_tag,
            )
        )

    return failures


def check_release_metadata(
    root: Path,
    *,
    expected_version: str = TARGET_VERSION,
    expected_source_license: str = TARGET_LICENSE,
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
            if project.get("version") != expected_version:
                failures.append(f"pyproject project.version is not {expected_version}.")
            if _project_license_text(project) != expected_source_license:
                failures.append(
                    f"pyproject license metadata is not {expected_source_license}."
                )

    init_path = root / "src" / "osw" / "__init__.py"
    if not init_path.exists():
        failures.append("src/osw/__init__.py is missing.")
    elif f'__version__ = "{expected_version}"' not in _read(init_path):
        failures.append(f"osw.__version__ is not {expected_version}.")

    readme_path = root / "README.md"
    if not readme_path.exists():
        failures.append("README.md is missing.")
    else:
        readme = _read(readme_path)
        if not _contains_heading(readme, "License"):
            failures.append("README.md has no License section.")
        if expected_source_license not in readme:
            failures.append(f"README.md does not mention {expected_source_license}.")

    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.exists():
        failures.append("CHANGELOG.md is missing.")
    else:
        changelog = _read(changelog_path)
        if expected_version not in changelog:
            failures.append(f"CHANGELOG.md does not mention {expected_version}.")
        if (
            tag_policy
            and tag_policy.expected_rc_tag
            and tag_policy.expected_rc_tag not in changelog
        ):
            failures.append(f"CHANGELOG.md does not mention {tag_policy.expected_rc_tag}.")

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
    allowed_prior_rc_tags: list[ReleaseTagExpectation] = []
    prior_tag = args.allowed_prior_rc_tag or os.environ.get("OSW_RELEASE_ALLOWED_PRIOR_RC_TAG")
    prior_target = args.allowed_prior_rc_target or os.environ.get(
        "OSW_RELEASE_ALLOWED_PRIOR_RC_TARGET"
    )
    if prior_tag:
        allowed_prior_rc_tags.append(ReleaseTagExpectation(prior_tag, prior_target))
    elif DEFAULT_PRIOR_RC_TAG:
        allowed_prior_rc_tags.append(
            ReleaseTagExpectation(DEFAULT_PRIOR_RC_TAG, DEFAULT_PRIOR_RC_TARGET)
        )

    return ReleaseTagPolicy(
        forbid_release_tags=forbid_release_tags,
        expected_rc_tag=expected_rc_tag,
        expected_rc_target=expected_rc_target,
        require_annotated_rc_tag=require_annotated or expected_rc_tag == DEFAULT_RC_TAG,
        require_expected_rc_tag=bool(args.expected_rc_tag),
        allowed_prior_rc_tags=tuple(allowed_prior_rc_tags),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expected-version",
        default=os.environ.get("OSW_RELEASE_EXPECTED_VERSION", TARGET_VERSION),
        help="expected PEP 440 package version",
    )
    parser.add_argument(
        "--expected-source-license",
        default=os.environ.get("OSW_RELEASE_EXPECTED_SOURCE_LICENSE", TARGET_LICENSE),
        help="expected project source license metadata",
    )
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
        "--allowed-prior-rc-tag",
        help="local historical RC tag allowed as release evidence",
    )
    parser.add_argument(
        "--allowed-prior-rc-target",
        help="expected peeled commit for the allowed prior RC tag",
    )
    parser.add_argument(
        "--require-annotated-rc-tag",
        action="store_true",
        help="require the expected RC tag to be an annotated tag object",
    )
    args = parser.parse_args()

    root = repo_root()
    failures = check_release_metadata(
        root,
        expected_version=args.expected_version,
        expected_source_license=args.expected_source_license,
        tag_policy=_tag_policy_from_args(args),
    )
    if failures:
        print("[fail] Release metadata check failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(f"[ok] Release metadata is aligned for {args.expected_version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
