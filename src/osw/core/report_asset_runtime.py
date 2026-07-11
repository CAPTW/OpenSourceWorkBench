"""Immutable runtime contracts for report screenshot path intent.

This module performs lexical classification and pure candidate construction
only. It does not inspect a filesystem, contact a network location, open image
content, persist runtime state, or mutate a durable report asset.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath
from unicodedata import category

from osw.core.report_asset import (
    ReportAssetPathKind,
    coerce_report_asset_path_kind,
    validate_report_asset_path,
)

_SUPPORTED_RASTER_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})
_URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")
_WINDOWS_DRIVE_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
_WINDOWS_RESERVED_NAMES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{number}" for number in range(1, 10)),
        *(f"LPT{number}" for number in range(1, 10)),
    }
)
_GENERIC_SAFE_BASENAME = "screenshot"


class PathFlavor(StrEnum):
    """Lexical path syntax, independent of the host platform."""

    WINDOWS = "windows"
    POSIX = "posix"
    UNKNOWN = "unknown"


class ReportAssetPortability(StrEnum):
    """Portable meaning established without external access."""

    LEGACY_OR_UNKNOWN = "legacy_or_unknown"
    PROJECT_RELATIVE_PORTABLE = "project_relative_portable"
    EXTERNAL_LOCAL_ABSOLUTE = "external_local_absolute"
    NETWORK_LIKE = "network_like"
    DEVICE_BLOCKED = "device_blocked"
    UNSUPPORTED_OR_FOREIGN = "unsupported_or_foreign"


class ReportAssetLocation(StrEnum):
    """Lexical location class, never an existence or reachability claim."""

    UNRESOLVED = "unresolved"
    LOCAL_PROJECT = "local_project"
    LOCAL_EXTERNAL = "local_external"
    NETWORK_LIKE = "network_like"
    DEVICE = "device"
    FOREIGN = "foreign"


class ConsentState(StrEnum):
    """Runtime-only consent state carried by an immutable context snapshot."""

    NOT_APPLICABLE = "not_applicable"
    REQUIRED = "required"
    GRANTED_FOR_ACTION = "granted_for_action"
    DENIED = "denied"
    STALE = "stale"


class LexicalContainment(StrEnum):
    """Informative lexical relationship; it is not a security boundary."""

    UNKNOWN = "unknown"
    WITHIN_ROOT = "within_root"


class CanonicalContainment(StrEnum):
    """Filesystem-backed containment state unavailable to this pure module."""

    UNKNOWN = "unknown"


class ReportAssetResolutionStatus(StrEnum):
    """Stable runtime resolution vocabulary shared by later layers."""

    LEGACY_NOT_RESOLVED = "legacy_not_resolved"
    ROOT_UNAVAILABLE = "root_unavailable"
    CANDIDATE_READY = "candidate_ready"
    CONSENT_REQUIRED = "consent_required"
    NETWORK_CONSENT_REQUIRED = "network_consent_required"
    RESOLVED_LOCAL = "resolved_local"
    RESOLVED_NETWORK = "resolved_network"
    MISSING = "missing"
    NOT_REGULAR_FILE = "not_regular_file"
    UNSUPPORTED_SUFFIX = "unsupported_suffix"
    PERMISSION_DENIED = "permission_denied"
    OUTSIDE_PROJECT_ROOT = "outside_project_root"
    SYMLINK_OR_JUNCTION_ESCAPE = "symlink_or_junction_escape"
    DEVICE_PATH_BLOCKED = "device_path_blocked"
    STALE_CONTEXT = "stale_context"
    STALE_REQUEST = "stale_request"
    FILESYSTEM_ERROR = "filesystem_error"
    UNSUPPORTED_KIND = "unsupported_kind"
    UNRESOLVED_NO_RESOLVER = "unresolved_no_resolver"
    INVALID_INTENT = "invalid_intent"
    UNSUPPORTED_PATH_FLAVOR = "unsupported_path_flavor"
    UNSAFE_PATH_COMPONENT = "unsafe_path_component"


class ReportAssetResolutionPhase(StrEnum):
    REQUEST = "request"
    COMPATIBILITY = "compatibility"
    CANDIDATE = "candidate"
    CONSENT = "consent"
    FILESYSTEM = "filesystem"
    LEXICAL = "lexical"
    ORCHESTRATION = "orchestration"
    COMPATIBILITY_BRIDGE = "compatibility_bridge"


class ReportAssetResolutionSeverity(StrEnum):
    INFO = "info"
    ACTION_REQUIRED = "action_required"
    WARNING = "warning"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class ReportAssetStatusMetadata:
    phase: ReportAssetResolutionPhase
    severity: ReportAssetResolutionSeverity
    retryable: bool
    message: str


_STATUS_METADATA: tuple[
    tuple[ReportAssetResolutionStatus, ReportAssetStatusMetadata], ...
] = (
    (
        ReportAssetResolutionStatus.INVALID_INTENT,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.REQUEST,
            ReportAssetResolutionSeverity.BLOCKED,
            True,
            "Screenshot reference is invalid.",
        ),
    ),
    (
        ReportAssetResolutionStatus.LEGACY_NOT_RESOLVED,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.COMPATIBILITY,
            ReportAssetResolutionSeverity.INFO,
            False,
            "Legacy reference is preserved; availability was not checked.",
        ),
    ),
    (
        ReportAssetResolutionStatus.ROOT_UNAVAILABLE,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.CANDIDATE,
            ReportAssetResolutionSeverity.ACTION_REQUIRED,
            True,
            "Project-relative screenshot needs an absolute project location.",
        ),
    ),
    (
        ReportAssetResolutionStatus.CANDIDATE_READY,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.CANDIDATE,
            ReportAssetResolutionSeverity.INFO,
            True,
            "Screenshot reference is ready to check.",
        ),
    ),
    (
        ReportAssetResolutionStatus.CONSENT_REQUIRED,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.CONSENT,
            ReportAssetResolutionSeverity.ACTION_REQUIRED,
            True,
            "Approval is required for this external location.",
        ),
    ),
    (
        ReportAssetResolutionStatus.NETWORK_CONSENT_REQUIRED,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.CONSENT,
            ReportAssetResolutionSeverity.ACTION_REQUIRED,
            True,
            "Network access approval is required for this action.",
        ),
    ),
    (
        ReportAssetResolutionStatus.RESOLVED_LOCAL,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.FILESYSTEM,
            ReportAssetResolutionSeverity.INFO,
            True,
            "Screenshot is available locally.",
        ),
    ),
    (
        ReportAssetResolutionStatus.RESOLVED_NETWORK,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.FILESYSTEM,
            ReportAssetResolutionSeverity.INFO,
            True,
            "Screenshot is available at the approved network location.",
        ),
    ),
    (
        ReportAssetResolutionStatus.MISSING,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.FILESYSTEM,
            ReportAssetResolutionSeverity.WARNING,
            True,
            "Screenshot was not found.",
        ),
    ),
    (
        ReportAssetResolutionStatus.NOT_REGULAR_FILE,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.FILESYSTEM,
            ReportAssetResolutionSeverity.BLOCKED,
            True,
            "Screenshot reference is not a regular file.",
        ),
    ),
    (
        ReportAssetResolutionStatus.UNSUPPORTED_SUFFIX,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.LEXICAL,
            ReportAssetResolutionSeverity.BLOCKED,
            True,
            "Screenshot format is not supported.",
        ),
    ),
    (
        ReportAssetResolutionStatus.PERMISSION_DENIED,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.FILESYSTEM,
            ReportAssetResolutionSeverity.WARNING,
            True,
            "Access was denied while checking the screenshot.",
        ),
    ),
    (
        ReportAssetResolutionStatus.OUTSIDE_PROJECT_ROOT,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.FILESYSTEM,
            ReportAssetResolutionSeverity.BLOCKED,
            True,
            "Project-relative screenshot is outside the current project folder.",
        ),
    ),
    (
        ReportAssetResolutionStatus.SYMLINK_OR_JUNCTION_ESCAPE,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.FILESYSTEM,
            ReportAssetResolutionSeverity.BLOCKED,
            True,
            "A link or junction leaves the current project folder.",
        ),
    ),
    (
        ReportAssetResolutionStatus.DEVICE_PATH_BLOCKED,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.LEXICAL,
            ReportAssetResolutionSeverity.BLOCKED,
            False,
            "Device paths are blocked.",
        ),
    ),
    (
        ReportAssetResolutionStatus.UNSAFE_PATH_COMPONENT,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.LEXICAL,
            ReportAssetResolutionSeverity.BLOCKED,
            True,
            "Screenshot path contains an unsafe component.",
        ),
    ),
    (
        ReportAssetResolutionStatus.UNSUPPORTED_PATH_FLAVOR,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.LEXICAL,
            ReportAssetResolutionSeverity.BLOCKED,
            True,
            "Screenshot path uses an unsupported platform flavor.",
        ),
    ),
    (
        ReportAssetResolutionStatus.STALE_CONTEXT,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.ORCHESTRATION,
            ReportAssetResolutionSeverity.INFO,
            True,
            "Project location changed; check again.",
        ),
    ),
    (
        ReportAssetResolutionStatus.STALE_REQUEST,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.ORCHESTRATION,
            ReportAssetResolutionSeverity.INFO,
            True,
            "Screenshot request changed; check again.",
        ),
    ),
    (
        ReportAssetResolutionStatus.FILESYSTEM_ERROR,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.FILESYSTEM,
            ReportAssetResolutionSeverity.WARNING,
            True,
            "Screenshot availability could not be checked.",
        ),
    ),
    (
        ReportAssetResolutionStatus.UNSUPPORTED_KIND,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.LEXICAL,
            ReportAssetResolutionSeverity.BLOCKED,
            False,
            "Screenshot reference kind is not supported.",
        ),
    ),
    (
        ReportAssetResolutionStatus.UNRESOLVED_NO_RESOLVER,
        ReportAssetStatusMetadata(
            ReportAssetResolutionPhase.COMPATIBILITY_BRIDGE,
            ReportAssetResolutionSeverity.WARNING,
            True,
            "Screenshot availability has not been checked.",
        ),
    ),
)


def status_metadata(status: ReportAssetResolutionStatus) -> ReportAssetStatusMetadata:
    """Return immutable, path-free presentation metadata for ``status``."""
    if not isinstance(status, ReportAssetResolutionStatus):
        raise TypeError("status must be a ReportAssetResolutionStatus")
    for candidate, metadata in _STATUS_METADATA:
        if candidate is status:
            return metadata
    raise AssertionError("Missing report asset status metadata")


@dataclass(frozen=True, slots=True)
class ReportAssetRuntimeIntent:
    """Strict runtime input preserving exact durable text and kind declaration."""

    asset_id: str
    stored_path: str = field(repr=False)
    declared_kind: ReportAssetPathKind | str | None

    def __post_init__(self) -> None:
        _require_string(self.asset_id, "asset_id")
        _require_string(self.stored_path, "stored_path")
        if self.declared_kind is not None and not isinstance(
            self.declared_kind, (ReportAssetPathKind, str)
        ):
            raise TypeError(
                "declared_kind must be a ReportAssetPathKind, string, or None"
            )


@dataclass(frozen=True, slots=True)
class ReportAssetResolutionContext:
    """Neutral, immutable snapshot used only for pure candidate construction."""

    project_root: str | None = field(repr=False)
    project_root_flavor: PathFlavor
    context_generation: int
    document_token: str = field(repr=False)
    request_token: str = field(repr=False)
    purpose: str
    consent_state: ConsentState = ConsentState.NOT_APPLICABLE
    consent_token: str | None = field(default=None, repr=False)
    record_fingerprint: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        _require_optional_string(self.project_root, "project_root")
        if not isinstance(self.project_root_flavor, PathFlavor):
            raise TypeError("project_root_flavor must be a PathFlavor")
        if isinstance(self.context_generation, bool) or not isinstance(
            self.context_generation, int
        ):
            raise TypeError("context_generation must be an integer")
        if self.context_generation < 0:
            raise ValueError("context_generation must be non-negative")
        _require_string(self.document_token, "document_token")
        _require_string(self.request_token, "request_token")
        _require_string(self.purpose, "purpose")
        if not isinstance(self.consent_state, ConsentState):
            raise TypeError("consent_state must be a ConsentState")
        _require_optional_string(self.consent_token, "consent_token")
        _require_string(self.record_fingerprint, "record_fingerprint")


@dataclass(frozen=True, slots=True)
class ReportAssetResolutionDescriptor:
    """Runtime-only descriptor; private locators are never generally serialized."""

    asset_id: str
    declared_kind: ReportAssetPathKind | str | None
    path_flavor: PathFlavor
    portability: ReportAssetPortability
    location: ReportAssetLocation
    status: ReportAssetResolutionStatus
    diagnostic_codes: tuple[str, ...]
    diagnostic_messages: tuple[str, ...]
    context_generation: int
    document_token: str = field(repr=False)
    request_token: str = field(repr=False)
    purpose: str
    consent_state: ConsentState
    consent_token: str | None = field(repr=False)
    record_fingerprint: str = field(repr=False)
    stored_path: str | None = field(repr=False)
    project_root: str | None = field(repr=False)
    lexical_candidate: str | None = field(repr=False)
    effective_path: str | None = field(repr=False)
    lexical_containment: LexicalContainment
    canonical_containment: CanonicalContainment
    caveats: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReportAssetSafeView:
    """Path-free projection safe for ordinary presentation and report metadata."""

    asset_id: str
    safe_basename: str
    declared_kind: str
    status: ReportAssetResolutionStatus
    phase: ReportAssetResolutionPhase
    severity: ReportAssetResolutionSeverity
    retryable: bool
    diagnostic_codes: tuple[str, ...]
    diagnostic_messages: tuple[str, ...]
    portability: ReportAssetPortability
    location: ReportAssetLocation
    caveats: tuple[str, ...]

    def to_mapping(self) -> dict[str, object]:
        """Return a one-way, JSON-shaped mapping containing no private locator."""
        return {
            "asset_id": self.asset_id,
            "safe_basename": self.safe_basename,
            "declared_kind": self.declared_kind,
            "status": self.status.value,
            "phase": self.phase.value,
            "severity": self.severity.value,
            "retryable": self.retryable,
            "diagnostic_codes": list(self.diagnostic_codes),
            "diagnostic_messages": list(self.diagnostic_messages),
            "portability": self.portability.value,
            "location": self.location.value,
            "caveats": list(self.caveats),
        }


def evaluate_report_asset_runtime(
    intent: ReportAssetRuntimeIntent,
    context: ReportAssetResolutionContext,
) -> ReportAssetResolutionDescriptor:
    """Evaluate durable intent and construct a lexical candidate without I/O."""
    if not isinstance(intent, ReportAssetRuntimeIntent):
        raise TypeError("intent must be a ReportAssetRuntimeIntent")
    if not isinstance(context, ReportAssetResolutionContext):
        raise TypeError("context must be a ReportAssetResolutionContext")

    kind = _coerce_kind_for_evaluation(intent.declared_kind)
    if kind is None and intent.declared_kind is not None:
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.UNSUPPORTED_KIND,
            portability=ReportAssetPortability.UNSUPPORTED_OR_FOREIGN,
        )
    if kind is ReportAssetPathKind.MANAGED_PROJECT_ASSET:
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.UNSUPPORTED_KIND,
            portability=ReportAssetPortability.UNSUPPORTED_OR_FOREIGN,
        )
    if kind is None or kind is ReportAssetPathKind.LEGACY_RAW:
        if kind is not None:
            try:
                validate_report_asset_path(intent.stored_path, kind)
            except (TypeError, ValueError):
                return _descriptor(
                    intent,
                    context,
                    status=ReportAssetResolutionStatus.INVALID_INTENT,
                )
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.LEGACY_NOT_RESOLVED,
            caveats=("legacy_compatibility_preserved", "filesystem_not_checked"),
        )
    if kind is ReportAssetPathKind.EXTERNAL_ABSOLUTE:
        return _evaluate_external(intent, context, kind)
    if kind is ReportAssetPathKind.PROJECT_RELATIVE:
        return _evaluate_project_relative(intent, context, kind)
    return _descriptor(
        intent,
        context,
        status=ReportAssetResolutionStatus.UNSUPPORTED_KIND,
        portability=ReportAssetPortability.UNSUPPORTED_OR_FOREIGN,
    )


def report_asset_safe_view(
    descriptor: ReportAssetResolutionDescriptor,
) -> ReportAssetSafeView:
    """Project a private runtime descriptor into path-free presentation data."""
    if not isinstance(descriptor, ReportAssetResolutionDescriptor):
        raise TypeError("descriptor must be a ReportAssetResolutionDescriptor")
    metadata = status_metadata(descriptor.status)
    return ReportAssetSafeView(
        asset_id=descriptor.asset_id,
        safe_basename=_safe_basename(descriptor.stored_path or ""),
        declared_kind=_safe_kind_label(descriptor.declared_kind),
        status=descriptor.status,
        phase=metadata.phase,
        severity=metadata.severity,
        retryable=metadata.retryable,
        diagnostic_codes=descriptor.diagnostic_codes,
        diagnostic_messages=descriptor.diagnostic_messages,
        portability=descriptor.portability,
        location=descriptor.location,
        caveats=descriptor.caveats,
    )


def _evaluate_external(
    intent: ReportAssetRuntimeIntent,
    context: ReportAssetResolutionContext,
    kind: ReportAssetPathKind,
) -> ReportAssetResolutionDescriptor:
    stored = intent.stored_path
    if _is_windows_device_path(stored):
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.DEVICE_PATH_BLOCKED,
            portability=ReportAssetPortability.DEVICE_BLOCKED,
            location=ReportAssetLocation.DEVICE,
        )
    flavor = _external_path_flavor(stored)
    if _looks_like_uri(stored) or flavor is PathFlavor.UNKNOWN:
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.INVALID_INTENT,
            portability=ReportAssetPortability.UNSUPPORTED_OR_FOREIGN,
        )
    if _has_control_character(stored) or (
        flavor is PathFlavor.WINDOWS and _has_unsafe_windows_component(stored)
    ):
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.UNSAFE_PATH_COMPONENT,
            flavor=flavor,
            portability=ReportAssetPortability.UNSUPPORTED_OR_FOREIGN,
        )
    try:
        validate_report_asset_path(stored, kind)
    except (TypeError, ValueError):
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.INVALID_INTENT,
            flavor=flavor,
            portability=ReportAssetPortability.UNSUPPORTED_OR_FOREIGN,
        )
    network_like = _is_network_like(stored, flavor)
    portability = (
        ReportAssetPortability.NETWORK_LIKE
        if network_like
        else ReportAssetPortability.EXTERNAL_LOCAL_ABSOLUTE
    )
    location = (
        ReportAssetLocation.NETWORK_LIKE
        if network_like
        else ReportAssetLocation.LOCAL_EXTERNAL
    )
    if not _has_supported_suffix(stored):
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.UNSUPPORTED_SUFFIX,
            flavor=flavor,
            portability=portability,
            location=location,
        )
    status = (
        ReportAssetResolutionStatus.NETWORK_CONSENT_REQUIRED
        if network_like
        else ReportAssetResolutionStatus.CONSENT_REQUIRED
    )
    return _descriptor(
        intent,
        context,
        status=status,
        flavor=flavor,
        portability=portability,
        location=location,
        candidate=stored,
    )


def _evaluate_project_relative(
    intent: ReportAssetRuntimeIntent,
    context: ReportAssetResolutionContext,
    kind: ReportAssetPathKind,
) -> ReportAssetResolutionDescriptor:
    stored = intent.stored_path
    if _looks_like_uri(stored) or PurePosixPath(stored).is_absolute():
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.INVALID_INTENT,
            portability=ReportAssetPortability.UNSUPPORTED_OR_FOREIGN,
        )
    windows_form = PureWindowsPath(stored)
    if windows_form.drive or windows_form.root:
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.INVALID_INTENT,
            portability=ReportAssetPortability.UNSUPPORTED_OR_FOREIGN,
        )
    if _project_relative_has_unsafe_component(stored):
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.UNSAFE_PATH_COMPONENT,
            portability=ReportAssetPortability.PROJECT_RELATIVE_PORTABLE,
        )
    try:
        validate_report_asset_path(stored, kind)
    except (TypeError, ValueError):
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.INVALID_INTENT,
            portability=ReportAssetPortability.UNSUPPORTED_OR_FOREIGN,
        )
    if not _has_supported_suffix(stored):
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.UNSUPPORTED_SUFFIX,
            portability=ReportAssetPortability.PROJECT_RELATIVE_PORTABLE,
        )

    root = context.project_root
    flavor = context.project_root_flavor
    if root is None:
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.ROOT_UNAVAILABLE,
            portability=ReportAssetPortability.PROJECT_RELATIVE_PORTABLE,
        )
    if flavor is PathFlavor.UNKNOWN or _root_has_foreign_flavor(root, flavor):
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.UNSUPPORTED_PATH_FLAVOR,
            portability=ReportAssetPortability.UNSUPPORTED_OR_FOREIGN,
            location=ReportAssetLocation.FOREIGN,
            root=root,
        )
    if not _root_is_absolute(root, flavor):
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.ROOT_UNAVAILABLE,
            flavor=flavor,
            portability=ReportAssetPortability.PROJECT_RELATIVE_PORTABLE,
            root=root,
        )
    if flavor is PathFlavor.WINDOWS and _has_unsafe_windows_component(root):
        return _descriptor(
            intent,
            context,
            status=ReportAssetResolutionStatus.UNSAFE_PATH_COMPONENT,
            flavor=flavor,
            portability=ReportAssetPortability.UNSUPPORTED_OR_FOREIGN,
            root=root,
        )

    segments = stored.split("/")
    if flavor is PathFlavor.WINDOWS:
        candidate = str(PureWindowsPath(root).joinpath(*segments))
    else:
        candidate = str(PurePosixPath(root).joinpath(*segments))
    network_like = _is_network_like(root, flavor)
    return _descriptor(
        intent,
        context,
        status=ReportAssetResolutionStatus.CANDIDATE_READY,
        flavor=flavor,
        portability=ReportAssetPortability.PROJECT_RELATIVE_PORTABLE,
        location=(
            ReportAssetLocation.NETWORK_LIKE
            if network_like
            else ReportAssetLocation.LOCAL_PROJECT
        ),
        root=root,
        candidate=candidate,
        lexical_containment=LexicalContainment.WITHIN_ROOT,
    )


def _descriptor(
    intent: ReportAssetRuntimeIntent,
    context: ReportAssetResolutionContext,
    *,
    status: ReportAssetResolutionStatus,
    flavor: PathFlavor = PathFlavor.UNKNOWN,
    portability: ReportAssetPortability = ReportAssetPortability.LEGACY_OR_UNKNOWN,
    location: ReportAssetLocation = ReportAssetLocation.UNRESOLVED,
    root: str | None = None,
    candidate: str | None = None,
    lexical_containment: LexicalContainment = LexicalContainment.UNKNOWN,
    caveats: tuple[str, ...] = (
        "lexical_only",
        "filesystem_not_checked",
        "canonical_containment_unverified",
    ),
) -> ReportAssetResolutionDescriptor:
    metadata = status_metadata(status)
    return ReportAssetResolutionDescriptor(
        asset_id=intent.asset_id,
        declared_kind=intent.declared_kind,
        path_flavor=flavor,
        portability=portability,
        location=location,
        status=status,
        diagnostic_codes=(f"report_asset.{status.value}",),
        diagnostic_messages=(metadata.message,),
        context_generation=context.context_generation,
        document_token=context.document_token,
        request_token=context.request_token,
        purpose=context.purpose,
        consent_state=context.consent_state,
        consent_token=context.consent_token,
        record_fingerprint=context.record_fingerprint,
        stored_path=intent.stored_path,
        project_root=root,
        lexical_candidate=candidate,
        effective_path=None,
        lexical_containment=lexical_containment,
        canonical_containment=CanonicalContainment.UNKNOWN,
        caveats=caveats,
    )


def _coerce_kind_for_evaluation(
    value: ReportAssetPathKind | str | None,
) -> ReportAssetPathKind | None:
    if value is None:
        return None
    if value is ReportAssetPathKind.MANAGED_PROJECT_ASSET:
        return value
    try:
        return coerce_report_asset_path_kind(value)
    except (TypeError, ValueError):
        return None


def _external_path_flavor(value: str) -> PathFlavor:
    if value.startswith("\\\\") or _WINDOWS_DRIVE_ABSOLUTE.match(value):
        return PathFlavor.WINDOWS
    if value.startswith("/"):
        return PathFlavor.POSIX
    return PathFlavor.UNKNOWN


def _root_has_foreign_flavor(value: str, flavor: PathFlavor) -> bool:
    if flavor is PathFlavor.WINDOWS:
        return value.startswith("/") and not value.startswith("//")
    if flavor is PathFlavor.POSIX:
        return bool(_WINDOWS_DRIVE.match(value)) or "\\" in value
    return True


def _root_is_absolute(value: str, flavor: PathFlavor) -> bool:
    if flavor is PathFlavor.WINDOWS:
        return PureWindowsPath(value).is_absolute()
    if flavor is PathFlavor.POSIX:
        return PurePosixPath(value).is_absolute()
    return False


def _is_network_like(value: str, flavor: PathFlavor) -> bool:
    if flavor is PathFlavor.WINDOWS:
        return value.startswith(("\\\\", "//"))
    if flavor is PathFlavor.POSIX:
        return value.startswith("//")
    return False


def _is_windows_device_path(value: str) -> bool:
    windows_text = value.replace("/", "\\")
    return windows_text.startswith(("\\\\?\\", "\\\\.\\", "\\??\\", "\\\\??\\"))


def _looks_like_uri(value: str) -> bool:
    return bool(_URI_SCHEME.match(value)) and not bool(
        _WINDOWS_DRIVE_ABSOLUTE.match(value)
    )


def _project_relative_has_unsafe_component(value: str) -> bool:
    if _has_control_character(value) or "\\" in value:
        return True
    segments = value.split("/")
    return any(segment in {"", ".", ".."} for segment in segments) or any(
        _is_unsafe_windows_component(segment) for segment in segments
    )


def _has_unsafe_windows_component(value: str) -> bool:
    parts = PureWindowsPath(value).parts
    if parts and (PureWindowsPath(value).anchor == parts[0]):
        parts = parts[1:]
    return any(_is_unsafe_windows_component(part) for part in parts)


def _is_unsafe_windows_component(value: str) -> bool:
    if not value or value in {".", ".."} or _has_control_character(value):
        return True
    if value.endswith((" ", ".")) or any(character in '<>"|?*' for character in value):
        return True
    if ":" in value:
        return True
    stem = value.split(".", maxsplit=1)[0].rstrip(" .").upper()
    return stem in _WINDOWS_RESERVED_NAMES


def _has_supported_suffix(value: str) -> bool:
    basename = value.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    dot_index = basename.rfind(".")
    suffix = basename[dot_index:].lower() if dot_index >= 0 else ""
    return suffix in _SUPPORTED_RASTER_SUFFIXES


def _safe_basename(value: str) -> str:
    basename = value.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    if (
        not basename
        or basename in {".", ".."}
        or _has_control_character(basename)
        or _is_unsafe_windows_component(basename)
    ):
        return _GENERIC_SAFE_BASENAME
    return basename


def _safe_kind_label(value: ReportAssetPathKind | str | None) -> str:
    if value is None:
        return "omitted"
    if value is ReportAssetPathKind.MANAGED_PROJECT_ASSET:
        return value.value
    try:
        return coerce_report_asset_path_kind(value).value
    except (TypeError, ValueError):
        return "unsupported"


def _has_control_character(value: str) -> bool:
    return any(category(character) == "Cc" for character in value)


def _require_string(value: object, name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")


def _require_optional_string(value: object, name: str) -> None:
    if value is not None:
        _require_string(value, name)


__all__ = [
    "CanonicalContainment",
    "ConsentState",
    "LexicalContainment",
    "PathFlavor",
    "ReportAssetLocation",
    "ReportAssetPortability",
    "ReportAssetResolutionContext",
    "ReportAssetResolutionDescriptor",
    "ReportAssetResolutionPhase",
    "ReportAssetResolutionSeverity",
    "ReportAssetResolutionStatus",
    "ReportAssetRuntimeIntent",
    "ReportAssetSafeView",
    "ReportAssetStatusMetadata",
    "evaluate_report_asset_runtime",
    "report_asset_safe_view",
    "status_metadata",
]
