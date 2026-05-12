"""Preview-only `.m` importer."""

from __future__ import annotations

import re
from pathlib import Path

from .safety_scan import scan_mscript_text, strip_mscript_comment
from .script_model import MScriptKind, MScriptPreview

_FUNCTION_DECLARATION = re.compile(
    r"^\s*function(?:\s+(?:\[[^\]]+\]|\w+)\s*=\s*)?\s*(?P<name>[A-Za-z_]\w*)",
    re.IGNORECASE,
)
_PLOT_CALL = re.compile(r"\b(plot|figure|surf|mesh|contour|scatter)\s*\(", re.IGNORECASE)


class MScriptImportError(RuntimeError):
    """Raised when a preview-only `.m` import cannot be created."""


def import_mscript_preview(path: str | Path) -> MScriptPreview:
    script_path = Path(path)
    if script_path.suffix.lower() != ".m":
        msg = "Only .m script preview is supported in this importer."
        raise MScriptImportError(msg)
    if not script_path.exists():
        msg = f"M-script file does not exist: {script_path}"
        raise MScriptImportError(msg)

    try:
        text = script_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = script_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        msg = f"Could not read M-script file {script_path}: {exc}"
        raise MScriptImportError(msg) from exc

    return preview_mscript_text(text, source=str(script_path), fallback_name=script_path.stem)


def preview_mscript_text(
    text: str,
    *,
    source: str = "<memory>",
    fallback_name: str = "script",
) -> MScriptPreview:
    lines = text.splitlines()
    code_lines = [strip_mscript_comment(line).strip() for line in lines]
    executable_lines = [line for line in code_lines if line]
    comment_count = sum(1 for line in lines if line.strip().startswith("%"))
    first_executable = executable_lines[0] if executable_lines else ""

    function_match = _FUNCTION_DECLARATION.match(first_executable)
    if function_match:
        kind = MScriptKind.FUNCTION
        entrypoint = function_match.group("name")
        name = entrypoint
    else:
        kind = MScriptKind.SCRIPT
        entrypoint = None
        name = fallback_name

    return MScriptPreview(
        source=source,
        kind=kind,
        name=name,
        entrypoint=entrypoint,
        line_count=len(lines),
        executable_line_count=len(executable_lines),
        comment_line_count=comment_count,
        contains_plot_call=any(_PLOT_CALL.search(line) for line in executable_lines),
        safety=scan_mscript_text(text, source=source),
    )
