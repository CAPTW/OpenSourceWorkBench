"""Experimental no-run FEASpec CalculiX INP renderer.

The renderer consumes an already reviewed FEASpec CalculiX case plan and
returns deterministic text or diagnostics. It does not integrate with solver
adapters, command execution layers, GUI code, provider APIs, or ProjectSchema
mutation paths.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .calculix_case_plan import (
    CalculiXCaseBoundaryConditionPlan,
    CalculiXCaseElementPlan,
    CalculiXCaseLoadPlan,
    CalculiXCaseMaterialPlan,
    CalculiXCaseNodePlan,
    CalculiXCaseOutputRequestPlan,
    CalculiXCaseSectionPlan,
    CalculiXCaseStepPlan,
    FEASpecCalculiXCasePlan,
)
from .calculix_diagnostics import CalculiXPlanDiagnosticCode
from .calculix_inp_diagnostics import (
    CalculiXInpDiagnosticCode,
    CalculiXInpSeverity,
    FEASpecCalculiXInpDiagnostic,
)

SUPPORTED_ELEMENT_TYPES = frozenset(
    {"T3D2", "B31", "CPS3", "CPS4", "CPE3", "CPE4", "C3D4", "C3D8"}
)
SUPPORTED_FORCE_LOADS = frozenset({"force", "point_force", "concentrated_force"})
SUPPORTED_PRESSURE_LOADS = frozenset({"pressure", "distributed", "distributed_load"})
SUPPORTED_STEP_TYPES = frozenset({"static", "linear_static"})
SUPPORTED_OUTPUT_VARIABLES = frozenset({"U", "S"})

__all__ = [
    "CalculiXInpRenderResult",
    "CalculiXInpRenderStatus",
    "CalculiXInpSection",
    "CalculiXInpWriteResult",
    "CalculiXInpWriteStatus",
    "explain_inp_render_result",
    "render_calculix_inp",
    "write_calculix_inp",
]


class CalculiXInpRenderStatus(str, Enum):
    """Status for in-memory INP rendering."""

    BLOCKED = "blocked"
    RENDERED = "rendered"
    RENDERED_WITH_WARNINGS = "rendered-with-warnings"


class CalculiXInpWriteStatus(str, Enum):
    """Status for explicit caller-path INP writing."""

    BLOCKED = "blocked"
    WRITTEN = "written"
    WRITTEN_WITH_WARNINGS = "written-with-warnings"


@dataclass(frozen=True)
class CalculiXInpSection:
    """A rendered INP section and its source record references."""

    name: str
    lines: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "lines": list(self.lines),
            "source_refs": list(self.source_refs),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class CalculiXInpRenderResult:
    """Result of no-run FEASpec CalculiX INP rendering."""

    status: str
    text: str = ""
    sections: tuple[CalculiXInpSection, ...] = ()
    diagnostics: tuple[FEASpecCalculiXInpDiagnostic, ...] = ()
    line_count: int = 0
    ready_for_solver_execution: bool = False

    @property
    def is_blocked(self) -> bool:
        return self.status == CalculiXInpRenderStatus.BLOCKED.value

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "text": self.text,
            "sections": [section.to_dict() for section in self.sections],
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
            "line_count": self.line_count,
            "ready_for_solver_execution": self.ready_for_solver_execution,
        }


@dataclass(frozen=True)
class CalculiXInpWriteResult:
    """Result of explicit caller-path FEASpec CalculiX INP writing."""

    status: str
    path: Path
    bytes_written: int = 0
    render_result: CalculiXInpRenderResult | None = None
    diagnostics: tuple[FEASpecCalculiXInpDiagnostic, ...] = ()
    ready_for_solver_execution: bool = False

    @property
    def is_blocked(self) -> bool:
        return self.status == CalculiXInpWriteStatus.BLOCKED.value

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "path": str(self.path),
            "bytes_written": self.bytes_written,
            "render_result": self.render_result.to_dict() if self.render_result else None,
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
            "ready_for_solver_execution": self.ready_for_solver_execution,
        }


def render_calculix_inp(
    case_plan: FEASpecCalculiXCasePlan,
) -> CalculiXInpRenderResult:
    """Render deterministic INP text from a writer-ready FEASpec case plan."""

    diagnostics = _render_diagnostics(case_plan)
    if any(diagnostic.blocks_render for diagnostic in diagnostics):
        return CalculiXInpRenderResult(
            status=CalculiXInpRenderStatus.BLOCKED.value,
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
            ready_for_solver_execution=False,
        )

    sections = (
        _header_section(case_plan),
        _node_section(case_plan.nodes),
        _element_section(case_plan.elements),
        _material_section(case_plan.materials),
        _section_property_section(case_plan.sections, case_plan.materials),
        _boundary_section(case_plan.boundary_conditions),
        _load_section(case_plan.loads),
        _step_section(case_plan.steps),
        _output_section(case_plan.output_requests),
        CalculiXInpSection("*END STEP", ("*END STEP",)),
    )
    text = _sections_to_text(sections)
    status = (
        CalculiXInpRenderStatus.RENDERED_WITH_WARNINGS.value
        if any(
            diagnostic.severity is CalculiXInpSeverity.WARNING
            for diagnostic in diagnostics
        )
        else CalculiXInpRenderStatus.RENDERED.value
    )
    return CalculiXInpRenderResult(
        status=status,
        text=text,
        sections=sections,
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        line_count=len(text.rstrip("\n").splitlines()) if text else 0,
        ready_for_solver_execution=False,
    )


def write_calculix_inp(
    case_plan: FEASpecCalculiXCasePlan,
    path: str | Path,
    *,
    overwrite: bool = False,
) -> CalculiXInpWriteResult:
    """Write rendered INP text to a caller-provided path without running CalculiX."""

    target = Path(path)
    render_result = render_calculix_inp(case_plan)
    diagnostics = list(render_result.diagnostics)
    if render_result.is_blocked:
        return CalculiXInpWriteResult(
            status=CalculiXInpWriteStatus.BLOCKED.value,
            path=target,
            render_result=render_result,
            diagnostics=tuple(diagnostics),
            ready_for_solver_execution=False,
        )
    if target.exists() and not overwrite:
        diagnostics.append(
            _diag(
                CalculiXInpDiagnosticCode.FW_WRITE_PATH_EXISTS,
                CalculiXInpSeverity.BLOCKER,
                "Refusing to overwrite an existing INP file.",
                target_ref=str(target),
                source_field="path",
                suggested_fix="Pass overwrite=True or choose a new output path.",
                blocks_render=False,
                blocks_write=True,
            )
        )
        return CalculiXInpWriteResult(
            status=CalculiXInpWriteStatus.BLOCKED.value,
            path=target,
            render_result=render_result,
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
            ready_for_solver_execution=False,
        )
    if not target.parent.exists():
        diagnostics.append(
            _diag(
                CalculiXInpDiagnosticCode.FW_PLAN_NOT_READY,
                CalculiXInpSeverity.BLOCKER,
                "Parent directory does not exist; renderer will not create directories.",
                target_ref=str(target.parent),
                source_field="path.parent",
                suggested_fix="Create the parent directory before writing.",
                blocks_render=False,
                blocks_write=True,
            )
        )
        return CalculiXInpWriteResult(
            status=CalculiXInpWriteStatus.BLOCKED.value,
            path=target,
            render_result=render_result,
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
            ready_for_solver_execution=False,
        )

    target.write_text(render_result.text, encoding="utf-8", newline="\n")
    status = (
        CalculiXInpWriteStatus.WRITTEN_WITH_WARNINGS.value
        if render_result.status == CalculiXInpRenderStatus.RENDERED_WITH_WARNINGS.value
        else CalculiXInpWriteStatus.WRITTEN.value
    )
    return CalculiXInpWriteResult(
        status=status,
        path=target,
        bytes_written=len(render_result.text.encode("utf-8")),
        render_result=render_result,
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        ready_for_solver_execution=False,
    )


def explain_inp_render_result(result: CalculiXInpRenderResult) -> list[str]:
    """Return reviewer-readable INP render status and diagnostics."""

    lines = [
        f"CalculiX INP render status: {result.status}.",
        f"Ready for solver execution: {str(result.ready_for_solver_execution).lower()}.",
    ]
    if result.text:
        lines.append(f"Rendered {result.line_count} deterministic INP lines.")
    else:
        lines.append("No INP text was rendered.")
    for diagnostic in result.diagnostics:
        target = f" [{diagnostic.target_ref}]" if diagnostic.target_ref else ""
        lines.append(
            f"{diagnostic.severity.value.upper()} {diagnostic.code.value}{target}: "
            f"{diagnostic.message}"
        )
    lines.append("No CalculiX solver execution was performed.")
    return lines


def _render_diagnostics(
    case_plan: FEASpecCalculiXCasePlan,
) -> list[FEASpecCalculiXInpDiagnostic]:
    diagnostics: list[FEASpecCalculiXInpDiagnostic] = []
    if not case_plan.ready_for_inp_writer:
        diagnostics.append(
            _diag(
                CalculiXInpDiagnosticCode.FW_PLAN_NOT_READY,
                CalculiXInpSeverity.BLOCKER,
                "Case plan is not ready for INP rendering.",
                target_ref=case_plan.case_id,
                source_field="ready_for_inp_writer",
                suggested_fix="Resolve case-plan blockers before renderer handoff.",
            )
        )
    for diagnostic in case_plan.diagnostics:
        if getattr(diagnostic, "blocks_case_plan", False):
            diagnostics.append(_diagnostic_from_case_plan(diagnostic))
    diagnostics.extend(_topology_diagnostics(case_plan.nodes, case_plan.elements))
    diagnostics.extend(_material_diagnostics(case_plan.materials))
    diagnostics.extend(_section_diagnostics(case_plan.sections, case_plan.materials))
    known_targets = _known_targets(case_plan)
    diagnostics.extend(_boundary_diagnostics(case_plan.boundary_conditions, known_targets))
    diagnostics.extend(_load_diagnostics(case_plan.loads, known_targets))
    diagnostics.extend(_step_diagnostics(case_plan.steps))
    diagnostics.extend(_output_diagnostics(case_plan.output_requests))
    if not case_plan.provenance_comments:
        diagnostics.append(
            _diag(
                CalculiXInpDiagnosticCode.FW_PROVENANCE_INCOMPLETE,
                CalculiXInpSeverity.WARNING,
                "Case plan has no provenance comments for the INP header.",
                source_field="provenance_comments",
                suggested_fix="Preserve source, validator, bridge, and review comments.",
                blocks_render=False,
                blocks_write=False,
            )
        )
    return _dedupe_diagnostics(diagnostics)


def _diagnostic_from_case_plan(diagnostic: Any) -> FEASpecCalculiXInpDiagnostic:
    code_map = {
        CalculiXPlanDiagnosticCode.FC_MESH_REQUIRED: CalculiXInpDiagnosticCode.FW_MESH_REQUIRED,
        CalculiXPlanDiagnosticCode.FC_UNSUPPORTED_ELEMENT_TYPE: (
            CalculiXInpDiagnosticCode.FW_UNSUPPORTED_ELEMENT_TYPE
        ),
        CalculiXPlanDiagnosticCode.FC_MATERIAL_MISSING: (
            CalculiXInpDiagnosticCode.FW_MATERIAL_MISSING
        ),
        CalculiXPlanDiagnosticCode.FC_SECTION_MISSING: (
            CalculiXInpDiagnosticCode.FW_SECTION_MISSING
        ),
        CalculiXPlanDiagnosticCode.FC_BC_INVALID_TARGET: (
            CalculiXInpDiagnosticCode.FW_BC_INVALID_TARGET
        ),
        CalculiXPlanDiagnosticCode.FC_LOAD_INVALID_TARGET: (
            CalculiXInpDiagnosticCode.FW_LOAD_INVALID_TARGET
        ),
        CalculiXPlanDiagnosticCode.FC_LOAD_UNSUPPORTED_TYPE: (
            CalculiXInpDiagnosticCode.FW_LOAD_UNSUPPORTED_TYPE
        ),
        CalculiXPlanDiagnosticCode.FC_STEP_UNSUPPORTED: (
            CalculiXInpDiagnosticCode.FW_STEP_UNSUPPORTED
        ),
        CalculiXPlanDiagnosticCode.FC_OUTPUT_UNSUPPORTED: (
            CalculiXInpDiagnosticCode.FW_OUTPUT_UNSUPPORTED
        ),
        CalculiXPlanDiagnosticCode.FC_PROVENANCE_INCOMPLETE: (
            CalculiXInpDiagnosticCode.FW_PROVENANCE_INCOMPLETE
        ),
    }
    return _diag(
        code_map.get(
            getattr(diagnostic, "code", None),
            CalculiXInpDiagnosticCode.FW_PLAN_NOT_READY,
        ),
        CalculiXInpSeverity.BLOCKER,
        str(getattr(diagnostic, "message", "Case-plan diagnostic blocks rendering.")),
        target_ref=str(getattr(diagnostic, "target_ref", "")),
        source_field=str(getattr(diagnostic, "source_field", "")),
        suggested_fix=str(getattr(diagnostic, "suggested_fix", "")),
    )


def _topology_diagnostics(
    nodes: Sequence[CalculiXCaseNodePlan],
    elements: Sequence[CalculiXCaseElementPlan],
) -> list[FEASpecCalculiXInpDiagnostic]:
    diagnostics: list[FEASpecCalculiXInpDiagnostic] = []
    if not nodes:
        diagnostics.append(
            _diag(
                CalculiXInpDiagnosticCode.FW_NODE_MISSING,
                CalculiXInpSeverity.BLOCKER,
                "INP rendering requires explicit node topology.",
                source_field="nodes",
                suggested_fix="Provide reviewed case-plan nodes.",
            )
        )
    node_ids = {item.node_id for item in nodes}
    if not elements:
        diagnostics.extend(
            [
                _diag(
                    CalculiXInpDiagnosticCode.FW_MESH_REQUIRED,
                    CalculiXInpSeverity.BLOCKER,
                    "INP rendering requires explicit element topology.",
                    source_field="elements",
                    suggested_fix="Provide reviewed element connectivity.",
                ),
                _diag(
                    CalculiXInpDiagnosticCode.FW_ELEMENT_MISSING,
                    CalculiXInpSeverity.BLOCKER,
                    "No element records are available for INP rendering.",
                    source_field="elements",
                    suggested_fix="Provide reviewed element records.",
                ),
            ]
        )
    for element in elements:
        if element.element_type.upper() not in SUPPORTED_ELEMENT_TYPES:
            diagnostics.append(
                _diag(
                    CalculiXInpDiagnosticCode.FW_UNSUPPORTED_ELEMENT_TYPE,
                    CalculiXInpSeverity.BLOCKER,
                    f"Unsupported CalculiX element type {element.element_type!r}.",
                    target_ref=element.element_id,
                    source_field="elements",
                    suggested_fix="Use a supported reviewed CalculiX element type.",
                )
            )
        missing_refs = [ref for ref in element.node_refs if ref not in node_ids]
        if not element.node_refs or missing_refs:
            diagnostics.append(
                _diag(
                    CalculiXInpDiagnosticCode.FW_ELEMENT_MISSING,
                    CalculiXInpSeverity.BLOCKER,
                    "Element connectivity is missing or references unknown nodes.",
                    target_ref=element.element_id,
                    source_field="elements.node_refs",
                    suggested_fix="Review element node references before rendering.",
                )
            )
    return diagnostics


def _material_diagnostics(
    materials: Sequence[CalculiXCaseMaterialPlan],
) -> list[FEASpecCalculiXInpDiagnostic]:
    if not materials:
        return [
            _diag(
                CalculiXInpDiagnosticCode.FW_MATERIAL_MISSING,
                CalculiXInpSeverity.BLOCKER,
                "INP rendering requires at least one reviewed material.",
                source_field="materials",
                suggested_fix="Add explicit isotropic elastic material data.",
            )
        ]
    diagnostics: list[FEASpecCalculiXInpDiagnostic] = []
    for material in materials:
        if _young_modulus(material) is None or _poisson_ratio(material) is None:
            diagnostics.append(
                _diag(
                    CalculiXInpDiagnosticCode.FW_MATERIAL_MISSING,
                    CalculiXInpSeverity.BLOCKER,
                    "Material is missing isotropic elastic properties.",
                    target_ref=material.material_id,
                    source_field="materials.properties",
                    suggested_fix="Provide Young's modulus and Poisson ratio.",
                )
            )
    return diagnostics


def _section_diagnostics(
    sections: Sequence[CalculiXCaseSectionPlan],
    materials: Sequence[CalculiXCaseMaterialPlan],
) -> list[FEASpecCalculiXInpDiagnostic]:
    if not sections:
        return [
            _diag(
                CalculiXInpDiagnosticCode.FW_SECTION_MISSING,
                CalculiXInpSeverity.BLOCKER,
                "INP rendering requires at least one reviewed section.",
                source_field="sections",
                suggested_fix="Add explicit section assignments.",
            )
        ]
    material_ids = {material.material_id for material in materials}
    diagnostics: list[FEASpecCalculiXInpDiagnostic] = []
    for section in sections:
        if section.material_ref and section.material_ref not in material_ids:
            diagnostics.append(
                _diag(
                    CalculiXInpDiagnosticCode.FW_SECTION_MISSING,
                    CalculiXInpSeverity.BLOCKER,
                    "Section references an unknown material.",
                    target_ref=section.section_id,
                    source_field="sections.material_ref",
                    suggested_fix="Map the section to a reviewed material.",
                )
            )
        if not section.target_refs:
            diagnostics.append(
                _diag(
                    CalculiXInpDiagnosticCode.FW_SECTION_MISSING,
                    CalculiXInpSeverity.BLOCKER,
                    "Section has no target element set or element reference.",
                    target_ref=section.section_id,
                    source_field="sections.target_refs",
                    suggested_fix="Provide reviewed section target references.",
                )
            )
    return diagnostics


def _boundary_diagnostics(
    boundary_conditions: Sequence[CalculiXCaseBoundaryConditionPlan],
    known_targets: set[str],
) -> list[FEASpecCalculiXInpDiagnostic]:
    if not boundary_conditions:
        return [
            _diag(
                CalculiXInpDiagnosticCode.FW_BC_INVALID_TARGET,
                CalculiXInpSeverity.BLOCKER,
                "INP rendering requires reviewed boundary conditions.",
                source_field="boundary_conditions",
                suggested_fix="Provide explicit reviewed boundary conditions.",
            )
        ]
    diagnostics: list[FEASpecCalculiXInpDiagnostic] = []
    for condition in boundary_conditions:
        if not condition.target_refs or any(
            target not in known_targets for target in condition.target_refs
        ):
            diagnostics.append(
                _diag(
                    CalculiXInpDiagnosticCode.FW_BC_INVALID_TARGET,
                    CalculiXInpSeverity.BLOCKER,
                    "Boundary condition target is missing or unresolved.",
                    target_ref=condition.bc_id,
                    source_field="boundary_conditions.target_refs",
                    suggested_fix="Retarget the boundary condition to reviewed nodes or sets.",
                )
            )
        if not condition.degrees_of_freedom or any(
            _dof_number(dof) is None for dof in condition.degrees_of_freedom
        ):
            diagnostics.append(
                _diag(
                    CalculiXInpDiagnosticCode.FW_BC_INVALID_TARGET,
                    CalculiXInpSeverity.BLOCKER,
                    "Boundary condition has unsupported degrees of freedom.",
                    target_ref=condition.bc_id,
                    source_field="boundary_conditions.degrees_of_freedom",
                    suggested_fix="Use explicit ux, uy, uz, rx, ry, or rz degrees of freedom.",
                )
            )
    return diagnostics


def _load_diagnostics(
    loads: Sequence[CalculiXCaseLoadPlan],
    known_targets: set[str],
) -> list[FEASpecCalculiXInpDiagnostic]:
    if not loads:
        return [
            _diag(
                CalculiXInpDiagnosticCode.FW_LOAD_INVALID_TARGET,
                CalculiXInpSeverity.BLOCKER,
                "INP rendering requires reviewed loads.",
                source_field="loads",
                suggested_fix="Provide explicit reviewed load records.",
            )
        ]
    diagnostics: list[FEASpecCalculiXInpDiagnostic] = []
    for load in loads:
        kind = load.kind.casefold()
        if kind not in SUPPORTED_FORCE_LOADS | SUPPORTED_PRESSURE_LOADS:
            diagnostics.append(
                _diag(
                    CalculiXInpDiagnosticCode.FW_LOAD_UNSUPPORTED_TYPE,
                    CalculiXInpSeverity.BLOCKER,
                    f"Unsupported load kind {load.kind!r}.",
                    target_ref=load.load_id,
                    source_field="loads.kind",
                    suggested_fix="Use force, point_force, pressure, or distributed load.",
                )
            )
        if not load.target_refs or any(target not in known_targets for target in load.target_refs):
            diagnostics.append(
                _diag(
                    CalculiXInpDiagnosticCode.FW_LOAD_INVALID_TARGET,
                    CalculiXInpSeverity.BLOCKER,
                    "Load target is missing or unresolved.",
                    target_ref=load.load_id,
                    source_field="loads.target_refs",
                    suggested_fix="Retarget the load to reviewed nodes, elements, or sets.",
                )
            )
        if kind in SUPPORTED_FORCE_LOADS and not load.vector and not load.magnitude:
            diagnostics.append(
                _diag(
                    CalculiXInpDiagnosticCode.FW_LOAD_UNSUPPORTED_TYPE,
                    CalculiXInpSeverity.BLOCKER,
                    "Force load requires vector or magnitude data.",
                    target_ref=load.load_id,
                    source_field="loads.vector",
                    suggested_fix="Provide reviewed force components.",
                )
            )
    return diagnostics


def _step_diagnostics(
    steps: Sequence[CalculiXCaseStepPlan],
) -> list[FEASpecCalculiXInpDiagnostic]:
    if not steps:
        return [
            _diag(
                CalculiXInpDiagnosticCode.FW_STEP_UNSUPPORTED,
                CalculiXInpSeverity.BLOCKER,
                "INP rendering requires an explicit static step plan.",
                source_field="steps",
                suggested_fix="Add a reviewed static step record.",
            )
        ]
    diagnostics: list[FEASpecCalculiXInpDiagnostic] = []
    for step in steps:
        if step.analysis_type.casefold() not in SUPPORTED_STEP_TYPES or step.nonlinear:
            diagnostics.append(
                _diag(
                    CalculiXInpDiagnosticCode.FW_STEP_UNSUPPORTED,
                    CalculiXInpSeverity.BLOCKER,
                    "Only static linear steps are supported by the FEASpec renderer.",
                    target_ref=step.step_id,
                    source_field="steps.analysis_type",
                    suggested_fix="Use static linear step metadata.",
                )
            )
    return diagnostics


def _output_diagnostics(
    output_requests: Sequence[CalculiXCaseOutputRequestPlan],
) -> list[FEASpecCalculiXInpDiagnostic]:
    if not output_requests:
        return [
            _diag(
                CalculiXInpDiagnosticCode.FW_OUTPUT_UNSUPPORTED,
                CalculiXInpSeverity.BLOCKER,
                "INP rendering requires at least one output request.",
                source_field="output_requests",
                suggested_fix="Add displacement or stress output metadata.",
            )
        ]
    diagnostics: list[FEASpecCalculiXInpDiagnostic] = []
    for request in output_requests:
        variables = {variable.upper() for variable in request.variables}
        if not variables or not variables.issubset(SUPPORTED_OUTPUT_VARIABLES):
            diagnostics.append(
                _diag(
                    CalculiXInpDiagnosticCode.FW_OUTPUT_UNSUPPORTED,
                    CalculiXInpSeverity.BLOCKER,
                    "Output request contains unsupported variables.",
                    target_ref=request.request_id,
                    source_field="output_requests.variables",
                    suggested_fix="Use U and S output variables for the initial renderer.",
                )
            )
    return diagnostics


def _header_section(case_plan: FEASpecCalculiXCasePlan) -> CalculiXInpSection:
    lines = [
        "** OpenSolver Workbench experimental FEASpec CalculiX INP renderer",
        f"** Case plan: {case_plan.case_id}",
        f"** Source FEASpec: {case_plan.source_feaspec_id or 'unknown'}",
        "** This file is generated from experimental, human-reviewed FEASpec evidence.",
        "** No industrial certification, compliance, production CAE, or accuracy claim.",
        "** Solver execution was not performed by this renderer.",
    ]
    unit_context = ", ".join(
        f"{key}={value}" for key, value in sorted(case_plan.unit_context.items())
    )
    if unit_context:
        lines.append(f"** Unit context: {unit_context}")
    for comment in case_plan.provenance_comments:
        safe_comment = str(comment).replace("\n", " ").strip()
        if safe_comment:
            lines.append(f"** Provenance: {safe_comment}")
    return CalculiXInpSection(
        "header/provenance comments",
        tuple(lines),
        (case_plan.case_id, case_plan.source_feaspec_id),
    )


def _node_section(nodes: Sequence[CalculiXCaseNodePlan]) -> CalculiXInpSection:
    lines = ["*NODE"]
    source_refs: list[str] = []
    for node in sorted(nodes, key=lambda item: _sort_key(item.node_id)):
        coords = _coordinates_3d(node.coordinates)
        lines.append(
            f"{node.node_id}, {_format_number(coords[0])}, "
            f"{_format_number(coords[1])}, {_format_number(coords[2])}"
        )
        source_refs.append(node.source_ref or node.node_id)
    return CalculiXInpSection("*NODE", tuple(lines), tuple(source_refs))


def _element_section(
    elements: Sequence[CalculiXCaseElementPlan],
) -> CalculiXInpSection:
    lines: list[str] = []
    source_refs: list[str] = []
    current_header = ""
    for element in sorted(elements, key=lambda item: _sort_key(item.element_id)):
        element_set = str(element.metadata.get("element_set", "EALL") or "EALL")
        header = f"*ELEMENT, TYPE={element.element_type.upper()}, ELSET={element_set}"
        if header != current_header:
            lines.append(header)
            current_header = header
        lines.append(f"{element.element_id}, {', '.join(element.node_refs)}")
        source_refs.append(element.source_ref or element.element_id)
    return CalculiXInpSection("*ELEMENT", tuple(lines), tuple(source_refs))


def _material_section(
    materials: Sequence[CalculiXCaseMaterialPlan],
) -> CalculiXInpSection:
    lines: list[str] = []
    source_refs: list[str] = []
    for material in sorted(materials, key=lambda item: _sort_key(item.material_id)):
        lines.extend(
            [
                f"*MATERIAL, NAME={material.material_id}",
                "** FEASpec material model: "
                f"{material.model or material.name or material.material_id}",
                "*ELASTIC",
                (
                    f"{_format_number(_young_modulus(material))}, "
                    f"{_format_number(_poisson_ratio(material))}"
                ),
            ]
        )
        density = _property_value(material.properties, ("density", "rho"))
        if density is not None:
            lines.extend(["*DENSITY", _format_number(density)])
        source_refs.append(material.source_ref or material.material_id)
    return CalculiXInpSection("material cards", tuple(lines), tuple(source_refs))


def _section_property_section(
    sections: Sequence[CalculiXCaseSectionPlan],
    materials: Sequence[CalculiXCaseMaterialPlan],
) -> CalculiXInpSection:
    material_fallback = materials[0].material_id if materials else "UNASSIGNED"
    lines: list[str] = []
    source_refs: list[str] = []
    for section in sorted(sections, key=lambda item: _sort_key(item.section_id)):
        material_ref = section.material_ref or material_fallback
        for target_ref in section.target_refs:
            section_type = section.section_type.casefold()
            if section_type in {"beam", "truss", "shell"}:
                lines.append(
                    f"** FEASpec {section.section_type} section {section.section_id}"
                )
            lines.append(
                f"*SOLID SECTION, ELSET={target_ref}, MATERIAL={material_ref}"
            )
        source_refs.append(section.source_ref or section.section_id)
    return CalculiXInpSection("section/property cards", tuple(lines), tuple(source_refs))


def _boundary_section(
    boundary_conditions: Sequence[CalculiXCaseBoundaryConditionPlan],
) -> CalculiXInpSection:
    lines = ["*BOUNDARY"]
    source_refs: list[str] = []
    for condition in sorted(boundary_conditions, key=lambda item: _sort_key(item.bc_id)):
        values = list(condition.values)
        for target_ref in condition.target_refs:
            for index, dof in enumerate(condition.degrees_of_freedom):
                dof_number = _dof_number(dof)
                if dof_number is None:
                    continue
                value = values[index] if index < len(values) else 0.0
                lines.append(
                    f"{target_ref}, {dof_number}, {dof_number}, {_format_number(value)}"
                )
        source_refs.append(condition.source_ref or condition.bc_id)
    return CalculiXInpSection("boundary cards", tuple(lines), tuple(source_refs))


def _load_section(loads: Sequence[CalculiXCaseLoadPlan]) -> CalculiXInpSection:
    force_lines: list[str] = []
    pressure_lines: list[str] = []
    source_refs: list[str] = []
    for load in sorted(loads, key=lambda item: _sort_key(item.load_id)):
        kind = load.kind.casefold()
        if kind in SUPPORTED_FORCE_LOADS:
            components = _force_components(load)
            for target_ref in load.target_refs:
                for dof, value in enumerate(components, start=1):
                    if value:
                        force_lines.append(f"{target_ref}, {dof}, {_format_number(value)}")
        elif kind in SUPPORTED_PRESSURE_LOADS:
            pressure_value = _load_scalar(load)
            for target_ref in load.target_refs:
                pressure_lines.append(f"{target_ref}, P, {_format_number(pressure_value)}")
        source_refs.append(load.source_ref or load.load_id)
    lines: list[str] = []
    if force_lines:
        lines.append("*CLOAD")
        lines.extend(force_lines)
    if pressure_lines:
        lines.append("*DLOAD")
        lines.extend(pressure_lines)
    return CalculiXInpSection("load cards", tuple(lines), tuple(source_refs))


def _step_section(steps: Sequence[CalculiXCaseStepPlan]) -> CalculiXInpSection:
    step = sorted(steps, key=lambda item: _sort_key(item.step_id))[0]
    return CalculiXInpSection(
        "*STEP",
        (
            f"*STEP, NAME={step.step_id}",
            "*STATIC",
        ),
        (step.step_id,),
    )


def _output_section(
    output_requests: Sequence[CalculiXCaseOutputRequestPlan],
) -> CalculiXInpSection:
    variables = {
        variable.upper()
        for request in output_requests
        for variable in request.variables
    }
    lines: list[str] = []
    if "U" in variables:
        lines.extend(["*NODE PRINT, NSET=NALL", "U"])
    if "S" in variables:
        lines.extend(["*EL PRINT, ELSET=EALL", "S"])
    return CalculiXInpSection(
        "output request cards",
        tuple(lines),
        tuple(request.request_id for request in output_requests),
    )


def _sections_to_text(sections: Sequence[CalculiXInpSection]) -> str:
    lines: list[str] = []
    for section in sections:
        lines.extend(section.lines)
    return "\n".join(lines) + "\n"


def _known_targets(case_plan: FEASpecCalculiXCasePlan) -> set[str]:
    targets = {"NALL", "EALL"}
    targets.update(node.node_id for node in case_plan.nodes)
    targets.update(element.element_id for element in case_plan.elements)
    targets.update(
        str(element.metadata.get("element_set", ""))
        for element in case_plan.elements
        if element.metadata.get("element_set")
    )
    for section in case_plan.sections:
        targets.update(section.target_refs)
    return {target for target in targets if target}


def _coordinates_3d(values: Sequence[Any]) -> tuple[Any, Any, Any]:
    coords = list(values[:3])
    while len(coords) < 3:
        coords.append(0.0)
    return (coords[0], coords[1], coords[2])


def _young_modulus(material: CalculiXCaseMaterialPlan) -> Any:
    return _property_value(
        material.properties,
        ("young_modulus", "youngs_modulus", "elastic_modulus", "E"),
    )


def _poisson_ratio(material: CalculiXCaseMaterialPlan) -> Any:
    return _property_value(material.properties, ("poisson_ratio", "nu"))


def _property_value(properties: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = properties.get(key)
        if isinstance(value, dict):
            for nested_key in ("value", "magnitude"):
                if nested_key in value:
                    return value[nested_key]
        if value is not None:
            return value
    return None


def _load_scalar(load: CalculiXCaseLoadPlan) -> Any:
    for payload in (load.magnitude, load.units):
        for key in ("value", "magnitude", "pressure"):
            if key in payload:
                return payload[key]
    return load.vector[0] if load.vector else 0.0


def _force_components(load: CalculiXCaseLoadPlan) -> tuple[Any, Any, Any]:
    if load.vector:
        return _coordinates_3d(load.vector)
    value = _property_value(load.magnitude, ("value", "magnitude", "force"))
    direction = load.direction.casefold()
    components = [0.0, 0.0, 0.0]
    dof = {"x": 0, "ux": 0, "fx": 0, "y": 1, "uy": 1, "fy": 1, "z": 2, "uz": 2, "fz": 2}.get(
        direction,
        0,
    )
    components[dof] = value if value is not None else 0.0
    return (components[0], components[1], components[2])


def _dof_number(value: str) -> int | None:
    normalized = str(value).casefold()
    if normalized.isdigit():
        number = int(normalized)
        return number if 1 <= number <= 6 else None
    return {
        "ux": 1,
        "x": 1,
        "uy": 2,
        "y": 2,
        "uz": 3,
        "z": 3,
        "rx": 4,
        "ry": 5,
        "rz": 6,
    }.get(normalized)


def _format_number(value: Any) -> str:
    try:
        return f"{float(value):.12g}"
    except (TypeError, ValueError):
        return str(value)


def _sort_key(value: str) -> tuple[int, Any]:
    text = str(value)
    return (0, int(text)) if text.isdigit() else (1, text)


def _diag(
    code: CalculiXInpDiagnosticCode,
    severity: CalculiXInpSeverity,
    message: str,
    *,
    target_ref: str = "",
    source_field: str = "",
    suggested_fix: str = "",
    blocks_render: bool | None = None,
    blocks_write: bool | None = None,
) -> FEASpecCalculiXInpDiagnostic:
    return FEASpecCalculiXInpDiagnostic.make(
        code,
        severity,
        message,
        target_ref=target_ref,
        source_field=source_field,
        suggested_fix=suggested_fix,
        blocks_render=blocks_render,
        blocks_write=blocks_write,
    )


def _dedupe_diagnostics(
    diagnostics: Sequence[FEASpecCalculiXInpDiagnostic],
) -> list[FEASpecCalculiXInpDiagnostic]:
    seen: set[tuple[CalculiXInpDiagnosticCode, str, str]] = set()
    unique: list[FEASpecCalculiXInpDiagnostic] = []
    for diagnostic in diagnostics:
        key = (diagnostic.code, diagnostic.target_ref, diagnostic.source_field)
        if key not in seen:
            seen.add(key)
            unique.append(diagnostic)
    return unique
