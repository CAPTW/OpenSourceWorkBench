"""GUI-only manager for persisted 3D scene screenshot report records.

The dialog presents snapshots supplied by MainWindow and dispatches exact-row
targets back to MainWindow. It owns no Project state, performs no filesystem
mutation, and never saves a project. Screenshot paths remain local report
artifact references only; they are not validation evidence or release assets.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from osw.core.report_asset import ReportAssetPathKind, ReportScreenshotAsset
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object

_NO_SELECTION_TEXT = "Select a persisted scene screenshot first."
_NO_RECORDS_TEXT = "No persisted scene screenshot records are available."
_CALLBACK_MISSING_TEXT = "Persisted screenshot management is not wired to MainWindow."


@dataclass(frozen=True)
class PersistedReportScreenshotTarget:
    """Presentation snapshot used for exact-row stale-target protection."""

    index: int
    expected_id: str
    expected_asset: ReportScreenshotAsset


PersistedAssetsProvider = Callable[[], Sequence[ReportScreenshotAsset]]
TransientIdsProvider = Callable[[], Sequence[str]]
TargetCallback = Callable[[PersistedReportScreenshotTarget], object]


class PersistedReportScreenshotManager(_BaseDialog):
    """Present persisted screenshot rows and dispatch MainWindow-owned actions."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        assets_provider: PersistedAssetsProvider,
        transient_ids_provider: TransientIdsProvider,
        edit_callback: TargetCallback,
        remove_callback: TargetCallback,
        relink_callback: TargetCallback,
    ) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswPersistedReportScreenshotManager")
        self.setWindowTitle("Manage persisted report screenshots")
        self.setModal(True)
        self.resize(980, 440)

        self._assets_provider = assets_provider
        self._transient_ids_provider = transient_ids_provider
        self._edit_callback = edit_callback
        self._remove_callback = remove_callback
        self._relink_callback = relink_callback
        # Presentation snapshots only. MainWindow revalidates every target
        # against the current Project before any mutation.
        self._targets: tuple[PersistedReportScreenshotTarget, ...] = ()

        self.summary_label = QtWidgets.QLabel(self)
        self.summary_label.setObjectName("oswPersistedScreenshotManagerSummary")
        self.summary_label.setWordWrap(True)

        self.records_table = QtWidgets.QTableWidget(self)
        self.records_table.setObjectName("oswPersistedScreenshotManagerTable")
        self.records_table.setColumnCount(5)
        self.records_table.setHorizontalHeaderLabels(
            ("Row", "Record ID", "Caption", "Stored path", "State")
        )
        self.records_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.records_table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.records_table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        header = self.records_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)

        self.status_label = QtWidgets.QLabel(self)
        self.status_label.setObjectName("oswPersistedScreenshotManagerStatus")
        self.status_label.setWordWrap(True)

        self.edit_button = QtWidgets.QPushButton("Edit caption...", self)
        self.edit_button.setObjectName("oswPersistedScreenshotManagerEditButton")
        self.remove_button = QtWidgets.QPushButton(
            "Remove selected persisted screenshot", self
        )
        self.remove_button.setObjectName("oswPersistedScreenshotManagerRemoveButton")
        self.relink_button = QtWidgets.QPushButton(
            "Relink selected screenshot...", self
        )
        self.relink_button.setObjectName("oswPersistedScreenshotManagerRelinkButton")
        self.close_button = QtWidgets.QPushButton("Close", self)
        self.close_button.setObjectName("oswPersistedScreenshotManagerCloseButton")

        actions = QtWidgets.QHBoxLayout()
        actions.addWidget(self.edit_button)
        actions.addWidget(self.remove_button)
        actions.addWidget(self.relink_button)
        actions.addStretch(1)
        actions.addWidget(self.close_button)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.records_table)
        layout.addWidget(self.status_label)
        layout.addLayout(actions)

        self.records_table.itemSelectionChanged.connect(self._update_action_buttons)
        self.edit_button.clicked.connect(lambda _checked=False: self._dispatch_edit())
        self.remove_button.clicked.connect(lambda _checked=False: self._dispatch_remove())
        self.relink_button.clicked.connect(lambda _checked=False: self._dispatch_relink())
        self.close_button.clicked.connect(self.close)
        self.refresh_records()

    def targets(self) -> tuple[PersistedReportScreenshotTarget, ...]:
        """Return the current presentation targets for tests and selection logic."""
        return self._targets

    def selected_target(self) -> PersistedReportScreenshotTarget | None:
        row = self.records_table.currentRow()
        if 0 <= row < len(self._targets):
            return self._targets[row]
        return None

    def refresh_records(self) -> None:
        """Rebuild presentation rows from the MainWindow-owned providers."""
        previous_row = self.records_table.currentRow()
        assets = tuple(self._assets_provider() or ())
        transient_ids = tuple(str(item) for item in self._transient_ids_provider() or ())
        states = persisted_report_screenshot_states(assets, transient_ids)
        self._targets = tuple(
            PersistedReportScreenshotTarget(index, asset.id, _snapshot_asset(asset))
            for index, asset in enumerate(assets)
        )

        self.records_table.blockSignals(True)
        self.records_table.setRowCount(len(assets))
        for index, (asset, state) in enumerate(zip(assets, states, strict=True)):
            values = (
                str(index),
                asset.id or "(missing id)",
                asset.caption or "(no caption)",
                asset.path or "(no image path)",
                state,
            )
            for column, value in enumerate(values):
                self.records_table.setItem(index, column, QtWidgets.QTableWidgetItem(value))
        if 0 <= previous_row < len(assets):
            self.records_table.selectRow(previous_row)
        else:
            self.records_table.clearSelection()
            self.records_table.setCurrentCell(-1, -1)
        self.records_table.blockSignals(False)

        self.summary_label.setText(f"Persisted report screenshots: {len(assets)}")
        self.status_label.setText(_NO_RECORDS_TEXT if not assets else "")
        self._update_action_buttons()

    def show_status(self, message: str) -> None:
        self.status_label.setText(str(message))

    def _update_action_buttons(self) -> None:
        enabled = self.selected_target() is not None
        self.edit_button.setEnabled(enabled)
        self.remove_button.setEnabled(enabled)
        self.relink_button.setEnabled(enabled)

    def _target_or_diagnostic(self) -> PersistedReportScreenshotTarget | None:
        target = self.selected_target()
        if target is None:
            self.show_status(_NO_SELECTION_TEXT)
        return target

    def _dispatch_edit(self) -> None:
        target = self._target_or_diagnostic()
        if target is None:
            return
        if self._edit_callback is None:
            self.show_status(_CALLBACK_MISSING_TEXT)
            return
        self._edit_callback(target)

    def _dispatch_remove(self) -> None:
        target = self._target_or_diagnostic()
        if target is None:
            return
        if self._remove_callback is None:
            self.show_status(_CALLBACK_MISSING_TEXT)
            return
        self._remove_callback(target)

    def _dispatch_relink(self) -> None:
        target = self._target_or_diagnostic()
        if target is None:
            return
        if self._relink_callback is None:
            self.show_status(_CALLBACK_MISSING_TEXT)
            return
        self._relink_callback(target)


def persisted_report_screenshot_states(
    assets: Sequence[ReportScreenshotAsset],
    transient_ids: Sequence[str] = (),
) -> tuple[str, ...]:
    """Return deterministic presentation status for each persisted row."""
    ids = tuple(asset.id for asset in assets)
    counts = Counter(item for item in ids if item)
    first_index: dict[str, int] = {}
    for index, record_id in enumerate(ids):
        if record_id and record_id not in first_index:
            first_index[record_id] = index
    transient = {str(item) for item in transient_ids if str(item)}

    states: list[str] = []
    for index, asset in enumerate(assets):
        if asset.path_kind is ReportAssetPathKind.LEGACY_RAW:
            path_state = (
                "legacy_raw — explicit legacy/raw reference; availability not checked"
            )
        elif asset.path_kind is not None:
            path_state = (
                f"{asset.path_kind.value}; Unresolved — path resolver unavailable."
            )
        elif not asset.path:
            path_state = "no path"
        elif Path(asset.path).is_file():
            path_state = "available"
        else:
            path_state = "missing"

        details: list[str] = [path_state]
        record_id = asset.id
        if not record_id:
            details.append("missing id")
        elif record_id in transient:
            details.append("shadowed by transient")
        if record_id and counts[record_id] > 1:
            details.append("duplicate id")
            if record_id not in transient:
                if first_index[record_id] == index:
                    details.append("first persisted record wins")
                else:
                    details.append("shadowed by earlier persisted record")
        states.append("; ".join(details))
    return tuple(states)


def _snapshot_asset(asset: ReportScreenshotAsset) -> ReportScreenshotAsset:
    """Create an independent complete snapshot of the JSON-friendly asset."""
    payload = json.loads(json.dumps(asset.to_dict()))
    return ReportScreenshotAsset.from_dict(payload)


__all__ = [
    "PersistedReportScreenshotManager",
    "PersistedReportScreenshotTarget",
    "persisted_report_screenshot_states",
]
