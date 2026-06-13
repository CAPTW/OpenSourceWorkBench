from __future__ import annotations

import pytest

from osw.cli.main import build_parser

EXPECTED_COMMANDS = {
    "gui",
    "project-demo-json",
    "project-validate",
    "plugins-list",
    "plugins-health",
    "plugins-install-folder",
    "plugins-install-zip",
    "plugins-installed",
    "plugins-uninstall",
    "plugins-quarantine-list",
    "runner-fake-smoke",
    "mesh-formats",
    "gmsh-check",
    "gmsh-write-geo",
    "mscript-preview",
    "octave-check",
    "mat-info",
    "report-export",
    "report-summary",
    "calculix-check",
    "feaspec-calculix-export-preview",
    "feaspec-calculix-export-write",
    "openfoam-check",
    "result-catalog-inspect",
    "field-dataset-inspect",
    "coolprop-check",
    "cantera-check",
}


def _subcommand_names() -> set[str]:
    parser = build_parser()
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict):
            return set(choices)
    return set()


def test_packaging_quickstart_commands_are_registered() -> None:
    assert EXPECTED_COMMANDS.issubset(_subcommand_names())


@pytest.mark.parametrize("command", sorted(EXPECTED_COMMANDS))
def test_packaging_quickstart_commands_are_help_safe(
    command: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args([command, "--help"])

    assert exc_info.value.code == 0
    assert command in capsys.readouterr().out
