"""Cantera adapter errors."""

from __future__ import annotations


class CanteraAdapterError(RuntimeError):
    """Base error for bounded Cantera adapter failures."""


class CanteraDependencyMissingError(CanteraAdapterError):
    """Raised only by callers that explicitly request an exception on missing Cantera."""

