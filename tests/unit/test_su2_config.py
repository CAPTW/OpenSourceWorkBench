from __future__ import annotations

from pathlib import Path

import pytest

from osw.solvers.su2.config import (
    Su2BoundaryConfig,
    Su2ConfigError,
    Su2ConfigGenerator,
    Su2SimulationConfig,
    generate_su2_config,
)


def test_basic_su2_cfg_contains_expected_settings() -> None:
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

    text = generate_su2_config(config)

    assert "SOLVER= EULER" in text
    assert "MATH_PROBLEM= DIRECT" in text
    assert "MACH_NUMBER= 0.5" in text
    assert "AOA= 2" in text
    assert "MESH_FILENAME= mesh.su2" in text
    assert "MARKER_EULER= ( wall )" in text
    assert "MARKER_FAR= ( farfield )" in text
    assert "CONV_FILENAME= history" in text


def test_su2_cfg_validation_reports_missing_mesh() -> None:
    config = Su2SimulationConfig(mesh_filename="")
    messages = Su2ConfigGenerator(config).validate()

    assert any("SU2 mesh filename is required" in message for message in messages)
    with pytest.raises(Su2ConfigError, match="SU2 mesh filename is required"):
        generate_su2_config(config)


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        (
            Su2SimulationConfig(mesh_filename="mesh.su2\nITER=1"),
            "SU2 mesh filename contains unsupported characters",
        ),
        (
            Su2SimulationConfig(convergence_filename="history\nMARKER_EULER=bad"),
            "SU2 convergence filename contains unsupported characters",
        ),
        (
            Su2SimulationConfig(
                boundaries=Su2BoundaryConfig(euler_markers=("wall\nMACH_NUMBER=99",)),
            ),
            "SU2 boundary marker contains unsupported characters",
        ),
    ],
)
def test_su2_cfg_rejects_directive_injection_tokens(
    config: Su2SimulationConfig,
    expected: str,
) -> None:
    messages = Su2ConfigGenerator(config).validate()

    assert any(expected in message for message in messages)
    with pytest.raises(Su2ConfigError, match=expected):
        generate_su2_config(config)


def test_su2_reference_values_are_documented_as_nondimensional() -> None:
    config = Su2SimulationConfig()

    assert config.reference_frame == "su2_nondimensional"
    assert "SU2 nondimensional" in Su2ConfigGenerator(config).assumptions()


def test_su2_cfg_can_be_written_to_case_directory(tmp_path: Path) -> None:
    config = Su2SimulationConfig(case_name="demo", mesh_filename="demo.su2")
    generated = Su2ConfigGenerator(config).write(tmp_path)

    assert generated.path == tmp_path / "demo.cfg"
    assert generated.path.read_text(encoding="utf-8").startswith("% OpenSolver Workbench SU2")
    assert generated.mesh_reference == "demo.su2"


def test_su2_cfg_write_validates_before_creating_output_dir(tmp_path: Path) -> None:
    target = tmp_path / "not_created"
    config = Su2SimulationConfig(mesh_filename="mesh.su2\nITER=1")

    with pytest.raises(Su2ConfigError):
        Su2ConfigGenerator(config).write(target)

    assert not target.exists()
