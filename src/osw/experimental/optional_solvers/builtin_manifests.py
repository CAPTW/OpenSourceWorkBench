"""Built-in optional solver manifest fixtures.

The built-ins are declarative metadata. They do not discover tools, import
optional packages, install dependencies, or execute solver health checks.
"""

from __future__ import annotations

from .manifest_models import (
    OptionalSolverManifest,
    OptionalSolverStackId,
    parse_optional_solver_manifest_dict,
)

_DISCLAIMER = (
    "External solvers and optional science packages are not bundled by "
    "OpenSolver Workbench."
)
_COMMON_DOCS = (
    "docs/experimental/optional_solver_manifest_ux_design.md",
    "docs/validation/live_optional_validation_matrix_v0_1_5rc1.md",
    "docs/validation/live_optional_validation_environment_plan.md",
)
_COMMON_SAFETY = (
    "No solver install is performed by this manifest.",
    "No dependency install is performed by this manifest.",
    "No bundled solver is provided by OpenSolver Workbench.",
    "No solver execution is performed by manifest parsing or validation.",
    "No certification claim is made.",
)

_BUILTIN_MANIFEST_DATA: tuple[dict[str, object], ...] = (
    {
        "stack_id": OptionalSolverStackId.GMSH.value,
        "display_name": "Gmsh",
        "related_issue": 6,
        "capabilities": [
            {
                "capability_id": "mesh_generation",
                "description": (
                    "Generate or inspect small educational meshes when Gmsh "
                    "is already installed."
                ),
            },
            {
                "capability_id": "mesh_exchange",
                "description": "Pair with meshio for prepared-machine mesh round-trip validation.",
            },
        ],
        "executable_requirements": [
            {
                "identifier": "gmsh",
                "display_name": "Gmsh executable",
                "notes": ["Required for executable-based prepared validation."],
            }
        ],
        "python_package_requirements": [
            {
                "identifier": "gmsh",
                "display_name": "Gmsh Python package",
                "required": False,
                "notes": ["Alternative supported path for prepared validation."],
            },
            {
                "identifier": "meshio",
                "display_name": "meshio",
                "required": False,
                "notes": ["Optional readback companion for generated meshes."],
            },
        ],
        "version_probe": {
            "name": "gmsh version",
            "command": ["gmsh", "--version"],
            "description": "Declarative version probe for a prepared machine.",
        },
        "help_probe": {
            "name": "gmsh help",
            "command": ["gmsh", "--help"],
            "description": "Declarative help probe for a prepared machine.",
        },
        "smoke_test_description": (
            "Generate a tiny geometry/mesh or run a Python-package mesh smoke "
            "under an ignored artifact directory."
        ),
        "prepared_machine_notes": [
            "Run only where Gmsh is already installed.",
            "Keep generated mesh evidence under artifacts/validation.",
        ],
        "platform_notes": ["Executable and Python-package availability vary by platform."],
        "documentation_refs": _COMMON_DOCS,
        "support_status": "experimental",
        "non_bundled_disclaimer": _DISCLAIMER,
        "safety_notes": _COMMON_SAFETY,
    },
    {
        "stack_id": OptionalSolverStackId.OCTAVE.value,
        "display_name": "GNU Octave",
        "related_issue": 7,
        "capabilities": [
            {
                "capability_id": "safe_script_smoke",
                "description": "Run bounded safe fixture scripts when Octave is already installed.",
            },
            {
                "capability_id": "figure_capture_validation",
                "description": "Support future prepared-machine FigureDataset validation evidence.",
            },
        ],
        "executable_requirements": [
            {"identifier": "octave-cli", "display_name": "GNU Octave CLI"},
            {
                "identifier": "octave",
                "display_name": "GNU Octave executable",
                "required": False,
            },
        ],
        "version_probe": {
            "name": "octave version",
            "command": ["octave-cli", "--version"],
            "description": "Declarative version probe for a prepared machine.",
        },
        "help_probe": {
            "name": "octave help",
            "command": ["octave-cli", "--help"],
            "description": "Declarative help probe for a prepared machine.",
        },
        "smoke_test_description": (
            "Run a minimal safe arithmetic/script smoke with timeout and "
            "captured output."
        ),
        "prepared_machine_notes": [
            "Run only where octave or octave-cli is already installed.",
            "Do not auto-run arbitrary user .m scripts.",
        ],
        "platform_notes": ["Executable naming can differ between local installations."],
        "documentation_refs": _COMMON_DOCS,
        "support_status": "experimental",
        "non_bundled_disclaimer": _DISCLAIMER,
        "safety_notes": _COMMON_SAFETY,
    },
    {
        "stack_id": OptionalSolverStackId.CALCULIX.value,
        "display_name": "CalculiX ccx",
        "related_issue": 8,
        "capabilities": [
            {
                "capability_id": "installed_only_run_gate",
                "description": (
                    "Run the bounded FEASpec CalculiX gate only when ccx is "
                    "already installed."
                ),
            },
            {
                "capability_id": "result_import_evidence",
                "description": "Support future installed-only DAT/STA/FRD evidence collection.",
            },
        ],
        "executable_requirements": [
            {"identifier": "ccx", "display_name": "CalculiX ccx executable"}
        ],
        "version_probe": {
            "name": "ccx version",
            "command": ["ccx", "-v"],
            "description": "Declarative version probe for a prepared machine.",
        },
        "help_probe": {
            "name": "ccx help",
            "command": ["ccx"],
            "description": "Declarative help/banner probe for a prepared machine.",
        },
        "smoke_test_description": (
            "Run the existing installed-only FEASpec CalculiX run gate "
            "against a safe isolated bundle."
        ),
        "prepared_machine_notes": [
            "Run only where ccx is already installed.",
            "Keep run logs and result artifacts under ignored validation directories.",
        ],
        "platform_notes": ["ccx binary naming and PATH configuration can vary."],
        "documentation_refs": _COMMON_DOCS
        + ("docs/validation/live_calculix_run_gate_validation_v0_1_4rc1.md",),
        "support_status": "experimental",
        "non_bundled_disclaimer": _DISCLAIMER,
        "safety_notes": _COMMON_SAFETY,
    },
    {
        "stack_id": OptionalSolverStackId.OPENFOAM.value,
        "display_name": "OpenFOAM",
        "related_issue": 9,
        "capabilities": [
            {
                "capability_id": "template_case_validation",
                "description": (
                    "Validate a tiny OpenFOAM template case only from an "
                    "initialized prepared environment."
                ),
            },
            {
                "capability_id": "residual_log_summary",
                "description": "Support future residual/log parsing evidence for bounded cases.",
            },
        ],
        "executable_requirements": [
            {"identifier": "foamVersion", "display_name": "OpenFOAM version command"},
            {"identifier": "blockMesh", "display_name": "OpenFOAM blockMesh"},
            {
                "identifier": "icoFoam",
                "display_name": "OpenFOAM icoFoam solver",
                "required": False,
            },
            {
                "identifier": "simpleFoam",
                "display_name": "OpenFOAM simpleFoam solver",
                "required": False,
            },
            {
                "identifier": "foamRun",
                "display_name": "OpenFOAM foamRun command",
                "required": False,
            },
        ],
        "environment_variable_hints": ["WM_PROJECT_VERSION", "FOAM_APPBIN"],
        "version_probe": {
            "name": "OpenFOAM version",
            "command": ["foamVersion"],
            "description": "Declarative version probe for an initialized prepared shell.",
        },
        "help_probe": {
            "name": "blockMesh help",
            "command": ["blockMesh", "-help"],
            "description": "Declarative help probe for an initialized prepared shell.",
        },
        "smoke_test_description": (
            "Run foamVersion and, only with a safe case, a short "
            "blockMesh/solver smoke under ignored artifacts."
        ),
        "prepared_machine_notes": [
            "Run only from an initialized OpenFOAM environment.",
            (
                "Classify as blocked-no-safe-case if commands exist but no "
                "safe tiny case is available."
            ),
        ],
        "platform_notes": [
            "OpenFOAM shell initialization is platform and distribution specific."
        ],
        "documentation_refs": _COMMON_DOCS,
        "support_status": "experimental",
        "non_bundled_disclaimer": _DISCLAIMER,
        "safety_notes": _COMMON_SAFETY,
    },
    {
        "stack_id": OptionalSolverStackId.COOLPROP_CANTERA.value,
        "display_name": "CoolProp / Cantera",
        "related_issue": 10,
        "capabilities": [
            {
                "capability_id": "property_query_smoke",
                "description": (
                    "Run bounded thermophysical property queries when "
                    "packages are already installed."
                ),
            },
            {
                "capability_id": "gas_object_smoke",
                "description": (
                    "Run minimal Cantera object construction when the "
                    "package is already installed."
                ),
            },
        ],
        "python_package_requirements": [
            {"identifier": "CoolProp", "display_name": "CoolProp Python package"},
            {"identifier": "cantera", "display_name": "Cantera Python package"},
        ],
        "smoke_test_description": (
            "Run a CoolProp property query and a minimal Cantera gas/object "
            "smoke in a prepared Python environment."
        ),
        "prepared_machine_notes": [
            "Run only where CoolProp and/or Cantera are already installed.",
            "Classify partial-installed when only one package is available.",
        ],
        "platform_notes": ["Python package availability can vary by interpreter and platform."],
        "documentation_refs": _COMMON_DOCS,
        "support_status": "experimental",
        "non_bundled_disclaimer": _DISCLAIMER,
        "safety_notes": _COMMON_SAFETY,
    },
    {
        "stack_id": OptionalSolverStackId.PYVISTA_MESHIO.value,
        "display_name": "PyVista / meshio",
        "related_issue": 11,
        "capabilities": [
            {
                "capability_id": "mesh_round_trip",
                "description": (
                    "Run meshio read/write smoke checks when meshio is "
                    "already installed."
                ),
            },
            {
                "capability_id": "offscreen_mesh_object",
                "description": (
                    "Construct simple PyVista mesh objects without opening a "
                    "GUI window."
                ),
            },
        ],
        "python_package_requirements": [
            {"identifier": "meshio", "display_name": "meshio Python package"},
            {"identifier": "pyvista", "display_name": "PyVista Python package"},
            {
                "identifier": "vtk",
                "display_name": "VTK Python package",
                "required": False,
                "notes": ["Required by many PyVista installations."],
            },
        ],
        "smoke_test_description": (
            "Run meshio minimal mesh write/read and PyVista simple mesh object "
            "construction in a prepared Python environment."
        ),
        "prepared_machine_notes": [
            "Run only where meshio and PyVista are already installed.",
            "Use offscreen-safe checks and require no visualization window.",
        ],
        "platform_notes": ["Headless rendering support can vary by graphics stack."],
        "documentation_refs": _COMMON_DOCS,
        "support_status": "experimental",
        "non_bundled_disclaimer": _DISCLAIMER,
        "safety_notes": _COMMON_SAFETY,
    },
)


def builtin_optional_solver_manifests() -> tuple[OptionalSolverManifest, ...]:
    """Return the built-in declarative optional solver manifests."""

    return tuple(
        parse_optional_solver_manifest_dict(item)
        for item in _BUILTIN_MANIFEST_DATA
    )


def get_builtin_optional_solver_manifest(stack_id: str) -> OptionalSolverManifest:
    """Return one built-in manifest by stack id."""

    for manifest in builtin_optional_solver_manifests():
        if manifest.stack_id == stack_id:
            return manifest
    msg = f"Unknown built-in optional solver manifest: {stack_id}"
    raise KeyError(msg)
