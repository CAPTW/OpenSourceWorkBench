"""Semantic color tokens for the OpenSolver Workbench GUI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ThemeMode(StrEnum):
    """Persisted theme mode values."""

    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


REQUIRED_TOKEN_NAMES = (
    "bg_app",
    "bg_panel",
    "bg_panel_alt",
    "bg_viewport",
    "bg_header",
    "border",
    "border_strong",
    "text_primary",
    "text_secondary",
    "text_muted",
    "accent",
    "primary",
    "primary_hover",
    "success",
    "warning",
    "danger",
    "info",
    "chart_grid",
    "chart_axis",
    "mesh_line",
    "contour_low",
    "contour_mid",
    "contour_high",
)


@dataclass(frozen=True, slots=True)
class ThemeTokens:
    """Color tokens consumed by widgets, charts, and custom paint surfaces."""

    bg_app: str
    bg_panel: str
    bg_panel_alt: str
    bg_viewport: str
    bg_header: str
    border: str
    border_strong: str
    text_primary: str
    text_secondary: str
    text_muted: str
    accent: str
    primary: str
    primary_hover: str
    success: str
    warning: str
    danger: str
    info: str
    chart_grid: str
    chart_axis: str
    mesh_line: str
    contour_low: str
    contour_mid: str
    contour_high: str

    def as_dict(self) -> dict[str, str]:
        """Return token values keyed by semantic token name."""

        return {name: getattr(self, name) for name in REQUIRED_TOKEN_NAMES}


DARK_TOKENS = ThemeTokens(
    bg_app="#07111f",
    bg_panel="#0b1d31",
    bg_panel_alt="#0f2942",
    bg_viewport="#061426",
    bg_header="#081827",
    border="#1d3c5a",
    border_strong="#2d5c83",
    text_primary="#dcecff",
    text_secondary="#9eb8cf",
    text_muted="#66839d",
    accent="#00d5e6",
    primary="#2478ff",
    primary_hover="#3b8aff",
    success="#38d46a",
    warning="#ffba3a",
    danger="#ff5b5b",
    info="#4aa8ff",
    chart_grid="#193852",
    chart_axis="#6f90aa",
    mesh_line="#2b7cff",
    contour_low="#0056ff",
    contour_mid="#20d36b",
    contour_high="#ff2d1f",
)

LIGHT_TOKENS = ThemeTokens(
    bg_app="#eef4f8",
    bg_panel="#ffffff",
    bg_panel_alt="#f4f8fb",
    bg_viewport="#eaf1f8",
    bg_header="#f8fbfd",
    border="#c9d8e5",
    border_strong="#9fb7cc",
    text_primary="#102c46",
    text_secondary="#405d76",
    text_muted="#71879b",
    accent="#007f99",
    primary="#1267d8",
    primary_hover="#1d76ed",
    success="#188a45",
    warning="#b56a00",
    danger="#c93636",
    info="#1e73be",
    chart_grid="#d9e4ee",
    chart_axis="#60788f",
    mesh_line="#1f65d6",
    contour_low="#0056ff",
    contour_mid="#18a957",
    contour_high="#df2b1d",
)


def normalize_theme_mode(
    value: ThemeMode | str | None,
    *,
    default: ThemeMode | None = None,
) -> ThemeMode:
    """Normalize a persisted or user-provided theme value."""

    if value is None:
        if default is not None:
            return default
        expected = ", ".join(mode.value for mode in ThemeMode)
        raise ValueError(f"Unknown theme mode None; expected one of: {expected}.")

    if isinstance(value, ThemeMode):
        return value

    normalized = str(value).strip().lower()
    try:
        return ThemeMode(normalized)
    except ValueError as exc:
        expected = ", ".join(mode.value for mode in ThemeMode)
        raise ValueError(
            f"Unknown theme mode {value!r}; expected one of: {expected}."
        ) from exc


def get_theme_tokens(mode: ThemeMode | str) -> ThemeTokens:
    """Return tokens for a resolved theme mode.

    ``system`` is resolved by ``ThemeManager``. Direct token lookup treats it as
    dark so non-Qt callers have a stable fallback.
    """

    normalized = normalize_theme_mode(mode)
    if normalized is ThemeMode.LIGHT:
        return LIGHT_TOKENS
    return DARK_TOKENS
