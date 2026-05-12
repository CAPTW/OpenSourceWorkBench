from __future__ import annotations

from osw.scripts.mscript.safety_scan import scan_mscript_text


def test_safe_script_has_no_findings() -> None:
    result = scan_mscript_text(
        """
        x = linspace(0, 1, 5);
        y = sin(x);
        plot(x, y);
        """,
        source="safe.m",
    )

    assert result.findings == ()
    assert result.is_safe_for_preview is True


def test_dangerous_commands_are_reported_with_line_numbers() -> None:
    result = scan_mscript_text(
        """
        system('echo unsafe');
        unix('whoami');
        delete('output.txt');
        rmdir('scratch');
        webread('https://example.test');
        urlread('https://example.test');
        """,
        source="unsafe.m",
    )

    functions = [finding.function for finding in result.findings]
    assert functions == ["system", "unix", "delete", "rmdir", "webread", "urlread"]
    assert result.findings[0].line == 2
    assert all(finding.severity == "danger" for finding in result.findings)
    assert result.is_safe_for_preview is False


def test_file_io_usage_is_warned_but_not_blocked_for_preview() -> None:
    result = scan_mscript_text(
        """
        fid = fopen('data.txt', 'w');
        fdelete('old.txt');
        """,
        source="file_io.m",
    )

    assert [finding.function for finding in result.findings] == ["fopen", "fdelete"]
    assert all(finding.severity == "warning" for finding in result.findings)
    assert result.is_safe_for_preview is True


def test_comments_do_not_trigger_safety_findings() -> None:
    result = scan_mscript_text(
        """
        % system('echo ignored');
        x = 1; % delete('ignored.txt')
        """,
        source="comments.m",
    )

    assert result.findings == ()
