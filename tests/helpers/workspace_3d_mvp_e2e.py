"""Shared 3D Workspace MVP end-to-end fixture builders and journey helpers."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import zlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from osw.core.materials import IsotropicElastic, Material
from osw.core.project_io import load_project, save_project
from osw.core.project_schema import (
    PhysicsSetup,
    Project,
    ProjectMetadata,
    ResultRef,
    project_with,
)
from osw.core.report_asset import ReportAssetPathKind
from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.core.result_mesh_binding import (
    RESULT_MESH_BINDING_SCHEMA_V2,
    ResultMeshBinding,
    ResultMeshSignature,
)
from osw.core.selection import EntityKind, EntityLocator, NamedSelection, SelectionTargetRef
from osw.core.selection_resolution import (
    CELL_ORDINAL_NAMESPACE,
    NODE_ORDINAL_NAMESPACE,
    create_named_selection,
)
from osw.core.solver_setup import (
    FixedSupportRecord,
    ForceLoadRecord,
    HeatFluxRecord,
    MaterialAssignmentRecord,
    PrescribedDisplacementRecord,
    PressureLoadRecord,
    SetupReadiness,
    SetupRecordKind,
    TemperatureRecord,
    evaluate_solver_setup,
)
from osw.core.solver_setup_handoff import build_solver_setup_handoff
from osw.core.units import Quantity
from osw.core.workspace_3d import (
    ACTIVE_SCENE_PROVENANCE_METADATA_KEY,
    ACTIVE_SCENE_SCHEMA,
    ActiveSceneCameraState,
    ActiveSceneRestoreStatus,
    ActiveSceneScreenshotRequest,
    ActiveSceneState,
    active_scene_state_digest,
)
from osw.gui.workspace_scene_controller import ActiveSceneController
from osw.gui.workspace_scene_view_model import mesh_input_ref, scene_view_state_from_toggles
from osw.mesh.identity import MESH_IDENTITY_SCHEMA, compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.mesh.quality import (
    MESH_QUALITY_METRIC_SCHEMA,
    analyze_mesh_cell_quality,
)
from osw.post.report_generator import build_report
from osw.post.report_model import (
    ReportBuildRequest,
    ReportFormat,
    report_assets_to_scene_screenshots,
    scene_screenshots_to_report_assets,
)
from osw.post.result_deformation import DeformationMode, DeformationScaleMode
from osw.post.result_probe import ResultProbeRequest
from osw.post.scene_model import SceneScreenshotRecord
from osw.solvers.calculix.adapter import prepare_solver_setup

MESH_REF = "mesh-mvp-e2e-complete"
PROJECT_NAME = "project-mvp-e2e-complete"
MATERIAL_ID = "material-steel"
RESULT_REF_ID = "result-ref-mvp-e2e"
RESULT_DATASET_ID = "result-dataset-mvp-e2e"
QUALITY_THRESHOLD = 0.3
VECTOR_SCALE = 1.5
VECTOR_MAX_COUNT = 4
DEFORMATION_MANUAL_SCALE = 2.0
CAPTURE_CAPTION = "MVP E2E captured scene"
STAGE_MANIFEST_NAME = "stage_manifest.json"
PROJECT_FILE_NAME = "project.osw.json"
CAPTURE_FILE_NAME = "scene-capture.png"
REPORT_HTML_NAME = "report.html"

NS_MATERIAL = "ns-material-cells"
NS_FIXED = "ns-fixed-points"
NS_FORCE = "ns-force-points"
NS_DISPLACEMENT = "ns-displacement-points"
NS_SURFACE = "ns-explicit-surface"
NS_THERMAL = "ns-thermal-points"
NS_PICKED_POINTS = "ns-picked-points"
NS_PICKED_CELLS = "ns-picked-cells"
NS_BAD = "ns-bad-elements"

SETUP_MATERIAL = "setup-material"
SETUP_FIXED = "setup-fixed"
SETUP_DISPLACEMENT = "setup-displacement"
SETUP_FORCE = "setup-force"
SETUP_PRESSURE = "setup-pressure"
SETUP_TEMPERATURE = "setup-temperature"
SETUP_HEAT_FLUX = "setup-heat-flux"

CALCULIX_SUPPORTED_KINDS = (
    SetupRecordKind.MATERIAL_REGION,
    SetupRecordKind.FIXED_SUPPORT,
    SetupRecordKind.PRESCRIBED_DISPLACEMENT,
    SetupRecordKind.FORCE,
)


def e2e_mesh(*, changed: bool = False) -> MeshData:
    """Mixed surface + linear tetra fixture with one flattened tetra."""

    point_x = 1.15 if changed else 1.0
    return MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (point_x, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
            (3.0, 0.0, 0.0),
            (4.0, 0.0, 0.0),
            (3.5, 0.8, 0.0),
            (3.5, 0.3, 0.02),
            (6.0, 0.0, 0.0),
            (7.0, 0.0, 0.0),
            (6.5, 1.0, 0.0),
            (9.0, 0.0, 0.0),
            (10.0, 0.0, 0.0),
            (10.0, 1.0, 0.0),
            (9.0, 1.0, 0.0),
            (12.0, 0.0, 0.0),
            (13.0, 0.2, 0.0),
            (12.8, 1.0, 0.0),
            (11.8, 0.6, 0.0),
        ),
        cells=(
            MeshCellBlock("triangle", ((8, 9, 10),)),
            MeshCellBlock("quad", ((11, 12, 13, 14),)),
            MeshCellBlock("polygon", ((15, 16, 17, 18),)),
            MeshCellBlock(
                "tetra",
                (
                    (0, 1, 2, 3),
                    (4, 5, 6, 7),
                ),
            ),
        ),
    )


def clone_e2e_mesh(mesh: MeshData) -> MeshData:
    return MeshData(points=mesh.points, cells=mesh.cells)


def mesh_snapshot(mesh: MeshData) -> tuple[object, object]:
    return (
        mesh.points,
        tuple((block.cell_type, block.data) for block in mesh.cells),
    )


def e2e_material() -> Material:
    return Material(
        MATERIAL_ID,
        "Steel",
        elastic=IsotropicElastic(Quantity(210e9, "Pa"), 0.3),
    )


def _rows(
    values: Sequence[Sequence[float]],
    components: Sequence[str],
) -> tuple[ResultRow, ...]:
    return tuple(
        ResultRow(index, dict(zip(components, value, strict=True)))
        for index, value in enumerate(values)
    )


def e2e_result_dataset(mesh: MeshData) -> ResultDataset:
    point_count = len(mesh.points)
    cell_count = sum(block.count for block in mesh.cells)
    temperatures = tuple((300.0 + 2.0 * index,) for index in range(point_count))
    displacements = tuple(
        (0.01 * index, 0.0 if index % 2 else 0.02, 0.0) for index in range(point_count)
    )
    point_vectors = tuple(
        (float(index), 0.0, 1.0 if index else 0.0) for index in range(point_count)
    )
    cell_scalars = tuple((10.0 + index,) for index in range(cell_count))
    cell_vectors = tuple((1.0, float(index), 0.0) for index in range(cell_count))
    return ResultDataset(
        dataset_id=RESULT_DATASET_ID,
        source="mvp-e2e-fixture",
        solver="fixture",
        analysis_type="static",
        fields=(
            ResultField(
                "temperature",
                "point",
                ("value",),
                _rows(temperatures, ("value",)),
                "K",
            ),
            ResultField(
                "cell_stress",
                "cell",
                ("value",),
                _rows(cell_scalars, ("value",)),
                "Pa",
            ),
            ResultField(
                "velocity",
                "point",
                ("vx", "vy", "vz"),
                _rows(point_vectors, ("vx", "vy", "vz")),
                "mm/s",
            ),
            ResultField(
                "cell_flux",
                "cell",
                ("fx", "fy", "fz"),
                _rows(cell_vectors, ("fx", "fy", "fz")),
                "W/m^2",
            ),
            ResultField(
                "displacement",
                "point",
                ("ux", "uy", "uz"),
                _rows(displacements, ("ux", "uy", "uz")),
                "mm",
            ),
        ),
        metadata={
            "mesh_ref": MESH_REF,
            "mesh_length_unit": "mm",
            "field_semantics": {
                "displacement": {
                    "semantic_role": "displacement",
                    "quantity_dimension": "length",
                    "coordinate_system": "global_cartesian",
                }
            },
        },
    )


def e2e_result_binding(mesh: MeshData) -> ResultMeshBinding:
    fingerprint = compute_mesh_fingerprint(mesh)
    return ResultMeshBinding(
        mesh_ref=MESH_REF,
        result_dataset_id=RESULT_DATASET_ID,
        schema=RESULT_MESH_BINDING_SCHEMA_V2,
        field_id="temperature",
        mesh_identity_schema=MESH_IDENTITY_SCHEMA,
        mesh_fingerprint=fingerprint.digest,
        mesh_signature=ResultMeshSignature(
            node_count=len(mesh.points),
            cell_count=sum(block.count for block in mesh.cells),
        ),
    )


def _selection(
    mesh: MeshData,
    *,
    selection_id: str,
    name: str,
    kind: EntityKind,
    entity_ids: tuple[int | str, ...],
) -> NamedSelection:
    fingerprint = compute_mesh_fingerprint(mesh)
    namespace = NODE_ORDINAL_NAMESPACE if kind is EntityKind.NODE else CELL_ORDINAL_NAMESPACE
    locator = EntityLocator(
        fingerprint.schema,
        MESH_REF,
        fingerprint.digest,
        kind,
        namespace,
        entity_ids,
    )
    return NamedSelection(
        selection_id,
        name,
        entity_kind=kind,
        targets=(SelectionTargetRef(kind, entity_ids, MESH_REF, locator=locator),),
        source_mesh_ref=MESH_REF,
    )


def setup_named_selections(mesh: MeshData) -> tuple[NamedSelection, ...]:
    return (
        _selection(
            mesh,
            selection_id=NS_MATERIAL,
            name="Material Cells",
            kind=EntityKind.CELL,
            entity_ids=("3:0",),
        ),
        _selection(
            mesh,
            selection_id=NS_FIXED,
            name="Fixed Points",
            kind=EntityKind.NODE,
            entity_ids=(0,),
        ),
        _selection(
            mesh,
            selection_id=NS_FORCE,
            name="Force Points",
            kind=EntityKind.NODE,
            entity_ids=(1,),
        ),
        _selection(
            mesh,
            selection_id=NS_DISPLACEMENT,
            name="Displacement Points",
            kind=EntityKind.NODE,
            entity_ids=(2,),
        ),
        _selection(
            mesh,
            selection_id=NS_SURFACE,
            name="Explicit Surface",
            kind=EntityKind.CELL,
            entity_ids=("0:0",),
        ),
        _selection(
            mesh,
            selection_id=NS_THERMAL,
            name="Thermal Points",
            kind=EntityKind.NODE,
            entity_ids=(8,),
        ),
    )


def e2e_physics_setup() -> PhysicsSetup:
    return PhysicsSetup(
        setup_id="structural",
        name="MVP E2E Setup",
        analysis_type="linear_static",
        domain="STRUCTURAL",
        material_assignment_records=[
            MaterialAssignmentRecord(SETUP_MATERIAL, "Steel region", MATERIAL_ID, NS_MATERIAL)
        ],
        fixed_support_records=[
            FixedSupportRecord(SETUP_FIXED, "Fixed support", NS_FIXED, (1, 2, 3))
        ],
        prescribed_displacement_records=[
            PrescribedDisplacementRecord(
                SETUP_DISPLACEMENT,
                "Prescribed displacement",
                NS_DISPLACEMENT,
                ux=Quantity(0.001, "m"),
            )
        ],
        force_load_records=[
            ForceLoadRecord(
                SETUP_FORCE,
                "Force",
                NS_FORCE,
                Quantity(100.0, "N"),
                (1.0, 0.0, 0.0),
                coordinate_system="GLOBAL",
                application_mode="PER_NODE",
            )
        ],
        pressure_load_records=[
            PressureLoadRecord(SETUP_PRESSURE, "Pressure", NS_SURFACE, Quantity(2.0, "Pa"))
        ],
        temperature_records=[
            TemperatureRecord(
                SETUP_TEMPERATURE,
                "Temperature",
                NS_THERMAL,
                Quantity(300.0, "K"),
            )
        ],
        heat_flux_records=[
            HeatFluxRecord(SETUP_HEAT_FLUX, "Heat flux", NS_SURFACE, Quantity(-4.0, "W/m^2"))
        ],
    )


def empty_e2e_project() -> Project:
    return Project(
        metadata=ProjectMetadata(name=PROJECT_NAME),
        schema_version="0.4",
    )


def authored_e2e_project(mesh: MeshData) -> Project:
    binding = e2e_result_binding(mesh)
    return Project(
        metadata=ProjectMetadata(name=PROJECT_NAME),
        materials=(e2e_material(),),
        physics=e2e_physics_setup(),
        results=(
            ResultRef(
                id=RESULT_REF_ID,
                name="MVP E2E result",
                metadata={
                    "result_dataset_id": RESULT_DATASET_ID,
                    "mesh_binding": binding.to_dict(),
                },
            ),
        ),
        selections=setup_named_selections(mesh),
        schema_version="0.4",
    )


class FixtureScaledJacobianProvider:
    provider_schema = "osw.mesh_quality.provider.mvp-e2e-fixture.v1"
    provider_version = "1"

    def evaluate(self, mesh: MeshData) -> tuple[float, ...]:
        values: list[float] = []
        for block in mesh.cells:
            cell_type = str(block.cell_type or "").strip().lower()
            if cell_type not in {"triangle", "quad", "tetra"}:
                continue
            for connectivity in block.data:
                if cell_type == "tetra" and connectivity == (4, 5, 6, 7):
                    values.append(0.05)
                elif cell_type == "tetra":
                    values.append(0.90)
                elif cell_type == "quad":
                    values.append(0.80)
                else:
                    values.append(0.85)
        return tuple(values)


def fixture_quality_analyzer(mesh: MeshData, **kwargs: object) -> object:
    return analyze_mesh_cell_quality(
        mesh,
        provider=FixtureScaledJacobianProvider(),
        **kwargs,
    )


def write_nonblank_png(path: Path, *, width: int = 16, height: int = 12) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    raw = bytearray()
    for row in range(height):
        raw.append(0)
        for column in range(width):
            raw.extend((min(255, 48 + column * 12), min(255, 32 + row * 14), 200, 255))
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(payload)
    return payload


def png_signature_and_size(image_bytes: bytes) -> tuple[bool, tuple[int, int] | None]:
    if (
        len(image_bytes) < 24
        or not image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        or image_bytes[12:16] != b"IHDR"
    ):
        return False, None
    width, height = struct.unpack(">II", image_bytes[16:24])
    if width <= 0 or height <= 0:
        return True, None
    return True, (width, height)


def png_is_nonblank(image_bytes: bytes) -> bool:
    signature_ok, size = png_signature_and_size(image_bytes)
    if not signature_ok or size is None:
        return False
    width, height = size
    offset = 8
    data = bytearray()
    while offset + 12 <= len(image_bytes):
        length = struct.unpack(">I", image_bytes[offset : offset + 4])[0]
        tag = image_bytes[offset + 4 : offset + 8]
        chunk = image_bytes[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if tag == b"IDAT":
            data.extend(chunk)
        elif tag == b"IEND":
            break
    pixels = zlib.decompress(bytes(data))
    stride = 1 + width * 4
    colors: set[tuple[int, int, int]] = set()
    for row in range(height):
        start = row * stride + 1
        row_bytes = pixels[start : start + width * 4]
        for column in range(width):
            index = column * 4
            colors.add((row_bytes[index], row_bytes[index + 1], row_bytes[index + 2]))
            if len(colors) > 1:
                return True
    return False


def provenance_has_absolute_path(payload: Mapping[str, Any], workspace: Path) -> bool:
    text = json.dumps(payload, default=str)
    workspace_text = str(workspace.resolve())
    if workspace_text in text:
        return True
    if ":\\" in text or text.count("/") > 8:
        for token in text.replace("\\", "/").split('"'):
            if len(token) >= 3 and token[1:3] == ":/" and token[0].isalpha():
                return True
    return False


@dataclass
class ActionCounters:
    solver_calls: int = 0
    runner_calls: int = 0
    solver_subprocess_calls: int = 0
    automatic_saves: int = 0
    automatic_captures: int = 0
    automatic_exports: int = 0
    automatic_relinks: int = 0
    explicit_saves: int = 0
    explicit_captures: int = 0
    explicit_exports: int = 0
    test_harness_processes: int = 0
    network_calls: int = 0


class RecordingSceneSession:
    backend_kind = "fake-mvp-e2e"
    capabilities = frozenset(
        {
            "axes",
            "camera",
            "clipping",
            "hosted-widget",
            "interactive",
            "interactive-results",
            "mesh-preview",
            "mesh-quality-overlays",
            "picking",
            "representation",
            "result-overlays",
            "scene-screenshot",
            "selection-overlays",
            "semantic-actors",
            "semantic-visibility",
            "setup-overlays",
        }
    )

    def __init__(self) -> None:
        self.widget = SimpleNamespace(objectName="fake-mvp-e2e")
        self.actors: dict[str, object] = {}
        self.visibility: dict[str, bool] = {}
        self.named_overlays: dict[str, tuple[str, tuple[object, ...], int]] = {}
        self.calls: list[tuple[object, ...]] = []
        self.pick_callback: object | None = None
        self.base_load_count = 0
        self.capture_count = 0
        self.close_count = 0
        self.camera = ActiveSceneCameraState(
            position=(8.0, 6.0, 5.0),
            focal_point=(6.0, 0.4, 0.3),
            view_up=(0.0, 0.0, 1.0),
            view_preset="isometric",
        )
        self.applied_cameras: list[ActiveSceneCameraState] = []

    @property
    def hosted_widget(self) -> object:
        return self.widget

    def clear(self) -> None:
        self.actors.clear()
        self.visibility.clear()
        self.named_overlays.clear()

    def replace_actor(
        self,
        semantic_id: str,
        payload: object,
        *,
        generation: int,
    ) -> object:
        if semantic_id == "base_mesh":
            self.base_load_count += 1
        self.actors[semantic_id] = payload
        self.visibility[semantic_id] = True
        self.calls.append(("replace", semantic_id, generation))
        return SimpleNamespace(rendered=True, warnings=(), diagnostics=())

    def remove_actor(self, semantic_id: str) -> None:
        self.actors.pop(semantic_id, None)
        self.visibility.pop(semantic_id, None)

    def request_render(self) -> None:
        self.calls.append(("render",))

    def fit_to_scene(self) -> None:
        self.calls.append(("fit",))

    def set_camera_preset(self, preset: str) -> None:
        self.calls.append(("camera", preset))
        self.camera = replace(self.camera, view_preset=str(preset))

    def get_camera_state(self) -> ActiveSceneCameraState:
        return self.camera

    def apply_camera_state(self, camera: ActiveSceneCameraState) -> None:
        self.camera = camera
        self.applied_cameras.append(camera)

    def set_interaction_mode(self, mode: str) -> None:
        self.calls.append(("interaction", mode))

    def set_axes_visible(self, visible: bool) -> None:
        self.calls.append(("axes", bool(visible)))

    def set_representation(self, mode: str) -> None:
        self.calls.append(("representation", mode))

    def set_actor_visible(self, semantic_id: str, visible: bool) -> None:
        self.visibility[semantic_id] = bool(visible)

    def isolate_actor(self, semantic_id: str) -> None:
        for key in self.visibility:
            self.visibility[key] = key == semantic_id

    def clear_isolation(self) -> None:
        for key in self.visibility:
            self.visibility[key] = True

    def show_all_actors(self) -> None:
        for key in self.visibility:
            self.visibility[key] = True

    def enable_clipping(self, axis: str, origin: float) -> None:
        self.calls.append(("clip-enable", axis, origin))

    def update_clipping(self, axis: str, origin: float) -> None:
        self.calls.append(("clip-update", axis, origin))

    def clear_clipping(self) -> None:
        self.calls.append(("clip-clear",))

    def set_pick_mode(self, mode: str, callback: object) -> None:
        self.pick_callback = callback
        self.calls.append(("pick-mode", mode))

    def disable_picking(self) -> None:
        self.pick_callback = None

    def set_selection_operation(self, operation: str) -> None:
        self.calls.append(("selection-operation", operation))

    def set_hover_entities(
        self,
        kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        self.calls.append(("hover", kind, indices, generation))

    def clear_hover(self) -> None:
        self.calls.append(("clear-hover",))

    def set_current_selection(
        self,
        kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        self.calls.append(("current-selection", kind, indices, generation))

    def clear_current_selection(self) -> None:
        self.calls.append(("clear-current-selection",))

    def set_named_selection_overlay(
        self,
        selection_id: str,
        kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        self.named_overlays[selection_id] = (kind, indices, generation)

    def remove_named_selection_overlay(self, selection_id: str) -> None:
        self.named_overlays.pop(selection_id, None)

    def export_screenshot_record(
        self,
        path: str,
        *,
        record_id: str,
        scene_state: object,
        mesh: MeshData,
        mesh_ref: str | None = None,
        selection_ids: Sequence[str] = (),
        caption: str | None = None,
        created_by: str | None = None,
    ) -> SceneScreenshotRecord:
        self.capture_count += 1
        target = Path(path)
        write_nonblank_png(target)
        assert mesh is not None
        return SceneScreenshotRecord(
            id=record_id,
            path=str(target),
            caption=caption,
            scene_state=scene_state,
            mesh_ref=mesh_ref,
            selection_ids=tuple(selection_ids),
            created_by=created_by,
            path_kind=ReportAssetPathKind.EXTERNAL_ABSOLUTE,
        )

    def close(self) -> None:
        self.close_count += 1
        self.actors.clear()
        self.named_overlays.clear()
        self.pick_callback = None


class RecordingSceneFactory:
    backend_kind = RecordingSceneSession.backend_kind
    capabilities = RecordingSceneSession.capabilities

    def __init__(self, session: RecordingSceneSession | None = None) -> None:
        self.sessions: list[RecordingSceneSession] = []
        self._seed = session

    def create_session(self) -> RecordingSceneSession:
        session = self._seed or RecordingSceneSession()
        self._seed = None
        self.sessions.append(session)
        return session

    @property
    def current(self) -> RecordingSceneSession:
        return self.sessions[-1]


class FailingSceneFactory:
    backend_kind = "pyvistaqt"
    capabilities = RecordingSceneSession.capabilities

    def create_session(self) -> object:
        from osw.gui.workspace_scene_controller import SceneRendererInitializationError

        raise SceneRendererInitializationError("renderer backend unavailable")


def make_controller(
    factory: object | None = None,
    *,
    use_fixture_quality: bool = True,
) -> ActiveSceneController:
    analyzer = fixture_quality_analyzer if use_fixture_quality else None
    return ActiveSceneController(
        factory or RecordingSceneFactory(),
        mesh_quality_analyzer=analyzer,
    )


def load_e2e_mesh(controller: ActiveSceneController, mesh: MeshData) -> object:
    return controller.load_mesh(
        mesh,
        mesh_input_ref(MESH_REF),
        scene_view_state_from_toggles(show_edges=True, show_axes=True),
    )


def handle_pick(
    controller: ActiveSceneController,
    *,
    entity_kind: str,
    backend_index: int,
    intent: str = "replace",
) -> bool:
    fingerprint = controller.current_mesh_fingerprint
    assert fingerprint is not None
    return controller.handle_pick(
        {
            "generation": controller.generation,
            "mesh_ref": controller.current_mesh_ref,
            "mesh_fingerprint": fingerprint.digest,
            "entity_kind": entity_kind,
            "backend_index": backend_index,
            "intent": intent,
        }
    )


def create_selection_from_current(
    controller: ActiveSceneController,
    *,
    selection_id: str,
    name: str,
    existing: Sequence[NamedSelection] = (),
) -> NamedSelection:
    created = create_named_selection(
        existing,
        controller.current_selection_target,
        controller.current_selection_resolution,
        selection_id=selection_id,
        name=name,
    )
    return created[-1]


def workspace_paths(root: Path) -> dict[str, Path]:
    return {
        "root": root,
        "project": root / PROJECT_FILE_NAME,
        "capture": root / CAPTURE_FILE_NAME,
        "report_html": root / REPORT_HTML_NAME,
        "manifest": root / STAGE_MANIFEST_NAME,
    }


def write_stage_manifest(root: Path, payload: Mapping[str, Any]) -> Path:
    target = workspace_paths(root)["manifest"]
    target.write_text(json.dumps(dict(payload), indent=2, sort_keys=True), encoding="utf-8")
    return target


def read_stage_manifest(root: Path) -> dict[str, Any]:
    return json.loads(workspace_paths(root)["manifest"].read_text(encoding="utf-8"))


def merge_stage_manifest(root: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    current = read_stage_manifest(root) if workspace_paths(root)["manifest"].is_file() else {}
    current.update(dict(payload))
    write_stage_manifest(root, current)
    return current


def _assert_no_transient_persistence(state: ActiveSceneState) -> None:
    text = str(state.to_dict()).casefold()
    assert "backend_index" not in text
    assert "probe" not in text
    assert "hover" not in text
    assert "selected_result_table" not in text


def run_renderer_neutral_author_journey(
    workspace: Path,
    *,
    counters: ActionCounters | None = None,
) -> dict[str, Any]:
    counts = counters or ActionCounters()
    mesh = e2e_mesh()
    original_mesh = mesh_snapshot(mesh)
    changed = e2e_mesh(changed=True)
    dataset = e2e_result_dataset(mesh)
    original_dataset = dataset.to_dict()
    fingerprint = compute_mesh_fingerprint(mesh)
    changed_fingerprint = compute_mesh_fingerprint(changed)
    factory = RecordingSceneFactory()
    controller = make_controller(factory)
    project = authored_e2e_project(mesh)
    saved_selections = tuple(project.selections)

    scene = load_e2e_mesh(controller, mesh)
    assert getattr(scene, "rendered", False) is True
    assert controller.fallback_reason == ""
    assert controller.current_mesh_fingerprint == fingerprint
    assert {"base_mesh", "wireframe"}.issubset(controller.actor_records)
    assert mesh_snapshot(mesh) == original_mesh
    assert counts.automatic_saves == 0

    assert controller.set_camera_preset("isometric")
    factory.current.camera = ActiveSceneCameraState(
        position=(11.0, 8.0, 7.0),
        focal_point=(6.0, 0.4, 0.3),
        view_up=(0.0, 0.0, 1.0),
        view_preset="isometric",
    )
    assert controller.set_representation("surface_with_edges")
    assert controller.set_axes_visible(True)
    camera_before_isolation = factory.current.get_camera_state()
    assert controller.hide_actor("wireframe")
    assert controller.show_actor("wireframe")
    assert controller.isolate_actor("base_mesh")
    assert controller.actor_records["base_mesh"].visible is True
    assert controller.clear_isolation()
    assert controller.actor_records["wireframe"].visible is True
    assert factory.current.get_camera_state() == camera_before_isolation

    assert controller.set_pick_mode("node")
    assert handle_pick(controller, entity_kind="node", backend_index=5, intent="replace")
    assert handle_pick(controller, entity_kind="node", backend_index=4, intent="add")
    picked_points = create_selection_from_current(
        controller,
        selection_id=NS_PICKED_POINTS,
        name="Picked Points",
        existing=project.selections,
    )
    assert picked_points.entity_kind is EntityKind.NODE
    assert picked_points.targets[0].locator is not None
    assert picked_points.targets[0].locator.mesh_fingerprint == fingerprint.digest
    project = project_with(project, selections=(*project.selections, picked_points))
    assert controller.set_pick_mode("cell")
    assert handle_pick(controller, entity_kind="cell", backend_index=0, intent="replace")
    picked_cells = create_selection_from_current(
        controller,
        selection_id=NS_PICKED_CELLS,
        name="Picked Cells",
        existing=project.selections,
    )
    assert picked_cells.entity_kind is EntityKind.CELL
    assert picked_cells.targets[0].locator is not None
    assert picked_cells.targets[0].locator.entity_ids == ("0:0",)
    project = project_with(project, selections=(*project.selections, picked_cells))
    controller.set_named_selections(project.selections)
    controller.clear_current_selection()
    assert {item.id for item in project.selections} >= {
        NS_MATERIAL,
        NS_FIXED,
        NS_FORCE,
        NS_DISPLACEMENT,
        NS_SURFACE,
        NS_THERMAL,
        NS_PICKED_POINTS,
        NS_PICKED_CELLS,
    }

    controller.set_solver_setup(project.primary_physics, materials=project.materials)
    statuses = evaluate_solver_setup(
        project.primary_physics,
        selections=project.selections,
        materials=project.materials,
        resolutions=controller.named_selection_resolutions,
        mesh=mesh,
        project_units=project.units,
    )
    assert all(status.state is SetupReadiness.READY for status in statuses)
    setup_actor_keys = tuple(
        key
        for key in controller.actor_records
        if key.startswith(("setup_target:", "setup_glyph:", "setup:"))
    )
    assert len(setup_actor_keys) == len(set(setup_actor_keys))
    covered_setup_ids = {key.rsplit(":", 1)[-1] for key in setup_actor_keys}
    assert covered_setup_ids == {
        SETUP_MATERIAL,
        SETUP_FIXED,
        SETUP_DISPLACEMENT,
        SETUP_FORCE,
        SETUP_PRESSURE,
        SETUP_TEMPERATURE,
        SETUP_HEAT_FLUX,
    }

    supported_handoff = build_solver_setup_handoff(
        project,
        mesh=mesh,
        mesh_ref=MESH_REF,
        adapter_id="osw.solvers.calculix.linear_static",
        supported_kinds=CALCULIX_SUPPORTED_KINDS,
        strict=False,
    )
    assert {record.setup_kind for record in supported_handoff.records} == set(
        CALCULIX_SUPPORTED_KINDS
    )
    assert all(
        index >= 0
        for record in supported_handoff.records
        for index in record.resolved_entity_indices
    )
    unsupported = {
        item.setup_id: item.reason_code
        for item in supported_handoff.diagnostics
        if item.reason_code == "UNSUPPORTED_BY_ADAPTER"
    }
    assert set(unsupported) == {SETUP_PRESSURE, SETUP_TEMPERATURE, SETUP_HEAT_FLUX}
    strict_handoff = build_solver_setup_handoff(
        project,
        mesh=mesh,
        mesh_ref=MESH_REF,
        adapter_id="osw.solvers.calculix.linear_static",
        supported_kinds=CALCULIX_SUPPORTED_KINDS,
        strict=True,
    )
    assert strict_handoff.ready is False
    assert strict_handoff.records == ()
    disabled_project = project_with(
        project,
        physics=replace(
            project.primary_physics,
            pressure_load_records=[
                replace(record, enabled=False)
                for record in project.primary_physics.pressure_load_records
            ],
            temperature_records=[
                replace(record, enabled=False)
                for record in project.primary_physics.temperature_records
            ],
            heat_flux_records=[
                replace(record, enabled=False)
                for record in project.primary_physics.heat_flux_records
            ],
        ),
    )
    prepared = prepare_solver_setup(disabled_project, mesh=mesh, mesh_ref=MESH_REF)
    assert prepared.eligible is True
    assert prepared.execution_mode == "prepare_only"
    material_handoff = next(
        record
        for record in supported_handoff.records
        if record.setup_kind is SetupRecordKind.MATERIAL_REGION
    )
    assert material_handoff.resolved_entity_indices == (3,)
    assert prepared.element_sets[0][1] == tuple(
        index + 1 for index in material_handoff.resolved_entity_indices
    )
    assert all(min(ids) >= 1 for _name, ids in (*prepared.element_sets, *prepared.node_sets))
    assert "*BOUNDARY" in prepared.input_preview
    assert not hasattr(prepared, "command")
    assert counts.solver_calls == 0

    analysis = controller.analyze_mesh_quality()
    assert analysis is not None
    assert analysis.metric_schema == MESH_QUALITY_METRIC_SCHEMA
    assert analysis.mesh_fingerprint.digest == fingerprint.digest
    assert analysis.uncovered_count == 1
    assert controller.set_mesh_quality_threshold(QUALITY_THRESHOLD)
    assert controller.mesh_quality_view_model.bad_cell_keys == ("3:1",)
    assert controller.set_mesh_quality_highlight_visible(True)
    assert controller.set_mesh_quality_isolated(True)
    assert controller.restore_mesh_quality_visibility()
    assert controller.select_mesh_quality_bad_cells()
    bad_selection = create_selection_from_current(
        controller,
        selection_id=NS_BAD,
        name="Bad Elements",
        existing=project.selections,
    )
    assert bad_selection.targets[0].locator is not None
    assert bad_selection.targets[0].locator.entity_ids == ("3:1",)
    project = project_with(project, selections=(*project.selections, bad_selection))
    controller.set_named_selections(project.selections)
    controller.clear_current_selection()
    assert mesh_snapshot(mesh) == original_mesh

    resolution = controller.set_interactive_result_dataset(
        dataset,
        e2e_result_binding(mesh),
        result_ref_id=RESULT_REF_ID,
    )
    assert resolution is not None
    assert str(resolution.state) == "RESOLVED"
    point_scalar = controller.set_scalar_result(
        "temperature",
        component="value",
        range_mode="MANUAL",
        manual_range=(300.0, 340.0),
        colormap="plasma",
        colorbar_visible=True,
    )
    assert point_scalar.applied is True
    cell_scalar = controller.set_scalar_result(
        "cell_stress",
        component="value",
        range_mode="AUTO",
        colormap="viridis",
        colorbar_visible=True,
    )
    assert cell_scalar.applied is True
    vector = controller.set_vector_result(
        "velocity",
        components=("vx", "vy", "vz"),
        maximum_glyph_count=VECTOR_MAX_COUNT,
        scale=VECTOR_SCALE,
    )
    assert vector.applied is True
    assert vector.sampled_count == VECTOR_MAX_COUNT
    point_probe = controller.probe_result(
        ResultProbeRequest(
            dataset_id=RESULT_DATASET_ID,
            field_name="temperature",
            component="value",
            association="point",
            stable_entity_key=1,
            mesh_fingerprint=fingerprint.digest,
        )
    )
    cell_probe = controller.probe_result(
        ResultProbeRequest(
            dataset_id=RESULT_DATASET_ID,
            field_name="cell_stress",
            component="value",
            association="cell",
            stable_entity_key="0:0",
            mesh_fingerprint=fingerprint.digest,
        )
    )
    table = controller.set_selected_result_table(
        field_name="temperature",
        component="value",
        association="point",
        stable_entity_keys=(0, 1, 2),
    )
    assert point_probe is not None and point_probe.value == 302.0
    assert cell_probe is not None and cell_probe.value == 10.0
    assert table is not None
    original_mode = controller.set_deformed_result(
        "displacement",
        mode=DeformationMode.ORIGINAL,
    )
    deformed = controller.set_deformed_result(
        "displacement",
        mode=DeformationMode.DEFORMED,
        scale_mode=DeformationScaleMode.MANUAL,
        manual_scale=DEFORMATION_MANUAL_SCALE,
    )
    overlay = controller.set_deformed_result(
        "displacement",
        mode=DeformationMode.OVERLAY,
        scale_mode=DeformationScaleMode.MANUAL,
        manual_scale=DEFORMATION_MANUAL_SCALE,
    )
    assert original_mode.applied is True
    assert deformed.applied is True
    assert overlay.applied is True
    assert overlay.mode is DeformationMode.OVERLAY
    assert dataset.to_dict() == original_dataset
    assert mesh_snapshot(mesh) == original_mesh
    assert set(setup_actor_keys).issubset(controller.actor_records)
    controller.set_active_named_selection_ids((NS_SURFACE,))
    controller.set_active_setup_id(SETUP_FORCE)

    state = controller.snapshot_active_scene_state()
    assert state is not None
    assert state.schema == ACTIVE_SCENE_SCHEMA
    assert state.mesh_fingerprint == fingerprint.digest
    assert state.representation == "surface_with_edges"
    assert state.axes_visible is True
    assert state.result_state is not None
    assert state.result_state.vector_field == "velocity"
    assert state.result_state.deformation_mode == "OVERLAY"
    assert state.mesh_quality_state is not None
    _assert_no_transient_persistence(state)
    scene_digest = active_scene_state_digest(state)
    project = project_with(project, active_scene=state)
    paths = workspace_paths(workspace)
    capture = controller.capture_active_scene_screenshot(
        ActiveSceneScreenshotRequest(
            record_id="scene-screenshot-mvp-e2e",
            output_path=str(paths["capture"]),
            path_kind=ReportAssetPathKind.EXTERNAL_ABSOLUTE.value,
            caption=CAPTURE_CAPTION,
        )
    )
    counts.explicit_captures += 1
    assert capture.status == "CAPTURED"
    assert capture.record is not None
    image_bytes = paths["capture"].read_bytes()
    signature_ok, image_size = png_signature_and_size(image_bytes)
    assert signature_ok
    assert image_size is not None
    assert png_is_nonblank(image_bytes)
    provenance = capture.record.metadata[ACTIVE_SCENE_PROVENANCE_METADATA_KEY]
    assert provenance["active_scene_digest"] == scene_digest
    assert provenance["image_sha256"] == hashlib.sha256(image_bytes).hexdigest()
    assert provenance["mesh_fingerprint"] == fingerprint.digest
    assert provenance["vector_field"] == "velocity"
    assert provenance["deformation_mode"] == "OVERLAY"
    assert not provenance_has_absolute_path(provenance, workspace)
    assets = scene_screenshots_to_report_assets((capture.record,))
    project = project_with(project, report_screenshots=list(assets))
    project_before_report = project.to_dict()
    html = build_report(
        ReportBuildRequest(
            project=project,
            output_path=paths["report_html"],
            format=ReportFormat.HTML,
        ),
        scene_screenshots=report_assets_to_scene_screenshots(project.report_screenshots),
    )
    counts.explicit_exports += 1
    html_text = paths["report_html"].read_text(encoding="utf-8")
    assert html.status in {"ok", "warning"}
    assert CAPTURE_CAPTION in html_text
    assert fingerprint.digest[:12] in html_text
    assert "osw.active_scene.v1" in html_text
    assert str(workspace.resolve()) not in html_text
    assert factory.current.capture_count == 1
    assert project.to_dict() == project_before_report
    pdf = build_report(
        ReportBuildRequest(
            project=project,
            output_path=workspace / "report-pdf-optional.html",
            format=ReportFormat.PDF_OPTIONAL,
        ),
        scene_screenshots=report_assets_to_scene_screenshots(project.report_screenshots),
    )
    pdf_codes = {str(message.code) for message in pdf.diagnostics.messages}
    assert "report-pdf-deferred" in pdf_codes
    save_project(project, paths["project"])
    counts.explicit_saves += 1
    assert counts.automatic_saves == 0
    assert counts.automatic_captures == 0
    assert counts.automatic_exports == 0
    controller.close()
    assert factory.current.close_count == 1
    assert factory.current.actors == {}
    assert factory.current.pick_callback is None

    write_stage_manifest(
        workspace,
        {
            "author_pid": os.getpid(),
            "mesh_fingerprint": fingerprint.digest,
            "changed_fingerprint": changed_fingerprint.digest,
            "scene_digest": scene_digest,
            "image_sha256": hashlib.sha256(image_bytes).hexdigest(),
            "image_byte_length": len(image_bytes),
            "image_size": list(image_size),
            "capture_id": capture.record.id,
            "vector_sampled_count": vector.sampled_count,
            "vector_scale": VECTOR_SCALE,
            "deformation_mode": overlay.mode.value,
            "deformation_scale": overlay.scale,
            "point_probe_value": point_probe.value,
            "cell_probe_value": cell_probe.value,
            "bad_cell_keys": ["3:1"],
            "named_selection_ids": [item.id for item in project.selections],
            "setup_ids": [
                SETUP_MATERIAL,
                SETUP_FIXED,
                SETUP_DISPLACEMENT,
                SETUP_FORCE,
                SETUP_PRESSURE,
                SETUP_TEMPERATURE,
                SETUP_HEAT_FLUX,
            ],
            "setup_selection_ids": [item.id for item in saved_selections],
            "source_mesh": "unchanged",
            "source_result": "unchanged",
        },
    )
    return {
        "workspace": workspace,
        "mesh": mesh,
        "changed_mesh": changed,
        "dataset": dataset,
        "fingerprint": fingerprint.digest,
        "changed_fingerprint": changed_fingerprint.digest,
        "scene_digest": scene_digest,
        "image_sha256": hashlib.sha256(image_bytes).hexdigest(),
        "image_size": image_size,
        "image_byte_length": len(image_bytes),
        "counters": counts,
        "project_path": paths["project"],
        "capture_id": capture.record.id,
        "pdf_status": "unavailable_deferred",
        "html_status": html.status,
        "named_selection_ids": [item.id for item in project.selections],
        "bad_cell_keys": ("3:1",),
        "vector_sampled_count": vector.sampled_count,
        "point_probe_value": point_probe.value,
        "cell_probe_value": cell_probe.value,
        "deformation_mode": overlay.mode.value,
        "deformation_scale": overlay.scale,
        "setup_ids": [
            SETUP_MATERIAL,
            SETUP_FIXED,
            SETUP_DISPLACEMENT,
            SETUP_FORCE,
            SETUP_PRESSURE,
            SETUP_TEMPERATURE,
            SETUP_HEAT_FLUX,
        ],
    }


def run_renderer_neutral_restore_journey(
    workspace: Path,
    *,
    counters: ActionCounters | None = None,
) -> dict[str, Any]:
    counts = counters or ActionCounters()
    manifest = read_stage_manifest(workspace)
    mesh = e2e_mesh()
    dataset = e2e_result_dataset(mesh)
    original_mesh = mesh_snapshot(mesh)
    original_dataset = dataset.to_dict()
    original_membership = {
        item.id: item.targets[0].locator.entity_ids if item.targets[0].locator else ()
        for item in setup_named_selections(mesh)
    }
    factory = RecordingSceneFactory()
    controller = make_controller(factory)
    project = load_project(workspace_paths(workspace)["project"])
    assert project.active_scene is not None
    assert project.active_scene.schema == ACTIVE_SCENE_SCHEMA
    controller.set_named_selections(project.selections)
    controller.set_solver_setup(project.primary_physics, materials=project.materials)
    controller.set_pending_active_scene_state(project.active_scene)
    assert controller.active_scene_restore_result.status is ActiveSceneRestoreStatus.PENDING
    load_e2e_mesh(controller, mesh)
    pending = controller.active_scene_restore_result
    assert pending.status in {
        ActiveSceneRestoreStatus.PARTIAL,
        ActiveSceneRestoreStatus.RESTORED,
    }
    controller.set_interactive_result_dataset(
        dataset,
        e2e_result_binding(mesh),
        result_ref_id=RESULT_REF_ID,
    )
    restored = controller.restore_pending_active_scene_state()
    assert restored.status is ActiveSceneRestoreStatus.RESTORED
    state = controller.snapshot_active_scene_state()
    assert state is not None
    assert state.mesh_fingerprint == manifest["mesh_fingerprint"]
    assert state.representation == "surface_with_edges"
    assert state.axes_visible is True
    assert state.result_state is not None
    assert state.result_state.vector_field == "velocity"
    assert state.result_state.deformation_mode == "OVERLAY"
    assert factory.current.applied_cameras
    capture = next(iter(project.report_screenshots))
    capture_restore = controller.restore_captured_active_scene(capture)
    assert capture_restore.status is ActiveSceneRestoreStatus.RESTORED
    actor_ids = tuple(controller.actor_records)
    assert len(actor_ids) == len(set(actor_ids))
    assert mesh_snapshot(mesh) == original_mesh
    assert dataset.to_dict() == original_dataset
    restored_membership = {
        item.id: item.targets[0].locator.entity_ids if item.targets[0].locator else ()
        for item in project.selections
        if item.id in original_membership
    }
    assert restored_membership == original_membership
    assert counts.automatic_saves == 0
    controller.close()
    return {
        "status": restored.status.value,
        "scene_digest": active_scene_state_digest(state),
        "restore_pid": os.getpid(),
        "actor_count": len(controller.actor_records),
        "counters": counts,
    }


def run_renderer_neutral_stale_journey(
    workspace: Path,
    *,
    counters: ActionCounters | None = None,
) -> dict[str, Any]:
    counts = counters or ActionCounters()
    manifest = read_stage_manifest(workspace)
    changed = e2e_mesh(changed=True)
    factory = RecordingSceneFactory()
    controller = make_controller(factory)
    project = load_project(workspace_paths(workspace)["project"])
    retained_ids = [item.id for item in project.selections]
    retained_setup_ids = [
        record.id
        for record in (
            *project.primary_physics.material_assignment_records,
            *project.primary_physics.fixed_support_records,
            *project.primary_physics.prescribed_displacement_records,
            *project.primary_physics.force_load_records,
            *project.primary_physics.pressure_load_records,
            *project.primary_physics.temperature_records,
            *project.primary_physics.heat_flux_records,
        )
    ]
    controller.set_named_selections(project.selections)
    controller.set_solver_setup(project.primary_physics, materials=project.materials)
    controller.set_pending_active_scene_state(project.active_scene)
    load_e2e_mesh(controller, changed)
    result = controller.active_scene_restore_result
    assert result.status is ActiveSceneRestoreStatus.STALE
    assert "MESH_FINGERPRINT_MISMATCH" in result.reason_codes
    assert factory.current.applied_cameras == []
    assert not any(key.startswith("result:") for key in controller.actor_records)
    assert "mesh_bad_elements" not in controller.actor_records
    assert all(
        resolution.state.value == "STALE"
        for resolution in controller.named_selection_resolutions.values()
    )
    assert all(
        status.state is SetupReadiness.BLOCKED for status in controller.setup_statuses.values()
    )
    capture = next(iter(project.report_screenshots))
    capture_restore = controller.restore_captured_active_scene(capture)
    assert capture_restore.status is ActiveSceneRestoreStatus.STALE
    reloaded = load_project(workspace_paths(workspace)["project"])
    assert [item.id for item in reloaded.selections] == retained_ids
    assert reloaded.active_scene is not None
    assert reloaded.active_scene.mesh_fingerprint == manifest["mesh_fingerprint"]
    assert counts.automatic_saves == 0
    controller.close()
    return {
        "status": result.status.value,
        "reason_codes": list(result.reason_codes),
        "stale_pid": os.getpid(),
        "retained_selection_ids": retained_ids,
        "retained_setup_ids": retained_setup_ids,
        "counters": counts,
    }
