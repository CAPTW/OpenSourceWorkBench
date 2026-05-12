"""Safe GNU Octave runner for explicitly approved M-script execution."""

from __future__ import annotations

import shutil
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path

from osw.core.diagnostics import DiagnosticReport
from osw.core.run_manager import ExecutableLookup, ExecutablePathRegistry
from osw.solvers.runner import (
    ExternalCommandRunner,
    RunArtifact,
    RunLog,
    RunResult,
    RunStatus,
    TimeoutPolicy,
)

from .importer import MScriptImportError, import_mscript_preview
from .script_model import MScriptPreview


class OctaveExecutionNotConfirmed(RuntimeError):
    """Raised when Octave execution is requested without explicit approval."""


class OctaveRunner:
    """Run previewed `.m` scripts through GNU Octave from backend code only.

    Importing a script remains preview-only. Calling `run_script` requires
    `allow_execution=True`, which keeps execution opt-in and auditable.
    """

    def __init__(
        self,
        *,
        executable: str | Path = "octave",
        registry: ExecutablePathRegistry | None = None,
        command_runner: ExternalCommandRunner | None = None,
        timeout_policy: TimeoutPolicy | None = None,
    ) -> None:
        self.executable = executable
        self.registry = registry or ExecutablePathRegistry()
        self.timeout_policy = timeout_policy or TimeoutPolicy()
        self.command_runner = command_runner or ExternalCommandRunner(
            registry=self.registry,
            timeout_policy=self.timeout_policy,
        )

    def detect_executable(self, executable: str | Path | None = None) -> ExecutableLookup:
        """Resolve the configured GNU Octave executable without running it."""

        return self.registry.resolve(self.executable if executable is None else executable)

    def run_script(
        self,
        script_path: str | Path,
        *,
        artifact_dir: str | Path,
        allow_execution: bool = False,
        allow_unsafe: bool = False,
        env: Mapping[str, str] | None = None,
        extra_args: Sequence[str] = (),
        timeout_policy: TimeoutPolicy | None = None,
    ) -> RunResult:
        """Execute an `.m` script in an isolated artifact workspace.

        The source script is copied into `artifact_dir/octave_workspace`, then
        run from that temporary workspace. Artifacts created by the script are
        collected from the workspace and reported alongside stdout/stderr.
        """

        if not allow_execution:
            msg = "GNU Octave execution requires explicit execution approval."
            raise OctaveExecutionNotConfirmed(msg)

        artifact_path = Path(artifact_dir).expanduser().resolve()
        workspace = artifact_path / "octave_workspace"
        workspace.mkdir(parents=True, exist_ok=True)

        script = Path(script_path).expanduser().resolve()
        preview, preview_error = self._preview_script(script, artifact_path)
        if preview_error is not None:
            return preview_error
        if preview is not None and not preview.safety.is_safe_for_preview and not allow_unsafe:
            return self._blocked_result(
                artifact_path,
                workspace,
                "M-script safety scan found dangerous operations. Execution was blocked.",
            )

        workspace_script = workspace / script.name
        shutil.copy2(script, workspace_script)

        result = self.command_runner.run(
            self.executable,
            self._octave_args(workspace_script.name, extra_args),
            cwd=workspace,
            artifact_dir=artifact_path,
            env=env,
            timeout_policy=timeout_policy,
        )
        result = self._with_octave_diagnostics(result)
        return self._with_workspace_artifacts(result, workspace, workspace_script)

    @staticmethod
    def _octave_args(script_name: str, extra_args: Sequence[str]) -> tuple[str, ...]:
        return (
            "--quiet",
            "--no-gui",
            "--eval",
            f"run('{_octave_quote(script_name)}')",
            *[str(arg) for arg in extra_args],
        )

    def _preview_script(
        self,
        script: Path,
        artifact_path: Path,
    ) -> tuple[MScriptPreview | None, RunResult | None]:
        try:
            return import_mscript_preview(script), None
        except MScriptImportError as exc:
            diagnostics = DiagnosticReport()
            diagnostics.add_error("octave.preview_failed", str(exc), path=str(script))
            return (
                None,
                RunResult(
                    status=RunStatus.FAILED,
                    command=(str(self.executable),),
                    cwd=artifact_path,
                    artifact_dir=artifact_path,
                    returncode=None,
                    duration_seconds=0.0,
                    log=RunLog(),
                    artifacts=(RunArtifact(artifact_path, "directory", "Run artifact directory."),),
                    diagnostics=diagnostics,
                ),
            )

    def _blocked_result(
        self,
        artifact_path: Path,
        workspace: Path,
        message: str,
    ) -> RunResult:
        diagnostics = DiagnosticReport()
        diagnostics.add_error("octave.safety_blocked", message)
        return RunResult(
            status=RunStatus.FAILED,
            command=(str(self.executable),),
            cwd=workspace,
            artifact_dir=artifact_path,
            returncode=None,
            duration_seconds=0.0,
            log=RunLog(),
            artifacts=(
                RunArtifact(artifact_path, "directory", "Run artifact directory."),
                RunArtifact(workspace, "octave_workspace", "Temporary Octave workspace."),
            ),
            diagnostics=diagnostics,
        )

    @staticmethod
    def _with_octave_diagnostics(result: RunResult) -> RunResult:
        if result.status != RunStatus.MISSING_EXECUTABLE:
            return result
        diagnostics = DiagnosticReport()
        diagnostics.extend(result.diagnostics)
        diagnostics.add_error(
            "octave.missing_executable",
            (
                "GNU Octave executable was not found. Install GNU Octave on PATH "
                "or configure ExecutablePathRegistry before explicit execution."
            ),
        )
        return replace(result, diagnostics=diagnostics)

    @staticmethod
    def _with_workspace_artifacts(
        result: RunResult,
        workspace: Path,
        workspace_script: Path,
    ) -> RunResult:
        workspace_artifacts: list[RunArtifact] = [
            RunArtifact(workspace, "octave_workspace", "Temporary Octave workspace."),
        ]
        for artifact in sorted(workspace.rglob("*")):
            if artifact == workspace_script or not artifact.is_file():
                continue
            workspace_artifacts.append(
                RunArtifact(
                    artifact,
                    "octave_artifact",
                    "File generated in the Octave workspace.",
                )
            )
        return replace(result, artifacts=(*result.artifacts, *workspace_artifacts))


def _octave_quote(value: str) -> str:
    return value.replace("'", "''")
