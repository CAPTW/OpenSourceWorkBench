from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from osw.solvers.openfoam.case_generator import default_cavity_request, generate_openfoam_case
from osw.solvers.openfoam.model import OpenFOAMRunPolicy, OpenFOAMRunStatus
from osw.solvers.openfoam.runner import OpenFOAMRunner


def test_real_openfoam_optional_cavity_run(tmp_path: Path) -> None:
    if shutil.which("icoFoam") is None:
        pytest.skip("OpenFOAM icoFoam is not installed.")

    case = generate_openfoam_case(default_cavity_request(tmp_path / "openfoam"))
    assert case.status == "ok"

    result = OpenFOAMRunner().run_case(
        case.case_dir,
        "icoFoam",
        OpenFOAMRunPolicy(timeout_seconds=20.0),
    )

    assert result.status in {OpenFOAMRunStatus.COMPLETED, OpenFOAMRunStatus.FAILED}
    assert result.run_result is not None
