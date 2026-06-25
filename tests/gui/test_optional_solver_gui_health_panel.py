from __future__ import annotations

import importlib.util
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None
pytestmark = pytest.mark.skipif(
    not PYSIDE6_AVAILABLE,
    reason="PySide6 optional GUI extra is not installed.",
)

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def sample_optional_solver_health_view_model():
    from osw.experimental.optional_solvers import (
        OptionalSolverDiagnosticSeverity,
        OptionalSolverDiscoveryDiagnostic,
        OptionalSolverDiscoveryReport,
        OptionalSolverExecutableDiscovery,
        OptionalSolverHealthState,
        OptionalSolverPythonPackageDiscovery,
        OptionalSolverStackDiscovery,
        build_optional_solver_health_panel_viewmodel,
        parse_optional_solver_manifest_dict,
    )

    manifests = [
        parse_optional_solver_manifest_dict(
            {
                "stack_id": "gmsh",
                "display_name": "Gmsh",
                "related_issue": 6,
                "capabilities": ["mesh_generation"],
                "executable_requirements": ["gmsh"],
                "prepared_machine_notes": ["Run only where Gmsh is installed."],
                "documentation_refs": ["docs/validation/gmsh.md"],
                "support_status": "experimental",
                "non_bundled_disclaimer": "External solvers are not bundled.",
                "safety_notes": ["No solver install.", "No dependency install."],
            }
        ),
        parse_optional_solver_manifest_dict(
            {
                "stack_id": "calculix",
                "display_name": "CalculiX ccx",
                "related_issue": 8,
                "capabilities": [
                    {
                        "capability_id": "run_gate",
                        "description": "Prepared-machine run gate.",
                    }
                ],
                "executable_requirements": [
                    {"identifier": "ccx", "display_name": "CalculiX ccx"}
                ],
                "python_package_requirements": [
                    {
                        "identifier": "meshio",
                        "display_name": "meshio",
                        "required": False,
                    }
                ],
                "prepared_machine_notes": ["Run only where ccx is installed."],
                "documentation_refs": ["docs/validation/calculix.md"],
                "support_status": "experimental",
                "non_bundled_disclaimer": "External solvers are not bundled.",
                "safety_notes": ["No solver execution.", "No certification claim."],
            }
        ),
        parse_optional_solver_manifest_dict(
            {
                "stack_id": "pyvista_meshio",
                "display_name": "PyVista / meshio",
                "related_issue": 11,
                "capabilities": ["mesh_round_trip"],
                "python_package_requirements": ["meshio", "pyvista"],
                "prepared_machine_notes": ["Run only where packages are installed."],
                "documentation_refs": ["docs/validation/pyvista_meshio.md"],
                "support_status": "experimental",
                "non_bundled_disclaimer": "External packages are not bundled.",
                "safety_notes": ["No dependency install."],
            }
        ),
    ]
    report = OptionalSolverDiscoveryReport(
        stacks=(
            OptionalSolverStackDiscovery(
                stack_id="gmsh",
                display_name="Gmsh",
                related_issue=6,
                health_state=OptionalSolverHealthState.MISSING,
                executables=(
                    OptionalSolverExecutableDiscovery(
                        identifier="gmsh",
                        required=True,
                        found=False,
                    ),
                ),
                diagnostics=(
                    OptionalSolverDiscoveryDiagnostic(
                        code="OSD_MISSING_EXECUTABLE",
                        severity=OptionalSolverDiagnosticSeverity.WARNING,
                        message="Required executable was not discovered: gmsh",
                        path="executable_requirements.gmsh",
                        suggested_fix="Expose gmsh on PATH.",
                    ),
                ),
            ),
            OptionalSolverStackDiscovery(
                stack_id="calculix",
                display_name="CalculiX ccx",
                related_issue=8,
                health_state=OptionalSolverHealthState.PARTIALLY_INSTALLED,
                executables=(
                    OptionalSolverExecutableDiscovery(
                        identifier="ccx",
                        display_name="CalculiX ccx",
                        required=True,
                        found=True,
                        path="C:/Users/USER/tools/ccx.exe",
                    ),
                ),
                python_packages=(
                    OptionalSolverPythonPackageDiscovery(
                        identifier="meshio",
                        display_name="meshio",
                        required=False,
                        found=False,
                    ),
                ),
            ),
            OptionalSolverStackDiscovery(
                stack_id="pyvista_meshio",
                display_name="PyVista / meshio",
                related_issue=11,
                health_state=OptionalSolverHealthState.DISCOVERED,
                python_packages=(
                    OptionalSolverPythonPackageDiscovery(
                        identifier="meshio",
                        found=True,
                        version="5.3.0",
                    ),
                    OptionalSolverPythonPackageDiscovery(
                        identifier="pyvista",
                        found=True,
                        version="0.44.0",
                    ),
                ),
            ),
        )
    )
    return build_optional_solver_health_panel_viewmodel(
        manifests=manifests,
        discovery_reports=report,
        selected_stack_id="calculix",
        validation_history=[
            {
                "source": "OSW-VALID-005",
                "status": "skipped-missing",
                "summary": "Prepared machine validation skipped missing components.",
                "related_issue": 8,
            }
        ],
    )


def test_panel_constructs_with_supplied_view_model(app: object) -> None:
    from osw.gui.dialogs import OptionalSolverHealthPanel as PackagePanel
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    panel = OptionalSolverHealthPanel(sample_optional_solver_health_view_model())

    assert PackagePanel is OptionalSolverHealthPanel
    assert panel.objectName() == "oswOptionalSolverHealthPanel"
    assert panel.windowTitle() == "Optional Solver Health"
    assert panel.tabs.objectName() == "oswOptionalSolverHealthTabs"


def test_summary_section_renders_counts(app: object) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    panel = OptionalSolverHealthPanel(sample_optional_solver_health_view_model())
    text = panel.summary_text()

    assert "total=3" in text
    assert "missing=1" in text
    assert "partial=1" in text
    assert "discovered=1" in text
    assert "open_issues=3" in text
