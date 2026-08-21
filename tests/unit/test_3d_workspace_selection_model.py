"""Unit tests for the core 3D Workspace selection contracts."""

from __future__ import annotations

import json
from pathlib import Path

from osw.core.selection import (
    BoundaryTargetRef,
    EntityKind,
    EntityLocator,
    NamedSelection,
    SelectionMode,
    SelectionOperation,
    SelectionState,
    SelectionTargetRef,
)


def test_entity_kind_string_values() -> None:
    assert EntityKind.NODE.value == "node"
    assert EntityKind.CELL.value == "cell"
    assert EntityKind.SOLVER_LABEL.value == "solver_label"
    assert EntityKind.UNKNOWN.value == "unknown"
    # Unknown/invalid text coerces to UNKNOWN rather than raising.
    assert EntityKind.coerce("Node") is EntityKind.NODE
    assert EntityKind.coerce("bogus") is EntityKind.UNKNOWN


def test_selection_mode_values_and_coerce() -> None:
    assert {mode.value for mode in SelectionMode} == {
        "node",
        "cell",
        "face",
        "edge",
        "mixed",
        "none",
        "setup",
    }
    assert SelectionMode.coerce("cell") is SelectionMode.CELL
    assert SelectionMode.coerce("setup") is SelectionMode.SETUP
    assert SelectionMode.coerce("bogus") is SelectionMode.NONE


def test_selection_operation_values_and_coerce() -> None:
    assert {operation.value for operation in SelectionOperation} == {
        "replace",
        "add",
        "toggle",
        "subtract",
    }
    assert SelectionOperation.coerce("ADD") is SelectionOperation.ADD
    assert SelectionOperation.coerce("bogus") is SelectionOperation.REPLACE


def test_selection_target_ref_roundtrip_and_order() -> None:
    target = SelectionTargetRef(
        kind="node",
        ids=[3, 1, 2],
        mesh_ref="mesh-1",
        provenance={"node_count": 10, "source_path": "a.vtu"},
    )
    assert target.kind is EntityKind.NODE
    # Order is preserved (not sorted).
    assert target.ids == (3, 1, 2)
    restored = SelectionTargetRef.from_dict(target.to_dict())
    assert restored == target
    # JSON round-trip stays stable.
    assert SelectionTargetRef.from_dict(json.loads(json.dumps(target.to_dict()))) == target


def test_durable_entity_locator_roundtrip_is_additive_and_legacy_shape_is_stable() -> None:
    legacy = SelectionTargetRef(kind="node", ids=[3], mesh_ref="mesh-1")
    assert "locator" not in legacy.to_dict()

    locator = EntityLocator(
        identity_schema="osw.mesh_identity.v1",
        mesh_ref="mesh-1",
        mesh_fingerprint="a" * 64,
        entity_kind="node",
        id_namespace="osw.mesh.point_ordinal.v1",
        entity_ids=(3,),
    )
    durable = SelectionTargetRef(
        kind="node",
        ids=(3,),
        mesh_ref="mesh-1",
        locator=locator,
    )

    payload = json.loads(json.dumps(durable.to_dict()))
    assert payload["locator"]["mesh_fingerprint"] == "a" * 64
    assert SelectionTargetRef.from_dict(payload) == durable
    assert not durable.validate().has_errors


def test_selection_target_ref_id_type_validation() -> None:
    # Integer ids for node/cell kinds validate cleanly.
    ints = SelectionTargetRef(kind="cell", ids=[1, 2], mesh_ref="m")
    assert not ints.validate().has_errors and not ints.validate().has_warnings
    # A string id under an integer kind is a warning, not an error.
    mixed = SelectionTargetRef(kind="node", ids=["a"], mesh_ref="m")
    assert mixed.validate().has_warnings
    # solver_label kinds accept string ids without warnings.
    labels = SelectionTargetRef(kind="solver_label", ids=["inlet", "outlet"], label="patches")
    assert not labels.validate().has_warnings
    # Empty ids warn.
    assert SelectionTargetRef(kind="node", ids=[], mesh_ref="m").validate().has_warnings


def test_named_selection_validation_requires_id_name_targets() -> None:
    valid = NamedSelection(
        id="sel-1",
        name="Inlet",
        entity_kind="node",
        targets=[SelectionTargetRef(kind="node", ids=[1, 2], mesh_ref="m")],
        source_mesh_ref="m",
    )
    assert not valid.validate().has_errors

    empty = NamedSelection(id="", name="", entity_kind="node", targets=[])
    report = empty.validate()
    assert report.has_errors
    paths = {message.path for message in report.messages}
    assert any(path.endswith(".id") for path in paths)
    assert any(path.endswith(".name") for path in paths)
    assert any(path.endswith(".targets") for path in paths)


def test_named_selection_roundtrip() -> None:
    selection = NamedSelection(
        id="sel-2",
        name="Wall",
        description="fixed wall",
        entity_kind="solver_label",
        targets=[SelectionTargetRef(kind="solver_label", ids=["wall"], label="wall")],
        solver_labels={"calculix": ["NWALL"], "openfoam": "wall"},
    )
    restored = NamedSelection.from_dict(selection.to_dict())
    assert restored == selection
    # solver_labels normalize scalar strings into lists.
    assert restored.solver_labels["openfoam"] == ["wall"]


def test_selection_state_to_named_selection() -> None:
    target = SelectionTargetRef(kind="cell", ids=[5, 6], mesh_ref="mesh-9")
    state = SelectionState(active_targets=[target], mode="cell")
    assert state.to_dict()["active_targets"][0]["ids"] == [5, 6]
    named = state.to_named_selection("sel-3", "Region", description="hot region")
    assert named.id == "sel-3"
    assert named.name == "Region"
    assert named.entity_kind is EntityKind.CELL
    assert named.targets == (target,)
    assert named.source_mesh_ref == "mesh-9"
    # SelectionState round-trips too.
    assert SelectionState.from_dict(state.to_dict()) == state


def test_boundary_target_ref_roundtrip_and_empty() -> None:
    ref = BoundaryTargetRef(selection_id="sel-1", solver_label="NINLET", display="Inlet")
    assert not ref.is_empty
    assert BoundaryTargetRef.from_dict(ref.to_dict()) == ref
    assert BoundaryTargetRef().is_empty
    assert BoundaryTargetRef().validate().has_warnings


def test_selection_model_has_no_heavy_or_gui_imports() -> None:
    import osw.core.selection as selection_module

    source = Path(selection_module.__file__).read_text(encoding="utf-8")
    forbidden_tokens = (
        "PySide6",
        "pyvista",
        "import meshio",
        "import gmsh",
        "subprocess",
        "QProcess",
    )
    for forbidden in forbidden_tokens:
        assert forbidden not in source, f"selection.py must not reference {forbidden}"
