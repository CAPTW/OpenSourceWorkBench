"""Lightweight structural checks for experimental FEASpec data."""

from __future__ import annotations

from collections import Counter, deque
from collections.abc import Iterable, Mapping
from typing import Any

from .models import Diagnostic

REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "spec_type",
    "source",
    "problem_type",
    "units",
    "geometry",
    "materials",
    "sections",
    "boundary_conditions",
    "loads",
    "dimensions",
    "assumptions",
    "evidence",
    "confidence",
    "diagnostics",
    "validation",
    "solver_compatibility",
}
VALID_SPEC_TYPES = {"candidate", "approved"}
VALID_VALIDATION_STATES = {"unchecked", "invalid", "valid-with-warnings", "approved", "rejected"}


def check_feaspec_dict(data: object) -> list[Diagnostic]:
    """Return structural diagnostics for FEASpec-style dictionaries.

    These checks are intentionally shallow and deterministic. They do not
    perform physical validation, mesh generation, solver compatibility analysis,
    ProjectSchema conversion, or solver execution.
    """

    if not isinstance(data, Mapping):
        return [Diagnostic.error("invalid_document", "FEASpec document must be a mapping.")]

    diagnostics: list[Diagnostic] = []
    _check_required_fields(data, diagnostics)
    _check_spec_type_and_validation(data, diagnostics)
    _check_units(data, diagnostics)
    graph = _geometry_graph(data)
    known_targets = _check_geometry_graph(graph, diagnostics)
    _check_target_refs(data, known_targets, diagnostics)
    _check_quantity_units(data, diagnostics)
    _check_expected_diagnostics(data, diagnostics)
    return diagnostics


def _check_required_fields(data: Mapping[str, Any], diagnostics: list[Diagnostic]) -> None:
    for field_name in sorted(REQUIRED_TOP_LEVEL_FIELDS - set(data)):
        diagnostics.append(
            Diagnostic.error(
                "missing_required_field",
                f"Required FEASpec field {field_name!r} is missing.",
                path=field_name,
            )
        )


def _check_spec_type_and_validation(
    data: Mapping[str, Any], diagnostics: list[Diagnostic]
) -> None:
    spec_type = str(data.get("spec_type", ""))
    if spec_type and spec_type not in VALID_SPEC_TYPES:
        diagnostics.append(
            Diagnostic.error(
                "invalid_spec_type",
                f"Unsupported FEASpec spec_type {spec_type!r}.",
                path="spec_type",
            )
        )

    validation = data.get("validation")
    validation_state = ""
    if isinstance(validation, Mapping):
        validation_state = str(validation.get("state", ""))
        if validation_state and validation_state not in VALID_VALIDATION_STATES:
            diagnostics.append(
                Diagnostic.error(
                    "invalid_validation_state",
                    f"Unsupported FEASpec validation state {validation_state!r}.",
                    path="validation.state",
                )
            )
    elif "validation" in data:
        diagnostics.append(
            Diagnostic.error(
                "invalid_validation",
                "validation must be a mapping.",
                path="validation",
            )
        )

    if spec_type == "approved":
        if not isinstance(data.get("human_review"), Mapping):
            diagnostics.append(
                Diagnostic.error(
                    "missing_human_review",
                    "Approved FEASpec requires a human_review block.",
                    path="human_review",
                )
            )
        if validation_state != "approved":
            diagnostics.append(
                Diagnostic.error(
                    "approved_requires_approved_state",
                    "Approved FEASpec requires validation.state == 'approved'.",
                    path="validation.state",
                )
            )
    elif spec_type == "candidate" and validation_state == "approved":
        diagnostics.append(
            Diagnostic.error(
                "candidate_cannot_be_approved",
                "FEASpecCandidate must not be marked approved for solver handoff.",
                path="validation.state",
            )
        )


def _check_units(data: Mapping[str, Any], diagnostics: list[Diagnostic]) -> None:
    units = data.get("units")
    if not isinstance(units, Mapping):
        diagnostics.append(
            Diagnostic.error("missing_units", "units must be present.", path="units")
        )
        return
    for field_name in ("system", "length"):
        if not str(units.get(field_name, "")).strip():
            diagnostics.append(
                Diagnostic.error(
                    "missing_units",
                    f"units.{field_name} is required.",
                    path=f"units.{field_name}",
                )
            )
    if not any(str(units.get(name, "")).strip() for name in ("force", "stress", "mass")):
        diagnostics.append(
            Diagnostic.error(
                "missing_units",
                "At least one physical default unit beyond length is required.",
                path="units",
            )
        )


def _geometry_graph(data: Mapping[str, Any]) -> Mapping[str, Any]:
    geometry = data.get("geometry")
    if not isinstance(geometry, Mapping):
        return {}
    graph = geometry.get("geometry_graph")
    return graph if isinstance(graph, Mapping) else {}


def _check_geometry_graph(
    graph: Mapping[str, Any], diagnostics: list[Diagnostic]
) -> set[str]:
    if not graph:
        diagnostics.append(
            Diagnostic.error(
                "missing_geometry_graph",
                "geometry.geometry_graph is required.",
                path="geometry.geometry_graph",
            )
        )
        return set()

    nodes = _mapping_items(graph.get("nodes", ()))
    edges = _mapping_items(graph.get("edges", ()))
    regions = _mapping_items(graph.get("regions", ()))
    node_ids = _ids(nodes)
    edge_ids = _ids(edges)
    region_ids = _ids(regions)
    _check_duplicate_ids("geometry.nodes", node_ids, diagnostics)
    _check_duplicate_ids("geometry.edges", edge_ids, diagnostics)
    _check_duplicate_ids("geometry.regions", region_ids, diagnostics)
    all_ids = node_ids + edge_ids + region_ids
    _check_duplicate_ids("geometry", all_ids, diagnostics)

    known_node_ids = set(node_ids)
    for edge in edges:
        edge_id = str(edge.get("id", ""))
        node_refs = [str(ref) for ref in _as_list(edge.get("node_refs", ()))]
        for node_ref in node_refs:
            if node_ref not in known_node_ids:
                diagnostics.append(
                    Diagnostic.error(
                        "invalid_edge_endpoint",
                        f"Edge {edge_id!r} references unknown node {node_ref!r}.",
                        path="geometry.geometry_graph.edges",
                        target_refs=[edge_id, node_ref],
                    )
                )
    _check_graph_connectivity(nodes, edges, regions, diagnostics)
    return set(all_ids)


def _check_duplicate_ids(path: str, ids: list[str], diagnostics: list[Diagnostic]) -> None:
    for duplicate_id, count in Counter(item for item in ids if item).items():
        if count > 1:
            diagnostics.append(
                Diagnostic.error(
                    "duplicate_geometry_id",
                    f"Geometry id {duplicate_id!r} is repeated.",
                    path=path,
                    target_refs=[duplicate_id],
                )
            )


def _check_graph_connectivity(
    nodes: list[Mapping[str, Any]],
    edges: list[Mapping[str, Any]],
    regions: list[Mapping[str, Any]],
    diagnostics: list[Diagnostic],
) -> None:
    node_ids = [str(node.get("id", "")) for node in nodes if str(node.get("id", ""))]
    if len(node_ids) <= 1 or not edges:
        return
    adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    edge_nodes: dict[str, list[str]] = {}
    for edge in edges:
        edge_id = str(edge.get("id", ""))
        refs = [str(ref) for ref in _as_list(edge.get("node_refs", ()))]
        edge_nodes[edge_id] = refs
        if len(refs) < 2:
            continue
        first = refs[0]
        for other in refs[1:]:
            if first in adjacency and other in adjacency:
                adjacency[first].add(other)
                adjacency[other].add(first)

    for region in regions:
        _connect_refs(region, adjacency, edge_nodes)

    start = node_ids[0]
    visited = {start}
    queue: deque[str] = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current] - visited:
            visited.add(neighbor)
            queue.append(neighbor)
    missing = sorted(set(node_ids) - visited)
    if missing:
        diagnostics.append(
            Diagnostic.error(
                "disconnected_graph",
                "Geometry graph contains disconnected node components.",
                path="geometry.geometry_graph",
                target_refs=missing,
            )
        )


def _check_target_refs(
    data: Mapping[str, Any], known_targets: set[str], diagnostics: list[Diagnostic]
) -> None:
    for section_name, code in (
        ("boundary_conditions", "invalid_boundary_condition_target"),
        ("loads", "invalid_load_target"),
    ):
        for item in _mapping_items(data.get(section_name, ())):
            item_id = str(item.get("id", ""))
            for target_ref in [str(ref) for ref in _as_list(item.get("target_refs", ()))]:
                if target_ref and target_ref not in known_targets:
                    diagnostics.append(
                        Diagnostic.error(
                            code,
                            (
                                f"{section_name} item {item_id!r} references "
                                f"unknown target {target_ref!r}."
                            ),
                            path=f"{section_name}.target_refs",
                            target_refs=[item_id, target_ref],
                        )
                    )


def _check_quantity_units(data: Mapping[str, Any], diagnostics: list[Diagnostic]) -> None:
    for section_name in ("materials", "sections", "loads", "dimensions"):
        section = data.get(section_name, ())
        _check_nested_quantity_units(section, diagnostics, path=section_name)


def _check_nested_quantity_units(
    value: object, diagnostics: list[Diagnostic], *, path: str
) -> None:
    if isinstance(value, Mapping):
        if "value" in value and "units" not in value:
            diagnostics.append(
                Diagnostic.error(
                    "missing_units",
                    "Quantity value is missing units.",
                    path=path,
                    target_refs=[str(value.get("id", ""))] if value.get("id") else (),
                )
            )
        for key, item in value.items():
            _check_nested_quantity_units(item, diagnostics, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_nested_quantity_units(item, diagnostics, path=f"{path}[{index}]")


def _check_expected_diagnostics(
    data: Mapping[str, Any], diagnostics: list[Diagnostic]
) -> None:
    expected = {str(item) for item in _as_list(data.get("expected_diagnostics", ()))}
    if not expected:
        return
    found = {diagnostic.code for diagnostic in diagnostics}
    documented = {
        str(item.get("code", ""))
        for item in _mapping_items(data.get("diagnostics", ()))
        if str(item.get("code", ""))
    }
    for missing in sorted(expected - found - documented):
        diagnostics.append(
            Diagnostic.error(
                "missing_expected_diagnostic",
                f"Expected diagnostic {missing!r} was not produced by basic checks.",
                path="expected_diagnostics",
                target_refs=[missing],
            )
        )


def _mapping_items(value: object) -> list[Mapping[str, Any]]:
    return [item for item in _as_list(value) if isinstance(item, Mapping)]


def _ids(items: Iterable[Mapping[str, Any]]) -> list[str]:
    return [str(item.get("id", "")) for item in items]


def _as_list(value: object) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    return []


def _connect_refs(
    region: Mapping[str, Any],
    adjacency: dict[str, set[str]],
    edge_nodes: Mapping[str, list[str]],
) -> None:
    edge_refs = []
    for key in ("boundary_refs", "boundary_edge_refs", "void_edge_refs"):
        edge_refs.extend(str(ref) for ref in _as_list(region.get(key, ())))
    connected_nodes: list[str] = []
    for edge_ref in edge_refs:
        connected_nodes.extend(ref for ref in edge_nodes.get(edge_ref, ()) if ref in adjacency)
    if len(connected_nodes) < 2:
        return
    first = connected_nodes[0]
    for other in connected_nodes[1:]:
        adjacency[first].add(other)
        adjacency[other].add(first)
