"""Tests for additive Project.selections and BoundaryCondition.target_ref wiring."""

from __future__ import annotations

import json

from osw.core.project_schema import (
    CURRENT_SCHEMA_VERSION,
    DEFAULT_PROJECT_SCHEMA_VERSION,
    BoundaryCondition,
    PhysicsSetup,
    Project,
    ProjectMetadata,
)
from osw.core.selection import BoundaryTargetRef, NamedSelection, SelectionTargetRef


def _selection(selection_id: str = "sel-1") -> NamedSelection:
    return NamedSelection(
        id=selection_id,
        name="Inlet",
        entity_kind="node",
        targets=[SelectionTargetRef(kind="node", ids=[1, 2, 3], mesh_ref="mesh-1")],
        source_mesh_ref="mesh-1",
    )


def test_project_defaults_selections_to_empty_list() -> None:
    project = Project(metadata=ProjectMetadata(name="P"))
    assert project.selections == []


def test_old_project_dict_without_selections_loads_unchanged() -> None:
    legacy = {"schema_version": "0.1", "metadata": {"name": "Legacy"}}
    project = Project.from_dict(legacy)
    assert project.selections == []
    # An empty selections list is not emitted, so legacy serialization is unchanged.
    assert "selections" not in project.to_dict()


def test_project_with_named_selection_roundtrips() -> None:
    project = Project(metadata=ProjectMetadata(name="P"), selections=[_selection()])
    payload = project.to_dict()
    assert CURRENT_SCHEMA_VERSION == "0.4"
    assert DEFAULT_PROJECT_SCHEMA_VERSION == "0.1"
    assert payload["schema_version"] == DEFAULT_PROJECT_SCHEMA_VERSION
    assert len(payload["selections"]) == 1
    restored = Project.from_dict(payload)
    assert len(restored.selections) == 1
    assert restored.selections[0].id == "sel-1"
    # Stable through a JSON serialization round-trip.
    reloaded = Project.from_dict(json.loads(json.dumps(payload)))
    assert reloaded.selections[0] == project.selections[0]


def test_boundary_condition_legacy_target_only_remains_valid() -> None:
    bc = BoundaryCondition(name="fix", kind="fixed", value="0", target="face-1")
    assert bc.target_ref is None
    assert "target_ref" not in bc.to_dict()
    project = Project(
        metadata=ProjectMetadata(name="P"),
        physics=[PhysicsSetup(name="s", boundary_conditions=[bc])],
    )
    assert not project.validate().has_errors


def test_boundary_condition_target_ref_valid_selection_validates() -> None:
    bc = BoundaryCondition(
        name="fix",
        kind="fixed",
        value="0",
        target="Inlet",
        target_ref=BoundaryTargetRef(selection_id="sel-1", display="Inlet"),
    )
    project = Project(
        metadata=ProjectMetadata(name="P"),
        physics=[PhysicsSetup(name="s", boundary_conditions=[bc])],
        selections=[_selection("sel-1")],
    )
    report = project.validate()
    assert not report.has_errors
    assert not any("missing selection id" in message.message for message in report.messages)
    # target_ref round-trips through the boundary-condition dict.
    restored = BoundaryCondition.from_dict(bc.to_dict())
    assert restored.target_ref is not None
    assert restored.target_ref.selection_id == "sel-1"


def test_boundary_condition_target_ref_missing_selection_warns() -> None:
    bc = BoundaryCondition(
        name="fix",
        kind="fixed",
        value="0",
        target="Inlet",
        target_ref=BoundaryTargetRef(selection_id="does-not-exist"),
    )
    project = Project(
        metadata=ProjectMetadata(name="P"),
        physics=[PhysicsSetup(name="s", boundary_conditions=[bc])],
    )
    report = project.validate()
    assert report.has_warnings
    assert any(
        "missing selection id: does-not-exist" in message.message for message in report.messages
    )
    # Missing selection is a warning, not a hard error.
    assert not report.has_errors


def test_duplicate_selection_ids_are_errors() -> None:
    project = Project(
        metadata=ProjectMetadata(name="P"),
        selections=[_selection("dup"), _selection("dup")],
    )
    report = project.validate()
    assert report.has_errors
    assert any("Duplicate named selection id" in message.message for message in report.messages)


def test_schema_version_remains_0_1_with_selections() -> None:
    project = Project(metadata=ProjectMetadata(name="P"), selections=[_selection()])
    assert project.schema_version == DEFAULT_PROJECT_SCHEMA_VERSION == "0.1"
    assert CURRENT_SCHEMA_VERSION == "0.4"
    assert Project.from_dict(project.to_dict()).schema_version == "0.1"
