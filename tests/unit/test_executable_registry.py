from __future__ import annotations

import sys
from pathlib import Path

from osw.core.diagnostics import DiagnosticCode
from osw.core.executables import ExecutablePathRegistry


def test_registry_resolves_configured_executable_path() -> None:
    registry = ExecutablePathRegistry().register("python", sys.executable)

    result = registry.resolve("python")

    assert result.found
    assert result.source == "configured"
    assert result.resolved_path == Path(sys.executable).resolve()


def test_registry_resolves_path_executable_without_execution() -> None:
    result = ExecutablePathRegistry().resolve(Path(sys.executable))

    assert result.found
    assert result.source == "configured"


def test_missing_executable_returns_friendly_diagnostic() -> None:
    result = ExecutablePathRegistry().resolve("osw-missing-executable-for-registry-test")

    assert not result.found
    assert result.diagnostics.has_errors
    assert result.diagnostics.errors()[0].code == DiagnosticCode.EXECUTABLE_NOT_FOUND.value
    assert "Executable not found" in result.diagnostics.summary()


def test_registry_round_trips_configuration() -> None:
    registry = ExecutablePathRegistry().register(
        "python",
        sys.executable,
        aliases=["py"],
        env_var="OSW_TEST_PYTHON",
    )

    restored = ExecutablePathRegistry.from_dict(registry.to_dict())

    assert restored.resolve("py").found


def test_resolve_any_uses_first_available() -> None:
    result = ExecutablePathRegistry().resolve_any(
        ["osw-missing-executable-for-registry-test", sys.executable]
    )

    assert result.found
