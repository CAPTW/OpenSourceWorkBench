"""Core 3D Workspace persisted report asset contracts.

Solver-agnostic, GUI-free, JSON-friendly data contracts for report assets
persisted in ProjectSchema. The first persisted report asset is a scene
screenshot reference: local path plus provenance metadata only.

These models are metadata/state only. They never trigger a solver, never render,
and never import GUI, rendering, mesh-io, solver-runner, or post-processing
code, keeping the inward dependency direction intact. A persisted scene
screenshot asset stores a local path only -- image bytes are not copied here,
and the asset is a local report artifact only: it is not validation evidence and
not a release asset. Conversion to and from the transient session record lives
in the post-processing layer.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .validation import ValidationReport

REPORT_SCREENSHOT_ASSET_CAVEAT = (
    "Persisted scene screenshot assets store local paths only; they are not "
    "validation evidence or release assets."
)


def _string_dict(value: Mapping[str, Any] | None) -> dict[str, Any]:
    return dict(value or {})


def _str_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(str(item) for item in value)


@dataclass(frozen=True)
class ReportScreenshotAsset:
    """A persisted report scene-screenshot reference (local path + provenance).

    Core-owned: ``scene_state`` and ``glyph_options`` are opaque provenance
    dictionaries, so this module carries no dependency on the post-processing
    view-state types. The ``metadata`` caveat flags ``is_release_asset`` and
    ``is_validation_evidence`` are always forced ``False`` -- a persisted
    screenshot is a local report artifact only.
    """

    id: str = ""
    kind: str = "scene_screenshot"
    path: str = ""
    caption: str = ""
    mesh_ref: str = ""
    result_dataset_ref: str = ""
    field_id: str = ""
    selection_ids: tuple[str, ...] = ()
    scene_state: dict[str, Any] = field(default_factory=dict)
    glyph_options: dict[str, Any] = field(default_factory=dict)
    diagnostics: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", str(self.id or ""))
        object.__setattr__(self, "kind", str(self.kind or "scene_screenshot"))
        object.__setattr__(self, "path", str(self.path or ""))
        object.__setattr__(self, "caption", str(self.caption or ""))
        object.__setattr__(self, "mesh_ref", str(self.mesh_ref or ""))
        object.__setattr__(self, "result_dataset_ref", str(self.result_dataset_ref or ""))
        object.__setattr__(self, "field_id", str(self.field_id or ""))
        object.__setattr__(self, "selection_ids", _str_tuple(self.selection_ids))
        object.__setattr__(self, "scene_state", _string_dict(self.scene_state))
        object.__setattr__(self, "glyph_options", _string_dict(self.glyph_options))
        object.__setattr__(self, "diagnostics", _str_tuple(self.diagnostics))
        metadata = _string_dict(self.metadata)
        # A persisted screenshot is never a release asset or validation evidence.
        metadata["is_release_asset"] = False
        metadata["is_validation_evidence"] = False
        metadata.setdefault("artifact_caveat", REPORT_SCREENSHOT_ASSET_CAVEAT)
        object.__setattr__(self, "metadata", metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "path": self.path,
            "caption": self.caption,
            "mesh_ref": self.mesh_ref,
            "result_dataset_ref": self.result_dataset_ref,
            "field_id": self.field_id,
            "selection_ids": list(self.selection_ids),
            "scene_state": dict(self.scene_state),
            "glyph_options": dict(self.glyph_options),
            "diagnostics": list(self.diagnostics),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> ReportScreenshotAsset:
        if not isinstance(data, Mapping):
            msg = "ReportScreenshotAsset data must be a mapping."
            raise TypeError(msg)
        return cls(
            id=str(data.get("id", "")),
            kind=str(data.get("kind", "scene_screenshot")),
            path=str(data.get("path", "")),
            caption=str(data.get("caption", "")),
            mesh_ref=str(data.get("mesh_ref", "")),
            result_dataset_ref=str(data.get("result_dataset_ref", "")),
            field_id=str(data.get("field_id", "")),
            selection_ids=_str_tuple(data.get("selection_ids", ())),
            scene_state=_string_dict(data.get("scene_state", {})),
            glyph_options=_string_dict(data.get("glyph_options", {})),
            diagnostics=_str_tuple(data.get("diagnostics", ())),
            metadata=_string_dict(data.get("metadata", {})),
        )

    def validate(self, *, path: str = "report_screenshot") -> ValidationReport:
        # Model validation only; filesystem existence is a report/export concern.
        report = ValidationReport()
        if not self.id:
            report.add_error(f"{path}.id", "Report screenshot asset id is required.")
        if not self.path:
            report.add_warning(
                f"{path}.path",
                "Report screenshot asset has no local image path (metadata only).",
            )
        return report


def coerce_report_screenshots(
    value: Sequence[Any] | None,
) -> list[ReportScreenshotAsset]:
    """Coerce a sequence of ReportScreenshotAsset/dict into a list of assets."""
    if not value:
        return []
    result: list[ReportScreenshotAsset] = []
    for item in value:
        if isinstance(item, ReportScreenshotAsset):
            result.append(item)
        elif isinstance(item, Mapping):
            result.append(ReportScreenshotAsset.from_dict(item))
        else:
            msg = "Project report screenshot must be a ReportScreenshotAsset or mapping."
            raise TypeError(msg)
    return result


__all__ = [
    "REPORT_SCREENSHOT_ASSET_CAVEAT",
    "ReportScreenshotAsset",
    "coerce_report_screenshots",
]
