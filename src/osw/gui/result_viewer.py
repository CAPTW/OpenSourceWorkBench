"""Result viewer for structured OSW dataset previews."""

from __future__ import annotations

from typing import Any

from osw.core.result_dataset import ResultCatalog, ResultDataset, ResultTable
from osw.mesh.mesh_model import MeshData
from osw.post.field_view_model import (
    FieldViewModel,
    field_view_model_from_result_dataset,
)
from osw.post.pyvista_scene import (
    PyVistaSceneConfig,
    PyVistaSceneState,
    build_result_contour_placeholder,
    build_scene_state,
)
from osw.post.result_view_model import (
    ResultViewModel,
    figure_dataset_to_view_dataset,
    mesh_info_to_view_dataset,
    result_catalog_from_result_datasets,
    result_dataset_to_view_model,
    summarize_result_catalog_for_view,
    summarize_result_dataset_for_view,
)

from .qt_compat import PySide6UnavailableError, pyside6_missing_message
from .theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


class ResultViewer(_BaseWidget):
    """PySide6 panel that shows a unified, summary-first result catalog."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswResultViewer")
        self._tokens = DARK_TOKENS
        self._catalog = ResultCatalog(catalog_id="empty-results")
        self._view_model: ResultViewModel | None = None
        self._field_view_model: FieldViewModel | None = None
        self._figure_dataset: object | None = None

        self.dataset_selector = QtWidgets.QComboBox(self)
        self.dataset_selector.setObjectName("oswResultDatasetSelector")
        self.catalog_summary_panel = QtWidgets.QLabel("No result catalog loaded.", self)
        self.catalog_summary_panel.setObjectName("oswResultCatalogSummaryPanel")
        self.catalog_summary_panel.setWordWrap(True)
        self.summary_panel = QtWidgets.QLabel("No result datasets loaded.", self)
        self.summary_panel.setObjectName("oswResultSummaryPanel")
        self.summary_panel.setWordWrap(True)
        self.handoff_panel = QtWidgets.QLabel("No viewer handoff available.", self)
        self.handoff_panel.setObjectName("oswResultHandoffPanel")
        self.handoff_panel.setWordWrap(True)
        self.empty_state = QtWidgets.QLabel("No result datasets loaded.", self)
        self.empty_state.setObjectName("oswResultEmptyState")
        self.empty_state.setWordWrap(True)
        self.scalar_cards = QtWidgets.QTableWidget(self)
        self.scalar_cards.setObjectName("oswResultScalarCards")
        self.scalar_cards.setColumnCount(4)
        self.scalar_cards.setHorizontalHeaderLabels(["Scalar", "Value", "Unit", "Source"])
        self.series_panel = QtWidgets.QTableWidget(self)
        self.series_panel.setObjectName("oswResultSeriesPanel")
        self.series_panel.setColumnCount(5)
        self.series_panel.setHorizontalHeaderLabels(["Series", "Points", "First", "Last", "Unit"])

        from osw.gui.table_viewer import TableViewer
        from osw.gui.widgets.field_viewer_panel import FieldViewerPanel

        self.table_viewer = TableViewer(self)
        self.table_viewer.setObjectName("oswResultTableViewer")
        self.field_viewer = FieldViewerPanel(self)
        self.artifacts_panel = QtWidgets.QTableWidget(self)
        self.artifacts_panel.setObjectName("oswResultArtifactsPanel")
        self.artifacts_panel.setColumnCount(5)
        self.artifacts_panel.setHorizontalHeaderLabels(
            ["Role", "Path", "Format", "Exists", "Size"]
        )
        self.diagnostics_list = QtWidgets.QListWidget(self)
        self.diagnostics_list.setObjectName("oswResultDiagnosticsList")
        self.plot_handoff_button = QtWidgets.QPushButton("Open Figure Dataset", self)
        self.plot_handoff_button.setObjectName("oswResultFigureHandoffButton")
        self.plot_handoff_button.setEnabled(False)

        self.surface_toggle = QtWidgets.QCheckBox("Surface", self)
        self.surface_toggle.setObjectName("surfaceToggle")
        self.surface_toggle.setChecked(True)
        self.edge_toggle = QtWidgets.QCheckBox("Edges", self)
        self.edge_toggle.setObjectName("edgeToggle")
        self.axis_toggle = QtWidgets.QCheckBox("Axes", self)
        self.axis_toggle.setObjectName("axisToggle")
        self.axis_toggle.setChecked(True)
        self.grid_toggle = QtWidgets.QCheckBox("Grid", self)
        self.grid_toggle.setObjectName("gridToggle")
        self.scalar_field_placeholder = QtWidgets.QLabel("Scalar field: none", self)
        self.scalar_field_placeholder.setObjectName("scalarFieldPlaceholder")
        self.summary_label = QtWidgets.QLabel("Result viewer placeholder", self)
        self.summary_label.setObjectName("resultViewerPlaceholder")
        self.summary_label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(self.catalog_summary_panel)
        layout.addWidget(self.dataset_selector)
        layout.addWidget(self.summary_panel)
        layout.addWidget(self.handoff_panel)
        layout.addWidget(self.empty_state)
        layout.addWidget(self.scalar_cards)
        layout.addWidget(self.series_panel)
        layout.addWidget(self.field_viewer)
        layout.addWidget(self.table_viewer, 1)
        layout.addWidget(self.artifacts_panel)
        layout.addWidget(self.diagnostics_list)
        layout.addWidget(self.plot_handoff_button)

        toggles = QtWidgets.QHBoxLayout()
        toggles.addWidget(self.surface_toggle)
        toggles.addWidget(self.edge_toggle)
        toggles.addWidget(self.axis_toggle)
        toggles.addWidget(self.grid_toggle)
        toggles.addStretch(1)
        layout.addLayout(toggles)
        layout.addWidget(self.scalar_field_placeholder)
        layout.addWidget(self.summary_label)

        self.dataset_selector.currentIndexChanged.connect(self._on_dataset_selected)
        self.plot_handoff_button.clicked.connect(self._on_plot_handoff_requested)
        self.set_theme_tokens(self._tokens)

    def load_mesh_preview(self, mesh_data: MeshData) -> PyVistaSceneState:
        state = build_scene_state(mesh_data, config=self._scene_config())
        self.summary_label.setText(_mesh_summary_text(state))
        self.set_result_datasets((mesh_info_to_view_dataset(state.mesh_info),))
        return state

    def set_result_catalog(self, catalog: ResultCatalog | object) -> None:
        self._catalog = catalog if isinstance(catalog, ResultCatalog) else ResultCatalog.from_dict(
            catalog.to_dict() if hasattr(catalog, "to_dict") else catalog
        )
        self.dataset_selector.blockSignals(True)
        self.dataset_selector.clear()
        for dataset in self._catalog.datasets:
            view_model = result_dataset_to_view_model(dataset)
            self.dataset_selector.addItem(view_model.title, dataset.dataset_id)
        self.dataset_selector.blockSignals(False)
        if self._catalog.datasets:
            selected = self._catalog.selected_dataset_id
            index = self.dataset_selector.findData(selected)
            self.dataset_selector.setCurrentIndex(index if index >= 0 else 0)
            self._show_dataset(self.dataset_selector.currentIndex())
        else:
            self._show_empty_catalog()
        self._populate_catalog_summary()

    def set_result_datasets(
        self,
        datasets: tuple[ResultDataset, ...] | list[ResultDataset],
    ) -> None:
        self.set_result_catalog(result_catalog_from_result_datasets(datasets))

    def add_result_dataset(self, dataset: ResultDataset) -> None:
        self.set_result_catalog(
            ResultCatalog(
                catalog_id=self._catalog.catalog_id,
                project_name=self._catalog.project_name,
                datasets=(*self._catalog.datasets, dataset),
                selected_dataset_id=dataset.dataset_id,
                diagnostics=self._catalog.diagnostics,
                metadata=self._catalog.metadata,
            )
        )

    def set_result_view_model(self, view_model: ResultViewModel) -> None:
        self._view_model = view_model
        self._populate_view_model(view_model)

    def current_view_model(self) -> ResultViewModel | None:
        return self._view_model

    def current_field_view_model(self) -> FieldViewModel | None:
        return self._field_view_model

    def current_catalog(self) -> ResultCatalog:
        return self._catalog

    def set_figure_dataset(self, dataset: object) -> None:
        self._figure_dataset = dataset
        self.set_result_datasets((figure_dataset_to_view_dataset(dataset),))

    def handoff_to_plot_viewer(self, plot_viewer: object) -> bool:
        if self._figure_dataset is None:
            return False
        set_dataset = getattr(plot_viewer, "set_figure_dataset", None)
        if not callable(set_dataset):
            return False
        set_dataset(self._figure_dataset)
        return True

    def contour_placeholder(self, scalar_field: str) -> object:
        dataset = self._catalog.selected_dataset()
        return build_result_contour_placeholder(dataset, scalar_field=scalar_field)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QWidget#oswResultViewer {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QComboBox, QTableWidget, QListWidget, QLabel#oswResultEmptyState {"
            f"background-color: {tokens.bg_viewport};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "}"
            "QLabel#oswResultSummaryPanel {"
            f"color: {tokens.text_primary};"
            "}"
            "QPushButton {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "padding: 5px 8px;"
            "border-radius: 3px;"
            "}"
        )
        if hasattr(self.table_viewer, "setStyleSheet"):
            self.table_viewer.setStyleSheet("")

    def _scene_config(self) -> PyVistaSceneConfig:
        return PyVistaSceneConfig(
            show_surface=self.surface_toggle.isChecked(),
            show_edges=self.edge_toggle.isChecked(),
            show_axes=self.axis_toggle.isChecked(),
            show_grid=self.grid_toggle.isChecked(),
            scalar_field=None,
        )

    def _on_dataset_selected(self, index: int) -> None:
        self._show_dataset(index)

    def _show_dataset(self, index: int) -> None:
        if index < 0 or index >= len(self._catalog.datasets):
            self._show_empty_catalog()
            return
        dataset = self._catalog.datasets[index]
        self._field_view_model = field_view_model_from_result_dataset(dataset)
        self.field_viewer.set_field_view_model(self._field_view_model)
        self.set_result_view_model(result_dataset_to_view_model(dataset))

    def _show_empty_catalog(self) -> None:
        self._view_model = None
        self._field_view_model = FieldViewModel(
            dataset_id="empty-fields",
            title="Field Metadata",
            empty_state_message="No mesh field arrays are available.",
        )
        self.field_viewer.set_field_view_model(self._field_view_model)
        self.summary_panel.setText("No result datasets loaded.")
        self.catalog_summary_panel.setText("No result catalog loaded.")
        self.handoff_panel.setText("No viewer handoff available.")
        self.empty_state.setText("No result datasets loaded.")
        self.empty_state.setVisible(True)
        self.scalar_cards.setRowCount(0)
        self.series_panel.setRowCount(0)
        self.artifacts_panel.setRowCount(0)
        self.diagnostics_list.clear()
        self.plot_handoff_button.setEnabled(False)

    def _populate_view_model(self, view_model: ResultViewModel) -> None:
        self.empty_state.setVisible(bool(view_model.empty_state_message))
        self.empty_state.setText(view_model.empty_state_message)
        field_count = len(self._field_view_model.arrays) if self._field_view_model else 0
        dataset = self._dataset_for_view_model(view_model)
        details = (
            summarize_result_dataset_for_view(dataset, field_count=field_count)
            if dataset is not None
            else None
        )
        if details is not None:
            self.summary_panel.setText(_dataset_details_text(details))
            self.handoff_panel.setText(_handoff_text(details))
        else:
            self.summary_panel.setText("No selected result dataset.")
            self.handoff_panel.setText("No viewer handoff available.")
        self._populate_scalars(view_model)
        self._populate_series(view_model)
        self._populate_table(view_model)
        self._populate_artifacts(view_model)
        self._populate_diagnostics(view_model)
        self.plot_handoff_button.setEnabled(bool(view_model.figures and self._figure_dataset))

    def _populate_catalog_summary(self) -> None:
        summary = summarize_result_catalog_for_view(self._catalog)
        self.catalog_summary_panel.setText(_catalog_summary_text(summary))

    def _dataset_for_view_model(self, view_model: ResultViewModel) -> ResultDataset | None:
        for dataset in self._catalog.datasets:
            if dataset.dataset_id == view_model.dataset_id:
                return dataset
        return self._catalog.selected_dataset()

    def _populate_scalars(self, view_model: ResultViewModel) -> None:
        self.scalar_cards.setRowCount(len(view_model.scalars))
        for row, scalar in enumerate(view_model.scalars):
            values = (
                scalar.name,
                str(scalar.value),
                scalar.unit,
                scalar.source,
            )
            for column, value in enumerate(values):
                self.scalar_cards.setItem(row, column, QtWidgets.QTableWidgetItem(value))
        self.scalar_cards.resizeColumnsToContents()

    def _populate_series(self, view_model: ResultViewModel) -> None:
        self.series_panel.setRowCount(len(view_model.series))
        for row, series in enumerate(view_model.series):
            first_value = series.y_values[0] if series.y_values else ""
            last_value = series.y_values[-1] if series.y_values else ""
            values = (
                series.name,
                str(len(series.y_values)),
                _format_number(first_value),
                _format_number(last_value),
                series.y_unit,
            )
            for column, value in enumerate(values):
                self.series_panel.setItem(row, column, QtWidgets.QTableWidgetItem(value))
        self.series_panel.resizeColumnsToContents()

    def _populate_table(self, view_model: ResultViewModel) -> None:
        if view_model.tables:
            self.table_viewer.load_result_table(view_model.tables[0])
        else:
            self.table_viewer.load_result_table(
                ResultTable(
                    table_id="empty",
                    title="No table data",
                    columns=("Message",),
                    rows=(("No table data available.",),),
                )
            )

    def _populate_artifacts(self, view_model: ResultViewModel) -> None:
        self.artifacts_panel.setRowCount(len(view_model.artifacts))
        for row, artifact in enumerate(view_model.artifacts):
            values = (
                artifact.role,
                artifact.path,
                artifact.format,
                "yes" if artifact.exists else "missing",
                "" if artifact.size_bytes is None else str(artifact.size_bytes),
            )
            for column, value in enumerate(values):
                self.artifacts_panel.setItem(row, column, QtWidgets.QTableWidgetItem(value))
        self.artifacts_panel.resizeColumnsToContents()

    def _populate_diagnostics(self, view_model: ResultViewModel) -> None:
        self.diagnostics_list.clear()
        for diagnostic in view_model.diagnostics:
            self.diagnostics_list.addItem(diagnostic)
        if not view_model.diagnostics:
            self.diagnostics_list.addItem("No diagnostics.")

    def _on_plot_handoff_requested(self) -> None:
        # MainWindow owns opening PlotViewer; this button only records the available handoff.
        if self._figure_dataset is not None:
            self.summary_panel.setText(f"{self.summary_panel.text()}\nFigureDataset ready.")


def build_result_viewer(parent: object | None = None) -> object:
    return ResultViewer(parent)


def _mesh_summary_text(state: PyVistaSceneState) -> str:
    return (
        f"Nodes: {state.mesh_info.nodes}\n"
        f"Elements: {state.mesh_info.elements}\n"
        f"Cell types: {', '.join(state.mesh_info.cell_types) or 'none'}\n"
        f"Bounds: {state.bounding_box.minimum} to {state.bounding_box.maximum}"
    )


def _format_number(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def _catalog_summary_text(summary: object) -> str:
    kind_counts = tuple(getattr(summary, "kind_counts", ()) or ())
    kinds = ", ".join(f"{kind}: {count}" for kind, count in kind_counts) or "none"
    selected_title = str(getattr(summary, "selected_title", ""))
    selected_suffix = f" ({selected_title})" if selected_title else ""
    return (
        f"Catalog: {getattr(summary, 'catalog_id', '') or 'results'}\n"
        f"Project: {getattr(summary, 'project_name', '') or 'Not recorded'}\n"
        f"Datasets: {getattr(summary, 'dataset_count', 0)} | Types: {kinds}\n"
        f"Active: {getattr(summary, 'selected_dataset_id', '') or 'none'}"
        f"{selected_suffix}\n"
        f"Sources: {getattr(summary, 'source_summary', '')}\n"
        f"Diagnostics: {getattr(summary, 'diagnostics_count', 0)}"
    )


def _dataset_details_text(details: object) -> str:
    kind = getattr(details, "kind", "")
    source_kind = getattr(details, "source_kind", "")
    return (
        f"{getattr(details, 'title', '')}\n"
        f"Dataset ID: {getattr(details, 'dataset_id', '')}\n"
        f"Type: {kind} | Source kind: {source_kind}\n"
        f"Source: {getattr(details, 'source', '') or 'Not recorded'}\n"
        f"Scalars: {getattr(details, 'scalar_count', 0)} | "
        f"Series: {getattr(details, 'series_count', 0)} | "
        f"Tables: {getattr(details, 'table_count', 0)} | "
        f"Figures: {getattr(details, 'figure_count', 0)} | "
        f"Artifacts: {getattr(details, 'artifact_count', 0)} | "
        f"Fields: {getattr(details, 'field_count', 0)} | "
        f"Diagnostics: {getattr(details, 'diagnostics_count', 0)}"
    )


def _handoff_text(details: object) -> str:
    hints = tuple(getattr(details, "handoff_hints", ()) or ())
    limitations = tuple(getattr(details, "limitations", ()) or ())
    lines = ["Viewer handoff:"]
    lines.extend(f"- {hint}" for hint in hints)
    if getattr(details, "report_compatible", False) and "Report compatible" not in hints:
        lines.append("- Report compatible")
    if limitations:
        lines.append("Limitations:")
        lines.extend(f"- {limitation}" for limitation in limitations)
    return "\n".join(lines)
