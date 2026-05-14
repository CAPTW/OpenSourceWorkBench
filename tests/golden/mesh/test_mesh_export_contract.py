from __future__ import annotations

from pathlib import Path

from helpers import assert_json_matches_golden

from osw.mesh.conversion import SUPPORTED_EXPORT_FORMATS, MeshExportArtifact


def test_supported_export_formats_are_stable_for_v0_1() -> None:
    assert SUPPORTED_EXPORT_FORMATS == {
        ".inp": "abaqus",
        ".msh": "gmsh",
        ".vtu": "vtu",
        ".xdmf": "xdmf",
        ".xmf": "xdmf",
    }


def test_mesh_export_artifact_dict_contract_is_report_friendly() -> None:
    artifact = MeshExportArtifact(
        path="mesh/out.vtu",
        format="vtu",
        meshio_format="vtu",
        node_count=3,
        element_count=1,
        cell_types=("triangle",),
    )
    expected = (Path(__file__).with_name("export_artifact_summary.json")).read_text(
        encoding="utf-8"
    )

    assert_json_matches_golden(
        artifact.to_dict(),
        expected,
        label="mesh/export_artifact_summary.json",
    )
