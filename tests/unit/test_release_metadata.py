from __future__ import annotations

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
CURRENT_RC3_TARGET = "3b85946c27c8275079476f57bdae3a02e39f2fed"
ZERO_TARGET = "0000000000000000000000000000000000000000"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_release_tree(root: Path, *, version: str = "0.1.0rc3") -> None:
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
    _write(root / "CHANGELOG.md", f"## {version} - Draft\n\nTag: v0.1.0-rc3\n")
    _write(root / "docs" / "13_license_and_version_plan.md", "# Plan\n")
    _write(root / "docs" / "14_third_party_notices.md", "# Notices\n")


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
    )


def test_release_metadata_accepts_aligned_rc3_tree(tmp_path: Path) -> None:
    _minimal_release_tree(tmp_path)

    assert check_release_metadata(tmp_path, check_tags=False) == []


def test_release_metadata_rejects_placeholder_license(tmp_path: Path) -> None:
    _minimal_release_tree(tmp_path)
    _write(tmp_path / "LICENSE", "License placeholder.\n")

    failures = check_release_metadata(tmp_path, check_tags=False)

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

    assert check_release_metadata(tmp_path) == []


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

    failures = check_release_metadata(tmp_path)

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

    failures = check_release_metadata(tmp_path)

    assert any(f"not {PRIOR_RC2_TARGET}" in failure for failure in failures)


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

    assert check_release_metadata(tmp_path, tag_policy=_rc3_policy()) == []


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

    assert check_release_metadata(tmp_path, tag_policy=_rc3_policy(rc3_target="HEAD")) == []


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

    failures = check_release_metadata(tmp_path, tag_policy=_rc3_policy())

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

    failures = check_release_metadata(tmp_path, tag_policy=_rc3_policy())

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

    failures = check_release_metadata(tmp_path)

    assert any("Final v0.1.0 tag exists" in failure for failure in failures)


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

    failures = check_release_metadata(tmp_path)

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
        tag_policy=ReleaseTagPolicy(forbid_release_tags=True),
    )

    assert any("strict pre-tag mode forbids release tags" in failure for failure in failures)
