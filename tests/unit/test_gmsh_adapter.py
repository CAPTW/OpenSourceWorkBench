from __future__ import annotations

import json
import sys
from pathlib import Path

from osw.core.executables import ExecutablePathRegistry
from osw.mesh.gmsh_adapter import (
    GmshAdapter,
    GmshMeshStatus,
    convert_result_to_mesh_ref,
    find_gmsh_executable,
)
from osw.mesh.gmsh_geometry import write_geo_script
from osw.mesh.gmsh_model import (
    GmshGeometryKind,
    GmshGeometrySpec,
    GmshMeshDimension,
    GmshMeshRequest,
    GmshMeshSizeField,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "gmsh"


def _request(tmp_path: Path, *, output_name: str = "box", timeout: float = 5.0) -> GmshMeshRequest:
    return GmshMeshRequest(
        geometry=GmshGeometrySpec(
            GmshGeometryKind.BOX,
            {"length": 1.0, "width": 0.2, "height": 0.1},
            geometry_id="box",
        ),
        mesh_dimension=GmshMeshDimension.DIM3,
        mesh_size=GmshMeshSizeField(global_size=0.05),
        output_dir=tmp_path,
        output_name=output_name,
        timeout_seconds=timeout,
    )


def _fake_adapter(tmp_path: Path, mode: str = "success") -> GmshAdapter:
    registry = ExecutablePathRegistry().register("gmsh", sys.executable)
    return GmshAdapter(
        executable_registry=registry,
        command_prefix=(str(FIXTURES / "fake_gmsh.py"), "--mode", mode),
    )


def test_module_imports_without_gmsh_meshio_or_pyside6() -> None:
    import osw.mesh.gmsh_adapter as adapter

    assert hasattr(adapter, "GmshAdapter")


def test_gmsh_executable_detection_uses_registry_and_reports_missing(tmp_path: Path) -> None:
    missing = find_gmsh_executable(ExecutablePathRegistry())
    configured = find_gmsh_executable(ExecutablePathRegistry().register("gmsh", sys.executable))

    assert not missing.found
    assert "Gmsh executable was not found" in missing.diagnostics.summary()
    assert configured.found
    assert configured.resolved_path == Path(sys.executable).resolve()


def test_write_geo_works_without_gmsh_installed(tmp_path: Path) -> None:
    output = write_geo_script(_request(tmp_path), tmp_path / "box.geo")

    assert output.exists()
    assert "Box(1)" in output.read_text(encoding="utf-8")


def test_fake_gmsh_success_creates_msh_artifact(tmp_path: Path) -> None:
    result = _fake_adapter(tmp_path).generate_mesh(_request(tmp_path))

    assert result.status in {GmshMeshStatus.OK, GmshMeshStatus.WARNING}
    assert result.msh_path is not None
    assert result.msh_path.exists()
    assert result.run_result is not None
    assert "fake gmsh wrote" in result.run_result.log.stdout


def test_fake_gmsh_failure_returns_error_diagnostic(tmp_path: Path) -> None:
    result = _fake_adapter(tmp_path, "fail").generate_mesh(_request(tmp_path))

    assert result.status is GmshMeshStatus.ERROR
    assert result.run_result is not None
    assert result.run_result.return_code == 3
    assert "fake gmsh failed intentionally" in result.run_result.log.stderr


def test_fake_gmsh_timeout_returns_timed_out(tmp_path: Path) -> None:
    result = _fake_adapter(tmp_path, "sleep").generate_mesh(_request(tmp_path, timeout=0.1))

    assert result.status is GmshMeshStatus.TIMED_OUT
    assert "timed out" in result.diagnostics.summary().lower()


def test_meshio_missing_or_invalid_conversion_is_friendly(tmp_path: Path) -> None:
    request = _request(tmp_path)
    result = _fake_adapter(tmp_path).generate_mesh(request)

    assert result.status in {GmshMeshStatus.OK, GmshMeshStatus.WARNING}
    json.dumps(result.to_dict())


def test_gmsh_result_converts_to_project_mesh_ref(tmp_path: Path) -> None:
    result = _fake_adapter(tmp_path).generate_mesh(_request(tmp_path))
    mesh_ref = convert_result_to_mesh_ref(result)

    assert mesh_ref.path.endswith("box.msh")
    assert mesh_ref.format == "msh"
    assert mesh_ref.metadata["generated_by"] == "osw.gmsh"
    assert mesh_ref.metadata["physical_groups"]
