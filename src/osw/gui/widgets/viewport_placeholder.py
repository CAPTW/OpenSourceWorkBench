"""Central host panel for the interactive-or-fallback 3D workspace."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens
from osw.gui.widgets.mock_simulation_viewport import MockSimulationViewport
from osw.gui.widgets.viewport_toolbar import ViewportToolbar
from osw.gui.workspace_scene_view_model import (
    mesh_input_ref,
    scene_view_state_from_toggles,
)

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QFrame if QtWidgets is not None else object


class CentralViewportPanel(_BaseWidget):
    """Host one controller-owned renderer widget or an explicit fallback."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        scene_controller: object | None = None,
    ) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswCentralViewportPanel")
        self.setMinimumSize(560, 360)
        self._scene_controller: object | None = None
        self.hosted_widget: object | None = None
        self.interactive_available = False

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.toolbar = ViewportToolbar(self)

        self.scene_stack = QtWidgets.QStackedWidget(self)
        self.scene_stack.setObjectName("oswViewportSceneStack")

        fallback = QtWidgets.QWidget(self.scene_stack)
        fallback.setObjectName("oswViewportFallbackSurface")
        fallback_layout = QtWidgets.QVBoxLayout(fallback)
        fallback_layout.setContentsMargins(0, 0, 0, 0)
        fallback_layout.setSpacing(0)
        self.diagnostic_label = QtWidgets.QLabel("", fallback)
        self.diagnostic_label.setObjectName("oswViewportDiagnostic")
        self.diagnostic_label.setWordWrap(True)
        self.viewport = MockSimulationViewport(self)
        fallback_layout.addWidget(self.diagnostic_label, 0)
        fallback_layout.addWidget(self.viewport, 1)

        self.renderer_host = QtWidgets.QFrame(self.scene_stack)
        self.renderer_host.setObjectName("oswViewportRendererHost")
        self._renderer_layout = QtWidgets.QVBoxLayout(self.renderer_host)
        self._renderer_layout.setContentsMargins(0, 0, 0, 0)
        self._renderer_layout.setSpacing(0)

        self.scene_stack.addWidget(fallback)
        self.scene_stack.addWidget(self.renderer_host)
        layout.addWidget(self.toolbar, 0)
        layout.addWidget(self.scene_stack, 1)
        self._connect_toolbar()
        self.set_scene_controller(scene_controller)
        self.set_theme_tokens(DARK_TOKENS)

    def set_scene_controller(self, controller: object | None) -> None:
        """Bind a document controller and host its session-owned Qt widget."""

        self._remove_hosted_widget()
        self._scene_controller = controller
        if controller is None:
            self._show_fallback("No active 3D scene controller is attached.")
            return
        attach_host = getattr(controller, "attach_host", None)
        widget = attach_host(self.renderer_host) if callable(attach_host) else None
        capabilities = frozenset(getattr(controller, "capabilities", frozenset()))
        if (
            widget is not None
            and isinstance(widget, QtWidgets.QWidget)
            and "interactive" in capabilities
            and "hosted-widget" in capabilities
        ):
            widget.setParent(self.renderer_host)
            self._renderer_layout.addWidget(widget)
            self.hosted_widget = widget
            self.interactive_available = True
            self.diagnostic_label.hide()
            self.scene_stack.setCurrentWidget(self.renderer_host)
            self.toolbar.set_interactive_enabled(True)
            self._sync_toolbar_state()
            return
        reason = str(getattr(controller, "fallback_reason", "") or "")
        if not reason:
            backend = str(getattr(controller, "backend_kind", "unknown"))
            reason = f"Scene backend '{backend}' does not provide an embedded interactive widget."
        self._show_fallback(reason)

    def set_mesh(self, mesh: object, *, mesh_ref: str = "") -> object | None:
        """Load an existing in-memory mesh into the one active scene."""

        controller = self._scene_controller
        load_mesh = getattr(controller, "load_mesh", None)
        if not callable(load_mesh):
            self._show_fallback("No active 3D scene controller is attached.")
            return None
        representation = str(self.toolbar.representation_selector.currentData())
        show_surface = representation != "wireframe"
        show_edges = representation != "surface"
        result = load_mesh(
            mesh,
            mesh_input_ref(mesh_ref),
            scene_view_state_from_toggles(
                show_surface=show_surface,
                show_edges=show_edges,
                show_axes=self.toolbar.axes_button.isChecked(),
            ),
        )
        fallback_reason = str(getattr(controller, "fallback_reason", "") or "")
        if fallback_reason:
            self._show_fallback(fallback_reason)
        else:
            self._sync_toolbar_state()
        return result

    def _connect_toolbar(self) -> None:
        self.toolbar.commandRequested.connect(self._on_command_requested)
        self.toolbar.cameraPresetRequested.connect(
            lambda preset: self._invoke("set_camera_preset", preset)
        )
        self.toolbar.representationRequested.connect(
            lambda mode: self._invoke("set_representation", mode)
        )
        self.toolbar.axesToggled.connect(lambda visible: self._invoke("set_axes_visible", visible))
        self.toolbar.actorVisibilityRequested.connect(
            lambda semantic_id, visible: self._invoke(
                "set_actor_visible",
                semantic_id,
                visible,
            )
        )
        self.toolbar.actorIsolationRequested.connect(
            lambda semantic_id: self._invoke("isolate_actor", semantic_id)
        )
        self.toolbar.clearIsolationRequested.connect(lambda: self._invoke("clear_isolation"))
        self.toolbar.showAllActorsRequested.connect(lambda: self._invoke("show_all_actors"))
        self.toolbar.clippingToggled.connect(self._on_clipping_toggled)
        self.toolbar.clippingUpdated.connect(self._on_clipping_updated)

    def _on_command_requested(self, command: str) -> None:
        if command == "fit":
            self._invoke("fit_to_scene")
        elif command in {"orbit", "pan", "zoom"}:
            self._invoke("set_interaction_mode", command)

    def _on_clipping_toggled(self, enabled: bool) -> None:
        if enabled:
            self._invoke(
                "enable_clipping",
                self.toolbar.selected_clip_axis(),
                float(self.toolbar.clip_origin_input.value()),
            )
        else:
            self._invoke("clear_clipping")

    def _on_clipping_updated(self, axis: str, origin: float) -> None:
        if self.toolbar.tool_buttons["Section"].isChecked():
            self._invoke("update_clipping", axis, origin)

    def _invoke(self, method_name: str, *args: object) -> bool:
        controller = self._scene_controller
        method = getattr(controller, method_name, None)
        succeeded = bool(method(*args)) if callable(method) else False
        if succeeded:
            self._sync_toolbar_state()
        if not succeeded:
            reason = str(getattr(controller, "fallback_reason", "") or "")
            if reason:
                self._show_fallback(reason)
        return succeeded

    def _sync_toolbar_state(self) -> None:
        controller = self._scene_controller
        records = getattr(controller, "actor_records", {})
        self.toolbar.sync_actor_records(
            records,
            isolation_active=bool(getattr(controller, "isolation_active", False)),
            representation=str(getattr(controller, "representation", "surface")),
            axes_visible=bool(getattr(controller, "axes_visible", True)),
        )

    def _show_fallback(self, reason: str) -> None:
        self.interactive_available = False
        self.hosted_widget = None
        self.diagnostic_label.setText(
            "Interactive 3D unavailable: "
            f"{reason} The non-interactive workspace preview remains available."
        )
        self.diagnostic_label.show()
        self.scene_stack.setCurrentIndex(0)
        self.toolbar.set_interactive_enabled(False)

    def _remove_hosted_widget(self) -> None:
        widget = self.hosted_widget
        self.hosted_widget = None
        if widget is None:
            return
        try:
            self._renderer_layout.removeWidget(widget)
            widget.setParent(None)
        except RuntimeError:
            return

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self.setStyleSheet(
            "QFrame#oswCentralViewportPanel {"
            f"background-color: {tokens.bg_viewport};"
            f"border: 1px solid {tokens.border};"
            "}"
            "QLabel#oswViewportDiagnostic {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_secondary};"
            f"border-bottom: 1px solid {tokens.border};"
            "padding: 8px;"
            "}"
        )
        self.toolbar.set_theme_tokens(tokens)
        self.viewport.set_theme_tokens(tokens)


ViewportPlaceholder = CentralViewportPanel
