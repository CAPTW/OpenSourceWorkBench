from __future__ import annotations

from osw.experimental.optional_solvers import discover_builtin_optional_solvers

EXPECTED_STACKS = {
    "gmsh",
    "octave",
    "calculix",
    "openfoam",
    "coolprop_cantera",
    "pyvista_meshio",
}


def test_builtin_discovery_returns_six_stack_ids_without_local_environment() -> None:
    report = discover_builtin_optional_solvers(
        executable_resolver=lambda _name: None,
        python_package_resolver=lambda _name: None,
        environment_resolver=lambda _name: None,
    )

    assert {stack.stack_id for stack in report.stacks} == EXPECTED_STACKS
    assert len(report.stacks) == 6


def test_builtin_discovery_uses_injected_resolvers_for_all_presence() -> None:
    report = discover_builtin_optional_solvers(
        executable_resolver=lambda name: f"C:/tools/{name}.exe",
        python_package_resolver=lambda _name: {"found": True, "version": "1.0"},
        environment_resolver=lambda _name: "C:/env",
    )

    states = {stack.stack_id: stack.health_state.value for stack in report.stacks}

    assert states["gmsh"] == "discovered"
    assert states["octave"] == "discovered"
    assert states["calculix"] == "discovered"
    assert states["openfoam"] == "discovered"
    assert states["coolprop_cantera"] == "discovered"
    assert states["pyvista_meshio"] == "discovered"


def test_builtin_discovery_does_not_emit_smoke_pass_or_failure() -> None:
    report = discover_builtin_optional_solvers(
        executable_resolver=lambda _name: None,
        python_package_resolver=lambda _name: None,
        environment_resolver=lambda _name: None,
    )

    assert {stack.health_state.value for stack in report.stacks}.isdisjoint(
        {"smoke_passed", "smoke_failed"}
    )
