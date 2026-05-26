"""Errors for preview-only MATLAB/Octave script import."""

from __future__ import annotations


class MScriptImportError(RuntimeError):
    """Raised by compatibility APIs when `.m` preview cannot be created."""
