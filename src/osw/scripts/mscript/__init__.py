"""MATLAB/Octave script preview package."""

from __future__ import annotations

from .importer import MScriptImportError, import_mscript_preview, preview_mscript_text
from .octave_runner import OctaveExecutionNotConfirmed, OctaveRunner
from .safety_scan import scan_mscript_text, strip_mscript_comment
from .script_model import MScriptKind, MScriptPreview, SafetyFinding, SafetyScanResult

__all__ = [
    "MScriptImportError",
    "MScriptKind",
    "MScriptPreview",
    "OctaveExecutionNotConfirmed",
    "OctaveRunner",
    "SafetyFinding",
    "SafetyScanResult",
    "import_mscript_preview",
    "preview_mscript_text",
    "scan_mscript_text",
    "strip_mscript_comment",
]
