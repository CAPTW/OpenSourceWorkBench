"""Unit tests for variant-aware OpenFOAM property-file generation (issue #18).

These tests never run OpenFOAM, never resolve OpenFOAM executables, and never
touch the network. They exercise only deterministic template generation and the
CLI dispatch surface.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from osw.cli.main import build_parser, main
from osw.solvers.openfoam.case_generator import (
    OSW_OPENFOAM_TEMPLATE_FOUNDATION_V12_PHYSICAL_PROPERTIES,
    OSW_OPENFOAM_TEMPLATE_LEGACY_TRANSPORT_PROPERTIES,
    OSW_OPENFOAM_TEMPLATE_VARIANT_UNSUPPORTED,
    OpenFoamCaseTemplateError,
    OpenFoamCavityConfig,
    OpenFoamDuctConfig,
    default_cavity_request,
    default_duct_request,
    generate_cavity_case,
    generate_duct_case,
    generate_openfoam_case,
    layout_diagnostic_code,
    property_file_for_layout,
    resolve_property_file_layout,
)
from osw.solvers.openfoam.model import (
    OpenFOAMCaseRequest,
    OpenFOAMPropertyFileLayout,
)

LEGACY = OpenFOAMPropertyFileLayout.LEGACY_TRANSPORT_PROPERTIES
FOUNDATION = OpenFOAMPropertyFileLayout.FOUNDATION_V11_PLUS_PHYSICAL_PROPERTIES

TRANSPORT = "constant/transportProperties"
PHYSICAL = "constant/physicalProperties"


def _read(root: Path, relative_path: str) -> str:
    return (root / relative_path).read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Layout resolution                                                           #
# --------------------------------------------------------------------------- #


def test_default_layout_is_legacy() -> None:
    assert OpenFoamCavityConfig().property_file_layout is LEGACY
    assert OpenFoamDuctConfig().property_file_layout is LEGACY


@pytest.mark.parametrize(
    "value",
    [None, "", "legacy", "transportProperties", "esi", "foundation_v10", "v10", LEGACY],
)
def test_legacy_aliases_resolve_to_legacy(value: object) -> None:
    assert resolve_property_file_layout(value) is LEGACY


@pytest.mark.parametrize(
    "value",
    [
        "foundation_v11_plus",
        "foundation_v11",
        "foundation_v12",
        "foundation-v12",
        "physicalProperties",
        "v12",
        FOUNDATION,
    ],
)
def test_foundation_aliases_resolve_to_foundation(value: object) -> None:
    assert resolve_property_file_layout(value) is FOUNDATION


def test_unknown_layout_raises_deterministic_error() -> None:
    with pytest.raises(OpenFoamCaseTemplateError) as excinfo:
        resolve_property_file_layout("bogus_variant")
    assert OSW_OPENFOAM_TEMPLATE_VARIANT_UNSUPPORTED in str(excinfo.value)


def test_property_file_for_layout_maps_each_layout() -> None:
    assert property_file_for_layout(LEGACY) == TRANSPORT
    assert property_file_for_layout(FOUNDATION) == PHYSICAL


def test_layout_diagnostic_codes() -> None:
    assert layout_diagnostic_code(LEGACY) == OSW_OPENFOAM_TEMPLATE_LEGACY_TRANSPORT_PROPERTIES
    assert (
        layout_diagnostic_code(FOUNDATION)
        == OSW_OPENFOAM_TEMPLATE_FOUNDATION_V12_PHYSICAL_PROPERTIES
    )


# --------------------------------------------------------------------------- #
# Cavity generation                                                           #
# --------------------------------------------------------------------------- #


def test_legacy_cavity_emits_transport_properties_only(tmp_path: Path) -> None:
    generated = generate_cavity_case(OpenFoamCavityConfig(), tmp_path)
    paths = set(generated.relative_paths)

    assert TRANSPORT in paths
    assert PHYSICAL not in paths
    assert generated.property_file_layout is LEGACY
    assert generated.property_file == TRANSPORT
    # Legacy content is unchanged (transportModel + nu entry).
    transport = _read(generated.root, TRANSPORT)
    assert "transportModel  Newtonian;" in transport
    assert "nu              [0 2 -1 0 0 0 0] 0.01;" in transport


def test_foundation_cavity_emits_physical_properties_only(tmp_path: Path) -> None:
    generated = generate_cavity_case(
        OpenFoamCavityConfig(property_file_layout=FOUNDATION), tmp_path
    )
    paths = set(generated.relative_paths)

    assert PHYSICAL in paths
    assert TRANSPORT not in paths
    assert generated.property_file_layout is FOUNDATION
    assert generated.property_file == PHYSICAL

    physical = _read(generated.root, PHYSICAL)
    assert "object      physicalProperties;" in physical
    assert "nu              [0 2 -1 0 0 0 0] 0.01;" in physical
    # Foundation v11/v12 physicalProperties must not carry the legacy key.
    assert "transportModel" not in physical


def test_foundation_cavity_preserves_shared_files(tmp_path: Path) -> None:
    legacy = generate_cavity_case(OpenFoamCavityConfig(), tmp_path / "legacy")
    foundation = generate_cavity_case(
        OpenFoamCavityConfig(property_file_layout=FOUNDATION), tmp_path / "foundation"
    )
    shared = ("0/U", "0/p", "system/blockMeshDict", "system/controlDict")
    for relative_path in shared:
        assert _read(legacy.root, relative_path) == _read(foundation.root, relative_path)


# --------------------------------------------------------------------------- #
# Duct generation                                                             #
# --------------------------------------------------------------------------- #


def test_legacy_duct_emits_transport_properties_only(tmp_path: Path) -> None:
    generated = generate_duct_case(OpenFoamDuctConfig(), tmp_path)
    paths = set(generated.relative_paths)

    assert TRANSPORT in paths
    assert PHYSICAL not in paths
    assert "constant/turbulenceProperties" in paths


def test_foundation_duct_emits_physical_properties_only(tmp_path: Path) -> None:
    generated = generate_duct_case(
        OpenFoamDuctConfig(property_file_layout="foundation_v12"), tmp_path
    )
    paths = set(generated.relative_paths)

    assert PHYSICAL in paths
    assert TRANSPORT not in paths
    # The laminar turbulenceProperties file is unaffected by the layout swap.
    assert "constant/turbulenceProperties" in paths

    physical = _read(generated.root, PHYSICAL)
    assert "nu              [0 2 -1 0 0 0 0] 1e-05;" in physical


# --------------------------------------------------------------------------- #
# Request/result flow                                                         #
# --------------------------------------------------------------------------- #


def test_request_flow_defaults_to_legacy(tmp_path: Path) -> None:
    result = generate_openfoam_case(default_cavity_request(tmp_path))

    assert result.status == "ok"
    assert result.metadata["property_file_layout"] == LEGACY.value
    assert result.metadata["property_file"] == TRANSPORT
    assert (
        result.metadata["property_file_diagnostic"]
        == OSW_OPENFOAM_TEMPLATE_LEGACY_TRANSPORT_PROPERTIES
    )
    rel = {path.relative_to(result.case_dir).as_posix() for path in result.generated_files}
    assert TRANSPORT in rel
    assert PHYSICAL not in rel


def test_request_flow_foundation_via_metadata(tmp_path: Path) -> None:
    base = default_cavity_request(tmp_path)
    request = OpenFOAMCaseRequest.from_dict(
        {**base.to_dict(), "metadata": {"property_file_layout": "foundation_v11_plus"}}
    )

    result = generate_openfoam_case(request)

    assert result.status == "ok"
    assert result.metadata["property_file_layout"] == FOUNDATION.value
    assert result.metadata["property_file"] == PHYSICAL
    assert (
        result.metadata["property_file_diagnostic"]
        == OSW_OPENFOAM_TEMPLATE_FOUNDATION_V12_PHYSICAL_PROPERTIES
    )
    rel = {path.relative_to(result.case_dir).as_posix() for path in result.generated_files}
    assert PHYSICAL in rel
    assert TRANSPORT not in rel


def test_request_flow_foundation_duct_via_metadata(tmp_path: Path) -> None:
    base = default_duct_request(tmp_path)
    request = OpenFOAMCaseRequest.from_dict(
        {**base.to_dict(), "metadata": {"property_file_layout": "foundation_v12"}}
    )

    result = generate_openfoam_case(request)

    rel = {path.relative_to(result.case_dir).as_posix() for path in result.generated_files}
    assert PHYSICAL in rel
    assert TRANSPORT not in rel


def test_request_flow_unknown_layout_reports_error(tmp_path: Path) -> None:
    base = default_cavity_request(tmp_path)
    request = OpenFOAMCaseRequest.from_dict(
        {**base.to_dict(), "metadata": {"property_file_layout": "totally_unknown"}}
    )

    result = generate_openfoam_case(request)

    assert result.status == "error"
    assert result.diagnostics.has_errors
    assert OSW_OPENFOAM_TEMPLATE_VARIANT_UNSUPPORTED in result.diagnostics.summary()


# --------------------------------------------------------------------------- #
# CLI surface                                                                 #
# --------------------------------------------------------------------------- #


def test_cli_exposes_property_file_layout_option() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    # Locate the openfoam-write-case subparser and confirm its choices.
    write_parser = None
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict) and "openfoam-write-case" in choices:
            write_parser = choices["openfoam-write-case"]
            break
    assert write_parser is not None
    sub_help = write_parser.format_help()
    assert "--property-file-layout" in sub_help
    assert "physicalProperties" in sub_help
    assert help_text  # parser builds without error


def test_cli_legacy_option_preserves_legacy_output(tmp_path: Path, capsys) -> None:
    out_dir = tmp_path / "cav_legacy"
    code = main(
        [
            "openfoam-write-case",
            "--template",
            "cavity",
            "--out-dir",
            str(out_dir),
            "--property-file-layout",
            "legacy",
        ]
    )
    captured = capsys.readouterr()

    assert code == 0
    assert (out_dir / "constant" / "transportProperties").exists()
    assert not (out_dir / "constant" / "physicalProperties").exists()
    assert "Property file layout: legacy" in captured.out


def test_cli_default_is_legacy(tmp_path: Path, capsys) -> None:
    out_dir = tmp_path / "cav_default"
    code = main(["openfoam-write-case", "--template", "cavity", "--out-dir", str(out_dir)])
    capsys.readouterr()

    assert code == 0
    assert (out_dir / "constant" / "transportProperties").exists()
    assert not (out_dir / "constant" / "physicalProperties").exists()


def test_cli_foundation_option_emits_physical_properties(tmp_path: Path, capsys) -> None:
    out_dir = tmp_path / "cav_foundation"
    code = main(
        [
            "openfoam-write-case",
            "--template",
            "cavity",
            "--out-dir",
            str(out_dir),
            "--property-file-layout",
            "foundation_v11_plus",
        ]
    )
    captured = capsys.readouterr()

    assert code == 0
    assert (out_dir / "constant" / "physicalProperties").exists()
    assert not (out_dir / "constant" / "transportProperties").exists()
    assert "Property file layout: foundation_v11_plus" in captured.out
    assert "Property file: constant/physicalProperties" in captured.out


def test_cli_foundation_duct_emits_physical_properties(tmp_path: Path, capsys) -> None:
    out_dir = tmp_path / "duct_foundation"
    code = main(
        [
            "openfoam-write-case",
            "--template",
            "duct",
            "--out-dir",
            str(out_dir),
            "--property-file-layout",
            "foundation_v11_plus",
        ]
    )
    capsys.readouterr()

    assert code == 0
    assert (out_dir / "constant" / "physicalProperties").exists()
    assert not (out_dir / "constant" / "transportProperties").exists()


# --------------------------------------------------------------------------- #
# No live solver execution                                                    #
# --------------------------------------------------------------------------- #


def test_case_generator_source_has_no_solver_execution() -> None:
    """The generator must never spawn OpenFOAM; property files are pure text."""

    from osw.solvers.openfoam import case_generator

    source = Path(case_generator.__file__).read_text(encoding="utf-8")
    for forbidden in ("subprocess", "os.system", "Popen", "check_call", "check_output"):
        assert forbidden not in source, forbidden
