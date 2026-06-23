from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverDiscoveryDiagnostic,
    OptionalSolverDiscoveryOptions,
    OptionalSolverDiscoveryReport,
    OptionalSolverEnvironmentHintDiscovery,
    OptionalSolverExecutableDiscovery,
    OptionalSolverPathRedactionMode,
    OptionalSolverPythonPackageDiscovery,
    OptionalSolverStackDiscovery,
    discover_optional_solver_manifests,
    discover_optional_solver_stack,
    explain_optional_solver_discovery,
    parse_optional_solver_manifest_dict,
)


def _manifest():
    return parse_optional_solver_manifest_dict(
        {
            "stack_id": "example_stack",
            "display_name": "Example Stack",
            "related_issue": 6,
            "capabilities": ["example"],
            "executable_requirements": [
                {"identifier": "example-tool", "display_name": "Example Tool"}
            ],
            "python_package_requirements": [
                {"identifier": "example_pkg", "display_name": "Example Package"}
            ],
            "environment_variable_hints": ["EXAMPLE_HOME"],
            "smoke_test_description": "Passive discovery fixture.",
            "prepared_machine_notes": ["Prepared machine only."],
            "documentation_refs": ["docs/example.md"],
            "support_status": "experimental",
            "non_bundled_disclaimer": "External solvers are not bundled.",
            "safety_notes": [
                "No solver install.",
                "No dependency install.",
                "No bundled solver.",
            ],
        }
    )


def test_public_api_imports() -> None:
    assert OptionalSolverExecutableDiscovery
    assert OptionalSolverPythonPackageDiscovery
    assert OptionalSolverEnvironmentHintDiscovery
    assert OptionalSolverStackDiscovery
    assert OptionalSolverDiscoveryReport
    assert OptionalSolverDiscoveryDiagnostic
    assert OptionalSolverDiscoveryOptions
    assert OptionalSolverPathRedactionMode.REDACTED.value == "redacted"
    assert callable(discover_optional_solver_stack)
    assert callable(discover_optional_solver_manifests)
    assert callable(explain_optional_solver_discovery)


def test_discover_manifest_with_all_fake_requirements_missing() -> None:
    discovery = discover_optional_solver_stack(
        _manifest(),
        executable_resolver=lambda _name: None,
        python_package_resolver=lambda _name: None,
        environment_resolver=lambda _name: None,
    )

    assert discovery.health_state.value == "missing"
    assert discovery.executables[0].found is False
    assert discovery.python_packages[0].found is False
    codes = {diagnostic.code for diagnostic in discovery.diagnostics}
    assert "OSD_MISSING_EXECUTABLE" in codes
    assert "OSD_MISSING_PYTHON_PACKAGE" in codes
    assert "OSD_PASSIVE_ONLY" in codes


def test_injectable_resolvers_are_used() -> None:
    calls: dict[str, list[str]] = {"exe": [], "pkg": [], "env": []}

    def exe(name: str) -> str | None:
        calls["exe"].append(name)
        return "C:/Users/USER/tools/example-tool.exe"

    def pkg(name: str) -> dict[str, object] | None:
        calls["pkg"].append(name)
        return {"found": True, "version": "1.2.3"}

    def env(name: str) -> str | None:
        calls["env"].append(name)
        return "C:/Users/USER/example"

    discovery = discover_optional_solver_stack(
        _manifest(),
        executable_resolver=exe,
        python_package_resolver=pkg,
        environment_resolver=env,
    )

    assert calls == {
        "exe": ["example-tool"],
        "pkg": ["example_pkg"],
        "env": ["EXAMPLE_HOME"],
    }
    assert discovery.health_state.value == "discovered"
    assert discovery.executables[0].redacted_path == "<redacted:example-tool.exe>"
    assert discovery.executables[0].path == ""
    assert discovery.python_packages[0].version == "1.2.3"
    assert discovery.environment_hints[0].redacted_value == "<redacted>"


def test_full_path_and_environment_values_are_explicit_options() -> None:
    options = OptionalSolverDiscoveryOptions(
        path_redaction=OptionalSolverPathRedactionMode.FULL,
        include_environment_values=True,
    )
    discovery = discover_optional_solver_stack(
        _manifest(),
        options=options,
        executable_resolver=lambda _name: "C:/Users/USER/tools/example-tool.exe",
        python_package_resolver=lambda _name: "1.2.3",
        environment_resolver=lambda _name: "C:/Users/USER/example",
    )

    assert discovery.health_state.value == "discovered"
    assert discovery.executables[0].path == "C:/Users/USER/tools/example-tool.exe"
    assert discovery.environment_hints[0].value == "C:/Users/USER/example"


def test_discover_multiple_manifests_returns_report() -> None:
    report = discover_optional_solver_manifests(
        [_manifest()],
        options=OptionalSolverDiscoveryOptions(generated_at="2026-06-23T00:00:00Z"),
        executable_resolver=lambda _name: None,
        python_package_resolver=lambda _name: None,
        environment_resolver=lambda _name: None,
    )

    assert isinstance(report, OptionalSolverDiscoveryReport)
    assert report.generated_at == "2026-06-23T00:00:00Z"
    assert len(report.stacks) == 1
    assert "did not run smoke checks" in explain_optional_solver_discovery(report)
