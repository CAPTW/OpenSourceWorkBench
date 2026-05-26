from __future__ import annotations

from pathlib import Path

from osw.scripts.mscript.safety_scan import scan_mscript_text

FIXTURES = Path(__file__).parents[1] / "fixtures" / "mscript"


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
    assert all(finding.severity == "high" for finding in result.findings)
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


def test_external_command_shell_escape_detection() -> None:
    result = scan_mscript_text(
        (FIXTURES / "dangerous_system.m").read_text(encoding="utf-8"),
        source="dangerous_system.m",
    )

    tokens = [finding.token for finding in result.findings]
    assert {"system", "unix", "dos", "!"}.issubset(tokens)
    assert all(finding.severity == "high" for finding in result.findings)
    assert result.findings[0].line_no == 3


def test_destructive_network_path_and_dynamic_tokens_are_reported() -> None:
    destructive = scan_mscript_text(
        (FIXTURES / "dangerous_delete.m").read_text(encoding="utf-8"),
        source="dangerous_delete.m",
    )
    network = scan_mscript_text(
        (FIXTURES / "network_webread.m").read_text(encoding="utf-8"),
        source="network_webread.m",
    )
    path_mutation = scan_mscript_text(
        (FIXTURES / "path_mutation.m").read_text(encoding="utf-8"),
        source="path_mutation.m",
    )
    dynamic = scan_mscript_text(
        """
        eval('x = 1');
        run('other.m');
        source('other.m');
        """,
        source="dynamic.m",
    )

    assert [finding.token for finding in destructive.findings] == ["delete", "rmdir"]
    assert {finding.token for finding in network.findings} == {"webread", "urlread"}
    assert {finding.token for finding in path_mutation.findings} == {
        "cd",
        "addpath",
        "setenv",
    }
    assert all(finding.severity == "warning" for finding in path_mutation.findings)
    assert {finding.token for finding in dynamic.findings} == {"eval", "run", "source"}
    assert all(finding.severity == "high" for finding in dynamic.findings)


def test_simulink_and_app_designer_tokens_are_out_of_scope() -> None:
    result = scan_mscript_text(
        (FIXTURES / "simulink_out_of_scope.m").read_text(encoding="utf-8"),
        source="simulink_out_of_scope.m",
    )

    assert {finding.token for finding in result.findings} >= {
        ".slx",
        ".mlapp",
        "open_system",
        "sim",
    }
    assert all(finding.severity == "blocked" for finding in result.findings)
    assert "out of scope" in result.findings[0].message.lower()


def test_unicode_text_does_not_crash() -> None:
    result = scan_mscript_text("α = 1;\nplot(α, α);\n% system('ignored')\n", source="unicode.m")

    assert result.findings == ()
