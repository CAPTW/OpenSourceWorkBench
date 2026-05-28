from __future__ import annotations

import json
from pathlib import Path

from osw.core.boundary_curve import BoundaryCurve
from osw.core.result_dataset import ResultCatalog, ResultDataset
from osw.mesh.mesh_model import MeshBounds, MeshCellBlock, MeshInfo
from osw.post.result_view_model import (
    boundary_curve_to_view_dataset,
    figure_dataset_to_view_dataset,
    mat_summary_to_view_dataset,
    mesh_info_to_view_dataset,
    result_catalog_from_project,
    result_catalog_from_result_datasets,
    result_dataset_summary,
    result_dataset_to_view_model,
)
from osw.scripts.mscript.figure_dataset import FigureDataset
from osw.scripts.mscript.mat_model import MatFileSummary

FIXTURES = Path(__file__).parents[1] / "fixtures" / "results"


def _load_dataset(name: str) -> ResultDataset:
    return ResultDataset.from_dict(json.loads((FIXTURES / name).read_text(encoding="utf-8")))


def test_calculix_result_dataset_converts_to_view_model() -> None:
    view_model = result_dataset_to_view_model(_load_dataset("calculix_summary_result.json"))

    assert view_model.kind == "calculix_summary"
    assert {scalar.name for scalar in view_model.scalars} == {
        "max_displacement",
        "max_von_mises_stress",
    }
    assert view_model.artifacts[0].exists


def test_openfoam_residual_dataset_converts_series() -> None:
    view_model = result_dataset_to_view_model(_load_dataset("openfoam_residual_result.json"))

    assert view_model.kind == "openfoam_residuals"
    assert {"Ux", "Uy", "Uz", "p"}.issubset({series.name for series in view_model.series})
    assert view_model.tables


def test_figure_dataset_converts_to_view_dataset_and_model() -> None:
    payload = json.loads((FIXTURES / "figure_dataset_result.json").read_text(encoding="utf-8"))
    dataset = figure_dataset_to_view_dataset(FigureDataset.from_dict(payload))
    view_model = result_dataset_to_view_model(dataset)

    assert view_model.kind == "figure_dataset"
    assert view_model.figures[0].title == "Simple Plot"
    assert view_model.tables[0].title == "Scalar summaries"
    assert any(table.title == "Workspace variables" for table in view_model.tables)


def test_mat_summary_converts_to_workspace_table() -> None:
    payload = json.loads((FIXTURES / "mat_workspace_result.json").read_text(encoding="utf-8"))
    dataset = mat_summary_to_view_dataset(MatFileSummary.from_dict(payload))
    view_model = result_dataset_to_view_model(dataset)

    assert view_model.kind == "mat_workspace"
    assert any(table.title == "Workspace variables" for table in view_model.tables)
    assert view_model.scalars[0].name == "variable_count"


def test_boundary_curve_converts_to_series_and_table() -> None:
    payload = json.loads((FIXTURES / "boundary_curve_result.json").read_text(encoding="utf-8"))
    dataset = boundary_curve_to_view_dataset(BoundaryCurve.from_dict(payload))
    view_model = result_dataset_to_view_model(dataset)

    assert view_model.kind == "boundary_curve"
    assert view_model.series[0].y_values[-1] == 30.0
    assert view_model.tables[0].columns == ("entity_id", "x", "y")


def test_mesh_info_converts_to_scalar_summary() -> None:
    mesh_info = MeshInfo(
        source_path="mesh.msh",
        format="msh",
        node_count=8,
        cell_blocks=(MeshCellBlock("hexahedron", count=1),),
        bounds=MeshBounds(minimum=(0.0, 0.0, 0.0), maximum=(1.0, 1.0, 1.0)),
    )
    view_model = result_dataset_to_view_model(mesh_info_to_view_dataset(mesh_info))

    assert view_model.kind == "mesh_summary"
    assert {scalar.name for scalar in view_model.scalars} == {"node_count", "element_count"}
    assert any(table.title == "Mesh cell types" for table in view_model.tables)


def test_empty_dataset_and_missing_artifact_are_friendly() -> None:
    empty = result_dataset_to_view_model(
        ResultDataset("empty", "none", "fixture", "generic")
    )
    broken = result_dataset_to_view_model(_load_dataset("broken_artifact_result.json"))

    assert "No result summaries" in empty.empty_state_message
    assert any("Missing artifact" in diagnostic for diagnostic in broken.diagnostics)


def test_result_catalog_helpers_round_trip() -> None:
    catalog = result_catalog_from_result_datasets(
        (
            _load_dataset("calculix_summary_result.json"),
            _load_dataset("openfoam_residual_result.json"),
        ),
        project_name="Demo",
    )
    restored = ResultCatalog.from_dict(catalog.to_dict())

    assert restored.project_name == "Demo"
    assert len(restored.datasets) == 2
    assert result_dataset_summary(restored.datasets[0]).scalar_count == 2


def test_result_catalog_from_project_includes_mesh_and_boundary_curve() -> None:
    from osw.core.project_schema import MeshRef, Project, ProjectMetadata

    curve_payload = json.loads(
        (FIXTURES / "boundary_curve_result.json").read_text(encoding="utf-8")
    )
    mesh_info = MeshInfo(source_path="mesh.msh", format="msh", node_count=4, element_count=1)
    project = Project(
        metadata=ProjectMetadata(name="ProjectResults"),
        meshes=(MeshRef(id="mesh", path="mesh.msh", format="msh", mesh_info=mesh_info.to_dict()),),
        boundary_curves=(BoundaryCurve.from_dict(curve_payload),),
    )

    catalog = result_catalog_from_project(project)

    assert len(catalog.datasets) == 2
    assert {dataset.metadata["kind"] for dataset in catalog.datasets} == {
        "mesh_summary",
        "boundary_curve",
    }
