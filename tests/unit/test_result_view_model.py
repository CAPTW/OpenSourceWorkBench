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
    summarize_result_catalog_for_view,
    summarize_result_dataset_for_view,
)
from osw.scripts.mscript.figure_dataset import FigureDataset
from osw.scripts.mscript.mat_model import MatFileSummary
from osw.solvers.cantera.model import (
    CanteraMixtureSpec,
    CanteraReactorRequest,
    CanteraReactorResult,
)
from osw.solvers.cantera.results import cantera_result_to_result_dataset
from osw.solvers.coolprop.model import (
    CoolPropPropertyRequest,
    CoolPropPropertyResult,
    CoolPropPropertyValue,
    CoolPropSweepRequest,
    CoolPropSweepResult,
    PropertyInputPair,
)
from osw.solvers.coolprop.results import (
    coolprop_result_to_result_dataset,
    coolprop_sweep_to_result_dataset,
)

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


def test_chm_result_datasets_convert_to_view_models() -> None:
    property_dataset = coolprop_result_to_result_dataset(
        CoolPropPropertyResult(
            "ok",
            CoolPropPropertyRequest(
                "Water",
                PropertyInputPair("T", 300.0, "P", 101325.0),
            ),
            values=(CoolPropPropertyValue("density", 997.0, "kg/m^3"),),
        )
    )
    sweep_dataset = coolprop_sweep_to_result_dataset(
        CoolPropSweepResult(
            "ok",
            CoolPropSweepRequest(
                "Water",
                "T",
                (280.0, 300.0),
                "P",
                101325.0,
                ("density",),
                sweep_unit="K",
                fixed_unit="Pa",
            ),
            columns=("T [K]", "density [kg/m^3]"),
            rows=((280.0, 999.0), (300.0, 997.0)),
            series={"density": (999.0, 997.0)},
        )
    )
    reactor_dataset = cantera_result_to_result_dataset(
        CanteraReactorResult(
            "ok",
            CanteraReactorRequest(
                mixture=CanteraMixtureSpec(mechanism="gri30.yaml"),
                tracked_species=("CH4",),
            ),
            times=(0.0, 0.001),
            temperature_series=(1000.0, 1025.0),
            pressure_series=(101325.0, 101400.0),
            species_series={"CH4": (0.05, 0.03)},
        )
    )

    property_view = result_dataset_to_view_model(property_dataset)
    sweep_view = result_dataset_to_view_model(sweep_dataset)
    reactor_view = result_dataset_to_view_model(reactor_dataset)

    assert property_view.kind == "coolprop_property"
    assert any(table.title == "CoolProp property table" for table in property_view.tables)
    assert sweep_view.kind == "coolprop_sweep"
    assert sweep_view.series[0].x_values == (280.0, 300.0)
    assert reactor_view.kind == "cantera_reactor"
    assert {"temperature", "CH4"}.issubset({series.name for series in reactor_view.series})


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


def test_catalog_view_summary_counts_types_and_selection() -> None:
    catalog = result_catalog_from_result_datasets(
        (
            _load_dataset("calculix_summary_result.json"),
            _load_dataset("openfoam_residual_result.json"),
        ),
        project_name="Demo",
        selected_dataset_id="duct-residuals",
    )

    summary = summarize_result_catalog_for_view(catalog)

    assert summary.dataset_count == 2
    assert summary.selected_dataset_id == "duct-residuals"
    assert ("calculix_summary", 1) in summary.kind_counts
    assert ("openfoam_residuals", 1) in summary.kind_counts
    assert "simple_success.dat" in summary.source_summary


def test_dataset_view_details_exposes_handoff_and_limitations() -> None:
    field_fixture = (
        Path(__file__).parents[1]
        / "fixtures"
        / "fields"
        / "scalar_field_dataset.json"
    )
    dataset = ResultDataset.from_dict(
        json.loads(field_fixture.read_text(encoding="utf-8"))
    )

    details = summarize_result_dataset_for_view(dataset, field_count=2)

    assert details.source_kind == "vtk"
    assert details.field_count == 2
    assert "Shown in Table Viewer" in details.handoff_hints
    assert "Shown in Field Viewer" in details.handoff_hints
    assert any("does not execute solvers or scripts" in item for item in details.limitations)


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
