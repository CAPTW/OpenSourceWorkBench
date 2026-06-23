from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "maintenance" / "gui_aggregate_timeout_hardening.md"


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_gui_timeout_hardening_doc_exists() -> None:
    assert DOC.exists()


def test_doc_says_timeout_warning_only_with_full_fallback_pass() -> None:
    text = _normalized()

    assert "aggregate gui timeout is warning-only only if a full deterministic" in text
    assert "per-file fallback passes" in text
    assert "every `tests/gui/test_*.py` file" in text


def test_doc_says_aggregate_failure_is_blocking() -> None:
    text = _normalized()

    assert "aggregate gui failure is blocking" in text
    assert "failed gui file" in text
    assert "is blocking" in text


def test_doc_says_no_solver_execution_or_mutation() -> None:
    text = _normalized()

    assert "no solver execution" in text
    assert "no release edit" in text
    assert "no issue creation" in text
