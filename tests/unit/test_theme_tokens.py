from __future__ import annotations

import pytest

from osw.gui.theme import ThemeManager
from osw.gui.theme_tokens import (
    DARK_TOKENS,
    LIGHT_TOKENS,
    REQUIRED_TOKEN_NAMES,
    ThemeMode,
    get_theme_tokens,
    normalize_theme_mode,
)

EXPECTED_DARK = {
    "bg_app": "#07111f",
    "bg_panel": "#0b1d31",
    "bg_panel_alt": "#0f2942",
    "bg_viewport": "#061426",
    "bg_header": "#081827",
    "border": "#1d3c5a",
    "border_strong": "#2d5c83",
    "text_primary": "#dcecff",
    "text_secondary": "#9eb8cf",
    "text_muted": "#66839d",
    "accent": "#00d5e6",
    "primary": "#2478ff",
    "primary_hover": "#3b8aff",
    "success": "#38d46a",
    "warning": "#ffba3a",
    "danger": "#ff5b5b",
    "info": "#4aa8ff",
    "chart_grid": "#193852",
    "chart_axis": "#6f90aa",
    "mesh_line": "#2b7cff",
    "contour_low": "#0056ff",
    "contour_mid": "#20d36b",
    "contour_high": "#ff2d1f",
}

EXPECTED_LIGHT = {
    "bg_app": "#eef4f8",
    "bg_panel": "#ffffff",
    "bg_panel_alt": "#f4f8fb",
    "bg_viewport": "#eaf1f8",
    "bg_header": "#f8fbfd",
    "border": "#c9d8e5",
    "border_strong": "#9fb7cc",
    "text_primary": "#102c46",
    "text_secondary": "#405d76",
    "text_muted": "#71879b",
    "accent": "#007f99",
    "primary": "#1267d8",
    "primary_hover": "#1d76ed",
    "success": "#188a45",
    "warning": "#b56a00",
    "danger": "#c93636",
    "info": "#1e73be",
    "chart_grid": "#d9e4ee",
    "chart_axis": "#60788f",
    "mesh_line": "#1f65d6",
    "contour_low": "#0056ff",
    "contour_mid": "#18a957",
    "contour_high": "#df2b1d",
}


def test_theme_mode_persisted_values_are_stable() -> None:
    assert [mode.value for mode in ThemeMode] == ["dark", "light", "system"]


def test_dark_tokens_match_reference_values() -> None:
    assert DARK_TOKENS.as_dict() == EXPECTED_DARK


def test_light_tokens_match_reference_values() -> None:
    assert LIGHT_TOKENS.as_dict() == EXPECTED_LIGHT


@pytest.mark.parametrize("tokens", [DARK_TOKENS, LIGHT_TOKENS])
def test_required_tokens_are_present_and_non_empty(tokens: object) -> None:
    token_map = tokens.as_dict()

    assert set(token_map) == set(REQUIRED_TOKEN_NAMES)
    assert all(token_map[name] for name in REQUIRED_TOKEN_NAMES)


def test_get_theme_tokens_maps_modes_to_token_sets() -> None:
    assert get_theme_tokens(ThemeMode.DARK) is DARK_TOKENS
    assert get_theme_tokens("light") is LIGHT_TOKENS
    assert get_theme_tokens(ThemeMode.SYSTEM) is DARK_TOKENS


def test_default_theme_manager_mode_is_dark() -> None:
    manager = ThemeManager(auto_load=False)

    assert manager.current_mode is ThemeMode.DARK
    assert manager.resolved_mode is ThemeMode.DARK
    assert manager.current_tokens is DARK_TOKENS


def test_invalid_theme_mode_message_lists_valid_values() -> None:
    with pytest.raises(ValueError, match="dark, light, system"):
        normalize_theme_mode("blue")
