from __future__ import annotations

from pathlib import Path

from osw.gui.workflow_service import WorkbenchWorkflowSession


def test_workflow_session_imports_geometry_and_script_without_running_code(
    tmp_path: Path,
) -> None:
    session = WorkbenchWorkflowSession(artifact_dir=tmp_path / "artifacts")
    geometry_path = tmp_path / "plate.stl"
    marker_path = tmp_path / "marker.txt"
    script_path = tmp_path / "preview.m"
    geometry_path.write_text(_ascii_stl(), encoding="utf-8")
    script_path.write_text(
        "\n".join(
            [
                "plot(1:3, 1:3);",
                f"fid = fopen('{marker_path.as_posix()}', 'w');",
                "fprintf(fid, 'ran');",
            ]
        ),
        encoding="utf-8",
    )

    geometry_operation = session.import_path(geometry_path)
    script_operation = session.import_path(script_path)

    assert geometry_operation.status == "Imported"
    assert script_operation.status == "Previewed with findings"
    assert marker_path.exists() is False
    assert len(session.project.geometry) == 1
    assert len(session.project.scripts) == 1
    assert session.result_tables


def test_workflow_session_run_generate_records_prepare_or_diagnostics(
    tmp_path: Path,
) -> None:
    session = WorkbenchWorkflowSession(artifact_dir=tmp_path / "artifacts")

    operation = session.run_generate()

    labels = {item.label for item in operation.items}
    assert operation.status == "Prepared"
    assert "CalculiX linear static prepare" in labels
    assert "OpenFOAM cavity prepare" in labels
    assert "M-script explicit run diagnostic" in labels
    assert session.project.solvers
    assert session.result_tables
    assert any("execution is explicit" in warning for warning in session.warnings)


def _ascii_stl() -> str:
    return "\n".join(
        [
            "solid plate",
            "  facet normal 0 0 1",
            "    outer loop",
            "      vertex 0 0 0",
            "      vertex 1 0 0",
            "      vertex 0 1 0",
            "    endloop",
            "  endfacet",
            "endsolid plate",
            "",
        ]
    )
