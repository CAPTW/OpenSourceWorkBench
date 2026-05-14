"""Local plugin folder and zip installer.

The installer validates OSW plugin manifests by reading manifest files only. It
does not import plugin modules or execute plugin entry points during install.
"""

from __future__ import annotations

import base64
import shutil
import tempfile
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from .discovery import iter_manifest_paths
from .health import check_manifest_health
from .manifest import PluginManifest, PluginManifestError


class PluginInstallError(RuntimeError):
    """Raised when a local plugin cannot be installed safely."""


class DuplicatePluginInstallError(PluginInstallError):
    """Raised when an installed plugin already declares the same id."""


class ZipPathTraversalError(PluginInstallError):
    """Raised when a zip archive attempts to write outside the extraction root."""


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


@dataclass(frozen=True)
class PluginInstallResult:
    manifest: PluginManifest
    source_path: Path
    installed_path: Path
    manifest_path: Path
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def plugin_id(self) -> str:
        return self.manifest.id


class PluginInstallManager:
    """Install local plugin folders or zip archives into a managed directory."""

    def __init__(self, install_root: str | Path) -> None:
        self.install_root = Path(install_root)

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
    ) -> PluginInstallResult:
        source = Path(plugin_folder)
        validation = self.validate_folder(
            source,
            existing_plugin_ids=self._known_plugin_ids(existing_plugin_ids),
        )
        if (
            not validation.valid
            or validation.manifest is None
            or validation.manifest_path is None
        ):
            _raise_install_error(validation.error_message or f"Invalid plugin folder: {source}")

        destination = self._destination_for(validation.manifest)
        self.install_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(validation.plugin_root, destination)
        installed_manifest_path = destination / validation.manifest_path.name
        return PluginInstallResult(
            manifest=validation.manifest,
            source_path=source,
            installed_path=destination,
            manifest_path=installed_manifest_path,
            warnings=validation.warnings,
        )

    def install_from_zip(
        self,
        archive_path: str | Path,
        *,
        existing_plugin_ids: Iterable[str] = (),
    ) -> PluginInstallResult:
        source = Path(archive_path)
        with tempfile.TemporaryDirectory(prefix="osw-plugin-") as temp_dir:
            extract_root = Path(temp_dir)
            _safe_extract_zip(source, extract_root)
            validation = self.validate_folder(
                extract_root,
                existing_plugin_ids=self._known_plugin_ids(existing_plugin_ids),
            )
            if (
                not validation.valid
                or validation.manifest is None
                or validation.manifest_path is None
            ):
                _raise_install_error(
                    validation.error_message or f"Invalid plugin archive: {source}"
                )

            destination = self._destination_for(validation.manifest)
            self.install_root.mkdir(parents=True, exist_ok=True)
            shutil.copytree(validation.plugin_root, destination)
            installed_manifest_path = destination / validation.manifest_path.name
            return PluginInstallResult(
                manifest=validation.manifest,
                source_path=source,
                installed_path=destination,
                manifest_path=installed_manifest_path,
                warnings=validation.warnings,
            )

    def installed_plugin_ids(self) -> tuple[str, ...]:
        ids: list[str] = []
        for manifest_path in iter_manifest_paths(self.install_root):
            try:
                ids.append(PluginManifest.load(manifest_path).id)
            except PluginManifestError:
                continue
        return tuple(ids)

    def _destination_for(self, manifest: PluginManifest) -> Path:
        destination = self.install_root / _install_directory_name(manifest.id)
        if destination.exists():
            raise DuplicatePluginInstallError(
                f"Plugin install destination already exists for id: {manifest.id}"
            )
        return destination

    def _known_plugin_ids(self, additional_ids: Iterable[str]) -> tuple[str, ...]:
        return tuple({*self.installed_plugin_ids(), *additional_ids})


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
            for member in archive.infolist():
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
    if member_path.is_absolute() or _has_unsafe_zip_part(member_path.parts):
        raise ZipPathTraversalError(
            f"Plugin zip entry would write outside the install staging folder: {member_name}"
        )

    target = (root / Path(*member_path.parts)).resolve()
    if target != root and root not in target.parents:
        raise ZipPathTraversalError(
            f"Plugin zip entry would write outside the install staging folder: {member_name}"
        )
    return target


def _has_unsafe_zip_part(parts: tuple[str, ...]) -> bool:
    return any(part in ("", ".", "..") or ":" in part for part in parts)


def _install_directory_name(plugin_id: str) -> str:
    encoded = base64.urlsafe_b64encode(plugin_id.encode("utf-8")).decode("ascii")
    return "plugin_" + encoded.rstrip("=")


def _raise_install_error(message: str) -> None:
    if message.startswith("Duplicate plugin id:"):
        raise DuplicatePluginInstallError(message)
    raise PluginInstallError(message)
