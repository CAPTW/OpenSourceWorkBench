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
CURRENT_RC2_TARGET = "84651ef17ea74f30706bc13b7593bf94662ada9e"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_release_tree(root: Path, *, version: str = "0.1.0rc2") -> None:
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
    _write(root / "CHANGELOG.md", f"## {version} - Draft\n\nTag: v0.1.0-rc2\n")
    _write(root / "docs" / "13_license_and_version_plan.md", "# Plan\n")
    _write(root / "docs" / "14_third_party_notices.md", "# Notices\n")


def _mock_git_tags(
    monkeypatch: pytest.MonkeyPatch,
    *,
    tags: list[str],
    tag_types: dict[str, str] | None = None,
    commits: dict[str, str] | None = None,
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
            tag = args[2].removesuffix("^{commit}")
            if tag in commits:
                return FakeCompletedProcess(stdout=commits[tag])
            return FakeCompletedProcess(returncode=1, stderr=f"missing commit {tag}")
        raise AssertionError(f"unexpected git command: {args}")

    monkeypatch.setattr(release_metadata.subprocess, "run", fake_run)


def test_release_metadata_accepts_aligned_tree(tmp_path: Path) -> None:
    _minimal_release_tree(tmp_path)

    assert check_release_metadata(tmp_path, check_tags=False) == []


def test_release_metadata_rejects_placeholder_license(tmp_path: Path) -> None:
    _minimal_release_tree(tmp_path)
    _write(tmp_path / "LICENSE", "License placeholder.\n")

    failures = check_release_metadata(tmp_path, check_tags=False)

    assert any("canonical GNU GPL version 3" in failure for failure in failures)
    assert any("placeholder" in failure for failure in failures)


def test_default_check_accepts_prior_rc1_when_current_rc2_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1"],
        tag_types={"v0.1.0-rc1": "tag"},
        commits={"v0.1.0-rc1": PRIOR_RC1_TARGET},
    )

    assert check_release_metadata(tmp_path) == []


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


def test_allowed_prior_rc1_wrong_target_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1"],
        tag_types={"v0.1.0-rc1": "tag"},
        commits={"v0.1.0-rc1": "0000000000000000000000000000000000000000"},
    )

    failures = check_release_metadata(
        tmp_path,
        tag_policy=ReleaseTagPolicy(
            allowed_prior_rc_tags=(
                ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
            ),
        ),
    )

    assert any("not 29c5c8bec8df30c7f7be72fc9be5e5409794968e" in failure for failure in failures)


def test_expected_rc2_tag_mode_accepts_matching_annotated_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag"},
        commits={"v0.1.0-rc1": PRIOR_RC1_TARGET, "v0.1.0-rc2": CURRENT_RC2_TARGET},
    )

    failures = check_release_metadata(
        tmp_path,
        tag_policy=ReleaseTagPolicy(
            expected_rc_tag="v0.1.0-rc2",
            expected_rc_target=CURRENT_RC2_TARGET,
            require_annotated_rc_tag=True,
            require_expected_rc_tag=True,
            allowed_prior_rc_tags=(
                ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
            ),
        ),
    )

    assert failures == []


def test_expected_rc2_tag_mode_rejects_wrong_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag"},
        commits={
            "v0.1.0-rc1": PRIOR_RC1_TARGET,
            "v0.1.0-rc2": "0000000000000000000000000000000000000000",
        },
    )

    failures = check_release_metadata(
        tmp_path,
        tag_policy=ReleaseTagPolicy(
            expected_rc_tag="v0.1.0-rc2",
            expected_rc_target=CURRENT_RC2_TARGET,
            require_annotated_rc_tag=True,
            require_expected_rc_tag=True,
            allowed_prior_rc_tags=(
                ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
            ),
        ),
    )

    assert any("not 84651ef17ea74f30706bc13b7593bf94662ada9e" in failure for failure in failures)


def test_expected_rc2_tag_mode_rejects_lightweight_tag_when_annotated_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "commit"},
        commits={"v0.1.0-rc1": PRIOR_RC1_TARGET, "v0.1.0-rc2": CURRENT_RC2_TARGET},
    )

    failures = check_release_metadata(
        tmp_path,
        tag_policy=ReleaseTagPolicy(
            expected_rc_tag="v0.1.0-rc2",
            expected_rc_target=CURRENT_RC2_TARGET,
            require_annotated_rc_tag=True,
            require_expected_rc_tag=True,
            allowed_prior_rc_tags=(
                ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
            ),
        ),
    )

    assert any("not an annotated tag object" in failure for failure in failures)


def test_expected_rc2_tag_mode_rejects_final_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc2", "v0.1.0"],
        tag_types={"v0.1.0-rc1": "tag", "v0.1.0-rc2": "tag"},
        commits={"v0.1.0-rc1": PRIOR_RC1_TARGET, "v0.1.0-rc2": CURRENT_RC2_TARGET},
    )

    failures = check_release_metadata(
        tmp_path,
        tag_policy=ReleaseTagPolicy(
            expected_rc_tag="v0.1.0-rc2",
            expected_rc_target=CURRENT_RC2_TARGET,
            require_annotated_rc_tag=True,
            require_expected_rc_tag=True,
            allowed_prior_rc_tags=(
                ReleaseTagExpectation("v0.1.0-rc1", PRIOR_RC1_TARGET),
            ),
        ),
    )

    assert any("Final v0.1.0 tag exists" in failure for failure in failures)


def test_unexpected_release_tag_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_release_tree(tmp_path)
    _mock_git_tags(
        monkeypatch,
        tags=["v0.1.0-rc1", "v0.1.0-rc3"],
        tag_types={"v0.1.0-rc1": "tag"},
        commits={"v0.1.0-rc1": PRIOR_RC1_TARGET},
    )

    failures = check_release_metadata(tmp_path)

    assert any(
        "Unexpected local v0.1* Git tags exist: v0.1.0-rc3" in failure
        for failure in failures
    )
