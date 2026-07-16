from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STRATEGY = REPO_ROOT / "docs" / "release" / "code_signing_installer_strategy.md"
PUBLIC_DOCS_QA = REPO_ROOT / "tools" / "qa" / "check_public_docs.py"
RELEASE_ASSET_DOCS = (
    REPO_ROOT / "docs" / "tutorials" / "release_asset_smoke_walkthrough.md",
    REPO_ROOT / "docs" / "release" / "release_asset_download_smoke.md",
    REPO_ROOT / "docs" / "release" / "windows_portable_zip.md",
    REPO_ROOT / "tools" / "release" / "README.md",
    REPO_ROOT / "docs" / "04_validation_matrix.md",
    REPO_ROOT / "docs" / "10_release_checklist.md",
)
STATIC_ONLY_CONTRACT = """The checker verifies release identity and static consistency only. `quick`
reports `IDENTITY_BOUND_QUICK`; `full-static` adds static package and
portable-layout inspection and reports `IDENTITY_BOUND_FULL_STATIC`. Both set
`release_readiness=false`. Neither level extracts or installs a package,
imports downloaded code, runs a downloaded CLI, launches
`OpenSolverWorkbench.exe`, proves runtime behavior, establishes engineering
correctness, or establishes publication readiness."""
FIXTURE_CONTRACT = """`tests/fixtures/release_assets` is a frozen synthetic, non-installable
fixture. It is not a byte snapshot of the published `v0.1.3-rc1` assets and
supplies no remote provenance."""
TARGET_CONTRACT = """Immutable target authority is the annotated Git tag object peeled to its exact
40-hex commit. GitHub Release `target_commitish` is display context only and
cannot override the selected profile or caller-supplied target."""
HISTORICAL_CORRECTION = (
    "Use `tag=v0.1.3-rc1` for the public prerelease current at the time of this "
    "smoke validation."
)
RELEASE_ASSET_COMMANDS = (
    ".venv\\Scripts\\python.exe tools\\qa\\check_release_asset_smoke.py "
    "--mode current-live --download-dir "
    "artifacts\\release\\download_smoke\\manual-current "
    "--verification-level quick --json-out "
    "artifacts\\release\\download_smoke\\manual-current-summary.json",
    ".venv\\Scripts\\python.exe tools\\qa\\check_release_asset_smoke.py "
    "--mode explicit-remote --repo CAPTW/OpenSourceWorkBench "
    "--tag v0.1.3-rc1 --expected-version 0.1.3rc1 "
    "--expected-target a6e8d3a8211e02359841d10e1947e16ab847b132 "
    "--download-dir artifacts\\release\\download_smoke\\manual-v013 "
    "--verification-level quick --json-out "
    "artifacts\\release\\download_smoke\\manual-v013-summary.json",
    ".venv\\Scripts\\python.exe tools\\qa\\check_release_asset_smoke.py "
    "--mode local-set --tag v0.1.3-rc1 --expected-version 0.1.3rc1 "
    "--expected-target a6e8d3a8211e02359841d10e1947e16ab847b132 "
    "--asset-dir artifacts\\release\\download_smoke\\local-v013\\assets "
    "--verification-level quick",
    ".venv\\Scripts\\python.exe tools\\qa\\check_release_asset_smoke.py "
    "--mode offline-fixture --asset-dir tests\\fixtures\\release_assets "
    "--verification-level quick",
)


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


def test_release_asset_verification_docs_use_identity_bound_static_only_contract() -> None:
    texts = {path: _read(path) for path in RELEASE_ASSET_DOCS}
    combined = "\n".join(texts.values())

    for path, text in texts.items():
        assert STATIC_ONLY_CONTRACT in text, path
        assert "`v0.1.5-rc1`" in text, path
        assert "`v0.1.3-rc1`" in text, path

    for mode in ("current-live", "explicit-remote", "local-set", "offline-fixture"):
        assert f"--mode {mode}" in combined
    for command in RELEASE_ASSET_COMMANDS:
        assert command in combined
    assert FIXTURE_CONTRACT in combined
    assert TARGET_CONTRACT in combined
    assert combined.count(HISTORICAL_CORRECTION) == 1

    for stale_form in (
        "--offline-asset-dir",
        "--full-smoke",
        "full_smoke=false",
        "full_smoke=true",
        "--skip-portable-exe",
        "tools\\release\\check_release_assets.py",
    ):
        assert stale_form not in combined
    for stale_behavior in (
        "Full smoke may install the wheel",
        "install the downloaded wheel in a fresh virtual environment",
        "run `python -m osw.cli --version`",
        "optionally install the sdist",
        "optional executable `--help` smoke",
    ):
        assert stale_behavior not in combined
