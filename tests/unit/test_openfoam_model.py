from __future__ import annotations

import json
from pathlib import Path

from osw.solvers.openfoam.model import (
    OpenFOAMBoundaryPatch,
    OpenFOAMCaseRequest,
    OpenFOAMCaseResult,
    OpenFOAMResidualSeries,
    OpenFOAMResidualSummary,
)


def test_openfoam_boundary_patch_serializes() -> None:
    patch = OpenFOAMBoundaryPatch(
        "inlet",
        "velocityInlet",
        {"U": [1.0, 0.0, 0.0]},
        role="inlet",
    )

    restored = OpenFOAMBoundaryPatch.from_dict(patch.to_dict())

    assert restored.name == "inlet"
    assert restored.field_values["U"] == [1.0, 0.0, 0.0]
    assert restored.role == "inlet"


def test_openfoam_case_request_paths_serialize_as_strings(tmp_path: Path) -> None:
    request = OpenFOAMCaseRequest(
        template_kind="cavity",
        solver="icoFoam",
        case_name="case",
        output_dir=tmp_path,
    )

    payload = request.to_dict()
    restored = OpenFOAMCaseRequest.from_dict(payload)

    assert payload["output_dir"] == str(tmp_path)
    assert restored.output_dir == tmp_path
    assert json.loads(json.dumps(payload))["case_name"] == "case"


def test_openfoam_case_result_serializes(tmp_path: Path) -> None:
    request = OpenFOAMCaseRequest(output_dir=tmp_path)
    result = OpenFOAMCaseResult(
        "ok",
        request,
        tmp_path / "cavity",
        generated_files=(tmp_path / "cavity" / "system" / "controlDict",),
    )

    payload = result.to_dict()

    assert payload["case_dir"] == str(tmp_path / "cavity")
    assert payload["generated_files"] == [str(tmp_path / "cavity" / "system" / "controlDict")]


def test_openfoam_residual_summary_serializes() -> None:
    summary = OpenFOAMResidualSummary(
        series=(OpenFOAMResidualSeries("Ux", (0.1, 0.01), (1, 2)),),
        final_residuals={"Ux": 0.01},
        initial_residuals={"Ux": 0.1},
        iteration_count=2,
        converged=True,
    )

    restored = OpenFOAMResidualSummary.from_dict(summary.to_dict())

    assert restored.final_residuals["Ux"] == 0.01
    assert restored.series[0].values == (0.1, 0.01)
    assert restored.converged is True
