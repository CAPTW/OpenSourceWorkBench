from __future__ import annotations

import ast
from pathlib import Path

from osw.experimental.feaspec import (
    HumanReviewDialogAction,
    build_human_review_dialog_state,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT / "src" / "osw" / "experimental" / "feaspec" / "human_review_viewmodel.py"
)
VIEWMODEL_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_human_review_gui_dialog_viewmodel.md"
)
DESIGN_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_human_review_gui_dialog_design.md"
)


def _module_source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def _imported_modules() -> set[str]:
    tree = ast.parse(_module_source())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _docs_text() -> str:
    return " ".join(
        (VIEWMODEL_DOC.read_text(encoding="utf-8") + "\n" + DESIGN_DOC.read_text(encoding="utf-8"))
        .lower()
        .split()
    )


def test_viewmodel_does_not_import_pyside6_or_qt() -> None:
    imports = _imported_modules()

    assert "PySide6" not in imports
    assert not any(module.lower().startswith("pyside") for module in imports)
    assert not any("qt" in module.lower() for module in imports)


def test_viewmodel_does_not_import_gui_modules() -> None:
    assert not any(module.startswith("osw.gui") for module in _imported_modules())


def test_viewmodel_does_not_import_process_or_runner_modules() -> None:
    imports = _imported_modules()

    assert "subprocess" not in imports
    assert "osw.runners" not in imports
    assert "osw.solvers.runner" not in imports
    assert not any("runner" in module for module in imports)


def test_viewmodel_does_not_import_solver_adapter_or_exporter_renderer() -> None:
    source = _module_source()
    imports = _imported_modules()

    assert "SolverAdapter" not in source
    assert not any("calculix_exporter" in module for module in imports)
    assert not any("calculix_inp_renderer" in module for module in imports)


def test_viewmodel_does_not_write_files(tmp_path: Path) -> None:
    review_path = tmp_path / "review.json"

    state = build_human_review_dialog_state(
        source_feaspec_id="cantilever-approved",
        reviewer="reviewer@example.test",
        reviewed_at="2026-06-18T00:00:00Z",
        notes=("reviewed",),
        desired_action=HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT,
        validator_summary={"has_blockers": False, "has_errors": False, "diagnostics": []},
        validator_report_hash="sha256:validator",
        save_path=review_path,
    )

    assert state.save_plan.can_save is True
    assert not review_path.exists()


def test_docs_say_no_gui_implementation() -> None:
    assert "no gui implementation" in _docs_text()


def test_docs_say_no_solver_execution() -> None:
    assert "no solver execution" in _docs_text()


def test_docs_keep_issue_8_live_validation_separate() -> None:
    assert "issue `#8` live validation remains separate" in _docs_text()


def test_docs_do_not_claim_bundled_external_solver() -> None:
    text = _docs_text()

    assert "no bundled external solver" in text
    assert "external solvers are optional and not bundled" in text


def test_docs_do_not_claim_industrial_certification() -> None:
    text = _docs_text()

    assert "no industrial certification" in text
    assert "no certification" in text


def test_no_vlm_api_or_provider_credentials_are_introduced() -> None:
    source = _module_source()

    assert "OPENAI_API_KEY" not in source
    assert "ANTHROPIC_API_KEY" not in source
    assert "GEMINI_API_KEY" not in source
    assert "VLMProvider" not in source
    assert "api_key" not in source
    assert "credential" not in source.casefold()


def test_no_projectschema_mutation_is_introduced() -> None:
    source = _module_source()
    imports = _imported_modules()

    assert "ProjectSchema" not in source
    assert not any("project_schema" in module for module in imports)
