"""Bounded Qt surface for node/cell picking and NamedSelection lifecycle."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from PySide6 import QtCore, QtGui, QtWidgets


class NamedSelectionPanel(QtWidgets.QWidget):
    """Present selection controls while keeping identity logic in pure owners."""

    pickModeChanged = QtCore.Signal(str)
    selectionOperationChanged = QtCore.Signal(str)
    clearRequested = QtCore.Signal()
    invertRequested = QtCore.Signal()
    createRequested = QtCore.Signal(str, str)
    renameRequested = QtCore.Signal(str, str)
    replaceRequested = QtCore.Signal(str)
    deleteRequested = QtCore.Signal(str)
    selectionActivated = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("oswNamedSelectionPanel")
        self._backend_available = True
        self._current_count = 0
        self._current_resolution = "UNRESOLVED"
        self._build_ui()
        self._connect_signals()
        self.set_current_selection(
            count=0,
            resolution_state="UNRESOLVED",
            status="No current entities are selected.",
        )

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(7)

        title = QtWidgets.QLabel("Named Selections", self)
        title.setObjectName("oswNamedSelectionTitle")
        title.setStyleSheet("font-weight: 600;")
        layout.addWidget(title)

        mode_row = QtWidgets.QHBoxLayout()
        mode_label = QtWidgets.QLabel("Pick mode", self)
        self.mode_selector = QtWidgets.QComboBox(self)
        self.mode_selector.setObjectName("oswEntityPickMode")
        self.mode_selector.addItems(("Node", "Cell"))
        mode_row.addWidget(mode_label)
        mode_row.addWidget(self.mode_selector, 1)
        layout.addLayout(mode_row)

        operation_row = QtWidgets.QHBoxLayout()
        operation_label = QtWidgets.QLabel("Operation", self)
        self.operation_selector = QtWidgets.QComboBox(self)
        self.operation_selector.setObjectName("oswEntitySelectionOperation")
        self.operation_selector.addItems(("Replace", "Add", "Toggle", "Subtract"))
        operation_row.addWidget(operation_label)
        operation_row.addWidget(self.operation_selector, 1)
        layout.addLayout(operation_row)

        deferred_row = QtWidgets.QHBoxLayout()
        deferred_reason = (
            "Face and edge entity identity is not supported in this gate."
        )
        self.face_mode_button = QtWidgets.QPushButton("Face (deferred)", self)
        self.edge_mode_button = QtWidgets.QPushButton("Edge (deferred)", self)
        for button in (self.face_mode_button, self.edge_mode_button):
            button.setEnabled(False)
            button.setToolTip(deferred_reason)
            deferred_row.addWidget(button)
        layout.addLayout(deferred_row)

        self.hover_semantics_label = QtWidgets.QLabel(
            "Hover: amber · Current: cyan · Named: purple",
            self,
        )
        self.hover_semantics_label.setWordWrap(True)
        layout.addWidget(self.hover_semantics_label)

        current_row = QtWidgets.QHBoxLayout()
        self.selected_count_label = QtWidgets.QLabel("Selected: 0", self)
        self.invert_button = QtWidgets.QPushButton("Invert", self)
        self.invert_button.setToolTip(
            "Select the complement in the active node/cell domain."
        )
        self.clear_button = QtWidgets.QPushButton("Clear Selection", self)
        self.clear_button.setShortcut(QtGui.QKeySequence("Esc"))
        self.clear_button.setToolTip("Clear transient current selection (Esc).")
        current_row.addWidget(self.selected_count_label)
        current_row.addStretch(1)
        current_row.addWidget(self.invert_button)
        current_row.addWidget(self.clear_button)
        layout.addLayout(current_row)

        self.current_resolution_label = QtWidgets.QLabel(
            "Current: UNRESOLVED",
            self,
        )
        layout.addWidget(self.current_resolution_label)

        self.metadata_label = QtWidgets.QLabel("Entity metadata: none", self)
        self.metadata_label.setObjectName("oswCurrentSelectionMetadata")
        self.metadata_label.setAccessibleName("Current selection entity metadata")
        self.metadata_label.setWordWrap(True)
        layout.addWidget(self.metadata_label)

        self.selection_list = QtWidgets.QListWidget(self)
        self.selection_list.setObjectName("oswNamedSelectionList")
        self.selection_list.setAccessibleName("Named selections")
        layout.addWidget(self.selection_list, 1)

        form = QtWidgets.QFormLayout()
        self.name_input = QtWidgets.QLineEdit(self)
        self.name_input.setObjectName("oswNamedSelectionName")
        self.description_input = QtWidgets.QLineEdit(self)
        self.description_input.setObjectName("oswNamedSelectionDescription")
        form.addRow("Name", self.name_input)
        form.addRow("Description", self.description_input)
        layout.addLayout(form)

        create_row = QtWidgets.QHBoxLayout()
        self.create_button = QtWidgets.QPushButton("Create", self)
        self.rename_button = QtWidgets.QPushButton("Rename", self)
        create_row.addWidget(self.create_button)
        create_row.addWidget(self.rename_button)
        layout.addLayout(create_row)

        target_row = QtWidgets.QHBoxLayout()
        self.replace_button = QtWidgets.QPushButton("Replace Targets", self)
        self.delete_button = QtWidgets.QPushButton("Delete", self)
        target_row.addWidget(self.replace_button)
        target_row.addWidget(self.delete_button)
        layout.addLayout(target_row)

        self.status_label = QtWidgets.QLabel("", self)
        self.status_label.setObjectName("oswNamedSelectionStatus")
        self.status_label.setWordWrap(True)
        self.status_label.setAccessibleName("Named selection status")
        layout.addWidget(self.status_label)

    def _connect_signals(self) -> None:
        self.mode_selector.currentTextChanged.connect(
            lambda text: self.pickModeChanged.emit(text.lower())
        )
        self.operation_selector.currentTextChanged.connect(
            lambda text: self.selectionOperationChanged.emit(text.lower())
        )
        self.clear_button.clicked.connect(self.clearRequested.emit)
        self.invert_button.clicked.connect(self.invertRequested.emit)
        self.create_button.clicked.connect(
            lambda: self.createRequested.emit(
                self.name_input.text().strip(),
                self.description_input.text().strip(),
            )
        )
        self.rename_button.clicked.connect(self._emit_rename)
        self.replace_button.clicked.connect(self._emit_replace)
        self.delete_button.clicked.connect(self._emit_delete)
        self.selection_list.currentItemChanged.connect(
            self._on_current_item_changed
        )

    def set_backend_available(self, available: bool, reason: str = "") -> None:
        self._backend_available = bool(available)
        self.mode_selector.setEnabled(available)
        self.operation_selector.setEnabled(available)
        self.clear_button.setEnabled(available)
        self.invert_button.setEnabled(available)
        if not available:
            self.set_status(
                reason or "Interactive picking is unavailable.",
                error=True,
            )
        self._refresh_button_state()

    def set_current_selection(
        self,
        *,
        count: int,
        resolution_state: str,
        status: str,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        self._current_count = max(0, int(count))
        self._current_resolution = str(resolution_state or "UNRESOLVED")
        self.selected_count_label.setText(f"Selected: {self._current_count}")
        self.current_resolution_label.setText(
            f"Current: {self._current_resolution}"
        )
        summary, details = _selection_metadata_text(metadata)
        self.metadata_label.setText(summary)
        self.metadata_label.setToolTip(details)
        self.set_status(status, error=self._current_resolution in {"STALE", "INVALID"})
        self._refresh_button_state()

    def set_named_selections(
        self,
        selections: Sequence[object],
        resolutions: Mapping[str, object],
    ) -> None:
        selected_id = self.current_selection_id()
        self.selection_list.blockSignals(True)
        self.selection_list.clear()
        selected_row = -1
        for row, selection in enumerate(selections):
            selection_id = str(getattr(selection, "id", ""))
            name = str(getattr(selection, "name", "") or selection_id)
            resolution = resolutions.get(selection_id)
            state = str(getattr(resolution, "state", "UNRESOLVED"))
            if "." in state:
                state = state.rsplit(".", 1)[-1]
            item = QtWidgets.QListWidgetItem(f"{name} — {state}")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, selection_id)
            item.setData(
                QtCore.Qt.ItemDataRole.UserRole + 1,
                str(getattr(selection, "description", "")),
            )
            item.setToolTip(
                str(
                    getattr(
                        resolution,
                        "message",
                        "Selection resolution has not been evaluated.",
                    )
                )
            )
            self.selection_list.addItem(item)
            if selection_id == selected_id:
                selected_row = row
        if selected_row >= 0:
            self.selection_list.setCurrentRow(selected_row)
        self.selection_list.blockSignals(False)
        self._refresh_button_state()

    def current_selection_id(self) -> str:
        item = self.selection_list.currentItem()
        if item is None:
            return ""
        return str(item.data(QtCore.Qt.ItemDataRole.UserRole) or "")

    def set_status(self, message: str, *, error: bool = False) -> None:
        self.status_label.setText(str(message or ""))
        self.status_label.setProperty("error", bool(error))
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def select_named_selection(self, selection_id: str, *, emit: bool = True) -> bool:
        for row in range(self.selection_list.count()):
            item = self.selection_list.item(row)
            if str(item.data(QtCore.Qt.ItemDataRole.UserRole) or "") == selection_id:
                blocked = self.selection_list.blockSignals(not emit)
                try:
                    self.selection_list.setCurrentRow(row)
                finally:
                    self.selection_list.blockSignals(blocked)
                self._refresh_button_state()
                return True
        return False

    def clear_named_selection(self, *, emit: bool = True) -> None:
        blocked = self.selection_list.blockSignals(not emit)
        try:
            self.selection_list.setCurrentRow(-1)
        finally:
            self.selection_list.blockSignals(blocked)
        self._refresh_button_state()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.clearRequested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def _on_current_item_changed(
        self,
        current: QtWidgets.QListWidgetItem | None,
        _previous: QtWidgets.QListWidgetItem | None,
    ) -> None:
        if current is None:
            self._refresh_button_state()
            return
        selection_id = str(
            current.data(QtCore.Qt.ItemDataRole.UserRole) or ""
        )
        display = current.text().split(" — ", 1)[0]
        self.name_input.setText(display)
        self.description_input.setText(
            str(
                current.data(QtCore.Qt.ItemDataRole.UserRole + 1) or ""
            )
        )
        self.selectionActivated.emit(selection_id)
        self._refresh_button_state()

    def _emit_rename(self) -> None:
        selection_id = self.current_selection_id()
        if selection_id:
            self.renameRequested.emit(
                selection_id,
                self.name_input.text().strip(),
            )

    def _emit_replace(self) -> None:
        selection_id = self.current_selection_id()
        if selection_id:
            self.replaceRequested.emit(selection_id)

    def _emit_delete(self) -> None:
        selection_id = self.current_selection_id()
        if selection_id:
            self.deleteRequested.emit(selection_id)

    def _refresh_button_state(self) -> None:
        has_named_selection = bool(self.current_selection_id())
        current_is_usable = (
            self._backend_available
            and self._current_count > 0
            and self._current_resolution == "RESOLVED"
        )
        self.create_button.setEnabled(current_is_usable)
        self.rename_button.setEnabled(has_named_selection)
        self.replace_button.setEnabled(has_named_selection and current_is_usable)
        self.delete_button.setEnabled(has_named_selection)


def _selection_metadata_text(
    metadata: Mapping[str, object] | None,
) -> tuple[str, str]:
    if not metadata:
        return "Entity metadata: none", "No canonical entity is selected."
    kind = str(metadata.get("entity_kind", "") or "unknown")
    raw_ids = tuple(metadata.get("entity_ids", ()) or ())
    preview = ", ".join(str(item) for item in raw_ids[:8])
    if len(raw_ids) > 8:
        preview = f"{preview}, … (+{len(raw_ids) - 8})"
    summary = f"{kind} IDs: {preview or 'none'}"
    mesh_ref = str(metadata.get("mesh_ref", "") or "")
    fingerprint = str(metadata.get("mesh_fingerprint", "") or "")
    namespace = str(metadata.get("id_namespace", "") or "")
    details = (
        f"Kind: {kind}\n"
        f"Canonical IDs: {', '.join(str(item) for item in raw_ids) or 'none'}\n"
        f"Mesh ref: {mesh_ref or 'none'}\n"
        f"Mesh fingerprint: {fingerprint or 'none'}\n"
        f"ID namespace: {namespace or 'none'}"
    )
    return summary, details


__all__ = ["NamedSelectionPanel"]
