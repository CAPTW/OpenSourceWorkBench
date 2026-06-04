from __future__ import annotations

from tools.qa.check_public_docs import check_public_docs


def test_public_docs_are_present_and_scoped() -> None:
    assert check_public_docs() == []
