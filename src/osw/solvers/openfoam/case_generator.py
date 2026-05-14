"""OpenFOAM lid-driven cavity template generation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from string import Template

from osw.core.validation import ValidationReport


class OpenFoamCaseTemplateError(ValueError):
    """Raised when a template case cannot be generated safely."""


@dataclass(frozen=True)
class OpenFoamBoundaryConfig:
    """Patch names and lid velocity used by the simple cavity template."""

    moving_wall: str = "movingWall"
    fixed_walls: tuple[str, ...] = ("fixedWalls",)
    front_and_back: str = "frontAndBack"
    lid_velocity: tuple[float, float, float] = (1.0, 0.0, 0.0)


@dataclass(frozen=True)
class OpenFoamCavityConfig:
    """Bounded OpenFOAM lid-driven cavity case parameters."""

    case_name: str = "cavity"
    length: float = 0.1
    z_thickness: float = 0.01
    cells: tuple[int, int, int] = (20, 20, 1)
    viscosity: float = 0.01
    end_time: float = 1.0
    delta_t: float = 0.005
    write_interval: float = 0.1
    boundaries: OpenFoamBoundaryConfig | None = field(default_factory=OpenFoamBoundaryConfig)


@dataclass(frozen=True)
class OpenFoamGeneratedCase:
    """Generated case directory metadata."""

    root: Path
    files: tuple[Path, ...]
    warnings: tuple[str, ...] = ()

    @property
    def relative_paths(self) -> tuple[str, ...]:
        return tuple(path.relative_to(self.root).as_posix() for path in self.files)


class OpenFoamCaseGenerator:
    """Render a deterministic OpenFOAM cavity case without running OpenFOAM."""

    template_root = Path(__file__).with_name("templates") / "cavity"
    template_paths: tuple[str, ...] = (
        "0/U",
        "0/p",
        "constant/transportProperties",
        "system/blockMeshDict",
        "system/controlDict",
        "system/fvSchemes",
        "system/fvSolution",
    )

    def validate(self, config: OpenFoamCavityConfig) -> ValidationReport:
        report = ValidationReport()
        if not config.case_name or not _SAFE_CASE_NAME.match(config.case_name):
            report.add_error(
                "case_name",
                "Case name must contain only letters, numbers, underscores, or hyphens.",
            )
        if config.length <= 0:
            report.add_error("length", "Cavity length must be positive.")
        if config.z_thickness <= 0:
            report.add_error("z_thickness", "Cavity z thickness must be positive.")
        if len(config.cells) != 3 or any(count <= 0 for count in config.cells):
            report.add_error("cells", "Cavity cell counts must be three positive integers.")
        if config.viscosity <= 0:
            report.add_error("viscosity", "Kinematic viscosity must be positive.")
        if config.end_time <= 0:
            report.add_error("end_time", "End time must be positive.")
        if config.delta_t <= 0:
            report.add_error("delta_t", "Time step must be positive.")
        if config.write_interval <= 0:
            report.add_error("write_interval", "Write interval must be positive.")

        if config.boundaries is None:
            report.add_warning(
                "boundaries",
                "Boundary configuration is missing; default lid-driven cavity boundaries "
                "will be used.",
            )
        else:
            _validate_boundary_config(config.boundaries, report)
        return report

    def generate(
        self,
        config: OpenFoamCavityConfig,
        output_dir: str | Path,
    ) -> OpenFoamGeneratedCase:
        report = self.validate(config)
        if report.has_errors:
            raise OpenFoamCaseTemplateError(report.friendly_summary())

        boundaries = config.boundaries or OpenFoamBoundaryConfig()
        root = Path(output_dir) / config.case_name
        rendered_files: list[Path] = []
        context = _template_context(config, boundaries)
        for relative_path in self.template_paths:
            destination = root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                self._render_template(relative_path, context),
                encoding="utf-8",
            )
            rendered_files.append(destination)

        warnings = tuple(
            message.message for message in report.messages if message.severity == "warning"
        )
        return OpenFoamGeneratedCase(root=root, files=tuple(rendered_files), warnings=warnings)

    def _render_template(self, relative_path: str, context: dict[str, str]) -> str:
        template_path = self.template_root / relative_path
        if template_path.exists():
            text = template_path.read_text(encoding="utf-8")
        else:
            text = _EMBEDDED_TEMPLATES[relative_path]
        return Template(text).safe_substitute(context)


def generate_cavity_case(
    config: OpenFoamCavityConfig,
    output_dir: str | Path,
) -> OpenFoamGeneratedCase:
    return OpenFoamCaseGenerator().generate(config, output_dir)


def _validate_boundary_config(
    boundaries: OpenFoamBoundaryConfig,
    report: ValidationReport,
) -> None:
    if not boundaries.moving_wall:
        report.add_error("boundaries.moving_wall", "Moving wall patch name is required.")
    if not boundaries.fixed_walls or any(not patch for patch in boundaries.fixed_walls):
        report.add_error(
            "boundaries.fixed_walls",
            "At least one fixed wall patch name is required.",
        )
    if not boundaries.front_and_back:
        report.add_error("boundaries.front_and_back", "Front/back patch name is required.")
    if len(boundaries.lid_velocity) != 3:
        report.add_error("boundaries.lid_velocity", "Lid velocity must have three components.")


def _template_context(
    config: OpenFoamCavityConfig,
    boundaries: OpenFoamBoundaryConfig,
) -> dict[str, str]:
    fixed_walls = boundaries.fixed_walls[0]
    return {
        "case_name": config.case_name,
        "length": _format_float(config.length),
        "z_thickness": _format_float(config.z_thickness),
        "cells_x": str(int(config.cells[0])),
        "cells_y": str(int(config.cells[1])),
        "cells_z": str(int(config.cells[2])),
        "viscosity": _format_float(config.viscosity),
        "end_time": _format_float(config.end_time),
        "delta_t": _format_float(config.delta_t),
        "write_interval": _format_float(config.write_interval),
        "moving_wall": boundaries.moving_wall,
        "fixed_walls": fixed_walls,
        "front_and_back": boundaries.front_and_back,
        "lid_velocity": _format_vector(boundaries.lid_velocity),
    }


def _format_vector(values: tuple[float, float, float]) -> str:
    return f"({_format_float(values[0])} {_format_float(values[1])} {_format_float(values[2])})"


def _format_float(value: float) -> str:
    return f"{float(value):.12g}"


_SAFE_CASE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")

_EMBEDDED_TEMPLATES: dict[str, str] = {
    "0/U": """FoamFile
{
    version     2.0;
    format      ascii;
    class       volVectorField;
    object      U;
}

dimensions      [0 1 -1 0 0 0 0];

internalField   uniform (0 0 0);

boundaryField
{
    $moving_wall
    {
        type        fixedValue;
        value       uniform $lid_velocity;
    }
    $fixed_walls
    {
        type        fixedValue;
        value       uniform (0 0 0);
    }
    $front_and_back
    {
        type        empty;
    }
}
""",
    "0/p": """FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      p;
}

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform 0;

boundaryField
{
    $moving_wall
    {
        type        zeroGradient;
    }
    $fixed_walls
    {
        type        zeroGradient;
    }
    $front_and_back
    {
        type        empty;
    }
}
""",
    "constant/transportProperties": """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      transportProperties;
}

transportModel  Newtonian;

nu              [0 2 -1 0 0 0 0] $viscosity;
""",
    "system/blockMeshDict": """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}

convertToMeters 1;

vertices
(
    (0 0 0)
    ($length 0 0)
    ($length $length 0)
    (0 $length 0)
    (0 0 $z_thickness)
    ($length 0 $z_thickness)
    ($length $length $z_thickness)
    (0 $length $z_thickness)
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ($cells_x $cells_y $cells_z) simpleGrading (1 1 1)
);

edges
(
);

boundary
(
    $moving_wall
    {
        type wall;
        faces
        (
            (3 7 6 2)
        );
    }
    $fixed_walls
    {
        type wall;
        faces
        (
            (0 4 7 3)
            (2 6 5 1)
            (1 5 4 0)
        );
    }
    $front_and_back
    {
        type empty;
        faces
        (
            (0 3 2 1)
            (4 5 6 7)
        );
    }
);

mergePatchPairs
(
);
""",
    "system/controlDict": """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      controlDict;
}

application     icoFoam;

startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         $end_time;

deltaT          $delta_t;

writeControl    runTime;
writeInterval   $write_interval;

purgeWrite      0;
writeFormat     ascii;
writePrecision  6;
writeCompression off;
timeFormat      general;
timePrecision   6;

runTimeModifiable true;
""",
    "system/fvSchemes": """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      fvSchemes;
}

ddtSchemes
{
    default         Euler;
}

gradSchemes
{
    default         Gauss linear;
}

divSchemes
{
    default         none;
    div(phi,U)      Gauss linear;
}

laplacianSchemes
{
    default         Gauss linear orthogonal;
}

interpolationSchemes
{
    default         linear;
}

snGradSchemes
{
    default         orthogonal;
}
""",
    "system/fvSolution": """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      fvSolution;
}

solvers
{
    p
    {
        solver          PCG;
        preconditioner  DIC;
        tolerance       1e-06;
        relTol          0.05;
    }

    U
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-05;
        relTol          0;
    }
}

PISO
{
    nCorrectors     2;
    nNonOrthogonalCorrectors 0;
    pRefCell        0;
    pRefValue       0;
}
""",
}
