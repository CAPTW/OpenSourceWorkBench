"""Deterministic tests for durable 3D Workspace mesh identity."""

from __future__ import annotations

import math
from importlib import import_module

import pytest

from osw.mesh.mesh_model import MeshCellBlock, MeshData


def _identity_api() -> object:
    return import_module("osw.mesh.identity")


def _mesh(
    *,
    points: tuple[tuple[float, float, float], ...] | None = None,
    connectivity: tuple[tuple[int, ...], ...] = ((0, 1, 2),),
) -> MeshData:
    return MeshData(
        points=points
        or (
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        ),
        cells=(MeshCellBlock("triangle", connectivity),),
    )


def test_mesh_fingerprint_is_deterministic_and_metadata_independent() -> None:
    api = _identity_api()
    first = api.compute_mesh_fingerprint(
        MeshData(
            points=_mesh().points,
            cells=_mesh().cells,
            field_data={"source_path": "C:/private/a.vtu", "display_name": "A"},
        )
    )
    second = api.compute_mesh_fingerprint(
        MeshData(
            points=_mesh().points,
            cells=_mesh().cells,
            field_data={"source_path": "D:/other/b.vtu", "display_name": "B"},
        )
    )

    assert first == second
    assert first.schema == "osw.mesh_identity.v1"
    assert first.algorithm == "sha256"
    assert first.coordinate_basis == "unspecified"
    assert first.point_count == 3
    assert first.cell_count == 1
    assert len(first.digest) == 64
    assert first.digest == first.digest.lower()
    assert set(first.digest) <= set("0123456789abcdef")


def test_mesh_fingerprint_detects_same_count_coordinate_and_connectivity_change() -> None:
    api = _identity_api()
    baseline = api.compute_mesh_fingerprint(_mesh())
    moved = api.compute_mesh_fingerprint(
        _mesh(
            points=(
                (0.0, 0.0, 0.0),
                (1.0, 0.0, 0.0),
                (0.0, 2.0, 0.0),
            )
        )
    )
    rewired = api.compute_mesh_fingerprint(
        _mesh(connectivity=((0, 2, 1),))
    )

    assert moved.point_count == baseline.point_count
    assert moved.cell_count == baseline.cell_count
    assert rewired.point_count == baseline.point_count
    assert rewired.cell_count == baseline.cell_count
    assert moved.digest != baseline.digest
    assert rewired.digest != baseline.digest


def test_mesh_fingerprint_preserves_order_and_normalizes_negative_zero() -> None:
    api = _identity_api()
    positive_zero = api.compute_mesh_fingerprint(_mesh())
    negative_zero = api.compute_mesh_fingerprint(
        _mesh(
            points=(
                (-0.0, 0.0, -0.0),
                (1.0, -0.0, 0.0),
                (0.0, 1.0, -0.0),
            )
        )
    )
    reordered = api.compute_mesh_fingerprint(
        _mesh(
            points=(
                (1.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
            ),
            connectivity=((1, 0, 2),),
        )
    )

    assert negative_zero.digest == positive_zero.digest
    assert reordered.digest != positive_zero.digest


@pytest.mark.parametrize("coordinate", [math.nan, math.inf, -math.inf])
def test_mesh_fingerprint_rejects_non_finite_coordinates(coordinate: float) -> None:
    api = _identity_api()
    with pytest.raises(api.MeshIdentityError, match="finite"):
        api.compute_mesh_fingerprint(
            _mesh(
                points=(
                    (coordinate, 0.0, 0.0),
                    (1.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0),
                )
            )
        )


def test_mesh_fingerprint_rejects_negative_or_incomplete_connectivity() -> None:
    api = _identity_api()
    with pytest.raises(api.MeshIdentityError, match="non-negative"):
        api.compute_mesh_fingerprint(_mesh(connectivity=((0, -1, 2),)))

    inconsistent = MeshData(
        points=_mesh().points,
        cells=(MeshCellBlock("triangle", (), count=1),),
    )
    with pytest.raises(api.MeshIdentityError, match="connectivity"):
        api.compute_mesh_fingerprint(inconsistent)


def test_source_ids_require_explicit_complete_unique_namespace() -> None:
    api = _identity_api()

    validated = api.validate_source_ids(
        namespace="meshio:point-id",
        values=(101, 102, 103),
        expected_count=3,
    )
    assert validated.namespace == "meshio:point-id"
    assert validated.values == (101, 102, 103)
    without_source_ids = api.compute_mesh_fingerprint(_mesh())
    with_source_ids = api.compute_mesh_fingerprint(
        _mesh(),
        node_source_ids=validated,
    )
    assert with_source_ids.digest != without_source_ids.digest

    with pytest.raises(api.MeshIdentityError, match="namespace"):
        api.validate_source_ids(namespace="", values=(1, 2, 3), expected_count=3)
    with pytest.raises(api.MeshIdentityError, match="complete"):
        api.validate_source_ids(
            namespace="meshio:point-id",
            values=(1, 2),
            expected_count=3,
        )
    with pytest.raises(api.MeshIdentityError, match="unique"):
        api.validate_source_ids(
            namespace="meshio:point-id",
            values=(1, 1, 2),
            expected_count=3,
        )
