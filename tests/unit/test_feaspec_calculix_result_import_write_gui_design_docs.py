from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_import_write_gui_design.md"
)


def _read() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_gui_write_design_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_status_and_boundaries_are_explicit() -> None:
    text = _normalized()

    assert "design-only" in text
    assert "no gui write command implementation" in text
    assert "no file dialog implementation" in text
    assert "no solver execution" in text


def test_relationship_to_existing_layers_is_defined() -> None:
    text = _normalized()

    assert "relationship to existing layers" in text
    assert "feaspec-calculix-result-import-preview" in text
    assert "feaspec-calculix-result-import-write" in text
    assert "resultdataset write plan model" in text
    assert "schema payload model" in text
    assert "library writer" in text
    assert "human review gui patterns" in text


def test_proposed_entry_points_and_workflow_are_defined() -> None:
    text = _normalized()

    assert "proposed gui entry points" in text
    assert "result import preview panel" in text
    assert "future resultdataset write dialog" in text
    assert "future project context action" in text
    assert "workflow" in text
    assert "select an explicit calculix result directory" in text
    assert "choose an explicit output directory" in text
    assert "final review-first confirmation" in text


def test_panels_tabs_and_action_states_are_defined() -> None:
    text = _normalized()

    assert "panels and tabs" in text
    assert "source/result directory" in text
    assert "artifact summary" in text
    assert "parser diagnostics" in text
    assert "draft mapping" in text
    assert "write plan" in text
    assert "schema/manifest preview" in text
    assert "safety/limitations" in text
    assert "write action" in text
    assert "action states" in text
    assert "plan blocked" in text
    assert "plan ready" in text
    assert "write disabled" in text
    assert "write ready with acknowledgements" in text
    assert "write completed" in text
    assert "write failed" in text


def test_disabled_reasons_file_dialog_policy_and_acknowledgements_are_defined() -> None:
    text = _normalized()

    assert "disabled reasons" in text
    assert "missing result directory" in text
    assert "missing output directory" in text
    assert "blocked import plan" in text
    assert "blocked write plan" in text
    assert "missing acknowledgement" in text
    assert "overwrite required" in text
    assert "unsafe path" in text
    assert "file dialog policy" in text
    assert "require an explicit output directory" in text
    assert "no hidden defaults" in text
    assert "remember successful selections only" in text
    assert "overwrite confirmation" in text
    assert "acknowledgements" in text
    assert "limitations" in text
    assert "review required" in text
    assert "create directory" in text


def test_cli_gui_consistency_and_safety_boundary_are_defined() -> None:
    text = _normalized()

    assert "cli and gui consistency" in text
    assert "plan-only inspection before write" in text
    assert "explicit write intent" in text
    assert "the same diagnostics and blocker semantics" in text
    assert "exit/status semantics translated to visible ui state" in text
    assert "safety boundary" in text
    assert "no solveradapter" in text
    assert "no runner" in text
    assert "no subprocess use" in text
    assert "no projectschema mutation" in text
    assert "no vlm api" in text


def test_issue_8_non_goals_and_future_tests_are_defined() -> None:
    text = _normalized()

    assert "issue `#8` remains open" in text
    assert "does not validate live `ccx`" in text
    assert "non-goals" in text
    assert "no cli behavior change" in text
    assert "no bundled solver" in text
    assert "future implementation tests" in text
    assert "dialog construction" in text
    assert "view-model action states" in text
    assert "file-dialog mock behavior" in text
    assert "writer mock/call boundary" in text


def test_doc_does_not_claim_forbidden_capabilities() -> None:
    text = _normalized()

    forbidden_claims = (
        "gui command exists",
        "gui write command exists",
        "live validation passed",
        "issue `#8` can close",
        "external solver is bundled",
        "industrial certification is provided",
    )
    for claim in forbidden_claims:
        assert claim not in text
