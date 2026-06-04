from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TUTORIALS = REPO_ROOT / "docs" / "tutorials"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_tutorial_index_exists() -> None:
    text = _read(TUTORIALS / "README.md").lower()
    assert "first cli walkthrough" in text
    assert "result dataset walkthrough" in text
    assert "first gui walkthrough" in text
    assert "release asset smoke walkthrough" in text


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
