"""CoolProp adapter errors."""

from __future__ import annotations


class CoolPropAdapterError(RuntimeError):
    """Base error for bounded CoolProp adapter failures."""


class CoolPropDependencyMissingError(CoolPropAdapterError):
    """Raised only by callers that explicitly request an exception on missing CoolProp."""

