"""Errors for the experimental FEASpec human review record layer."""

from __future__ import annotations


class FEASpecHumanReviewError(ValueError):
    """Raised when a human review record cannot be loaded or written."""


class FEASpecHumanReviewValidationError(FEASpecHumanReviewError):
    """Raised when human review record input has an invalid shape."""
