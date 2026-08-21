"""Left project tree panel for the OpenSolver Workbench run screen."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from osw.core.demo_project import create_heatsink_flow_demo_project
from osw.core.project_schema import Project
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtGui = None
    QtWidgets = None


@dataclass(frozen=True, slots=True)
class ProjectTreeNode:
    """Static demo tree record for the HeatSink_Flow reference project."""

    label: str
    kind: str = "file"
    icon_key: str = "file"
    complete: bool = False
    data: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    children: tuple[ProjectTreeNode, ...] = field(default_factory=tuple)


DEMO_PROJECT_TREE = ProjectTreeNode(
    "HeatSink_Flow",
    kind="project",
    icon_key="project",
    children=(
        ProjectTreeNode(
            "Geometry",
            kind="group",
            icon_key="geometry",
            children=(
                ProjectTreeNode("heatsink.step", icon_key="geometry_file"),
                ProjectTreeNode("enclosure.stp", icon_key="geometry_file"),
                ProjectTreeNode("fluid_domain.csg", icon_key="geometry_file"),
            ),
        ),
        ProjectTreeNode(
            "Mesh",
            kind="group",
            icon_key="mesh",
            children=(
                ProjectTreeNode("mesh.msh", icon_key="mesh_file", complete=True),
                ProjectTreeNode("mesh_stats.txt", icon_key="mesh_file"),
            ),
        ),
        ProjectTreeNode(
            "Physics",
            kind="group",
            icon_key="physics",
            children=(
                ProjectTreeNode("heat_transfer.yaml", icon_key="config_file"),
                ProjectTreeNode("turbulence.yaml", icon_key="config_file"),
            ),
        ),
        ProjectTreeNode(
            "Solvers",
            kind="group",
            icon_key="solver",
            children=(
                ProjectTreeNode("chtSolver", icon_key="solver_file"),
                ProjectTreeNode("settings.json", icon_key="config_file"),
            ),
        ),
        ProjectTreeNode(
            "Scripts",
            kind="group",
            icon_key="script",
            children=(
                ProjectTreeNode("preprocess.m", icon_key="script_file"),
                ProjectTreeNode("run_case.m", icon_key="script_file"),
                ProjectTreeNode("postprocess.m", icon_key="script_file"),
            ),
        ),
        ProjectTreeNode(
            "Results",
            kind="group",
            icon_key="result",
            children=(
                ProjectTreeNode(
                    "run_0001",
                    kind="run",
                    icon_key="result",
                    children=(
                        ProjectTreeNode("fields.ex2", icon_key="result_file"),
                        ProjectTreeNode("residuals.dat", icon_key="result_file"),
                        ProjectTreeNode("monitor.log", icon_key="log_file"),
                    ),
                ),
                ProjectTreeNode("run_0000 (baseline)", kind="run", icon_key="result_file"),
            ),
        ),
        ProjectTreeNode(
            "Reports",
            kind="group",
            icon_key="report",
            children=(
                ProjectTreeNode("report.md", icon_key="report_file"),
                ProjectTreeNode("report.pdf", icon_key="report_file"),
            ),
        ),
    ),
)


def _walk_nodes(node: ProjectTreeNode) -> tuple[ProjectTreeNode, ...]:
    nodes = [node]
    for child in node.children:
        nodes.extend(_walk_nodes(child))
    return tuple(nodes)


MAJOR_GROUP_LABELS = tuple(child.label for child in DEMO_PROJECT_TREE.children)
DEMO_PROJECT_LABELS = tuple(node.label for node in _walk_nodes(DEMO_PROJECT_TREE))
_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


def project_tree_filter_matches(text: str) -> list[str]:
    """Return demo tree labels that directly match a case-insensitive filter."""

    query = text.strip().casefold()
    if not query:
        return list(DEMO_PROJECT_LABELS)
    return [label for label in DEMO_PROJECT_LABELS if query in label.casefold()]


def _project_to_tree_node(project: Project) -> ProjectTreeNode:
    solver = project.solver_config
    return ProjectTreeNode(
        project.metadata.name,
        kind="project",
        icon_key="project",
        children=(
            ProjectTreeNode(
                "Geometry",
                kind="group",
                icon_key="geometry",
                children=tuple(
                    ProjectTreeNode(_ref_label(ref), icon_key="geometry_file")
                    for ref in project.geometry_refs
                ),
            ),
            ProjectTreeNode(
                "Mesh",
                kind="group",
                icon_key="mesh",
                children=tuple(
                    ProjectTreeNode(
                        _ref_label(ref),
                        kind="mesh_ref",
                        icon_key="mesh_file",
                        complete=_mesh_is_complete(ref),
                        data=_mesh_ref_payload(ref),
                    )
                    for ref in project.mesh_refs
                ),
            ),
            *(
                (
                    ProjectTreeNode(
                        "Named Selections",
                        kind="group",
                        icon_key="selection",
                        children=tuple(
                            ProjectTreeNode(
                                selection.name or selection.id,
                                kind="named_selection",
                                icon_key="selection",
                                data=_named_selection_payload(selection),
                            )
                            for selection in project.selections
                        ),
                    ),
                )
                if project.selections
                else ()
            ),
            ProjectTreeNode(
                "Physics",
                kind="group",
                icon_key="physics",
                children=tuple(_physics_nodes(project)),
            ),
            ProjectTreeNode(
                "Solvers",
                kind="group",
                icon_key="solver",
                children=(
                    ProjectTreeNode(
                        solver.solver or solver.name,
                        icon_key="solver_file",
                    )
                    if solver is not None
                    else ProjectTreeNode("No solver configured", icon_key="solver_file"),
                    ProjectTreeNode(
                        str(
                            (solver.settings if solver is not None else {}).get(
                                "settings_file",
                                "settings.json",
                            )
                        ),
                        icon_key="config_file",
                    ),
                ),
            ),
            ProjectTreeNode(
                "Scripts",
                kind="group",
                icon_key="script",
                children=tuple(
                    ProjectTreeNode(_ref_label(ref), icon_key="script_file")
                    for ref in project.script_refs
                ),
            ),
            ProjectTreeNode(
                "Results",
                kind="group",
                icon_key="result",
                children=tuple(_result_nodes(project)),
            ),
            ProjectTreeNode(
                "Reports",
                kind="group",
                icon_key="report",
                children=tuple(
                    ProjectTreeNode(label, icon_key="report_file")
                    for label in _report_labels(project)
                ),
            ),
        ),
    )


def _ref_label(ref: object) -> str:
    name = str(getattr(ref, "name", "") or "")
    path = str(getattr(ref, "path", "") or "")
    return name or Path(path).name or str(getattr(ref, "id", ""))


def _mesh_is_complete(ref: object) -> bool:
    label = _ref_label(ref)
    status = str(getattr(ref, "status", "") or "").casefold()
    return label == "mesh.msh" or status in {"complete", "completed"}


def _mesh_ref_payload(ref: object) -> tuple[tuple[str, str], ...]:
    payload: dict[str, str] = {"source": "project_mesh_ref"}
    for key in ("id", "ref_id", "name", "path", "format", "status"):
        value = str(getattr(ref, key, "") or "").strip()
        if value:
            payload[key] = value
    mesh_ref = (
        payload.get("id")
        or payload.get("ref_id")
        or payload.get("path")
        or payload.get("name")
        or ""
    )
    if mesh_ref:
        payload["mesh_ref"] = mesh_ref
    return tuple(payload.items())


def _named_selection_payload(selection: object) -> tuple[tuple[str, str], ...]:
    payload = {
        "selection_id": str(getattr(selection, "id", "") or ""),
        "entity_kind": str(
            getattr(getattr(selection, "entity_kind", ""), "value", "")
            or getattr(selection, "entity_kind", "")
            or ""
        ),
        "mesh_ref": str(getattr(selection, "source_mesh_ref", "") or ""),
    }
    targets = tuple(getattr(selection, "targets", ()) or ())
    locator = getattr(targets[0], "locator", None) if targets else None
    fingerprint = str(getattr(locator, "mesh_fingerprint", "") or "")
    if fingerprint:
        payload["mesh_fingerprint"] = fingerprint
    return tuple((key, value) for key, value in payload.items() if value)


def _physics_nodes(project: Project) -> list[ProjectTreeNode]:
    physics = project.primary_physics
    nodes = [
        ProjectTreeNode(label, icon_key="config_file")
        for label in (physics.files if physics is not None else ())
    ]
    if project.boundary_curves:
        nodes.append(
            ProjectTreeNode(
                "Boundary Curves",
                kind="group",
                icon_key="curve",
                children=tuple(
                    ProjectTreeNode(
                        str(getattr(curve, "name", "") or getattr(curve, "curve_id", "")),
                        icon_key="curve_file",
                    )
                    for curve in project.boundary_curves
                ),
            )
        )
    if physics is not None:
        from osw.core.solver_setup import SetupRecordKind, iter_solver_setup_records

        grouped: dict[str, list[object]] = {
            "Materials": [],
            "Boundary Conditions": [],
            "Loads": [],
            "Thermal Conditions": [],
        }
        group_for_kind = {
            SetupRecordKind.MATERIAL_REGION: "Materials",
            SetupRecordKind.FIXED_SUPPORT: "Boundary Conditions",
            SetupRecordKind.PRESCRIBED_DISPLACEMENT: "Boundary Conditions",
            SetupRecordKind.FORCE: "Loads",
            SetupRecordKind.PRESSURE: "Loads",
            SetupRecordKind.TEMPERATURE: "Thermal Conditions",
            SetupRecordKind.HEAT_FLUX: "Thermal Conditions",
        }
        for record in iter_solver_setup_records(physics):
            grouped[group_for_kind[record.setup_kind]].append(record)
        for label, records in grouped.items():
            if not records:
                continue
            nodes.append(
                ProjectTreeNode(
                    label,
                    kind="group",
                    icon_key="physics",
                    children=tuple(
                        ProjectTreeNode(
                            str(record.name or record.id),
                            kind="solver_setup",
                            icon_key="physics",
                            data=_setup_payload(record, project),
                        )
                        for record in records
                    ),
                )
            )
    return nodes


def _setup_payload(record: object, project: Project) -> tuple[tuple[str, str], ...]:
    target_id = str(getattr(record, "target_selection_id", "") or "")
    target = next(
        (
            selection
            for selection in project.selections
            if str(getattr(selection, "id", "")) == target_id
        ),
        None,
    )
    material_id = str(getattr(record, "material_id", "") or "")
    material = next(
        (
            item
            for item in project.materials
            if str(getattr(item, "material_id", "")) == material_id
        ),
        None,
    )
    payload = {
        "setup_id": str(getattr(record, "id", "") or ""),
        "setup_kind": str(
            getattr(getattr(record, "setup_kind", ""), "value", "")
            or getattr(record, "setup_kind", "")
            or ""
        ),
        "target_selection_id": target_id,
        "target_name": str(getattr(target, "name", "") or target_id),
        "enabled": "true" if bool(getattr(record, "enabled", True)) else "false",
        "material_id": material_id,
        "material_name": str(getattr(material, "name", "") or material_id),
    }
    return tuple((key, value) for key, value in payload.items() if value)


def _result_nodes(project: Project) -> list[ProjectTreeNode]:
    run_0001_children = [
        ProjectTreeNode(_ref_label(ref), icon_key="result_file")
        for ref in project.result_refs
        if getattr(ref, "run_id", "") == "run_0001" and getattr(ref, "role", "") != "run"
    ]
    nodes: list[ProjectTreeNode] = []
    if any(getattr(ref, "run_id", "") == "run_0001" for ref in project.result_refs):
        nodes.append(
            ProjectTreeNode(
                "run_0001",
                kind="run",
                icon_key="result",
                children=tuple(run_0001_children),
            )
        )
    for ref in project.result_refs:
        if getattr(ref, "run_id", "") != "run_0001":
            nodes.append(ProjectTreeNode(_ref_label(ref), kind="run", icon_key="result_file"))
    return nodes


def _report_labels(project: Project) -> list[str]:
    if project.report.artifacts:
        return list(project.report.artifacts)
    path_label = Path(project.report.path).name
    return [path_label] if path_label else []


class ProjectTreePanel(_BaseWidget):
    """Theme-aware project sidebar for the HeatSink_Flow demo project."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtGui is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswProjectTreePanel")
        self.setMinimumWidth(300)
        self.items_by_label: dict[str, object] = {}
        self._icon_cache: dict[str, object] = {}
        self._current_tokens = DARK_TOKENS
        self._current_project: Project | None = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 8)
        layout.setSpacing(8)

        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        self.header_label = QtWidgets.QLabel("PROJECTS", self)
        self.header_label.setObjectName("oswProjectTreeHeader")
        self.search_button = QtWidgets.QToolButton(self)
        self.search_button.setObjectName("oswProjectTreeSearchButton")
        self.search_button.setText("⌕")
        self.refresh_button = QtWidgets.QToolButton(self)
        self.refresh_button.setObjectName("oswProjectTreeRefreshButton")
        self.refresh_button.setText("↻")
        header_layout.addWidget(self.header_label, 1)
        header_layout.addWidget(self.search_button)
        header_layout.addWidget(self.refresh_button)

        self.tree = QtWidgets.QTreeWidget(self)
        self.tree.setObjectName("oswProjectTree")
        self.tree.setColumnCount(2)
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(14)
        self.tree.setUniformRowHeights(True)
        self.tree.setAnimated(False)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.tree.setColumnWidth(1, 24)

        self.filter_frame = QtWidgets.QFrame(self)
        self.filter_frame.setObjectName("oswProjectTreeFilters")
        filter_layout = QtWidgets.QVBoxLayout(self.filter_frame)
        filter_layout.setContentsMargins(8, 8, 8, 8)
        filter_layout.setSpacing(6)
        self.filter_label = QtWidgets.QLabel("FILTERS", self.filter_frame)
        self.filter_label.setObjectName("oswProjectTreeFiltersLabel")
        self.search_field = QtWidgets.QLineEdit(self.filter_frame)
        self.search_field.setObjectName("oswProjectTreeSearch")
        self.search_field.setPlaceholderText("Search project tree...")
        self.search_field.textChanged.connect(self.filter_tree)
        filter_layout.addWidget(self.filter_label)
        filter_layout.addWidget(self.search_field)

        self.footer_label = QtWidgets.QLabel("Active Project: HeatSink_Flow", self)
        self.footer_label.setObjectName("oswProjectTreeFooter")

        layout.addLayout(header_layout)
        layout.addWidget(self.tree, 1)
        layout.addWidget(self.filter_frame)
        layout.addWidget(self.footer_label)

        self.set_theme_tokens(DARK_TOKENS)
        self.set_project(create_heatsink_flow_demo_project())

    def populate_demo_project(self) -> None:
        self.set_project(create_heatsink_flow_demo_project())

    def set_project(self, project: Project) -> None:
        self._current_project = project
        self.populate_from_project(project)
        self.set_active_project(project.metadata.name)

    def current_project(self) -> Project | None:
        return self._current_project

    def populate_from_project(self, project: Project) -> None:
        self.tree.clear()
        self.items_by_label.clear()
        root = self._build_item(_project_to_tree_node(project))
        self.tree.addTopLevelItem(root)
        self.expand_demo_tree()
        self.tree.setColumnWidth(1, 24)

    def set_active_project(self, name: str) -> None:
        self.footer_label.setText(f"Active Project: {name}")

    def expand_demo_tree(self) -> None:
        for item in self.items_by_label.values():
            item.setExpanded(True)

    def selected_node_path(self) -> list[str]:
        item = self.tree.currentItem()
        if item is None:
            return []
        path = []
        while item is not None:
            path.append(item.text(0))
            item = item.parent()
        return list(reversed(path))

    def item_payload(self, item: object | None) -> dict[str, str]:
        """Return stable tree-item metadata stored outside the display label."""
        if item is None:
            return {}
        payload = item.data(0, QtCore.Qt.ItemDataRole.UserRole + 2)
        if not isinstance(payload, dict):
            return {}
        return {str(key): str(value) for key, value in payload.items()}

    def selected_item_payload(self) -> dict[str, str]:
        return self.item_payload(self.tree.currentItem())

    def named_selection_item(self, selection_id: str) -> object | None:
        for item in self._tree_items():
            if self.item_payload(item).get("selection_id") == selection_id:
                return item
        return None

    def setup_item(self, setup_id: str) -> object | None:
        for item in self._tree_items():
            if self.item_payload(item).get("setup_id") == setup_id:
                return item
        return None

    def current_setup_id(self) -> str:
        current = self.tree.currentItem()
        if current is None:
            return ""
        kind = str(current.data(0, QtCore.Qt.ItemDataRole.UserRole) or "")
        if kind != "solver_setup":
            return ""
        return self.item_payload(current).get("setup_id", "")

    def select_setup(self, setup_id: str, *, emit: bool = True) -> bool:
        item = self.setup_item(setup_id)
        if item is None:
            return False
        blocked = self.tree.blockSignals(not emit)
        try:
            self.tree.setCurrentItem(item)
        finally:
            self.tree.blockSignals(blocked)
        return True

    def clear_setup(self, *, emit: bool = True) -> None:
        if not self.current_setup_id():
            return
        blocked = self.tree.blockSignals(not emit)
        try:
            self.tree.setCurrentItem(None)
            self.tree.clearSelection()
        finally:
            self.tree.blockSignals(blocked)

    def set_setup_statuses(
        self,
        statuses: Mapping[str, object],
        *,
        active_setup_id: str = "",
    ) -> None:
        for item in self._tree_items():
            setup_id = self.item_payload(item).get("setup_id", "")
            if not setup_id:
                continue
            status = statuses.get(setup_id)
            reason = str(getattr(status, "reason_code", "NOT_EVALUATED"))
            payload = self.item_payload(item)
            kind = payload.get("setup_kind", "setup").replace("_", " ")
            target = payload.get("target_name", payload.get("target_selection_id", ""))
            enabled = "enabled" if payload.get("enabled") == "true" else "disabled"
            item.setText(1, f"{kind} · {target} · {enabled} · {reason}")
            item.setToolTip(
                0,
                (
                    f"Type: {kind}\nTarget: {target or 'missing'}\n"
                    f"State: {enabled}\nStatus: {reason}\n"
                    + str(getattr(status, "message", "Setup record not evaluated."))
                ),
            )
            font = item.font(0)
            font.setBold(setup_id == active_setup_id)
            item.setFont(0, font)
        self.tree.setColumnWidth(1, 360)

    def current_named_selection_id(self) -> str:
        current = self.tree.currentItem()
        if current is None:
            return ""
        kind = str(current.data(0, QtCore.Qt.ItemDataRole.UserRole) or "")
        if kind != "named_selection":
            return ""
        return self.item_payload(current).get("selection_id", "")

    def select_named_selection(self, selection_id: str, *, emit: bool = True) -> bool:
        item = self.named_selection_item(selection_id)
        if item is None:
            return False
        blocked = self.tree.blockSignals(not emit)
        try:
            self.tree.setCurrentItem(item)
        finally:
            self.tree.blockSignals(blocked)
        return True

    def clear_named_selection(self, *, emit: bool = True) -> None:
        if not self.current_named_selection_id():
            return
        blocked = self.tree.blockSignals(not emit)
        try:
            self.tree.setCurrentItem(None)
            self.tree.clearSelection()
        finally:
            self.tree.blockSignals(blocked)

    def set_named_selection_resolutions(
        self,
        resolutions: Mapping[str, object],
        *,
        active_selection_ids: tuple[str, ...] = (),
    ) -> None:
        active = set(active_selection_ids)
        for item in self._tree_items():
            selection_id = self.item_payload(item).get("selection_id", "")
            if not selection_id:
                continue
            resolution = resolutions.get(selection_id)
            state = str(getattr(resolution, "state", "UNRESOLVED"))
            if "." in state:
                state = state.rsplit(".", 1)[-1]
            item.setText(1, state)
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole + 3, state)
            item.setToolTip(
                0,
                str(
                    getattr(
                        resolution,
                        "message",
                        "Selection resolution has not been evaluated.",
                    )
                ),
            )
            font = item.font(0)
            font.setBold(selection_id in active)
            item.setFont(0, font)
        self.tree.setColumnWidth(1, 82)

    def filter_tree(self, text: str) -> None:
        query = text.strip().casefold()
        for top_index in range(self.tree.topLevelItemCount()):
            self._apply_filter_to_item(self.tree.topLevelItem(top_index), query)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._current_tokens = tokens
        self._icon_cache = self._build_icons(tokens)
        self.setStyleSheet(
            "QWidget#oswProjectTreePanel {"
            f"background-color: {tokens.bg_panel};"
            f"border-right: 1px solid {tokens.border};"
            "}"
            "QLabel#oswProjectTreeHeader {"
            f"color: {tokens.accent};"
            "font-weight: 700;"
            "letter-spacing: 0px;"
            "}"
            "QToolButton#oswProjectTreeSearchButton, "
            "QToolButton#oswProjectTreeRefreshButton {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_secondary};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 3px;"
            "padding: 2px 5px;"
            "}"
            "QTreeWidget#oswProjectTree {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_secondary};"
            f"border: 1px solid {tokens.border};"
            "font-size: 9pt;"
            "outline: 0;"
            "}"
            "QTreeWidget#oswProjectTree::item {"
            "min-height: 24px;"
            "padding: 1px 3px;"
            "}"
            "QTreeWidget#oswProjectTree::item:selected {"
            f"background-color: {tokens.primary};"
            f"color: {tokens.text_primary};"
            "}"
            "QFrame#oswProjectTreeFilters {"
            f"background-color: {tokens.bg_panel_alt};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "}"
            "QLabel#oswProjectTreeFiltersLabel {"
            f"color: {tokens.text_muted};"
            "font-weight: 700;"
            "font-size: 8pt;"
            "}"
            "QLineEdit#oswProjectTreeSearch {"
            f"background-color: {tokens.bg_viewport};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 3px;"
            "padding: 4px 6px;"
            "}"
            "QLabel#oswProjectTreeFooter {"
            f"color: {tokens.accent};"
            "font-size: 9pt;"
            "font-weight: 600;"
            "}"
        )
        if hasattr(self, "items_by_label"):
            self._refresh_item_icons()

    def _build_item(self, node: ProjectTreeNode) -> object:
        item = QtWidgets.QTreeWidgetItem([node.label, "✓" if node.complete else ""])
        item.setData(0, QtCore.Qt.ItemDataRole.UserRole, node.kind)
        item.setData(0, QtCore.Qt.ItemDataRole.UserRole + 1, node.icon_key)
        if node.data:
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole + 2, dict(node.data))
        item.setIcon(0, self._icon_cache.get(node.icon_key, self._icon_cache["file"]))
        if node.kind in {"project", "group", "run"}:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
        if node.complete:
            item.setForeground(1, QtGui.QBrush(QtGui.QColor(self._current_tokens.success)))
        self.items_by_label[node.label] = item
        for child in node.children:
            item.addChild(self._build_item(child))
        return item

    def _apply_filter_to_item(self, item: object, query: str) -> bool:
        if not query:
            item.setHidden(False)
            for index in range(item.childCount()):
                self._apply_filter_to_item(item.child(index), query)
            return True
        direct_match = query in item.text(0).casefold()
        child_match = False
        for index in range(item.childCount()):
            child_match = self._apply_filter_to_item(item.child(index), query) or child_match
        visible = direct_match or child_match
        item.setHidden(not visible)
        if visible:
            item.setExpanded(True)
        return visible

    def _refresh_item_icons(self) -> None:
        for item in self.items_by_label.values():
            icon_key = item.data(0, QtCore.Qt.ItemDataRole.UserRole + 1)
            item.setIcon(0, self._icon_cache.get(str(icon_key), self._icon_cache["file"]))
            if item.text(1):
                item.setForeground(
                    1,
                    QtGui.QBrush(QtGui.QColor(self._current_tokens.success)),
                )

    def _tree_items(self) -> tuple[object, ...]:
        items: list[object] = []

        def visit(item: object) -> None:
            items.append(item)
            for index in range(item.childCount()):
                visit(item.child(index))

        for index in range(self.tree.topLevelItemCount()):
            visit(self.tree.topLevelItem(index))
        return tuple(items)

    def _build_icons(self, tokens: ThemeTokens) -> dict[str, object]:
        # Purple/yellow are centralized category accents required by the visual spec.
        category_colors = {
            "project": tokens.accent,
            "geometry": tokens.success,
            "geometry_file": tokens.success,
            "mesh": "#9b6dff",
            "mesh_file": "#9b6dff",
            "selection": "#c084fc",
            "physics": tokens.warning,
            "curve": tokens.info,
            "curve_file": tokens.info,
            "solver": tokens.info,
            "solver_file": tokens.info,
            "script": "#f6d34b",
            "script_file": "#f6d34b",
            "result": tokens.accent,
            "result_file": tokens.accent,
            "log_file": tokens.chart_axis,
            "report": tokens.danger,
            "report_file": tokens.danger,
            "config_file": tokens.text_muted,
            "file": tokens.text_muted,
        }
        return {key: self._make_icon(color, tokens) for key, color in category_colors.items()}

    def _make_icon(self, color: str, tokens: ThemeTokens) -> object:
        pixmap = QtGui.QPixmap(14, 14)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtGui.QPen(QtGui.QColor(tokens.border), 1))
        painter.setBrush(QtGui.QColor(color))
        painter.drawRoundedRect(2, 2, 10, 10, 2, 2)
        painter.end()
        return QtGui.QIcon(pixmap)
