"""Local plugin folder and zip installer.

The installer validates OSW plugin manifests by reading manifest files only. It
does not import plugin modules or execute plugin entry points during install.
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import json
import shutil
import stat
import tempfile
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any

from .discovery import iter_manifest_paths
from .examples import builtin_plugin_manifests
from .health import check_manifest_health
from .manifest import PluginManifest, PluginManifestError
from .state import PluginStateStore

MAX_UNCOMPRESSED_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_FILE_COUNT = 200


class PluginInstallError(RuntimeError):
    """Raised when a local plugin cannot be installed safely."""


class DuplicatePluginInstallError(PluginInstallError):
    """Raised when an installed plugin already declares the same id."""


class ZipPathTraversalError(PluginInstallError):
    """Raised when a zip archive attempts to write outside the extraction root."""


class UnsafeArchiveError(PluginInstallError):
    """Raised when a zip archive exceeds limits or contains symlinks/dangerous items."""


class PluginSourceKind(StrEnum):
    LOCAL_FOLDER = "local_folder"
    LOCAL_ZIP = "local_zip"
    BUILTIN = "builtin"
    ENTRY_POINT = "entry_point"
    UNKNOWN = "unknown"


class PluginInstallStatus(StrEnum):
    VALID = "valid"
    INSTALLED = "installed"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"
    DUPLICATE = "duplicate"
    UNSAFE_ARCHIVE = "unsafe_archive"
    INVALID_MANIFEST = "invalid_manifest"
    MISSING_MANIFEST = "missing_manifest"
    ERROR = "error"


@dataclass
class PluginInstallRequest:
    source_path: str
    source_kind: str  # values from PluginSourceKind
    install_root: str | None = None
    allow_replace: bool = False
    enable_after_install: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "source_kind": self.source_kind,
            "install_root": self.install_root,
            "allow_replace": self.allow_replace,
            "enable_after_install": self.enable_after_install,
            "metadata": self.metadata,
        }


@dataclass
class PluginInstallReceipt:
    plugin_id: str
    name: str
    version: str
    source_kind: str
    source_path: str
    installed_path: str
    manifest_path: str
    sha256: str | None = None
    installed_at: str = ""
    status: str = "installed"
    diagnostics: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.installed_at:
            self.installed_at = datetime.datetime.now(datetime.UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "source_kind": self.source_kind,
            "source_path": self.source_path,
            "installed_path": self.installed_path,
            "manifest_path": self.manifest_path,
            "sha256": self.sha256,
            "installed_at": self.installed_at,
            "status": self.status,
            "diagnostics": self.diagnostics,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PluginInstallReceipt:
        return cls(
            plugin_id=data["plugin_id"],
            name=data["name"],
            version=data["version"],
            source_kind=data["source_kind"],
            source_path=data["source_path"],
            installed_path=data["installed_path"],
            manifest_path=data["manifest_path"],
            sha256=data.get("sha256"),
            installed_at=data.get("installed_at", ""),
            status=data.get("status", "installed"),
            diagnostics=data.get("diagnostics", []),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class PluginValidationResult:
    manifest: PluginManifest | None
    manifest_path: Path | None
    plugin_root: Path
    warnings: tuple[str, ...] = field(default_factory=tuple)
    error_message: str = ""

    @property
    def valid(self) -> bool:
        return self.manifest is not None and not self.error_message


@dataclass
class PluginInstallResult:
    # Status can be: valid, installed, rejected, quarantined, duplicate,
    # unsafe_archive, invalid_manifest, missing_manifest, error
    status: str
    receipt: PluginInstallReceipt | None = None
    manifest: PluginManifest | None = None
    diagnostics: list[str] = field(default_factory=list)
    source_path: Path = field(default_factory=Path)
    installed_path: Path | None = None
    quarantine_path: Path | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def plugin_id(self) -> str:
        if self.manifest:
            return self.manifest.id
        if self.receipt:
            return self.receipt.plugin_id
        return ""

    @property
    def manifest_path(self) -> Path:
        if self.receipt:
            return Path(self.receipt.manifest_path)
        if self.installed_path and self.manifest:
            return self.installed_path / "osw-plugin.json"
        return Path()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "receipt": self.receipt.to_dict() if self.receipt else None,
            "manifest": self.manifest.to_dict() if self.manifest else None,
            "diagnostics": self.diagnostics,
            "source_path": str(self.source_path),
            "installed_path": str(self.installed_path) if self.installed_path else None,
            "quarantine_path": str(self.quarantine_path) if self.quarantine_path else None,
            "warnings": list(self.warnings),
        }


@dataclass
class PluginQuarantineRecord:
    source_path: str
    quarantine_path: str | None = None
    reason: str = ""
    diagnostics: list[str] = field(default_factory=list)
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.datetime.now(datetime.UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "quarantine_path": self.quarantine_path,
            "reason": self.reason,
            "diagnostics": self.diagnostics,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


class PluginInstallManager:
    """Install local plugin folders or zip archives into a managed directory."""

    def __init__(
        self,
        install_root: str | Path,
        *,
        state_store: PluginStateStore | None = None,
    ) -> None:
        self.install_root = Path(install_root)
        self.state_store = state_store

    def _load_receipts(self) -> dict[str, dict[str, Any]]:
        receipts_file = self.install_root / "receipts.json"
        if not receipts_file.exists():
            return {}
        try:
            return json.loads(receipts_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_receipts(self, receipts: dict[str, dict[str, Any]]) -> None:
        self.install_root.mkdir(parents=True, exist_ok=True)
        receipts_file = self.install_root / "receipts.json"
        receipts_file.write_text(json.dumps(receipts, indent=2), encoding="utf-8")

    def _load_quarantine_records(self) -> list[dict[str, Any]]:
        q_file = self.install_root / "quarantine_records.json"
        if not q_file.exists():
            return []
        try:
            return json.loads(q_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []

    def _save_quarantine_records(self, records: list[dict[str, Any]]) -> None:
        self.install_root.mkdir(parents=True, exist_ok=True)
        q_file = self.install_root / "quarantine_records.json"
        q_file.write_text(json.dumps(records, indent=2), encoding="utf-8")

    def list_quarantine(self) -> list[PluginQuarantineRecord]:
        return [PluginQuarantineRecord(**r) for r in self._load_quarantine_records()]

    def list_receipts(self) -> list[PluginInstallReceipt]:
        return [PluginInstallReceipt.from_dict(r) for r in self._load_receipts().values()]

    def get_receipt(self, plugin_id: str) -> PluginInstallReceipt | None:
        receipts = self._load_receipts()
        if plugin_id in receipts:
            return PluginInstallReceipt.from_dict(receipts[plugin_id])
        return None

    def validate_folder(
        self,
        plugin_folder: str | Path,
        *,
        existing_plugin_ids: Iterable[str] = (),
    ) -> PluginValidationResult:
        folder = Path(plugin_folder)
        try:
            manifest_path = _single_manifest_path(folder)
            manifest = PluginManifest.load(manifest_path)
        except PluginInstallError as exc:
            return PluginValidationResult(None, None, folder, error_message=str(exc))
        except PluginManifestError as exc:
            return PluginValidationResult(None, None, folder, error_message=str(exc))

        if manifest.id in set(existing_plugin_ids):
            return PluginValidationResult(
                manifest,
                manifest_path,
                manifest_path.parent,
                error_message=f"Duplicate plugin id: {manifest.id}",
            )

        return PluginValidationResult(
            manifest=manifest,
            manifest_path=manifest_path,
            plugin_root=manifest_path.parent,
            warnings=_dependency_messages(manifest),
        )

    def install_from_folder(
        self,
        plugin_folder: str | Path,
        *,
        existing_plugin_ids: Iterable[str] = (),
        allow_replace: bool = False,
        enable_after_install: bool = False,
    ) -> PluginInstallResult:
        source = Path(plugin_folder)
        replace_plugin_id = ""
        if allow_replace:
            # exclude self if replacement is allowed
            try:
                manifest_path = _single_manifest_path(source)
                replace_plugin_id = PluginManifest.load(manifest_path).id
            except Exception:
                pass
        known_ids = self._known_plugin_ids(
            existing_plugin_ids,
            replace_plugin_id=replace_plugin_id,
        )

        validation = self.validate_folder(
            source,
            existing_plugin_ids=known_ids,
        )

        if not validation.valid or validation.manifest is None or validation.manifest_path is None:
            reason = validation.error_message or f"Invalid plugin folder: {source}"
            # Quarantine the rejected action
            self._quarantine_failed_install(source, reason)
            # Raise appropriate error as expected by tests and clients
            if "Duplicate plugin id" in reason:
                raise DuplicatePluginInstallError(reason)
            raise PluginInstallError(reason)

        manifest = validation.manifest
        destination = self.install_root / _install_directory_name(manifest.id)

        try:
            _assert_install_source_is_safe(
                source=source,
                plugin_root=validation.plugin_root,
                install_root=self.install_root,
            )
            if destination.exists():
                _assert_managed_child(destination, self.install_root)
                if allow_replace:
                    shutil.rmtree(destination)
                else:
                    raise DuplicatePluginInstallError(
                        f"Plugin install destination already exists for id: {manifest.id}"
                    )

            self.install_root.mkdir(parents=True, exist_ok=True)
            shutil.copytree(validation.plugin_root, destination)
            installed_manifest_path = destination / validation.manifest_path.name

            # Compute Hash
            sha256 = _compute_folder_hash(validation.plugin_root)

            # Receipt
            receipt = PluginInstallReceipt(
                plugin_id=manifest.id,
                name=manifest.name,
                version=manifest.version,
                source_kind=PluginSourceKind.LOCAL_FOLDER.value,
                source_path=str(source.resolve()),
                installed_path=str(destination.resolve()),
                manifest_path=str(installed_manifest_path.resolve()),
                sha256=sha256,
            )

            receipts = self._load_receipts()
            receipts[manifest.id] = receipt.to_dict()
            self._save_receipts(receipts)
            self._apply_enablement(manifest.id, enable_after_install)

            return PluginInstallResult(
                status=PluginInstallStatus.INSTALLED.value,
                receipt=receipt,
                manifest=manifest,
                source_path=source,
                installed_path=destination,
                warnings=validation.warnings,
            )
        except Exception as exc:
            if isinstance(exc, PluginInstallError):
                self._quarantine_failed_install(source, str(exc))
                raise
            reason = f"Install from folder failed: {exc}"
            self._quarantine_failed_install(source, reason)
            raise PluginInstallError(reason) from exc

    def install_from_zip(
        self,
        archive_path: str | Path,
        *,
        existing_plugin_ids: Iterable[str] = (),
        allow_replace: bool = False,
        enable_after_install: bool = False,
    ) -> PluginInstallResult:
        source = Path(archive_path)
        with tempfile.TemporaryDirectory(prefix="osw-plugin-") as temp_dir:
            extract_root = Path(temp_dir)
            try:
                _safe_extract_zip(source, extract_root)
            except Exception as exc:
                reason = str(exc)
                self._quarantine_failed_install(source, reason)
                raise

            # Detect ID to optionally exclude it from duplicates in replacement mode
            known_ids = self._known_plugin_ids(existing_plugin_ids)
            if allow_replace:
                try:
                    manifest_path = _single_manifest_path(extract_root)
                    manifest_id = PluginManifest.load(manifest_path).id
                    known_ids = self._known_plugin_ids(
                        existing_plugin_ids,
                        replace_plugin_id=manifest_id,
                    )
                except Exception:
                    pass

            validation = self.validate_folder(
                extract_root,
                existing_plugin_ids=known_ids,
            )

            if (
                not validation.valid
                or validation.manifest is None
                or validation.manifest_path is None
            ):
                reason = validation.error_message or f"Invalid plugin archive: {source}"
                self._quarantine_failed_install(source, reason)
                if "Duplicate plugin id" in reason:
                    raise DuplicatePluginInstallError(reason)
                raise PluginInstallError(reason)

            manifest = validation.manifest
            destination = self.install_root / _install_directory_name(manifest.id)

            try:
                if destination.exists():
                    _assert_managed_child(destination, self.install_root)
                    if allow_replace:
                        shutil.rmtree(destination)
                    else:
                        raise DuplicatePluginInstallError(
                            f"Plugin install destination already exists for id: {manifest.id}"
                        )

                self.install_root.mkdir(parents=True, exist_ok=True)
                shutil.copytree(validation.plugin_root, destination)
                installed_manifest_path = destination / validation.manifest_path.name

                # Compute Zip SHA256
                sha256 = _compute_file_hash(source)

                receipt = PluginInstallReceipt(
                    plugin_id=manifest.id,
                    name=manifest.name,
                    version=manifest.version,
                    source_kind=PluginSourceKind.LOCAL_ZIP.value,
                    source_path=str(source.resolve()),
                    installed_path=str(destination.resolve()),
                    manifest_path=str(installed_manifest_path.resolve()),
                    sha256=sha256,
                )

                receipts = self._load_receipts()
                receipts[manifest.id] = receipt.to_dict()
                self._save_receipts(receipts)
                self._apply_enablement(manifest.id, enable_after_install)

                return PluginInstallResult(
                    status=PluginInstallStatus.INSTALLED.value,
                    receipt=receipt,
                    manifest=manifest,
                    source_path=source,
                    installed_path=destination,
                    warnings=validation.warnings,
                )
            except Exception as exc:
                if isinstance(exc, PluginInstallError):
                    self._quarantine_failed_install(source, str(exc))
                    raise
                reason = f"Install from zip failed: {exc}"
                self._quarantine_failed_install(source, reason)
                raise PluginInstallError(reason) from exc

    def uninstall_plugin(self, plugin_id: str) -> None:
        receipts = self._load_receipts()
        if plugin_id not in receipts:
            raise PluginInstallError(
                f"Plugin '{plugin_id}' is not installed in the managed root."
            )

        receipt = receipts[plugin_id]
        installed_path = Path(receipt["installed_path"])

        # Safety boundary check:
        # 1. Resolve path
        # 2. Make sure it is strictly under the managed install root
        try:
            resolved_installed = installed_path.resolve()
            resolved_root = self.install_root.resolve()
            if (
                resolved_installed == resolved_root
                or resolved_root not in resolved_installed.parents
            ):
                raise PluginInstallError(
                    "Safety rejection: uninstall would write outside managed root."
                )

            if installed_path.exists():
                shutil.rmtree(installed_path)

            receipts.pop(plugin_id, None)
            self._save_receipts(receipts)
        except Exception as exc:
            if isinstance(exc, PluginInstallError):
                raise
            raise PluginInstallError(f"Failed to uninstall plugin '{plugin_id}': {exc}") from exc

    def installed_plugin_ids(self) -> tuple[str, ...]:
        ids: list[str] = []
        for manifest_path in iter_manifest_paths(self.install_root):
            try:
                # ignore quarantine path
                if "quarantine" in manifest_path.parts:
                    continue
                ids.append(PluginManifest.load(manifest_path).id)
            except PluginManifestError:
                continue
        # Deduplicate with receipts list just in case
        receipt_ids = list(self._load_receipts().keys())
        return tuple(sorted(list(set(ids + receipt_ids))))

    def _quarantine_failed_install(
        self, source_path: Path, reason: str
    ) -> PluginQuarantineRecord | None:
        self.install_root.mkdir(parents=True, exist_ok=True)
        q_dir = self.install_root / "quarantine"
        q_dir.mkdir(exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target_name = f"{source_path.stem}_quarantine_{timestamp}"
        target_path = q_dir / target_name

        # Keep invalid local folders as records only; copying them could follow
        # local symlink/junction escapes. Zip files are copied as inert bytes.
        quarantined_dest: str | None = None
        try:
            if source_path.exists():
                if source_path.is_file():
                    shutil.copy2(
                        source_path,
                        target_path.with_name(target_name + source_path.suffix)
                    )
                    target_path = target_path.with_name(target_name + source_path.suffix)
                    quarantined_dest = str(target_path.resolve())
        except Exception:
            pass

        record = PluginQuarantineRecord(
            source_path=str(source_path.resolve()) if source_path.exists() else str(source_path),
            quarantine_path=quarantined_dest,
            reason=reason,
            diagnostics=[reason],
        )

        records = self._load_quarantine_records()
        records.append(record.to_dict())
        self._save_quarantine_records(records)
        return record

    def _known_plugin_ids(
        self,
        additional_ids: Iterable[str],
        *,
        replace_plugin_id: str = "",
    ) -> tuple[str, ...]:
        builtin_ids = {manifest.id for manifest in builtin_plugin_manifests()}
        installed_ids = {
            plugin_id
            for plugin_id in self.installed_plugin_ids()
            if not replace_plugin_id or plugin_id != replace_plugin_id
        }
        return tuple({*builtin_ids, *installed_ids, *additional_ids})

    def _apply_enablement(self, plugin_id: str, enable_after_install: bool) -> None:
        if self.state_store is not None and enable_after_install:
            self.state_store.set_enabled(plugin_id, enable_after_install)


def _single_manifest_path(folder: Path) -> Path:
    if not folder.exists():
        raise PluginInstallError(f"Plugin folder does not exist: {folder}")
    if not folder.is_dir():
        raise PluginInstallError(f"Plugin source is not a folder: {folder}")

    manifest_paths = tuple(iter_manifest_paths(folder))
    if not manifest_paths:
        raise PluginInstallError(f"No OSW plugin manifest found in: {folder}")
    if len(manifest_paths) > 1:
        raise PluginInstallError(
            f"Expected one OSW plugin manifest in {folder}, found {len(manifest_paths)}"
        )
    return manifest_paths[0]


def _dependency_messages(manifest: PluginManifest) -> tuple[str, ...]:
    health = check_manifest_health(manifest)
    return health.messages


def _safe_extract_zip(archive_path: Path, extract_root: Path) -> None:
    root = extract_root.resolve()
    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = archive.infolist()
            if not members:
                raise UnsafeArchiveError("Archive is empty; no plugin manifest can be read.")
            # 1. Enforce file count limits
            if len(members) > MAX_FILE_COUNT:
                raise UnsafeArchiveError(
                    f"Archive exceeds maximum file count limit ({MAX_FILE_COUNT})."
                )

            # 2. Enforce total uncompressed size limit
            total_size = sum(m.file_size for m in members)
            if total_size > MAX_UNCOMPRESSED_SIZE_BYTES:
                limit_mb = MAX_UNCOMPRESSED_SIZE_BYTES // (1024 * 1024)
                raise UnsafeArchiveError(
                    f"Archive exceeds uncompressed size limit ({limit_mb} MB)."
                )

            # Pre-scan for path traversal, UNC, symlinks, absolute paths
            normalized_names: set[str] = set()
            for member in members:
                # Reject symlinks if detectable via Unix mode
                # zipfile external_attr: upper 16 bits are Unix mode.
                mode = member.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise UnsafeArchiveError(
                        "Archive contains a symbolic link, which is not "
                        f"allowed for security reasons: {member.filename}"
                    )

                # Validate paths
                _safe_zip_target(root, member.filename)
                normalized = member.filename.replace("\\", "/")
                name_key = str(PurePosixPath(normalized)).casefold().rstrip("/")
                if name_key in normalized_names:
                    raise UnsafeArchiveError(
                        f"Archive contains duplicate/conflicting entry: {member.filename}"
                    )
                normalized_names.add(name_key)

            # Perform actual extraction safely
            for member in members:
                # Exclude .pyc, .pyo, and __pycache__ paths
                normalized = member.filename.replace("\\", "/")
                parts = PurePosixPath(normalized).parts
                if any(p == "__pycache__" or p.endswith((".pyc", ".pyo")) for p in parts):
                    continue

                target = _safe_zip_target(root, member.filename)
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue

                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open("wb") as destination:
                    shutil.copyfileobj(source, destination)
    except zipfile.BadZipFile as exc:
        raise PluginInstallError(f"Invalid plugin zip archive: {archive_path}") from exc


def _safe_zip_target(root: Path, member_name: str) -> Path:
    normalized = member_name.replace("\\", "/")
    member_path = PurePosixPath(normalized)

    # Aggressive security boundary check:
    # 1. Check for absolute path entries
    # 2. Check for unsafe path parts (.., empty, drive separator ":", UNC format starts with "//")
    if member_path.is_absolute():
        raise ZipPathTraversalError(
            f"Plugin zip entry is absolute, which is blocked for safety: {member_name}"
        )

    parts = member_path.parts
    if _has_unsafe_zip_part(parts) or normalized.startswith(("/", "\\")):
        raise ZipPathTraversalError(
            f"Plugin zip entry would write outside the install staging folder: {member_name}"
        )

    target = (root / Path(*parts)).resolve()
    if target != root and root not in target.parents:
        raise ZipPathTraversalError(
            f"Plugin zip entry would write outside the install staging folder: {member_name}"
        )
    return target


def _has_unsafe_zip_part(parts: tuple[str, ...]) -> bool:
    # catches .. or empty parts or parts with drive letters (":") or starts with empty.
    # on Windows UNC paths are also detected.
    return any(part in ("", ".", "..") or ":" in part for part in parts)


def _assert_install_source_is_safe(
    *,
    source: Path,
    plugin_root: Path,
    install_root: Path,
) -> None:
    resolved_source = source.resolve()
    resolved_plugin_root = plugin_root.resolve()
    resolved_install_root = install_root.resolve()
    if (
        resolved_source == resolved_install_root
        or resolved_install_root in resolved_source.parents
        or resolved_plugin_root == resolved_install_root
        or resolved_install_root in resolved_plugin_root.parents
    ):
        raise PluginInstallError(
            "Plugin folder install source must be outside the managed install root."
        )
    _reject_local_link_entries(resolved_plugin_root)


def _reject_local_link_entries(plugin_root: Path) -> None:
    if plugin_root.is_symlink() or _is_junction(plugin_root):
        raise UnsafeArchiveError(
            f"Plugin folder contains a symbolic link or junction: {plugin_root}"
        )
    for child in plugin_root.rglob("*"):
        if child.is_symlink() or _is_junction(child):
            raise UnsafeArchiveError(
                f"Plugin folder contains a symbolic link or junction: {child}"
            )


def _is_junction(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


def _assert_managed_child(path: Path, install_root: Path) -> None:
    resolved_path = path.resolve()
    resolved_root = install_root.resolve()
    if resolved_path == resolved_root or resolved_root not in resolved_path.parents:
        raise PluginInstallError(
            "Safety rejection: managed plugin path is outside install root."
        )


def _install_directory_name(plugin_id: str) -> str:
    encoded = base64.urlsafe_b64encode(plugin_id.encode("utf-8")).decode("ascii")
    return "plugin_" + encoded.rstrip("=")


def _compute_file_hash(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def _compute_folder_hash(path: Path) -> str:
    h = hashlib.sha256()
    try:
        for child in sorted(path.rglob("*")):
            if not child.is_file() or child.is_symlink():
                continue
            relative = child.relative_to(path).as_posix()
            h.update(relative.encode("utf-8"))
            h.update(b"\0")
            with child.open("rb") as handle:
                for chunk in iter(lambda: handle.read(65536), b""):
                    h.update(chunk)
            h.update(b"\0")
        return h.hexdigest()
    except Exception:
        return ""


def _first_direct_manifest(root: Path) -> Path | None:
    # Re-use logic to locate direct manifest
    from .discovery import MANIFEST_FILENAMES, MANIFEST_SUFFIXES
    candidates = [
        child for child in root.iterdir()
        if child.is_file() and (
            child.name in MANIFEST_FILENAMES
            or child.name.endswith(MANIFEST_SUFFIXES)
        )
    ]
    return sorted(candidates)[0] if candidates else None
