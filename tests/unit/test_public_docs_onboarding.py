from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TUTORIALS = REPO_ROOT / "docs" / "tutorials"
TUTORIAL_CURRENT_RELEASE_COPY = (
    "OSW package metadata is currently `0.1.5rc3`, and the current public GitHub "
    "prerelease is `v0.1.5-rc2`. OSW is intended for educational and research "
    "workflows, not stable-production, industrial, or regulated engineering use; "
    "it is not a MATLAB, ANSYS, or Simulink clone or a commercial CAD replacement."
)
TUTORIAL_CURRENT_RELEASE_BULLET = (
    "- understand that `v0.1.5-rc2` is the current public prerelease and that "
    "`v0.1.5-rc1` and `v0.1.3-rc1` records are historical"
)
EXAMPLES_CURRENT_RELEASE_COPY = (
    "These examples are small source-tree workflows for the current `develop` "
    "line. Package metadata is `0.1.5rc3`, and `v0.1.5-rc2` is the current public "
    "prerelease. They are intended for inspection and teaching, not production "
    "or regulated engineering use."
)
SUPERSEDED_TUTORIAL_RELEASE_COPY = (
    "OSW v0.1.3rc1 is a public prerelease for educational and research workflows. "
    "It is not a stable production solver, industrial-certified CAE tool, MATLAB "
    "clone, ANSYS clone, Simulink clone, or commercial CAD replacement."
)
SUPERSEDED_EXAMPLES_RELEASE_COPY = (
    "These examples are small, source-tree workflows for the v0.1.3rc1 release "
    "candidate. They are designed for inspection and teaching, not for certified "
    "engineering decisions."
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_tutorial_index_exists() -> None:
    text = _read(TUTORIALS / "README.md").lower()
    assert "first cli walkthrough" in text
    assert "result dataset walkthrough" in text
    assert "first gui walkthrough" in text
    assert "release asset smoke walkthrough" in text


def test_current_release_onboarding_copy_is_scope_safe() -> None:
    tutorial = _read(TUTORIALS / "README.md")
    examples = _read(REPO_ROOT / "examples" / "README.md")

    assert tutorial.count(TUTORIAL_CURRENT_RELEASE_COPY) == 1
    assert tutorial.count(TUTORIAL_CURRENT_RELEASE_BULLET) == 1
    assert examples.count(EXAMPLES_CURRENT_RELEASE_COPY) == 1
    assert "`0.1.5rc3`" in tutorial
    assert "`v0.1.5-rc2`" in tutorial
    assert "`v0.1.5-rc1`" in tutorial
    assert "`v0.1.3-rc1` records are historical" in tutorial
    assert "`0.1.5rc3`" in examples
    assert "`v0.1.5-rc2`" in examples
    assert SUPERSEDED_TUTORIAL_RELEASE_COPY not in " ".join(tutorial.split())
    assert SUPERSEDED_EXAMPLES_RELEASE_COPY not in " ".join(examples.split())
    assert "industrial-certified CAE tool" not in tutorial
    assert "certified engineering decisions" not in examples


def test_first_cli_walkthrough_has_copy_paste_commands() -> None:
    text = _read(TUTORIALS / "first_cli_walkthrough.md")
    assert "project-demo-json" in text
    assert "project-validate" in text
    assert "report-summary" in text
    assert "artifacts\\tutorials\\first_cli_demo_project.json" in text


def test_first_gui_walkthrough_links_screenshots() -> None:
    text = _read(TUTORIALS / "first_gui_walkthrough.md")
    assert "../assets/screenshots/osw_dark.png" in text
    assert "../assets/screenshots/osw_light.png" in text
    assert "../assets/screenshots/osw_system.png" in text
    assert "osw.cli gui" in text


def test_result_dataset_walkthrough_uses_safe_fixture_commands() -> None:
    text = _read(TUTORIALS / "result_dataset_walkthrough.md")
    assert "result-dataset-inspect" in text
    assert "field-dataset-inspect" in text
    assert "tests\\fixtures\\fields\\scalar_field_dataset.json" in text


def test_release_asset_smoke_walkthrough_documents_modes() -> None:
    text = _read(TUTORIALS / "release_asset_smoke_walkthrough.md")
    assert "offline fixture" in text.lower()
    assert "live github release download" in text.lower()
    assert "workflow_dispatch" in text
    assert "does not upload" in text.lower()


def test_onboarding_docs_do_not_claim_forbidden_scope() -> None:
    docs = [
        TUTORIALS / "README.md",
        TUTORIALS / "first_cli_walkthrough.md",
        TUTORIALS / "first_gui_walkthrough.md",
        TUTORIALS / "result_dataset_walkthrough.md",
        TUTORIALS / "release_asset_smoke_walkthrough.md",
        REPO_ROOT / "docs" / "examples.md",
        REPO_ROOT / "examples" / "README.md",
    ]
    combined = "\n".join(_read(path) for path in docs).lower()
    forbidden_claims = (
        "osw is a stable production",
        "is a stable production solver",
        "bundles external solvers",
        "osw is a matlab clone",
        "osw is an ansys clone",
        "osw is a simulink clone",
        "osw is an industrial-certified solver platform",
    )
    for claim in forbidden_claims:
        assert claim not in combined
