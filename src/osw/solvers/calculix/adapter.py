"""SolverAdapterPlugin wrapper and ProjectSchema bridge for CalculiX decks."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from osw.core.materials import IsotropicElastic, Material
from osw.core.project_schema import Project
from osw.core.solver_setup import (
    SetupRecordKind,
    iter_solver_setup_records,
)
from osw.core.solver_setup_handoff import build_solver_setup_handoff
from osw.core.units import Quantity
from osw.core.validation import ValidationReport
from osw.mesh.mesh_model import MeshCellBlock, MeshData, MeshModel
from osw.plugins.base import SolverAdapterPlugin
from osw.plugins.manifest import PluginManifest

from .errors import CalculiXProjectMappingError
from .input_deck import (
    CalculixBoundaryCondition,
    CalculixInputDeckGenerator,
    CalculixLinearStaticCase,
    CalculixLoad,
    CalculixNodeSet,
    CalculixSurface,
    deck_result_from_case,
)
from .model import CalculiXDeckResult


@dataclass(frozen=True)
class CalculiXSolverSetupPreparation:
    """In-memory, prepare-only handoff with no path, command, or native handle."""

    eligible: bool
    execution_mode: str
    source_project_name: str
    mesh_ref: str
    mesh_fingerprint: str
    record_ids: tuple[str, ...]
    element_sets: tuple[tuple[str, tuple[int, ...]], ...]
    node_sets: tuple[tuple[str, tuple[int, ...]], ...]
    diagnostics: tuple[str, ...]
    input_preview: str


def prepare_solver_setup(
    project: Project,
    *,
    mesh: MeshData,
    mesh_ref: str,
) -> CalculiXSolverSetupPreparation:
    """Consume the normalized zero-based handoff at a one-based adapter boundary."""

    handoff = build_solver_setup_handoff(
        project,
        mesh=mesh,
        mesh_ref=mesh_ref,
        adapter_id="osw.solvers.calculix.linear_static",
        supported_kinds=(
            SetupRecordKind.MATERIAL_REGION,
            SetupRecordKind.FIXED_SUPPORT,
            SetupRecordKind.PRESCRIBED_DISPLACEMENT,
            SetupRecordKind.FORCE,
        ),
        strict=True,
    )
    setup = project.primary_physics
    if setup is None:
        return _setup_preparation_error(
            project,
            mesh_ref,
            handoff.mesh_fingerprint,
            tuple(item.reason_code for item in handoff.diagnostics),
        )
    records = iter_solver_setup_records(setup)
    blockers = [
        (f"{item.setup_id}:{item.reason_code}" if item.setup_id else item.reason_code)
        for item in handoff.diagnostics
    ]
    names = [_setup_set_name(record) for record in records if record.enabled]
    if len(names) != len(set(names)):
        blockers.append("NORMALIZED_SET_NAME_COLLISION")
    for normalized in handoff.records:
        if normalized.setup_kind is not SetupRecordKind.MATERIAL_REGION:
            continue
        if any(
            _mesh_cell_type(mesh, index) != "tetra" for index in normalized.resolved_entity_indices
        ):
            blockers.append(f"{normalized.setup_id}:UNSUPPORTED_MATERIAL_CELL_TOPOLOGY")
    material_by_id = {item.material_id: item for item in project.materials}
    material_signatures: dict[str, tuple[str, float, str, float]] = {}
    for record in setup.material_assignment_records:
        material = material_by_id.get(record.material_id)
        if not record.enabled:
            continue
        if material is None or material.elastic is None:
            blockers.append(f"{record.id}:UNSUPPORTED_MATERIAL")
            continue
        modulus = material.elastic.young_modulus
        poisson_ratio = material.elastic.poisson_ratio
        if (
            not math.isfinite(modulus.value)
            or modulus.value <= 0.0
            or not math.isfinite(poisson_ratio)
            or not -1.0 < poisson_ratio < 0.5
        ):
            blockers.append(f"{record.id}:INVALID_MATERIAL_ELASTICITY")
            continue
        if modulus.unit != project.units.stress:
            blockers.append(f"{record.id}:MATERIAL_STRESS_UNIT_MISMATCH")
            continue
        if modulus.unit != "Pa":
            blockers.append(f"{record.id}:UNSUPPORTED_MATERIAL_STRESS_UNIT")
            continue
        material_name = _normalized_setup_name(material.name)
        signature = (
            material.material_id,
            modulus.value,
            modulus.unit,
            poisson_ratio,
        )
        existing = material_signatures.get(material_name)
        if existing is not None and existing != signature:
            if "NORMALIZED_MATERIAL_NAME_COLLISION" not in blockers:
                blockers.append("NORMALIZED_MATERIAL_NAME_COLLISION")
            continue
        material_signatures[material_name] = signature
    if blockers:
        return _setup_preparation_error(
            project,
            mesh_ref,
            handoff.mesh_fingerprint,
            tuple(blockers),
        )

    element_sets: list[tuple[str, tuple[int, ...]]] = []
    node_sets: list[tuple[str, tuple[int, ...]]] = []
    fragments: list[str] = []
    emitted_materials: set[tuple[str, str, float, str, float]] = set()
    record_by_id = {str(record.id): record for record in records}
    for normalized in handoff.records:
        record = record_by_id[normalized.setup_id]
        set_name = _setup_set_name(record)
        entity_ids = tuple(index + 1 for index in normalized.resolved_entity_indices)
        parameters = normalized.parameters_in_project_canonical_units
        if normalized.setup_kind is SetupRecordKind.MATERIAL_REGION:
            element_sets.append((set_name, entity_ids))
            material = material_by_id[normalized.material_ref_if_applicable]
            material_name = _normalized_setup_name(material.name)
            elastic = material.elastic
            assert elastic is not None
            material_signature = (
                material_name,
                material.material_id,
                elastic.young_modulus.value,
                elastic.young_modulus.unit,
                elastic.poisson_ratio,
            )
            fragments.append(f"*ELSET, ELSET={set_name}\n{_id_line(entity_ids)}")
            if material_signature not in emitted_materials:
                fragments.append(
                    f"*MATERIAL, NAME={material_name}\n"
                    f"*ELASTIC\n"
                    f"{elastic.young_modulus.value:g}, {elastic.poisson_ratio:g}"
                )
                emitted_materials.add(material_signature)
            fragments.append(f"*SOLID SECTION, ELSET={set_name}, MATERIAL={material_name}")
        elif normalized.setup_kind is SetupRecordKind.FIXED_SUPPORT:
            node_sets.append((set_name, entity_ids))
            boundary_lines = "\n".join(
                f"{set_name}, {dof}, {dof}" for dof in parameters["translational_dofs"]
            )
            fragments.extend(
                (
                    f"*NSET, NSET={set_name}\n{_id_line(entity_ids)}",
                    f"*BOUNDARY\n{boundary_lines}",
                )
            )
        elif normalized.setup_kind is SetupRecordKind.PRESCRIBED_DISPLACEMENT:
            node_sets.append((set_name, entity_ids))
            boundary_lines = "\n".join(
                f"{set_name}, {dof}, {dof}, {value:g}"
                for dof, value in enumerate(
                    (parameters["ux"], parameters["uy"], parameters["uz"]),
                    1,
                )
                if value is not None
            )
            fragments.extend(
                (
                    f"*NSET, NSET={set_name}\n{_id_line(entity_ids)}",
                    f"*BOUNDARY\n{boundary_lines}",
                )
            )
        elif normalized.setup_kind is SetupRecordKind.FORCE:
            node_sets.append((set_name, entity_ids))
            load_lines = "\n".join(
                f"{set_name}, {dof}, {value:g}"
                for dof, value in enumerate(parameters["vector"], 1)
                if value != 0.0
            )
            fragments.extend(
                (
                    f"*NSET, NSET={set_name}\n{_id_line(entity_ids)}",
                    f"*CLOAD\n{load_lines}",
                )
            )
    record_ids = tuple(record.setup_id for record in handoff.records)
    return CalculiXSolverSetupPreparation(
        eligible=True,
        execution_mode="prepare_only",
        source_project_name=project.metadata.name,
        mesh_ref=mesh_ref,
        mesh_fingerprint=handoff.mesh_fingerprint,
        record_ids=record_ids,
        element_sets=tuple(element_sets),
        node_sets=tuple(node_sets),
        diagnostics=(),
        input_preview="\n".join(fragments) + ("\n" if fragments else ""),
    )


def _setup_preparation_error(
    project: Project,
    mesh_ref: str,
    mesh_fingerprint: str,
    diagnostics: tuple[str, ...],
) -> CalculiXSolverSetupPreparation:
    return CalculiXSolverSetupPreparation(
        eligible=False,
        execution_mode="prepare_only",
        source_project_name=project.metadata.name,
        mesh_ref=mesh_ref,
        mesh_fingerprint=mesh_fingerprint,
        record_ids=(),
        element_sets=(),
        node_sets=(),
        diagnostics=diagnostics,
        input_preview="",
    )


def _setup_set_name(record: object) -> str:
    prefixes = {
        "MaterialAssignmentRecord": "MAT",
        "FixedSupportRecord": "FIX",
        "PrescribedDisplacementRecord": "DISP",
        "ForceLoadRecord": "FORCE",
    }
    prefix = prefixes.get(type(record).__name__, "SET")
    return f"{prefix}_{_normalized_setup_name(str(getattr(record, 'id', '')))}"


def _normalized_setup_name(value: str) -> str:
    normalized = re.sub(r"[^A-Z0-9_]+", "_", value.upper()).strip("_")
    return normalized or "UNNAMED"


def _id_line(entity_ids: Sequence[int]) -> str:
    return ", ".join(str(item) for item in entity_ids)


def _mesh_cell_type(mesh: MeshData, cell_index: int) -> str:
    remaining = int(cell_index)
    for block in mesh.cells:
        if remaining < block.count:
            return str(block.cell_type).casefold()
        remaining -= block.count
    return ""


class CalculixLinearStaticAdapter(SolverAdapterPlugin):
    """Prepare CalculiX `.inp` files without launching an external solver."""

    manifest: ClassVar[PluginManifest] = PluginManifest.from_dict(
        {
            "id": "osw.solvers.calculix.linear_static",
            "name": "CalculiX Linear Static Adapter",
            "version": "0.1.0",
            "domain": "solver",
            "type": "solver_adapter",
            "license": "GPL-3.0-or-later",
            "input_formats": ["osw.mesh", "osw.project.material"],
            "output_formats": ["calculix.inp"],
            "requires": [],
            "optional_requires": [],
            "capabilities": ["validate", "prepare_case", "linear_static", "dry_run"],
        }
    )

    def __init__(self, generator: CalculixInputDeckGenerator | None = None) -> None:
        self.generator = generator or CalculixInputDeckGenerator()
        super().__init__()

    def prepare_case(self, parameters: dict[str, Any]) -> dict[str, Any]:
        case = parameters.get("case")
        if not isinstance(case, CalculixLinearStaticCase):
            msg = "CalculiX prepare_case requires a CalculixLinearStaticCase in parameters['case']."
            raise TypeError(msg)

        output_path = Path(parameters.get("output_path", f"{case.case_id}.inp"))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        deck_text = self.generator.generate(case)
        output_path.write_text(deck_text, encoding="utf-8")

        return {
            "solver": "CalculiX",
            "adapter_id": self.id,
            "case_id": case.case_id,
            "execution_mode": "prepare_only",
            "input_deck_path": str(output_path),
            "run_command_preview": ["ccx", output_path.stem],
            "validation": self.generator.validate(case).friendly_summary(),
            "limitations": [
                "OSW v0.1 prepares linear static CalculiX decks only.",
                "External solver execution is intentionally outside this adapter.",
            ],
        }


def create_calculix_deck(
    project: Project | None = None,
    *,
    mesh_model: MeshModel | MeshData | None = None,
    options: Mapping[str, Any] | None = None,
    base_path: str | Path | None = None,
) -> CalculiXDeckResult:
    """Create a structured deck result without executing CalculiX."""

    opts = dict(options or {})
    explicit_case = opts.get("case")
    if isinstance(explicit_case, CalculixLinearStaticCase):
        return deck_result_from_case(
            explicit_case,
            output_path=opts.get("output_path"),
            source_project_name=opts.get("source_project_name", ""),
        )
    if opts.get("demo") == "cantilever" or project is None:
        return deck_result_from_case(
            create_cantilever_demo_case(),
            output_path=opts.get("output_path"),
            source_project_name="CalculiX_Cantilever",
        )
    return project_to_calculix_deck(
        project,
        mesh_model=mesh_model,
        base_path=base_path,
        output_path=opts.get("output_path"),
    )


def project_to_calculix_deck(
    project: Project,
    *,
    mesh_model: MeshModel | MeshData | None = None,
    base_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> CalculiXDeckResult:
    """Map ProjectSchema data to a prepare-only CalculiX deck result."""

    case, report = project_to_calculix_case(
        project,
        mesh_model=mesh_model,
        base_path=base_path,
    )
    diagnostics = _validation_diagnostics(report)
    if case is None or report.has_errors:
        return CalculiXDeckResult(
            status="error",
            deck=None,
            input_text="",
            output_path=Path(output_path) if output_path else None,
            diagnostics=diagnostics,
            source_project_name=project.metadata.name,
        )

    result = deck_result_from_case(
        case,
        output_path=output_path,
        source_project_name=project.metadata.name,
    )
    merged = (*diagnostics, *result.diagnostics)
    return CalculiXDeckResult(
        status=result.status,
        deck=result.deck,
        input_text=result.input_text,
        output_path=result.output_path,
        diagnostics=tuple(_deduplicate_diagnostics(merged)),
        source_project_name=result.source_project_name,
        metadata={"project_schema_version": project.schema_version},
    )


def project_to_calculix_case(
    project: Project,
    *,
    mesh_model: MeshModel | MeshData | None = None,
    base_path: str | Path | None = None,
) -> tuple[CalculixLinearStaticCase | None, ValidationReport]:
    """Build a legacy prepare-only case from ProjectSchema data."""

    report = ValidationReport()
    settings = _calculix_settings(project)
    mesh = _resolve_mesh_data(project, mesh_model, base_path, settings, report)
    material = _resolve_material(project, settings, report)
    node_sets = _node_sets_from_settings(settings, report)
    surfaces = _surfaces_from_settings(settings, report)

    boundary_conditions = _boundaries_from_settings(settings, report)
    loads = _loads_from_settings(settings, report)
    if not boundary_conditions and not loads:
        mapped_boundaries, mapped_loads = _loads_and_boundaries_from_project(project, report)
        boundary_conditions = mapped_boundaries
        loads = mapped_loads

    if mesh is None or material is None:
        return None, report

    case = CalculixLinearStaticCase(
        case_id=str(settings.get("case_id") or _slug(project.metadata.name)),
        mesh=mesh,
        material=material,
        node_sets=node_sets,
        surfaces=surfaces,
        boundary_conditions=boundary_conditions,
        loads=loads,
        step_name=str(settings.get("step_name") or "linear_static"),
    )
    report.extend(CalculixInputDeckGenerator().validate(case))
    return case, report


def create_cantilever_demo_case() -> CalculixLinearStaticCase:
    """Return the small deterministic cantilever fixture used by tests and CLI."""

    return CalculixLinearStaticCase(
        case_id="cantilever",
        mesh=create_cantilever_demo_mesh(),
        material=create_cantilever_demo_material(),
        node_sets=(
            CalculixNodeSet("FIXED", (1, 4, 5, 8)),
            CalculixNodeSet("TIP", (2, 3, 6, 7)),
        ),
        boundary_conditions=(CalculixBoundaryCondition.fixed(name="fixed-left", node_set="FIXED"),),
        loads=(
            CalculixLoad.force(
                name="tip-force",
                node_set="TIP",
                dof=2,
                value=-100.0,
            ),
        ),
    )


def create_cantilever_demo_mesh() -> MeshData:
    """Return a one-element hexahedral cantilever mesh."""

    return MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 0.2, 0.0),
            (0.0, 0.2, 0.0),
            (0.0, 0.0, 0.2),
            (1.0, 0.0, 0.2),
            (1.0, 0.2, 0.2),
            (0.0, 0.2, 0.2),
        ),
        cells=(MeshCellBlock("hexahedron", ((0, 1, 2, 3, 4, 5, 6, 7),)),),
    )


def create_cantilever_demo_material() -> Material:
    """Return the isotropic elastic material used by the cantilever demo."""

    return Material(
        material_id="steel",
        name="Steel",
        density=Quantity(7850.0, "kg/m^3"),
        elastic=IsotropicElastic(
            young_modulus=Quantity(210_000_000_000.0, "Pa"),
            poisson_ratio=0.3,
        ),
    )


def load_mesh_model_json(path: str | Path) -> MeshModel:
    """Load a small MeshModel JSON fixture with full topology."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, Mapping) and "mesh" in payload:
        payload = payload["mesh"]
    if not isinstance(payload, Mapping):
        msg = f"Mesh model JSON must contain a mapping: {path}"
        raise CalculiXProjectMappingError(msg)
    return MeshModel.from_dict(payload)


def _resolve_mesh_data(
    project: Project,
    mesh_model: MeshModel | MeshData | None,
    base_path: str | Path | None,
    settings: Mapping[str, Any],
    report: ValidationReport,
) -> MeshData | None:
    if isinstance(mesh_model, MeshData):
        return mesh_model
    if isinstance(mesh_model, MeshModel):
        return mesh_model.to_mesh_data()

    mesh_path = _mesh_model_path(project, settings)
    if not mesh_path:
        report.add_error(
            "project.meshes",
            "Full MeshModel topology is required for CalculiX deck generation.",
        )
        return None
    source = Path(mesh_path)
    if not source.is_absolute() and base_path is not None:
        source = Path(base_path) / source
    try:
        return load_mesh_model_json(source).to_mesh_data()
    except FileNotFoundError:
        report.add_error("project.meshes", f"Mesh topology file does not exist: {source}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report.add_error("project.meshes", f"Could not load mesh topology file {source}: {exc}")
    return None


def _mesh_model_path(project: Project, settings: Mapping[str, Any]) -> str:
    for key in ("mesh_model_path", "mesh_topology_path", "topology_path"):
        if settings.get(key):
            return str(settings[key])
    for mesh_ref in project.meshes:
        metadata = getattr(mesh_ref, "metadata", {}) or {}
        for key in ("mesh_model_path", "mesh_topology_path", "topology_path"):
            if metadata.get(key):
                return str(metadata[key])
        if str(mesh_ref.format).casefold() in {"internal_mesh_model", "mesh_model", "json"}:
            return str(mesh_ref.path)
    return ""


def _resolve_material(
    project: Project,
    settings: Mapping[str, Any],
    report: ValidationReport,
) -> Material | None:
    material_id = str(settings.get("material_id", ""))
    candidates = tuple(project.materials)
    if material_id:
        for material in candidates:
            if material.material_id == material_id or material.name == material_id:
                if material.elastic is None:
                    report.add_error(
                        "project.materials",
                        "Material is required to include isotropic elastic material fields.",
                    )
                    return None
                return material
        report.add_error("project.materials", f"Unknown CalculiX material: {material_id}")
        return None
    for material in candidates:
        if material is not None and material.elastic is not None:
            return material
    report.add_error(
        "project.materials",
        "Material is required and must include isotropic elastic material fields.",
    )
    return None


def _calculix_settings(project: Project) -> Mapping[str, Any]:
    for solver in project.solvers:
        settings = dict(getattr(solver, "settings", {}) or {})
        parameters = dict(getattr(solver, "parameters", {}) or {})
        solver_text = " ".join(
            str(item)
            for item in (
                getattr(solver, "solver_id", ""),
                getattr(solver, "solver", ""),
                getattr(solver, "name", ""),
            )
        ).casefold()
        if isinstance(settings.get("calculix"), Mapping):
            return dict(settings["calculix"])
        if isinstance(parameters.get("calculix"), Mapping):
            return dict(parameters["calculix"])
        if "calculix" in solver_text or "ccx" in solver_text:
            return settings or parameters
    return {}


def _node_sets_from_settings(
    settings: Mapping[str, Any],
    report: ValidationReport,
) -> tuple[CalculixNodeSet, ...]:
    raw = settings.get("node_sets", ())
    records: list[CalculixNodeSet] = []
    if isinstance(raw, Mapping):
        iterator = ({"name": name, "node_ids": ids} for name, ids in raw.items())
    elif isinstance(raw, Sequence) and not isinstance(raw, str | bytes):
        iterator = (item for item in raw if isinstance(item, Mapping))
    else:
        iterator = ()
    for item in iterator:
        name = str(item.get("name", ""))
        node_ids = _int_tuple(item.get("node_ids", ()))
        if not name:
            report.add_error("solvers[].settings.node_sets", "Node set name is required.")
            continue
        records.append(CalculixNodeSet(name, node_ids))
    return tuple(records)


def _surfaces_from_settings(
    settings: Mapping[str, Any],
    report: ValidationReport,
) -> tuple[CalculixSurface, ...]:
    raw = settings.get("surfaces", ())
    records: list[CalculixSurface] = []
    if isinstance(raw, Mapping):
        iterator = ({"name": name, "element_faces": faces} for name, faces in raw.items())
    elif isinstance(raw, Sequence) and not isinstance(raw, str | bytes):
        iterator = (item for item in raw if isinstance(item, Mapping))
    else:
        iterator = ()
    for item in iterator:
        name = str(item.get("name", ""))
        if not name:
            report.add_error("solvers[].settings.surfaces", "Surface name is required.")
            continue
        faces = tuple(
            (int(face[0]), str(face[1]))
            for face in item.get("element_faces", ())
            if isinstance(face, Sequence) and not isinstance(face, str | bytes) and len(face) >= 2
        )
        records.append(CalculixSurface(name, faces))
    return tuple(records)


def _boundaries_from_settings(
    settings: Mapping[str, Any],
    report: ValidationReport,
) -> tuple[CalculixBoundaryCondition, ...]:
    records: list[CalculixBoundaryCondition] = []
    for index, item in enumerate(_mapping_items(settings.get("boundary_conditions", ()))):
        set_name = str(item.get("set_name", item.get("node_set", item.get("target_set", ""))))
        if not set_name:
            report.add_error(
                f"solvers[].settings.boundary_conditions[{index}]",
                "Boundary condition target set is required for CalculiX deck generation.",
            )
            continue
        records.append(
            CalculixBoundaryCondition(
                name=str(item.get("name", f"boundary-{index + 1}")),
                node_set=set_name,
                dof_start=int(item.get("dof_start", 1)),
                dof_end=int(item.get("dof_end", 3)),
                value=float(item.get("value", 0.0)),
                kind=str(item.get("kind", "fixed")),
            )
        )
    return tuple(records)


def _loads_from_settings(
    settings: Mapping[str, Any],
    report: ValidationReport,
) -> tuple[CalculixLoad, ...]:
    records: list[CalculixLoad] = []
    for index, item in enumerate(_mapping_items(settings.get("loads", ()))):
        kind = str(item.get("kind", item.get("load_type", "force"))).casefold()
        if kind == "force":
            node_set = str(item.get("node_set", item.get("target_set", "")))
            if not node_set:
                report.add_error(
                    f"solvers[].settings.loads[{index}]",
                    "Load target set is required for CalculiX deck generation.",
                )
                continue
            components = item.get("components")
            if components is not None:
                records.extend(_component_loads(item, node_set))
                continue
            records.append(
                CalculixLoad.force(
                    name=str(item.get("name", f"force-{index + 1}")),
                    node_set=node_set,
                    dof=int(item.get("dof", 1)),
                    value=float(item.get("value", item.get("magnitude", 0.0))),
                )
            )
        elif kind == "pressure":
            surface = str(item.get("surface", item.get("target_set", "")))
            if not surface:
                report.add_error(
                    f"solvers[].settings.loads[{index}]",
                    "Pressure load target surface is required for CalculiX deck generation.",
                )
                continue
            records.append(
                CalculixLoad.pressure(
                    name=str(item.get("name", f"pressure-{index + 1}")),
                    surface=surface,
                    value=float(item.get("value", item.get("magnitude", 0.0))),
                )
            )
        else:
            report.add_error(
                f"solvers[].settings.loads[{index}]",
                f"Unsupported CalculiX load kind: {kind}",
            )
    return tuple(records)


def _component_loads(item: Mapping[str, Any], node_set: str) -> tuple[CalculixLoad, ...]:
    components = _float_tuple(item.get("components", (0.0, 0.0, 0.0)), length=3)
    records: list[CalculixLoad] = []
    for dof, value in enumerate(components, start=1):
        if value == 0.0:
            continue
        records.append(
            CalculixLoad.force(
                name=f"{item.get('name', 'force')}-{dof}",
                node_set=node_set,
                dof=dof,
                value=value,
            )
        )
    return tuple(records)


def _loads_and_boundaries_from_project(
    project: Project,
    report: ValidationReport,
) -> tuple[tuple[CalculixBoundaryCondition, ...], tuple[CalculixLoad, ...]]:
    boundaries: list[CalculixBoundaryCondition] = []
    loads: list[CalculixLoad] = []
    for physics_index, setup in enumerate(project.physics):
        for boundary_index, boundary in enumerate(setup.boundary_conditions):
            path = f"physics[{physics_index}].boundary_conditions[{boundary_index}]"
            kind = f"{boundary.type} {boundary.kind}".casefold()
            target_set = _boundary_target_set(boundary)
            if "fixed" in kind:
                if not target_set:
                    report.add_error(
                        path,
                        "Boundary condition target set is required for CalculiX deck generation.",
                    )
                    continue
                boundaries.append(
                    CalculixBoundaryCondition.fixed(
                        name=boundary.name,
                        node_set=target_set,
                    )
                )
            elif "force" in kind:
                if not target_set:
                    report.add_error(
                        path,
                        "Load target set is required for CalculiX deck generation.",
                    )
                    continue
                dof = int(boundary.values.get("dof", boundary.metadata.get("dof", 1)))
                loads.append(
                    CalculixLoad.force(
                        name=boundary.name,
                        node_set=target_set,
                        dof=dof,
                        value=_numeric_value(boundary.value),
                    )
                )
            elif "pressure" in kind and "outlet" not in kind:
                if not target_set:
                    report.add_error(
                        path,
                        "Pressure load target surface is required for CalculiX deck generation.",
                    )
                    continue
                loads.append(
                    CalculixLoad.pressure(
                        name=boundary.name,
                        surface=target_set,
                        value=_numeric_value(boundary.value),
                    )
                )
            else:
                report.add_warning(
                    path,
                    (
                        f"Boundary condition '{boundary.name}' of type "
                        f"'{boundary.type or boundary.kind}' is not mapped to the "
                        "CalculiX linear static deck."
                    ),
                )
    return tuple(boundaries), tuple(loads)


def _boundary_target_set(boundary: object) -> str:
    metadata = getattr(boundary, "metadata", {}) or {}
    values = getattr(boundary, "values", {}) or {}
    return str(
        metadata.get("target_set")
        or values.get("target_set")
        or metadata.get("node_set")
        or values.get("node_set")
        or getattr(boundary, "target", "")
    )


def _numeric_value(value: object) -> float:
    match = re.search(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", str(value))
    return float(match.group(0)) if match else 0.0


def _mapping_items(value: object) -> tuple[Mapping[str, Any], ...]:
    if isinstance(value, Mapping):
        return tuple(item for item in value.values() if isinstance(item, Mapping))
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return tuple(item for item in value if isinstance(item, Mapping))
    return ()


def _int_tuple(value: object) -> tuple[int, ...]:
    if value is None:
        return ()
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return tuple(int(item) for item in value)
    return (int(value),)


def _float_tuple(value: object, *, length: int) -> tuple[float, ...]:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        items = tuple(float(item) for item in value)
    else:
        items = (float(value),)
    if len(items) >= length:
        return items[:length]
    return (*items, *(0.0 for _ in range(length - len(items))))


def _validation_diagnostics(report: ValidationReport) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "severity": message.severity,
            "path": message.path,
            "message": message.message,
        }
        for message in report.messages
    )


def _deduplicate_diagnostics(
    diagnostics: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict[str, Any]] = []
    for item in diagnostics:
        key = (
            str(item.get("severity", "")),
            str(item.get("path", "")),
            str(item.get("message", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(dict(item))
    return tuple(unique)


def _slug(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
    return slug or "calculix-case"
