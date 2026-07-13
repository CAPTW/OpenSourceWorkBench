from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

GENERAL_ISSUE_COPY = (
    "GitHub state verified 2026-07-14: Issues #6 through #11 are closed with "
    "bounded, issue-specific evidence."
)
COMBINED_ISSUE_COPY = (
    "GitHub state verified 2026-07-14: Issues #6 through #11 are closed with "
    "bounded, issue-specific evidence; skipped-missing remains historical "
    "non-pass evidence."
)
PREPARED_MACHINE_COPY = (
    "GitHub state verified 2026-07-14: Issues #6 through #11 are closed with "
    "bounded, issue-specific evidence; revalidation or reopening requires a "
    "separate explicit gate."
)
CALCULIX_ISSUE_COPY = (
    "GitHub state verified 2026-07-14: Issue #8 is closed after bounded WSL "
    "CalculiX evidence; this workflow does not broaden that closure."
)
GUI_SUMMARY_COPY = (
    "Safety: no solver execution; no artifact copying; GitHub state verified "
    "2026-07-14: issue #8 is closed after bounded WSL CalculiX evidence, and "
    "this workflow does not broaden that closure."
)
PROJECT_SCHEMA_BLOCKER_ID = (
    "bounded_optional_validation_closure_not_projectschema_authority"
)
PROJECT_SCHEMA_BLOCKER_LABEL = (
    "bounded issues #6 through #11 closure does not authorize ProjectSchema "
    "mutation"
)

VECTOR_RELEASE_LIMITATION = (
    "- Bounded vector-field mapping and preview-only Mesh Viewer glyph "
    "controls/state are implemented for compatible three-component point/cell "
    "arrays. Live PyVista glyph rendering, arbitrary vector visualization, "
    "streamlines, tensor visualization, and time animation remain unsupported; "
    "the preview requires optional GUI/visualization components where "
    "applicable and is not solver validation, scientific validation, "
    "certification, or production readiness."
)
OPTIONAL_DEPENDENCY_LIMITATION = (
    "Full CalculiX FRD field parsing and full OpenFOAM field parsing remain "
    "deferred. Bounded vector-field mapping and preview-only Mesh Viewer glyph "
    "controls/state exist for compatible three-component point/cell arrays, "
    "but live PyVista glyph rendering, arbitrary vector visualization, "
    "streamlines, tensor visualization, time animation, and PDF export remain "
    "deferred. The preview requires optional GUI/visualization components where "
    "applicable and makes no solver-validation, scientific-validation, "
    "certification, or production-readiness claim."
)
TUTORIAL_LIMITATION = (
    "- FieldViewer does not render vector glyphs. Mesh Viewer provides bounded "
    "preview-only glyph controls/state for compatible three-component vectors; "
    "live PyVista glyph rendering, arbitrary vector visualization, streamlines, "
    "tensor visualization, and time animation remain future work."
)
MAPPER_DOCSTRING = (
    "The same module also exposes the bounded vector overlay mapper used by "
    "Mesh Viewer glyph-preview controls/state."
)
FIELD_VIEW_MODEL_LIMITATION = (
    "Field Viewer live vector-glyph rendering, streamlines, and animation remain "
    "deferred; Mesh Viewer glyph controls/state are preview-only."
)
RELEASE_ASSET_LIMITATION = (
    "- The public `v0.1.3-rc1` GitHub prerelease has five attached Release "
    "assets: a wheel, an sdist, an unsigned Windows portable ZIP, "
    "`SHA256SUMS.txt`, and `release_asset_manifest.json`. GitHub’s automatic "
    "source archives are separate from that five-asset count. No MSI, code "
    "signing, Python package-index publication, bundled-solver distribution, "
    "stable-production status, or future packaging format is claimed; those "
    "remain separately gated."
)
HISTORICAL_OPEN_CONTEXT = (
    "- At this completed maintenance gate, live optional validation issues `#6` "
    "through `#11` were still open, and `#8` was `skipped-missing` because "
    "`ccx` was absent from the local installed-only audit."
)
LATER_CLOSURE_CONTEXT = (
    "- Later issue-specific validation gates closed `#6` through `#11` with "
    "bounded, environment-scoped evidence; those closures do not convert the "
    "earlier `skipped-missing` result into a pass."
)


ISSUE_SOURCE_EXPECTATIONS: dict[str, tuple[tuple[str, int], ...]] = {
    "src/osw/cli/main.py": ((CALCULIX_ISSUE_COPY, 1),),
    "src/osw/cli/optional_solver_manifest_reload_acceptance.py": (
        (GENERAL_ISSUE_COPY, 1),
    ),
    "src/osw/cli/optional_solver_manifest_reload_acceptance_persistence.py": (
        (GENERAL_ISSUE_COPY, 1),
    ),
    "src/osw/cli/optional_solver_prepared_machine_validation.py": (
        (PREPARED_MACHINE_COPY, 1),
    ),
    "src/osw/experimental/feaspec/calculix_result_dataset_draft_mapping.py": (
        (CALCULIX_ISSUE_COPY, 1),
    ),
    "src/osw/experimental/feaspec/calculix_result_dataset_schema.py": (
        (CALCULIX_ISSUE_COPY, 1),
    ),
    "src/osw/experimental/feaspec/calculix_result_import.py": (
        (CALCULIX_ISSUE_COPY, 1),
    ),
    "src/osw/experimental/feaspec/calculix_result_write_viewmodel.py": (
        (CALCULIX_ISSUE_COPY, 1),
    ),
    "src/osw/experimental/feaspec/calculix_run_gate.py": (
        (CALCULIX_ISSUE_COPY, 2),
    ),
    "src/osw/experimental/optional_solvers/plugin_manifest_deactivation_viewmodel.py": (
        (COMBINED_ISSUE_COPY, 1),
    ),
    "src/osw/experimental/optional_solvers/plugin_manifest_discovery_refresh_viewmodel.py": (
        (COMBINED_ISSUE_COPY, 1),
    ),
    "src/osw/experimental/optional_solvers/plugin_manifest_export_summary_viewmodel.py": (
        (GENERAL_ISSUE_COPY, 1),
    ),
    "src/osw/experimental/optional_solvers/plugin_manifest_persistence_viewmodel.py": (
        (COMBINED_ISSUE_COPY, 1),
    ),
    "src/osw/experimental/optional_solvers/plugin_manifest_reactivation_viewmodel.py": (
        (COMBINED_ISSUE_COPY, 1),
    ),
    (
        "src/osw/experimental/optional_solvers/"
        "plugin_manifest_reload_acceptance_persistence_projectschema_boundary.py"
    ): (
        (GENERAL_ISSUE_COPY, 1),
        (PROJECT_SCHEMA_BLOCKER_ID, 1),
        (PROJECT_SCHEMA_BLOCKER_LABEL, 1),
    ),
    (
        "src/osw/experimental/optional_solvers/"
        "plugin_manifest_reload_acceptance_persistence_summary_audit.py"
    ): (
        (GENERAL_ISSUE_COPY, 1),
    ),
    (
        "src/osw/experimental/optional_solvers/"
        "plugin_manifest_reload_acceptance_persistence_viewmodel.py"
    ): (
        (GENERAL_ISSUE_COPY, 1),
    ),
    (
        "src/osw/experimental/optional_solvers/"
        "plugin_manifest_reload_acceptance_persistence_writer.py"
    ): (
        (GENERAL_ISSUE_COPY, 1),
    ),
    "src/osw/experimental/optional_solvers/plugin_manifest_reload_acceptance_viewmodel.py": (
        (GENERAL_ISSUE_COPY, 1),
    ),
    "src/osw/experimental/optional_solvers/plugin_manifest_reload_viewmodel.py": (
        (GENERAL_ISSUE_COPY, 1),
    ),
    "src/osw/experimental/optional_solvers/plugin_manifest_state_writer.py": (
        (GENERAL_ISSUE_COPY, 1),
    ),
    "src/osw/experimental/optional_solvers/plugin_manifest_state_writer_viewmodel.py": (
        (GENERAL_ISSUE_COPY, 1),
    ),
    "src/osw/gui/dialogs/feaspec_calculix_result_write_dialog.py": (
        (GUI_SUMMARY_COPY, 1),
        (CALCULIX_ISSUE_COPY, 1),
    ),
    "src/osw/gui/dialogs/optional_solver_plugin_manifest_reload_acceptance_panel.py": (
        (GENERAL_ISSUE_COPY, 1),
    ),
    "src/osw/gui/dialogs/optional_solver_plugin_manifest_reload_acceptance_persistence_panel.py": (
        (GENERAL_ISSUE_COPY, 1),
    ),
}


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _compact(text: str) -> str:
    return " ".join(text.split())


def _string_literals(relative: str) -> list[str]:
    tree = ast.parse(_read(relative), filename=relative)
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


def test_current_public_docs_distinguish_vector_preview_rendering_and_release_assets() -> None:
    known_limitations = _compact(_read("docs/release/known_limitations_v0_1.md"))
    optional_dependencies = _compact(_read("docs/install/optional_dependencies.md"))
    tutorial = _compact(_read("docs/tutorials/result_dataset_walkthrough.md"))
    mapper = _compact(_read("src/osw/post/result_field_mapping.py"))

    assert _compact(VECTOR_RELEASE_LIMITATION) in known_limitations
    assert _compact(RELEASE_ASSET_LIMITATION) in known_limitations
    assert _compact(OPTIONAL_DEPENDENCY_LIMITATION) in optional_dependencies
    assert _compact(TUTORIAL_LIMITATION) in tutorial
    assert _compact(MAPPER_DOCSTRING) in mapper

    for relative in (
        "src/osw/post/result_view_model.py",
        "src/osw/post/field_view_model.py",
    ):
        assert FIELD_VIEW_MODEL_LIMITATION in _string_literals(relative)

    audited = " ".join((known_limitations, optional_dependencies, tutorial)).lower()
    for positive_uplift in (
        "is production ready",
        "validated on native windows",
        "solvers are bundled",
        "certified for",
        "publication ready",
    ):
        assert positive_uplift not in audited


def test_live_issue_status_literals_use_dated_bounded_closure_copy() -> None:
    stale_literals = (
        "remain open",
        "remains open",
        "remain live optional validation issues",
        "keep issues #6 through #11 open",
        "live_optional_validation_issues_open",
        "validation issues #6 through #11 unresolved",
        "separate and open",
    )

    for relative, expectations in ISSUE_SOURCE_EXPECTATIONS.items():
        literals = _string_literals(relative)
        for expected, count in expectations:
            assert literals.count(expected) == count, relative
        lowered = "\n".join(literals).lower()
        for stale in stale_literals:
            assert stale not in lowered, f"{relative}: {stale}"


def test_historical_issue_status_records_remain_framed() -> None:
    maintenance = _compact(_read("docs/maintenance/gui_aggregate_timeout_hardening.md"))
    decision_log = _compact(_read("docs/07_decision_log.md")).lower()
    changelog = _compact(_read("CHANGELOG.md")).lower()

    assert _compact(HISTORICAL_OPEN_CONTEXT) in maintenance
    assert _compact(LATER_CLOSURE_CONTEXT) in maintenance
    assert "issues `#6` through `#11` remain open" in decision_log
    assert "issues `#6` through `#11` remain open" in changelog
    assert "issue `#8` remains `skipped-missing`" in changelog


def test_issue_status_copy_preserves_non_claim_boundaries() -> None:
    main = _read("src/osw/cli/main.py")
    exporter = _read("src/osw/experimental/feaspec/calculix_exporter.py")
    result_viewmodel = _read(
        "src/osw/experimental/feaspec/calculix_result_write_viewmodel.py"
    )
    dialog = _read("src/osw/gui/dialogs/feaspec_calculix_result_write_dialog.py")
    acceptance = _read(
        "src/osw/gui/dialogs/optional_solver_plugin_manifest_reload_acceptance_panel.py"
    )

    assert "Issue #8 live CalculiX validation remains separate." in main
    assert "Issue #8 live CalculiX validation remains separate." in exporter
    assert "FWVM_ISSUE_8_OPEN" in result_viewmodel
    assert "No solver execution." in dialog
    assert "External solvers are optional and not bundled." in dialog
    assert "Trust label is not certification." in acceptance
    assert "Accepted state does not close issues or mutate releases." in acceptance

    combined_source = "\n".join(_read(path) for path in ISSUE_SOURCE_EXPECTATIONS)
    lowered = combined_source.lower()
    for network_token in (
        "import requests",
        "import httpx",
        "urllib.request",
        "api.github.com",
        "gh api",
    ):
        assert network_token not in lowered

    approved_copy = " ".join(
        (
            GENERAL_ISSUE_COPY,
            COMBINED_ISSUE_COPY,
            PREPARED_MACHINE_COPY,
            CALCULIX_ISSUE_COPY,
            GUI_SUMMARY_COPY,
            PROJECT_SCHEMA_BLOCKER_LABEL,
        )
    ).lower()
    for positive_uplift in (
        "certified for",
        "production-ready",
        "native windows validated",
        "bundled solver included",
        "publication-ready",
    ):
        assert positive_uplift not in approved_copy
