"""Plot viewer for FigureDataset previews."""

from __future__ import annotations

from typing import Any

from osw.scripts.mscript.figure_dataset import FigureDataset

from .qt_compat import PySide6UnavailableError, pyside6_missing_message

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


class PlotViewer(_BaseWidget):
    """PySide6 panel that lists captured FigureDataset records."""

    def __init__(self, parent: object | None = None) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("plotViewer")
        self.summary_label = QtWidgets.QLabel("No figures loaded.", self)
        self.summary_label.setObjectName("plotViewerSummary")
        self.summary_label.setWordWrap(True)
        self.figure_list = QtWidgets.QListWidget(self)
        self.figure_list.setObjectName("figureList")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.figure_list)

    def load_figure_dataset(self, dataset: FigureDataset) -> None:
        self.figure_list.clear()
        for row in figure_display_rows(dataset):
            self.figure_list.addItem(row)
        self.summary_label.setText(
            f"Dataset: {dataset.dataset_id}\nFigures: {len(dataset.figures)}"
        )


def build_plot_viewer(parent: object | None = None) -> object:
    return PlotViewer(parent)


def figure_display_rows(dataset: FigureDataset) -> tuple[str, ...]:
    return tuple(
        f"{record.figure_id} | {record.title} | {record.image_format}"
        for record in dataset.figures
    )
