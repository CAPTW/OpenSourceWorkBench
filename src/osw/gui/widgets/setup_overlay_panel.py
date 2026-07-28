"""Thin Qt editor for typed structural setup records and prepare-only preview."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from PySide6 import QtCore, QtWidgets


class SetupOverlayPanel(QtWidgets.QWidget):
    createRequested = QtCore.Signal(object)
    editRequested = QtCore.Signal(str, str, object)
    deleteRequested = QtCore.Signal(str, str)
    recordSelected = QtCore.Signal(str, str, str)
    categoryVisibilityChanged = QtCore.Signal(str, bool)
    preparePreviewRequested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("oswSetupOverlayPanel")
        self._setup: object | None = None
        self._statuses: Mapping[str, object] = {}
        self._filter_selection_id = ""
        self._selected_translational_dofs = (1, 2, 3)
        self._selected_enabled = True
        self._build_ui()
        self._connect()
        self._update_form_controls()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(QtWidgets.QLabel("Solver Setup Overlays", self))

        visibility_row = QtWidgets.QHBoxLayout()
        self.visibility_checks: dict[str, QtWidgets.QCheckBox] = {}
        for category, label in (
            ("material", "Materials"),
            ("fixed_support", "Supports"),
            ("force", "Forces"),
        ):
            checkbox = QtWidgets.QCheckBox(label, self)
            checkbox.setChecked(True)
            checkbox.setObjectName(f"oswSetupVisibility_{category}")
            self.visibility_checks[category] = checkbox
            visibility_row.addWidget(checkbox)
        layout.addLayout(visibility_row)

        self.record_list = QtWidgets.QListWidget(self)
        self.record_list.setObjectName("oswSetupRecordList")
        layout.addWidget(self.record_list, 1)

        form = QtWidgets.QFormLayout()
        self.record_kind_combo = QtWidgets.QComboBox(self)
        self.record_kind_combo.addItems(("Material", "Fixed Support", "Force"))
        self.name_edit = QtWidgets.QLineEdit(self)
        self.target_combo = QtWidgets.QComboBox(self)
        self.material_combo = QtWidgets.QComboBox(self)
        self.magnitude_spin = QtWidgets.QDoubleSpinBox(self)
        self.magnitude_spin.setRange(-1.0e12, 1.0e12)
        self.magnitude_spin.setValue(1.0)
        self.force_unit_combo = QtWidgets.QComboBox(self)
        self.force_unit_combo.addItems(("N", "kN"))
        self.direction_widget = QtWidgets.QWidget(self)
        direction_layout = QtWidgets.QHBoxLayout(self.direction_widget)
        direction_layout.setContentsMargins(0, 0, 0, 0)
        self.direction_spins = tuple(
            QtWidgets.QDoubleSpinBox(self.direction_widget) for _ in range(3)
        )
        for index, spin in enumerate(self.direction_spins):
            spin.setRange(-1.0e6, 1.0e6)
            spin.setValue(1.0 if index == 0 else 0.0)
            direction_layout.addWidget(spin)
        form.addRow("Kind", self.record_kind_combo)
        form.addRow("Name", self.name_edit)
        form.addRow("Target", self.target_combo)
        form.addRow("Material", self.material_combo)
        form.addRow("Magnitude", self.magnitude_spin)
        form.addRow("Force unit", self.force_unit_combo)
        form.addRow("Direction", self.direction_widget)
        self.coordinate_system_label = QtWidgets.QLabel("GLOBAL", self)
        self.application_mode_label = QtWidgets.QLabel("PER_NODE", self)
        form.addRow("Coordinate system", self.coordinate_system_label)
        form.addRow("Force application", self.application_mode_label)
        layout.addLayout(form)
        self.kind_controls_diagnostic = QtWidgets.QLabel(self)
        self.kind_controls_diagnostic.setWordWrap(True)
        layout.addWidget(self.kind_controls_diagnostic)

        button_row = QtWidgets.QHBoxLayout()
        self.create_button = QtWidgets.QPushButton("Create", self)
        self.edit_button = QtWidgets.QPushButton("Update", self)
        self.delete_button = QtWidgets.QPushButton("Delete", self)
        button_row.addWidget(self.create_button)
        button_row.addWidget(self.edit_button)
        button_row.addWidget(self.delete_button)
        layout.addLayout(button_row)

        self.prepare_preview_button = QtWidgets.QPushButton(
            "Prepare CalculiX Preview",
            self,
        )
        self.prepare_preview_button.setObjectName("oswPrepareCalculixSetupPreview")
        layout.addWidget(self.prepare_preview_button)
        self.preview_text = QtWidgets.QPlainTextEdit(self)
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumBlockCount(1000)
        layout.addWidget(self.preview_text)

        self.deferred_scope_label = QtWidgets.QLabel(
            "Deferred: pressure, thermal loads, face/edge targeting, and solver execution.",
            self,
        )
        self.deferred_scope_label.setWordWrap(True)
        layout.addWidget(self.deferred_scope_label)

    def _connect(self) -> None:
        self.create_button.clicked.connect(
            lambda: self.createRequested.emit(self._form_payload())
        )
        self.edit_button.clicked.connect(self._emit_edit)
        self.delete_button.clicked.connect(self._emit_delete)
        self.record_list.currentItemChanged.connect(self._record_changed)
        self.record_kind_combo.currentTextChanged.connect(
            self._update_form_controls
        )
        self.prepare_preview_button.clicked.connect(
            self.preparePreviewRequested.emit
        )
        for category, checkbox in self.visibility_checks.items():
            checkbox.toggled.connect(
                lambda visible, name=category: self.categoryVisibilityChanged.emit(
                    name,
                    visible,
                )
            )

    def set_context(
        self,
        *,
        setup: object,
        selections: Sequence[object],
        materials: Sequence[object],
        statuses: Mapping[str, object],
    ) -> None:
        self._setup = setup
        self._statuses = statuses
        self.target_combo.clear()
        for selection in selections:
            self.target_combo.addItem(
                str(getattr(selection, "name", "") or getattr(selection, "id", "")),
                str(getattr(selection, "id", "")),
            )
        self.material_combo.clear()
        for material in materials:
            self.material_combo.addItem(
                str(getattr(material, "name", "")),
                str(getattr(material, "material_id", "")),
            )
        self._refresh_records()

    def set_selection_filter(self, selection_id: str) -> None:
        self._filter_selection_id = str(selection_id or "")
        self._refresh_records()

    def set_preview(self, text: str) -> None:
        self.preview_text.setPlainText(str(text or ""))

    def _records(self) -> tuple[tuple[str, object], ...]:
        if self._setup is None:
            return ()
        rows: list[tuple[str, object]] = []
        for kind, field in (
            ("material", "material_assignment_records"),
            ("fixed_support", "fixed_support_records"),
            ("force", "force_load_records"),
        ):
            rows.extend(
                (kind, record)
                for record in getattr(self._setup, field, ()) or ()
            )
        return tuple(rows)

    def _refresh_records(self) -> None:
        self.record_list.clear()
        for kind, record in self._records():
            if (
                self._filter_selection_id
                and record.target_selection_id != self._filter_selection_id
            ):
                continue
            status = self._statuses.get(record.id)
            reason = str(getattr(status, "reason_code", "NOT_EVALUATED"))
            item = QtWidgets.QListWidgetItem(f"{record.name} — {reason}")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, (kind, record.id))
            item.setData(
                QtCore.Qt.ItemDataRole.UserRole + 1,
                record.target_selection_id,
            )
            item.setToolTip(
                str(getattr(status, "message", "Setup record not evaluated."))
            )
            self.record_list.addItem(item)

    def _form_payload(self) -> dict[str, object]:
        kind = self.record_kind_combo.currentText()
        return {
            "kind": kind,
            "name": self.name_edit.text().strip(),
            "target_selection_id": str(self.target_combo.currentData() or ""),
            "material_id": str(self.material_combo.currentData() or ""),
            "translational_dofs": self._selected_translational_dofs,
            "magnitude": self.magnitude_spin.value(),
            "unit": self.force_unit_combo.currentText(),
            "direction": tuple(spin.value() for spin in self.direction_spins),
            "coordinate_system": "GLOBAL",
            "application_mode": "PER_NODE",
            "enabled": self._selected_enabled,
        }

    def _update_form_controls(self) -> None:
        kind = self.record_kind_combo.currentText()
        is_material = kind == "Material"
        is_force = kind == "Force"
        self.material_combo.setEnabled(is_material)
        self.magnitude_spin.setEnabled(is_force)
        self.force_unit_combo.setEnabled(is_force)
        self.direction_widget.setEnabled(is_force)
        self.material_combo.setToolTip(
            "Material selection is available only for Material records."
        )
        force_tooltip = "Force values are available only for Force records."
        self.magnitude_spin.setToolTip(force_tooltip)
        self.force_unit_combo.setToolTip(force_tooltip)
        self.direction_widget.setToolTip(force_tooltip)
        if is_material:
            diagnostic = (
                "Material record: force values are not applicable. "
                "GLOBAL and PER_NODE describe Force records only."
            )
        elif is_force:
            diagnostic = (
                "Force record: material selection is not applicable. "
                "Coordinate system is GLOBAL; application is PER_NODE."
            )
        else:
            diagnostic = (
                "Fixed Support record: material and force values are not "
                "applicable."
            )
        self.kind_controls_diagnostic.setText(diagnostic)

    @staticmethod
    def _select_combo_data(combo: QtWidgets.QComboBox, value: str) -> None:
        index = combo.findData(str(value))
        combo.setCurrentIndex(index)

    def _record(self, kind: str, record_id: str) -> object | None:
        for candidate_kind, record in self._records():
            if candidate_kind == kind and str(getattr(record, "id", "")) == record_id:
                return record
        return None

    def _populate_record(self, kind: str, record: object) -> None:
        labels = {
            "material": "Material",
            "fixed_support": "Fixed Support",
            "force": "Force",
        }
        self.record_kind_combo.setCurrentText(labels[kind])
        self.record_kind_combo.setEnabled(False)
        self.name_edit.setText(str(getattr(record, "name", "")))
        self._select_combo_data(
            self.target_combo,
            str(getattr(record, "target_selection_id", "")),
        )
        self._select_combo_data(
            self.material_combo,
            str(getattr(record, "material_id", "")),
        )
        self._selected_translational_dofs = tuple(
            int(item)
            for item in getattr(record, "translational_dofs", (1, 2, 3))
        )
        self._selected_enabled = bool(getattr(record, "enabled", True))
        magnitude = getattr(record, "magnitude", None)
        if magnitude is not None:
            self.magnitude_spin.setValue(float(getattr(magnitude, "value", 0.0)))
            unit_index = self.force_unit_combo.findText(
                str(getattr(magnitude, "unit", "N"))
            )
            if unit_index >= 0:
                self.force_unit_combo.setCurrentIndex(unit_index)
        direction = tuple(getattr(record, "direction", (1.0, 0.0, 0.0)))
        if len(direction) == 3:
            for spin, value in zip(self.direction_spins, direction, strict=True):
                spin.setValue(float(value))
        self.coordinate_system_label.setText(
            str(getattr(record, "coordinate_system", "GLOBAL"))
        )
        self.application_mode_label.setText(
            str(getattr(record, "application_mode", "PER_NODE"))
        )
        self._update_form_controls()

    def _record_identity(self) -> tuple[str, str]:
        item = self.record_list.currentItem()
        if item is None:
            return ("", "")
        value = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(value, tuple) or len(value) != 2:
            return ("", "")
        return (str(value[0]), str(value[1]))

    def _emit_edit(self) -> None:
        kind, record_id = self._record_identity()
        if record_id:
            self.editRequested.emit(kind, record_id, self._form_payload())

    def _emit_delete(self) -> None:
        kind, record_id = self._record_identity()
        if record_id:
            self.deleteRequested.emit(kind, record_id)

    def _record_changed(
        self,
        current: QtWidgets.QListWidgetItem | None,
        _previous: QtWidgets.QListWidgetItem | None,
    ) -> None:
        if current is None:
            self.record_kind_combo.setEnabled(True)
            self._selected_translational_dofs = (1, 2, 3)
            self._selected_enabled = True
            self._update_form_controls()
            return
        kind, record_id = self._record_identity()
        record = self._record(kind, record_id)
        if record is not None:
            self._populate_record(kind, record)
        target_id = str(
            current.data(QtCore.Qt.ItemDataRole.UserRole + 1) or ""
        )
        self.recordSelected.emit(kind, record_id, target_id)


__all__ = ["SetupOverlayPanel"]
