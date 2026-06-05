from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STRATEGY = REPO_ROOT / "docs" / "release" / "code_signing_installer_strategy.md"
PUBLIC_DOCS_QA = REPO_ROOT / "tools" / "qa" / "check_public_docs.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_code_signing_strategy_doc_exists() -> None:
    assert STRATEGY.exists()


def test_current_release_trust_state_is_explicit() -> None:
    text = _read(STRATEGY).lower()
    assert "unsigned portable zip" in text
    assert "msi installer: none" in text
    assert "authenticode code signing: none" in text
    assert "external solvers: optional and not bundled" in text


def test_integrity_and_identity_mechanisms_are_distinct() -> None:
    text = _read(STRATEGY).lower()
    assert "checksums and `release_asset_manifest.json`" in text
    assert "do not identify a windows publisher" in text
    assert "artifact attestations" in text
    assert "do not replace authenticode code signing" in text


def test_release_trust_doc_avoids_overclaims() -> None:
    text = _read(STRATEGY).lower()
    forbidden = (
        "stable production release",
        "smartscreen bypass",
        "msi installer exists",
        "msix installer exists",
        "microsoft store distribution exists",
        "code signing is configured",
        "external solvers are bundled",
    )
    for phrase in forbidden:
        assert phrase not in text


def test_release_trust_doc_records_secret_policy() -> None:
    text = _read(STRATEGY).lower()
    assert "do not commit certificates" in text
    assert "private keys" in text
    assert "pfx files" in text
    assert "do not print signing secrets in logs" in text


def test_public_docs_qa_requires_strategy_doc() -> None:
    text = _read(PUBLIC_DOCS_QA)
    assert "code_signing_installer_strategy.md" in text
