"""Serializable report data models for OSW report generation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from osw.core.diagnostics import DiagnosticReport
from osw.core.report_asset import ReportAssetPathKind, ReportScreenshotAsset
from osw.post.scene_model import SceneScreenshotRecord, SceneViewState

if TYPE_CHECKING:
    from osw.core.project_schema import Project


class ReportFormat(StrEnum):
    HTML = "html"
    MARKDOWN = "markdown"
    PDF_OPTIONAL = "pdf_optional"
    JSON_SUMMARY = "json_summary"


@dataclass(frozen=True)
class ReportAsset:
    asset_id: str
    path: str | Path
    role: str
    format: str = ""
    exists: bool | None = None
    size_bytes: int | None = None
    caption: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        path = str(self.path)
        exists = Path(path).exists() if self.exists is None and path else bool(self.exists)
        size_bytes = self.size_bytes
        if size_bytes is None and exists:
            candidate = Path(path)
            if candidate.is_file():
                size_bytes = candidate.stat().st_size
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "exists", bool(exists))
        object.__setattr__(self, "size_bytes", size_bytes)
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "path": self.path,
            "role": self.role,
            "format": self.format,
            "exists": self.exists,
            "size_bytes": self.size_bytes,
            "caption": self.caption,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ReportAsset:
        return cls(
            asset_id=str(payload.get("asset_id", "")),
            path=str(payload.get("path", "")),
            role=str(payload.get("role", "")),
            format=str(payload.get("format", "")),
            exists=bool(payload.get("exists", False)),
            size_bytes=_optional_int(payload.get("size_bytes")),
            caption=str(payload.get("caption", "")),
            metadata=dict(payload.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class ReportSection:
    section_id: str
    title: str
    level: int = 2
    content_blocks: tuple[str, ...] = field(default_factory=tuple)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "level", int(self.level))
        object.__setattr__(
            self,
            "content_blocks",
            tuple(str(item) for item in self.content_blocks),
        )
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "level": self.level,
            "content_blocks": list(self.content_blocks),
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ReportSection:
        return cls(
            section_id=str(payload.get("section_id", "")),
            title=str(payload.get("title", "")),
            level=int(payload.get("level", 2) or 2),
            content_blocks=tuple(str(item) for item in payload.get("content_blocks", ()) or ()),
            diagnostics=DiagnosticReport.from_dict(payload.get("diagnostics", {}) or {}),
            metadata=dict(payload.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class ReportTable:
    table_id: str
    title: str
    columns: tuple[str, ...] = field(default_factory=tuple)
    rows: tuple[tuple[str, ...], ...] = field(default_factory=tuple)
    truncated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", tuple(str(item) for item in self.columns))
        object.__setattr__(
            self,
            "rows",
            tuple(tuple(str(cell) for cell in row) for row in self.rows),
        )
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "title": self.title,
            "columns": list(self.columns),
            "rows": [list(row) for row in self.rows],
            "truncated": self.truncated,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ReportTable:
        return cls(
            table_id=str(payload.get("table_id", "")),
            title=str(payload.get("title", "")),
            columns=tuple(str(item) for item in payload.get("columns", ()) or ()),
            rows=tuple(
                tuple(str(cell) for cell in row)
                for row in payload.get("rows", ()) or ()
            ),
            truncated=bool(payload.get("truncated", False)),
            metadata=dict(payload.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class ReportFigure:
    figure_id: str
    title: str = ""
    image_path: str | Path | None = None
    vector_path: str | Path | None = None
    pdf_path: str | Path | None = None
    caption: str = ""
    source_run_id: str = ""
    source_script: str = ""
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "image_path", _path_text(self.image_path))
        object.__setattr__(self, "vector_path", _path_text(self.vector_path))
        object.__setattr__(self, "pdf_path", _path_text(self.pdf_path))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def primary_path(self) -> str:
        return self.image_path or self.vector_path or self.pdf_path

    @property
    def format(self) -> str:
        path = self.primary_path
        return Path(path).suffix.lower().lstrip(".") if path else ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "figure_id": self.figure_id,
            "title": self.title,
            "image_path": self.image_path,
            "vector_path": self.vector_path,
            "pdf_path": self.pdf_path,
            "caption": self.caption,
            "source_run_id": self.source_run_id,
            "source_script": self.source_script,
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ReportFigure:
        return cls(
            figure_id=str(payload.get("figure_id", "")),
            title=str(payload.get("title", "")),
            image_path=payload.get("image_path") or None,
            vector_path=payload.get("vector_path") or None,
            pdf_path=payload.get("pdf_path") or None,
            caption=str(payload.get("caption", "")),
            source_run_id=str(payload.get("source_run_id", "")),
            source_script=str(payload.get("source_script", "")),
            diagnostics=DiagnosticReport.from_dict(payload.get("diagnostics", {}) or {}),
            metadata=dict(payload.get("metadata", {}) or {}),
        )


SCENE_SCREENSHOT_ARTIFACT_CAVEAT = (
    "Scene screenshot is a local report artifact only; it is not validation "
    "evidence and not a release asset."
)


def scene_screenshot_to_report_figure(record: SceneScreenshotRecord) -> ReportFigure:
    """Bridge a local ``SceneScreenshotRecord`` into a report ``ReportFigure``.

    The conversion is pure and filesystem-agnostic: it never renders, never runs
    a solver, and never touches ProjectSchema. Scene provenance -- mesh ref,
    result dataset ref, scalar field id, vector/glyph state, selections, camera,
    and render options -- is preserved in the figure metadata alongside a
    friendly caveat recording that the screenshot is a local report artifact
    only (not validation evidence and not a release asset).

    Whether the image file exists on disk is a report/export concern handled by
    the renderer. A metadata-only record (no local path) is annotated with a
    figure diagnostic warning so a missing image surfaces as a placeholder
    rather than a crash.
    """
    scene = record.scene_state
    glyph = scene.glyph_options
    selection_ids = tuple(record.selection_ids) or tuple(scene.selected_selection_ids)
    scalar_field_id = scene.scalar_field_id or scene.render_options.color_by
    diagnostics = DiagnosticReport()
    path_kind = record.path_kind
    unresolved_without_resolver = path_kind in {
        ReportAssetPathKind.EXTERNAL_ABSOLUTE,
        ReportAssetPathKind.PROJECT_RELATIVE,
    }
    if unresolved_without_resolver:
        diagnostics.add_warning(
            "report-scene-screenshot-path-unresolved-no-resolver",
            f"Scene screenshot {record.id or '<unnamed>'} with path kind "
            f"{path_kind.value} is unresolved because no path resolver is available.",
            hint=(
                "Keep this metadata-only report entry until an authorized path "
                "resolver supplies an effective local path."
            ),
        )
    elif not record.path:
        diagnostics.add_warning(
            "report-scene-screenshot-path-missing",
            f"Scene screenshot {record.id or '<unnamed>'} has no local image path "
            "(metadata only).",
            hint=(
                "Capture a local screenshot image, or keep the record as a "
                "metadata-only report entry."
            ),
        )
    metadata: dict[str, Any] = {
        "kind": "scene_screenshot",
        "screenshot_id": record.id,
        "mesh_ref": record.mesh_ref,
        "result_dataset_ref": record.dataset_ref,
        "scalar_field_id": scalar_field_id,
        "vector_field": glyph.vector_field,
        "glyph_enabled": glyph.enabled,
        "glyph_scale": glyph.scale,
        "glyph_max_count": glyph.max_glyph_count,
        "selection_ids": list(selection_ids),
        "camera": scene.camera.to_dict(),
        "render_options": scene.render_options.to_dict(),
        "glyph_options": glyph.to_dict(),
        "created_by": record.created_by,
        "artifact_caveat": SCENE_SCREENSHOT_ARTIFACT_CAVEAT,
        "is_release_asset": False,
        "is_validation_evidence": False,
        "scene_metadata": dict(record.metadata),
    }
    active_scene_provenance = record.metadata.get(
        "osw.active_scene.provenance"
    )
    if isinstance(active_scene_provenance, Mapping):
        metadata["active_scene_provenance"] = dict(active_scene_provenance)
    if path_kind is not None:
        metadata["path_kind"] = path_kind.value
    if unresolved_without_resolver:
        metadata["path_status"] = "unresolved_no_resolver"
    return ReportFigure(
        figure_id=record.id or "scene-screenshot",
        title=record.caption or record.id or "Scene screenshot",
        image_path=None if unresolved_without_resolver else record.path or None,
        caption=record.caption or "",
        diagnostics=diagnostics,
        metadata=metadata,
    )


def scene_screenshots_to_report_figures(
    records: Iterable[SceneScreenshotRecord],
) -> tuple[ReportFigure, ...]:
    """Bridge many ``SceneScreenshotRecord`` values into report figures."""
    return tuple(scene_screenshot_to_report_figure(record) for record in records)


def scene_screenshot_to_report_asset(record: SceneScreenshotRecord) -> ReportScreenshotAsset:
    """Bridge a transient ``SceneScreenshotRecord`` into a core ``ReportScreenshotAsset``.

    Runs outside core so ProjectSchema stays post-independent. Provenance and the
    local-artifact caveat are preserved; ``scene_state``/``glyph_options`` are
    serialized to opaque dicts. No image bytes are copied -- only the local path.
    """
    scene = record.scene_state
    glyph = scene.glyph_options
    metadata = dict(record.metadata)
    if record.created_by and "created_by" not in metadata:
        metadata["created_by"] = record.created_by
    return ReportScreenshotAsset(
        id=record.id,
        path=record.path,
        caption=record.caption or "",
        mesh_ref=record.mesh_ref or "",
        result_dataset_ref=record.dataset_ref or "",
        field_id=scene.scalar_field_id or scene.render_options.color_by or "",
        selection_ids=tuple(record.selection_ids) or tuple(scene.selected_selection_ids),
        scene_state=scene.to_dict(),
        glyph_options=glyph.to_dict(),
        metadata=metadata,
        path_kind=record.path_kind,
    )


def scene_screenshots_to_report_assets(
    records: Iterable[SceneScreenshotRecord],
) -> tuple[ReportScreenshotAsset, ...]:
    """Bridge many ``SceneScreenshotRecord`` values into core report assets."""
    return tuple(scene_screenshot_to_report_asset(record) for record in records)


def report_asset_to_scene_screenshot(asset: ReportScreenshotAsset) -> SceneScreenshotRecord:
    """Bridge a persisted core ``ReportScreenshotAsset`` back into a record.

    Reconstructs the post-layer ``SceneViewState`` from the opaque ``scene_state``
    dict so the persisted asset feeds the existing report screenshot bridge for
    preview/export.
    """
    scene_state = (
        SceneViewState.from_dict(asset.scene_state) if asset.scene_state else SceneViewState()
    )
    return SceneScreenshotRecord(
        id=asset.id,
        path=asset.path,
        caption=asset.caption or None,
        scene_state=scene_state,
        dataset_ref=asset.result_dataset_ref or None,
        mesh_ref=asset.mesh_ref or None,
        selection_ids=asset.selection_ids,
        created_by=asset.metadata.get("created_by"),
        metadata=dict(asset.metadata),
        path_kind=asset.path_kind,
    )


def report_assets_to_scene_screenshots(
    assets: Iterable[ReportScreenshotAsset],
) -> tuple[SceneScreenshotRecord, ...]:
    """Bridge many persisted core report assets back into records."""
    return tuple(report_asset_to_scene_screenshot(asset) for asset in assets)


@dataclass(frozen=True)
class ReportSummary:
    title: str
    project_name: str
    run_label: str = ""
    created_at: str = ""
    sections: tuple[ReportSection, ...] = field(default_factory=tuple)
    tables: tuple[ReportTable, ...] = field(default_factory=tuple)
    figures: tuple[ReportFigure, ...] = field(default_factory=tuple)
    assets: tuple[ReportAsset, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "sections", tuple(self.sections))
        object.__setattr__(self, "tables", tuple(self.tables))
        object.__setattr__(self, "figures", tuple(self.figures))
        object.__setattr__(self, "assets", tuple(self.assets))
        object.__setattr__(self, "warnings", tuple(str(item) for item in self.warnings))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def section_titles(self) -> tuple[str, ...]:
        return tuple(section.title for section in self.sections)

    @property
    def warning_count(self) -> int:
        return len(self.warnings) + len(self.diagnostics.warnings())

    @property
    def figure_count(self) -> int:
        return len(self.figures)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "project_name": self.project_name,
            "run_label": self.run_label,
            "created_at": self.created_at,
            "sections": [section.to_dict() for section in self.sections],
            "tables": [table.to_dict() for table in self.tables],
            "figures": [figure.to_dict() for figure in self.figures],
            "assets": [asset.to_dict() for asset in self.assets],
            "warnings": list(self.warnings),
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ReportSummary:
        return cls(
            title=str(payload.get("title", "")),
            project_name=str(payload.get("project_name", "")),
            run_label=str(payload.get("run_label", "")),
            created_at=str(payload.get("created_at", "")),
            sections=tuple(
                ReportSection.from_dict(section)
                for section in payload.get("sections", ()) or ()
                if isinstance(section, Mapping)
            ),
            tables=tuple(
                ReportTable.from_dict(table)
                for table in payload.get("tables", ()) or ()
                if isinstance(table, Mapping)
            ),
            figures=tuple(
                ReportFigure.from_dict(figure)
                for figure in payload.get("figures", ()) or ()
                if isinstance(figure, Mapping)
            ),
            assets=tuple(
                ReportAsset.from_dict(asset)
                for asset in payload.get("assets", ()) or ()
                if isinstance(asset, Mapping)
            ),
            warnings=tuple(str(item) for item in payload.get("warnings", ()) or ()),
            diagnostics=DiagnosticReport.from_dict(payload.get("diagnostics", {}) or {}),
            metadata=dict(payload.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class ReportBuildRequest:
    project: Project
    output_path: str | Path | None = None
    format: str | ReportFormat = ReportFormat.HTML
    include_figures: bool = True
    include_tables: bool = True
    include_warnings: bool = True
    include_known_limitations: bool = True
    include_validation_summary: bool = True
    asset_mode: str = "relative"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "output_path", _path_text(self.output_path))
        object.__setattr__(self, "format", _format_value(self.format))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        project_to_dict = getattr(self.project, "to_dict", None)
        return {
            "project": project_to_dict() if callable(project_to_dict) else {},
            "output_path": self.output_path,
            "format": self.format,
            "include_figures": self.include_figures,
            "include_tables": self.include_tables,
            "include_warnings": self.include_warnings,
            "include_known_limitations": self.include_known_limitations,
            "include_validation_summary": self.include_validation_summary,
            "asset_mode": self.asset_mode,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ReportBuildResult:
    status: str
    output_path: str | Path
    summary: ReportSummary
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    assets: tuple[ReportAsset, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "output_path", _path_text(self.output_path))
        object.__setattr__(self, "assets", tuple(self.assets))

    @property
    def ok(self) -> bool:
        return self.status in {"ok", "warning"} and not self.diagnostics.has_errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "output_path": self.output_path,
            "summary": self.summary.to_dict(),
            "diagnostics": self.diagnostics.to_dict(),
            "assets": [asset.to_dict() for asset in self.assets],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ReportBuildResult:
        summary_payload = payload.get("summary", {})
        summary = (
            ReportSummary.from_dict(summary_payload)
            if isinstance(summary_payload, Mapping)
            else ReportSummary(title="", project_name="")
        )
        return cls(
            status=str(payload.get("status", "error")),
            output_path=str(payload.get("output_path", "")),
            summary=summary,
            diagnostics=DiagnosticReport.from_dict(payload.get("diagnostics", {}) or {}),
            assets=tuple(
                ReportAsset.from_dict(asset)
                for asset in payload.get("assets", ()) or ()
                if isinstance(asset, Mapping)
            ),
        )


def _format_value(value: str | ReportFormat) -> str:
    if isinstance(value, ReportFormat):
        return value.value
    text = str(value or ReportFormat.HTML.value).strip().lower()
    aliases = {"md": ReportFormat.MARKDOWN.value, "json": ReportFormat.JSON_SUMMARY.value}
    text = aliases.get(text, text)
    try:
        return ReportFormat(text).value
    except ValueError:
        return text


def _path_text(path: str | Path | None) -> str:
    return "" if path in (None, "") else str(path)


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
