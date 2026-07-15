from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release-asset-smoke.yml"


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _live_job_text(text: str) -> str:
    return text.split("live-release-asset-download-smoke:", 1)[1]


def test_release_asset_smoke_workflow_exists() -> None:
    assert WORKFLOW.exists()


def test_release_asset_smoke_workflow_has_required_triggers() -> None:
    text = _workflow_text()

    assert "workflow_dispatch:" in text
    assert "pull_request:" in text
    assert "push:" in text
    assert "branches:" in text
    assert "develop" in text


def test_release_asset_smoke_workflow_uses_read_only_permissions() -> None:
    text = _workflow_text().lower()

    assert "permissions:" in text
    assert "contents: read" in text
    assert "contents: write" not in text


def test_release_asset_smoke_workflow_forbids_mutating_commands() -> None:
    text = _workflow_text().lower()

    assert "gh release upload" not in text
    assert "gh release edit" not in text
    assert "git push" not in text
    assert "--clobber" not in text


def test_release_asset_smoke_workflow_has_expected_jobs() -> None:
    text = _workflow_text()

    assert "offline-release-asset-fixture-smoke:" in text
    assert "live-release-asset-download-smoke:" in text
    assert "github.event_name == 'workflow_dispatch'" in _live_job_text(text)


def test_release_asset_smoke_workflow_scopes_github_token_to_live_job() -> None:
    text = _workflow_text()
    before_live, live = text.split("live-release-asset-download-smoke:", 1)

    assert "GH_TOKEN" not in before_live
    assert "GH_TOKEN" in live
    assert "github.token" in live


def test_release_asset_smoke_workflow_references_smoke_tools_and_tests() -> None:
    text = _workflow_text()

    assert "tools/qa/check_release_asset_smoke.py" in text
    assert "tests/unit/test_release_asset_smoke.py" in text


def test_release_asset_smoke_workflow_defaults_to_current_live_identity() -> None:
    text = _workflow_text()

    assert "default: current-live" in text
    assert "default: quick" in text
    assert "default: v0.1.5-rc1" in text


def test_release_asset_smoke_workflow_forwards_identity_through_environment() -> None:
    live = _live_job_text(_workflow_text())

    for variable in (
        "OSW_RELEASE_MODE",
        "OSW_RELEASE_REPO",
        "OSW_RELEASE_TAG",
        "OSW_RELEASE_VERSION",
        "OSW_RELEASE_TARGET",
        "OSW_VERIFICATION_LEVEL",
    ):
        assert variable in live
    assert '"--mode", $env:OSW_RELEASE_MODE' in live
    assert '"--repo", $env:OSW_RELEASE_REPO' in live
    assert '"--tag", $env:OSW_RELEASE_TAG' in live
    assert '"--expected-version", $env:OSW_RELEASE_VERSION' in live
    assert '"--expected-target", $env:OSW_RELEASE_TARGET' in live
    assert '"${{ inputs.tag }}"' not in live


def test_release_asset_smoke_workflow_pins_offline_fixture_mode() -> None:
    text = _workflow_text()

    assert "--mode offline-fixture" in text
    assert "--asset-dir tests/fixtures/release_assets" in text
    assert "--verification-level quick" in text


def test_release_asset_smoke_workflow_uses_run_scoped_outputs_without_execution() -> None:
    text = _workflow_text().lower()

    assert "artifacts/release/download_smoke/**/summary.json" in text
    assert "__release-" in text
    assert "/assets" in text
    assert "--full-smoke" not in text
    assert "--skip-portable-exe" not in text
    assert "opensolverworkbench.exe" not in text
