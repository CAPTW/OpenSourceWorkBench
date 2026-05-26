# OpenSolver Workbench Theme System

The OpenSolver Workbench GUI uses a real runtime theme system. Dark is the
default and the visual reference theme. Light and System modes must preserve the
same layout, spacing, widget hierarchy, mock data, and workflow state.

## Modes

Supported theme modes:

- `dark`
- `light`
- `system`

User-facing names:

- `Dark`
- `Light`
- `System`

Requirements:

- Switching must work at runtime without restarting the application.
- The selected mode must be persisted with `QSettings` or a simple settings
  file.
- System mode must persist the literal value `system`, not the resolved
  `dark` or `light` value.
- Preferences or an appearance menu must let users choose Dark, Light, or
  System.
- All custom-painted widgets must update after theme changes.

## System Theme Detection

System mode should resolve the active colors in this order:

1. Use `QGuiApplication.styleHints().colorScheme()` when available.
2. Fall back to current palette window color lightness.
3. If detection fails, fall back to Dark.

Missing system detection must not crash. The fallback result should be explicit
in tests where practical.

## Theme Tokens

Widgets must consume semantic tokens instead of embedding raw one-off colors.
No hard-coded widget colors are allowed outside token definitions except where
the implementation documents a narrow reason, such as a fixed plot series color
that is still derived from a theme-aware chart palette.

Required semantic tokens:

- `bg_app`
- `bg_panel`
- `bg_panel_alt`
- `bg_viewport`
- `bg_header`
- `border`
- `border_strong`
- `text_primary`
- `text_secondary`
- `text_muted`
- `accent`
- `primary`
- `primary_hover`
- `success`
- `warning`
- `danger`
- `info`
- `chart_grid`
- `chart_axis`
- `mesh_line`
- `contour_low`
- `contour_mid`
- `contour_high`

## Dark Tokens

Dark is the default and reference theme.

| Token | Value |
| --- | --- |
| `bg_app` | `#07111f` |
| `bg_panel` | `#0b1d31` |
| `bg_panel_alt` | `#0f2942` |
| `bg_viewport` | `#061426` |
| `bg_header` | `#081827` |
| `border` | `#1d3c5a` |
| `border_strong` | `#2d5c83` |
| `text_primary` | `#dcecff` |
| `text_secondary` | `#9eb8cf` |
| `text_muted` | `#66839d` |
| `accent` | `#00d5e6` |
| `primary` | `#2478ff` |
| `primary_hover` | `#3b8aff` |
| `success` | `#38d46a` |
| `warning` | `#ffba3a` |
| `danger` | `#ff5b5b` |
| `info` | `#4aa8ff` |
| `chart_grid` | `#193852` |
| `chart_axis` | `#6f90aa` |
| `mesh_line` | `#2b7cff` |
| `contour_low` | `#0056ff` |
| `contour_mid` | `#20d36b` |
| `contour_high` | `#ff2d1f` |

## Light Tokens

Light mode is a contrast-safe derivative of the same interface.

| Token | Value |
| --- | --- |
| `bg_app` | `#eef4f8` |
| `bg_panel` | `#ffffff` |
| `bg_panel_alt` | `#f4f8fb` |
| `bg_viewport` | `#eaf1f8` |
| `bg_header` | `#f8fbfd` |
| `border` | `#c9d8e5` |
| `border_strong` | `#9fb7cc` |
| `text_primary` | `#102c46` |
| `text_secondary` | `#405d76` |
| `text_muted` | `#71879b` |
| `accent` | `#007f99` |
| `primary` | `#1267d8` |
| `primary_hover` | `#1d76ed` |
| `success` | `#188a45` |
| `warning` | `#b56a00` |
| `danger` | `#c93636` |
| `info` | `#1e73be` |
| `chart_grid` | `#d9e4ee` |
| `chart_axis` | `#60788f` |
| `mesh_line` | `#1f65d6` |
| `contour_low` | `#0056ff` |
| `contour_mid` | `#18a957` |
| `contour_high` | `#df2b1d` |

## Widgets That Must Update

Theme changes must update:

- Application background
- Header and toolbar
- Workflow stepper
- Left project tree
- Central viewport mock
- Viewport toolbar
- Legends, orientation cube, axes, and scale bar
- Run monitor panels
- Residuals chart
- Warnings and progress panel
- Octave / MATLAB plot panel
- Right inspector tabs, sections, tables, and report preview
- Status bar
- Scrollbars if styled
- Icons where practical

## Suggested Modules

Preferred files:

```text
src/osw/gui/theme.py
src/osw/gui/theme_tokens.py
src/osw/gui/styles.py
src/osw/gui/styles/base.qss
src/osw/gui/styles/dark.qss
src/osw/gui/styles/light.qss
src/osw/gui/dialogs/preferences_dialog.py
```

Tests:

```text
tests/unit/test_theme_tokens.py
tests/gui/test_theme_manager.py
```

## Theme Manager Contract

Expected API:

```text
ThemeMode enum: dark, light, system
ThemeTokens dataclass or equivalent
ThemeManager.current_mode
ThemeManager.resolved_theme
ThemeManager.set_mode()
ThemeManager.apply_to_app()
ThemeManager.load_settings()
ThemeManager.save_settings()
ThemeManager.detect_system_theme()
```

Expected behavior:

- Load persisted mode at startup.
- Default to Dark when no persisted setting exists.
- Emit a signal or callback when the effective theme changes.
- Apply a palette and/or generated QSS from tokens.
- Keep custom-painted widgets synchronized through the theme-change signal.
- Never import heavy optional visualization dependencies just to resolve a
  theme.

## UI-001 Implementation Notes

The runtime theme system is implemented in:

```text
src/osw/gui/theme_tokens.py
src/osw/gui/theme.py
src/osw/gui/widgets/theme_selector.py
src/osw/gui/dialogs/preferences_dialog.py
```

Implementation behavior:

- `ThemeMode` persists the exact values `dark`, `light`, and `system`.
- `ThemeTokens` is a frozen dataclass with the required semantic token fields.
- `DARK_TOKENS` and `LIGHT_TOKENS` match the reference values above.
- `ThemeManager` defaults to Dark, loads/saves the selected mode, generates QSS,
  applies a Qt palette when a `QApplication` is available, and notifies custom
  painted widgets through `subscribe(callback)`.
- `ThemeManager` uses `QSettings` with organization `OpenSolver` and
  application `OpenSolver Workbench` when PySide6 is available. Without PySide6,
  importing `osw`, `osw.gui.theme_tokens`, and `osw.gui.theme` remains safe.
- System mode stores `system`; only `resolved_mode` and `current_tokens` map it
  to Dark or Light at runtime.
- `ThemeSelector` and `PreferencesDialog` are optional PySide6 GUI modules for
  future embedding in the toolbar or shell.

Generated QSS currently covers:

- `QMainWindow`
- `QWidget`
- `QFrame`
- `QLabel`
- `QPushButton`
- `QToolButton`
- `QLineEdit`
- `QComboBox`
- `QTreeWidget` / `QTreeView`
- `QTableWidget` / `QTableView`
- `QTabWidget` / `QTabBar`
- `QGroupBox`
- `QSplitter`
- `QProgressBar`
- `QScrollBar`
- `QMenuBar`
- `QMenu`
- `QStatusBar`

The first implementation does not create a `QApplication` at import time and
does not implement the main shell, viewport, project tree, run monitor, or
solver execution behavior.

## Visual Consistency Rules

- Dark, Light, and System must use the same region proportions and widget names.
- Theme switching must not reset the active project, active Run step, mock
  chart data, selected tree item, or visible report preview.
- The central mock viewport should use the same heat sink geometry in every
  mode and only change theme-dependent background, mesh, axis, text, and panel
  colors.
- Chart grid, axes, and labels must remain readable in both Dark and Light.
- The stored System mode must remain `system` even when the OS resolves it to
  Dark or Light at runtime.
