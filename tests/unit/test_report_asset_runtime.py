"""Pure runtime report-asset path contract tests.

The contract under test is lexical only. Synthetic path text is used throughout;
no test creates an image or contacts a local, network, UNC, or device path.
"""

from __future__ import annotations

import ast
import builtins
import inspect
import os
import shutil
import socket
import urllib.request
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import osw.core.report_asset_runtime as runtime_module
from osw.core.report_asset import ReportAssetPathKind
from osw.core.report_asset_runtime import (
    CanonicalContainment,
    ConsentState,
    LexicalContainment,
    PathFlavor,
    ReportAssetLocation,
    ReportAssetPortability,
    ReportAssetResolutionContext,
    ReportAssetResolutionDescriptor,
    ReportAssetResolutionPhase,
    ReportAssetResolutionSeverity,
    ReportAssetResolutionStatus,
    ReportAssetRuntimeIntent,
    ReportAssetSafeView,
    evaluate_report_asset_runtime,
    report_asset_safe_view,
    status_metadata,
)

EXPECTED_STATUSES = {
    "legacy_not_resolved",
    "root_unavailable",
    "candidate_ready",
    "consent_required",
    "network_consent_required",
    "resolved_local",
    "resolved_network",
    "missing",
    "not_regular_file",
    "unsupported_suffix",
    "permission_denied",
    "outside_project_root",
    "symlink_or_junction_escape",
    "device_path_blocked",
    "stale_context",
    "stale_request",
    "filesystem_error",
    "unsupported_kind",
    "unresolved_no_resolver",
    "invalid_intent",
    "unsupported_path_flavor",
    "unsafe_path_component",
}


def _context(
    *,
    root: str | None = None,
    flavor: PathFlavor = PathFlavor.UNKNOWN,
    generation: int = 7,
) -> ReportAssetResolutionContext:
    return ReportAssetResolutionContext(
        project_root=root,
        project_root_flavor=flavor,
        context_generation=generation,
        document_token="document-token",
        request_token="request-token",
        purpose="preview",
        consent_state=ConsentState.REQUIRED,
        consent_token="consent-token",
        record_fingerprint="record-fingerprint",
    )


def _evaluate(
    stored_path: str,
    kind: ReportAssetPathKind | str | None,
    *,
    context: ReportAssetResolutionContext | None = None,
) -> ReportAssetResolutionDescriptor:
    return evaluate_report_asset_runtime(
        ReportAssetRuntimeIntent(
            asset_id="asset-1",
            stored_path=stored_path,
            declared_kind=kind,
        ),
        context or _context(),
    )


def test_exact_status_vocabulary_and_metadata_are_stable() -> None:
    assert {status.value for status in ReportAssetResolutionStatus} == EXPECTED_STATUSES

    for status in ReportAssetResolutionStatus:
        metadata = status_metadata(status)
        assert isinstance(metadata.phase, ReportAssetResolutionPhase)
        assert isinstance(metadata.severity, ReportAssetResolutionSeverity)
        assert isinstance(metadata.retryable, bool)
        assert metadata.message
        assert "\\" not in metadata.message
        assert "/" not in metadata.message

    assert status_metadata(ReportAssetResolutionStatus.CANDIDATE_READY).phase is (
        ReportAssetResolutionPhase.CANDIDATE
    )
    assert status_metadata(ReportAssetResolutionStatus.DEVICE_PATH_BLOCKED).severity is (
        ReportAssetResolutionSeverity.BLOCKED
    )
    assert not status_metadata(
        ReportAssetResolutionStatus.DEVICE_PATH_BLOCKED
    ).retryable


@pytest.mark.parametrize(
    "contract_type",
    [
        ReportAssetRuntimeIntent,
        ReportAssetResolutionContext,
        ReportAssetResolutionDescriptor,
        ReportAssetSafeView,
    ],
)
def test_contract_types_are_frozen_and_slotted(contract_type: type[object]) -> None:
    assert "__slots__" in contract_type.__dict__

    intent = ReportAssetRuntimeIntent("asset-1", "scene.png", None)
    with pytest.raises(FrozenInstanceError):
        intent.asset_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("factory", "match"),
    [
        (lambda: ReportAssetRuntimeIntent(1, "scene.png", None), "asset_id"),
        (lambda: ReportAssetRuntimeIntent("asset", Path("scene.png"), None), "stored_path"),
        (lambda: ReportAssetRuntimeIntent("asset", "scene.png", object()), "declared_kind"),
        (
            lambda: ReportAssetResolutionContext(
                project_root=Path("project"),
                project_root_flavor=PathFlavor.POSIX,
                context_generation=0,
                document_token="document",
                request_token="request",
                purpose="preview",
                record_fingerprint="fingerprint",
            ),
            "project_root",
        ),
    ],
)
def test_runtime_inputs_require_actual_strings_without_coercion(
    factory: object,
    match: str,
) -> None:
    with pytest.raises(TypeError, match=match):
        factory()  # type: ignore[operator]


@pytest.mark.parametrize("generation", [-1, True, 1.5])
def test_context_rejects_invalid_generation(generation: object) -> None:
    with pytest.raises((TypeError, ValueError), match="context_generation"):
        ReportAssetResolutionContext(
            project_root=None,
            project_root_flavor=PathFlavor.UNKNOWN,
            context_generation=generation,  # type: ignore[arg-type]
            document_token="document",
            request_token="request",
            purpose="preview",
            record_fingerprint="fingerprint",
        )


def test_context_identity_values_remain_distinct_private_and_immutable() -> None:
    context = _context(generation=11)

    assert context.context_generation == 11
    assert context.document_token == "document-token"
    assert context.request_token == "request-token"
    assert context.purpose == "preview"
    assert context.consent_state is ConsentState.REQUIRED
    assert context.consent_token == "consent-token"
    assert context.record_fingerprint == "record-fingerprint"
    rendered = repr(context)
    for private_value in (
        "document-token",
        "request-token",
        "consent-token",
        "record-fingerprint",
    ):
        assert private_value not in rendered


def test_omitted_and_explicit_legacy_remain_distinct_without_candidates() -> None:
    omitted = _evaluate("legacy/private.png", None)
    explicit = _evaluate("legacy/private.png", ReportAssetPathKind.LEGACY_RAW)

    assert omitted.declared_kind is None
    assert explicit.declared_kind is ReportAssetPathKind.LEGACY_RAW
    assert omitted.status is ReportAssetResolutionStatus.LEGACY_NOT_RESOLVED
    assert explicit.status is ReportAssetResolutionStatus.LEGACY_NOT_RESOLVED
    for descriptor in (omitted, explicit):
        assert descriptor.lexical_candidate is None
        assert descriptor.effective_path is None
        assert descriptor.project_root is None
        assert descriptor.path_flavor is PathFlavor.UNKNOWN


@pytest.mark.parametrize(
    ("stored_path", "flavor", "location", "status"),
    [
        (
            r"C:\captures\scene.PNG",
            PathFlavor.WINDOWS,
            ReportAssetLocation.LOCAL_EXTERNAL,
            ReportAssetResolutionStatus.CONSENT_REQUIRED,
        ),
        (
            "/var/captures/scene.webp",
            PathFlavor.POSIX,
            ReportAssetLocation.LOCAL_EXTERNAL,
            ReportAssetResolutionStatus.CONSENT_REQUIRED,
        ),
        (
            r"\\server\share\scene.jpg",
            PathFlavor.WINDOWS,
            ReportAssetLocation.NETWORK_LIKE,
            ReportAssetResolutionStatus.NETWORK_CONSENT_REQUIRED,
        ),
        (
            "//server/share/scene.gif",
            PathFlavor.POSIX,
            ReportAssetLocation.NETWORK_LIKE,
            ReportAssetResolutionStatus.NETWORK_CONSENT_REQUIRED,
        ),
    ],
)
def test_external_absolute_paths_are_lexical_candidates_only(
    stored_path: str,
    flavor: PathFlavor,
    location: ReportAssetLocation,
    status: ReportAssetResolutionStatus,
) -> None:
    descriptor = _evaluate(
        stored_path,
        ReportAssetPathKind.EXTERNAL_ABSOLUTE,
        context=_context(root="/ignored/root", flavor=PathFlavor.POSIX),
    )

    assert descriptor.path_flavor is flavor
    assert descriptor.location is location
    assert descriptor.status is status
    assert descriptor.lexical_candidate == stored_path
    assert descriptor.project_root is None
    assert descriptor.effective_path is None
    assert descriptor.canonical_containment is CanonicalContainment.UNKNOWN


@pytest.mark.parametrize(
    ("stored_path", "status"),
    [
        (r"\\?\C:\captures\scene.png", ReportAssetResolutionStatus.DEVICE_PATH_BLOCKED),
        (r"\\.\C:\captures\scene.png", ReportAssetResolutionStatus.DEVICE_PATH_BLOCKED),
        (r"C:captures\scene.png", ReportAssetResolutionStatus.INVALID_INTENT),
        (r"\captures\scene.png", ReportAssetResolutionStatus.INVALID_INTENT),
        ("https://example.invalid/scene.png", ReportAssetResolutionStatus.INVALID_INTENT),
        (r"C:\captures\CON.png", ReportAssetResolutionStatus.UNSAFE_PATH_COMPONENT),
        (r"C:\captures\scene.svg", ReportAssetResolutionStatus.UNSUPPORTED_SUFFIX),
    ],
)
def test_external_absolute_rejects_unsafe_or_unsupported_syntax(
    stored_path: str,
    status: ReportAssetResolutionStatus,
) -> None:
    descriptor = _evaluate(stored_path, ReportAssetPathKind.EXTERNAL_ABSOLUTE)

    assert descriptor.status is status
    assert descriptor.lexical_candidate is None
    assert descriptor.effective_path is None


@pytest.mark.parametrize(
    ("root", "flavor", "expected_candidate"),
    [
        (r"C:\project", PathFlavor.WINDOWS, r"C:\project\screenshots\scene.png"),
        ("/srv/project", PathFlavor.POSIX, "/srv/project/screenshots/scene.png"),
    ],
)
def test_project_relative_builds_matching_pure_path_candidate(
    root: str,
    flavor: PathFlavor,
    expected_candidate: str,
) -> None:
    descriptor = _evaluate(
        "screenshots/scene.png",
        ReportAssetPathKind.PROJECT_RELATIVE,
        context=_context(root=root, flavor=flavor),
    )

    assert descriptor.status is ReportAssetResolutionStatus.CANDIDATE_READY
    assert descriptor.path_flavor is flavor
    assert descriptor.portability is ReportAssetPortability.PROJECT_RELATIVE_PORTABLE
    assert descriptor.location is ReportAssetLocation.LOCAL_PROJECT
    assert descriptor.lexical_candidate == expected_candidate
    assert descriptor.lexical_containment is LexicalContainment.WITHIN_ROOT
    assert descriptor.canonical_containment is CanonicalContainment.UNKNOWN
    assert descriptor.effective_path is None


@pytest.mark.parametrize(
    ("root", "flavor", "status"),
    [
        (None, PathFlavor.UNKNOWN, ReportAssetResolutionStatus.ROOT_UNAVAILABLE),
        ("relative/project", PathFlavor.POSIX, ReportAssetResolutionStatus.ROOT_UNAVAILABLE),
        (r"relative\project", PathFlavor.WINDOWS, ReportAssetResolutionStatus.ROOT_UNAVAILABLE),
        (r"C:\project", PathFlavor.POSIX, ReportAssetResolutionStatus.UNSUPPORTED_PATH_FLAVOR),
        ("/srv/project", PathFlavor.WINDOWS, ReportAssetResolutionStatus.UNSUPPORTED_PATH_FLAVOR),
        ("/srv/project", PathFlavor.UNKNOWN, ReportAssetResolutionStatus.UNSUPPORTED_PATH_FLAVOR),
    ],
)
def test_project_relative_requires_explicit_absolute_compatible_root(
    root: str | None,
    flavor: PathFlavor,
    status: ReportAssetResolutionStatus,
) -> None:
    descriptor = _evaluate(
        "screenshots/scene.png",
        ReportAssetPathKind.PROJECT_RELATIVE,
        context=_context(root=root, flavor=flavor),
    )

    assert descriptor.status is status
    assert descriptor.lexical_candidate is None
    assert descriptor.effective_path is None


@pytest.mark.parametrize(
    ("stored_path", "status"),
    [
        ("screenshots/./scene.png", ReportAssetResolutionStatus.UNSAFE_PATH_COMPONENT),
        ("screenshots/../scene.png", ReportAssetResolutionStatus.UNSAFE_PATH_COMPONENT),
        ("screenshots//scene.png", ReportAssetResolutionStatus.UNSAFE_PATH_COMPONENT),
        (r"screenshots\scene.png", ReportAssetResolutionStatus.UNSAFE_PATH_COMPONENT),
        ("screenshots/scene\x01.png", ReportAssetResolutionStatus.UNSAFE_PATH_COMPONENT),
        ("screenshots/scene.png/", ReportAssetResolutionStatus.UNSAFE_PATH_COMPONENT),
        ("screenshots/CON.png", ReportAssetResolutionStatus.UNSAFE_PATH_COMPONENT),
        ("screenshots/scene.svg", ReportAssetResolutionStatus.UNSUPPORTED_SUFFIX),
        ("https://example.invalid/scene.png", ReportAssetResolutionStatus.INVALID_INTENT),
    ],
)
def test_project_relative_fails_closed_for_bad_components(
    stored_path: str,
    status: ReportAssetResolutionStatus,
) -> None:
    descriptor = _evaluate(
        stored_path,
        ReportAssetPathKind.PROJECT_RELATIVE,
        context=_context(root="/srv/project", flavor=PathFlavor.POSIX),
    )

    assert descriptor.status is status
    assert descriptor.lexical_candidate is None


@pytest.mark.parametrize("kind", [ReportAssetPathKind.MANAGED_PROJECT_ASSET, "future_kind"])
def test_reserved_or_unknown_kind_fails_closed(kind: ReportAssetPathKind | str) -> None:
    descriptor = _evaluate("assets/scene.png", kind)

    assert descriptor.status is ReportAssetResolutionStatus.UNSUPPORTED_KIND
    assert descriptor.lexical_candidate is None
    assert descriptor.effective_path is None


@pytest.mark.parametrize(
    ("stored_path", "safe_basename"),
    [
        (r"C:\private\alice\scene.png", "scene.png"),
        ("/home/alice/private/scene.jpg", "scene.jpg"),
        (r"\\secret-server\private-share\shot.gif", "shot.gif"),
        ("", "screenshot"),
        (r"C:\private\CON.png", "screenshot"),
    ],
)
def test_safe_projection_contains_only_path_free_values(
    stored_path: str,
    safe_basename: str,
) -> None:
    kind = None if not stored_path else ReportAssetPathKind.LEGACY_RAW
    descriptor = _evaluate(stored_path, kind)
    safe = report_asset_safe_view(descriptor)
    mapping = safe.to_mapping()

    assert safe.safe_basename == safe_basename
    assert mapping["safe_basename"] == safe_basename
    assert mapping["status"] == descriptor.status.value
    assert isinstance(mapping["diagnostic_codes"], list)
    assert isinstance(mapping["diagnostic_messages"], list)
    forbidden_keys = {
        "stored_path",
        "project_root",
        "lexical_candidate",
        "effective_path",
        "document_token",
        "request_token",
        "consent_token",
        "record_fingerprint",
    }
    assert forbidden_keys.isdisjoint(mapping)
    rendered = repr(descriptor) + repr(safe) + repr(mapping)
    for private_value in (
        stored_path,
        descriptor.project_root or "",
        descriptor.lexical_candidate or "",
        "document-token",
        "request-token",
        "consent-token",
        "record-fingerprint",
        "secret-server",
        "private-share",
    ):
        if private_value and private_value != safe_basename:
            assert private_value not in rendered


def test_descriptor_has_no_persistence_serializer_and_never_has_effective_path() -> None:
    descriptor = _evaluate(
        "screenshots/scene.png",
        ReportAssetPathKind.PROJECT_RELATIVE,
        context=_context(root="/srv/project", flavor=PathFlavor.POSIX),
    )

    assert not hasattr(descriptor, "to_dict")
    assert not hasattr(descriptor, "to_mapping")
    assert descriptor.effective_path is None
    assert descriptor.canonical_containment is CanonicalContainment.UNKNOWN


def test_diagnostics_are_generic_and_do_not_echo_private_values() -> None:
    descriptor = _evaluate(
        r"\\secret-server\private-share\scene.svg",
        ReportAssetPathKind.EXTERNAL_ABSOLUTE,
    )
    diagnostics = " ".join(
        (*descriptor.diagnostic_codes, *descriptor.diagnostic_messages)
    )

    assert descriptor.status is ReportAssetResolutionStatus.UNSUPPORTED_SUFFIX
    assert "secret-server" not in diagnostics
    assert "private-share" not in diagnostics
    assert "scene.svg" not in diagnostics


def test_poisoned_filesystem_and_network_apis_are_never_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_access(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("pure runtime evaluation attempted external access")

    for method_name in (
        "exists",
        "is_file",
        "stat",
        "lstat",
        "resolve",
        "absolute",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "unlink",
        "rename",
    ):
        monkeypatch.setattr(Path, method_name, unexpected_access)
    for function_name in ("exists", "isfile", "realpath", "abspath"):
        monkeypatch.setattr(os.path, function_name, unexpected_access)
    monkeypatch.setattr(os, "stat", unexpected_access)
    monkeypatch.setattr(os, "lstat", unexpected_access)
    monkeypatch.setattr(os, "remove", unexpected_access)
    monkeypatch.setattr(builtins, "open", unexpected_access)
    monkeypatch.setattr(shutil, "copy", unexpected_access)
    monkeypatch.setattr(shutil, "copy2", unexpected_access)
    monkeypatch.setattr(shutil, "move", unexpected_access)
    monkeypatch.setattr(socket, "create_connection", unexpected_access)
    monkeypatch.setattr(urllib.request, "urlopen", unexpected_access)

    cases = (
        ("legacy/private.png", None, _context()),
        ("legacy/private.png", ReportAssetPathKind.LEGACY_RAW, _context()),
        (r"C:\captures\scene.png", ReportAssetPathKind.EXTERNAL_ABSOLUTE, _context()),
        (r"\\server\share\scene.png", ReportAssetPathKind.EXTERNAL_ABSOLUTE, _context()),
        (r"\\?\C:\scene.png", ReportAssetPathKind.EXTERNAL_ABSOLUTE, _context()),
        ("screenshots/scene.png", ReportAssetPathKind.PROJECT_RELATIVE, _context()),
        (
            "screenshots/scene.png",
            ReportAssetPathKind.PROJECT_RELATIVE,
            _context(root="/srv/project", flavor=PathFlavor.POSIX),
        ),
        ("assets/scene.png", ReportAssetPathKind.MANAGED_PROJECT_ASSET, _context()),
        ("assets/scene.png", "future_kind", _context()),
    )
    for stored_path, kind, context in cases:
        descriptor = _evaluate(stored_path, kind, context=context)
        report_asset_safe_view(descriptor).to_mapping()


def test_production_module_static_boundary_has_no_io_or_outer_layer_path() -> None:
    source = inspect.getsource(runtime_module)
    tree = ast.parse(source)
    imported: set[str] = set()
    called_names: set[str] = set()
    called_attributes: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_attributes.add(node.func.attr)

    forbidden_import_roots = {
        "os",
        "osw.gui",
        "osw.post",
        "osw.core.project_schema",
        "osw.core.project_io",
        "PySide6",
        "pyvista",
        "vtk",
        "meshio",
        "gmsh",
        "subprocess",
        "socket",
        "urllib",
        "requests",
        "shutil",
        "tempfile",
        "glob",
        "PIL",
        "imageio",
        "hashlib",
    }
    assert not any(
        name == forbidden or name.startswith(f"{forbidden}.")
        for name in imported
        for forbidden in forbidden_import_roots
    )
    assert not any(
        isinstance(node, ast.ImportFrom)
        and node.module == "pathlib"
        and any(alias.name == "Path" for alias in node.names)
        for node in ast.walk(tree)
    )
    assert "open" not in called_names
    assert not called_attributes.intersection(
        {
            "exists",
            "is_file",
            "stat",
            "lstat",
            "resolve",
            "absolute",
            "realpath",
            "abspath",
            "read_text",
            "read_bytes",
            "write_text",
            "write_bytes",
            "copy",
            "copy2",
            "move",
            "rename",
            "unlink",
            "remove",
            "save",
        }
    )
