from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverExportSummaryFormat,
    plan_optional_solver_export_summary_save,
)


def _codes(plan) -> set[str]:
    return {diagnostic.code for diagnostic in plan.diagnostics}


def test_save_plan_rejects_missing_path() -> None:
    plan = plan_optional_solver_export_summary_save("")

    assert plan.can_save is False
    assert "OSE_PATH_REQUIRED" in _codes(plan)
    assert plan.would_write_file is False


def test_save_plan_rejects_unsafe_traversal_path() -> None:
    plan = plan_optional_solver_export_summary_save("..\\summary.json")

    assert plan.can_save is False
    assert "OSE_UNSAFE_PATH" in _codes(plan)


def test_save_plan_rejects_unsupported_extension(tmp_path) -> None:
    plan = plan_optional_solver_export_summary_save(tmp_path / "summary.pdf")

    assert plan.can_save is False
    assert "OSE_UNSUPPORTED_EXTENSION" in _codes(plan)


def test_save_plan_rejects_missing_parent(tmp_path) -> None:
    plan = plan_optional_solver_export_summary_save(
        tmp_path / "missing" / "summary.json"
    )

    assert plan.can_save is False
    assert "OSE_PARENT_MISSING" in _codes(plan)


def test_save_plan_blocks_overwrite_by_default(tmp_path) -> None:
    target = tmp_path / "summary.json"
    target.write_text("existing", encoding="utf-8")

    plan = plan_optional_solver_export_summary_save(target)

    assert plan.can_save is False
    assert "OSE_OVERWRITE_BLOCKED" in _codes(plan)
    assert target.read_text(encoding="utf-8") == "existing"


def test_save_plan_accepts_existing_parent_supported_extension(tmp_path) -> None:
    target = tmp_path / "summary.md"

    plan = plan_optional_solver_export_summary_save(
        target,
        export_format=OptionalSolverExportSummaryFormat.MARKDOWN,
    )

    assert plan.can_save is True
    assert plan.file_extension == ".md"
    assert plan.export_format == OptionalSolverExportSummaryFormat.MARKDOWN
    assert plan.parent_exists is True
    assert plan.target_exists is False
    assert plan.would_write_file is False
