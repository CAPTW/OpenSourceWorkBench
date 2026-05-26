"""Execution policy for explicit GNU Octave script runs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from osw.core.diagnostics import DiagnosticReport
from osw.solvers.runner import TimeoutPolicy

from .script_model import SafetyFinding, SafetySeverity

DEFAULT_OCTAVE_ARTIFACT_PATTERNS = (
    "*.txt",
    "*.csv",
    "*.png",
    "*.svg",
    "*.pdf",
    "*.mat",
    "*.dat",
    "*.json",
)


class SafetyGateStatus(StrEnum):
    ALLOWED = "allowed"
    BLOCKED_BY_SAFETY = "blocked_by_safety"


@dataclass(frozen=True)
class OctaveExecutionPolicy:
    """Serializable controls for one explicit Octave execution request."""

    timeout_seconds: float = 30.0
    allow_high_risk: bool = False
    allow_blocked: bool = False
    isolate_workspace: bool = True
    copy_script_to_workspace: bool = True
    capture_artifacts: bool = True
    artifact_patterns: tuple[str, ...] = field(
        default_factory=lambda: DEFAULT_OCTAVE_ARTIFACT_PATTERNS
    )
    env_overrides: dict[str, str] = field(default_factory=dict)
    kill_grace_seconds: float = 1.0
    warn_missing_artifacts: bool = False

    def __init__(
        self,
        timeout_seconds: float = 30.0,
        allow_high_risk: bool = False,
        allow_blocked: bool = False,
        isolate_workspace: bool = True,
        copy_script_to_workspace: bool = True,
        capture_artifacts: bool = True,
        artifact_patterns: Iterable[str] | None = None,
        env_overrides: Mapping[str, str] | None = None,
        kill_grace_seconds: float = 1.0,
        warn_missing_artifacts: bool = False,
    ) -> None:
        object.__setattr__(self, "timeout_seconds", float(timeout_seconds))
        object.__setattr__(self, "allow_high_risk", bool(allow_high_risk))
        object.__setattr__(self, "allow_blocked", bool(allow_blocked))
        object.__setattr__(self, "isolate_workspace", bool(isolate_workspace))
        object.__setattr__(self, "copy_script_to_workspace", bool(copy_script_to_workspace))
        object.__setattr__(self, "capture_artifacts", bool(capture_artifacts))
        object.__setattr__(
            self,
            "artifact_patterns",
            tuple(
                str(pattern)
                for pattern in (
                    artifact_patterns or DEFAULT_OCTAVE_ARTIFACT_PATTERNS
                )
            ),
        )
        object.__setattr__(
            self,
            "env_overrides",
            {str(key): str(value) for key, value in (env_overrides or {}).items()},
        )
        object.__setattr__(self, "kill_grace_seconds", float(kill_grace_seconds))
        object.__setattr__(self, "warn_missing_artifacts", bool(warn_missing_artifacts))

    def timeout_policy(self) -> TimeoutPolicy:
        return TimeoutPolicy(
            timeout_seconds=self.timeout_seconds,
            kill_grace_seconds=self.kill_grace_seconds,
        )

    def diagnostics(self) -> DiagnosticReport:
        report = DiagnosticReport()
        if self.timeout_seconds <= 0:
            report.add_error(
                "octave-timeout-invalid",
                "Octave timeout must be greater than zero seconds.",
                hint="Use a positive timeout for script execution.",
            )
        if self.kill_grace_seconds < 0:
            report.add_error(
                "octave-kill-grace-invalid",
                "Octave kill grace period cannot be negative.",
                hint="Use zero or a positive grace period.",
            )
        if self.allow_blocked and not self.allow_high_risk:
            report.add_warning(
                "octave-policy-blocked-implies-high-risk",
                "Allowing blocked findings also allows high-risk findings.",
                hint="Use this only for trusted fixtures in an isolated workspace.",
            )
        return report

    def to_dict(self) -> dict[str, Any]:
        return {
            "timeout_seconds": self.timeout_seconds,
            "allow_high_risk": self.allow_high_risk,
            "allow_blocked": self.allow_blocked,
            "isolate_workspace": self.isolate_workspace,
            "copy_script_to_workspace": self.copy_script_to_workspace,
            "capture_artifacts": self.capture_artifacts,
            "artifact_patterns": list(self.artifact_patterns),
            "env_overrides": dict(self.env_overrides),
            "kill_grace_seconds": self.kill_grace_seconds,
            "warn_missing_artifacts": self.warn_missing_artifacts,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> OctaveExecutionPolicy:
        return cls(
            timeout_seconds=float(data.get("timeout_seconds", 30.0)),
            allow_high_risk=bool(data.get("allow_high_risk", False)),
            allow_blocked=bool(data.get("allow_blocked", False)),
            isolate_workspace=bool(data.get("isolate_workspace", True)),
            copy_script_to_workspace=bool(data.get("copy_script_to_workspace", True)),
            capture_artifacts=bool(data.get("capture_artifacts", True)),
            artifact_patterns=tuple(
                str(item)
                for item in data.get(
                    "artifact_patterns",
                    DEFAULT_OCTAVE_ARTIFACT_PATTERNS,
                )
            ),
            env_overrides={
                str(key): str(value)
                for key, value in dict(data.get("env_overrides", {}) or {}).items()
            },
            kill_grace_seconds=float(data.get("kill_grace_seconds", 1.0)),
            warn_missing_artifacts=bool(data.get("warn_missing_artifacts", False)),
        )


def safety_gate_diagnostics(
    findings: Iterable[SafetyFinding],
    policy: OctaveExecutionPolicy,
) -> DiagnosticReport:
    report = DiagnosticReport()
    blocked = [
        finding
        for finding in findings
        if finding.severity == SafetySeverity.BLOCKED.value
    ]
    high = [
        finding
        for finding in findings
        if finding.severity == SafetySeverity.HIGH.value
    ]
    if blocked and not policy.allow_blocked:
        report.add_error(
            "mscript-execution-blocked-by-safety",
            "This script contains blocked MATLAB/Octave workflow signals and was not executed.",
            hint=(
                "Review safety findings. Blocked findings are out of scope for normal OSW v0.1 "
                "execution."
            ),
            metadata={"blocked_count": len(blocked)},
        )
    if high and not policy.allow_high_risk and not policy.allow_blocked:
        report.add_error(
            "mscript-execution-blocked-by-safety",
            "This script contains high-risk commands and was not executed.",
            hint="Review safety findings. Override only in a trusted, isolated environment.",
            metadata={"high_count": len(high)},
        )
    return report


def safety_gate_status(
    findings: Iterable[SafetyFinding],
    policy: OctaveExecutionPolicy,
) -> SafetyGateStatus:
    return (
        SafetyGateStatus.BLOCKED_BY_SAFETY
        if safety_gate_diagnostics(findings, policy).has_errors
        else SafetyGateStatus.ALLOWED
    )
