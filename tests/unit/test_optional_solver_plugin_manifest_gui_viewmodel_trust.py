from __future__ import annotations

from tests.unit.test_optional_solver_plugin_manifest_gui_viewmodel import (
    duplicate_stack_report,
    third_party_report,
    valid_project_report,
)

from osw.experimental.optional_solvers import (
    build_optional_solver_plugin_manifest_gui_viewmodel,
)


def test_trust_badges_include_project_review_text() -> None:
    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        valid_project_report()
    )

    badge = view_model.trust_badges[0]
    assert badge.source_type == "project_local"
    assert badge.trust_label == "reviewed_project"
    assert "not validation evidence" in badge.warning_text.lower()


def test_trust_badges_include_third_party_warning() -> None:
    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        third_party_report()
    )

    badge = view_model.trust_badges[0]
    assert badge.trust_label == "third_party_plugin"
    assert badge.is_third_party is True
    assert "not trusted by default" in badge.warning_text.lower()


def test_trust_badges_include_invalid_and_builtin_conflict_sources() -> None:
    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        duplicate_stack_report()
    )
    labels = {badge.trust_label for badge in view_model.trust_badges}

    assert "trusted_builtin" in labels
    assert "invalid" in labels
    assert any(badge.is_invalid for badge in view_model.trust_badges)
