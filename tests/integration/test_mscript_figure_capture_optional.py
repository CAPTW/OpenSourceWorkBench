from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from osw.scripts.mscript.execution_policy import OctaveExecutionPolicy
from osw.scripts.mscript.figure_capture import capture_octave_figures
from osw.scripts.mscript.octave_runner import (
    OctaveRunner,
    OctaveRunRequest,
    OctaveRunStatus,
)

pytestmark = pytest.mark.external_solver


def test_octave_simple_plot_can_be_captured_when_octave_is_available(tmp_path: Path) -> None:
    octave = shutil.which("octave")
    if octave is None:
        pytest.skip("GNU Octave is not installed.")

    script = tmp_path / "simple_plot.m"
    script.write_text(
        "\n".join(
            [
                "x = [0, 1, 2];",
                "y = [0, 1, 4];",
                "figure('visible', 'off');",
                "plot(x, y);",
                "title('OSW simple plot');",
                "print('-dpng', 'simple_plot.png');",
                "print('-dsvg', 'simple_plot.svg');",
            ]
        ),
        encoding="utf-8",
    )

    runner = OctaveRunner(executable=octave)
    result = runner.run(
        OctaveRunRequest(
            script,
            working_directory=tmp_path / "artifacts",
            policy=OctaveExecutionPolicy(timeout_seconds=20),
        )
    )
    if result.status is not OctaveRunStatus.COMPLETED:
        pytest.skip(f"GNU Octave plotting backend unavailable: {result.diagnostics.summary()}")

    dataset = capture_octave_figures(result, dataset_id="octave-figures")

    assert dataset.dataset_id == "octave-figures"
    assert set(dataset.formats) >= {"png", "svg"}
    assert all(
        record.primary_path is not None and record.primary_path.exists()
        for record in dataset.figures
    )
    assert dataset.stdout == result.stdout
