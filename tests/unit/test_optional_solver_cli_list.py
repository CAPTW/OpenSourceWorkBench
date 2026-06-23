from __future__ import annotations

import json

from osw.cli.main import main

EXPECTED_STACKS = {
    "gmsh",
    "octave",
    "calculix",
    "openfoam",
    "coolprop_cantera",
    "pyvista_meshio",
}


def test_optional_solver_list_text_succeeds(capsys) -> None:
    exit_code = main(["optional-solver-list", "--format", "text"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "OSW optional solver stacks" in output
    for stack_id in EXPECTED_STACKS:
        assert stack_id in output


def test_optional_solver_list_json_parses(capsys) -> None:
    exit_code = main(["optional-solver-list", "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert {item["stack_id"] for item in payload["stacks"]} == EXPECTED_STACKS
    assert payload["passive_only"] is True
    assert payload["external_solvers_bundled"] is False


def test_optional_solver_list_can_include_requirements(capsys) -> None:
    exit_code = main(
        ["optional-solver-list", "--format", "json", "--include-requirements"]
    )

    payload = json.loads(capsys.readouterr().out)
    calculix = next(item for item in payload["stacks"] if item["stack_id"] == "calculix")
    assert exit_code == 0
    assert calculix["executable_requirements"][0]["identifier"] == "ccx"
