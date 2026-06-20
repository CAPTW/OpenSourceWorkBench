from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_write_gui_writer_integration_design.md"
)


def _read() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_writer_integration_design_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_status_and_boundaries_are_explicit() -> None:
    text = _normalized()

    assert "design-only" in text
    assert "no gui writer invocation" in text
    assert "no gui file writes" in text
    assert "no solver execution" in text


def test_relationship_to_existing_layers_is_defined() -> None:
    text = _normalized()

    assert "relationship to existing layers" in text
    assert "result write gui file dialog" in text
    assert "result write dialog" in text
    assert "result write view-model" in text
    assert "result import write cli" in text
    assert "resultdataset writer" in text
    assert "write plan and schema payload" in text


def test_future_write_action_enablement_is_defined() -> None:
    text = _normalized()

    assert "future write action enablement" in text
    assert "output directory selected" in text
    assert "write plan ready" in text
    assert "schema ready" in text
    assert "limitations acknowledged" in text
    assert "review required acknowledged" in text
    assert "overwrite acknowledged" in text
    assert "create-dir acknowledged" in text


def test_confirmation_flow_is_defined() -> None:
    text = _normalized()

    assert "confirmation flow" in text
    assert "final confirmation summary" in text
    assert "files to be written" in text
    assert "limitations and diagnostics" in text
    assert "no solver execution warning" in text
    assert "issue `#8` live calculix validation remains separate" in text


def test_writer_invocation_boundary_is_defined() -> None:
    text = _normalized()

    assert "future writer invocation boundary" in text
    assert "single explicit call" in text
    assert "library writer" in text
    assert "build or refresh the result import plan" in text
    assert "build the draft resultdataset mapping" in text
    assert "build the write plan" in text
    assert "build the schema payload" in text
    assert "update the view-model with the writer result summary" in text


def test_failure_handling_post_write_retry_and_state_refresh_are_defined() -> None:
    text = _normalized()

    assert "failure handling" in text
    assert "blocked write plan" in text
    assert "blocked schema" in text
    assert "writer failure" in text
    assert "partial cleanup failure" in text
    assert "overwrite or collision failure" in text
    assert "target path issue" in text
    assert "post-write ui" in text
    assert "written files" in text
    assert "sha-256 hashes" in text
    assert "open output folder action" in text
    assert "retry behavior" in text
    assert "safe retry after failure" in text
    assert "stale plans must be rebuilt" in text
    assert "state refresh" in text
    assert "after output-dir change" in text
    assert "after acknowledgement change" in text
    assert "after writer result" in text


def test_test_plan_and_safety_boundary_are_defined() -> None:
    text = _normalized()

    assert "test plan" in text
    assert "mocked writer success" in text
    assert "mocked writer failure" in text
    assert "confirmation accepted and cancelled" in text
    assert "acknowledgements gating" in text
    assert "no unexpected file writes before the mocked writer boundary" in text
    assert "safety boundary" in text
    assert "no gui source mutation" in text
    assert "no view-model source mutation" in text
    assert "no cli behavior change" in text
    assert "no library writer behavior change" in text
    assert "no solveradapter" in text
    assert "no runner" in text
    assert "no subprocess" in text


def test_issue_8_non_goals_and_forbidden_claims_are_defined() -> None:
    text = _normalized()

    assert "relationship to #8" in text
    assert "issue `#8` remains open" in text
    assert "future gui writer integration does not validate live `ccx`" in text
    assert "non-goals" in text
    assert "no bundled solver" in text
    assert "no industrial certification" in text

    forbidden_claims = (
        "writer integration exists",
        "gui file writes are active",
        "live validation passed",
        "issue `#8` can close",
        "external solvers are bundled",
        "industrial certification is provided",
    )
    for claim in forbidden_claims:
        assert claim not in text
