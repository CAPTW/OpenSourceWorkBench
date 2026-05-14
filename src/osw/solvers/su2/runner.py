"""Backend SU2 runner wrapper built on ExternalCommandRunner."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from osw.core.diagnostics import DiagnosticReport
from osw.core.run_manager import ExecutablePathRegistry
from osw.solvers.runner import ExternalCommandRunner, RunResult, RunStatus, TimeoutPolicy


class Su2Runner:
    """Run a prepared SU2 config through the backend command runner."""

    def __init__(
        self,
        *,
        executable: str = "SU2_CFD",
        registry: ExecutablePathRegistry | None = None,
        timeout_policy: TimeoutPolicy | None = None,
        command_runner: ExternalCommandRunner | None = None,
    ) -> None:
        self.executable = executable
        self.registry = registry or ExecutablePathRegistry()
        self.timeout_policy = timeout_policy or TimeoutPolicy()
        self.command_runner = command_runner or ExternalCommandRunner(
            registry=self.registry,
            timeout_policy=self.timeout_policy,
        )

    def run_config(
        self,
        config_path: str | Path,
        *,
        artifact_dir: str | Path,
        timeout_policy: TimeoutPolicy | None = None,
    ) -> RunResult:
        cfg_path = Path(config_path).expanduser().resolve()
        result = self.command_runner.run(
            self.executable,
            (cfg_path.name,),
            cwd=cfg_path.parent,
            artifact_dir=artifact_dir,
            timeout_policy=timeout_policy or self.timeout_policy,
        )
        if result.status is RunStatus.MISSING_EXECUTABLE:
            diagnostics = DiagnosticReport()
            diagnostics.add_error(
                "su2.missing_executable",
                (
                    f"{self.executable} executable was not found. Configure it in "
                    f"ExecutablePathRegistry or install {self.executable} on PATH "
                    "before running SU2."
                ),
            )
            diagnostics.extend(result.diagnostics)
            return replace(result, diagnostics=diagnostics)
        return result
