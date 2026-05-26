from __future__ import annotations

from osw.core.diagnostics import DiagnosticCode, DiagnosticMessage, DiagnosticReport


def test_diagnostic_message_serializes_round_trips() -> None:
    message = DiagnosticMessage.error(
        DiagnosticCode.COMMAND_FAILED,
        "Command failed.",
        hint="Inspect stderr.",
        source="runner",
        field="command",
        path="case",
        command=("python", "-c"),
        return_code=7,
        metadata={"solver": "fake"},
    )

    restored = DiagnosticMessage.from_dict(message.to_dict())

    assert restored == message
    assert restored.code == "command-failed"
    assert restored.hint == "Inspect stderr."


def test_diagnostic_report_tracks_warnings_and_errors() -> None:
    report = DiagnosticReport()
    report.add_warning(DiagnosticCode.LOG_WARNING_DETECTED, "warning found", hint="review")
    report.add_error(DiagnosticCode.LOG_ERROR_DETECTED, "error found")

    assert report.has_warnings
    assert report.has_errors
    assert len(report.warnings()) == 1
    assert len(report.errors()) == 1
    assert "warning found" in report.summary()


def test_diagnostic_report_serializes_round_trips() -> None:
    report = DiagnosticReport()
    report.add_info(DiagnosticCode.COMMAND_COMPLETED, "complete")

    restored = DiagnosticReport.from_dict(report.to_dict())

    assert restored.messages == report.messages
