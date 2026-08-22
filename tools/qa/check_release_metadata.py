#!/usr/bin/env python3
"""Check v0.1 release metadata without network or build artifacts."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import stat
import subprocess
import sys
import tomllib
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from _common import repo_root

TARGET_VERSION = "0.1.5rc3"
TARGET_LICENSE = "GPL-3.0-or-later"
DEFAULT_RC_TAG = "v0.1.5-rc3"
DEFAULT_PRIOR_RC1_TAG = "v0.1.0-rc1"
DEFAULT_PRIOR_RC1_TARGET = "29c5c8bec8df30c7f7be72fc9be5e5409794968e"
DEFAULT_PRIOR_RC2_TAG = "v0.1.0-rc2"
DEFAULT_PRIOR_RC2_TARGET = "684dc6138d4257564bbcdd176a9d5ed311a7316d"
DEFAULT_PRIOR_RC3_TAG = "v0.1.0-rc3"
DEFAULT_PRIOR_RC3_TARGET = "dc7df75c53f0a4acb0a1ccf33d97c01ffdde4b16"
DEFAULT_PRIOR_PATCH_V011_RC1_TAG = "v0.1.1-rc1"
DEFAULT_PRIOR_PATCH_V011_RC1_TARGET = "da1a2c9e2d27674dc4bb85a2800138170c4c4dec"
DEFAULT_PRIOR_PATCH_V012_RC1_TAG = "v0.1.2-rc1"
DEFAULT_PRIOR_PATCH_V012_RC1_TARGET = "28b30c1f79d4c62d160629e96fc1fcefa2382ebe"
DEFAULT_PRIOR_PATCH_V013_RC1_TAG = "v0.1.3-rc1"
DEFAULT_PRIOR_PATCH_V013_RC1_TARGET = "a6e8d3a8211e02359841d10e1947e16ab847b132"
DEFAULT_PRIOR_PATCH_V014_RC1_TAG = "v0.1.4-rc1"
DEFAULT_PRIOR_PATCH_V014_RC1_TARGET = "f1683b441ab308fd65318ef6de3f1282549946a1"
DEFAULT_PRIOR_PATCH_V015_RC1_TAG = "v0.1.5-rc1"
DEFAULT_PRIOR_PATCH_V015_RC1_TARGET = "85c8144f7ff19159ab02c40adb6483ce6b13c017"
DEFAULT_PRIOR_PATCH_V015_RC2_TAG = "v0.1.5-rc2"
DEFAULT_PRIOR_PATCH_V015_RC2_TARGET = "3eced55adf49e70690af80aeb1eb9a8b053555fd"
DEFAULT_HISTORICAL_FINAL_V010_TAG = "v0.1.0"
DEFAULT_HISTORICAL_FINAL_V010_TARGET = "da8728adf679314442755ed781c1dd57d1c6ed27"
DEFAULT_HISTORICAL_FINAL_V011_TAG = "v0.1.1"
DEFAULT_HISTORICAL_FINAL_V011_TARGET = "7b232f5003fcc8eb207846570499ffb3442d3197"
DEFAULT_HISTORICAL_FINAL_V012_TAG = "v0.1.2"
DEFAULT_HISTORICAL_FINAL_V012_TARGET = "c39f21372ef837f096aa0d430cced82adc6f3485"
FINAL_TAG = "v0.1.3"
RELEASE_TAG_PATTERN = "v0.1*"
INSTALLED_METADATA_QUERY = r"""
import importlib.metadata as metadata
import json
import platform
import sys

payload = {
    "executable": sys.executable,
    "python_version": platform.python_version(),
    "distribution_version": None,
    "osw_version": None,
    "osw_file": None,
    "direct_url": None,
    "dir_info": None,
}

try:
    distribution = metadata.distribution("open-solver-workbench")
except metadata.PackageNotFoundError:
    distribution = None

if distribution is not None:
    payload["distribution_version"] = distribution.version
    direct_url_text = distribution.read_text("direct_url.json")
    if direct_url_text:
        try:
            payload["direct_url"] = json.loads(direct_url_text)
            if isinstance(payload["direct_url"], dict):
                payload["dir_info"] = payload["direct_url"].get("dir_info")
        except json.JSONDecodeError:
            payload["direct_url"] = {"invalid_json": direct_url_text}

try:
    import osw
except Exception as exc:
    payload["osw_import_error"] = f"{type(exc).__name__}: {exc}"
else:
    payload["osw_version"] = getattr(osw, "__version__", None)
    payload["osw_file"] = getattr(osw, "__file__", None)

print(json.dumps(payload, sort_keys=True))
"""


@dataclass(frozen=True)
class ReleaseTagExpectation:
    """Expected local release tag identity."""

    name: str
    target: str | None = None
    require_annotated: bool = True


DEFAULT_PRIOR_RC_TAGS = (
    ReleaseTagExpectation(DEFAULT_PRIOR_RC1_TAG, DEFAULT_PRIOR_RC1_TARGET),
    ReleaseTagExpectation(DEFAULT_PRIOR_RC2_TAG, DEFAULT_PRIOR_RC2_TARGET),
    ReleaseTagExpectation(DEFAULT_PRIOR_RC3_TAG, DEFAULT_PRIOR_RC3_TARGET),
    ReleaseTagExpectation(
        DEFAULT_PRIOR_PATCH_V011_RC1_TAG,
        DEFAULT_PRIOR_PATCH_V011_RC1_TARGET,
    ),
    ReleaseTagExpectation(
        DEFAULT_PRIOR_PATCH_V012_RC1_TAG,
        DEFAULT_PRIOR_PATCH_V012_RC1_TARGET,
    ),
    ReleaseTagExpectation(
        DEFAULT_PRIOR_PATCH_V013_RC1_TAG,
        DEFAULT_PRIOR_PATCH_V013_RC1_TARGET,
    ),
    ReleaseTagExpectation(
        DEFAULT_PRIOR_PATCH_V014_RC1_TAG,
        DEFAULT_PRIOR_PATCH_V014_RC1_TARGET,
    ),
    ReleaseTagExpectation(
        DEFAULT_PRIOR_PATCH_V015_RC1_TAG,
        DEFAULT_PRIOR_PATCH_V015_RC1_TARGET,
    ),
    ReleaseTagExpectation(
        DEFAULT_PRIOR_PATCH_V015_RC2_TAG,
        DEFAULT_PRIOR_PATCH_V015_RC2_TARGET,
    ),
)

DEFAULT_HISTORICAL_FINAL_TAGS = (
    ReleaseTagExpectation(
        DEFAULT_HISTORICAL_FINAL_V010_TAG,
        DEFAULT_HISTORICAL_FINAL_V010_TARGET,
    ),
    ReleaseTagExpectation(
        DEFAULT_HISTORICAL_FINAL_V011_TAG,
        DEFAULT_HISTORICAL_FINAL_V011_TARGET,
    ),
    ReleaseTagExpectation(
        DEFAULT_HISTORICAL_FINAL_V012_TAG,
        DEFAULT_HISTORICAL_FINAL_V012_TARGET,
    ),
)


@dataclass(frozen=True)
class ReleaseTagPolicy:
    """Release tag validation policy for pre-tag and RC-aware gates."""

    forbid_release_tags: bool = False
    expected_rc_tag: str | None = DEFAULT_RC_TAG
    expected_rc_target: str | None = None
    require_annotated_rc_tag: bool = True
    require_expected_rc_tag: bool = False
    allowed_prior_rc_tags: tuple[ReleaseTagExpectation, ...] = DEFAULT_PRIOR_RC_TAGS
    forbid_final_tag: bool = False
    forbidden_final_tag: str | None = None
    expected_final_tag: str | None = None
    expected_final_target: str | None = None
    require_annotated_final_tag: bool = True
    require_expected_final_tag: bool = False
    allowed_historical_final_tags: tuple[ReleaseTagExpectation, ...] = (
        DEFAULT_HISTORICAL_FINAL_TAGS
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


def _path_identity(path: Path) -> str:
    return os.path.normcase(os.path.normpath(str(path.resolve(strict=False))))


def _parse_local_file_url(value: object) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value:
        return None, "[DIRECT_URL_INVALID] direct_url.url must be a nonempty string."
    try:
        parsed = urllib.parse.urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        return None, f"[DIRECT_URL_INVALID] direct_url.url is malformed: {exc}"
    if parsed.scheme.casefold() != "file":
        return None, "[DIRECT_URL_NON_FILE_SCHEME] direct_url.url must use file:."
    if parsed.query or parsed.fragment:
        return None, "[DIRECT_URL_INVALID] file URL must not contain query or fragment."
    if parsed.username is not None or parsed.password is not None or port is not None:
        return None, "[DIRECT_URL_INVALID] file URL must not contain credentials or port."
    if re.search(r"%(?![0-9A-Fa-f]{2})", parsed.path):
        return None, "[DIRECT_URL_INVALID] file URL contains a malformed percent escape."
    try:
        decoded_path = urllib.parse.unquote_to_bytes(parsed.path).decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        return None, f"[DIRECT_URL_INVALID] file URL path is not valid UTF-8: {exc}"
    if not decoded_path:
        return None, "[DIRECT_URL_INVALID] file URL path is empty."

    authority = parsed.hostname or ""
    if authority and authority.casefold() != "localhost":
        if os.name != "nt":
            return None, "[DIRECT_URL_INVALID] nonlocal file URL authority is unsupported."
        path_text = f"\\\\{authority}{decoded_path.replace('/', os.sep)}"
    else:
        path_text = urllib.request.url2pathname(decoded_path)
        if os.name == "nt" and re.match(r"^[/\\][A-Za-z]:", path_text):
            path_text = path_text[1:]
    path = Path(path_text)
    if not path.is_absolute():
        return None, "[DIRECT_URL_INVALID] file URL must resolve to an absolute path."
    return path, None


def _direct_url_failures(value: object, metadata_root: Path) -> list[str]:
    if not isinstance(value, Mapping):
        return ["[DIRECT_URL_NOT_MAPPING] direct_url must be a mapping."]

    failures: list[str] = []
    direct_path, error = _parse_local_file_url(value.get("url"))
    if error is not None:
        failures.append(error)
    elif direct_path is not None and _path_identity(direct_path) != _path_identity(
        metadata_root
    ):
        failures.append(
            "[DIRECT_URL_ROOT_MISMATCH] Installed distribution direct URL does not "
            f"match selected metadata root {metadata_root}."
        )

    if "dir_info" not in value:
        failures.append("[DIRECT_URL_DIR_INFO_MISSING] direct_url.dir_info is missing.")
        return failures
    dir_info = value.get("dir_info")
    if not isinstance(dir_info, Mapping):
        failures.append("[DIRECT_URL_DIR_INFO_INVALID] direct_url.dir_info must be a mapping.")
        return failures
    if "editable" not in dir_info:
        failures.append("[DIRECT_URL_EDITABLE_MISSING] direct_url.dir_info.editable is missing.")
    elif dir_info.get("editable") is not True:
        failures.append(
            "[DIRECT_URL_EDITABLE_NOT_TRUE] direct_url.dir_info.editable must be "
            "Boolean true."
        )
    return failures


def _expected_repository_package_path(metadata_root: Path) -> Path:
    return metadata_root / "src" / "osw" / "__init__.py"


def _query_installed_metadata(
    metadata_python: Path,
    *,
    metadata_root: Path,
) -> tuple[dict[str, object] | None, str | None]:
    try:
        proc = subprocess.run(
            [str(metadata_python), "-I", "-c", INSTALLED_METADATA_QUERY],
            cwd=metadata_root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
            shell=False,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        return (
            None,
            "[SELECTED_INTERPRETER_TIMEOUT] Selected installed metadata interpreter "
            f"timed out after {exc.timeout} seconds.",
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return (
            None,
            "[SELECTED_INTERPRETER_UNAVAILABLE] Could not run selected installed "
            f"metadata interpreter: {exc}",
        )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "no diagnostic output"
        return (
            None,
            "[SELECTED_INTERPRETER_NONZERO] Selected installed metadata interpreter exited "
            f"{proc.returncode}: {detail}",
        )
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return (
            None,
            "[OBSERVATION_JSON_INVALID] Selected installed metadata interpreter "
            f"returned invalid JSON: {exc}",
        )
    if not isinstance(value, dict):
        return (
            None,
            "[OBSERVATION_JSON_NOT_OBJECT] Selected installed metadata interpreter "
            "returned a non-object JSON value.",
        )
    return value, None


def _validate_installed_metadata_observation(
    observation: dict[str, object],
    *,
    expected_version: str,
    metadata_python: Path,
    metadata_root: Path,
) -> list[str]:
    failures: list[str] = []
    executable = observation.get("executable")
    if not isinstance(executable, str) or _path_identity(Path(executable)) != _path_identity(
        metadata_python
    ):
        failures.append(
            "Selected installed metadata interpreter reported an unexpected executable: "
            f"{executable!r}."
        )

    python_version = observation.get("python_version")
    if not isinstance(python_version, str) or not python_version:
        failures.append("Selected installed metadata interpreter did not report Python version.")

    distribution_version = observation.get("distribution_version")
    if distribution_version is None:
        failures.append(
            "[DISTRIBUTION_MISSING] Selected open-solver-workbench distribution is missing."
        )
    elif distribution_version != expected_version:
        failures.append(
            "[DISTRIBUTION_VERSION_MISMATCH] Installed package metadata version is "
            f"{distribution_version}, "
            f"expected {expected_version}."
        )

    imported_version = observation.get("osw_version")
    if imported_version is None:
        detail = observation.get("osw_import_error")
        failures.append(
            "[IMPORTED_VERSION_MISMATCH] Selected environment could not import osw: "
            f"{detail or 'unknown error' }."
        )
    elif imported_version != expected_version:
        failures.append(
            "[IMPORTED_VERSION_MISMATCH] Selected imported osw.__version__ is "
            f"{imported_version}, "
            f"expected {expected_version}."
        )

    failures.extend(_direct_url_failures(observation.get("direct_url"), metadata_root))

    expected_package = _expected_repository_package_path(metadata_root)
    try:
        expected_stat = expected_package.lstat()
    except FileNotFoundError:
        failures.append(
            "[EXPECTED_PACKAGE_MISSING] Expected repository package file is missing: "
            f"{expected_package}."
        )
    except OSError as exc:
        failures.append(
            "[EXPECTED_PACKAGE_MISSING] Could not inspect expected repository package "
            f"file {expected_package}: {exc}"
        )
    else:
        if expected_package.is_symlink() or not stat.S_ISREG(expected_stat.st_mode):
            failures.append(
                "[EXPECTED_PACKAGE_NOT_REGULAR] Expected repository package path is "
                f"not a regular non-symlink file: {expected_package}."
            )

    imported_file = observation.get("osw_file")
    if (
        not isinstance(imported_file, str)
        or not Path(imported_file).is_absolute()
        or _path_identity(Path(imported_file)) != _path_identity(expected_package)
    ):
        failures.append(
            "[IMPORTED_PACKAGE_PATH_MISMATCH] Imported osw path does not match exact "
            f"repository package path {expected_package}: {imported_file!r}."
        )
    return failures


def _source_version_failures(root: Path, expected_version: str, *, label: str) -> list[str]:
    failures: list[str] = []
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        failures.append(f"[SOURCE_VERSION_MISMATCH] {label} pyproject.toml is missing.")
    else:
        project = tomllib.loads(_read(pyproject_path)).get("project", {})
        version = project.get("version") if isinstance(project, dict) else None
        if version != expected_version:
            failures.append(
                "[SOURCE_VERSION_MISMATCH] "
                f"{label} pyproject version is {version}, expected {expected_version}."
            )

    init_path = root / "src" / "osw" / "__init__.py"
    if not init_path.exists():
        failures.append(
            f"[SOURCE_VERSION_MISMATCH] {label} src/osw/__init__.py is missing."
        )
    elif f'__version__ = "{expected_version}"' not in _read(init_path):
        failures.append(
            f"[SOURCE_VERSION_MISMATCH] {label} osw.__version__ is not {expected_version}."
        )
    return failures


def _source_project_version(root: Path) -> object:
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.is_file():
        return None
    project = tomllib.loads(_read(pyproject_path)).get("project", {})
    return project.get("version") if isinstance(project, dict) else None


def _validate_selected_installed_metadata(
    *,
    source_root: Path,
    metadata_python: Path,
    metadata_root: Path,
    expected_version: str,
) -> tuple[list[str], dict[str, object] | None]:
    failures = _source_version_failures(
        source_root,
        expected_version,
        label="Source-under-test",
    )
    failures.extend(
        _source_version_failures(
            metadata_root,
            expected_version,
            label="Selected metadata root",
        )
    )
    observation, error = _query_installed_metadata(
        metadata_python,
        metadata_root=metadata_root,
    )
    if error is not None:
        failures.append(error)
        return failures, None
    assert observation is not None
    observation = dict(observation)
    direct_url = observation.get("direct_url")
    observation["dir_info"] = (
        direct_url.get("dir_info") if isinstance(direct_url, Mapping) else None
    )
    observation["metadata_root"] = str(metadata_root.resolve(strict=False))
    observation["metadata_root_source_version"] = _source_project_version(metadata_root)
    observation["source_under_test_version"] = _source_project_version(source_root)
    failures.extend(
        _validate_installed_metadata_observation(
            observation,
            expected_version=expected_version,
            metadata_python=metadata_python,
            metadata_root=metadata_root,
        )
    )
    return failures, observation


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
    label: str = "RC",
) -> list[str]:
    failures: list[str] = []
    if expectation.name not in tags:
        if required:
            failures.append(f"Expected {label} tag {expectation.name} is missing.")
        return failures

    returncode, object_type, stderr = _git_stdout(
        root,
        ["cat-file", "-t", f"refs/tags/{expectation.name}"],
    )
    if returncode != 0:
        failures.append(stderr or f"Could not inspect expected {label} tag {expectation.name}.")
    elif expectation.require_annotated and object_type != "tag":
        failures.append(f"Expected {label} tag {expectation.name} is not an annotated tag object.")

    expected_target, target_error = _resolve_expected_target(root, expectation.target)
    if target_error is not None:
        failures.append(target_error)
    elif expected_target:
        returncode, commit, stderr = _git_stdout(
            root,
            ["rev-parse", f"{expectation.name}^{{commit}}"],
        )
        if returncode != 0:
            failures.append(stderr or f"Could not peel expected {label} tag {expectation.name}.")
        elif commit != expected_target:
            failures.append(
                f"Expected {label} tag {expectation.name} points to {commit}, "
                f"not {expected_target}."
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

    expected_final = policy.expected_final_tag
    historical_final_tags = {item.name for item in policy.allowed_historical_final_tags}
    forbidden_final_tag = policy.forbidden_final_tag or (
        FINAL_TAG if policy.forbid_final_tag else None
    )
    if forbidden_final_tag and forbidden_final_tag in tags:
        failures.append(
            f"Final {forbidden_final_tag} tag exists; final tag creation requires "
            "a separate release gate."
        )
    if FINAL_TAG in tags and FINAL_TAG not in historical_final_tags and expected_final != FINAL_TAG:
        failures.append(
            f"Final {FINAL_TAG} tag exists; final tag creation requires a separate "
            "release gate."
        )

    expected = policy.expected_rc_tag
    prior_tags = {item.name for item in policy.allowed_prior_rc_tags}
    allowed_tags = (
        prior_tags
        | ({expected} if expected else set())
        | ({expected_final} if expected_final else set())
        | historical_final_tags
    )
    unexpected_tags = sorted(tag for tag in tags if tag not in allowed_tags)
    if unexpected_tags:
        failures.append(
            "Unexpected local v0.1* Git tags exist: " + ", ".join(unexpected_tags) + "."
        )

    for prior in policy.allowed_prior_rc_tags:
        failures.extend(_validate_known_tag(root, tags, prior, required=False))

    for historical_final in policy.allowed_historical_final_tags:
        failures.extend(
            _validate_known_tag(
                root,
                tags,
                historical_final,
                required=True,
                label="historical final",
            )
        )

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

    if expected_final:
        failures.extend(
            _validate_known_tag(
                root,
                tags,
                ReleaseTagExpectation(
                    expected_final,
                    policy.expected_final_target,
                    policy.require_annotated_final_tag,
                ),
                required=policy.require_expected_final_tag,
                label="final",
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
        if (
            tag_policy
            and tag_policy.expected_final_tag
            and tag_policy.expected_final_tag not in changelog
        ):
            failures.append(f"CHANGELOG.md does not mention {tag_policy.expected_final_tag}.")

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
    use_current_defaults = args.expected_version == TARGET_VERSION
    expected_rc_tag = (
        args.expected_rc_tag
        or os.environ.get("OSW_RELEASE_EXPECTED_RC_TAG")
        or (DEFAULT_RC_TAG if use_current_defaults else None)
    )
    expected_rc_target = args.expected_rc_target or os.environ.get("OSW_RELEASE_EXPECTED_RC_TARGET")
    require_annotated = bool(args.require_annotated_rc_tag) or _truthy_env(
        "OSW_RELEASE_REQUIRE_ANNOTATED_RC_TAG"
    )
    expected_final_tag = args.expected_final_tag or os.environ.get(
        "OSW_RELEASE_EXPECTED_FINAL_TAG"
    )
    expected_final_target = args.expected_final_target or os.environ.get(
        "OSW_RELEASE_EXPECTED_FINAL_TARGET"
    )
    require_annotated_final = bool(args.require_annotated_final_tag) or _truthy_env(
        "OSW_RELEASE_REQUIRE_ANNOTATED_FINAL_TAG"
    )
    prior_tags = args.allowed_prior_rc_tag
    prior_targets = args.allowed_prior_rc_target
    historical_final_tags = args.allowed_historical_final_tag
    historical_final_targets = args.allowed_historical_final_target
    env_prior_tag = os.environ.get("OSW_RELEASE_ALLOWED_PRIOR_RC_TAG")
    env_prior_target = os.environ.get("OSW_RELEASE_ALLOWED_PRIOR_RC_TARGET")
    allowed_prior_rc_tags: tuple[ReleaseTagExpectation, ...]
    if prior_tags:
        allowed_prior_rc_tags = tuple(
            ReleaseTagExpectation(tag, prior_targets[index] if index < len(prior_targets) else None)
            for index, tag in enumerate(prior_tags)
        )
    elif env_prior_tag:
        allowed_prior_rc_tags = (
            ReleaseTagExpectation(env_prior_tag, env_prior_target),
        )
    else:
        allowed_prior_rc_tags = DEFAULT_PRIOR_RC_TAGS

    if historical_final_tags:
        allowed_historical_final_tags = tuple(
            ReleaseTagExpectation(
                tag,
                historical_final_targets[index] if index < len(historical_final_targets) else None,
            )
            for index, tag in enumerate(historical_final_tags)
        )
    elif use_current_defaults:
        allowed_historical_final_tags = DEFAULT_HISTORICAL_FINAL_TAGS
    else:
        allowed_historical_final_tags = ()

    return ReleaseTagPolicy(
        forbid_release_tags=forbid_release_tags,
        expected_rc_tag=expected_rc_tag,
        expected_rc_target=expected_rc_target,
        require_annotated_rc_tag=require_annotated or expected_rc_tag == DEFAULT_RC_TAG,
        require_expected_rc_tag=bool(args.expected_rc_tag),
        allowed_prior_rc_tags=allowed_prior_rc_tags,
        forbid_final_tag=bool(args.forbid_final_tag),
        forbidden_final_tag=args.forbid_final_tag,
        expected_final_tag=expected_final_tag,
        expected_final_target=expected_final_target,
        require_annotated_final_tag=require_annotated_final,
        require_expected_final_tag=bool(args.expected_final_tag),
        allowed_historical_final_tags=allowed_historical_final_tags,
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
        "--installed-metadata-python",
        type=Path,
        help="exact Python executable for the explicit installed-metadata check",
    )
    parser.add_argument(
        "--installed-metadata-root",
        type=Path,
        help="exact repository root represented by the installed-metadata interpreter",
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
        action="append",
        default=[],
        help="local historical RC tag allowed as release evidence",
    )
    parser.add_argument(
        "--allowed-prior-rc-target",
        action="append",
        default=[],
        help="expected peeled commit for the allowed prior RC tag",
    )
    parser.add_argument(
        "--require-annotated-rc-tag",
        action="store_true",
        help="require the expected RC tag to be an annotated tag object",
    )
    parser.add_argument(
        "--forbid-final-tag",
        nargs="?",
        const=FINAL_TAG,
        default=None,
        metavar="TAG",
        help="final-prep mode: fail if TAG exists; omit TAG to check %(const)s",
    )
    parser.add_argument(
        "--allowed-historical-final-tag",
        action="append",
        default=[],
        help="local historical final tag allowed as release evidence",
    )
    parser.add_argument(
        "--allowed-historical-final-target",
        action="append",
        default=[],
        help="expected peeled commit for the allowed historical final tag",
    )
    parser.add_argument(
        "--expected-final-tag",
        help="final-tag-aware mode: expected local final release tag name",
    )
    parser.add_argument(
        "--expected-final-target",
        help="final-tag-aware mode: expected peeled commit for the final release tag",
    )
    parser.add_argument(
        "--require-annotated-final-tag",
        action="store_true",
        help="require the expected final tag to be an annotated tag object",
    )
    args = parser.parse_args()
    if bool(args.installed_metadata_python) != bool(args.installed_metadata_root):
        parser.error(
            "[CLI_METADATA_OPTIONS_PAIRED] --installed-metadata-python and "
            "--installed-metadata-root "
            "must be provided together"
        )
    if args.installed_metadata_python is not None and (
        not args.installed_metadata_python.is_absolute()
        or not args.installed_metadata_root.is_absolute()
    ):
        parser.error(
            "[CLI_METADATA_OPTIONS_ABSOLUTE] --installed-metadata-python and "
            "--installed-metadata-root "
            "must be absolute paths"
        )
    if args.allowed_prior_rc_tag and (
        len(args.allowed_prior_rc_tag) != len(args.allowed_prior_rc_target)
    ):
        parser.error("--allowed-prior-rc-tag and --allowed-prior-rc-target must be paired")
    if args.allowed_prior_rc_target and not args.allowed_prior_rc_tag:
        parser.error("--allowed-prior-rc-target requires --allowed-prior-rc-tag")
    if args.allowed_historical_final_tag and (
        len(args.allowed_historical_final_tag) != len(args.allowed_historical_final_target)
    ):
        parser.error(
            "--allowed-historical-final-tag and --allowed-historical-final-target must be paired"
        )
    if args.allowed_historical_final_target and not args.allowed_historical_final_tag:
        parser.error(
            "--allowed-historical-final-target requires --allowed-historical-final-tag"
        )

    root = repo_root()
    print(
        f"[info] Release metadata driver: {Path(sys.executable).resolve()} "
        f"(Python {platform.python_version()})."
    )
    failures = check_release_metadata(
        root,
        expected_version=args.expected_version,
        expected_source_license=args.expected_source_license,
        tag_policy=_tag_policy_from_args(args),
    )
    observation: dict[str, object] | None = None
    if args.installed_metadata_python is None:
        print(
            "[info] Installed distribution metadata was not checked; "
            "provide both explicit installed-metadata options to enable it."
        )
    else:
        metadata_python = args.installed_metadata_python.resolve(strict=False)
        assert args.installed_metadata_root is not None
        metadata_root = args.installed_metadata_root.resolve(strict=False)
        selected_failures, observation = _validate_selected_installed_metadata(
            source_root=root,
            metadata_python=metadata_python,
            metadata_root=metadata_root,
            expected_version=args.expected_version,
        )
        failures.extend(selected_failures)
        print(f"[info] Selected installed metadata interpreter: {metadata_python}")
        print(f"[info] Selected installed metadata root: {metadata_root}")
        if observation is not None:
            print(
                "[info] Selected interpreter reported: "
                f"{observation.get('executable')} "
                f"(Python {observation.get('python_version')})."
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
