from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from osw.scripts.mscript.octave_runner import OctaveRunner
from osw.solvers.runner import RunStatus, TimeoutPolicy

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
    runner = OctaveRunner(timeout_policy=TimeoutPolicy(seconds=10))

    result = runner.run_script(
        script_path,
        artifact_dir=tmp_path / "artifacts",
        allow_execution=True,
    )

    assert result.status == RunStatus.COMPLETED
    assert "osw octave optional smoke" in result.log.stdout
