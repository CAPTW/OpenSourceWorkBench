"""Metadata helpers for persisted ResultDataset-to-mesh bindings."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from osw.core.project_schema import ResultRef

RESULT_MESH_BINDING_SCHEMA = "osw.result_mesh_binding.v1"
MESH_BINDING_METADATA_KEY = "mesh_binding"
SOURCE_MESH_REF_METADATA_KEY = "source_mesh_ref"
DEFAULT_ASSOCIATION_POLICY = "explicit_user_confirmed"
DEFAULT_BINDING_STATUS = "bound"
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
    field_id: str = ""
    association_policy: str = DEFAULT_ASSOCIATION_POLICY
    status: str = DEFAULT_BINDING_STATUS
    mesh_signature: ResultMeshSignature | Mapping[str, Any] | None = None
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "mesh_ref", str(self.mesh_ref))
        object.__setattr__(self, "result_dataset_id", str(self.result_dataset_id))
        object.__setattr__(self, "field_id", str(self.field_id))
        object.__setattr__(self, "association_policy", str(self.association_policy))
        object.__setattr__(self, "status", str(self.status))
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
            "schema": RESULT_MESH_BINDING_SCHEMA,
            "mesh_ref": self.mesh_ref,
            "result_dataset_id": self.result_dataset_id,
            "association_policy": self.association_policy,
            "status": self.status,
            "diagnostics": list(self.diagnostics),
        }
        if self.field_id:
            payload["field_id"] = self.field_id
        if self.mesh_signature.has_counts:
            payload["mesh_signature"] = self.mesh_signature.to_dict()
        return payload

    @classmethod
    def from_dict(cls, data: object) -> ResultMeshBinding:
        if not isinstance(data, Mapping):
            msg = "result mesh binding metadata must be a mapping."
            raise ValueError(msg)
        schema = str(data.get("schema", ""))
        if schema != RESULT_MESH_BINDING_SCHEMA:
            msg = (
                "result mesh binding metadata has unsupported schema "
                f"{schema!r}; expected {RESULT_MESH_BINDING_SCHEMA!r}."
            )
            raise ValueError(msg)
        return cls(
            mesh_ref=str(data.get("mesh_ref", "")),
            result_dataset_id=str(data.get("result_dataset_id", "")),
            field_id=str(data.get("field_id", "")),
            association_policy=str(
                data.get("association_policy", DEFAULT_ASSOCIATION_POLICY)
            ),
            status=str(data.get("status", DEFAULT_BINDING_STATUS)),
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
    proposal_metadata: Mapping[str, Any] | None = None,
    active_mesh_ref: str | None = None,
    require_field_id: bool = False,
    require_mesh_signature: bool = False,
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
        field_id=resolved_field_id,
        association_policy=association_policy,
        status=status,
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
