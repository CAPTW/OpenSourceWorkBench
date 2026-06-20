from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_write_gui_file_dialog_planning.md"
)


def _read() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_file_dialog_planning_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_status_and_boundaries_are_explicit() -> None:
    text = _normalized()

    assert "design/planning-only" in text
    assert "no qfiledialog implementation" in text
    assert "no gui source changes" in text
    assert "no writer invocation" in text
    assert "no file writes" in text
    assert "no solver execution" in text


def test_relationship_to_existing_layers_is_defined() -> None:
    text = _normalized()

    assert "relationship to existing layers" in text
    assert "display-only write dialog" in text
    assert "pure write view-model" in text
    assert "write cli" in text
    assert "library writer" in text
    assert "human-review file-dialog pattern" in text


def test_future_entry_points_are_defined() -> None:
    text = _normalized()

    assert "future entry points" in text
    assert "choose output directory action" in text
    assert "output directory text field" in text
    assert "create-dir acknowledgement" in text
    assert "overwrite acknowledgement" in text


def test_qfiledialog_policy_and_default_directory_policy_are_defined() -> None:
    text = _normalized()

    assert "qfiledialog policy" in text
    assert "directory selection only" in text
    assert "should not select an individual `result_dataset.json` file" in text
    assert "no hidden defaults" in text
    assert "no automatic write" in text
    assert "default directory policy" in text
    assert "last successful explicit selection" in text
    assert "visible project or result context fallback" in text
    assert "never default silently to hidden temporary directories" in text
    assert "never default silently to release asset directories" in text


def test_selection_behavior_is_no_write_and_cancel_noop() -> None:
    text = _normalized()

    assert "selection behavior" in text
    assert "cancel is no-op" in text
    assert "accepted directory selection updates" in text
    assert "view-model/save-plan only" in text
    assert "must not write files" in text
    assert "must not create directories" in text
    assert "must not call the writer" in text


def test_path_validation_create_dir_and_overwrite_are_defined() -> None:
    text = _normalized()

    assert "path validation" in text
    assert "normalize path separators" in text
    assert "reject traversal or unsafe internal paths" in text
    assert "reserved windows names" in text
    assert "create-dir behavior" in text
    assert "missing output directories require an explicit create-dir acknowledgement" in text
    assert "file-dialog selection step must not create the directory" in text
    assert "overwrite behavior" in text
    assert "existing planned files require an explicit overwrite acknowledgement" in text
    assert "selection must not overwrite anything" in text


def test_cli_gui_consistency_and_future_tests_are_defined() -> None:
    text = _normalized()

    assert "cli/gui consistency" in text
    assert "explicit output directory is required" in text
    assert "plan-only inspection precedes write" in text
    assert "limitations acknowledgement is required" in text
    assert "review-required acknowledgement is required" in text
    assert "future implementation test plan" in text
    assert "qfiledialog accepted directory" in text
    assert "qfiledialog cancel no-op" in text
    assert "no writer call during selection" in text
    assert "no file writes during selection" in text


def test_safety_boundary_and_issue_8_are_defined() -> None:
    text = _normalized()

    assert "safety boundary" in text
    assert "no solveradapter" in text
    assert "no runner" in text
    assert "no subprocess use" in text
    assert "no projectschema mutation" in text
    assert "no vlm api" in text
    assert "relationship to issue #8" in text
    assert "issue `#8` remains open" in text
    assert "does not validate live `ccx`" in text


def test_non_goals_are_defined() -> None:
    text = _normalized()

    assert "non-goals" in text
    assert "no gui file write behavior" in text
    assert "no resultdataset persistence" in text
    assert "no cli behavior change" in text
    assert "no library writer behavior change" in text
    assert "no bundled solver" in text
    assert "no industrial certification" in text


def test_doc_does_not_claim_forbidden_capabilities() -> None:
    text = _normalized()

    forbidden_claims = (
        "qfiledialog exists",
        "writer integration exists",
        "gui file writes are active",
        "live calculix validation passed",
        "issue `#8` can close",
        "external solvers are bundled",
        "industrial certification is provided",
    )
    for claim in forbidden_claims:
        assert claim not in text
