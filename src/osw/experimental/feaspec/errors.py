"""Errors raised by the experimental FEASpec model package."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


class FEASpecModelError(ValueError):
    """Raised when FEASpec data cannot be parsed as a model document."""


class FEASpecDiagnosticError(FEASpecModelError):
    """Raised when FEASpec basic checks find blocking diagnostics."""

    def __init__(self, diagnostics: Sequence[Any]) -> None:
        self.diagnostics = tuple(diagnostics)
        summary = "; ".join(_diagnostic_summary(diagnostic) for diagnostic in self.diagnostics)
        super().__init__(summary or "FEASpec basic checks failed.")


def _diagnostic_summary(diagnostic: Any) -> str:
    code = getattr(diagnostic, "code", "")
    message = getattr(diagnostic, "message", "")
    if code and message:
        return f"{code}: {message}"
    if code:
        return str(code)
    return str(message or diagnostic)
