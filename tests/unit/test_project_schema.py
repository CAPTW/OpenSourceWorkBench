"""Project schema serialization and validation tests."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest

from osw.core.demo_project import create_heatsink_flow_demo_project
from osw.core.materials import IsotropicElastic, Material
from osw.core.project_schema import (
    CURRENT_SCHEMA_VERSION,
    DEFAULT_PROJECT_SCHEMA_VERSION,
    LEGACY_PROJECT_SCHEMA_VERSION,
    PATH_KIND_PROJECT_SCHEMA_VERSION,
    SUPPORTED_PROJECT_SCHEMA_VERSIONS,
    BoundaryCondition,
    GeometryRef,
    MeshRef,
    Project,
    ProjectMetadata,
    ProjectSchemaError,
    ReportConfig,
    ResultRef,
    ScriptRef,
    SolverConfig,
    load_project,
)
from osw.core.report_asset import (
    REPORT_SCREENSHOT_ASSET_CAVEAT,
    ReportAssetPathKind,
    ReportScreenshotAsset,
)
from osw.core.result_mesh_binding import (
    MESH_BINDING_METADATA_KEY,
    SOURCE_MESH_REF_METADATA_KEY,
    bridge_result_dataset_mesh_binding,
    result_mesh_binding_from_metadata,
)
from osw.core.units import Quantity, UnitSystem
from osw.core.validation import validate_project

# Frozen minimal version-dispatch seam from R0 at
# db05475785a12a00d60476110b6ee9cd8574fe05 (the parent of edf62ec). The
# post-gate return is deliberately reduced because R0 did not know screenshots.
_HISTORICAL_R0_VERSION_GATE_SOURCE = """\
CURRENT_SCHEMA_VERSION = "0.1"

def historical_project_from_dict(data):
    migrated = dict(data)
    if "schema_version" not in migrated:
        migrated["schema_version"] = CURRENT_SCHEMA_VERSION
    if migrated.get("schema_version") == "0.0":
        migrated["schema_version"] = CURRENT_SCHEMA_VERSION
    schema_version = str(migrated.get("schema_version", CURRENT_SCHEMA_VERSION))
    if schema_version != CURRENT_SCHEMA_VERSION:
        raise ProjectSchemaError(
            f"Unsupported OSW project schema version: {schema_version}"
        )
    return ()
"""


# Frozen minimal version-dispatch seam from R1 at
# edf62ec521845d484d231a7d1b034e2c99e60d70. The post-gate expression models
# the historical screenshot-path consumption that must remain unreachable.
_HISTORICAL_R1_VERSION_GATE_SOURCE = """\
CURRENT_SCHEMA_VERSION = "0.1"

def historical_project_from_dict(data):
    migrated = dict(data)
    if "schema_version" not in migrated:
        migrated["schema_version"] = CURRENT_SCHEMA_VERSION
    if migrated.get("schema_version") == "0.0":
        migrated["schema_version"] = CURRENT_SCHEMA_VERSION
    schema_version = str(migrated.get("schema_version", CURRENT_SCHEMA_VERSION))
    if schema_version != CURRENT_SCHEMA_VERSION:
        raise ProjectSchemaError(
            f"Unsupported OSW project schema version: {schema_version}"
        )
    return tuple(item["path"] for item in migrated.get("report_screenshots", ()))
"""


class _FrozenHistoricalProjectSchemaError(ValueError):
    """Isolated stand-in for the historical ProjectSchemaError subclass."""


class _NestedScreenshotPathSentinel:
    """Explode if a historical fixture reaches nested screenshot consumption."""

    def __init__(self) -> None:
        self.access_count = 0
        self._records = (
            {
                "id": "historical-project-relative",
                "path": "screenshots/scene.png",
                "path_kind": "project_relative",
            },
        )

    def __iter__(self) -> Iterator[dict[str, str]]:
        self.access_count += 1
        raise AssertionError("historical reader consumed nested screenshot paths")


def _load_frozen_historical_reader(source: str) -> object:
    namespace: dict[str, object] = {
        "__builtins__": {
            "dict": dict,
            "str": str,
            "tuple": tuple,
        },
        "ProjectSchemaError": _FrozenHistoricalProjectSchemaError,
    }
    exec(source, namespace)  # noqa: S102 - intentionally isolated frozen fixture
    return namespace["historical_project_from_dict"]


def _sample_project() -> Project:
    return Project(
        metadata=ProjectMetadata(
            name="Cantilever demo",
            description="Linear static education fixture",
            author="OSW tests",
            tags=["demo", "validation"],
        ),
        units=UnitSystem.si(),
        materials=[
            Material(
                material_id="steel",
                name="Steel",
                density=Quantity(7850.0, "kg/m^3"),
                elastic=IsotropicElastic(
                    young_modulus=Quantity(210.0, "GPa"),
                    poisson_ratio=0.3,
                ),
            )
        ],
        geometry=[GeometryRef(ref_id="geom-1", path="geometry/cantilever.step", format="STEP")],
        meshes=[MeshRef(ref_id="mesh-1", path="mesh/cantilever.vtu", format="VTU")],
        scripts=[ScriptRef(ref_id="script-1", path="scripts/plot.m", language="m")],
        solvers=[
            SolverConfig(
                solver_id="calculix-linear-static",
                name="CalculiX linear static",
                execution_mode="prepare_only",
            )
        ],
        results=[ResultRef(ref_id="result-1", path="results/cantilever.json", kind="dataset")],
        report=ReportConfig(path="reports/cantilever.html", title="Cantilever report"),
    )


def test_project_json_round_trip(tmp_path: Path) -> None:
    project = _sample_project()
    path = tmp_path / "project.osw.json"

    project.save(path)
    loaded = load_project(path)

    assert loaded == project
    assert loaded.schema_version == "0.1"
    assert not loaded.validate().has_errors


def test_mesh_ref_round_trips_mesh_info_summary(tmp_path: Path) -> None:
    project = Project(
        metadata=ProjectMetadata(name="mesh info"),
        meshes=[
            MeshRef(
                ref_id="mesh-1",
                path="mesh/tiny.vtu",
                format="vtu",
                node_count=3,
                cell_count=1,
                mesh_info={
                    "node_count": 3,
                    "element_count": 1,
                    "cell_types": ["triangle"],
                },
            )
        ],
        results=[ResultRef(ref_id="result-1", path="results/preview.json", kind="dataset")],
    )
    path = tmp_path / "project.osw.json"

    project.save(path)
    loaded = Project.load(path)

    assert loaded.mesh_refs[0].mesh_info is not None
    assert loaded.mesh_refs[0].mesh_info["cell_types"] == ["triangle"]


def test_project_round_trip_preserves_bridge_result_mesh_binding_without_schema_bump() -> None:
    ref = ResultRef(
        ref_id="result-1",
        path="results/field.json",
        kind="result_dataset",
        metadata={"keep": "unchanged"},
    )
    bridge = bridge_result_dataset_mesh_binding(
        ref,
        result_dataset_id="dataset-1",
        mesh_ref="mesh-1",
        field_id="temperature",
        node_count=4,
        cell_count=1,
    )
    assert bridge.valid is True
    project = Project(metadata=ProjectMetadata(name="binding bridge"), results=[bridge.result_ref])

    restored = Project.from_dict(project.to_dict())
    metadata = restored.results[0].metadata

    assert restored.schema_version == "0.1"
    assert metadata["keep"] == "unchanged"
    assert metadata[SOURCE_MESH_REF_METADATA_KEY] == "mesh-1"
    assert MESH_BINDING_METADATA_KEY in metadata
    binding = result_mesh_binding_from_metadata(metadata)
    assert binding is not None
    assert binding.mesh_ref == "mesh-1"
    assert binding.result_dataset_id == "dataset-1"
    assert binding.field_id == "temperature"


def test_project_yaml_round_trip(tmp_path: Path) -> None:
    pytest.importorskip("yaml")
    project = _sample_project()
    path = tmp_path / "project.osw.yaml"

    project.save(path)
    loaded = Project.load(path)

    assert loaded == project
    assert "schema_version" in path.read_text(encoding="utf-8")


def test_invalid_yaml_raises_friendly_schema_error(tmp_path: Path) -> None:
    pytest.importorskip("yaml")
    path = tmp_path / "broken.osw.yaml"
    path.write_text("metadata: [unterminated\n", encoding="utf-8")

    with pytest.raises(ProjectSchemaError, match="Could not parse project file"):
        Project.load(path)


def test_project_validation_reports_friendly_errors() -> None:
    project = Project.from_dict(
        {
            "schema_version": "0.1",
            "metadata": {"name": ""},
            "units": UnitSystem.si().to_dict(),
            "materials": [{"material_id": "", "name": ""}],
        }
    )

    report = project.validate()

    assert report.has_errors
    assert any("Project metadata name is required." in item.message for item in report.messages)
    assert any("Material id is required." in item.message for item in report.messages)


def test_project_migration_adds_default_legacy_schema_version() -> None:
    project = Project.from_dict(
        {
            "metadata": {"name": "legacy"},
            "unit_system": UnitSystem.si().to_dict(),
        }
    )

    assert project.schema_version == "0.1"
    assert project.units == UnitSystem.si()


def test_project_schema_versions_keep_feature_unused_projects_at_0_1() -> None:
    assert LEGACY_PROJECT_SCHEMA_VERSION == "0.1"
    assert DEFAULT_PROJECT_SCHEMA_VERSION == "0.1"
    assert PATH_KIND_PROJECT_SCHEMA_VERSION == "0.2"
    assert CURRENT_SCHEMA_VERSION == "0.2"
    assert SUPPORTED_PROJECT_SCHEMA_VERSIONS == frozenset({"0.1", "0.2"})
    assert Project(metadata=ProjectMetadata(name="default")).schema_version == "0.1"


@pytest.mark.parametrize("legacy_version", [None, "0.0"])
def test_missing_and_0_0_schema_versions_still_migrate_to_0_1(
    legacy_version: str | None,
) -> None:
    payload: dict[str, object] = {"metadata": {"name": "legacy"}}
    if legacy_version is not None:
        payload["schema_version"] = legacy_version

    project = Project.from_dict(payload)

    assert project.schema_version == "0.1"


def test_demo_project_matches_heatsink_flow_visual_data() -> None:
    project = create_heatsink_flow_demo_project()

    assert project.metadata.name == "HeatSink_Flow"
    assert project.schema_version == "0.1"
    assert [item.name for item in project.geometry_refs] == [
        "heatsink.step",
        "enclosure.stp",
        "fluid_domain.csg",
    ]
    assert [item.name for item in project.mesh_refs] == ["mesh.msh", "mesh_stats.txt"]
    assert [item.name for item in project.script_refs] == [
        "preprocess.m",
        "run_case.m",
        "postprocess.m",
    ]
    assert {item.name for item in project.result_refs} >= {
        "run_0001",
        "fields.ex2",
        "residuals.dat",
        "monitor.log",
        "run_0000 (baseline)",
    }
    assert project.report.title == "HeatSink_Flow Simulation Report"
    assert project.report.run_label == "Run 0001"
    assert project.report.sections == ["Overview", "Key Results", "Summary"]


def test_demo_project_boundary_rows_and_solver_settings_match_gui_mock() -> None:
    project = create_heatsink_flow_demo_project()
    assert project.primary_physics is not None

    rows = [
        (item.name, item.type, item.value)
        for item in project.primary_physics.boundary_conditions
    ]

    assert rows == [
        ("inlet", "Velocity Inlet", "3.0 m/s"),
        ("outlet", "Pressure Outlet", "0 Pa"),
        ("wall_heatsink", "Wall (No Slip)", "—"),
        ("base_bottom", "Heat Flux", "1.0e5 W/m²"),
        ("symmetry", "Symmetry", "—"),
    ]
    assert project.solver_config is not None
    assert project.solver_config.solver == "chtSolver"
    assert project.solver_config.time_scheme == "Steady-State"
    assert project.solver_config.linear_solver == "GMRES"
    assert project.solver_config.preconditioner == "AMG"
    assert float(project.solver_config.convergence_tolerance) == pytest.approx(1.0e-6)


def test_script_refs_default_to_safe_preview_for_m_files() -> None:
    script = ScriptRef(id="script", path="scripts/run_case.m", language="matlab_octave")

    assert script.safe_preview_required is True


def test_project_validation_warns_when_mscript_preview_metadata_is_missing() -> None:
    project = Project(
        metadata=ProjectMetadata(name="script warning"),
        scripts=[ScriptRef(id="script", path="scripts/run_case.m", language="matlab_octave")],
        results=[ResultRef(ref_id="result-1", path="results/preview.json", kind="dataset")],
    )

    report = validate_project(project)

    assert report.has_warnings
    assert any("has not been previewed" in item.message for item in report.messages)


def test_project_validation_warns_for_high_risk_mscript_findings() -> None:
    script = ScriptRef(
        id="script",
        path="scripts/run_case.m",
        language="matlab_octave",
        metadata={
            "kind": "script",
            "safety_summary": "blocked=0, high=1, warnings=0",
            "safety_findings": [
                {
                    "severity": "high",
                    "token": "system",
                    "message": "External command token detected.",
                }
            ],
        },
    )
    project = Project(
        metadata=ProjectMetadata(name="script warning"),
        scripts=[script],
        results=[ResultRef(ref_id="result-1", path="results/preview.json", kind="dataset")],
    )

    report = validate_project(project)

    assert report.has_warnings
    assert any("high-risk or blocked" in item.message for item in report.messages)


def test_project_validation_warns_when_mat_preview_metadata_is_missing() -> None:
    project = Project(
        metadata=ProjectMetadata(name="mat warning"),
        scripts=[ScriptRef(id="mat-data", path="scripts/data.mat", language="matlab_mat")],
        results=[ResultRef(ref_id="result-1", path="results/preview.json", kind="dataset")],
    )

    report = validate_project(project)

    assert report.has_warnings
    assert any(
        "MAT data reference has no variable summary" in item.message
        for item in report.messages
    )


def test_project_validation_warns_for_native_commercial_cad_extension() -> None:
    project = Project(
        metadata=ProjectMetadata(name="native cad warning"),
        geometry=[GeometryRef(id="native", path="geometry/part.sldprt", format="SLDPRT")],
    )

    report = validate_project(project)

    assert report.has_warnings
    assert any("native commercial CAD direct import" in item.message for item in report.messages)


def test_project_validation_warns_for_native_commercial_mesh_path() -> None:
    project = Project(
        metadata=ProjectMetadata(name="native mesh warning"),
        meshes=[MeshRef(id="native", path="mesh/native_part.sldprt", format="SLDPRT")],
        results=[ResultRef(ref_id="result-1", path="results/preview.json", kind="dataset")],
    )

    report = validate_project(project)

    assert report.has_warnings
    assert any("standard/exported CAD and mesh formats" in item.message for item in report.messages)


def test_boundary_condition_accepts_project_schema_fields() -> None:
    boundary = BoundaryCondition(
        name="inlet",
        type="Velocity Inlet",
        value="3.0 m/s",
        unit="m/s",
        target="inlet",
    )

    assert boundary.kind == "Velocity Inlet"
    assert boundary.to_dict()["value"] == "3.0 m/s"


def _screenshot_asset(asset_id: str = "shot-1") -> ReportScreenshotAsset:
    return ReportScreenshotAsset(
        id=asset_id,
        path="scenes/iso.png",
        caption="Iso view",
        mesh_ref="mesh-1",
        result_dataset_ref="rd-1",
        field_id="temperature",
        selection_ids=("sel-a",),
        scene_state={"camera": {"view_preset": "iso"}},
        glyph_options={"enabled": True, "vector_field": "U"},
        metadata={"created_by": "mesh-viewer"},
    )


def test_report_screenshot_asset_serializes_deterministically() -> None:
    asset = _screenshot_asset()

    loaded = ReportScreenshotAsset.from_dict(asset.to_dict())

    assert loaded == asset
    # Persisted screenshots are never release assets or validation evidence.
    assert asset.metadata["is_release_asset"] is False
    assert asset.metadata["is_validation_evidence"] is False
    assert asset.metadata["artifact_caveat"] == REPORT_SCREENSHOT_ASSET_CAVEAT
    # Caveat flags are forced even if a payload claims otherwise.
    tampered = asset.to_dict()
    tampered["metadata"]["is_release_asset"] = True
    assert ReportScreenshotAsset.from_dict(tampered).metadata["is_release_asset"] is False


@pytest.mark.parametrize(
    ("path_kind", "path"),
    [
        (ReportAssetPathKind.LEGACY_RAW, "legacy/../scene.png"),
        (ReportAssetPathKind.EXTERNAL_ABSOLUTE, "C:/captures/scene.png"),
        (ReportAssetPathKind.PROJECT_RELATIVE, "screenshots/scene.png"),
    ],
)
def test_report_screenshot_explicit_path_kinds_round_trip_exactly(
    path_kind: ReportAssetPathKind,
    path: str,
) -> None:
    asset = ReportScreenshotAsset(id="shot-typed", path=path, path_kind=path_kind)

    payload = asset.to_dict()
    restored = ReportScreenshotAsset.from_dict(payload)

    assert asset.path == path
    assert asset.path_kind is path_kind
    assert payload["path"] == path
    assert payload["path_kind"] == path_kind.value
    assert restored == asset


def test_report_screenshot_omitted_and_explicit_legacy_remain_distinct() -> None:
    omitted = ReportScreenshotAsset(id="omitted", path="screenshots/scene.png")
    explicit = ReportScreenshotAsset(
        id="explicit",
        path="screenshots/scene.png",
        path_kind=ReportAssetPathKind.LEGACY_RAW,
    )

    assert omitted.path_kind is None
    assert "path_kind" not in omitted.to_dict()
    assert explicit.path_kind is ReportAssetPathKind.LEGACY_RAW
    assert explicit.to_dict()["path_kind"] == "legacy_raw"


def test_report_screenshot_path_kind_does_not_shift_legacy_positional_arguments() -> None:
    asset = ReportScreenshotAsset("shot", "scene_screenshot", "legacy.png", "Caption")

    assert asset.path == "legacy.png"
    assert asset.caption == "Caption"
    assert asset.path_kind is None


def test_caption_replacement_preserves_explicit_path_kind() -> None:
    asset = ReportScreenshotAsset(
        id="shot",
        path="screenshots/scene.png",
        caption="Before",
        path_kind=ReportAssetPathKind.PROJECT_RELATIVE,
    )

    edited = replace(asset, caption="After")

    assert edited.caption == "After"
    assert edited.path == asset.path
    assert edited.path_kind is ReportAssetPathKind.PROJECT_RELATIVE


@pytest.mark.parametrize(
    "bad_kind",
    ["", "unknown", "EXTERNAL_ABSOLUTE", " external_absolute", None, True, 1, [], {}],
)
def test_report_screenshot_explicit_path_kind_rejects_malformed_values(
    bad_kind: object,
) -> None:
    payload = ReportScreenshotAsset(id="shot", path="legacy.png").to_dict()
    payload["path_kind"] = bad_kind

    with pytest.raises((TypeError, ValueError), match="path_kind"):
        ReportScreenshotAsset.from_dict(payload)


def test_report_screenshot_reserved_managed_kind_is_rejected() -> None:
    with pytest.raises(ValueError, match="reserved"):
        ReportScreenshotAsset(
            id="shot",
            path="report-assets/scene.png",
            path_kind=ReportAssetPathKind.MANAGED_PROJECT_ASSET,
        )


@pytest.mark.parametrize("bad_path", [None, True, 7, [], {}, "", "   "])
def test_report_screenshot_explicit_paths_reject_non_strings_and_blanks(
    bad_path: object,
) -> None:
    with pytest.raises((TypeError, ValueError), match="path"):
        ReportScreenshotAsset(
            id="shot",
            path=bad_path,  # type: ignore[arg-type]
            path_kind=ReportAssetPathKind.LEGACY_RAW,
        )


@pytest.mark.parametrize("bad_path", [None, True, 7, [], {}, "", "   "])
def test_report_screenshot_from_dict_does_not_coerce_malformed_explicit_paths(
    bad_path: object,
) -> None:
    payload = {
        "id": "shot",
        "path": bad_path,
        "path_kind": "legacy_raw",
    }

    with pytest.raises((TypeError, ValueError), match="path"):
        ReportScreenshotAsset.from_dict(payload)


@pytest.mark.parametrize(
    "path",
    [
        "captures/scene.png",
        "C:captures/scene.png",
        r"\captures\scene.png",
        "https://example.invalid/scene.png",
        r"\\?\C:\captures\scene.png",
        r"\\.\C:\captures\scene.png",
    ],
)
def test_external_absolute_rejects_non_absolute_uri_and_device_paths(path: str) -> None:
    with pytest.raises(ValueError, match="external_absolute"):
        ReportScreenshotAsset(
            id="shot",
            path=path,
            path_kind=ReportAssetPathKind.EXTERNAL_ABSOLUTE,
        )


@pytest.mark.parametrize(
    "path",
    [
        "/captures/scene.png",
        "C:/captures/scene.png",
        "//server/share/scene.png",
        r"\\?\C:\captures\scene.png",
        "https://example.invalid/scene.png",
        r"screenshots\scene.png",
        "screenshots/\x01scene.png",
        "screenshots/\x85scene.png",
        "",
        ".",
        "..",
        "screenshots/./scene.png",
        "screenshots/../scene.png",
        "screenshots//scene.png",
        "screenshots/scene.png/",
    ],
)
def test_project_relative_rejects_noncanonical_or_unsafe_paths(path: str) -> None:
    with pytest.raises(ValueError, match="project_relative"):
        ReportScreenshotAsset(
            id="shot",
            path=path,
            path_kind=ReportAssetPathKind.PROJECT_RELATIVE,
        )


@pytest.mark.parametrize(
    "path",
    ["C:/captures/scene.png", "/var/tmp/scene.png", r"\\server\share\scene.png"],
)
def test_external_absolute_accepts_windows_posix_and_network_lexical_paths(path: str) -> None:
    asset = ReportScreenshotAsset(
        id="shot",
        path=path,
        path_kind=ReportAssetPathKind.EXTERNAL_ABSOLUTE,
    )

    assert asset.path == path


def test_explicit_path_parsing_performs_no_filesystem_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_io(*args: object, **kwargs: object) -> object:
        raise AssertionError("explicit path parsing must remain lexical")

    for method_name in (
        "exists",
        "is_file",
        "stat",
        "resolve",
        "absolute",
        "read_text",
        "read_bytes",
    ):
        monkeypatch.setattr(Path, method_name, unexpected_io)
    monkeypatch.setattr(os.path, "realpath", unexpected_io)

    external = ReportScreenshotAsset.from_dict(
        {
            "id": "external",
            "path": "Z:/foreign/scene.png",
            "path_kind": "external_absolute",
        }
    )
    relative = ReportScreenshotAsset.from_dict(
        {
            "id": "relative",
            "path": "screenshots/scene.png",
            "path_kind": "project_relative",
        }
    )

    assert external.path_kind is ReportAssetPathKind.EXTERNAL_ABSOLUTE
    assert relative.path_kind is ReportAssetPathKind.PROJECT_RELATIVE


def test_project_report_screenshots_round_trip() -> None:
    project = Project(
        metadata=ProjectMetadata(name="Report assets"),
        report_screenshots=[_screenshot_asset("shot-1"), _screenshot_asset("shot-2")],
    )

    loaded = Project.from_dict(project.to_dict())

    assert loaded.report_screenshots == project.report_screenshots
    assert [asset.id for asset in loaded.report_screenshots] == ["shot-1", "shot-2"]
    assert loaded.report_screenshots[0].caption == "Iso view"
    assert loaded.report_screenshots[0].mesh_ref == "mesh-1"


def test_project_0_2_loads_each_explicit_kind_and_mixed_legacy_records() -> None:
    payload = {
        "schema_version": "0.2",
        "metadata": {"name": "Typed paths"},
        "report_screenshots": [
            {"id": "omitted", "path": "legacy.png"},
            {"id": "legacy", "path": "legacy.png", "path_kind": "legacy_raw"},
            {
                "id": "external",
                "path": "C:/captures/scene.png",
                "path_kind": "external_absolute",
            },
            {
                "id": "relative",
                "path": "screenshots/scene.png",
                "path_kind": "project_relative",
            },
        ],
    }

    project = Project.from_dict(payload)
    serialized = project.to_dict()

    assert project.schema_version == "0.2"
    assert [asset.path_kind for asset in project.report_screenshots] == [
        None,
        ReportAssetPathKind.LEGACY_RAW,
        ReportAssetPathKind.EXTERNAL_ABSOLUTE,
        ReportAssetPathKind.PROJECT_RELATIVE,
    ]
    assert "path_kind" not in serialized["report_screenshots"][0]
    assert serialized["report_screenshots"][1]["path_kind"] == "legacy_raw"


@pytest.mark.parametrize("marker", [None, "legacy_raw", "project_relative"])
def test_project_0_1_rejects_any_explicit_path_kind_key(marker: object) -> None:
    payload = {
        "schema_version": "0.1",
        "metadata": {"name": "Invalid envelope"},
        "report_screenshots": [
            {"id": "shot", "path": "screenshots/scene.png", "path_kind": marker}
        ],
    }

    with pytest.raises(ProjectSchemaError, match="schema version 0.2"):
        Project.from_dict(payload)


def test_constructed_0_1_project_cannot_contain_or_serialize_marked_assets() -> None:
    marked = ReportScreenshotAsset(
        id="shot",
        path="screenshots/scene.png",
        path_kind=ReportAssetPathKind.PROJECT_RELATIVE,
    )

    with pytest.raises(ProjectSchemaError, match="schema version 0.2"):
        Project(
            metadata=ProjectMetadata(name="Invalid"),
            schema_version="0.1",
            report_screenshots=[marked],
        )

    mutated = Project(metadata=ProjectMetadata(name="Mutated"))
    mutated.report_screenshots.append(marked)
    with pytest.raises(ProjectSchemaError, match="schema version 0.2"):
        mutated.to_dict()


def test_project_0_2_with_deleted_marker_remains_0_2_legacy_raw() -> None:
    project = Project.from_dict(
        {
            "schema_version": "0.2",
            "metadata": {"name": "Unsigned marker gap"},
            "report_screenshots": [{"id": "shot", "path": "screenshots/scene.png"}],
        }
    )

    assert project.schema_version == "0.2"
    assert project.report_screenshots[0].path_kind is None
    assert "path_kind" not in project.to_dict()["report_screenshots"][0]


def test_unsupported_project_version_rejects_before_nested_asset_parsing() -> None:
    with pytest.raises(ProjectSchemaError, match="Unsupported.*9.9") as exc_info:
        Project.from_dict(
            {
                "schema_version": "9.9",
                "metadata": {"name": "Future"},
                "report_screenshots": [42],
            }
        )

    assert "ReportScreenshotAsset" not in str(exc_info.value)


@pytest.mark.parametrize(
    ("generation", "provenance", "source"),
    [
        (
            "R0",
            "db05475785a12a00d60476110b6ee9cd8574fe05",
            _HISTORICAL_R0_VERSION_GATE_SOURCE,
        ),
        (
            "R1",
            "edf62ec521845d484d231a7d1b034e2c99e60d70",
            _HISTORICAL_R1_VERSION_GATE_SOURCE,
        ),
    ],
    ids=("r0", "r1"),
)
def test_frozen_historical_reader_rejects_0_2_before_screenshot_consumption(
    generation: str,
    provenance: str,
    source: str,
) -> None:
    assert generation in {"R0", "R1"}
    assert len(provenance) == 40
    assert "Project.from_dict" not in source
    assert "import " not in source
    assert "__import__" not in source
    assert "subprocess" not in source
    assert "socket" not in source
    reader = _load_frozen_historical_reader(source)
    assert callable(reader)
    assert "Project" not in reader.__globals__
    sentinel = _NestedScreenshotPathSentinel()
    payload = {
        "schema_version": "0.2",
        "metadata": {"name": f"Historical {generation}"},
        "report_screenshots": sentinel,
    }

    with pytest.raises(
        _FrozenHistoricalProjectSchemaError,
        match="Unsupported.*0.2",
    ) as exc_info:
        reader(payload)

    assert type(exc_info.value) is _FrozenHistoricalProjectSchemaError
    assert str(exc_info.value) == "Unsupported OSW project schema version: 0.2"
    assert sentinel.access_count == 0


def test_project_without_report_screenshots_is_byte_identical() -> None:
    project = Project(metadata=ProjectMetadata(name="No assets"))
    payload = project.to_dict()

    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    expected = (
        b'{"boundary_curves":[],"geometry":[],"geometry_refs":[],"materials":[],'
        b'"mesh_refs":[],"meshes":[],"metadata":{"author":"","created_at":"",'
        b'"description":"","modified_at":"","name":"No assets","tags":[]},'
        b'"physics":[],"plugins":[],"report":{"artifacts":[],"export_formats":["html"],'
        b'"include_figures":true,"include_tables":true,"include_validation":true,'
        b'"include_warnings":true,"path":"reports/report.html","run_label":"",'
        b'"sections":[],"title":"OSW Report"},"result_refs":[],"results":[],'
        b'"schema_version":"0.1","script_refs":[],"scripts":[],"solvers":[],'
        b'"unit_system":{"amount":"mol","current":"A","energy":"J","force":"N",'
        b'"length":"m","mass":"kg","name":"SI","power":"W","pressure":"Pa",'
        b'"stress":"Pa","temperature":"K","time":"s"},"units":{"amount":"mol",'
        b'"current":"A","energy":"J","force":"N","length":"m","mass":"kg",'
        b'"name":"SI","power":"W","pressure":"Pa","stress":"Pa",'
        b'"temperature":"K","time":"s"},"warnings":[]}'
    )

    assert serialized == expected
    assert "report_screenshots" not in payload
    assert project.schema_version == "0.1"
    assert project.report_screenshots == []


def test_project_with_unmarked_report_screenshot_is_byte_identical() -> None:
    project = Project(
        metadata=ProjectMetadata(name="Legacy asset"),
        report_screenshots=[
            ReportScreenshotAsset(id="shot-1", path="screenshots/scene.png")
        ],
    )

    serialized = json.dumps(
        project.to_dict(), sort_keys=True, separators=(",", ":")
    ).encode()
    expected = (
        b'{"boundary_curves":[],"geometry":[],"geometry_refs":[],"materials":[],'
        b'"mesh_refs":[],"meshes":[],"metadata":{"author":"","created_at":"",'
        b'"description":"","modified_at":"","name":"Legacy asset","tags":[]},'
        b'"physics":[],"plugins":[],"report":{"artifacts":[],"export_formats":["html"],'
        b'"include_figures":true,"include_tables":true,"include_validation":true,'
        b'"include_warnings":true,"path":"reports/report.html","run_label":"",'
        b'"sections":[],"title":"OSW Report"},"report_screenshots":[{"caption":"",'
        b'"diagnostics":[],"field_id":"","glyph_options":{},"id":"shot-1",'
        b'"kind":"scene_screenshot","mesh_ref":"","metadata":{"artifact_caveat":'
        b'"Persisted scene screenshot assets store local paths only; they are not '
        b'validation evidence or release assets.","is_release_asset":false,'
        b'"is_validation_evidence":false},"path":"screenshots/scene.png",'
        b'"result_dataset_ref":"","scene_state":{},"selection_ids":[]}],'
        b'"result_refs":[],"results":[],"schema_version":"0.1","script_refs":[],'
        b'"scripts":[],"solvers":[],"unit_system":{"amount":"mol","current":"A",'
        b'"energy":"J","force":"N","length":"m","mass":"kg","name":"SI",'
        b'"power":"W","pressure":"Pa","stress":"Pa","temperature":"K",'
        b'"time":"s"},"units":{"amount":"mol","current":"A","energy":"J",'
        b'"force":"N","length":"m","mass":"kg","name":"SI","power":"W",'
        b'"pressure":"Pa","stress":"Pa","temperature":"K","time":"s"},'
        b'"warnings":[]}'
    )

    assert serialized == expected
    assert b'"path":"screenshots/scene.png"' in serialized
    assert b'"path_kind"' not in serialized


def test_old_project_without_report_screenshots_field_loads() -> None:
    payload = Project(metadata=ProjectMetadata(name="Legacy")).to_dict()
    payload.pop("report_screenshots", None)  # simulate a pre-field project file

    loaded = Project.from_dict(payload)

    assert loaded.report_screenshots == []
    assert loaded.schema_version == "0.1"


def test_report_screenshots_do_not_bump_schema_version() -> None:
    project = Project(
        metadata=ProjectMetadata(name="Report assets"),
        report_screenshots=[_screenshot_asset()],
    )

    assert project.schema_version == "0.1"
    assert project.to_dict()["schema_version"] == "0.1"


def test_core_report_asset_module_is_post_and_render_free() -> None:
    import osw.core.report_asset as module

    source = Path(module.__file__).read_text(encoding="utf-8")
    for banned in (
        "import osw.post",
        "from osw.post",
        "import osw.gui",
        "from osw.gui",
        "PySide6",
        "import pyvista",
        "import vtk",
        "import meshio",
        "import gmsh",
        "import cantera",
        "import CoolProp",
        "import matplotlib",
        "subprocess",
    ):
        assert banned not in source
