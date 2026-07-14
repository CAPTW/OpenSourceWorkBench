from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS_QA = Path(__file__).resolve().parents[2] / "tools" / "qa"
if str(TOOLS_QA) not in sys.path:
    sys.path.insert(0, str(TOOLS_QA))

import check_release_metadata as release_metadata  # noqa: E402
from check_release_metadata import (  # noqa: E402
    ReleaseTagExpectation,
    ReleaseTagPolicy,
    check_release_metadata,
)

PRIOR_RC1_TARGET = "29c5c8bec8df30c7f7be72fc9be5e5409794968e"
PRIOR_RC2_TARGET = "684dc6138d4257564bbcdd176a9d5ed311a7316d"
PRIOR_RC3_TARGET = "dc7df75c53f0a4acb0a1ccf33d97c01ffdde4b16"
CURRENT_RC3_TARGET = PRIOR_RC3_TARGET
FINAL_TARGET = "1111111111111111111111111111111111111111"
PATCH_RC1_TARGET = "2222222222222222222222222222222222222222"
PATCH_FINAL_TARGET = "3333333333333333333333333333333333333333"
PATCH_V012_RC1_TARGET = "4444444444444444444444444444444444444444"
PATCH_V012_FINAL_TARGET = "5555555555555555555555555555555555555555"
ZERO_TARGET = "0000000000000000000000000000000000000000"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_release_tree(root: Path, *, version: str = "0.1.0rc3") -> None:
    tag_by_version = {
        "0.1.0": "v0.1.0",
        "0.1.1rc1": "v0.1.1-rc1",
        "0.1.1": "v0.1.1",
        "0.1.2rc1": "v0.1.2-rc1",
        "0.1.2": "v0.1.2",
        "0.1.3rc1": "v0.1.3-rc1",
        "0.1.3rc2.dev0": "v0.1.3-rc1",
        "0.1.4rc1": "v0.1.4-rc1",
        "0.1.5rc1": "v0.1.5-rc1",
    }
    tag = tag_by_version.get(version, "v0.1.0-rc3")
    _write(
        root / "LICENSE",
        """GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007
Copyright (C) 2007 Free Software Foundation
""",
    )
    _write(
        root / "pyproject.toml",
        f"""[project]
name = "open-solver-workbench"
version = "{version}"
license = {{ text = "GPL-3.0-or-later" }}
""",
    )
    _write(root / "src" / "osw" / "__init__.py", f'__version__ = "{version}"\n')
    _write(
        root / "README.md",
        """# OpenSolver Workbench

## License

GPL-3.0-or-later
""",
    )
    _write(root / "CHANGELOG.md", f"## {version} - Draft\n\nTag: {tag}\n\nPrior: v0.1.0-rc3\n")
    _write(root / "docs" / "13_license_and_version_plan.md", "# Plan\n")
    _write(root / "docs" / "14_third_party_notices.md", "# Notices\n")


def _installed_observation(
    root: Path,
    python: Path,
    *,
    distribution_version: str | None = "0.1.5rc1",
    imported_version: str | None = "0.1.5rc1",
    direct_url_root: Path | None = None,
    imported_root: Path | None = None,
) -> dict[str, object]:
    direct_root = direct_url_root or root
    import_root = imported_root or root
    return {
        "executable": str(python),
        "python_version": "3.11.9",
        "distribution_version": distribution_version,
        "osw_version": imported_version,
        "osw_file": str(import_root / "src" / "osw" / "__init__.py"),
        "direct_url": {
            "dir_info": {"editable": True},
            "url": direct_root.resolve().as_uri(),
        },
    }


def _validate_observation(
    observation: dict[str, object],
    *,
    expected_version: str,
    metadata_python: Path,
    metadata_root: Path,
) -> list[str]:
    validator = getattr(
        release_metadata,
        "_validate_installed_metadata_observation",
        None,
    )
    assert callable(validator), "installed metadata observation validator is missing"
    return validator(
        observation,
        expected_version=expected_version,
        metadata_python=metadata_python,
        metadata_root=metadata_root,
    )


def _mock_git_tags(
    monkeypatch: pytest.MonkeyPatch,
    *,
    tags: list[str],
    tag_types: dict[str, str] | None = None,
    commits: dict[str, str] | None = None,
    head: str = CURRENT_RC3_TARGET,
) -> None:
    tag_types = tag_types or {}
    commits = commits or {}

    class FakeCompletedProcess:
        def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(args: list[str], **_: object) -> FakeCompletedProcess:
        if args[:3] == ["git", "tag", "--list"]:
            return FakeCompletedProcess(stdout="\n".join(tags))
        if args[:3] == ["git", "cat-file", "-t"]:
            tag = args[3].removeprefix("refs/tags/")
            if tag in tag_types:
                return FakeCompletedProcess(stdout=tag_types[tag])
            return FakeCompletedProcess(returncode=1, stderr=f"missing tag {tag}")
        if args[:2] == ["git", "rev-parse"]:
            if args[2] == "HEAD":
                return FakeCompletedProcess(stdout=head)
            tag = args[2].removesuffix("^{commit}")
            if tag in commits:
                return FakeCompletedProcess(stdout=commits[tag])
            return FakeCompletedProcess(returncode=1, stderr=f"missing commit {tag}")
        raise AssertionError(f"unexpected git command: {args}")

    monkeypatch.setattr(release_metadata.subprocess, "run", fake_run)


def _rc3_policy(*, rc3_target: str | None = CURRENT_RC3_TARGET) -> ReleaseTagPolicy:
    return ReleaseTagPolicy(
        expected_rc_tag="v0.1.0-rc3",
        expected_rc_target=rc3_target,
        require_annotated_rc_tag=True,
        require_expected_rc_tag=True,
        allowed_prior_rc_tags=(
            ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
            ReleaseTagExpectation("v0.1.0-rc2", PRIOR_RC2_TARGET),
        ),
        allowed_historical_final_tags=(),
    )


def _final_prep_policy() -> ReleaseTagPolicy:
    return ReleaseTagPolicy(
        expected_rc_tag=None,
        forbidden_final_tag="v0.1.0",
        allowed_prior_rc_tags=(
            ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
            ReleaseTagExpectation("v0.1.0-rc2", PRIOR_RC2_TARGET),
            ReleaseTagExpectation("v0.1.0-rc3", PRIOR_RC3_TARGET),
        ),
        allowed_historical_final_tags=(),
    )


def _final_tag_policy(*, final_target: str | None = FINAL_TARGET) -> ReleaseTagPolicy:
    return ReleaseTagPolicy(
        expected_rc_tag=None,
        expected_final_tag="v0.1.0",
        expected_final_target=final_target,
        require_annotated_final_tag=True,
        require_expected_final_tag=True,
        allowed_prior_rc_tags=(
            ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
            ReleaseTagExpectation("v0.1.0-rc2", PRIOR_RC2_TARGET),
            ReleaseTagExpectation("v0.1.0-rc3", PRIOR_RC3_TARGET),
        ),
        allowed_historical_final_tags=(),
    )


def _patch_rc1_policy(*, rc_target: str | None = None) -> ReleaseTagPolicy:
    return ReleaseTagPolicy(
        expected_rc_tag="v0.1.1-rc1" if rc_target is not None else None,
        expected_rc_target=rc_target,
        require_annotated_rc_tag=True,
        require_expected_rc_tag=rc_target is not None,
        allowed_prior_rc_tags=(
            ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
            ReleaseTagExpectation("v0.1.0-rc2", PRIOR_RC2_TARGET),
            ReleaseTagExpectation("v0.1.0-rc3", PRIOR_RC3_TARGET),
        ),
        forbidden_final_tag="v0.1.1",
        allowed_historical_final_tags=(
            ReleaseTagExpectation("v0.1.0", FINAL_TARGET),
        ),
    )


def _patch_final_prep_policy() -> ReleaseTagPolicy:
    return ReleaseTagPolicy(
        expected_rc_tag=None,
        forbidden_final_tag="v0.1.1",
        allowed_prior_rc_tags=(
            ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
            ReleaseTagExpectation("v0.1.0-rc2", PRIOR_RC2_TARGET),
            ReleaseTagExpectation("v0.1.0-rc3", PRIOR_RC3_TARGET),
            ReleaseTagExpectation("v0.1.1-rc1", PATCH_RC1_TARGET),
        ),
        allowed_historical_final_tags=(
            ReleaseTagExpectation("v0.1.0", FINAL_TARGET),
        ),
    )


def _patch_final_tag_policy(*, final_target: str | None = PATCH_FINAL_TARGET) -> ReleaseTagPolicy:
    return ReleaseTagPolicy(
        expected_rc_tag=None,
        expected_final_tag="v0.1.1",
        expected_final_target=final_target,
        require_annotated_final_tag=True,
        require_expected_final_tag=True,
        allowed_prior_rc_tags=(
            ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
            ReleaseTagExpectation("v0.1.0-rc2", PRIOR_RC2_TARGET),
            ReleaseTagExpectation("v0.1.0-rc3", PRIOR_RC3_TARGET),
            ReleaseTagExpectation("v0.1.1-rc1", PATCH_RC1_TARGET),
        ),
        allowed_historical_final_tags=(
            ReleaseTagExpectation("v0.1.0", FINAL_TARGET),
        ),
    )


def _patch_v012_rc1_prep_policy() -> ReleaseTagPolicy:
    return ReleaseTagPolicy(
        expected_rc_tag=None,
        forbidden_final_tag="v0.1.2",
        allowed_prior_rc_tags=(
            ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
            ReleaseTagExpectation("v0.1.0-rc2", PRIOR_RC2_TARGET),
            ReleaseTagExpectation("v0.1.0-rc3", PRIOR_RC3_TARGET),
            ReleaseTagExpectation("v0.1.1-rc1", PATCH_RC1_TARGET),
        ),
        allowed_historical_final_tags=(
            ReleaseTagExpectation("v0.1.0", FINAL_TARGET),
            ReleaseTagExpectation("v0.1.1", PATCH_FINAL_TARGET),
        ),
    )


def _patch_v012_rc1_tag_policy(
    *,
    rc_target: str | None = PATCH_V012_RC1_TARGET,
) -> ReleaseTagPolicy:
    return ReleaseTagPolicy(
        expected_rc_tag="v0.1.2-rc1",
        expected_rc_target=rc_target,
        require_annotated_rc_tag=True,
        require_expected_rc_tag=True,
        forbidden_final_tag="v0.1.2",
        allowed_prior_rc_tags=(
            ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
            ReleaseTagExpectation("v0.1.0-rc2", PRIOR_RC2_TARGET),
            ReleaseTagExpectation("v0.1.0-rc3", PRIOR_RC3_TARGET),
            ReleaseTagExpectation("v0.1.1-rc1", PATCH_RC1_TARGET),
        ),
        allowed_historical_final_tags=(
            ReleaseTagExpectation("v0.1.0", FINAL_TARGET),
            ReleaseTagExpectation("v0.1.1", PATCH_FINAL_TARGET),
        ),
    )


def _patch_v012_final_prep_policy() -> ReleaseTagPolicy:
    return ReleaseTagPolicy(
        expected_rc_tag=None,
        forbidden_final_tag="v0.1.2",
        allowed_prior_rc_tags=(
            ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
            ReleaseTagExpectation("v0.1.0-rc2", PRIOR_RC2_TARGET),
            ReleaseTagExpectation("v0.1.0-rc3", PRIOR_RC3_TARGET),
            ReleaseTagExpectation("v0.1.1-rc1", PATCH_RC1_TARGET),
            ReleaseTagExpectation("v0.1.2-rc1", PATCH_V012_RC1_TARGET),
        ),
        allowed_historical_final_tags=(
            ReleaseTagExpectation("v0.1.0", FINAL_TARGET),
            ReleaseTagExpectation("v0.1.1", PATCH_FINAL_TARGET),
        ),
    )


def _patch_v012_final_tag_policy(
    *,
    final_target: str | None = PATCH_V012_FINAL_TARGET,
) -> ReleaseTagPolicy:
    return ReleaseTagPolicy(
        expected_rc_tag=None,
        expected_final_tag="v0.1.2",
        expected_final_target=final_target,
        require_annotated_final_tag=True,
        require_expected_final_tag=True,
        allowed_prior_rc_tags=(
            ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
            ReleaseTagExpectation("v0.1.0-rc2", PRIOR_RC2_TARGET),
            ReleaseTagExpectation("v0.1.0-rc3", PRIOR_RC3_TARGET),
            ReleaseTagExpectation("v0.1.1-rc1", PATCH_RC1_TARGET),
            ReleaseTagExpectation("v0.1.2-rc1", PATCH_V012_RC1_TARGET),
        ),
        allowed_historical_final_tags=(
            ReleaseTagExpectation("v0.1.0", FINAL_TARGET),
            ReleaseTagExpectation("v0.1.1", PATCH_FINAL_TARGET),
        ),
    )


def test_release_metadata_accepts_aligned_rc3_tree(tmp_path: Path) -> None:
    _minimal_release_tree(tmp_path)

    assert check_release_metadata(tmp_path, expected_version="0.1.0rc3", check_tags=False) == []


def test_default_release_metadata_accepts_current_v015rc1_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _minimal_release_tree(tmp_path, version=release_metadata.TARGET_VERSION)
    tag_expectations = (
        *release_metadata.DEFAULT_PRIOR_RC_TAGS,
        *release_metadata.DEFAULT_HISTORICAL_FINAL_TAGS,
    )
    _mock_git_tags(
        monkeypatch,
        tags=[expectation.name for expectation in tag_expectations],
        tag_types={expectation.name: "tag" for expectation in tag_expectations},
        commits={
            expectation.name: expectation.target
            for expectation in tag_expectations
            if expectation.target is not None
        },
    )

    assert check_release_metadata(tmp_path) == []


def test_selected_metadata_rejects_stale_distribution_version(
    tmp_path: Path,
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.5rc1")
    metadata_python = tmp_path / "venv" / "python"
    failures = _validate_observation(
        _installed_observation(
            tmp_path,
            metadata_python,
            distribution_version="0.1.3rc1",
        ),
        expected_version="0.1.5rc1",
        metadata_python=metadata_python,
        metadata_root=tmp_path,
    )

    assert any(
        "Installed package metadata version is 0.1.3rc1, expected 0.1.5rc1."
        in failure
        for failure in failures
    )


def test_selected_metadata_accepts_matching_repository_environment(
    tmp_path: Path,
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.5rc1")
    metadata_python = tmp_path / "venv" / "python"

    assert _validate_observation(
        _installed_observation(tmp_path, metadata_python),
        expected_version="0.1.5rc1",
        metadata_python=metadata_python,
        metadata_root=tmp_path,
    ) == []


@pytest.mark.parametrize(
    ("case", "category"),
    [
        ("false", "DIRECT_URL_EDITABLE_NOT_TRUE"),
        ("missing", "DIRECT_URL_EDITABLE_MISSING"),
        ("string", "DIRECT_URL_EDITABLE_NOT_TRUE"),
        ("integer", "DIRECT_URL_EDITABLE_NOT_TRUE"),
        ("missing_dir_info", "DIRECT_URL_DIR_INFO_MISSING"),
        ("malformed_dir_info", "DIRECT_URL_DIR_INFO_INVALID"),
    ],
)
def test_selected_metadata_rejects_invalid_editable_provenance(
    tmp_path: Path,
    case: str,
    category: str,
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.5rc1")
    metadata_python = tmp_path / "venv" / "python"
    observation = _installed_observation(tmp_path, metadata_python)
    direct_url = observation["direct_url"]
    assert isinstance(direct_url, dict)
    if case == "false":
        direct_url["dir_info"] = {"editable": False}
    elif case == "missing":
        direct_url["dir_info"] = {}
    elif case == "string":
        direct_url["dir_info"] = {"editable": "true"}
    elif case == "integer":
        direct_url["dir_info"] = {"editable": 1}
    elif case == "missing_dir_info":
        direct_url.pop("dir_info")
    else:
        direct_url["dir_info"] = ["editable", True]

    failures = _validate_observation(
        observation,
        expected_version="0.1.5rc1",
        metadata_python=metadata_python,
        metadata_root=tmp_path,
    )

    assert any(f"[{category}]" in failure for failure in failures)


@pytest.mark.parametrize(
    ("case", "category"),
    [
        ("missing", "DIRECT_URL_NOT_MAPPING"),
        ("malformed", "DIRECT_URL_INVALID"),
        ("relative", "DIRECT_URL_INVALID"),
        ("non_file", "DIRECT_URL_NON_FILE_SCHEME"),
        ("external", "DIRECT_URL_ROOT_MISMATCH"),
        ("parent", "DIRECT_URL_ROOT_MISMATCH"),
        ("child", "DIRECT_URL_ROOT_MISMATCH"),
    ],
)
def test_selected_metadata_rejects_invalid_direct_url(
    tmp_path: Path,
    case: str,
    category: str,
) -> None:
    root = tmp_path / "repository"
    _minimal_release_tree(root, version="0.1.5rc1")
    metadata_python = tmp_path / "venv" / "python"
    observation = _installed_observation(root, metadata_python)
    if case == "missing":
        observation["direct_url"] = None
    else:
        direct_url = observation["direct_url"]
        assert isinstance(direct_url, dict)
        if case == "malformed":
            direct_url["url"] = "file:///bad%ZZpath"
        elif case == "relative":
            direct_url["url"] = "file:relative/repository"
        elif case == "non_file":
            direct_url["url"] = "https://example.invalid/repository"
        elif case == "external":
            direct_url["url"] = (tmp_path / "external").resolve().as_uri()
        elif case == "parent":
            direct_url["url"] = tmp_path.resolve().as_uri()
        else:
            direct_url["url"] = (root / "child").resolve().as_uri()

    failures = _validate_observation(
        observation,
        expected_version="0.1.5rc1",
        metadata_python=metadata_python,
        metadata_root=root,
    )

    assert any(f"[{category}]" in failure for failure in failures)


@pytest.mark.parametrize("case", ["unrelated", "nonexistent", "wrong_exact_path"])
def test_selected_metadata_rejects_noncanonical_import_path(
    tmp_path: Path,
    case: str,
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.5rc1")
    metadata_python = tmp_path / "venv" / "python"
    observation = _installed_observation(tmp_path, metadata_python)
    if case == "unrelated":
        imported_file = tmp_path / "alternate" / "osw" / "__init__.py"
        _write(imported_file, '__version__ = "0.1.5rc1"\n')
    elif case == "nonexistent":
        imported_file = tmp_path / "missing" / "osw" / "__init__.py"
    else:
        imported_file = tmp_path / "src" / "osw" / "alternate.py"
        _write(imported_file, '__version__ = "0.1.5rc1"\n')
    observation["osw_file"] = str(imported_file)

    failures = _validate_observation(
        observation,
        expected_version="0.1.5rc1",
        metadata_python=metadata_python,
        metadata_root=tmp_path,
    )

    assert any("[IMPORTED_PACKAGE_PATH_MISMATCH]" in failure for failure in failures)


@pytest.mark.parametrize(
    ("case", "category"),
    [
        ("missing", "EXPECTED_PACKAGE_MISSING"),
        ("directory", "EXPECTED_PACKAGE_NOT_REGULAR"),
    ],
)
def test_selected_metadata_requires_regular_expected_package_file(
    tmp_path: Path,
    case: str,
    category: str,
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.5rc1")
    metadata_python = tmp_path / "venv" / "python"
    observation = _installed_observation(tmp_path, metadata_python)
    expected_file = tmp_path / "src" / "osw" / "__init__.py"
    expected_file.unlink()
    if case == "directory":
        expected_file.mkdir()

    failures = _validate_observation(
        observation,
        expected_version="0.1.5rc1",
        metadata_python=metadata_python,
        metadata_root=tmp_path,
    )

    assert any(f"[{category}]" in failure for failure in failures)


def test_selected_metadata_rejects_missing_distribution(tmp_path: Path) -> None:
    _minimal_release_tree(tmp_path, version="0.1.5rc1")
    metadata_python = tmp_path / "venv" / "python"

    failures = _validate_observation(
        _installed_observation(
            tmp_path,
            metadata_python,
            distribution_version=None,
        ),
        expected_version="0.1.5rc1",
        metadata_python=metadata_python,
        metadata_root=tmp_path,
    )

    assert any(
        "open-solver-workbench distribution is missing" in failure for failure in failures
    )


def test_selected_metadata_rejects_imported_version_mismatch(tmp_path: Path) -> None:
    _minimal_release_tree(tmp_path, version="0.1.5rc1")
    metadata_python = tmp_path / "venv" / "python"

    failures = _validate_observation(
        _installed_observation(
            tmp_path,
            metadata_python,
            imported_version="0.1.4rc1",
        ),
        expected_version="0.1.5rc1",
        metadata_python=metadata_python,
        metadata_root=tmp_path,
    )

    assert any(
        "Selected imported osw.__version__ is 0.1.4rc1, expected 0.1.5rc1."
        in failure
        for failure in failures
    )


def test_selected_metadata_rejects_different_checkout(
    tmp_path: Path,
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.5rc1")
    metadata_python = tmp_path / "venv" / "python"
    other_root = tmp_path / "other-checkout"
    other_root.mkdir()

    failures = _validate_observation(
        _installed_observation(
            tmp_path,
            metadata_python,
            direct_url_root=other_root,
            imported_root=other_root,
        ),
        expected_version="0.1.5rc1",
        metadata_python=metadata_python,
        metadata_root=tmp_path,
    )

    assert any("does not match selected metadata root" in failure for failure in failures)


def test_selected_metadata_query_uses_only_requested_interpreter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    query = getattr(release_metadata, "_query_installed_metadata", None)
    assert callable(query), "installed metadata interpreter query is missing"
    metadata_python = tmp_path / "selected-python"
    observation = _installed_observation(tmp_path, metadata_python)
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, json.dumps(observation), "")

    monkeypatch.setattr(release_metadata.subprocess, "run", fake_run)

    actual, error = query(metadata_python, metadata_root=tmp_path)

    assert error is None
    assert actual == observation
    assert calls[0][0][0] == str(metadata_python)
    assert calls[0][1]["shell"] is False


def test_selected_metadata_query_rejects_invalid_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    query = getattr(release_metadata, "_query_installed_metadata", None)
    assert callable(query), "installed metadata interpreter query is missing"
    metadata_python = tmp_path / "selected-python"

    monkeypatch.setattr(
        release_metadata.subprocess,
        "run",
        lambda args, **_kwargs: subprocess.CompletedProcess(args, 0, "not-json", ""),
    )

    observation, error = query(metadata_python, metadata_root=tmp_path)

    assert observation is None
    assert error is not None
    assert "[OBSERVATION_JSON_INVALID]" in error


def test_selected_metadata_query_rejects_non_object_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    query = getattr(release_metadata, "_query_installed_metadata", None)
    assert callable(query), "installed metadata interpreter query is missing"
    metadata_python = tmp_path / "selected-python"

    monkeypatch.setattr(
        release_metadata.subprocess,
        "run",
        lambda args, **_kwargs: subprocess.CompletedProcess(args, 0, "[]", ""),
    )

    observation, error = query(metadata_python, metadata_root=tmp_path)

    assert observation is None
    assert error is not None
    assert "[OBSERVATION_JSON_NOT_OBJECT]" in error


@pytest.mark.parametrize(
    ("case", "category"),
    [
        ("unavailable", "SELECTED_INTERPRETER_UNAVAILABLE"),
        ("timeout", "SELECTED_INTERPRETER_TIMEOUT"),
        ("nonzero", "SELECTED_INTERPRETER_NONZERO"),
    ],
)
def test_selected_metadata_query_preserves_failures_and_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    category: str,
) -> None:
    query = getattr(release_metadata, "_query_installed_metadata", None)
    assert callable(query), "installed metadata interpreter query is missing"
    metadata_python = tmp_path / "selected-python"

    def fake_run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if case == "unavailable":
            raise OSError("selected interpreter is unavailable")
        if case == "timeout":
            raise subprocess.TimeoutExpired(args, timeout=30)
        return subprocess.CompletedProcess(args, 7, "query stdout", "query stderr")

    monkeypatch.setattr(release_metadata.subprocess, "run", fake_run)

    observation, error = query(metadata_python, metadata_root=tmp_path)

    assert observation is None
    assert error is not None
    assert f"[{category}]" in error


def test_selected_metadata_query_has_no_ambient_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    query = getattr(release_metadata, "_query_installed_metadata", None)
    assert callable(query), "installed metadata interpreter query is missing"
    metadata_python = tmp_path / "selected-python"
    calls: list[list[str]] = []

    def fake_run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        raise OSError("selected interpreter is unavailable")

    monkeypatch.setattr(release_metadata.subprocess, "run", fake_run)

    observation, error = query(metadata_python, metadata_root=tmp_path)

    assert observation is None
    assert error is not None
    assert "[SELECTED_INTERPRETER_UNAVAILABLE]" in error
    assert calls == [[str(metadata_python), "-I", "-c", release_metadata.INSTALLED_METADATA_QUERY]]


def test_selected_metadata_rejects_metadata_root_source_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selector = getattr(release_metadata, "_validate_selected_installed_metadata", None)
    assert callable(selector), "selected installed metadata validator is missing"
    source_root = tmp_path / "source"
    metadata_root = tmp_path / "metadata"
    _minimal_release_tree(source_root, version="0.1.5rc1")
    _minimal_release_tree(metadata_root, version="0.1.4rc1")
    metadata_python = tmp_path / "venv" / "python"
    observation = _installed_observation(
        metadata_root,
        metadata_python,
        distribution_version="0.1.5rc1",
        imported_version="0.1.5rc1",
    )
    monkeypatch.setattr(
        release_metadata,
        "_query_installed_metadata",
        lambda _python, *, metadata_root: (observation, None),
    )

    failures, _ = selector(
        source_root=source_root,
        metadata_python=metadata_python,
        metadata_root=metadata_root,
        expected_version="0.1.5rc1",
    )

    assert any(
        "Selected metadata root pyproject version is 0.1.4rc1, expected 0.1.5rc1."
        in failure
        for failure in failures
    )
    assert any("[SOURCE_VERSION_MISMATCH]" in failure for failure in failures)


def test_selected_metadata_observation_retains_structured_repository_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selector = getattr(release_metadata, "_validate_selected_installed_metadata", None)
    assert callable(selector), "selected installed metadata validator is missing"
    _minimal_release_tree(tmp_path, version="0.1.5rc1")
    metadata_python = tmp_path / "venv" / "python"
    queried = _installed_observation(tmp_path, metadata_python)
    monkeypatch.setattr(
        release_metadata,
        "_query_installed_metadata",
        lambda _python, *, metadata_root: (queried, None),
    )

    failures, observation = selector(
        source_root=tmp_path,
        metadata_python=metadata_python,
        metadata_root=tmp_path,
        expected_version="0.1.5rc1",
    )

    assert failures == []
    assert observation is not None
    assert observation["metadata_root"] == str(tmp_path.resolve())
    assert observation["metadata_root_source_version"] == "0.1.5rc1"
    assert observation["source_under_test_version"] == "0.1.5rc1"
    assert observation["dir_info"] == {"editable": True}


def test_release_metadata_main_is_source_only_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[dict[str, object]] = []

    def fake_check(_root: Path, **kwargs: object) -> list[str]:
        calls.append(kwargs)
        return []

    monkeypatch.setattr(release_metadata, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(release_metadata, "check_release_metadata", fake_check)
    monkeypatch.setattr(sys, "argv", ["check_release_metadata.py"])

    assert release_metadata.main() == 0
    output = capsys.readouterr().out
    assert f"Release metadata driver: {Path(sys.executable).resolve()}" in output
    assert "Installed distribution metadata was not checked" in output
    assert "check_installed_distribution" not in calls[0]


@pytest.mark.parametrize(
    "arguments",
    [
        ["--installed-metadata-python", str(Path(sys.executable).resolve())],
        ["--installed-metadata-root", str(Path.cwd().resolve())],
    ],
)
def test_release_metadata_main_requires_paired_environment_options(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
) -> None:
    monkeypatch.setattr(release_metadata, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_release_metadata.py", *arguments],
    )

    with pytest.raises(SystemExit) as exc_info:
        release_metadata.main()

    assert exc_info.value.code == 2
    error = capsys.readouterr().err
    assert "[CLI_METADATA_OPTIONS_PAIRED]" in error
    assert "must be provided together" in error


@pytest.mark.parametrize(
    ("python_path", "root_path"),
    [
        ("relative/python", None),
        (None, "relative/root"),
    ],
)
def test_release_metadata_main_requires_absolute_environment_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    python_path: str | None,
    root_path: str | None,
) -> None:
    monkeypatch.setattr(release_metadata, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        release_metadata,
        "check_release_metadata",
        lambda _root, **_kwargs: [],
    )
    monkeypatch.setattr(
        release_metadata,
        "_validate_selected_installed_metadata",
        lambda **_kwargs: ([], {}),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_release_metadata.py",
            "--installed-metadata-python",
            python_path or str(Path(sys.executable).resolve()),
            "--installed-metadata-root",
            root_path or str(tmp_path.resolve()),
        ],
    )

    try:
        result = release_metadata.main()
    except SystemExit as exc:
        result = int(exc.code)

    assert result == 2
    error = capsys.readouterr().err
    assert "[CLI_METADATA_OPTIONS_ABSOLUTE]" in error
    assert "must be absolute paths" in error


def test_release_metadata_main_reports_explicit_environment_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    metadata_python = tmp_path / "venv" / "python"
    observation = _installed_observation(tmp_path, metadata_python)

    monkeypatch.setattr(release_metadata, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        release_metadata,
        "check_release_metadata",
        lambda _root, **_kwargs: [],
    )
    monkeypatch.setattr(
        release_metadata,
        "_validate_selected_installed_metadata",
        lambda **_kwargs: ([], observation),
        raising=False,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_release_metadata.py",
            "--installed-metadata-python",
            str(metadata_python),
            "--installed-metadata-root",
            str(tmp_path),
        ],
    )

    try:
        result = release_metadata.main()
    except SystemExit as exc:
        result = int(exc.code)

    assert result == 0
    output = capsys.readouterr().out
    assert f"Release metadata driver: {Path(sys.executable).resolve()}" in output
    assert f"Selected installed metadata interpreter: {metadata_python}" in output
    assert f"Selected installed metadata root: {tmp_path}" in output


def test_release_metadata_rejects_placeholder_license(tmp_path: Path) -> None:
    _minimal_release_tree(tmp_path)
    _write(tmp_path / "LICENSE", "License placeholder.\n")

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.0rc3",
        check_tags=False,
    )

    assert any("canonical GNU GPL version 3" in failure for failure in failures)
    assert any("placeholder" in failure for failure in failures)


def test_prior_rc1_and_rc2_can_both_be_allowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag"},
        commits={"v0.1.0-rc1": PRIOR_RC1_TARGET, "v0.1.0-rc2": PRIOR_RC2_TARGET},
    )

    assert (
        check_release_metadata(
            tmp_path,
            expected_version="0.1.0rc3",
            tag_policy=ReleaseTagPolicy(
                expected_rc_tag="v0.1.0-rc3",
                allowed_prior_rc_tags=(
                    ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
                    ReleaseTagExpectation("v0.1.0-rc2", PRIOR_RC2_TARGET),
                ),
                allowed_historical_final_tags=(),
            ),
        )
        == []
    )


def test_cli_accepts_repeatable_prior_rc_allowances(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag"},
        commits={"v0.1.0-rc1": PRIOR_RC1_TARGET, "v0.1.0-rc2": PRIOR_RC2_TARGET},
    )
    monkeypatch.setattr(release_metadata, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_release_metadata.py",
            "--expected-version",
            "0.1.0rc3",
            "--expected-source-license",
            "GPL-3.0-or-later",
            "--allowed-prior-rc-tag",
            "v0.1.0-rc1",
            "--allowed-prior-rc-target",
            PRIOR_RC1_TARGET,
            "--allowed-prior-rc-tag",
            "v0.1.0-rc2",
            "--allowed-prior-rc-target",
            PRIOR_RC2_TARGET,
        ],
    )

    assert release_metadata.main() == 0


def test_cli_rejects_unpaired_prior_rc_targets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    monkeypatch.setattr(release_metadata, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_release_metadata.py",
            "--allowed-prior-rc-tag",
            "v0.1.0-rc1",
            "--allowed-prior-rc-tag",
            "v0.1.0-rc2",
            "--allowed-prior-rc-target",
            PRIOR_RC1_TARGET,
        ],
    )

    with pytest.raises(SystemExit) as excinfo:
        release_metadata.main()

    assert excinfo.value.code == 2


def test_cli_accepts_final_prep_with_three_prior_rc_tags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.0")
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag", "v0.1.0-rc3": "tag"},
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
        },
    )
    monkeypatch.setattr(release_metadata, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_release_metadata.py",
            "--expected-version",
            "0.1.0",
            "--expected-source-license",
            "GPL-3.0-or-later",
            "--allowed-prior-rc-tag",
            "v0.1.0-rc1",
            "--allowed-prior-rc-target",
            PRIOR_RC1_TARGET,
            "--allowed-prior-rc-tag",
            "v0.1.0-rc2",
            "--allowed-prior-rc-target",
            PRIOR_RC2_TARGET,
            "--allowed-prior-rc-tag",
            "v0.1.0-rc3",
            "--allowed-prior-rc-target",
            PRIOR_RC3_TARGET,
            "--forbid-final-tag",
        ],
    )

    assert release_metadata.main() == 0


def test_prior_rc1_wrong_target_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag"},
        commits={"v0.1.0-rc1": ZERO_TARGET, "v0.1.0-rc2": PRIOR_RC2_TARGET},
    )

    failures = check_release_metadata(tmp_path, expected_version="0.1.0rc3")

    assert any(f"not {PRIOR_RC1_TARGET}" in failure for failure in failures)


def test_prior_rc2_wrong_target_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag"},
        commits={"v0.1.0-rc1": PRIOR_RC1_TARGET, "v0.1.0-rc2": ZERO_TARGET},
    )

    failures = check_release_metadata(tmp_path, expected_version="0.1.0rc3")

    assert any(f"not {PRIOR_RC2_TARGET}" in failure for failure in failures)


def test_final_version_accepts_prior_rc1_rc2_rc3_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.0")
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag", "v0.1.0-rc3": "tag"},
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
        },
    )

    assert (
        check_release_metadata(
            tmp_path,
            expected_version="0.1.0",
            tag_policy=_final_prep_policy(),
        )
        == []
    )


def test_prior_rc3_wrong_target_fails_final_prep(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.0")
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag", "v0.1.0-rc3": "tag"},
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": ZERO_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.0",
        tag_policy=_final_prep_policy(),
    )

    assert any(f"not {PRIOR_RC3_TARGET}" in failure for failure in failures)


def test_expected_rc3_annotated_tag_passes_when_target_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag", "v0.1.0-rc3": "tag"},
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": CURRENT_RC3_TARGET,
        },
    )

    assert (
        check_release_metadata(
            tmp_path,
            expected_version="0.1.0rc3",
            tag_policy=_rc3_policy(),
        )
        == []
    )


def test_expected_rc3_head_target_is_resolved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag", "v0.1.0-rc3": "tag"},
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": CURRENT_RC3_TARGET,
        },
    )

    assert (
        check_release_metadata(
            tmp_path,
            expected_version="0.1.0rc3",
            tag_policy=_rc3_policy(rc3_target="HEAD"),
        )
        == []
    )


def test_expected_rc3_wrong_target_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag", "v0.1.0-rc3": "tag"},
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": ZERO_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.0rc3",
        tag_policy=_rc3_policy(),
    )

    assert any(f"not {CURRENT_RC3_TARGET}" in failure for failure in failures)


def test_expected_rc3_lightweight_tag_fails_when_annotated_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag", "v0.1.0-rc3": "commit"},
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": CURRENT_RC3_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.0rc3",
        tag_policy=_rc3_policy(),
    )

    assert any("not an annotated tag object" in failure for failure in failures)


def test_final_v0_1_0_tag_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag"},
        commits={"v0.1.0-rc1": PRIOR_RC1_TARGET, "v0.1.0-rc2": PRIOR_RC2_TARGET},
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.0rc3",
        tag_policy=ReleaseTagPolicy(
            expected_rc_tag="v0.1.0-rc3",
            allowed_prior_rc_tags=(
                ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
                ReleaseTagExpectation("v0.1.0-rc2", PRIOR_RC2_TARGET),
            ),
            forbidden_final_tag="v0.1.0",
            allowed_historical_final_tags=(),
        ),
    )

    assert any("Final v0.1.0 tag exists" in failure for failure in failures)


def test_forbid_final_tag_fails_when_final_tag_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.0")
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3", "v0.1.0"],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.0",
        tag_policy=_final_prep_policy(),
    )

    assert any("Final v0.1.0 tag exists" in failure for failure in failures)


def test_expected_final_annotated_tag_passes_when_target_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.0")
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3", "v0.1.0"],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
        },
    )

    assert (
        check_release_metadata(
            tmp_path,
            expected_version="0.1.0",
            tag_policy=_final_tag_policy(),
        )
        == []
    )


def test_expected_final_lightweight_tag_fails_when_annotated_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.0")
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3", "v0.1.0"],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "commit",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.0",
        tag_policy=_final_tag_policy(),
    )

    assert any(
        "Expected final tag v0.1.0 is not an annotated tag object" in failure
        for failure in failures
    )


def test_patch_rc1_metadata_accepts_historical_final_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1rc1")
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3", "v0.1.0"],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
        },
    )

    assert (
        check_release_metadata(
            tmp_path,
            expected_version="0.1.1rc1",
            tag_policy=_patch_rc1_policy(),
        )
        == []
    )


def test_cli_accepts_patch_rc1_historical_final_allowance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1rc1")
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3", "v0.1.0"],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
        },
    )
    monkeypatch.setattr(release_metadata, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_release_metadata.py",
            "--expected-version",
            "0.1.1rc1",
            "--expected-source-license",
            "GPL-3.0-or-later",
            "--allowed-historical-final-tag",
            "v0.1.0",
            "--allowed-historical-final-target",
            FINAL_TARGET,
            "--allowed-prior-rc-tag",
            "v0.1.0-rc1",
            "--allowed-prior-rc-target",
            PRIOR_RC1_TARGET,
            "--allowed-prior-rc-tag",
            "v0.1.0-rc2",
            "--allowed-prior-rc-target",
            PRIOR_RC2_TARGET,
            "--allowed-prior-rc-tag",
            "v0.1.0-rc3",
            "--allowed-prior-rc-target",
            PRIOR_RC3_TARGET,
            "--forbid-final-tag",
            "v0.1.1",
        ],
    )

    assert release_metadata.main() == 0


def test_patch_rc1_historical_final_wrong_target_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1rc1")
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3", "v0.1.0"],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": ZERO_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.1rc1",
        tag_policy=_patch_rc1_policy(),
    )

    assert any(f"not {FINAL_TARGET}" in failure for failure in failures)


def test_patch_rc1_historical_final_lightweight_tag_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1rc1")
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3", "v0.1.0"],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "commit",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.1rc1",
        tag_policy=_patch_rc1_policy(),
    )

    assert any(
        "Expected historical final tag v0.1.0 is not an annotated tag object" in failure
        for failure in failures
    )


def test_patch_rc1_forbids_v0_1_1_final_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1rc1")
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3", "v0.1.0", "v0.1.1"],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1": PATCH_RC1_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.1rc1",
        tag_policy=_patch_rc1_policy(),
    )

    assert any("Final v0.1.1 tag exists" in failure for failure in failures)


def test_expected_patch_rc1_annotated_tag_passes_when_target_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1rc1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
        },
    )

    assert (
        check_release_metadata(
            tmp_path,
            expected_version="0.1.1rc1",
            tag_policy=_patch_rc1_policy(rc_target=PATCH_RC1_TARGET),
        )
        == []
    )


def test_expected_patch_rc1_wrong_target_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1rc1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": ZERO_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.1rc1",
        tag_policy=_patch_rc1_policy(rc_target=PATCH_RC1_TARGET),
    )

    assert any(f"not {PATCH_RC1_TARGET}" in failure for failure in failures)


def test_expected_patch_rc1_lightweight_tag_fails_when_annotated_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1rc1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "commit",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.1rc1",
        tag_policy=_patch_rc1_policy(rc_target=PATCH_RC1_TARGET),
    )

    assert any(
        "Expected RC tag v0.1.1-rc1 is not an annotated tag object" in failure
        for failure in failures
    )


def test_patch_rc1_unexpected_v0_1_1_tag_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1rc1")
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3", "v0.1.0", "v0.1.1-rc2"],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc2": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc2": PATCH_RC1_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.1rc1",
        tag_policy=_patch_rc1_policy(),
    )

    assert any(
        "Unexpected local v0.1* Git tags exist: v0.1.1-rc2" in failure
        for failure in failures
    )


def test_patch_final_metadata_accepts_historical_final_and_prior_patch_rc1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
        },
    )

    assert (
        check_release_metadata(
            tmp_path,
            expected_version="0.1.1",
            tag_policy=_patch_final_prep_policy(),
        )
        == []
    )


def test_patch_final_metadata_historical_final_wrong_target_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1")
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3", "v0.1.0", "v0.1.1-rc1"],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": ZERO_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.1",
        tag_policy=_patch_final_prep_policy(),
    )

    assert any(f"not {FINAL_TARGET}" in failure for failure in failures)


def test_patch_final_metadata_prior_patch_rc1_wrong_target_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1")
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc3", "v0.1.0", "v0.1.1-rc1"],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": ZERO_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.1",
        tag_policy=_patch_final_prep_policy(),
    )

    assert any(f"not {PATCH_RC1_TARGET}" in failure for failure in failures)


def test_patch_final_prep_forbids_v0_1_1_final_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.1",
        tag_policy=_patch_final_prep_policy(),
    )

    assert any("Final v0.1.1 tag exists" in failure for failure in failures)


def test_expected_patch_final_annotated_tag_passes_when_target_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
        },
    )

    assert (
        check_release_metadata(
            tmp_path,
            expected_version="0.1.1",
            tag_policy=_patch_final_tag_policy(),
        )
        == []
    )


def test_expected_patch_final_lightweight_tag_fails_when_annotated_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "commit",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.1",
        tag_policy=_patch_final_tag_policy(),
    )

    assert any(
        "Expected final tag v0.1.1 is not an annotated tag object" in failure
        for failure in failures
    )


def test_patch_final_unexpected_v0_1_1_tag_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1-rc2",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1-rc2": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1-rc2": PATCH_FINAL_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.1",
        tag_policy=_patch_final_prep_policy(),
    )

    assert any(
        "Unexpected local v0.1* Git tags exist: v0.1.1-rc2" in failure
        for failure in failures
    )


def test_patch_v012_rc1_metadata_accepts_multiple_historical_final_tags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.2rc1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
        },
    )

    assert (
        check_release_metadata(
            tmp_path,
            expected_version="0.1.2rc1",
            tag_policy=_patch_v012_rc1_prep_policy(),
        )
        == []
    )


def test_patch_v012_rc1_historical_v011_wrong_target_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.2rc1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": ZERO_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.2rc1",
        tag_policy=_patch_v012_rc1_prep_policy(),
    )

    assert any(f"not {PATCH_FINAL_TARGET}" in failure for failure in failures)


def test_patch_v012_rc1_prior_v011_rc1_wrong_target_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.2rc1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": ZERO_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.2rc1",
        tag_policy=_patch_v012_rc1_prep_policy(),
    )

    assert any(f"not {PATCH_RC1_TARGET}" in failure for failure in failures)


def test_patch_v012_rc1_forbids_v0_1_2_final_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.2rc1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
            "v0.1.2",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
            "v0.1.2": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
            "v0.1.2": PATCH_V012_FINAL_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.2rc1",
        tag_policy=_patch_v012_rc1_prep_policy(),
    )

    assert any("Final v0.1.2 tag exists" in failure for failure in failures)


def test_expected_patch_v012_rc1_annotated_tag_passes_when_target_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.2rc1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
            "v0.1.2-rc1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
            "v0.1.2-rc1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
            "v0.1.2-rc1": PATCH_V012_RC1_TARGET,
        },
    )

    assert (
        check_release_metadata(
            tmp_path,
            expected_version="0.1.2rc1",
            tag_policy=_patch_v012_rc1_tag_policy(),
        )
        == []
    )


def test_expected_patch_v012_rc1_wrong_target_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.2rc1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
            "v0.1.2-rc1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
            "v0.1.2-rc1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
            "v0.1.2-rc1": ZERO_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.2rc1",
        tag_policy=_patch_v012_rc1_tag_policy(),
    )

    assert any(f"not {PATCH_V012_RC1_TARGET}" in failure for failure in failures)


def test_expected_patch_v012_rc1_lightweight_tag_fails_when_annotated_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.2rc1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
            "v0.1.2-rc1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
            "v0.1.2-rc1": "commit",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
            "v0.1.2-rc1": PATCH_V012_RC1_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.2rc1",
        tag_policy=_patch_v012_rc1_tag_policy(),
    )

    assert any(
        "Expected RC tag v0.1.2-rc1 is not an annotated tag object" in failure
        for failure in failures
    )


def test_patch_v012_rc1_unexpected_v0_1_2_tag_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.2rc1")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
            "v0.1.2-rc2",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
            "v0.1.2-rc2": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
            "v0.1.2-rc2": PATCH_V012_RC1_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.2rc1",
        tag_policy=_patch_v012_rc1_prep_policy(),
    )

    assert any(
        "Unexpected local v0.1* Git tags exist: v0.1.2-rc2" in failure
        for failure in failures
    )


def test_patch_v012_final_metadata_accepts_prior_rc1_and_historical_finals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.2")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
            "v0.1.2-rc1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
            "v0.1.2-rc1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
            "v0.1.2-rc1": PATCH_V012_RC1_TARGET,
        },
    )

    assert (
        check_release_metadata(
            tmp_path,
            expected_version="0.1.2",
            tag_policy=_patch_v012_final_prep_policy(),
        )
        == []
    )


def test_patch_v012_final_metadata_historical_v011_wrong_target_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.2")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
            "v0.1.2-rc1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
            "v0.1.2-rc1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": ZERO_TARGET,
            "v0.1.2-rc1": PATCH_V012_RC1_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.2",
        tag_policy=_patch_v012_final_prep_policy(),
    )

    assert any(f"not {PATCH_FINAL_TARGET}" in failure for failure in failures)


def test_patch_v012_final_metadata_prior_v012_rc1_wrong_target_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.2")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
            "v0.1.2-rc1",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
            "v0.1.2-rc1": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
            "v0.1.2-rc1": ZERO_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.2",
        tag_policy=_patch_v012_final_prep_policy(),
    )

    assert any(f"not {PATCH_V012_RC1_TARGET}" in failure for failure in failures)


def test_patch_v012_final_prep_forbids_v0_1_2_final_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.2")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
            "v0.1.2-rc1",
            "v0.1.2",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
            "v0.1.2-rc1": "tag",
            "v0.1.2": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
            "v0.1.2-rc1": PATCH_V012_RC1_TARGET,
            "v0.1.2": PATCH_V012_FINAL_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.2",
        tag_policy=_patch_v012_final_prep_policy(),
    )

    assert any("Final v0.1.2 tag exists" in failure for failure in failures)


def test_expected_patch_v012_final_annotated_tag_passes_when_target_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.2")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
            "v0.1.2-rc1",
            "v0.1.2",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
            "v0.1.2-rc1": "tag",
            "v0.1.2": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
            "v0.1.2-rc1": PATCH_V012_RC1_TARGET,
            "v0.1.2": PATCH_V012_FINAL_TARGET,
        },
    )

    assert (
        check_release_metadata(
            tmp_path,
            expected_version="0.1.2",
            tag_policy=_patch_v012_final_tag_policy(),
        )
        == []
    )


def test_expected_patch_v012_final_lightweight_tag_fails_when_annotated_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.2")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
            "v0.1.2-rc1",
            "v0.1.2",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
            "v0.1.2-rc1": "tag",
            "v0.1.2": "commit",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
            "v0.1.2-rc1": PATCH_V012_RC1_TARGET,
            "v0.1.2": PATCH_V012_FINAL_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.2",
        tag_policy=_patch_v012_final_tag_policy(),
    )

    assert any(
        "Expected final tag v0.1.2 is not an annotated tag object" in failure
        for failure in failures
    )


def test_patch_v012_final_unexpected_v0_1_2_tag_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path, version="0.1.2")
    _mock_git_tags(
        monkeypatch,
        tags=[
            "v0.1.0-rc1",
            "v0.1.0-rc2",
            "v0.1.0-rc3",
            "v0.1.0",
            "v0.1.1-rc1",
            "v0.1.1",
            "v0.1.2-rc1",
            "v0.1.2-rc2",
        ],
        tag_types={
            "v0.1.0-rc1": "tag",
            "v0.1.0-rc2": "tag",
            "v0.1.0-rc3": "tag",
            "v0.1.0": "tag",
            "v0.1.1-rc1": "tag",
            "v0.1.1": "tag",
            "v0.1.2-rc1": "tag",
            "v0.1.2-rc2": "tag",
        },
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": PRIOR_RC2_TARGET,
            "v0.1.0-rc3": PRIOR_RC3_TARGET,
            "v0.1.0": FINAL_TARGET,
            "v0.1.1-rc1": PATCH_RC1_TARGET,
            "v0.1.1": PATCH_FINAL_TARGET,
            "v0.1.2-rc1": PATCH_V012_RC1_TARGET,
            "v0.1.2-rc2": PATCH_V012_FINAL_TARGET,
        },
    )

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.2",
        tag_policy=_patch_v012_final_prep_policy(),
    )

    assert any(
        "Unexpected local v0.1* Git tags exist: v0.1.2-rc2" in failure
        for failure in failures
    )


def test_unexpected_release_tag_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0-rc4"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag"},
        commits={"v0.1.0-rc1": PRIOR_RC1_TARGET, "v0.1.0-rc2": PRIOR_RC2_TARGET},
    )

    failures = check_release_metadata(tmp_path, expected_version="0.1.0rc3")

    assert any(
        "Unexpected local v0.1* Git tags exist: v0.1.0-rc4" in failure
        for failure in failures
    )


def test_forbid_release_tags_rejects_existing_rc_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(monkeypatch, tags=["v0.1.0-rc1"])

    failures = check_release_metadata(
        tmp_path,
        expected_version="0.1.0rc3",
        tag_policy=ReleaseTagPolicy(forbid_release_tags=True),
    )

    assert any("strict pre-tag mode forbids release tags" in failure for failure in failures)
