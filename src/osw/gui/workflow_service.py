"""Stateful GUI workflow service for import, prepare, preview, and report flows."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from importlib import import_module
from pathlib import Path
from tempfile import gettempdir
from typing import Any

from osw.core.materials import IsotropicElastic, Material
from osw.core.project_schema import (
    GeometryRef,
    MeshRef,
    Project,
    ProjectMetadata,
    ResultRef,
    ScriptRef,
    SolverConfig,
)
from osw.core.run_manager import ExecutablePathRegistry
from osw.core.units import Quantity
from osw.geometry.cad_importer_base import (
    GeometryImportError,
    detect_geometry_format,
    preview_geometry,
)
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.mesh.meshio_bridge import MeshImportError, detect_mesh_format, load_mesh
from osw.post.table_model import TablePreview
from osw.scripts.mscript.figure_dataset import FigureDataset
from osw.scripts.mscript.importer import MScriptImportError, import_mscript_preview
from osw.scripts.mscript.mat_reader import MatReader

PROJECT_SECTIONS_BY_DOMAIN = {
    "geometry": "Geometry",
    "mesh": "Mesh",
    "script": "Scripts",
    "solver": "Solvers",
    "result": "Results",
    "report": "Reports",
    "diagnostic": "Results",
}


@dataclass(frozen=True)
class WorkbenchItem:
    """GUI-visible item backed by ProjectSchema state or workflow diagnostics."""

    item_id: str
    section: str
    label: str
    item_type: str
    workflow_step: str
    status: str
    summary: str
    path: str = ""
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, str] = field(default_factory=dict)
    mesh_data: Any | None = None
    mesh_info: Any | None = None
    table: TablePreview | None = None
    figure_dataset: FigureDataset | None = None

    def property_rows(self, *, project_name: str, units_name: str) -> dict[str, str]:
        diagnostics = "\n".join(self.diagnostics) if self.diagnostics else "None"
        rows = {
            "Project": project_name,
            "Units": units_name,
            "Selection": self.label,
            "Workflow step": self.workflow_step,
            "Type": self.item_type,
            "Path": self.path or "N/A",
            "Status": self.status,
            "Summary": self.summary,
            "Diagnostics": diagnostics,
        }
        for key, value in self.metadata.items():
            rows[f"Metadata: {key}"] = value
        return rows


@dataclass(frozen=True)
class WorkflowOperation:
    """Result of a GUI workflow service operation."""

    title: str
    status: str
    logs: tuple[str, ...]
    items: tuple[WorkbenchItem, ...] = field(default_factory=tuple)
    selected_item_id: str | None = None


class WorkbenchWorkflowSession:
    """Small state holder used by the GUI to demonstrate the v0.1 workflow."""

    def __init__(
        self,
        *,
        project: Project | None = None,
        artifact_dir: str | Path | None = None,
        registry: ExecutablePathRegistry | None = None,
    ) -> None:
        self.project = project or Project(metadata=ProjectMetadata(name="Untitled OSW Project"))
        self.artifact_dir = Path(artifact_dir) if artifact_dir else _default_artifact_dir()
        self.registry = registry or ExecutablePathRegistry()
        self.items: dict[str, WorkbenchItem] = {}
        self.mesh_infos: list[Any] = []
        self.result_tables: list[TablePreview] = []
        self.figure_datasets: list[FigureDataset] = []
        self.warnings: list[str] = []

    def item(self, item_id: str) -> WorkbenchItem | None:
        return self.items.get(item_id)

    def import_path(self, path: str | Path) -> WorkflowOperation:
        source = Path(path).expanduser()
        suffix = source.suffix.lower()
        try:
            if suffix == ".m":
                item = self._import_mscript(source)
            elif suffix == ".mat":
                item = self._import_mat(source)
            elif suffix in _mesh_extensions():
                item = self._import_mesh(source)
            else:
                detect_geometry_format(source)
                item = self._import_geometry(source)
        except (GeometryImportError, MeshImportError, MScriptImportError, OSError) as exc:
            item = self._record_diagnostic(
                label=f"Import diagnostic: {source.name}",
                path=source,
                summary=str(exc),
            )
        return WorkflowOperation(
            title="Import",
            status=item.status,
            logs=(f"{item.label}: {item.summary}", *item.diagnostics),
            items=(item,),
            selected_item_id=item.item_id,
        )

    def run_generate(self) -> WorkflowOperation:
        """Prepare bounded workflows and diagnostics without launching external tools."""

        items: list[WorkbenchItem] = []
        logs: list[str] = []
        for prepare in (
            self._prepare_calculix,
            self._prepare_openfoam,
            self._prepare_gmsh,
            self._prepare_cantera_or_coolprop,
            self._prepare_mscript,
        ):
            item = prepare()
            items.append(item)
            logs.append(f"{item.label}: {item.summary}")
            logs.extend(item.diagnostics)

        return WorkflowOperation(
            title="Run/Generate",
            status="Prepared",
            logs=tuple(logs),
            items=tuple(items),
            selected_item_id=items[-1].item_id if items else None,
        )

    def _import_mesh(self, path: Path) -> WorkbenchItem:
        mesh_data = load_mesh(path)
        mesh_format = detect_mesh_format(path)
        mesh_info = mesh_data.info(str(path), mesh_format)
        ref_id = self._next_id("mesh")
        metadata = {
            "nodes": str(mesh_info.nodes),
            "elements": str(mesh_info.elements),
            "cell_types": ", ".join(mesh_info.cell_types) or "None",
        }
        mesh_ref = MeshRef(ref_id=ref_id, path=str(path), format=mesh_format, metadata=metadata)
        self.project = replace(self.project, meshes=[*self.project.meshes, mesh_ref])
        table = _mesh_info_table(mesh_info)
        item = WorkbenchItem(
            item_id=ref_id,
            section="Mesh",
            label=f"Mesh: {path.name}",
            item_type=f"Mesh ({mesh_format})",
            workflow_step="Imported mesh preview",
            status="Imported",
            summary=(
                f"{mesh_info.nodes} nodes, {mesh_info.elements} elements, "
                f"cells: {', '.join(mesh_info.cell_types) or 'none'}"
            ),
            path=str(path),
            metadata=metadata,
            mesh_data=mesh_data,
            mesh_info=mesh_info,
            table=table,
        )
        self.mesh_infos.append(mesh_info)
        self.result_tables.append(table)
        return self._store_item(item)

    def _import_geometry(self, path: Path) -> WorkbenchItem:
        model = preview_geometry(path)
        ref_id = self._next_id("geometry")
        metadata = {
            "format": model.format,
            "bodies": str(model.body_count),
            "bounds": _bounds_text(model.bounding_box),
        }
        geometry_ref = GeometryRef(
            ref_id=ref_id,
            path=str(path),
            format=model.format,
            metadata=metadata,
        )
        self.project = replace(self.project, geometry=[*self.project.geometry, geometry_ref])
        diagnostics = tuple(model.warnings)
        table = _rows_table(
            "Geometry preview",
            (
                ("Format", model.format),
                ("Bodies", str(model.body_count)),
                ("Bounds", metadata["bounds"]),
                ("Parser", str(model.metadata.get("parser", "preview"))),
            ),
            source=str(path),
        )
        item = WorkbenchItem(
            item_id=ref_id,
            section="Geometry",
            label=f"Geometry: {path.name}",
            item_type=f"Geometry ({model.format})",
            workflow_step="Imported geometry preview",
            status="Imported with warnings" if diagnostics else "Imported",
            summary=f"{model.body_count} preview body/bodies from standard geometry",
            path=str(path),
            diagnostics=diagnostics,
            metadata=metadata,
            table=table,
        )
        self.result_tables.append(table)
        self.warnings.extend(diagnostics)
        return self._store_item(item)

    def _import_mscript(self, path: Path) -> WorkbenchItem:
        preview = import_mscript_preview(path)
        ref_id = self._next_id("script")
        findings = tuple(
            f"{finding.severity}: line {finding.line} {finding.message}"
            for finding in preview.safety.findings
        )
        metadata = {
            "kind": preview.kind.value,
            "lines": str(preview.line_count),
            "executable_lines": str(preview.executable_line_count),
            "contains_plot_call": str(preview.contains_plot_call),
            "safe_for_preview": str(preview.safety.is_safe_for_preview),
        }
        script_ref = ScriptRef(
            ref_id=ref_id,
            path=str(path),
            language="matlab-octave",
            metadata=metadata,
        )
        self.project = replace(self.project, scripts=[*self.project.scripts, script_ref])
        table = _rows_table(
            "M-script preview",
            (
                ("Name", preview.name),
                ("Kind", preview.kind.value),
                ("Lines", str(preview.line_count)),
                ("Executable lines", str(preview.executable_line_count)),
                ("Contains plot call", str(preview.contains_plot_call)),
                ("Preview safe", str(preview.safety.is_safe_for_preview)),
            ),
            source=str(path),
        )
        figure_dataset = (
            FigureDataset(
                dataset_id=f"{ref_id}-figures",
                source=str(path),
                notes=("Plot calls were detected. Import is preview-only; no script ran.",),
            )
            if preview.contains_plot_call
            else None
        )
        item = WorkbenchItem(
            item_id=ref_id,
            section="Scripts",
            label=f"M-script preview: {path.name}",
            item_type="M-script preview",
            workflow_step="Preview-first script import",
            status="Previewed with findings" if findings else "Previewed",
            summary="Script metadata loaded without executing code",
            path=str(path),
            diagnostics=findings,
            metadata=metadata,
            table=table,
            figure_dataset=figure_dataset,
        )
        self.result_tables.append(table)
        if figure_dataset is not None:
            self.figure_datasets.append(figure_dataset)
        self.warnings.extend(findings)
        return self._store_item(item)

    def _import_mat(self, path: Path) -> WorkbenchItem:
        preview = MatReader().read(path)
        ref_id = self._next_id("result")
        diagnostics = tuple(
            f"{message.severity.value}: {message.message}"
            for message in preview.diagnostics.messages
        )
        variable_rows = tuple(
            (
                variable.name,
                variable.display_shape,
                variable.dtype,
                "numeric" if variable.is_numeric else "non-numeric",
            )
            for variable in preview.variables
        )
        variables_table = TablePreview(
            columns=("variable", "shape", "dtype", "kind"),
            rows=variable_rows,
            title="MAT variables",
            source=str(path),
            notes=("MAT import is preview-only; no MATLAB or Octave code is executed.",),
        )
        table = (
            preview.table_preview(preview.variables[0].name)
            if preview.variables and not preview.diagnostics.has_errors
            else variables_table
        )
        metadata = {
            "format": preview.format_version,
            "variables": str(len(preview.variables)),
            "table": table.title or "MAT variables",
        }
        result_ref = ResultRef(
            ref_id=ref_id,
            path=str(path),
            kind="mat-preview",
            metadata=metadata,
        )
        self.project = replace(self.project, results=[*self.project.results, result_ref])
        item = WorkbenchItem(
            item_id=ref_id,
            section="Results",
            label=f"MAT data preview: {path.name}",
            item_type="MAT data preview",
            workflow_step="Preview MAT variables",
            status="Previewed with diagnostics" if diagnostics else "Previewed",
            summary=f"{len(preview.variables)} variable(s), format {preview.format_version}",
            path=str(path),
            diagnostics=diagnostics,
            metadata=metadata,
            table=table,
        )
        self.result_tables.append(table)
        self.warnings.extend(diagnostics)
        return self._store_item(item)

    def _prepare_calculix(self) -> WorkbenchItem:
        ref_id = self._next_id("solver")
        try:
            adapter_mod = import_module("osw.solvers.calculix.adapter")
            deck_mod = import_module("osw.solvers.calculix.input_deck")
            adapter = adapter_mod.CalculixLinearStaticAdapter()
            case = self._sample_calculix_case(deck_mod)
            output_path = self.artifact_dir / "calculix" / "gui_cantilever.inp"
            prepared = adapter.prepare_case({"case": case, "output_path": output_path})
            lookup = self.registry.resolve("ccx")
            diagnostics = _lookup_diagnostics(lookup)
            summary = f"Prepared input deck {output_path.name}; execution remains external"
            status = "Prepared with diagnostics" if diagnostics else "Prepared"
            table = _dict_table("CalculiX prepare result", prepared)
            solver_config = SolverConfig(
                solver_id=ref_id,
                name="CalculiX linear static",
                execution_mode="prepare_only",
                parameters={"input_deck_path": str(output_path)},
            )
            result_ref = ResultRef(
                ref_id=self._next_id("result"),
                path=str(output_path),
                kind="calculix-input-deck",
                metadata={"execution_mode": "prepare_only"},
            )
            self.project = replace(
                self.project,
                solvers=[*self.project.solvers, solver_config],
                results=[*self.project.results, result_ref],
            )
        except Exception as exc:  # pragma: no cover - exact optional errors vary.
            diagnostics = (str(exc),)
            summary = "CalculiX prepare-only workflow produced a diagnostic"
            status = "Diagnostic"
            table = _rows_table(
                "CalculiX diagnostic",
                (("Diagnostic", str(exc)),),
                source="CalculiX",
            )
        item = WorkbenchItem(
            item_id=ref_id,
            section="Solvers",
            label="CalculiX linear static prepare",
            item_type="Solver prepare-only workflow",
            workflow_step="Run/Generate",
            status=status,
            summary=summary,
            path=str(self.artifact_dir / "calculix"),
            diagnostics=diagnostics,
            table=table,
        )
        self.result_tables.append(table)
        self.warnings.extend(diagnostics)
        return self._store_item(item)

    def _prepare_openfoam(self) -> WorkbenchItem:
        ref_id = self._next_id("solver")
        try:
            adapter_mod = import_module("osw.solvers.openfoam.adapter")
            case_mod = import_module("osw.solvers.openfoam.case_generator")
            adapter = adapter_mod.OpenFoamCavityTemplateAdapter()
            output_dir = self.artifact_dir / "openfoam"
            prepared = adapter.prepare_case(
                {
                    "case": case_mod.OpenFoamCavityConfig(case_name="gui_cavity"),
                    "output_dir": output_dir,
                }
            )
            diagnostics = (
                *_lookup_diagnostics(self.registry.resolve("blockMesh")),
                *_lookup_diagnostics(self.registry.resolve("icoFoam")),
            )
            summary = "Prepared OpenFOAM cavity template; execution remains external"
            status = "Prepared with diagnostics" if diagnostics else "Prepared"
            table = _dict_table("OpenFOAM prepare result", prepared)
            solver_config = SolverConfig(
                solver_id=ref_id,
                name="OpenFOAM cavity template",
                execution_mode="prepare_only",
                parameters={"case_dir": str(prepared.get("case_dir", output_dir))},
            )
            self.project = replace(
                self.project,
                solvers=[*self.project.solvers, solver_config],
            )
        except Exception as exc:  # pragma: no cover - exact optional errors vary.
            diagnostics = (str(exc),)
            summary = "OpenFOAM prepare-only workflow produced a diagnostic"
            status = "Diagnostic"
            table = _rows_table(
                "OpenFOAM diagnostic",
                (("Diagnostic", str(exc)),),
                source="OpenFOAM",
            )
        item = WorkbenchItem(
            item_id=ref_id,
            section="Solvers",
            label="OpenFOAM cavity prepare",
            item_type="Solver prepare-only workflow",
            workflow_step="Run/Generate",
            status=status,
            summary=summary,
            path=str(self.artifact_dir / "openfoam"),
            diagnostics=diagnostics,
            table=table,
        )
        self.result_tables.append(table)
        self.warnings.extend(diagnostics)
        return self._store_item(item)

    def _prepare_gmsh(self) -> WorkbenchItem:
        ref_id = self._next_id("mesh")
        try:
            gmsh_mod = import_module("osw.mesh.gmsh_adapter")
            target = self.artifact_dir / "gmsh" / "gui_plate.msh"
            vtu_path = self.artifact_dir / "gmsh" / "gui_plate.vtu"
            result = gmsh_mod.generate_primitive_mesh(
                gmsh_mod.GmshPrimitive.plate(width=1.0, height=0.5, name="gui_plate"),
                target,
                mesh_size=gmsh_mod.MeshSizeControl(target_size=0.25),
                vtu_path=vtu_path,
            )
            diagnostics: tuple[str, ...] = ()
            mesh_info = result.mesh_info
            table = _rows_table(
                "Gmsh prepare result",
                (
                    ("Mesh path", str(result.msh_path)),
                    ("VTU path", str(result.vtu_path or "")),
                    ("Primitive", result.primitive.kind),
                    ("Mode", "generated by optional gmsh Python API"),
                ),
                source=str(result.msh_path),
            )
            summary = f"Generated Gmsh primitive mesh {result.msh_path.name}"
            status = "Generated"
            if mesh_info is not None:
                self.mesh_infos.append(mesh_info)
        except Exception as exc:  # pragma: no cover - depends on optional gmsh.
            diagnostics = (str(exc),)
            mesh_info = None
            table = _rows_table("Gmsh diagnostic", (("Diagnostic", str(exc)),), source="Gmsh")
            summary = "Gmsh mesh generation is unavailable in this environment"
            status = "Diagnostic"
        item = WorkbenchItem(
            item_id=ref_id,
            section="Mesh",
            label="Gmsh plate generation",
            item_type="Mesh generation workflow",
            workflow_step="Run/Generate",
            status=status,
            summary=summary,
            path=str(self.artifact_dir / "gmsh"),
            diagnostics=diagnostics,
            mesh_info=mesh_info,
            table=table,
        )
        self.result_tables.append(table)
        self.warnings.extend(diagnostics)
        return self._store_item(item)

    def _prepare_cantera_or_coolprop(self) -> WorkbenchItem:
        ref_id = self._next_id("result")
        diagnostics: tuple[str, ...] = ()
        try:
            coolprop_mod = import_module("osw.solvers.coolprop.property_plugin")
            plugin = coolprop_mod.CoolPropPropertyPlugin()
            report = plugin.dependency_report()
            if report.has_errors:
                raise coolprop_mod.CoolPropDependencyError(report)
            state = coolprop_mod.CoolPropStateInput(
                fluid="Water",
                pressure_pa=101325.0,
                temperature_k=300.0,
            )
            result = plugin.calculate_state(state)
            table = result.to_table_preview()
            summary = "Calculated CoolProp property table"
            status = "Calculated"
        except Exception as exc:
            diagnostics = (str(exc),)
            try:
                cantera_mod = import_module("osw.solvers.cantera.adapter")
                plugin = cantera_mod.CanteraReactorPlugin()
                prepared = plugin.prepare_case({})
                table = _dict_table("Cantera prepare preview", prepared)
                summary = "Prepared Cantera 0D reactor preview diagnostic"
            except Exception as cantera_exc:  # pragma: no cover - optional backend.
                diagnostics = (*diagnostics, str(cantera_exc))
                table = _rows_table(
                    "CHM diagnostic",
                    tuple(("Diagnostic", item) for item in diagnostics),
                    source="CHM",
                )
                summary = "CHM demo produced optional dependency diagnostics"
            status = "Diagnostic"
        result_ref = ResultRef(
            ref_id=ref_id,
            path="",
            kind="chm-preview",
            metadata={"status": status, "summary": summary},
        )
        self.project = replace(self.project, results=[*self.project.results, result_ref])
        item = WorkbenchItem(
            item_id=ref_id,
            section="Results",
            label="CHM property/reactor preview",
            item_type="CHM workflow",
            workflow_step="Run/Generate",
            status=status,
            summary=summary,
            diagnostics=diagnostics,
            table=table,
        )
        self.result_tables.append(table)
        self.warnings.extend(diagnostics)
        return self._store_item(item)

    def _prepare_mscript(self) -> WorkbenchItem:
        ref_id = self._next_id("result")
        lookup = self.registry.resolve("octave")
        diagnostics = (
            "M-script execution is explicit and never triggered by import.",
            *_lookup_diagnostics(lookup),
        )
        table = _rows_table(
            "M-script execution preview",
            (
                ("Mode", "preview-first"),
                ("Imported scripts", str(len(self.project.scripts))),
                ("Octave available", str(lookup.found)),
                ("Execution", "not run by GUI import"),
            ),
            source="M-script",
        )
        result_ref = ResultRef(
            ref_id=ref_id,
            path="",
            kind="mscript-diagnostic",
            metadata={"execution_mode": "explicit_only"},
        )
        self.project = replace(self.project, results=[*self.project.results, result_ref])
        item = WorkbenchItem(
            item_id=ref_id,
            section="Results",
            label="M-script explicit run diagnostic",
            item_type="Script workflow diagnostic",
            workflow_step="Run/Generate",
            status="Diagnostic",
            summary=(
                "Script imports remain preview-first; Octave execution requires "
                "explicit runner"
            ),
            diagnostics=diagnostics,
            table=table,
        )
        self.result_tables.append(table)
        self.warnings.extend(diagnostics)
        return self._store_item(item)

    def _record_diagnostic(self, *, label: str, path: Path, summary: str) -> WorkbenchItem:
        ref_id = self._next_id("diagnostic")
        table = _rows_table(
            "Import diagnostic",
            (("Path", str(path)), ("Diagnostic", summary)),
            source=str(path),
        )
        result_ref = ResultRef(
            ref_id=ref_id,
            path=str(path),
            kind="import-diagnostic",
            metadata={"summary": summary},
        )
        self.project = replace(self.project, results=[*self.project.results, result_ref])
        item = WorkbenchItem(
            item_id=ref_id,
            section="Results",
            label=label,
            item_type="Import diagnostic",
            workflow_step="Import",
            status="Diagnostic",
            summary=summary,
            path=str(path),
            diagnostics=(summary,),
            table=table,
        )
        self.result_tables.append(table)
        self.warnings.append(summary)
        return self._store_item(item)

    def _sample_calculix_case(self, deck_mod: Any) -> Any:
        return deck_mod.CalculixLinearStaticCase(
            case_id="gui_cantilever",
            mesh=MeshData(
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
            ),
            material=Material(
                material_id="steel",
                name="Steel",
                density=Quantity(7850.0, "kg/m^3"),
                elastic=IsotropicElastic(
                    young_modulus=Quantity(210_000_000_000.0, "Pa"),
                    poisson_ratio=0.3,
                ),
            ),
            node_sets=(
                deck_mod.CalculixNodeSet("FIXED", (1, 4, 5, 8)),
                deck_mod.CalculixNodeSet("TIP", (2, 3, 6, 7)),
            ),
            boundary_conditions=(
                deck_mod.CalculixBoundaryCondition.fixed(
                    name="fixed-left",
                    node_set="FIXED",
                ),
            ),
            loads=(
                deck_mod.CalculixLoad.force(
                    name="tip-force",
                    node_set="TIP",
                    dof=2,
                    value=-100.0,
                ),
            ),
        )

    def _store_item(self, item: WorkbenchItem) -> WorkbenchItem:
        self.items[item.item_id] = item
        return item

    def _next_id(self, prefix: str) -> str:
        count = 1 + sum(1 for key in self.items if key.startswith(f"{prefix}-"))
        return f"{prefix}-{count:03d}"


def _default_artifact_dir() -> Path:
    return Path(gettempdir()) / "osw-gui-workflow"


def _mesh_extensions() -> tuple[str, ...]:
    bridge = import_module("osw.mesh.meshio_bridge")
    return tuple(bridge.SUPPORTED_MESH_FORMATS)


def _lookup_diagnostics(lookup: Any) -> tuple[str, ...]:
    return () if lookup.found else (lookup.diagnostics.summary(),)


def _mesh_info_table(mesh_info: Any) -> TablePreview:
    return _rows_table(
        "Mesh preview",
        (
            ("Source", str(mesh_info.source)),
            ("Format", str(mesh_info.format)),
            ("Nodes", str(mesh_info.nodes)),
            ("Elements", str(mesh_info.elements)),
            ("Cell types", ", ".join(mesh_info.cell_types) or "None"),
            ("Bounds", _bounds_text(mesh_info.bounding_box)),
        ),
        source=str(mesh_info.source),
    )


def _dict_table(title: str, payload: dict[str, Any]) -> TablePreview:
    rows = tuple((str(key), _short_value(value)) for key, value in payload.items())
    return _rows_table(title, rows, source=str(payload.get("solver", "")))


def _rows_table(
    title: str,
    rows: tuple[tuple[str, str], ...],
    *,
    source: str = "",
) -> TablePreview:
    return TablePreview(
        columns=("Field", "Value"),
        rows=tuple((str(key), str(value)) for key, value in rows),
        title=title,
        source=source,
    )


def _bounds_text(bounds: Any) -> str:
    return f"min={tuple(bounds.minimum)}, max={tuple(bounds.maximum)}"


def _short_value(value: Any) -> str:
    if isinstance(value, list | tuple):
        return ", ".join(_short_value(item) for item in value[:8])
    if isinstance(value, dict):
        return "; ".join(f"{key}={_short_value(item)}" for key, item in value.items())
    text = str(value)
    return text if len(text) <= 240 else f"{text[:237]}..."
