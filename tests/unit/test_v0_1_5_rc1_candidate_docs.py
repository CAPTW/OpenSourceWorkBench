from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "docs" / "release" / "v0_1_5_rc1_candidate.md"


def _read() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_candidate_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_candidate_status_and_public_release_are_recorded() -> None:
    text = _normalized()

    assert "metadata aligned" in text
    assert "tag/release/assets not created" in text
    assert "`v0.1.4-rc1` remains the current public prerelease" in text


def test_target_version_and_tag_are_recorded() -> None:
    text = _normalized()

    assert "package version: `0.1.5rc1`" in text
    assert "future tag: `v0.1.5-rc1`" in text


def test_scope_basis_is_post_experimental_resultdataset_feaspec() -> None:
    text = _normalized()

    assert "post-experimental resultdataset/feaspec capability line" in text
    assert "resultdataset draft mapping" in text
    assert "write gui review-file persistence flow" in text


def test_validation_state_remains_open_and_skipped_missing() -> None:
    text = _normalized()

    assert "issues `#6` through `#11` remain open" in text
    assert "`#6` gmsh" in text
    assert "`#7` gnu octave" in text
    assert "`#8` calculix `ccx`" in text
    assert "`#9` openfoam" in text
    assert "`#10` coolprop / cantera" in text
    assert "`#11` pyvista / meshio" in text
    assert "issue `#8` remains `skipped-missing` because `ccx` was absent" in text


def test_non_actions_and_next_gates_are_recorded() -> None:
    text = _normalized()

    assert "no tag in this gate" in text
    assert "no release create/edit/publish" in text
    assert "no asset build/upload" in text
    assert "required next gates" in text
    assert "osw-release-033_v0_1_5rc1_final_revalidation_no_tag" in text
    assert "asset build from tag" in text


def test_candidate_doc_avoids_forbidden_claims() -> None:
    text = _normalized()
    required_cautions = (
        "no `v0.1.5-rc1` assets yet",
        "no live calculix pass yet",
        "external solvers are not bundled",
        "no certification",
    )
    forbidden_claims = (
        "`v0.1.5-rc1` public release exists",
        "live calculix validation passed",
        "issue `#8` can close",
        "issue #8 can close",
        "bundled solvers",
        "industrial certification",
    )

    for caution in required_cautions:
        assert caution in text
    for claim in forbidden_claims:
        assert claim not in text
