from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILES = (
    REPO_ROOT / "src" / "osw" / "experimental" / "feaspec" / "human_review.py",
    REPO_ROOT / "src" / "osw" / "experimental" / "feaspec" / "human_review_io.py",
    REPO_ROOT / "src" / "osw" / "experimental" / "feaspec" / "human_review_errors.py",
)
DOC_PATH = REPO_ROOT / "docs" / "experimental" / "feaspec_human_review_record_model.md"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _source_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in SOURCE_FILES)


def _doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8").lower()


def test_docs_say_no_gui_implementation() -> None:
    assert "no gui implementation" in _doc_text()


def test_docs_say_no_solver_execution() -> None:
    assert "no solver execution" in _doc_text()


def test_docs_say_run_gate_remains_separate() -> None:
    text = _doc_text()

    assert "run gate remains separate" in text
    assert "issue `#8` remains open until installed-only validation passes" in text


def test_docs_do_not_claim_certification_or_bundled_solver() -> None:
    text = _doc_text()

    assert "no certification" in text
    assert "no bundled solver" in text


def test_human_review_helpers_do_not_import_forbidden_execution_modules() -> None:
    imported = set().union(*(_imports(path) for path in SOURCE_FILES))

    assert "subprocess" not in imported
    assert "osw.solvers.runner" not in imported
    assert "osw.runners" not in imported
    assert "osw.gui" not in imported


def test_human_review_helpers_do_not_reference_solver_adapter_or_gui() -> None:
    text = _source_text()

    assert "SolverAdapter" not in text
    assert "QWidget" not in text
    assert "QDialog" not in text


def test_no_vlm_api_or_provider_credentials_are_added() -> None:
    text = _source_text().lower()

    assert "openai" not in text
    assert "anthropic" not in text
    assert "gemini" not in text
    assert "api_key" not in text
    assert "credential" not in text


def test_no_projectschema_mutation_is_introduced() -> None:
    text = _source_text().lower()
    imported = set().union(*(_imports(path) for path in SOURCE_FILES))

    assert "osw.core.project" not in imported
    assert "projectschema" not in "".join(imported).lower()
    assert "mutate_project" not in text
    assert "persist_project" not in text
