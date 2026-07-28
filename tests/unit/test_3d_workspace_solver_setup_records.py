from __future__ import annotations

import json
from importlib import import_module

import pytest

from osw.core.materials import IsotropicElastic, Material
from osw.core.project_schema import PhysicsSetup, Project, ProjectMetadata
from osw.core.selection import EntityKind, NamedSelection
from osw.core.selection_resolution import ResolutionResult, ResolutionState
from osw.core.units import Quantity


def _api() -> object:
    try:
        return import_module("osw.core.solver_setup")
    except ModuleNotFoundError:
        pytest.fail("typed solver-setup contracts are missing", pytrace=False)


def _selection(selection_id: str, kind: EntityKind) -> NamedSelection:
    return NamedSelection(id=selection_id, name=selection_id, entity_kind=kind)


def _resolved(*indices: int) -> ResolutionResult:
    return ResolutionResult(
        state=ResolutionState.RESOLVED,
        transient_indices=indices,
        total_requested=len(indices),
        resolved_count=len(indices),
        reason_code="RESOLVED",
        message="Resolved.",
    )


def _material() -> Material:
    return Material(
        material_id="steel",
        name="Steel",
        elastic=IsotropicElastic(Quantity(210e9, "Pa"), 0.3),
    )


def test_typed_records_roundtrip_additively_in_schema_0_3() -> None:
    api = _api()
    material = api.MaterialAssignmentRecord(
        id="mat-a",
        name="Steel region",
        material_id="steel",
        target_selection_id="cells-a",
    )
    support = api.FixedSupportRecord(
        id="fix-a",
        name="Clamp",
        target_selection_id="nodes-a",
        translational_dofs=(1, 2, 3),
    )
    force = api.ForceLoadRecord(
        id="force-a",
        name="Tip force",
        target_selection_id="nodes-b",
        magnitude=Quantity(2.0, "kN"),
        direction=(0.0, -2.0, 0.0),
    )
    project = Project(
        metadata=ProjectMetadata(name="Setup"),
        schema_version="0.3",
        physics=PhysicsSetup(
            setup_id="structural",
            material_assignment_records=[material],
            fixed_support_records=[support],
            force_load_records=[force],
        ),
    )

    reopened = Project.from_dict(json.loads(json.dumps(project.to_dict())))
    setup = reopened.primary_physics

    assert reopened.schema_version == "0.3"
    assert setup is not None
    assert setup.material_assignment_records == [material]
    assert setup.fixed_support_records == [support]
    assert setup.force_load_records == [force]
    assert setup.force_load_records[0].direction == (0.0, -2.0, 0.0)
    assert api.force_direction(force) == (0.0, -1.0, 0.0)

    for version in ("0.1", "0.2", "0.3"):
        legacy = Project.from_dict(
            {"schema_version": version, "metadata": {"name": version}}
        )
        assert legacy.primary_physics is None


def test_readiness_is_fail_closed_and_overlap_blocks_both_records() -> None:
    api = _api()
    records = (
        api.MaterialAssignmentRecord("mat-a", "A", "steel", "cells-a"),
        api.MaterialAssignmentRecord("mat-b", "B", "steel", "cells-b"),
        api.FixedSupportRecord("fix-a", "Clamp", "nodes-a"),
        api.ForceLoadRecord(
            "force-a",
            "Load",
            "nodes-a",
            Quantity(50.0, "N"),
            (1.0, 0.0, 0.0),
        ),
    )
    setup = PhysicsSetup(
        material_assignment_records=list(records[:2]),
        fixed_support_records=[records[2]],
        force_load_records=[records[3]],
    )
    selections = (
        _selection("cells-a", EntityKind.CELL),
        _selection("cells-b", EntityKind.CELL),
        _selection("nodes-a", EntityKind.NODE),
    )
    statuses = api.evaluate_solver_setup(
        setup,
        selections=selections,
        materials=(_material(),),
        resolutions={
            "cells-a": _resolved(0),
            "cells-b": _resolved(0),
            "nodes-a": _resolved(0, 1),
        },
    )
    by_id = {item.record_id: item for item in statuses}

    assert by_id["mat-a"].state is api.SetupReadiness.BLOCKED
    assert by_id["mat-b"].state is api.SetupReadiness.BLOCKED
    assert by_id["mat-a"].reason_code == "OVERLAPPING_MATERIAL_ASSIGNMENT"
    assert by_id["fix-a"].state is api.SetupReadiness.READY
    assert by_id["force-a"].state is api.SetupReadiness.READY

    blocked = api.evaluate_solver_setup(
        PhysicsSetup(
            force_load_records=[
                api.ForceLoadRecord(
                    "bad",
                    "Bad",
                    "missing",
                    Quantity(float("nan"), "Pa"),
                    (0.0, 0.0, 0.0),
                )
            ]
        ),
        selections=(),
        materials=(),
        resolutions={},
    )[0]
    assert blocked.state is api.SetupReadiness.BLOCKED
    assert blocked.reason_code == "MISSING_SELECTION"


def test_readiness_reports_exact_domain_material_id_and_resolution_reasons() -> None:
    api = _api()
    node = _selection("nodes", EntityKind.NODE)
    cell = _selection("cells", EntityKind.CELL)

    missing_material = api.evaluate_solver_setup(
        PhysicsSetup(
            material_assignment_records=[
                api.MaterialAssignmentRecord("mat", "Steel", "missing", "cells")
            ]
        ),
        selections=(cell,),
        materials=(),
        resolutions={"cells": _resolved(0)},
    )[0]
    wrong_domain = api.evaluate_solver_setup(
        PhysicsSetup(
            fixed_support_records=[
                api.FixedSupportRecord("support", "Support", "cells")
            ]
        ),
        selections=(cell,),
        materials=(),
        resolutions={"cells": _resolved(0)},
    )[0]
    disabled_missing_id = api.evaluate_solver_setup(
        PhysicsSetup(
            fixed_support_records=[
                api.FixedSupportRecord("", "Disabled", "nodes", enabled=False)
            ]
        ),
        selections=(node,),
        materials=(),
        resolutions={"nodes": _resolved(0)},
    )[0]

    assert missing_material.reason_code == "MISSING_MATERIAL"
    assert wrong_domain.reason_code == "WRONG_ENTITY_KIND"
    assert disabled_missing_id.reason_code == "DUPLICATE_OR_MISSING_RECORD_ID"

    for state, reason_code in (
        (ResolutionState.PARTIAL, "PARTIAL_SELECTION_MEMBERSHIP"),
        (ResolutionState.STALE, "LEGACY_IDENTITY_UNVERIFIED"),
        (ResolutionState.INVALID, "INVALID_LOCATOR"),
    ):
        status = api.evaluate_solver_setup(
            PhysicsSetup(
                fixed_support_records=[
                    api.FixedSupportRecord("support", "Support", "nodes")
                ]
            ),
            selections=(node,),
            materials=(),
            resolutions={
                "nodes": ResolutionResult(
                    state=state,
                    reason_code=reason_code,
                    message=f"{state.value} selection.",
                )
            },
        )[0]
        assert status.state is api.SetupReadiness.BLOCKED
        assert status.reason_code == reason_code


@pytest.mark.parametrize(
    ("record", "expected_reason"),
    (
        (
            lambda api: api.FixedSupportRecord(
                "support",
                "Support",
                "nodes",
                translational_dofs=(1, 1),
            ),
            "INVALID_TRANSLATIONAL_DOFS",
        ),
        (
            lambda api: api.ForceLoadRecord(
                "force",
                "Force",
                "nodes",
                Quantity(1.0, "Pa"),
                (1.0, 0.0, 0.0),
            ),
            "INVALID_FORCE_QUANTITY",
        ),
        (
            lambda api: api.ForceLoadRecord(
                "force",
                "Force",
                "nodes",
                Quantity(1.0, "N"),
                (0.0, 0.0, 0.0),
            ),
            "INVALID_FORCE_DIRECTION",
        ),
        (
            lambda api: api.ForceLoadRecord(
                "force",
                "Force",
                "nodes",
                Quantity(1.0, "N"),
                (1.0, 0.0, 0.0),
                coordinate_system="LOCAL",
            ),
            "UNSUPPORTED_COORDINATE_SYSTEM",
        ),
        (
            lambda api: api.ForceLoadRecord(
                "force",
                "Force",
                "nodes",
                Quantity(1.0, "N"),
                (1.0, 0.0, 0.0),
                application_mode="TOTAL",
            ),
            "UNSUPPORTED_APPLICATION_MODE",
        ),
    ),
)
def test_invalid_support_and_force_fields_have_exact_reasons(
    record,
    expected_reason: str,
) -> None:
    api = _api()
    selection = _selection("nodes", EntityKind.NODE)
    value = record(api)
    setup = (
        PhysicsSetup(fixed_support_records=[value])
        if isinstance(value, api.FixedSupportRecord)
        else PhysicsSetup(force_load_records=[value])
    )

    status = api.evaluate_solver_setup(
        setup,
        selections=(selection,),
        materials=(),
        resolutions={"nodes": _resolved(0)},
    )[0]

    assert status.state is api.SetupReadiness.BLOCKED
    assert status.reason_code == expected_reason


def test_typed_selection_references_block_deletion_without_reinterpreting_legacy() -> None:
    api = _api()
    from osw.core.selection_resolution import (
        NamedSelectionLifecycleError,
        delete_named_selection,
        find_named_selection_references,
    )

    selection = _selection("nodes-a", EntityKind.NODE)
    project = Project(
        metadata=ProjectMetadata(name="Refs"),
        selections=(selection,),
        physics=PhysicsSetup(
            fixed_support_records=[
                api.FixedSupportRecord("fix-a", "Clamp", "nodes-a")
            ],
            material_assignments={"legacy-cell-id": "steel"},
        ),
    )
    references = find_named_selection_references(project, "nodes-a")

    assert [(item.reference_kind, item.owner_id) for item in references] == [
        ("fixed_support", "fix-a")
    ]
    with pytest.raises(NamedSelectionLifecycleError, match="referenced"):
        delete_named_selection(
            project.selections,
            "nodes-a",
            references=references,
        )
