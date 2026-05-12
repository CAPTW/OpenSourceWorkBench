"""MATLAB/Octave script preview package."""

from __future__ import annotations

from .figure_capture import capture_existing_figures, capture_octave_figures
from .figure_dataset import FigureDataset, FigureDatasetError, FigureRecord
from .importer import MScriptImportError, import_mscript_preview, preview_mscript_text
from .octave_runner import OctaveExecutionNotConfirmed, OctaveRunner
from .safety_scan import scan_mscript_text, strip_mscript_comment
from .script_model import MScriptKind, MScriptPreview, SafetyFinding, SafetyScanResult
from .workspace_extractor import extract_figure_dataset, extract_figure_paths

__all__ = [
    "FigureDataset",
    "FigureDatasetError",
    "FigureRecord",
    "MScriptImportError",
    "MScriptKind",
    "MScriptPreview",
    "OctaveExecutionNotConfirmed",
    "OctaveRunner",
    "SafetyFinding",
    "SafetyScanResult",
    "capture_existing_figures",
    "capture_octave_figures",
    "extract_figure_dataset",
    "extract_figure_paths",
    "import_mscript_preview",
    "preview_mscript_text",
    "scan_mscript_text",
    "strip_mscript_comment",
]
