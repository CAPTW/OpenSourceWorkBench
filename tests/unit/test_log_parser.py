from __future__ import annotations

from osw.solvers.log_parser import GenericLogParser, LogSeverity, parse_run_log


def test_warning_detection() -> None:
    events = GenericLogParser().parse("warning: mesh skewness is high\n")

    assert events[0].severity == LogSeverity.WARNING
    assert events[0].line_no == 1


def test_error_detection() -> None:
    events = GenericLogParser().parse("fatal error: failed to read input\n")

    assert events[0].severity == LogSeverity.ERROR
    assert events[0].line_number == 1


def test_arbitrary_text_does_not_crash() -> None:
    events = GenericLogParser().parse("plain line\nanother plain line\n")

    assert events == []


def test_unicode_text_does_not_crash() -> None:
    events = GenericLogParser().parse("경고 warning Δ residual=1e-3\n")

    assert events[0].severity == LogSeverity.WARNING


def test_residual_and_progress_detection() -> None:
    events = GenericLogParser().parse("Iteration 10 residual p=1e-4\n")

    assert {event.severity for event in events} == {LogSeverity.RESIDUAL}


def test_tail_summary() -> None:
    summary = GenericLogParser().tail_summary("a\nb\nc\n", lines=2)

    assert summary == "b\nc"


def test_legacy_parse_run_log_name() -> None:
    findings = parse_run_log("line 1\nwarning: mesh quality\nfatal error: no input\n")

    assert [finding.severity for finding in findings] == [
        LogSeverity.WARNING,
        LogSeverity.ERROR,
    ]
    assert findings[0].line_number == 2
    assert findings[1].line_number == 3
