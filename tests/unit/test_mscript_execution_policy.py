from __future__ import annotations

import json

from osw.scripts.mscript.execution_policy import (
    DEFAULT_OCTAVE_ARTIFACT_PATTERNS,
    OctaveExecutionPolicy,
    SafetyGateStatus,
    safety_gate_status,
)
from osw.scripts.mscript.script_model import SafetyFinding


def test_default_policy_blocks_high_and_blocked_findings() -> None:
    policy = OctaveExecutionPolicy()
    findings = (
        SafetyFinding(severity="high", token="system", line_no=1),
        SafetyFinding(severity="blocked", token=".mlapp", line_no=2),
    )

    assert safety_gate_status(findings, policy) is SafetyGateStatus.BLOCKED_BY_SAFETY


def test_allow_high_risk_allows_high_but_not_blocked() -> None:
    policy = OctaveExecutionPolicy(allow_high_risk=True)

    assert safety_gate_status(
        (SafetyFinding(severity="high", token="system", line_no=1),),
        policy,
    ) is SafetyGateStatus.ALLOWED
    assert safety_gate_status(
        (SafetyFinding(severity="blocked", token=".slx", line_no=1),),
        policy,
    ) is SafetyGateStatus.BLOCKED_BY_SAFETY


def test_allow_blocked_allows_blocked_findings() -> None:
    policy = OctaveExecutionPolicy(allow_high_risk=True, allow_blocked=True)

    assert safety_gate_status(
        (SafetyFinding(severity="blocked", token=".mlapp", line_no=1),),
        policy,
    ) is SafetyGateStatus.ALLOWED


def test_policy_defaults_are_positive_and_collect_artifacts() -> None:
    policy = OctaveExecutionPolicy()

    assert policy.timeout_seconds > 0
    assert policy.artifact_patterns == DEFAULT_OCTAVE_ARTIFACT_PATTERNS
    assert policy.capture_artifacts is True
    assert "*.csv" in policy.artifact_patterns


def test_policy_round_trips_json() -> None:
    policy = OctaveExecutionPolicy(
        timeout_seconds=5,
        allow_high_risk=True,
        artifact_patterns=("*.csv",),
        env_overrides={"OSW_TEST": "1"},
    )

    restored = OctaveExecutionPolicy.from_dict(json.loads(json.dumps(policy.to_dict())))

    assert restored.timeout_seconds == 5
    assert restored.allow_high_risk is True
    assert restored.artifact_patterns == ("*.csv",)
    assert restored.env_overrides == {"OSW_TEST": "1"}
