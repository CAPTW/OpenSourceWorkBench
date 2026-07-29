"""Metadata helpers for persisted ResultDataset-to-mesh bindings."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from osw.core.project_schema import ResultRef
from osw.mesh.identity import (
    MESH_IDENTITY_SCHEMA,
    MeshIdentityError,
    compute_mesh_fingerprint,
)
from osw.mesh.mesh_model import MeshData

RESULT_MESH_BINDING_SCHEMA_V1 = "osw.result_mesh_binding.v1"
RESULT_MESH_BINDING_SCHEMA_V2 = "osw.result_mesh_binding.v2"
# Compatibility name used by the original v1 bridge and its callers.
RESULT_MESH_BINDING_SCHEMA = RESULT_MESH_BINDING_SCHEMA_V1
MESH_BINDING_METADATA_KEY = "mesh_binding"
SOURCE_MESH_REF_METADATA_KEY = "source_mesh_ref"
DEFAULT_ASSOCIATION_POLICY = "explicit_user_confirmed"
DEFAULT_BINDING_STATUS = "bound"
_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
PROPOSAL_MESH_REF_METADATA_KEYS = (
    "mesh_ref",
    SOURCE_MESH_REF_METADATA_KEY,
    "source_mesh_id",
    "mesh_id",
    "workflow_item_id",
)


def _coerce_optional_count(value: object, *, field_name: str) -> int | None:
    if value is None:
        return None
    try:
        count = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        msg = f"{field_name} must be an integer count."
        raise ValueError(msg) from exc
    if count < 0:
        msg = f"{field_name} must not be negative."
        raise ValueError(msg)
    return count


def _coerce_diagnostics(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        msg = "diagnostics must be a sequence of messages."
        raise ValueError(msg)
    try:
        return tuple(str(diagnostic) for diagnostic in value)
    except TypeError as exc:
        msg = "diagnostics must be a sequence of messages."
        raise ValueError(msg) from exc


@dataclass(frozen=True)
class ResultMeshSignature:
    """Small optional mesh fingerprint stored with a result binding."""

    node_count: int | None = None
    cell_count: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "node_count",
            _coerce_optional_count(self.node_count, field_name="node_count"),
        )
        object.__setattr__(
            self,
            "cell_count",
            _coerce_optional_count(self.cell_count, field_name="cell_count"),
        )

    @property
    def has_counts(self) -> bool:
        return self.node_count is not None or self.cell_count is not None

    def to_dict(self) -> dict[str, int]:
        payload: dict[str, int] = {}
        if self.node_count is not None:
            payload["node_count"] = self.node_count
        if self.cell_count is not None:
            payload["cell_count"] = self.cell_count
        return payload

    @classmethod
    def from_dict(cls, data: object) -> ResultMeshSignature:
        if data is None:
            return cls()
        if not isinstance(data, Mapping):
            msg = "mesh_signature must be a mapping."
            raise ValueError(msg)
        return cls(
            node_count=data.get("node_count"),
            cell_count=data.get("cell_count"),
        )


@dataclass(frozen=True)
class ResultMeshBinding:
    """Persisted association between a result dataset field and a mesh ref."""

    mesh_ref: str
    result_dataset_id: str
    schema: str = RESULT_MESH_BINDING_SCHEMA_V1
    field_id: str = ""
    association_policy: str = DEFAULT_ASSOCIATION_POLICY
    status: str = DEFAULT_BINDING_STATUS
    mesh_identity_schema: str = ""
    mesh_fingerprint: str = ""
    mesh_signature: ResultMeshSignature | Mapping[str, Any] | None = None
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "mesh_ref", str(self.mesh_ref))
        object.__setattr__(self, "result_dataset_id", str(self.result_dataset_id))
        object.__setattr__(self, "schema", str(self.schema or ""))
        object.__setattr__(self, "field_id", str(self.field_id))
        object.__setattr__(self, "association_policy", str(self.association_policy))
        object.__setattr__(self, "status", str(self.status))
        object.__setattr__(
            self,
            "mesh_identity_schema",
            str(self.mesh_identity_schema or ""),
        )
        object.__setattr__(
            self,
            "mesh_fingerprint",
            str(self.mesh_fingerprint or "").lower(),
        )
        if isinstance(self.mesh_signature, ResultMeshSignature):
            signature = self.mesh_signature
        else:
            signature = ResultMeshSignature.from_dict(self.mesh_signature)
        object.__setattr__(self, "mesh_signature", signature)
        object.__setattr__(
            self,
            "diagnostics",
            _coerce_diagnostics(self.diagnostics),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": self.schema,
            "mesh_ref": self.mesh_ref,
            "result_dataset_id": self.result_dataset_id,
            "association_policy": self.association_policy,
            "status": self.status,
            "diagnostics": list(self.diagnostics),
        }
        if self.field_id:
            payload["field_id"] = self.field_id
        if self.schema == RESULT_MESH_BINDING_SCHEMA_V2:
            payload["mesh_identity_schema"] = self.mesh_identity_schema
            payload["mesh_fingerprint"] = self.mesh_fingerprint
        if self.mesh_signature.has_counts:
            payload["mesh_signature"] = self.mesh_signature.to_dict()
        return payload

    @classmethod
    def from_dict(cls, data: object) -> ResultMeshBinding:
        if not isinstance(data, Mapping):
            msg = "result mesh binding metadata must be a mapping."
            raise ValueError(msg)
        schema = str(data.get("schema", ""))
        if schema not in {
            RESULT_MESH_BINDING_SCHEMA_V1,
            RESULT_MESH_BINDING_SCHEMA_V2,
        }:
            msg = (
                "result mesh binding metadata has unsupported schema "
                f"{schema!r}; expected {RESULT_MESH_BINDING_SCHEMA_V1!r} "
                f"or {RESULT_MESH_BINDING_SCHEMA_V2!r}."
            )
            raise ValueError(msg)
        return cls(
            mesh_ref=str(data.get("mesh_ref", "")),
            result_dataset_id=str(data.get("result_dataset_id", "")),
            schema=schema,
            field_id=str(data.get("field_id", "")),
            association_policy=str(
                data.get("association_policy", DEFAULT_ASSOCIATION_POLICY)
            ),
            status=str(data.get("status", DEFAULT_BINDING_STATUS)),
            mesh_identity_schema=str(data.get("mesh_identity_schema", "")),
            mesh_fingerprint=str(data.get("mesh_fingerprint", "")),
            mesh_signature=ResultMeshSignature.from_dict(data.get("mesh_signature")),
            diagnostics=_coerce_diagnostics(data.get("diagnostics", ())),
        )


@dataclass(frozen=True)
class ResultMeshBindingCheck:
    """Diagnostic result for resolving persisted binding metadata."""

    binding: ResultMeshBinding | None
    valid: bool
    stale: bool
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResultMeshBindingBridgeResult:
    """Result of preparing a persisted binding without mutating project state."""

    result_ref: ResultRef
    binding: ResultMeshBinding | None
    valid: bool
    diagnostics: tuple[str, ...] = ()


class ResultMeshBindingResolutionState(StrEnum):
    """Current-state authority for applying an in-memory result field."""

    UNRESOLVED = "UNRESOLVED"
    RESOLVED = "RESOLVED"
    STALE = "STALE"
    INVALID = "INVALID"


@dataclass(frozen=True)
class ResultMeshBindingResolution:
    """Pure exact-mesh binding evidence with no backend-native state."""

    state: ResultMeshBindingResolutionState
    reason_code: str
    message: str
    binding: ResultMeshBinding | None = None
    active_mesh_fingerprint: str = ""
    transient_field: object | None = None
    diagnostics: tuple[str, ...] = ()


def result_ref_with_mesh_binding(
    result_ref: ResultRef,
    binding: ResultMeshBinding,
) -> ResultRef:
    """Return a ResultRef copy with additive mesh binding metadata."""

    metadata = dict(result_ref.metadata)
    metadata[MESH_BINDING_METADATA_KEY] = binding.to_dict()
    metadata[SOURCE_MESH_REF_METADATA_KEY] = binding.mesh_ref
    return ResultRef(
        id=result_ref.id,
        name=result_ref.name,
        path=result_ref.path,
        format=result_ref.format,
        run_id=result_ref.run_id,
        role=result_ref.role,
        kind=result_ref.kind,
        metadata=metadata,
    )


def bridge_result_dataset_mesh_binding(
    result_ref: ResultRef,
    *,
    result_dataset_id: str | None,
    mesh_ref: str | None = None,
    field_id: str | None = None,
    association_policy: str = DEFAULT_ASSOCIATION_POLICY,
    status: str = DEFAULT_BINDING_STATUS,
    node_count: int | None = None,
    cell_count: int | None = None,
    mesh_identity_schema: str = "",
    mesh_fingerprint: str = "",
    proposal_metadata: Mapping[str, Any] | None = None,
    active_mesh_ref: str | None = None,
    require_field_id: bool = False,
    require_mesh_signature: bool = False,
    require_mesh_fingerprint: bool = False,
) -> ResultMeshBindingBridgeResult:
    """Prepare a ResultRef copy with persisted mesh binding metadata.

    ``proposal_metadata`` is a read-only compatibility input, typically copied
    from an in-memory ResultDataset. The returned ResultRef is the only object
    carrying durable binding metadata; the input ResultRef, proposal metadata,
    and ResultDataset owner remain untouched.
    """

    errors: list[str] = []
    caveats: list[str] = []

    dataset_id = str(result_dataset_id or "").strip()
    if not dataset_id:
        errors.append("Result mesh binding is missing a result dataset id.")

    resolved_mesh_ref, proposal_diagnostics = _resolve_binding_mesh_ref(
        mesh_ref,
        proposal_metadata,
    )
    errors.extend(proposal_diagnostics)
    if not resolved_mesh_ref:
        errors.append(
            "Result mesh binding is missing a mesh ref; select a mesh before persisting."
        )

    resolved_field_id = str(field_id or "").strip()
    if require_field_id and not resolved_field_id:
        errors.append(
            "Result mesh binding is missing a field id; select a result field before persisting."
        )

    try:
        signature = ResultMeshSignature(node_count=node_count, cell_count=cell_count)
    except ValueError as exc:
        errors.append(f"Malformed mesh count signature: {exc}")
        signature = ResultMeshSignature()

    if not signature.has_counts:
        message = "Mesh count signature was not provided; stale detection is limited."
        if require_mesh_signature:
            errors.append(message)
        else:
            caveats.append(message)

    normalized_fingerprint = str(mesh_fingerprint or "").strip().lower()
    normalized_identity_schema = str(mesh_identity_schema or "").strip()
    if normalized_fingerprint:
        if not _DIGEST_PATTERN.fullmatch(normalized_fingerprint):
            errors.append(
                "Mesh fingerprint must be a lowercase 64-character SHA-256 digest."
            )
        if normalized_identity_schema != MESH_IDENTITY_SCHEMA:
            errors.append(
                "Mesh identity schema must be "
                f"{MESH_IDENTITY_SCHEMA!r} for a v2 result binding."
            )
    elif require_mesh_fingerprint:
        errors.append("Exact mesh fingerprint is required for a v2 result binding.")

    if errors:
        return ResultMeshBindingBridgeResult(
            result_ref=result_ref,
            binding=None,
            valid=False,
            diagnostics=tuple(errors + caveats),
        )

    binding = ResultMeshBinding(
        mesh_ref=resolved_mesh_ref,
        result_dataset_id=dataset_id,
        schema=(
            RESULT_MESH_BINDING_SCHEMA_V2
            if normalized_fingerprint
            else RESULT_MESH_BINDING_SCHEMA_V1
        ),
        field_id=resolved_field_id,
        association_policy=association_policy,
        status=status,
        mesh_identity_schema=normalized_identity_schema,
        mesh_fingerprint=normalized_fingerprint,
        mesh_signature=signature,
        diagnostics=tuple(caveats),
    )
    check = check_result_mesh_binding(
        binding,
        active_mesh_ref=active_mesh_ref,
        node_count=node_count,
        cell_count=cell_count,
    )
    if not check.valid:
        return ResultMeshBindingBridgeResult(
            result_ref=result_ref,
            binding=None,
            valid=False,
            diagnostics=tuple(check.diagnostics + tuple(caveats)),
        )

    return ResultMeshBindingBridgeResult(
        result_ref=result_ref_with_mesh_binding(result_ref, binding),
        binding=binding,
        valid=True,
        diagnostics=tuple(caveats),
    )


def result_mesh_binding_from_metadata(
    metadata: Mapping[str, Any] | None,
) -> ResultMeshBinding | None:
    binding, diagnostics = _binding_from_metadata(metadata)
    if diagnostics:
        return None
    return binding


def check_result_mesh_binding(
    binding_or_metadata: ResultMeshBinding | Mapping[str, Any] | None,
    *,
    active_mesh_ref: str | None = None,
    node_count: int | None = None,
    cell_count: int | None = None,
    active_mesh_fingerprint: str | None = None,
) -> ResultMeshBindingCheck:
    """Check persisted binding metadata against the active mesh identity/counts."""

    binding, diagnostics = _binding_from_input(binding_or_metadata)
    if diagnostics or binding is None:
        return ResultMeshBindingCheck(
            binding=None,
            valid=False,
            stale=False,
            diagnostics=diagnostics,
        )

    check_diagnostics: list[str] = []
    stale = False
    if binding.schema == RESULT_MESH_BINDING_SCHEMA_V2:
        if binding.mesh_identity_schema != MESH_IDENTITY_SCHEMA:
            check_diagnostics.append(
                "Result binding v2 has an unsupported schema for mesh identity."
            )
        if not _DIGEST_PATTERN.fullmatch(binding.mesh_fingerprint):
            check_diagnostics.append(
                "Result binding v2 requires a valid exact mesh fingerprint."
            )
        if check_diagnostics:
            return ResultMeshBindingCheck(
                binding=None,
                valid=False,
                stale=False,
                diagnostics=tuple(check_diagnostics),
            )
    if not binding.mesh_ref.strip():
        check_diagnostics.append(
            "Result mesh binding is missing a mesh ref; select a mesh before applying fields."
        )
    if not binding.result_dataset_id.strip():
        check_diagnostics.append(
            "Result mesh binding is missing a result dataset id."
        )

    if active_mesh_ref is not None:
        active_ref = str(active_mesh_ref).strip()
        if not active_ref:
            check_diagnostics.append(
                "Active mesh ref is required to resolve persisted result-mesh binding."
            )
        elif binding.mesh_ref.strip() and active_ref != binding.mesh_ref:
            stale = True
            check_diagnostics.append(
                "Persisted result mesh binding is stale: active mesh ref "
                f"{active_ref!r} does not match stored mesh ref {binding.mesh_ref!r}."
            )

    if (
        active_mesh_fingerprint is not None
        and binding.schema == RESULT_MESH_BINDING_SCHEMA_V2
    ):
        active_digest = str(active_mesh_fingerprint or "").strip().lower()
        if active_digest != binding.mesh_fingerprint:
            stale = True
            check_diagnostics.append(
                "Persisted result mesh binding is stale: active mesh fingerprint "
                "does not match the stored exact fingerprint."
            )

    if node_count is not None and binding.mesh_signature.node_count is not None:
        if node_count != binding.mesh_signature.node_count:
            stale = True
            check_diagnostics.append(
                "Persisted result mesh binding is stale: active mesh node count "
                f"{node_count} does not match stored node count "
                f"{binding.mesh_signature.node_count}."
            )
    if cell_count is not None and binding.mesh_signature.cell_count is not None:
        if cell_count != binding.mesh_signature.cell_count:
            stale = True
            check_diagnostics.append(
                "Persisted result mesh binding is stale: active mesh cell count "
                f"{cell_count} does not match stored cell count "
                f"{binding.mesh_signature.cell_count}."
            )

    return ResultMeshBindingCheck(
        binding=binding,
        valid=not check_diagnostics,
        stale=stale,
        diagnostics=tuple(check_diagnostics),
    )


def resolve_result_mesh_binding(
    binding_or_metadata: ResultMeshBinding | Mapping[str, Any] | None,
    *,
    active_mesh: MeshData | None,
    active_mesh_ref: str | None,
    result_dataset: object | None,
    field_name: str | None = None,
    association: str | None = None,
) -> ResultMeshBindingResolution:
    """Resolve a binding only when v2 exact mesh identity is current."""

    if active_mesh is None:
        return _resolution(
            ResultMeshBindingResolutionState.UNRESOLVED,
            "ACTIVE_MESH_NOT_LOADED",
            "An in-memory active mesh is required before applying result fields.",
        )
    if result_dataset is None:
        return _resolution(
            ResultMeshBindingResolutionState.UNRESOLVED,
            "RESULT_DATASET_NOT_AVAILABLE",
            "The bound ResultDataset is not currently available in memory.",
        )

    binding, diagnostics = _binding_from_input(binding_or_metadata)
    if binding is None:
        reason = _malformed_reason(binding_or_metadata)
        return _resolution(
            ResultMeshBindingResolutionState.INVALID,
            reason,
            diagnostics[0] if diagnostics else "Result mesh binding metadata is malformed.",
            diagnostics=diagnostics,
        )
    if binding.schema == RESULT_MESH_BINDING_SCHEMA_V1:
        return _resolution(
            ResultMeshBindingResolutionState.STALE,
            "LEGACY_BINDING_FINGERPRINT_UNVERIFIED",
            (
                "Legacy result binding v1 has no exact mesh fingerprint and "
                "must be explicitly reconfirmed."
            ),
            binding=binding,
        )
    if binding.mesh_identity_schema != MESH_IDENTITY_SCHEMA:
        return _resolution(
            ResultMeshBindingResolutionState.INVALID,
            "MALFORMED_BINDING_SCHEMA",
            "Result binding v2 has an unsupported mesh identity schema.",
            binding=binding,
        )
    if not _DIGEST_PATTERN.fullmatch(binding.mesh_fingerprint):
        return _resolution(
            ResultMeshBindingResolutionState.INVALID,
            "MISSING_MESH_FINGERPRINT",
            "Result binding v2 requires a valid exact mesh fingerprint.",
            binding=binding,
        )

    active_ref = str(active_mesh_ref or "").strip()
    if not active_ref:
        return _resolution(
            ResultMeshBindingResolutionState.UNRESOLVED,
            "ACTIVE_MESH_NOT_LOADED",
            "An active mesh reference is required before applying result fields.",
            binding=binding,
        )
    if binding.mesh_ref != active_ref:
        return _resolution(
            ResultMeshBindingResolutionState.STALE,
            "MESH_REF_MISMATCH",
            "The active mesh reference does not match the result binding.",
            binding=binding,
        )

    dataset_id = str(getattr(result_dataset, "dataset_id", "") or "")
    if not dataset_id:
        return _resolution(
            ResultMeshBindingResolutionState.INVALID,
            "RESULT_DATASET_NOT_AVAILABLE",
            "The in-memory ResultDataset has no stable dataset ID.",
            binding=binding,
        )
    if binding.result_dataset_id != dataset_id:
        return _resolution(
            ResultMeshBindingResolutionState.INVALID,
            "RESULT_DATASET_ID_MISMATCH",
            "The in-memory ResultDataset ID does not match the result binding.",
            binding=binding,
        )

    try:
        fingerprint = compute_mesh_fingerprint(active_mesh)
    except (MeshIdentityError, TypeError, ValueError) as exc:
        return _resolution(
            ResultMeshBindingResolutionState.INVALID,
            "MISSING_MESH_FINGERPRINT",
            f"The active mesh fingerprint could not be computed: {exc}",
            binding=binding,
        )
    if fingerprint.digest != binding.mesh_fingerprint:
        return _resolution(
            ResultMeshBindingResolutionState.STALE,
            "MESH_FINGERPRINT_MISMATCH",
            "The active mesh geometry or topology differs from the result binding.",
            binding=binding,
            active_mesh_fingerprint=fingerprint.digest,
            diagnostics=_count_diagnostics(binding, active_mesh),
        )

    requested_field = str(field_name or binding.field_id or "").strip()
    field = _result_field(result_dataset, requested_field)
    if requested_field and field is None:
        return _resolution(
            ResultMeshBindingResolutionState.INVALID,
            "RESULT_FIELD_NOT_FOUND",
            f"Result field {requested_field!r} is not available in the bound dataset.",
            binding=binding,
            active_mesh_fingerprint=fingerprint.digest,
        )
    if association is not None and field is not None:
        requested_association = _normalize_association(association)
        field_association = _normalize_association(
            str(getattr(field, "location", ""))
        )
        if (
            not requested_association
            or field_association != requested_association
        ):
            return _resolution(
                ResultMeshBindingResolutionState.INVALID,
                "ASSOCIATION_MISMATCH",
                "The requested point/cell association does not match the result field.",
                binding=binding,
                active_mesh_fingerprint=fingerprint.digest,
            )

    return _resolution(
        ResultMeshBindingResolutionState.RESOLVED,
        "EXACT_MESH_FINGERPRINT_MATCH",
        "Result binding v2 matches the exact active mesh fingerprint.",
        binding=binding,
        active_mesh_fingerprint=fingerprint.digest,
        transient_field=field,
        diagnostics=_count_diagnostics(binding, active_mesh),
    )


def _resolution(
    state: ResultMeshBindingResolutionState,
    reason_code: str,
    message: str,
    *,
    binding: ResultMeshBinding | None = None,
    active_mesh_fingerprint: str = "",
    transient_field: object | None = None,
    diagnostics: tuple[str, ...] = (),
) -> ResultMeshBindingResolution:
    return ResultMeshBindingResolution(
        state=state,
        reason_code=reason_code,
        message=message,
        binding=binding,
        active_mesh_fingerprint=active_mesh_fingerprint,
        transient_field=transient_field,
        diagnostics=tuple(diagnostics),
    )


def _malformed_reason(
    binding_or_metadata: ResultMeshBinding | Mapping[str, Any] | None,
) -> str:
    payload: object = binding_or_metadata
    if isinstance(payload, Mapping) and "schema" not in payload:
        payload = payload.get(MESH_BINDING_METADATA_KEY)
    if isinstance(payload, Mapping):
        schema = str(payload.get("schema", ""))
        if schema == RESULT_MESH_BINDING_SCHEMA_V2 and not str(
            payload.get("mesh_fingerprint", "")
        ).strip():
            return "MISSING_MESH_FINGERPRINT"
    return "MALFORMED_BINDING_SCHEMA"


def _result_field(result_dataset: object, name: str) -> object | None:
    if not name:
        return None
    return next(
        (
            field
            for field in getattr(result_dataset, "fields", ()) or ()
            if str(getattr(field, "name", "")) == name
        ),
        None,
    )


def _normalize_association(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"point", "node", "vertex"}:
        return "point"
    if normalized in {"cell", "element"}:
        return "cell"
    return ""


def _count_diagnostics(
    binding: ResultMeshBinding,
    active_mesh: MeshData,
) -> tuple[str, ...]:
    diagnostics: list[str] = []
    node_count = len(active_mesh.points)
    cell_count = sum(block.count for block in active_mesh.cells)
    if (
        binding.mesh_signature.node_count is not None
        and binding.mesh_signature.node_count != node_count
    ):
        diagnostics.append(
            "Diagnostic node count differs from the persisted result binding."
        )
    if (
        binding.mesh_signature.cell_count is not None
        and binding.mesh_signature.cell_count != cell_count
    ):
        diagnostics.append(
            "Diagnostic cell count differs from the persisted result binding."
        )
    return tuple(diagnostics)


def _binding_from_input(
    binding_or_metadata: ResultMeshBinding | Mapping[str, Any] | None,
) -> tuple[ResultMeshBinding | None, tuple[str, ...]]:
    if isinstance(binding_or_metadata, ResultMeshBinding):
        return binding_or_metadata, ()
    if isinstance(binding_or_metadata, Mapping) and "schema" in binding_or_metadata:
        try:
            return ResultMeshBinding.from_dict(binding_or_metadata), ()
        except (TypeError, ValueError) as exc:
            return None, (f"Malformed result mesh binding metadata: {exc}",)
    return _binding_from_metadata(binding_or_metadata)


def _binding_from_metadata(
    metadata: Mapping[str, Any] | None,
) -> tuple[ResultMeshBinding | None, tuple[str, ...]]:
    if metadata is None:
        return None, ("Result metadata does not include a mesh binding.",)
    if not isinstance(metadata, Mapping):
        return None, ("Malformed result metadata: expected a mapping.",)
    payload = metadata.get(MESH_BINDING_METADATA_KEY)
    if payload is None:
        return None, ("Result metadata does not include a mesh binding.",)
    if not isinstance(payload, Mapping):
        return None, ("Malformed result mesh binding metadata: expected a mapping.",)
    try:
        return ResultMeshBinding.from_dict(payload), ()
    except (TypeError, ValueError) as exc:
        return None, (f"Malformed result mesh binding metadata: {exc}",)


def _resolve_binding_mesh_ref(
    mesh_ref: str | None,
    proposal_metadata: Mapping[str, Any] | None,
) -> tuple[str, tuple[str, ...]]:
    explicit_ref = str(mesh_ref or "").strip()
    proposal_refs, diagnostics = _proposal_mesh_refs(proposal_metadata)
    if diagnostics:
        return explicit_ref, diagnostics
    if len(proposal_refs) > 1:
        refs = ", ".join(repr(item) for item in proposal_refs)
        return explicit_ref, (
            "Ambiguous ResultDataset proposal metadata contains multiple mesh refs: "
            f"{refs}.",
        )
    if proposal_refs:
        proposal_ref = proposal_refs[0]
        if explicit_ref and explicit_ref != proposal_ref:
            return explicit_ref, (
                "ResultDataset proposal metadata mesh ref "
                f"{proposal_ref!r} does not match explicit mesh ref {explicit_ref!r}.",
            )
        return proposal_ref, ()
    return explicit_ref, ()


def _proposal_mesh_refs(
    proposal_metadata: Mapping[str, Any] | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if proposal_metadata is None:
        return (), ()
    if not isinstance(proposal_metadata, Mapping):
        return (), ("Malformed ResultDataset proposal metadata: expected a mapping.",)

    refs: list[str] = []
    seen: set[str] = set()
    for key in PROPOSAL_MESH_REF_METADATA_KEYS:
        if key not in proposal_metadata:
            continue
        value = proposal_metadata.get(key)
        values = value if isinstance(value, (list, tuple, set, frozenset)) else (value,)
        for item in values:
            text = str(item or "").strip()
            if text and text not in seen:
                seen.add(text)
                refs.append(text)
    return tuple(refs), ()
