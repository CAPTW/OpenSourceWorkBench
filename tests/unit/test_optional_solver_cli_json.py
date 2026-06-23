from __future__ import annotations

import importlib
import json

from osw.cli import main as cli_main
from osw.experimental.optional_solvers import (
    OptionalSolverDiscoveryReport,
    OptionalSolverEnvironmentHintDiscovery,
    OptionalSolverExecutableDiscovery,
    OptionalSolverHealthState,
    OptionalSolverStackDiscovery,
)

cli_module = importlib.import_module("osw.cli.main")


def test_optional_solver_doctor_json_parses_and_is_redacted_by_default(
    monkeypatch,
    capsys,
) -> None:
    report = OptionalSolverDiscoveryReport(
        stacks=(
            OptionalSolverStackDiscovery(
                stack_id="calculix",
                display_name="CalculiX",
                related_issue=8,
                health_state=OptionalSolverHealthState.DISCOVERED,
                executables=(
                    OptionalSolverExecutableDiscovery(
                        identifier="ccx",
                        found=True,
                        redacted_path="<redacted:ccx.exe>",
                    ),
                ),
                environment_hints=(
                    OptionalSolverEnvironmentHintDiscovery(
                        name="CALCULIX_HOME",
                        present=True,
                        redacted_value="<redacted>",
                    ),
                ),
            ),
        )
    )
    monkeypatch.setattr(cli_module, "_optional_solver_doctor_report", lambda *_a, **_k: report)
    monkeypatch.setattr(cli_module, "_select_optional_solver_manifests", lambda _ids: ())

    exit_code = cli_main(["optional-solver-doctor", "--all", "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    text = json.dumps(payload)
    assert "C:/Users/USER" not in text
    assert "<redacted:ccx.exe>" in text
    assert "<redacted>" in text


def test_optional_solver_list_json_includes_all_six_stack_ids(capsys) -> None:
    exit_code = cli_main(["optional-solver-list", "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert len(payload["stacks"]) == 6
