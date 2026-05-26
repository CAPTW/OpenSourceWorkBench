from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from osw.scripts.mscript.execution_policy import OctaveExecutionPolicy
from osw.scripts.mscript.octave_runner import (
    OctaveRunner,
    OctaveRunRequest,
    OctaveRunStatus,
)

pytestmark = [
    pytest.mark.external_solver,
    pytest.mark.skipif(
        shutil.which("octave") is None,
        reason="GNU Octave is not installed on PATH.",
    ),
]


def test_real_octave_optional_smoke(tmp_path: Path) -> None:
    script_path = tmp_path / "hello_octave.m"
    script_path.write_text("disp('osw octave optional smoke');\n", encoding="utf-8")
    runner = OctaveRunner()

    result = runner.run(
        OctaveRunRequest(
            script_path,
            working_directory=tmp_path / "artifacts",
            policy=OctaveExecutionPolicy(timeout_seconds=10),
        )
    )

    assert result.status == OctaveRunStatus.COMPLETED
    assert "osw octave optional smoke" in result.stdout
