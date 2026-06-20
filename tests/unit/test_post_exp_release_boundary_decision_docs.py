from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "docs" / "release" / "post_exp_release_boundary_decision.md"


def _read() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_decision_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_current_release_and_develop_state_are_recorded() -> None:
    text = _normalized()

    assert "current public release: `v0.1.4-rc1`" in text
    assert "release state: public prerelease, not draft" in text
    assert "`develop` is newer than the public `v0.1.4-rc1` tag" in text
    assert "metadata still report `0.1.4rc1`" in text


def test_evidence_reviewed_and_change_classification_are_recorded() -> None:
    text = _normalized()

    assert "evidence reviewed" in text
    assert "post-experimental resultdataset scope review" in text
    assert "live calculix run-gate validation" in text
    assert "result write gui closure review" in text
    assert "change classification" in text
    assert "feature-level additions" in text
    assert "validation state" in text
    assert "docs/test/qa state" in text


def test_open_validation_state_is_recorded() -> None:
    text = _normalized()

    assert "`#6` gmsh remains open" in text
    assert "`#7` gnu octave remains open" in text
    assert "`#8` calculix `ccx` remains open" in text
    assert "`#9` openfoam remains open" in text
    assert "`#10` coolprop / cantera remains open" in text
    assert "`#11` pyvista / meshio remains open" in text
    assert "osw-valid-004 is `skipped-missing` because `ccx` was missing" in text


def test_exactly_one_selected_decision_is_recorded() -> None:
    text = _read()
    selected_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith("Selected decision:")
    ]

    assert selected_lines == ["Selected decision: `v0.1.5-rc1`"]


def test_rationale_and_non_actions_are_recorded() -> None:
    text = _normalized()

    assert "rationale" in text
    assert "large post-`v0.1.4-rc1` experimental capability line" in text
    assert "no version bump" in text
    assert "no metadata alignment" in text
    assert "no tag creation" in text
    assert "no release edit" in text
    assert "no release creation" in text
    assert "no release publish" in text
    assert "no asset build" in text
    assert "no asset upload" in text


def test_required_next_gates_are_recorded() -> None:
    text = _read()

    assert "OSW-RELEASE-032_V0_1_5RC1_METADATA_ALIGNMENT" in text
    assert "final revalidation for the selected target" in text
    assert "local annotated tag creation gate" in text
    assert "tag-only push gate" in text
    assert "asset build-from-tag gate" in text
    assert "release draft, asset upload, publish, and post-public audit gates" in text


def test_doc_does_not_claim_forbidden_state() -> None:
    text = _normalized()
    forbidden_claims = (
        "metadata is already aligned for `v0.1.5-rc1`",
        "metadata already aligned for `v0.1.5-rc1`",
        "`v0.1.5-rc1` tag exists",
        "selected release tag exists",
        "selected release assets exist",
        "live calculix validation passed",
        "live validation passed",
        "issue `#8` can close",
        "issue #8 can close",
        "solvers are bundled",
        "industrial certification is provided",
    )

    for claim in forbidden_claims:
        assert claim not in text
