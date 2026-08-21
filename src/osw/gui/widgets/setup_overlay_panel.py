"""Qt editor for persistent NamedSelection-bound solver setup records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from PySide6 import QtCore, QtWidgets

SETUP_KIND_OPTIONS = (
    ("material_region", "Material Region"),
    ("fixed_support", "Fixed Support"),
    ("prescribed_displacement", "Prescribed Displacement"),
    ("force", "Force"),
    ("pressure", "Pressure"),
    ("temperature", "Temperature"),
    ("heat_flux", "Heat Flux"),
)

CATEGORY_LABELS = (
    ("material", "Materials"),
    ("fixed_support", "Supports"),
    ("prescribed_displacement", "Displacements"),
    ("force", "Forces"),
    ("pressure", "Pressure"),
    ("temperature", "Temperature"),
    ("heat_flux", "Heat Flux"),
)

CALCULIX_SUPPORTED_KINDS = frozenset(
    {"material_region", "fixed_support", "prescribed_displacement", "force"}
)


class SetupOverlayPanel(QtWidgets.QWidget):
    """Edit typed setup data while native rendering remains controller-owned."""

    createRequested = QtCore.Signal(object)
    editRequested = QtCore.Signal(str, str, object)
    deleteRequested = QtCore.Signal(str, str)
    recordSelected = QtCore.Signal(str, str, str)
    categoryVisibilityChanged = QtCore.Signal(str, bool)
    recordVisibilityChanged = QtCore.Signal(str, bool)
    preparePreviewRequested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("oswSetupOverlayPanel")
        self._setup: object | None = None
        self._statuses: Mapping[str, object] = {}
        self._selection_kinds: dict[str, str] = {}
        self._resolved_selection_ids: frozenset[str] | None = None
        self._explicit_surface_selection_ids: frozenset[str] | None = None
        self._project_units: object | None = None
        self._filter_selection_id = ""
        self._record_visibility: dict[str, bool] = {}
        self._selected_translational_dofs = (1, 2, 3)
        self._selected_enabled = True
        self._build_ui()
        self._connect()
        self._update_form_controls()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(QtWidgets.QLabel("Solver Setup Overlays", self))

        visibility_grid = QtWidgets.QGridLayout()
        self.visibility_checks: dict[str, QtWidgets.QCheckBox] = {}
        for index, (category, label) in enumerate(CATEGORY_LABELS):
            checkbox = QtWidgets.QCheckBox(label, self)
            checkbox.setChecked(True)
            checkbox.setObjectName(f"oswSetupVisibility_{category}")
            checkbox.setAccessibleName(f"Show {label} setup overlays")
            self.visibility_checks[category] = checkbox
            visibility_grid.addWidget(checkbox, index // 3, index % 3)
        layout.addLayout(visibility_grid)

        self.record_list = QtWidgets.QListWidget(self)
        self.record_list.setObjectName("oswSetupRecordList")
        self.record_list.setAccessibleName("Solver setup records")
        layout.addWidget(self.record_list, 1)

        form = QtWidgets.QFormLayout()
        self.record_kind_combo = QtWidgets.QComboBox(self)
        self.record_kind_combo.setObjectName("oswSetupKind")
        for key, label in SETUP_KIND_OPTIONS:
            self.record_kind_combo.addItem(label, key)
        self.record_kind_combo.setAccessibleName("Setup kind")
        self.name_edit = QtWidgets.QLineEdit(self)
        self.name_edit.setObjectName("oswSetupName")
        self.name_edit.setAccessibleName("Setup name")
        self.target_combo = QtWidgets.QComboBox(self)
        self.target_combo.setObjectName("oswSetupNamedSelection")
        self.target_combo.setAccessibleName("Target NamedSelection")
        self.material_combo = QtWidgets.QComboBox(self)
        self.material_combo.setObjectName("oswSetupMaterial")
        self.material_combo.setAccessibleName("Assigned material")
        self.enabled_checkbox = QtWidgets.QCheckBox("Enabled", self)
        self.enabled_checkbox.setObjectName("oswSetupEnabled")
        self.enabled_checkbox.setChecked(True)
        self.enabled_checkbox.setAccessibleName("Setup enabled state")
        form.addRow("Kind", self.record_kind_combo)
        form.addRow("Name", self.name_edit)
        form.addRow("Target", self.target_combo)
        form.addRow("Material", self.material_combo)
        form.addRow("State", self.enabled_checkbox)

        self.support_dof_widget = QtWidgets.QWidget(self)
        support_layout = QtWidgets.QHBoxLayout(self.support_dof_widget)
        support_layout.setContentsMargins(0, 0, 0, 0)
        self.support_dof_checks = tuple(
            QtWidgets.QCheckBox(axis, self.support_dof_widget) for axis in ("UX", "UY", "UZ")
        )
        for checkbox in self.support_dof_checks:
            checkbox.setChecked(True)
            checkbox.setAccessibleName(f"Fixed support {checkbox.text()}")
            support_layout.addWidget(checkbox)
        form.addRow("Fixed DOFs", self.support_dof_widget)

        self.displacement_widget = QtWidgets.QWidget(self)
        displacement_layout = QtWidgets.QGridLayout(self.displacement_widget)
        displacement_layout.setContentsMargins(0, 0, 0, 0)
        self.displacement_enabled_checks = tuple(
            QtWidgets.QCheckBox(axis, self.displacement_widget) for axis in ("UX", "UY", "UZ")
        )
        self.displacement_spins = tuple(
            QtWidgets.QDoubleSpinBox(self.displacement_widget) for _ in range(3)
        )
        for row, (checkbox, spin) in enumerate(
            zip(
                self.displacement_enabled_checks,
                self.displacement_spins,
                strict=True,
            )
        ):
            spin.setRange(-1.0e12, 1.0e12)
            spin.setDecimals(9)
            spin.setEnabled(False)
            spin.setAccessibleName(f"Prescribed displacement {checkbox.text()}")
            displacement_layout.addWidget(checkbox, row, 0)
            displacement_layout.addWidget(spin, row, 1)
        self.displacement_unit_combo = QtWidgets.QComboBox(self.displacement_widget)
        self.displacement_unit_combo.addItems(("m", "mm"))
        self.displacement_unit_combo.setAccessibleName("Displacement unit")
        displacement_layout.addWidget(self.displacement_unit_combo, 0, 2, 3, 1)
        form.addRow("Displacement", self.displacement_widget)

        self.magnitude_spin = QtWidgets.QDoubleSpinBox(self)
        self.magnitude_spin.setRange(-1.0e12, 1.0e12)
        self.magnitude_spin.setDecimals(9)
        self.magnitude_spin.setValue(1.0)
        self.magnitude_spin.setAccessibleName("Force magnitude")
        self.force_unit_combo = QtWidgets.QComboBox(self)
        self.force_unit_combo.addItems(("N", "kN"))
        self.force_unit_combo.setAccessibleName("Force unit")
        self.direction_widget = QtWidgets.QWidget(self)
        direction_layout = QtWidgets.QHBoxLayout(self.direction_widget)
        direction_layout.setContentsMargins(0, 0, 0, 0)
        self.direction_spins = tuple(
            QtWidgets.QDoubleSpinBox(self.direction_widget) for _ in range(3)
        )
        for index, spin in enumerate(self.direction_spins):
            spin.setRange(-1.0e6, 1.0e6)
            spin.setDecimals(6)
            spin.setValue(1.0 if index == 0 else 0.0)
            spin.setAccessibleName(f"Force direction {'XYZ'[index]}")
            direction_layout.addWidget(spin)
        form.addRow("Magnitude", self.magnitude_spin)
        form.addRow("Force unit", self.force_unit_combo)
        form.addRow("Direction", self.direction_widget)

        self.scalar_widget = QtWidgets.QWidget(self)
        scalar_layout = QtWidgets.QHBoxLayout(self.scalar_widget)
        scalar_layout.setContentsMargins(0, 0, 0, 0)
        self.scalar_spin = QtWidgets.QDoubleSpinBox(self.scalar_widget)
        self.scalar_spin.setRange(-1.0e15, 1.0e15)
        self.scalar_spin.setDecimals(9)
        self.scalar_unit_label = QtWidgets.QLabel("Pa", self.scalar_widget)
        self.scalar_unit_label.setAccessibleName("Setup scalar unit")
        scalar_layout.addWidget(self.scalar_spin, 1)
        scalar_layout.addWidget(self.scalar_unit_label)
        form.addRow("Scalar value", self.scalar_widget)

        self.coordinate_system_label = QtWidgets.QLabel("GLOBAL", self)
        self.application_mode_label = QtWidgets.QLabel("PER_NODE", self)
        form.addRow("Coordinate system", self.coordinate_system_label)
        form.addRow("Force application", self.application_mode_label)
        layout.addLayout(form)

        status_form = QtWidgets.QFormLayout()
        self.validity_label = QtWidgets.QLabel("NOT_EVALUATED", self)
        self.validity_label.setAccessibleName("Setup validity")
        self.validity_label.setWordWrap(True)
        self.adapter_readiness_label = QtWidgets.QLabel("NOT_EVALUATED", self)
        self.adapter_readiness_label.setAccessibleName("Adapter readiness")
        self.adapter_readiness_label.setWordWrap(True)
        self.record_visibility_checkbox = QtWidgets.QCheckBox("Show overlay", self)
        self.record_visibility_checkbox.setAccessibleName("Show selected setup overlay")
        self.record_visibility_checkbox.setChecked(True)
        self.record_visibility_checkbox.setEnabled(False)
        status_form.addRow("Validity", self.validity_label)
        status_form.addRow("Adapter", self.adapter_readiness_label)
        status_form.addRow("Visibility", self.record_visibility_checkbox)
        layout.addLayout(status_form)

        self.kind_controls_diagnostic = QtWidgets.QLabel(self)
        self.kind_controls_diagnostic.setWordWrap(True)
        self.kind_controls_diagnostic.setAccessibleName("Setup editor validation")
        layout.addWidget(self.kind_controls_diagnostic)

        button_row = QtWidgets.QHBoxLayout()
        self.new_button = QtWidgets.QPushButton("New", self)
        self.create_button = QtWidgets.QPushButton("Create", self)
        self.edit_button = QtWidgets.QPushButton("Update", self)
        self.delete_button = QtWidgets.QPushButton("Delete", self)
        for button in (
            self.new_button,
            self.create_button,
            self.edit_button,
            self.delete_button,
        ):
            button.setAccessibleName(f"{button.text()} solver setup")
            button_row.addWidget(button)
        layout.addLayout(button_row)

        self.prepare_preview_button = QtWidgets.QPushButton(
            "Prepare CalculiX Preview",
            self,
        )
        self.prepare_preview_button.setObjectName("oswPrepareCalculixSetupPreview")
        self.prepare_preview_button.setAccessibleName("Prepare CalculiX setup preview")
        layout.addWidget(self.prepare_preview_button)
        self.preview_text = QtWidgets.QPlainTextEdit(self)
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumBlockCount(1000)
        self.preview_text.setAccessibleName("Setup adapter preview and diagnostics")
        layout.addWidget(self.preview_text)

        self.deferred_scope_label = QtWidgets.QLabel(
            "Deferred: solid face identity, automatic surface reconstruction, "
            "and solver execution.",
            self,
        )
        self.deferred_scope_label.setWordWrap(True)
        layout.addWidget(self.deferred_scope_label)

    def _connect(self) -> None:
        self.new_button.clicked.connect(self._begin_create)
        self.create_button.clicked.connect(lambda: self.createRequested.emit(self._form_payload()))
        self.edit_button.clicked.connect(self._emit_edit)
        self.delete_button.clicked.connect(self._emit_delete)
        self.record_list.currentItemChanged.connect(self._record_changed)
        self.record_kind_combo.currentTextChanged.connect(self._update_form_controls)
        self.name_edit.textChanged.connect(self._update_validation_state)
        self.target_combo.currentIndexChanged.connect(self._update_validation_state)
        self.material_combo.currentIndexChanged.connect(self._update_validation_state)
        self.enabled_checkbox.toggled.connect(self._remember_enabled)
        self.prepare_preview_button.clicked.connect(self.preparePreviewRequested.emit)
        self.record_visibility_checkbox.toggled.connect(self._record_visibility_toggled)
        for checkbox in self.support_dof_checks:
            checkbox.toggled.connect(self._update_validation_state)
        for checkbox, spin in zip(
            self.displacement_enabled_checks,
            self.displacement_spins,
            strict=True,
        ):
            checkbox.toggled.connect(spin.setEnabled)
            checkbox.toggled.connect(self._update_validation_state)
        self.magnitude_spin.valueChanged.connect(self._update_validation_state)
        self.scalar_spin.valueChanged.connect(self._update_validation_state)
        for spin in self.direction_spins:
            spin.valueChanged.connect(self._update_validation_state)
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
        units: object | None = None,
        resolved_selection_ids: Iterable[str] | None = None,
        surface_selection_ids: Iterable[str] | None = None,
    ) -> None:
        self._setup = setup
        self._statuses = statuses
        self._project_units = units
        self._resolved_selection_ids = (
            None
            if resolved_selection_ids is None
            else frozenset(str(item) for item in resolved_selection_ids)
        )
        self._explicit_surface_selection_ids = (
            None
            if surface_selection_ids is None
            else frozenset(str(item) for item in surface_selection_ids)
        )
        self._sync_unit_controls()
        self._selection_kinds = {
            str(getattr(selection, "id", "")): str(
                getattr(getattr(selection, "entity_kind", ""), "value", "")
                or getattr(selection, "entity_kind", "")
                or ""
            )
            for selection in selections
        }
        self.target_combo.blockSignals(True)
        self.target_combo.clear()
        for selection in selections:
            self.target_combo.addItem(
                str(getattr(selection, "name", "") or getattr(selection, "id", "")),
                str(getattr(selection, "id", "")),
            )
        self.target_combo.blockSignals(False)
        self.material_combo.blockSignals(True)
        self.material_combo.clear()
        for material in materials:
            self.material_combo.addItem(
                str(getattr(material, "name", "")),
                str(getattr(material, "material_id", "")),
            )
        self.material_combo.blockSignals(False)
        self._refresh_records()
        self._update_validation_state()

    def set_selection_filter(self, selection_id: str) -> None:
        self._filter_selection_id = str(selection_id or "")
        self._refresh_records()

    def set_preview(self, text: str) -> None:
        self.preview_text.setPlainText(str(text or ""))

    def select_record(self, record_id: str, *, emit: bool = True) -> bool:
        for row in range(self.record_list.count()):
            item = self.record_list.item(row)
            identity = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if isinstance(identity, tuple) and len(identity) == 2 and identity[1] == record_id:
                blocked = self.record_list.blockSignals(not emit)
                try:
                    self.record_list.setCurrentRow(row)
                finally:
                    self.record_list.blockSignals(blocked)
                if not emit:
                    kind, selected_id = str(identity[0]), str(identity[1])
                    record = self._record(kind, selected_id)
                    if record is not None:
                        self._populate_record(kind, record)
                return True
        return False

    def current_record_id(self) -> str:
        return self._record_identity()[1]

    def _records(self) -> tuple[tuple[str, object], ...]:
        if self._setup is None:
            return ()
        rows: list[tuple[str, object]] = []
        for kind, field in (
            ("material_region", "material_assignment_records"),
            ("fixed_support", "fixed_support_records"),
            ("prescribed_displacement", "prescribed_displacement_records"),
            ("force", "force_load_records"),
            ("pressure", "pressure_load_records"),
            ("temperature", "temperature_records"),
            ("heat_flux", "heat_flux_records"),
        ):
            rows.extend((kind, record) for record in getattr(self._setup, field, ()) or ())
        return tuple(rows)

    def _refresh_records(self) -> None:
        selected_id = self.current_record_id()
        self.record_list.blockSignals(True)
        self.record_list.clear()
        selected_row = -1
        for kind, record in self._records():
            if (
                self._filter_selection_id
                and record.target_selection_id != self._filter_selection_id
            ):
                continue
            status = self._statuses.get(record.id)
            reason = str(getattr(status, "reason_code", "NOT_EVALUATED"))
            adapter = self._adapter_readiness(kind, status)
            enabled = "enabled" if bool(getattr(record, "enabled", True)) else "disabled"
            item = QtWidgets.QListWidgetItem(f"{record.name} — {reason} — {adapter} — {enabled}")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, (kind, record.id))
            item.setData(
                QtCore.Qt.ItemDataRole.UserRole + 1,
                record.target_selection_id,
            )
            item.setToolTip(str(getattr(status, "message", "Setup record not evaluated.")))
            self.record_list.addItem(item)
            if str(record.id) == selected_id:
                selected_row = self.record_list.count() - 1
        if selected_row >= 0:
            self.record_list.setCurrentRow(selected_row)
        self.record_list.blockSignals(False)

    def _form_payload(self) -> dict[str, object]:
        kind = str(self.record_kind_combo.currentData() or "")
        components = tuple(
            spin.value() if checkbox.isChecked() else None
            for checkbox, spin in zip(
                self.displacement_enabled_checks,
                self.displacement_spins,
                strict=True,
            )
        )
        scalar_unit = self.scalar_unit_label.text()
        return {
            "kind": self.record_kind_combo.currentText(),
            "kind_id": kind,
            "name": self.name_edit.text().strip(),
            "target_selection_id": str(self.target_combo.currentData() or ""),
            "material_id": str(self.material_combo.currentData() or ""),
            "translational_dofs": tuple(
                index
                for index, checkbox in enumerate(self.support_dof_checks, 1)
                if checkbox.isChecked()
            ),
            "ux": components[0],
            "uy": components[1],
            "uz": components[2],
            "displacement_unit": self.displacement_unit_combo.currentText(),
            "magnitude": self.magnitude_spin.value(),
            "unit": (self.force_unit_combo.currentText() if kind == "force" else scalar_unit),
            "value": self.scalar_spin.value(),
            "direction": tuple(spin.value() for spin in self.direction_spins),
            "coordinate_system": "GLOBAL",
            "application_mode": "PER_NODE",
            "enabled": self.enabled_checkbox.isChecked(),
        }

    def _update_form_controls(self, *_args: object) -> None:
        kind = str(self.record_kind_combo.currentData() or "")
        is_material = kind == "material_region"
        is_fixed = kind == "fixed_support"
        is_displacement = kind == "prescribed_displacement"
        is_force = kind == "force"
        is_scalar = kind in {"pressure", "temperature", "heat_flux"}
        self.material_combo.setEnabled(is_material)
        self.support_dof_widget.setEnabled(is_fixed)
        self.displacement_widget.setEnabled(is_displacement)
        self.magnitude_spin.setEnabled(is_force)
        self.force_unit_combo.setEnabled(is_force)
        self.direction_widget.setEnabled(is_force)
        self.scalar_widget.setEnabled(is_scalar)
        self.coordinate_system_label.setEnabled(is_force or is_displacement)
        self.application_mode_label.setEnabled(is_force)
        scalar_labels = {
            "pressure": (
                "Pressure value",
                str(getattr(self._project_units, "pressure", "Pa")),
            ),
            "temperature": (
                "Temperature value",
                str(getattr(self._project_units, "temperature", "K")),
            ),
            "heat_flux": (
                "Heat flux value",
                self._heat_flux_unit(),
            ),
        }
        if is_scalar:
            accessible_name, unit = scalar_labels[kind]
            self.scalar_spin.setAccessibleName(accessible_name)
            self.scalar_unit_label.setText(unit)
        else:
            self.scalar_spin.setAccessibleName("Setup scalar value")
        self.material_combo.setToolTip(
            "A Project material is required for Material Region records."
            if is_material
            else "Material does not apply to this setup kind."
        )
        self._update_validation_state()

    def _sync_unit_controls(self) -> None:
        length = str(getattr(self._project_units, "length", "m"))
        force = str(getattr(self._project_units, "force", "N"))
        for combo, unit in (
            (self.displacement_unit_combo, length),
            (self.force_unit_combo, force),
        ):
            index = combo.findText(unit)
            if index < 0:
                combo.addItem(unit)
                index = combo.findText(unit)
            combo.setCurrentIndex(index)

    def _heat_flux_unit(self) -> str:
        power = str(getattr(self._project_units, "power", "W"))
        length = str(getattr(self._project_units, "length", "m"))
        return f"{power}/{length}^2"

    def _update_validation_state(self, *_args: object) -> None:
        record_id = self.current_record_id()
        selected = bool(record_id)
        create_reason = self._local_validation_reason(excluding_record_id="")
        edit_reason = self._local_validation_reason(excluding_record_id=record_id)
        self.create_button.setEnabled(not selected and not create_reason)
        self.edit_button.setEnabled(selected and not edit_reason)
        self.delete_button.setEnabled(selected)
        if selected:
            status = self._statuses.get(self.current_record_id())
            reason_code = str(getattr(status, "reason_code", "NOT_EVALUATED"))
            message = str(getattr(status, "message", "Setup record not evaluated."))
            self.validity_label.setText(reason_code)
            self.validity_label.setToolTip(message)
            kind = self._record_identity()[0]
            self.adapter_readiness_label.setText(self._adapter_readiness(kind, status))
        else:
            self.validity_label.setText("NOT_EVALUATED")
            self.adapter_readiness_label.setText("NOT_EVALUATED")
        reason = edit_reason if selected else create_reason
        self.kind_controls_diagnostic.setText(
            reason or "Typed parameters use Project canonical units. Apply remains explicit."
        )

    def _local_validation_reason(self, *, excluding_record_id: str = "") -> str:
        kind = str(self.record_kind_combo.currentData() or "")
        normalized_name = self.name_edit.text().strip().casefold()
        if not normalized_name:
            return "A non-empty unique setup name is required."
        if any(
            str(getattr(record, "name", "")).strip().casefold() == normalized_name
            and str(getattr(record, "id", "")) != excluding_record_id
            for _record_kind, record in self._records()
        ):
            return "Setup names must be unique (case-insensitive)."
        target_id = str(self.target_combo.currentData() or "")
        if not target_id:
            return "A target NamedSelection is required."
        entity_kind = self._selection_kinds.get(target_id, "")
        expected = {
            "material_region": {"cell"},
            "fixed_support": {"node"},
            "prescribed_displacement": {"node"},
            "force": {"node"},
            "pressure": {"cell"},
            "temperature": {"node", "cell"},
            "heat_flux": {"cell"},
        }.get(kind, set())
        if entity_kind not in expected:
            label = self.record_kind_combo.currentText()
            target_kind = entity_kind or "unknown"
            return f"{label} is incompatible with {target_kind} targets."
        if (
            self._resolved_selection_ids is not None
            and target_id not in self._resolved_selection_ids
            and not self._editing_stale_target(target_id)
        ):
            return "The target NamedSelection must resolve exactly on the active mesh."
        if (
            kind in {"pressure", "heat_flux"}
            and self._explicit_surface_selection_ids is not None
            and target_id not in self._explicit_surface_selection_ids
            and not self._editing_stale_target(target_id)
        ):
            return (
                "Pressure and heat flux require an exact triangle, quad, or polygon "
                "surface NamedSelection."
            )
        if kind == "material_region" and not self.material_combo.currentData():
            return "A Project material is required."
        if kind == "fixed_support" and not any(
            checkbox.isChecked() for checkbox in self.support_dof_checks
        ):
            return "At least one translational support DOF is required."
        if kind == "prescribed_displacement" and not any(
            checkbox.isChecked() for checkbox in self.displacement_enabled_checks
        ):
            return "At least one prescribed translational component is required."
        if kind == "force":
            direction = tuple(spin.value() for spin in self.direction_spins)
            if self.magnitude_spin.value() == 0.0 or not any(direction):
                return "Force requires a finite non-zero global vector."
        return ""

    def _editing_stale_target(self, target_id: str) -> bool:
        kind, record_id = self._record_identity()
        if not kind or not record_id:
            return False
        record = self._record(kind, record_id)
        if record is None or str(getattr(record, "target_selection_id", "")) != target_id:
            return False
        reason = str(getattr(self._statuses.get(record_id), "reason_code", ""))
        return reason in {
            "MESH_NOT_LOADED",
            "MESH_REF_MISMATCH",
            "MESH_FINGERPRINT_MISMATCH",
            "LEGACY_IDENTITY_UNVERIFIED",
        }

    def _begin_create(self) -> None:
        blocked = self.record_list.blockSignals(True)
        try:
            self.record_list.setCurrentItem(None)
            self.record_list.clearSelection()
        finally:
            self.record_list.blockSignals(blocked)
        self.record_kind_combo.setEnabled(True)
        self.name_edit.clear()
        self.enabled_checkbox.setChecked(True)
        self.record_visibility_checkbox.setEnabled(False)
        self._update_form_controls()
        self.recordSelected.emit("", "", "")

    @staticmethod
    def _select_combo_data(combo: QtWidgets.QComboBox, value: str) -> None:
        combo.setCurrentIndex(combo.findData(str(value)))

    def _record(self, kind: str, record_id: str) -> object | None:
        for candidate_kind, record in self._records():
            if candidate_kind == kind and str(getattr(record, "id", "")) == record_id:
                return record
        return None

    def _populate_record(self, kind: str, record: object) -> None:
        self.record_kind_combo.setCurrentIndex(self.record_kind_combo.findData(kind))
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
        dofs = tuple(int(item) for item in getattr(record, "translational_dofs", ()))
        self._selected_translational_dofs = dofs or (1, 2, 3)
        for index, checkbox in enumerate(self.support_dof_checks, 1):
            checkbox.setChecked(index in self._selected_translational_dofs)
        self._selected_enabled = bool(getattr(record, "enabled", True))
        self.enabled_checkbox.setChecked(self._selected_enabled)
        components = tuple(getattr(record, "components", (None, None, None)))
        for checkbox, spin, component in zip(
            self.displacement_enabled_checks,
            self.displacement_spins,
            components,
            strict=True,
        ):
            checkbox.setChecked(component is not None)
            if component is not None:
                spin.setValue(float(component.value))
                unit_index = self.displacement_unit_combo.findText(str(component.unit))
                if unit_index >= 0:
                    self.displacement_unit_combo.setCurrentIndex(unit_index)
        magnitude = getattr(record, "magnitude", None)
        if magnitude is not None:
            self.magnitude_spin.setValue(float(getattr(magnitude, "value", 0.0)))
            unit_index = self.force_unit_combo.findText(str(getattr(magnitude, "unit", "N")))
            if unit_index >= 0:
                self.force_unit_combo.setCurrentIndex(unit_index)
        value = getattr(record, "value", None)
        if value is not None:
            self.scalar_spin.setValue(float(getattr(value, "value", 0.0)))
            self.scalar_unit_label.setText(str(getattr(value, "unit", "")))
        direction = tuple(getattr(record, "direction", (1.0, 0.0, 0.0)))
        if len(direction) == 3:
            for spin, value in zip(self.direction_spins, direction, strict=True):
                spin.setValue(float(value))
        self.coordinate_system_label.setText(str(getattr(record, "coordinate_system", "GLOBAL")))
        self.application_mode_label.setText(str(getattr(record, "application_mode", "PER_NODE")))
        record_id = str(getattr(record, "id", ""))
        visible = self._record_visibility.get(record_id, True)
        self.record_visibility_checkbox.blockSignals(True)
        self.record_visibility_checkbox.setChecked(visible)
        self.record_visibility_checkbox.setEnabled(True)
        self.record_visibility_checkbox.blockSignals(False)
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
        if record_id and not self._local_validation_reason(excluding_record_id=record_id):
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
            self.enabled_checkbox.setChecked(True)
            self.record_visibility_checkbox.setEnabled(False)
            self._update_form_controls()
            return
        kind, record_id = self._record_identity()
        record = self._record(kind, record_id)
        if record is not None:
            self._populate_record(kind, record)
        target_id = str(current.data(QtCore.Qt.ItemDataRole.UserRole + 1) or "")
        self.recordSelected.emit(kind, record_id, target_id)

    def _remember_enabled(self, enabled: bool) -> None:
        self._selected_enabled = bool(enabled)
        self._update_validation_state()

    def _record_visibility_toggled(self, visible: bool) -> None:
        record_id = self.current_record_id()
        if not record_id:
            return
        self._record_visibility[record_id] = bool(visible)
        self.recordVisibilityChanged.emit(record_id, bool(visible))

    @staticmethod
    def _adapter_readiness(kind: str, status: object | None) -> str:
        reason = str(getattr(status, "reason_code", "NOT_EVALUATED"))
        state = str(getattr(status, "state", ""))
        if "." in state:
            state = state.rsplit(".", 1)[-1]
        if state != "READY":
            return f"BLOCKED: {reason}"
        if kind not in CALCULIX_SUPPORTED_KINDS:
            return "UNSUPPORTED_BY_ADAPTER"
        return "READY"


__all__ = [
    "CALCULIX_SUPPORTED_KINDS",
    "CATEGORY_LABELS",
    "SETUP_KIND_OPTIONS",
    "SetupOverlayPanel",
]
