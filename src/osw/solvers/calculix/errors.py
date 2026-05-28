"""CalculiX adapter exceptions."""

from __future__ import annotations


class CalculiXAdapterError(ValueError):
    """Raised when a prepare-only CalculiX adapter operation cannot continue."""


class CalculiXProjectMappingError(CalculiXAdapterError):
    """Raised when ProjectSchema data cannot be mapped to a CalculiX deck."""
