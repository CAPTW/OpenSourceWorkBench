"""User-facing 3D Workspace MVP documentation and claim-boundary closure."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = (REPO_ROOT / "docs" / "02_architecture.md").read_text(encoding="utf-8")
CURRENT_CYCLE = (REPO_ROOT / "docs" / "development" / "current_cycle.md").read_text(
    encoding="utf-8"
)
KNOWN_LIMITATIONS = (REPO_ROOT / "docs" / "known_limitations.md").read_text(encoding="utf-8")
README = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
VALIDATION = (REPO_ROOT / "docs" / "04_validation_matrix.md").read_text(encoding="utf-8")
COMBINED = "\n".join((ARCHITECTURE, CURRENT_CYCLE, KNOWN_LIMITATIONS, README, VALIDATION))


def test_mvp_user_journey_and_run_commands_are_documented() -> None:
    assert "Import/Open" in COMBINED
    assert "NamedSelection" in COMBINED
    assert "Fresh-Process Reopen" in COMBINED
    assert "OSW_RUN_PREPARED_INTERACTIVE" in README
    assert "OSW_E2E_STAGE" in README
    assert "AUTHOR" in README and "RESTORE" in README and "STALE" in README
    assert "VAL-3D-008" in VALIDATION
    assert "VAL-3D-009" in VALIDATION
    assert "6936afa6d4fbb82dff67085b1f19dfee389cb7ff" in VALIDATION


def test_supported_and_unsupported_topology_are_documented() -> None:
    assert "triangle" in COMBINED.casefold()
    assert "quad" in COMBINED.casefold()
    assert "linear tetra" in COMBINED.casefold()
    assert "tetra10" in COMBINED
    assert "hexahedron" in COMBINED
    assert "hexahedron20" in COMBINED
    assert "wedge" in COMBINED
    assert "pyramid" in COMBINED


def test_adapter_diagnostics_results_and_save_boundaries_are_documented() -> None:
    assert "UNSUPPORTED_BY_ADAPTER" in ARCHITECTURE or "unsupported adapter" in COMBINED.casefold()
    assert "osw.mesh_quality.scaled_jacobian.v1" in ARCHITECTURE
    assert "osw.active_scene.v1" in COMBINED
    assert "DEFERRED_RETAINED" in COMBINED
    assert "does not launch a solver" in COMBINED.casefold() or (
        "does not run a solver subprocess" in COMBINED.casefold()
    )
    assert "advisory" in KNOWN_LIMITATIONS.casefold()
    assert "not claimed identical across GPU" in COMBINED.casefold() or (
        "not claimed identical across gpu" in COMBINED.casefold()
    )


def test_mvp_docs_do_not_overclaim_readiness_or_certification() -> None:
    lowered = COMBINED.casefold()
    assert "mvp_feature_complete_for_integration_review_with_documented_limitations" in lowered
    assert "not production-ready" in lowered or "not production ready" in lowered
    assert "not industrially certified" in lowered or "not industrial-certified" in lowered
    assert "native locality proven" not in lowered
    assert "all topologies supported" not in lowered
    assert "industry validated" not in lowered
    assert "all gpu/driver combinations verified" not in lowered
    assert "all solver workflows complete" not in lowered
