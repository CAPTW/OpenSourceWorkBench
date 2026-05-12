"""Project tree widget for the OSW GUI shell."""

from __future__ import annotations

from .qt_compat import require_qt_widgets

PROJECT_SECTIONS = (
    "Geometry",
    "Mesh",
    "Scripts",
    "Physics",
    "Solvers",
    "Results",
    "Reports",
)


def build_project_tree(parent: object | None = None) -> object:
    _, QtWidgets = require_qt_widgets()

    tree = QtWidgets.QTreeWidget(parent)
    tree.setObjectName("projectTree")
    tree.setHeaderLabel("Project")

    root_item = QtWidgets.QTreeWidgetItem(["OSW Project"])
    for section in PROJECT_SECTIONS:
        root_item.addChild(QtWidgets.QTreeWidgetItem([section]))

    tree.addTopLevelItem(root_item)
    root_item.setExpanded(True)
    return tree
