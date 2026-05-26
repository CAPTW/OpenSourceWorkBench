"""MATLAB/Octave script preview package."""

from __future__ import annotations

from .boundary_curve_bridge import (
    boundary_curve_from_mat_preview,
    boundary_curve_from_workspace_variables,
)
from .figure_capture import capture_existing_figures, capture_octave_figures
from .figure_dataset import FigureDataset, FigureDatasetError, FigureRecord
from .importer import (
    MScriptImportError,
    MScriptPreviewResult,
    MScriptReadResult,
    MScriptResultStatus,
    create_script_ref,
    import_mscript_preview,
    preview_mscript,
    preview_mscript_text,
    read_mscript_text,
)
from .mat_reader import (
    MatFilePreview,
    MatReader,
    MatReaderError,
    MatVariableSummary,
    export_mat_variable_csv,
    read_mat_file,
)
from .octave_runner import OctaveExecutionNotConfirmed, OctaveRunner
from .safety_scan import scan_mscript_text, strip_mscript_comment
from .script_model import (
    FunctionSignature,
    MScriptKind,
    MScriptPreview,
    PlotHint,
    SafetyFinding,
    SafetyScanResult,
    SafetySeverity,
    ScriptKind,
    ScriptLanguage,
    ScriptPreview,
)
from .workspace_extractor import extract_figure_dataset, extract_figure_paths

__all__ = [
    "FigureDataset",
    "FigureDatasetError",
    "FigureRecord",
    "MScriptImportError",
    "MScriptPreviewResult",
    "MScriptReadResult",
    "MScriptResultStatus",
    "MScriptKind",
    "MScriptPreview",
    "MatFilePreview",
    "MatReader",
    "MatReaderError",
    "MatVariableSummary",
    "FunctionSignature",
    "PlotHint",
    "OctaveExecutionNotConfirmed",
    "OctaveRunner",
    "SafetyFinding",
    "SafetyScanResult",
    "SafetySeverity",
    "ScriptKind",
    "ScriptLanguage",
    "ScriptPreview",
    "boundary_curve_from_mat_preview",
    "boundary_curve_from_workspace_variables",
    "capture_existing_figures",
    "capture_octave_figures",
    "create_script_ref",
    "export_mat_variable_csv",
    "extract_figure_dataset",
    "extract_figure_paths",
    "import_mscript_preview",
    "preview_mscript",
    "preview_mscript_text",
    "read_mat_file",
    "read_mscript_text",
    "scan_mscript_text",
    "strip_mscript_comment",
]
