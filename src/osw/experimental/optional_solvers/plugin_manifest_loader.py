"""Explicit optional solver plugin manifest loader model.

The loader accepts only caller-supplied dictionaries or explicit JSON files.
It validates manifest data and classifies source/trust metadata without
importing plugin packages, scanning directories, running discovery, or
executing solver commands.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .manifest_models import OptionalSolverManifest, parse_optional_solver_manifest_dict
from .manifest_validation import (
    OptionalSolverDiagnosticSeverity,
    OptionalSolverManifestValidationReport,
    validate_optional_solver_manifest,
)


class OptionalSolverManifestSourceType(str, Enum):
    """Known optional solver manifest source categories."""

    BUILTIN = "builtin"
    PROJECT_LOCAL = "project_local"
    USER_LOCAL = "user_local"
    PLUGIN_PACKAGE = "plugin_package"
    ORGANIZATION_MANAGED = "organization_managed"
    EXPLICIT_FILE = "explicit_file"
    EXPLICIT_DICT = "explicit_dict"

    @classmethod
    def from_value(cls, value: object) -> OptionalSolverManifestSourceType:
        if isinstance(value, cls):
            return value
        return cls(str(value))


class OptionalSolverManifestTrustLabel(str, Enum):
    """Trust labels attached to loaded optional solver manifests."""

    TRUSTED_BUILTIN = "trusted_builtin"
    REVIEWED_PROJECT = "reviewed_project"
    USER_PROVIDED = "user_provided"
    THIRD_PARTY_PLUGIN = "third_party_plugin"
    ORGANIZATION_MANAGED = "organization_managed"
    UNTRUSTED = "untrusted"
    INVALID = "invalid"

    @classmethod
    def from_value(cls, value: object) -> OptionalSolverManifestTrustLabel:
        if isinstance(value, cls):
            return value
        return cls(str(value))


class OptionalSolverPluginManifestDiagnosticSeverity(str, Enum):
    """Diagnostic severities for plugin manifest loading."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"

    @classmethod
    def from_manifest(
        cls,
        severity: OptionalSolverDiagnosticSeverity,
    ) -> OptionalSolverPluginManifestDiagnosticSeverity:
        return cls(severity.value)


class OptionalSolverPluginManifestDiagnosticCategory(str, Enum):
    """Diagnostic categories for plugin manifest loading."""

    SCHEMA = "schema"
    SOURCE = "source"
    TRUST = "trust"
    CONFLICT = "conflict"
    SAFETY = "safety"
    POLICY = "policy"
    IO = "io"


@dataclass(frozen=True, slots=True)
class OptionalSolverManifestSource:
    """Source metadata attached to a manifest document."""

    source_type: OptionalSolverManifestSourceType
    trust_label: OptionalSolverManifestTrustLabel
    label: str = ""
    reference: str = ""

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
        *,
        fallback_reference: str = "",
    ) -> OptionalSolverManifestSource:
        source_type = OptionalSolverManifestSourceType.from_value(
            data.get("type") or data.get("source_type")
        )
        expected_trust = _default_trust_label(source_type)
        trust_value = data.get("trust_label") or expected_trust.value
        try:
            trust_label = OptionalSolverManifestTrustLabel.from_value(trust_value)
        except ValueError:
            trust_label = expected_trust
        return cls(
            source_type=source_type,
            trust_label=trust_label,
            label=str(data.get("label") or data.get("name") or ""),
            reference=str(
                data.get("reference")
                or data.get("ref")
                or data.get("path")
                or fallback_reference
            ),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "source_type": self.source_type.value,
            "trust_label": self.trust_label.value,
            "label": self.label,
            "reference": self.reference,
        }


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDocument:
    """Raw plugin manifest document supplied by a caller."""

    manifest_data: Mapping[str, Any]
    source: OptionalSolverManifestSource
    schema_version: str = "1"
    document_ref: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source": self.source.to_dict(),
            "document_ref": self.document_ref,
            "manifest": dict(self.manifest_data),
        }


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestLoadDiagnostic:
    """Diagnostic emitted while loading plugin manifest data."""

    code: str
    severity: OptionalSolverPluginManifestDiagnosticSeverity
    category: OptionalSolverPluginManifestDiagnosticCategory
    message: str
    source_ref: str = ""
    stack_id: str = ""
    suggested_fix: str = ""

    @property
    def is_blocking(self) -> bool:
        return self.severity in {
            OptionalSolverPluginManifestDiagnosticSeverity.ERROR,
            OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
        }

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "source_ref": self.source_ref,
            "stack_id": self.stack_id,
            "suggested_fix": self.suggested_fix,
        }


@dataclass(frozen=True, slots=True)
class OptionalSolverLoadedManifest:
    """Accepted manifest plus source/trust metadata."""

    manifest: OptionalSolverManifest
    source: OptionalSolverManifestSource
    schema_version: str
    validation_report: OptionalSolverManifestValidationReport
    diagnostics: tuple[OptionalSolverPluginManifestLoadDiagnostic, ...] = ()

    @property
    def stack_id(self) -> str:
        return self.manifest.stack_id

    def to_dict(self) -> dict[str, object]:
        return {
            "stack_id": self.stack_id,
            "display_name": self.manifest.display_name,
            "schema_version": self.schema_version,
            "source": self.source.to_dict(),
            "manifest": self.manifest.to_dict(),
            "validation": self.validation_report.to_dict(),
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


@dataclass(frozen=True, slots=True)
class OptionalSolverRejectedManifest:
    """Rejected manifest data plus diagnostics."""

    stack_id: str
    source: OptionalSolverManifestSource
    schema_version: str
    diagnostics: tuple[OptionalSolverPluginManifestLoadDiagnostic, ...]
    manifest_data: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "stack_id": self.stack_id,
            "schema_version": self.schema_version,
            "source": self.source.to_dict(),
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "manifest": dict(self.manifest_data),
        }


@dataclass(frozen=True, slots=True)
class OptionalSolverManifestConflict:
    """Conflict detected between manifests for the same stack id."""

    stack_id: str
    winning_source: OptionalSolverManifestSource
    rejected_source: OptionalSolverManifestSource
    message: str

    def to_dict(self) -> dict[str, object]:
        return {
            "stack_id": self.stack_id,
            "winning_source": self.winning_source.to_dict(),
            "rejected_source": self.rejected_source.to_dict(),
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestLoadReport:
    """Result of loading explicit optional solver manifest documents."""

    accepted_manifests: tuple[OptionalSolverLoadedManifest, ...] = ()
    rejected_manifests: tuple[OptionalSolverRejectedManifest, ...] = ()
    conflicts: tuple[OptionalSolverManifestConflict, ...] = ()
    diagnostics: tuple[OptionalSolverPluginManifestLoadDiagnostic, ...] = ()

    @property
    def has_errors(self) -> bool:
        return bool(self.rejected_manifests) or any(
            item.is_blocking for item in self.diagnostics
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "accepted_count": len(self.accepted_manifests),
            "rejected_count": len(self.rejected_manifests),
            "conflict_count": len(self.conflicts),
            "accepted_manifests": [
                item.to_dict() for item in self.accepted_manifests
            ],
            "rejected_manifests": [
                item.to_dict() for item in self.rejected_manifests
            ],
            "conflicts": [item.to_dict() for item in self.conflicts],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "plugin_manifest_presence_is_validation_evidence": False,
        }


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestLoaderOptions:
    """Options for explicit plugin manifest data loading."""

    supported_schema_versions: tuple[str, ...] = ("1", "1.0")
    builtin_stack_ids: tuple[str, ...] = (
        "gmsh",
        "octave",
        "calculix",
        "openfoam",
        "coolprop_cantera",
        "pyvista_meshio",
    )
    reject_builtin_overrides: bool = True


def load_optional_solver_plugin_manifest_dict(
    data: Mapping[str, Any],
    *,
    source: OptionalSolverManifestSource | None = None,
    options: OptionalSolverPluginManifestLoaderOptions | None = None,
) -> OptionalSolverPluginManifestLoadReport:
    """Load one explicit manifest dictionary or wrapped document."""

    return load_optional_solver_plugin_manifest_documents(
        (data,),
        source=source or _default_source(OptionalSolverManifestSourceType.EXPLICIT_DICT),
        options=options,
    )


def load_optional_solver_plugin_manifest_json(
    path: str | Path,
    *,
    source: OptionalSolverManifestSource | None = None,
    options: OptionalSolverPluginManifestLoaderOptions | None = None,
) -> OptionalSolverPluginManifestLoadReport:
    """Load one explicitly supplied JSON manifest path."""

    text_path = str(path)
    default_source = source or _default_source(
        OptionalSolverManifestSourceType.EXPLICIT_FILE,
        reference=text_path,
    )
    if "://" in text_path:
        diagnostic = _diagnostic(
            "OSPL_NETWORK_SOURCE_UNSUPPORTED",
            OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
            OptionalSolverPluginManifestDiagnosticCategory.IO,
            "Network manifest URLs are not supported by the loader model.",
            default_source.reference,
            "",
            "Supply an explicit local JSON file path.",
        )
        return _report_from_rejection(
            OptionalSolverRejectedManifest(
                stack_id="",
                source=default_source,
                schema_version="",
                diagnostics=(diagnostic,),
            )
        )

    manifest_path = Path(path)
    if manifest_path.is_dir():
        diagnostic = _diagnostic(
            "OSPL_DIRECTORY_SCAN_FORBIDDEN",
            OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
            OptionalSolverPluginManifestDiagnosticCategory.IO,
            "Directory scanning is not implemented for plugin manifests.",
            default_source.reference,
            "",
            "Supply one explicit JSON file.",
        )
        return _report_from_rejection(
            OptionalSolverRejectedManifest(
                stack_id="",
                source=default_source,
                schema_version="",
                diagnostics=(diagnostic,),
            )
        )
    if manifest_path.suffix.lower() != ".json":
        diagnostic = _diagnostic(
            "OSPL_JSON_EXTENSION_REQUIRED",
            OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
            OptionalSolverPluginManifestDiagnosticCategory.IO,
            "Optional solver plugin manifests must be explicit JSON files.",
            default_source.reference,
            "",
            "Use a .json file.",
        )
        return _report_from_rejection(
            OptionalSolverRejectedManifest(
                stack_id="",
                source=default_source,
                schema_version="",
                diagnostics=(diagnostic,),
            )
        )
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        diagnostic = _diagnostic(
            "OSPL_JSON_READ_FAILED",
            OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
            OptionalSolverPluginManifestDiagnosticCategory.IO,
            f"Optional solver plugin manifest could not be read: {exc}",
            default_source.reference,
            "",
            "Check the explicit JSON file path.",
        )
        return _report_from_rejection(
            OptionalSolverRejectedManifest(
                stack_id="",
                source=default_source,
                schema_version="",
                diagnostics=(diagnostic,),
            )
        )
    except json.JSONDecodeError as exc:
        diagnostic = _diagnostic(
            "OSPL_JSON_INVALID",
            OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
            OptionalSolverPluginManifestDiagnosticCategory.IO,
            f"Optional solver plugin manifest JSON is invalid: {exc.msg}",
            default_source.reference,
            "",
            "Provide valid JSON.",
        )
        return _report_from_rejection(
            OptionalSolverRejectedManifest(
                stack_id="",
                source=default_source,
                schema_version="",
                diagnostics=(diagnostic,),
            )
        )
    if not isinstance(payload, Mapping):
        diagnostic = _diagnostic(
            "OSPL_JSON_OBJECT_REQUIRED",
            OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
            OptionalSolverPluginManifestDiagnosticCategory.IO,
            "Optional solver plugin manifest JSON must contain an object.",
            default_source.reference,
            "",
            "Use a JSON object containing manifest data.",
        )
        return _report_from_rejection(
            OptionalSolverRejectedManifest(
                stack_id="",
                source=default_source,
                schema_version="",
                diagnostics=(diagnostic,),
            )
        )
    return load_optional_solver_plugin_manifest_documents(
        (payload,),
        source=default_source,
        options=options,
    )


def load_optional_solver_plugin_manifest_documents(
    documents: Sequence[Mapping[str, Any] | OptionalSolverPluginManifestDocument],
    *,
    source: OptionalSolverManifestSource | None = None,
    options: OptionalSolverPluginManifestLoaderOptions | None = None,
) -> OptionalSolverPluginManifestLoadReport:
    """Load explicit plugin manifest documents without side effects."""

    loader_options = options or OptionalSolverPluginManifestLoaderOptions()
    provisional: list[OptionalSolverLoadedManifest] = []
    rejected: list[OptionalSolverRejectedManifest] = []
    diagnostics: list[OptionalSolverPluginManifestLoadDiagnostic] = []
    for document_data in documents:
        document = _coerce_document(document_data, source=source)
        result = _load_document(document, loader_options)
        diagnostics.extend(result.diagnostics)
        provisional.extend(result.accepted_manifests)
        rejected.extend(result.rejected_manifests)

    accepted, conflict_rejected, conflicts, conflict_diagnostics = _apply_conflicts(
        provisional,
        loader_options,
    )
    rejected.extend(conflict_rejected)
    diagnostics.extend(conflict_diagnostics)
    return OptionalSolverPluginManifestLoadReport(
        accepted_manifests=tuple(accepted),
        rejected_manifests=tuple(rejected),
        conflicts=tuple(conflicts),
        diagnostics=tuple(diagnostics),
    )


def explain_optional_solver_plugin_manifest_load_report(
    report: OptionalSolverPluginManifestLoadReport,
) -> str:
    """Return a short human-readable plugin manifest load summary."""

    return (
        "Optional solver plugin manifest loader accepted "
        f"{len(report.accepted_manifests)} manifest(s), rejected "
        f"{len(report.rejected_manifests)} manifest(s), and detected "
        f"{len(report.conflicts)} conflict(s). Manifest loading is data-only: "
        "it does not execute plugin code, scan directories, fetch network "
        "manifests, run discovery, execute solvers, or provide validation "
        "evidence."
    )


def _load_document(
    document: OptionalSolverPluginManifestDocument,
    options: OptionalSolverPluginManifestLoaderOptions,
) -> OptionalSolverPluginManifestLoadReport:
    diagnostics = list(_document_metadata_diagnostics(document, options))
    stack_id = str(document.manifest_data.get("stack_id", ""))
    if not any(item.is_blocking for item in diagnostics):
        diagnostics.extend(_safety_policy_diagnostics(document))
    validation_report = validate_optional_solver_manifest(document.manifest_data)
    diagnostics.extend(_validation_diagnostics(validation_report, document))

    try:
        manifest = parse_optional_solver_manifest_dict(document.manifest_data)
    except Exception as exc:  # noqa: BLE001 - parsed into loader diagnostics.
        diagnostic = _diagnostic(
            "OSPL_MANIFEST_PARSE_FAILED",
            OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
            OptionalSolverPluginManifestDiagnosticCategory.SCHEMA,
            f"Optional solver manifest could not be parsed: {exc}",
            document.source.reference,
            stack_id,
            "Provide manifest data matching the optional solver manifest schema.",
        )
        diagnostics.append(diagnostic)
        return _report_from_rejection(
            OptionalSolverRejectedManifest(
                stack_id=stack_id,
                source=_invalid_source(document.source),
                schema_version=document.schema_version,
                diagnostics=tuple(diagnostics),
                manifest_data=document.manifest_data,
            ),
            diagnostics=tuple(diagnostics),
        )

    if any(item.is_blocking for item in diagnostics):
        return _report_from_rejection(
            OptionalSolverRejectedManifest(
                stack_id=manifest.stack_id,
                source=_invalid_source(document.source),
                schema_version=document.schema_version,
                diagnostics=tuple(diagnostics),
                manifest_data=document.manifest_data,
            ),
            diagnostics=tuple(diagnostics),
        )

    loaded = OptionalSolverLoadedManifest(
        manifest=manifest,
        source=_normalized_source(document.source),
        schema_version=document.schema_version,
        validation_report=validation_report,
        diagnostics=tuple(diagnostics),
    )
    return OptionalSolverPluginManifestLoadReport(
        accepted_manifests=(loaded,),
        diagnostics=tuple(diagnostics),
    )


def _coerce_document(
    data: Mapping[str, Any] | OptionalSolverPluginManifestDocument,
    *,
    source: OptionalSolverManifestSource | None,
) -> OptionalSolverPluginManifestDocument:
    if isinstance(data, OptionalSolverPluginManifestDocument):
        return data
    if "manifest" in data or "schema_version" in data or "source" in data:
        source_value = data.get("source")
        source_obj = None
        if isinstance(source_value, Mapping):
            try:
                source_obj = OptionalSolverManifestSource.from_dict(source_value)
            except Exception:  # noqa: BLE001 - source diagnostics handle invalid shape.
                source_obj = _default_source(OptionalSolverManifestSourceType.EXPLICIT_DICT)
        if source_obj is None:
            source_obj = source
        if source_obj is None:
            source_obj = _default_source(OptionalSolverManifestSourceType.EXPLICIT_DICT)
        manifest_data = data.get("manifest")
        if not isinstance(manifest_data, Mapping):
            manifest_data = {}
        return OptionalSolverPluginManifestDocument(
            manifest_data=manifest_data,
            source=source_obj,
            schema_version=str(data.get("schema_version") or ""),
            document_ref=str(data.get("document_ref") or source_obj.reference),
        )
    source_obj = source or _default_source(OptionalSolverManifestSourceType.EXPLICIT_DICT)
    return OptionalSolverPluginManifestDocument(
        manifest_data=data,
        source=source_obj,
        schema_version="1",
        document_ref=source_obj.reference,
    )


def _document_metadata_diagnostics(
    document: OptionalSolverPluginManifestDocument,
    options: OptionalSolverPluginManifestLoaderOptions,
) -> tuple[OptionalSolverPluginManifestLoadDiagnostic, ...]:
    diagnostics: list[OptionalSolverPluginManifestLoadDiagnostic] = []
    stack_id = str(document.manifest_data.get("stack_id", ""))
    if not document.schema_version:
        diagnostics.append(
            _diagnostic(
                "OSPL_SCHEMA_VERSION_MISSING",
                OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
                OptionalSolverPluginManifestDiagnosticCategory.SCHEMA,
                "Plugin manifest documents require schema_version metadata.",
                document.source.reference,
                stack_id,
                "Set schema_version to a supported version such as 1.",
            )
        )
    elif document.schema_version not in options.supported_schema_versions:
        diagnostics.append(
            _diagnostic(
                "OSPL_SCHEMA_VERSION_UNSUPPORTED",
                OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
                OptionalSolverPluginManifestDiagnosticCategory.SCHEMA,
                f"Unsupported plugin manifest schema version: {document.schema_version}",
                document.source.reference,
                stack_id,
                "Use a supported schema version.",
            )
        )

    if _source_metadata_required(document.source) and (
        not document.source.label or not document.source.reference
    ):
        diagnostics.append(
            _diagnostic(
                "OSPL_SOURCE_METADATA_INCOMPLETE",
                OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
                OptionalSolverPluginManifestDiagnosticCategory.SOURCE,
                "Project, user, plugin, and organization manifests require source metadata.",
                document.source.reference,
                stack_id,
                "Provide source label and reference metadata.",
            )
        )
    expected = _default_trust_label(document.source.source_type)
    if document.source.trust_label != expected:
        diagnostics.append(
            _diagnostic(
                "OSPL_TRUST_LABEL_NORMALIZED",
                OptionalSolverPluginManifestDiagnosticSeverity.WARNING,
                OptionalSolverPluginManifestDiagnosticCategory.TRUST,
                "Manifest trust label does not match its source type and will be normalized.",
                document.source.reference,
                stack_id,
                f"Use trust label {expected.value} for this source type.",
            )
        )
    return tuple(diagnostics)


def _validation_diagnostics(
    report: OptionalSolverManifestValidationReport,
    document: OptionalSolverPluginManifestDocument,
) -> tuple[OptionalSolverPluginManifestLoadDiagnostic, ...]:
    diagnostics: list[OptionalSolverPluginManifestLoadDiagnostic] = []
    for item in report.diagnostics:
        diagnostics.append(
            _diagnostic(
                f"OSPL_{item.code}",
                OptionalSolverPluginManifestDiagnosticSeverity.from_manifest(
                    item.severity
                ),
                OptionalSolverPluginManifestDiagnosticCategory.SCHEMA,
                item.message,
                document.source.reference,
                report.stack_id,
                item.suggested_fix,
            )
        )
    return tuple(diagnostics)


def _safety_policy_diagnostics(
    document: OptionalSolverPluginManifestDocument,
) -> tuple[OptionalSolverPluginManifestLoadDiagnostic, ...]:
    strings = tuple(_walk_strings(document.manifest_data))
    joined = "\n".join(strings).lower()
    stack_id = str(document.manifest_data.get("stack_id", ""))
    diagnostics: list[OptionalSolverPluginManifestLoadDiagnostic] = []
    if _contains_installer_wording(joined):
        diagnostics.append(
            _diagnostic(
                "OSPL_INSTALLER_COMMAND_PRESENT",
                OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
                OptionalSolverPluginManifestDiagnosticCategory.SAFETY,
                "Manifest text contains installer or downloader command wording.",
                document.source.reference,
                stack_id,
                "Remove installer and downloader commands from manifest metadata.",
            )
        )
    if _contains_executable_code_reference(joined):
        diagnostics.append(
            _diagnostic(
                "OSPL_EXECUTABLE_CODE_REFERENCE_PRESENT",
                OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
                OptionalSolverPluginManifestDiagnosticCategory.SAFETY,
                "Manifest text references executable plugin code.",
                document.source.reference,
                stack_id,
                "Keep manifests declarative and move executable code to explicit plugin gates.",
            )
        )
    if _contains_bundled_solver_claim(joined):
        diagnostics.append(
            _diagnostic(
                "OSPL_BUNDLED_SOLVER_CLAIM",
                OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
                OptionalSolverPluginManifestDiagnosticCategory.SAFETY,
                "Manifest text claims a solver is bundled.",
                document.source.reference,
                stack_id,
                "State that external solvers are not bundled.",
            )
        )
    if _contains_certification_claim(joined):
        diagnostics.append(
            _diagnostic(
                "OSPL_CERTIFICATION_CLAIM",
                OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
                OptionalSolverPluginManifestDiagnosticCategory.SAFETY,
                "Manifest text contains a certification or production-readiness claim.",
                document.source.reference,
                stack_id,
                "Remove certification and production-readiness claims.",
            )
        )
    return tuple(diagnostics)


def _apply_conflicts(
    manifests: Sequence[OptionalSolverLoadedManifest],
    options: OptionalSolverPluginManifestLoaderOptions,
) -> tuple[
    list[OptionalSolverLoadedManifest],
    list[OptionalSolverRejectedManifest],
    list[OptionalSolverManifestConflict],
    list[OptionalSolverPluginManifestLoadDiagnostic],
]:
    accepted: list[OptionalSolverLoadedManifest] = []
    rejected: list[OptionalSolverRejectedManifest] = []
    conflicts: list[OptionalSolverManifestConflict] = []
    diagnostics: list[OptionalSolverPluginManifestLoadDiagnostic] = []
    by_stack: dict[str, OptionalSolverLoadedManifest] = {}

    for loaded in manifests:
        existing = by_stack.get(loaded.stack_id)
        if (
            options.reject_builtin_overrides
            and loaded.stack_id in options.builtin_stack_ids
            and loaded.source.source_type != OptionalSolverManifestSourceType.BUILTIN
        ):
            builtin_source = _default_source(
                OptionalSolverManifestSourceType.BUILTIN,
                reference=f"builtin:{loaded.stack_id}",
            )
            diagnostic = _conflict_diagnostic(
                "OSPL_BUILTIN_OVERRIDE_FORBIDDEN",
                (
                    "Built-in stack manifests win by default; plugin/user/project "
                    "overrides are forbidden."
                ),
                builtin_source,
                loaded,
            )
            conflict = OptionalSolverManifestConflict(
                stack_id=loaded.stack_id,
                winning_source=builtin_source,
                rejected_source=loaded.source,
                message=diagnostic.message,
            )
            conflicts.append(conflict)
            diagnostics.append(diagnostic)
            rejected.append(_reject_loaded(loaded, diagnostic))
            continue
        if existing is not None:
            winner = _choose_winner(existing, loaded)
            loser = loaded if winner is existing else existing
            diagnostic = _conflict_diagnostic(
                "OSPL_DUPLICATE_STACK_ID",
                "Duplicate optional solver stack id was rejected.",
                winner.source,
                loser,
            )
            conflict = OptionalSolverManifestConflict(
                stack_id=loser.stack_id,
                winning_source=winner.source,
                rejected_source=loser.source,
                message=diagnostic.message,
            )
            conflicts.append(conflict)
            diagnostics.append(diagnostic)
            rejected.append(_reject_loaded(loser, diagnostic))
            if winner is loaded:
                accepted.remove(existing)
                accepted.append(loaded)
                by_stack[loaded.stack_id] = loaded
            continue
        accepted.append(loaded)
        by_stack[loaded.stack_id] = loaded
    return accepted, rejected, conflicts, diagnostics


def _reject_loaded(
    loaded: OptionalSolverLoadedManifest,
    diagnostic: OptionalSolverPluginManifestLoadDiagnostic,
) -> OptionalSolverRejectedManifest:
    return OptionalSolverRejectedManifest(
        stack_id=loaded.stack_id,
        source=_invalid_source(loaded.source),
        schema_version=loaded.schema_version,
        diagnostics=loaded.diagnostics + (diagnostic,),
        manifest_data=loaded.manifest.to_dict(),
    )


def _choose_winner(
    left: OptionalSolverLoadedManifest,
    right: OptionalSolverLoadedManifest,
) -> OptionalSolverLoadedManifest:
    if left.source.source_type == OptionalSolverManifestSourceType.BUILTIN:
        return left
    if right.source.source_type == OptionalSolverManifestSourceType.BUILTIN:
        return right
    return left


def _conflict_diagnostic(
    code: str,
    message: str,
    winning_source: OptionalSolverManifestSource,
    rejected: OptionalSolverLoadedManifest,
) -> OptionalSolverPluginManifestLoadDiagnostic:
    return _diagnostic(
        code,
        OptionalSolverPluginManifestDiagnosticSeverity.BLOCKER,
        OptionalSolverPluginManifestDiagnosticCategory.CONFLICT,
        message,
        rejected.source.reference,
        rejected.stack_id,
        (
            "Use a unique stack id or remove the conflicting manifest. "
            f"Winner: {winning_source.reference}"
        ),
    )


def _default_source(
    source_type: OptionalSolverManifestSourceType,
    *,
    reference: str = "",
) -> OptionalSolverManifestSource:
    return OptionalSolverManifestSource(
        source_type=source_type,
        trust_label=_default_trust_label(source_type),
        label=source_type.value,
        reference=reference,
    )


def _normalized_source(
    source: OptionalSolverManifestSource,
) -> OptionalSolverManifestSource:
    return OptionalSolverManifestSource(
        source_type=source.source_type,
        trust_label=_default_trust_label(source.source_type),
        label=source.label,
        reference=source.reference,
    )


def _invalid_source(
    source: OptionalSolverManifestSource,
) -> OptionalSolverManifestSource:
    return OptionalSolverManifestSource(
        source_type=source.source_type,
        trust_label=OptionalSolverManifestTrustLabel.INVALID,
        label=source.label,
        reference=source.reference,
    )


def _default_trust_label(
    source_type: OptionalSolverManifestSourceType,
) -> OptionalSolverManifestTrustLabel:
    return {
        OptionalSolverManifestSourceType.BUILTIN: (
            OptionalSolverManifestTrustLabel.TRUSTED_BUILTIN
        ),
        OptionalSolverManifestSourceType.PROJECT_LOCAL: (
            OptionalSolverManifestTrustLabel.REVIEWED_PROJECT
        ),
        OptionalSolverManifestSourceType.USER_LOCAL: (
            OptionalSolverManifestTrustLabel.USER_PROVIDED
        ),
        OptionalSolverManifestSourceType.PLUGIN_PACKAGE: (
            OptionalSolverManifestTrustLabel.THIRD_PARTY_PLUGIN
        ),
        OptionalSolverManifestSourceType.ORGANIZATION_MANAGED: (
            OptionalSolverManifestTrustLabel.ORGANIZATION_MANAGED
        ),
        OptionalSolverManifestSourceType.EXPLICIT_FILE: (
            OptionalSolverManifestTrustLabel.USER_PROVIDED
        ),
        OptionalSolverManifestSourceType.EXPLICIT_DICT: (
            OptionalSolverManifestTrustLabel.USER_PROVIDED
        ),
    }[source_type]


def _source_metadata_required(source: OptionalSolverManifestSource) -> bool:
    return source.source_type in {
        OptionalSolverManifestSourceType.PROJECT_LOCAL,
        OptionalSolverManifestSourceType.USER_LOCAL,
        OptionalSolverManifestSourceType.PLUGIN_PACKAGE,
        OptionalSolverManifestSourceType.ORGANIZATION_MANAGED,
    }


def _walk_strings(value: object) -> tuple[str, ...]:
    strings: list[str] = []
    if isinstance(value, str):
        strings.append(value)
    elif isinstance(value, Mapping):
        for nested in value.values():
            strings.extend(_walk_strings(nested))
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        for nested in value:
            strings.extend(_walk_strings(nested))
    return tuple(strings)


def _contains_installer_wording(text: str) -> bool:
    return any(
        phrase in text
        for phrase in (
            "pip install",
            "conda install",
            "apt install",
            "apt-get install",
            "choco install",
            "winget install",
            "brew install",
            "curl ",
            "wget ",
        )
    )


def _contains_executable_code_reference(text: str) -> bool:
    return any(
        phrase in text
        for phrase in (
            "entry_point",
            "__import__",
            "eval(",
            "exec(",
            "python -c",
            "os.system",
            "sub" + "process",
            "plugin code",
        )
    )


def _contains_bundled_solver_claim(text: str) -> bool:
    return any(
        phrase in text
        for phrase in (
            "solvers are bundled",
            "solver is bundled",
            "bundles solver",
            "bundled solver binaries",
            "ships solver",
            "includes solver binary",
        )
    )


def _contains_certification_claim(text: str) -> bool:
    return any(
        phrase in text
        for phrase in (
            "certifi" + "ed for production",
            "industrial " + "certification provided",
            "certification " + "is provided",
            "validated" + " for production",
            "production-ready validated",
        )
    )


def _diagnostic(
    code: str,
    severity: OptionalSolverPluginManifestDiagnosticSeverity,
    category: OptionalSolverPluginManifestDiagnosticCategory,
    message: str,
    source_ref: str,
    stack_id: str,
    suggested_fix: str,
) -> OptionalSolverPluginManifestLoadDiagnostic:
    return OptionalSolverPluginManifestLoadDiagnostic(
        code=code,
        severity=severity,
        category=category,
        message=message,
        source_ref=source_ref,
        stack_id=stack_id,
        suggested_fix=suggested_fix,
    )


def _report_from_rejection(
    rejected: OptionalSolverRejectedManifest,
    *,
    diagnostics: tuple[OptionalSolverPluginManifestLoadDiagnostic, ...] | None = None,
) -> OptionalSolverPluginManifestLoadReport:
    return OptionalSolverPluginManifestLoadReport(
        rejected_manifests=(rejected,),
        diagnostics=diagnostics if diagnostics is not None else rejected.diagnostics,
    )
