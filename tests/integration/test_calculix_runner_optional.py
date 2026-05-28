from __future__ import annotations

from pathlib import Path

import pytest

from osw.solvers.calculix.adapter import create_cantilever_demo_case
from osw.solvers.calculix.input_deck import (
    CalculixInputDeckGenerator,
    write_input_deck,
)
from osw.solvers.calculix.runner import (
    CalculiXRunner,
    CalculiXRunPolicy,
    CalculiXRunStatus,
    find_ccx_executable,
)

pytestmark = pytest.mark.external_solver


def test_real_ccx_runner_is_optional(tmp_path: Path) -> None:
    resolution = find_ccx_executable()
    if not resolution.found:
        pytest.skip("CalculiX ccx executable is not installed.")

    deck = write_input_deck(
        CalculixInputDeckGenerator().generate(create_cantilever_demo_case()),
        tmp_path / "cantilever.inp",
    )
    result = CalculiXRunner().run_input_deck(
        deck,
        case_dir=tmp_path / "run",
        policy=CalculiXRunPolicy(timeout_seconds=20.0),
    )

    assert result.status in {
        CalculiXRunStatus.COMPLETED,
        CalculiXRunStatus.FAILED,
        CalculiXRunStatus.TIMED_OUT,
    }
    assert result.command
    assert result.case_dir.exists()
    assert any(artifact.role == "input_deck" for artifact in result.artifacts)
