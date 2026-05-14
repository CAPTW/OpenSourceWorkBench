from __future__ import annotations

from pathlib import Path

from helpers import assert_text_matches_golden

from osw.solvers.su2.config import Su2BoundaryConfig, Su2SimulationConfig, generate_su2_config


def test_basic_euler_cfg_matches_golden() -> None:
    config = Su2SimulationConfig(
        case_name="basic_euler",
        mesh_filename="mesh.su2",
        solver="EULER",
        mach_number=0.5,
        aoa_degrees=2.0,
        boundaries=Su2BoundaryConfig(
            euler_markers=("wall",),
            farfield_markers=("farfield",),
        ),
    )
    expected = (Path(__file__).with_name("basic_euler.cfg")).read_text(encoding="utf-8")

    assert_text_matches_golden(
        generate_su2_config(config),
        expected,
        label="su2/basic_euler.cfg",
    )
