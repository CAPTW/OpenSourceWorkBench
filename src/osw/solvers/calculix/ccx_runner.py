"""Backend CalculiX `ccx` runner integration."""

from __future__ import annotations

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

CALCULIX_ARTIFACT_KINDS = {
    ".dat": "calculix_dat",
    ".frd": "calculix_frd",
    ".sta": "calculix_sta",
    ".cvg": "calculix_convergence",
    ".12d": "calculix_12d",
}


class CalculixCcxRunner:
    """Run prepared CalculiX input decks through backend runner services.

    This class is intentionally outside the GUI layer. It requires an existing
    `.inp` deck, runs `ccx <case_name>` from the deck directory, captures
    stdout/stderr through `ExternalCommandRunner`, and records known CalculiX
    artifacts created in the case directory.
    """

    def __init__(
        self,
        *,
        executable: str | Path = "ccx",
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
        """Resolve the configured `ccx` executable without running it."""

        return self.registry.resolve(self.executable if executable is None else executable)

    def run_input_deck(
        self,
        input_deck_path: str | Path,
        *,
        artifact_dir: str | Path | None = None,
        env: Mapping[str, str] | None = None,
        extra_args: Sequence[str] = (),
        timeout_policy: TimeoutPolicy | None = None,
    ) -> RunResult:
        """Run `ccx` from the input deck directory and collect known artifacts."""

        deck = Path(input_deck_path).expanduser().resolve()
        case_dir = deck.parent
        artifact_path = Path(artifact_dir).expanduser().resolve() if artifact_dir else case_dir
        if not deck.exists():
            diagnostics = DiagnosticReport()
            diagnostics.add_error(
                "calculix.input_deck_missing",
                f"CalculiX input deck does not exist: {deck}",
                path=str(deck),
            )
            return RunResult(
                status=RunStatus.FAILED,
                command=(str(self.executable), deck.stem),
                cwd=case_dir,
                artifact_dir=artifact_path,
                returncode=None,
                duration_seconds=0.0,
                log=RunLog(),
                artifacts=(RunArtifact(artifact_path, "directory", "Run artifact directory."),),
                diagnostics=diagnostics,
            )
        if deck.suffix.lower() != ".inp":
            diagnostics = DiagnosticReport()
            diagnostics.add_error(
                "calculix.input_deck_extension",
                f"CalculiX runner expects a .inp input deck, got: {deck.name}",
                path=str(deck),
            )
            return RunResult(
                status=RunStatus.FAILED,
                command=(str(self.executable), deck.stem),
                cwd=case_dir,
                artifact_dir=artifact_path,
                returncode=None,
                duration_seconds=0.0,
                log=RunLog(),
                artifacts=(RunArtifact(artifact_path, "directory", "Run artifact directory."),),
                diagnostics=diagnostics,
            )

        result = self.command_runner.run(
            self.executable,
            (deck.stem, *[str(arg) for arg in extra_args]),
            cwd=case_dir,
            artifact_dir=artifact_path,
            env=env,
            timeout_policy=timeout_policy,
        )
        result = self._with_ccx_diagnostics(result)
        return self._with_case_artifacts(result, case_dir, deck.stem)

    @staticmethod
    def _with_ccx_diagnostics(result: RunResult) -> RunResult:
        if result.status != RunStatus.MISSING_EXECUTABLE:
            return result
        diagnostics = DiagnosticReport()
        diagnostics.extend(result.diagnostics)
        diagnostics.add_error(
            "calculix.missing_executable",
            (
                "CalculiX ccx executable was not found. Install CalculiX on PATH "
                "or configure ExecutablePathRegistry before solver execution."
            ),
        )
        return replace(result, diagnostics=diagnostics)

    @staticmethod
    def _with_case_artifacts(result: RunResult, case_dir: Path, case_name: str) -> RunResult:
        artifacts = [RunArtifact(case_dir, "calculix_case_dir", "CalculiX case directory.")]
        for suffix, kind in CALCULIX_ARTIFACT_KINDS.items():
            path = case_dir / f"{case_name}{suffix}"
            if path.exists():
                artifacts.append(RunArtifact(path, kind, f"CalculiX {suffix} artifact."))
        return replace(result, artifacts=(*result.artifacts, *artifacts))
