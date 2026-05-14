"""Basic SU2 configuration generation for prepare-only v0.1 workflows."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


class Su2ConfigError(ValueError):
    """Raised when a SU2 config cannot be generated safely."""


_CASE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
_SAFE_PATH_REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9_./\\:-]+$")
_SAFE_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]+$")
_SUPPORTED_SOLVERS = {"EULER", "NAVIER_STOKES"}
_SUPPORTED_MATH_PROBLEMS = {"DIRECT"}


@dataclass(frozen=True)
class Su2BoundaryConfig:
    """Boundary marker handoff for a minimal SU2 case."""

    euler_markers: tuple[str, ...] = ("wall",)
    farfield_markers: tuple[str, ...] = ("farfield",)
    inlet_markers: tuple[str, ...] = ()
    outlet_markers: tuple[str, ...] = ()


@dataclass(frozen=True)
class Su2SimulationConfig:
    """Small, explicit config model for the OSW SU2 adapter."""

    case_name: str = "basic_euler"
    mesh_filename: str = "mesh.su2"
    solver: str = "EULER"
    math_problem: str = "DIRECT"
    turbulence_model: str = "NONE"
    mach_number: float = 0.5
    aoa_degrees: float = 2.0
    sideslip_degrees: float = 0.0
    reference_frame: str = "su2_nondimensional"
    reference_length: float = 1.0
    reference_area: float = 1.0
    reference_origin: tuple[float, float, float] = (0.0, 0.0, 0.0)
    max_iterations: int = 100
    convergence_filename: str = "history"
    output_write_frequency: int = 10
    boundaries: Su2BoundaryConfig = field(default_factory=Su2BoundaryConfig)


@dataclass(frozen=True)
class Su2GeneratedConfig:
    """Prepared SU2 config artifact metadata."""

    path: Path
    mesh_reference: str
    warnings: tuple[str, ...] = ()


class Su2ConfigGenerator:
    """Generate a deterministic SU2 `.cfg` file for review and external use."""

    def __init__(self, config: Su2SimulationConfig) -> None:
        self.config = config

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.config.case_name.strip():
            errors.append("SU2 case name is required.")
        elif not _CASE_NAME_PATTERN.match(self.config.case_name):
            errors.append(
                "SU2 case name may contain only letters, numbers, dots, hyphens, "
                "and underscores."
            )

        if not self.config.mesh_filename.strip():
            errors.append("SU2 mesh filename is required; provide a .su2 mesh reference.")
        elif not _is_safe_path_reference(self.config.mesh_filename):
            errors.append(
                "SU2 mesh filename contains unsupported characters; use a plain path "
                "reference without whitespace, control characters, or SU2 directives."
            )

        if not self.config.convergence_filename.strip():
            errors.append("SU2 convergence filename is required.")
        elif not _is_safe_token(self.config.convergence_filename):
            errors.append(
                "SU2 convergence filename contains unsupported characters; use a plain "
                "token without whitespace, control characters, or SU2 directives."
            )

        solver = self.config.solver.upper()
        if solver not in _SUPPORTED_SOLVERS:
            allowed = ", ".join(sorted(_SUPPORTED_SOLVERS))
            errors.append(f"SU2 solver {self.config.solver!r} is unsupported; expected {allowed}.")

        math_problem = self.config.math_problem.upper()
        if math_problem not in _SUPPORTED_MATH_PROBLEMS:
            errors.append("OSW v0.1 SU2 adapter supports only MATH_PROBLEM= DIRECT.")

        if self.config.max_iterations <= 0:
            errors.append("SU2 ITER must be greater than zero.")
        if self.config.output_write_frequency <= 0:
            errors.append("SU2 OUTPUT_WRT_FREQ must be greater than zero.")
        if not self.config.boundaries.euler_markers and not self.config.boundaries.farfield_markers:
            errors.append("At least one SU2 boundary marker group is required.")
        for marker in _all_markers(self.config.boundaries):
            if not marker.strip() or not _is_safe_token(marker):
                errors.append(
                    "SU2 boundary marker contains unsupported characters; use plain "
                    "marker names without whitespace, control characters, or SU2 syntax."
                )
                break
        if self.config.reference_frame != "su2_nondimensional":
            errors.append("SU2 reference_frame must be 'su2_nondimensional' for v0.1.")
        return tuple(errors)

    def assumptions(self) -> str:
        return (
            "Reference length, area, and origin are SU2 nondimensional reference "
            "values used directly in the generated configuration."
        )

    def generate(self) -> str:
        errors = self.validate()
        if errors:
            raise Su2ConfigError("; ".join(errors))

        config = self.config
        lines = [
            "% OpenSolver Workbench SU2 config",
            "% v0.1 basic adapter: prepares standard SU2 input only.",
            f"SOLVER= {config.solver.upper()}",
            f"MATH_PROBLEM= {config.math_problem.upper()}",
            f"KIND_TURB_MODEL= {config.turbulence_model.upper()}",
            f"MESH_FILENAME= {config.mesh_filename}",
            "MESH_FORMAT= SU2",
            f"MACH_NUMBER= {_format_number(config.mach_number)}",
            f"AOA= {_format_number(config.aoa_degrees)}",
            f"SIDESLIP_ANGLE= {_format_number(config.sideslip_degrees)}",
            f"REF_LENGTH= {_format_number(config.reference_length)}",
            f"REF_AREA= {_format_number(config.reference_area)}",
            f"REF_ORIGIN_MOMENT_X= {_format_number(config.reference_origin[0])}",
            f"REF_ORIGIN_MOMENT_Y= {_format_number(config.reference_origin[1])}",
            f"REF_ORIGIN_MOMENT_Z= {_format_number(config.reference_origin[2])}",
        ]
        lines.extend(_marker_lines(config.boundaries))
        lines.extend(
            [
                f"CONV_FILENAME= {config.convergence_filename}",
                "OUTPUT_FILES= ( RESTART, PARAVIEW )",
                f"OUTPUT_WRT_FREQ= {config.output_write_frequency}",
                "SCREEN_OUTPUT= (INNER_ITER, RMS_DENSITY, RMS_ENERGY)",
                f"ITER= {config.max_iterations}",
            ]
        )
        return "\n".join(lines) + "\n"

    def write(self, output_dir: str | Path) -> Su2GeneratedConfig:
        text = self.generate()
        output_path = Path(output_dir).expanduser()
        output_path.mkdir(parents=True, exist_ok=True)
        config_path = output_path / f"{self.config.case_name}.cfg"
        config_path.write_text(text, encoding="utf-8")
        return Su2GeneratedConfig(
            path=config_path,
            mesh_reference=self.config.mesh_filename,
        )


def generate_su2_config(config: Su2SimulationConfig) -> str:
    return Su2ConfigGenerator(config).generate()


def _marker_lines(boundaries: Su2BoundaryConfig) -> list[str]:
    lines: list[str] = []
    if boundaries.euler_markers:
        lines.append(f"MARKER_EULER= { _format_marker_tuple(boundaries.euler_markers) }")
    if boundaries.farfield_markers:
        lines.append(f"MARKER_FAR= { _format_marker_tuple(boundaries.farfield_markers) }")
    if boundaries.inlet_markers:
        lines.append(f"MARKER_INLET= { _format_marker_tuple(boundaries.inlet_markers) }")
    if boundaries.outlet_markers:
        lines.append(f"MARKER_OUTLET= { _format_marker_tuple(boundaries.outlet_markers) }")
    return lines


def _all_markers(boundaries: Su2BoundaryConfig) -> tuple[str, ...]:
    return (
        *boundaries.euler_markers,
        *boundaries.farfield_markers,
        *boundaries.inlet_markers,
        *boundaries.outlet_markers,
    )


def _format_marker_tuple(markers: tuple[str, ...]) -> str:
    return f"( {' '.join(markers)} )"


def _format_number(value: float) -> str:
    return f"{value:.12g}"


def _is_safe_path_reference(value: str) -> bool:
    return _SAFE_PATH_REFERENCE_PATTERN.match(value) is not None


def _is_safe_token(value: str) -> bool:
    return _SAFE_TOKEN_PATTERN.match(value) is not None
