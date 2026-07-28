"""Pure deterministic identity for in-memory OSW meshes.

The fingerprint deliberately covers only canonical mesh topology/geometry and
validated source IDs.  Paths, display metadata, result arrays, quality data,
renderer state, and current selections are outside the identity domain.
"""

from __future__ import annotations

import hashlib
import math
import struct
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .mesh_model import MeshData

MESH_IDENTITY_SCHEMA = "osw.mesh_identity.v1"
MESH_IDENTITY_ALGORITHM = "sha256"
DEFAULT_COORDINATE_BASIS = "unspecified"


class MeshIdentityError(ValueError):
    """Canonical mesh identity could not be computed safely."""


@dataclass(frozen=True)
class ValidatedSourceIds:
    """Complete, unique source IDs in one explicit namespace."""

    namespace: str
    values: tuple[int | str, ...]


@dataclass(frozen=True)
class MeshFingerprint:
    """Stable summary of one exact canonical mesh ordering."""

    schema: str
    algorithm: str
    digest: str
    point_count: int
    cell_count: int
    coordinate_basis: str = DEFAULT_COORDINATE_BASIS

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "algorithm": self.algorithm,
            "digest": self.digest,
            "point_count": self.point_count,
            "cell_count": self.cell_count,
            "coordinate_basis": self.coordinate_basis,
        }

    @classmethod
    def from_dict(cls, data: object) -> MeshFingerprint:
        if not isinstance(data, Mapping):
            raise MeshIdentityError("Mesh fingerprint data must be a mapping.")
        return cls(
            schema=str(data.get("schema", "")),
            algorithm=str(data.get("algorithm", "")),
            digest=str(data.get("digest", "")),
            point_count=int(data.get("point_count", 0)),
            cell_count=int(data.get("cell_count", 0)),
            coordinate_basis=str(
                data.get("coordinate_basis", DEFAULT_COORDINATE_BASIS)
            ),
        )


class _CanonicalWriter:
    """Small length-delimited canonical byte writer."""

    def __init__(self) -> None:
        self._parts: list[bytes] = []

    def field(self, tag: str, payload: bytes) -> None:
        tag_bytes = tag.encode("utf-8")
        self._parts.extend(
            (
                struct.pack("<Q", len(tag_bytes)),
                tag_bytes,
                struct.pack("<Q", len(payload)),
                payload,
            )
        )

    def text(self, tag: str, value: str) -> None:
        self.field(tag, value.encode("utf-8"))

    def uint(self, tag: str, value: int) -> None:
        self.field(tag, _encode_uint(value))

    def float64(self, tag: str, value: float) -> None:
        number = float(value)
        if not math.isfinite(number):
            raise MeshIdentityError("Mesh coordinates must be finite float64 values.")
        if number == 0.0:
            number = 0.0
        self.field(tag, struct.pack("<d", number))

    def bytes(self) -> bytes:
        return b"".join(self._parts)


def validate_source_ids(
    *,
    namespace: str,
    values: Sequence[int | str],
    expected_count: int,
) -> ValidatedSourceIds:
    """Validate explicit source IDs before they can affect identity."""

    normalized_namespace = str(namespace or "").strip()
    if not normalized_namespace:
        raise MeshIdentityError("Source-ID namespace must be explicit.")
    normalized_values = tuple(_normalize_source_id(value) for value in values)
    if len(normalized_values) != int(expected_count):
        raise MeshIdentityError(
            "Source IDs must be complete for the represented domain."
        )
    if len(set(normalized_values)) != len(normalized_values):
        raise MeshIdentityError("Source IDs must be unique within their namespace.")
    return ValidatedSourceIds(
        namespace=normalized_namespace,
        values=normalized_values,
    )


def compute_mesh_fingerprint(
    mesh: MeshData,
    *,
    coordinate_basis: str = DEFAULT_COORDINATE_BASIS,
    node_source_ids: ValidatedSourceIds | None = None,
    cell_source_ids: Mapping[int, ValidatedSourceIds] | None = None,
) -> MeshFingerprint:
    """Hash one exact mesh ordering using ``osw.mesh_identity.v1``."""

    if not isinstance(mesh, MeshData):
        raise MeshIdentityError("Mesh identity requires an in-memory MeshData.")
    basis = str(coordinate_basis or DEFAULT_COORDINATE_BASIS).strip()
    if not basis:
        basis = DEFAULT_COORDINATE_BASIS

    writer = _CanonicalWriter()
    writer.text("identity_schema", MESH_IDENTITY_SCHEMA)
    writer.text("coordinate_basis", basis)
    writer.uint("point_count", len(mesh.points))
    for point_ordinal, point in enumerate(mesh.points):
        if len(point) != 3:
            raise MeshIdentityError("Every mesh point must have exactly three coordinates.")
        writer.uint("point_ordinal", point_ordinal)
        for axis, coordinate in zip(("x", "y", "z"), point, strict=True):
            writer.float64(f"coordinate_{axis}", coordinate)

    if node_source_ids is not None:
        _write_source_ids(
            writer,
            "node_source_ids",
            _require_validated_source_ids(
                node_source_ids,
                expected_count=len(mesh.points),
            ),
        )

    writer.uint("cell_block_count", len(mesh.cells))
    total_cells = 0
    normalized_cell_source_ids = dict(cell_source_ids or {})
    unexpected_source_blocks = set(normalized_cell_source_ids) - set(
        range(len(mesh.cells))
    )
    if unexpected_source_blocks:
        raise MeshIdentityError("Cell source IDs reference an unknown cell block.")

    for block_ordinal, block in enumerate(mesh.cells):
        cell_type = str(block.cell_type or "").strip().lower()
        if not cell_type:
            raise MeshIdentityError("Every cell block requires a canonical cell type.")
        if block.count != len(block.data):
            raise MeshIdentityError(
                "Cell block count requires complete ordered connectivity."
            )
        writer.uint("cell_block_ordinal", block_ordinal)
        writer.text("cell_type", cell_type)
        writer.uint("cell_count", block.count)
        total_cells += block.count
        for local_ordinal, connectivity in enumerate(block.data):
            writer.uint("cell_local_ordinal", local_ordinal)
            writer.uint("connectivity_length", len(connectivity))
            for point_index in connectivity:
                normalized_index = int(point_index)
                if normalized_index < 0:
                    raise MeshIdentityError(
                        "Mesh connectivity indices must be non-negative."
                    )
                if normalized_index >= len(mesh.points):
                    raise MeshIdentityError(
                        "Mesh connectivity index is outside the point domain."
                    )
                writer.uint("connectivity_index", normalized_index)

        source_ids = normalized_cell_source_ids.get(block_ordinal)
        if source_ids is not None:
            _write_source_ids(
                writer,
                "cell_source_ids",
                _require_validated_source_ids(
                    source_ids,
                    expected_count=block.count,
                ),
            )

    digest = hashlib.sha256(writer.bytes()).hexdigest()
    return MeshFingerprint(
        schema=MESH_IDENTITY_SCHEMA,
        algorithm=MESH_IDENTITY_ALGORITHM,
        digest=digest,
        point_count=len(mesh.points),
        cell_count=total_cells,
        coordinate_basis=basis,
    )


def _require_validated_source_ids(
    source_ids: ValidatedSourceIds,
    *,
    expected_count: int,
) -> ValidatedSourceIds:
    if not isinstance(source_ids, ValidatedSourceIds):
        raise MeshIdentityError(
            "Source IDs must be validated before inclusion in mesh identity."
        )
    return validate_source_ids(
        namespace=source_ids.namespace,
        values=source_ids.values,
        expected_count=expected_count,
    )


def _write_source_ids(
    writer: _CanonicalWriter,
    tag: str,
    source_ids: ValidatedSourceIds,
) -> None:
    writer.text(f"{tag}_namespace", source_ids.namespace)
    writer.uint(f"{tag}_count", len(source_ids.values))
    for value in source_ids.values:
        if isinstance(value, int):
            writer.text(f"{tag}_value_type", "int")
            writer.uint(f"{tag}_value", value)
        else:
            writer.text(f"{tag}_value_type", "str")
            writer.text(f"{tag}_value", value)


def _normalize_source_id(value: object) -> int | str:
    if isinstance(value, bool):
        raise MeshIdentityError("Boolean source IDs are not valid entity IDs.")
    if isinstance(value, int):
        if value < 0:
            raise MeshIdentityError("Integer source IDs must be non-negative.")
        return value
    text = str(value)
    if not text:
        raise MeshIdentityError("Source IDs must not be empty.")
    return text


def _encode_uint(value: int) -> bytes:
    normalized = int(value)
    if normalized < 0:
        raise MeshIdentityError("Canonical integers must be non-negative.")
    byte_length = max(1, (normalized.bit_length() + 7) // 8)
    return normalized.to_bytes(byte_length, byteorder="little", signed=False)


__all__ = [
    "DEFAULT_COORDINATE_BASIS",
    "MESH_IDENTITY_ALGORITHM",
    "MESH_IDENTITY_SCHEMA",
    "MeshFingerprint",
    "MeshIdentityError",
    "ValidatedSourceIds",
    "compute_mesh_fingerprint",
    "validate_source_ids",
]
