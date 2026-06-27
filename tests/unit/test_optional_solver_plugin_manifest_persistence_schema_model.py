from __future__ import annotations

import ast
import importlib
from pathlib import Path

from osw.experimental.optional_solvers import (
    DEFAULT_REDACTION_POLICY_ID,
    PERSISTENCE_SCHEMA_VERSION,
    SUPPORTED_PERSISTENCE_SCHEMA_VERSIONS,
    build_optional_solver_plugin_manifest_persistence_schema_model,
    build_optional_solver_plugin_manifest_persistence_viewmodel,
    redact_optional_solver_plugin_manifest_persistence_schema_source_reference,
    validate_optional_solver_plugin_manifest_persistence_schema_mapping,
)
from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestPersistenceCandidateInput as PCand,
)
from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestPersistenceSchemaAcknowledgementRecord as AckRecord,
)
from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestPersistenceSchemaConflictRecord as ConflictRecord,
)
from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestPersistenceSchemaInput as PSchema,
)
from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestPersistenceSchemaModel as Model,
)
from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestPersistenceSchemaSourceRecord as SourceRecord,
)
from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestPersistenceSchemaUnsafeClaimRecord as UnsafeRecord,
)
from osw.experimental.optional_solvers import (
    plugin_manifest_persistence_schema_model as module_under_test,
)
from osw.experimental.optional_solvers.plugin_manifest_persistence_viewmodel import (
    OSPMG_PERSISTENCE_ACK_REQUIRED,
    OSPMG_PERSISTENCE_CONFLICT_BLOCKED,
    OSPMG_PERSISTENCE_DIAGNOSTIC_CODES,
    OSPMG_PERSISTENCE_NOT_IMPLEMENTED,
    OSPMG_PERSISTENCE_REDACTION_REQUIRED,
    OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED,
    OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED,
    OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED,
    OSPMG_PERSISTENCE_UNSAFE_CLAIM,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_persistence_schema_model.md"
)


def _module_source() -> str:
    return Path(module_under_test.__file__).read_text(encoding="utf-8")


def _imported_modules() -> set[str]:
    tree = ast.parse(_module_source())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return {module.lower() for module in modules}


def _codes(diagnostics) -> set[str]:
    return {d.code for d in diagnostics}


def _collapse(text: str) -> str:
    return " ".join(text.lower().split())


# ---------------------------------------------------------------------------
# Purity / safety.
# ---------------------------------------------------------------------------
def test_module_imports_cleanly() -> None:
    module = importlib.import_module(
        "osw.experimental.optional_solvers.plugin_manifest_persistence_schema_model"
    )
    assert hasattr(module, "OptionalSolverPluginManifestPersistenceSchemaModel")


def test_module_has_no_gui_heavy_or_unsafe_imports() -> None:
    forbidden_roots = {
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "http",
        "pathlib",
        "os",
        "shutil",
        "gmsh",
        "meshio",
        "pyvista",
        "vtk",
        "coolprop",
        "cantera",
    }
    for module in _imported_modules():
        root = module.split(".", 1)[0]
        assert root not in forbidden_roots, module
        assert "pyside" not in module
        assert "pyqt" not in module
        assert not module.startswith("qt")


def test_module_source_has_no_io_mutation_discovery_or_solver_paths() -> None:
    source = _module_source()
    for phrase in (
        "QProcess",
        "subprocess",
        "os.system",
        "discover_builtin_optional_solvers",
        "discover_optional_solver_manifests",
        "pip install",
        "pip uninstall",
        "conda remove",
        "gh issue",
        "gh release",
        ".unlink(",
        ".rmdir(",
        "shutil.rmtree",
        ".write_text(",
        ".write_bytes(",
        ".read_text(",
        ".exists(",
        "open(",
        "json.load(",
        "ProjectSchema(",
        "load_optional_solver_plugin_manifest_json",
    ):
        assert phrase not in source, phrase


# ---------------------------------------------------------------------------
# Empty / default model.
# ---------------------------------------------------------------------------
def test_empty_model_is_supported_and_writes_nothing() -> None:
    model = Model.empty()
    assert model.header.schema_version == PERSISTENCE_SCHEMA_VERSION
    assert model.header.schema_version_supported is True
    assert model.header.redaction_policy_id == DEFAULT_REDACTION_POLICY_ID
    assert model.sources == ()
    assert model.candidates == ()
    assert model.acknowledgements == ()
    assert model.conflicts == ()
    assert model.unsafe_claims == ()
    assert model.this_gate_creates_schema_file is False
    assert model.schema_migration.this_gate_creates_schema_file is False
    assert model.not_validation_evidence is True
    assert model.reserved_diagnostic_codes == OSPMG_PERSISTENCE_DIAGNOSTIC_CODES


def test_empty_model_reports_no_implementation_and_no_migration() -> None:
    model = Model.empty()
    assert OSPMG_PERSISTENCE_NOT_IMPLEMENTED in _codes(model.diagnostics)
    assert model.schema_migration.migration_required is False
    assert model.schema_migration.migration_status == "not_required"
    summary = model.validation_summary
    assert summary is not None
    assert summary.persistence_performed is False
    assert summary.file_write_performed is False
    assert summary.ready_for_future_write is False


def test_supported_versions_include_current_and_092_preview() -> None:
    assert PERSISTENCE_SCHEMA_VERSION in SUPPORTED_PERSISTENCE_SCHEMA_VERSIONS
    assert "osw-exp-092-preview" in SUPPORTED_PERSISTENCE_SCHEMA_VERSIONS


# ---------------------------------------------------------------------------
# Redaction defaults.
# ---------------------------------------------------------------------------
def test_redaction_policy_defaults_are_redaction_first() -> None:
    policy = Model.empty().redaction_policy
    assert policy.redaction_required is True
    assert policy.raw_absolute_paths_allowed is False
    assert policy.unredacted_path_blocked is True
    assert policy.secret_like_content_blocked is True
    assert policy.path_review_required is True
    assert OSPMG_PERSISTENCE_REDACTION_REQUIRED in _codes(Model.empty().diagnostics)


def test_redact_source_reference_returns_basename_only() -> None:
    display, redacted = redact_optional_solver_plugin_manifest_persistence_schema_source_reference(
        "C:/secret/dir/manifest.json"
    )
    assert display == "manifest.json"
    assert redacted is True
    assert "/" not in display
    assert chr(92) not in display


def test_redaction_required_classmethod_blocks_raw_path() -> None:
    source = SourceRecord(
        source_id="s1",
        source_reference_display="C:/private/manifest.json",
    )
    model = Model.redaction_required(source)
    assert model.sources[0].raw_reference_blocked is True
    assert model.sources[0].source_reference_redacted is False
    assert OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED in _codes(model.diagnostics)
    assert model.validation_summary is not None
    assert model.validation_summary.redaction_issue_count == 1


# ---------------------------------------------------------------------------
# Schema version / migration.
# ---------------------------------------------------------------------------
def test_missing_schema_version_is_a_blocker() -> None:
    diagnostics = validate_optional_solver_plugin_manifest_persistence_schema_mapping({})
    codes = _codes(diagnostics)
    assert OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED in codes
    assert OSPMG_PERSISTENCE_REDACTION_REQUIRED in codes
    version_diag = next(
        d for d in diagnostics if d.code == OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED
    )
    assert version_diag.blocker is True


def test_unsupported_schema_version_requires_migration() -> None:
    model = Model.unsupported_version("osw-exp-001-legacy")
    assert model.header.schema_version_supported is False
    assert model.schema_migration.migration_required is True
    assert model.schema_migration.blocker is True
    assert OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED in _codes(model.diagnostics)
    assert model.validation_summary is not None
    assert model.validation_summary.migration_required_count == 1


def test_migration_required_classmethod_sets_notes() -> None:
    model = Model.migration_required("osw-exp-001-legacy", migration_notes="upgrade me")
    assert model.schema_migration.migration_required is True
    assert model.header.migration_notes == "upgrade me"
    assert model.schema_migration.migration_notes_display == "upgrade me"


def test_no_schema_file_is_created_in_this_gate() -> None:
    for model in (
        Model.empty(),
        Model.unsupported_version("x"),
        Model.migration_required("x"),
    ):
        assert model.this_gate_creates_schema_file is False
        assert model.schema_migration.this_gate_creates_schema_file is False


# ---------------------------------------------------------------------------
# Mapping round-trip.
# ---------------------------------------------------------------------------
def test_to_mapping_has_expected_top_level_keys() -> None:
    mapping = Model.empty().to_mapping()
    expected = {
        "schema_version",
        "created_by_osw_version",
        "created_at",
        "state_scope",
        "manifest_sources",
        "candidates",
        "acknowledgements",
        "diagnostics",
        "conflicts",
        "unsafe_claims",
        "redaction_policy",
        "evidence_history",
        "migration_notes",
        "non_action_flags",
    }
    assert expected <= set(mapping)


def test_to_mapping_from_mapping_round_trip_in_memory() -> None:
    model = build_optional_solver_plugin_manifest_persistence_schema_model(
        sources=(
            SourceRecord(
                source_id="s1",
                source_label="User manifest",
                source_reference_display="manifest.json",
            ),
        ),
        candidates=(),
        acknowledgements=(
            AckRecord(acknowledgement_id="ack.not_validation", required=True, satisfied=True),
        ),
    )
    mapping = model.to_mapping()
    restored = Model.from_mapping(mapping)
    assert restored.header.schema_version == model.header.schema_version
    assert len(restored.sources) == len(model.sources)
    assert restored.sources[0].source_id == "s1"
    assert len(restored.acknowledgements) == len(model.acknowledgements)
    # Round-tripping does not turn on any non-action flag.
    assert restored.to_mapping()["non_action_flags"] == mapping["non_action_flags"]


# ---------------------------------------------------------------------------
# Candidates do not imply persistence.
# ---------------------------------------------------------------------------
def test_candidates_do_not_imply_persistence_or_activation() -> None:
    model = build_optional_solver_plugin_manifest_persistence_schema_model(
        candidates=(
            module_under_test.OptionalSolverPluginManifestPersistenceSchemaCandidateRecord(
                stack_id="user_stack",
                activation_state="inactive_preview",
            ),
        ),
    )
    assert model.validation_summary is not None
    assert model.validation_summary.persistence_performed is False
    flags = model.non_action_flags
    assert flags.persistence_performed is False
    assert flags.automatic_activation_performed is False
    assert flags.trust_restoration_performed is False


# ---------------------------------------------------------------------------
# Acknowledgement expiry.
# ---------------------------------------------------------------------------
def test_acknowledgement_records_expire_by_default() -> None:
    ack = AckRecord(acknowledgement_id="ack.example")
    assert ack.required is True
    assert ack.satisfied is False
    assert ack.persisted is False
    assert ack.expires_on_reload is True
    assert ack.expires_on_source_change is True
    assert ack.expires_on_schema_change is True
    assert ack.expires_on_unsafe_claim is True


def test_missing_required_acknowledgements_are_flagged() -> None:
    model = build_optional_solver_plugin_manifest_persistence_schema_model(
        acknowledgements=(
            AckRecord(acknowledgement_id="ack.one", required=True, satisfied=False),
        ),
    )
    assert OSPMG_PERSISTENCE_ACK_REQUIRED in _codes(model.diagnostics)


# ---------------------------------------------------------------------------
# Conflicts / unsafe claims / stale.
# ---------------------------------------------------------------------------
def test_conflicts_are_visible_and_built_ins_win() -> None:
    model = build_optional_solver_plugin_manifest_persistence_schema_model(
        conflicts=(
            ConflictRecord(
                stack_id="shared",
                built_in_source_id="built_in",
                user_or_plugin_source_id="user",
            ),
        ),
    )
    conflict = model.conflicts[0]
    assert conflict.built_ins_win_by_default is True
    assert conflict.conflict_visible is True
    assert conflict.future_policy_required is True
    assert OSPMG_PERSISTENCE_CONFLICT_BLOCKED in _codes(model.diagnostics)


def test_unsafe_claims_are_never_accepted() -> None:
    model = build_optional_solver_plugin_manifest_persistence_schema_model(
        unsafe_claims=(
            UnsafeRecord(claim_id="c1", claim_text="this solver is certified"),
        ),
    )
    claim = model.unsafe_claims[0]
    assert claim.blocked is True
    assert claim.accepted_by_persistence is False
    assert OSPMG_PERSISTENCE_UNSAFE_CLAIM in _codes(model.diagnostics)


def test_stale_source_requires_repreview() -> None:
    model = build_optional_solver_plugin_manifest_persistence_schema_model(
        sources=(
            SourceRecord(
                source_id="s1",
                stale_source_state="stale",
                repreview_required=True,
            ),
        ),
    )
    assert OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED in _codes(model.diagnostics)
    assert model.validation_summary is not None
    assert model.validation_summary.stale_source_count == 1


# ---------------------------------------------------------------------------
# Evidence/history retention.
# ---------------------------------------------------------------------------
def test_evidence_history_defaults_retain_without_claiming_outcomes() -> None:
    history = Model.empty().evidence_history
    assert history.deactivation_history_retained is True
    assert history.reactivation_history_retained is True
    assert history.historical_validation_evidence_retained is True
    assert history.skipped_missing_remains_skipped_missing is True
    assert history.issue_closure_implied is False
    assert history.validation_success_claimed is False
    assert history.validation_failure_claimed is False
    assert history.evidence_deleted_or_rewritten is False


# ---------------------------------------------------------------------------
# Non-action flags.
# ---------------------------------------------------------------------------
def test_non_action_flags_are_all_false() -> None:
    flags = Model.empty().non_action_flags
    mapping = module_under_test._non_action_flags_to_mapping(flags)
    assert mapping  # non-empty
    assert all(value is False for value in mapping.values())


def test_validate_mapping_blocks_any_truthy_non_action_flag() -> None:
    diagnostics = validate_optional_solver_plugin_manifest_persistence_schema_mapping(
        {
            "schema_version": PERSISTENCE_SCHEMA_VERSION,
            "redaction_policy": {},
            "non_action_flags": {"file_write_performed": True},
        }
    )
    blockers = [
        d
        for d in diagnostics
        if d.code == OSPMG_PERSISTENCE_NOT_IMPLEMENTED and d.blocker
    ]
    assert blockers


# ---------------------------------------------------------------------------
# Determinism.
# ---------------------------------------------------------------------------
def test_build_is_deterministic() -> None:
    def make() -> Model:
        return build_optional_solver_plugin_manifest_persistence_schema_model(
            sources=(SourceRecord(source_id="s1"),),
            acknowledgements=(
                AckRecord(acknowledgement_id="ack.one", required=True, satisfied=True),
            ),
        )

    first = make()
    second = make()
    assert first == second
    assert first.to_mapping() == second.to_mapping()
    assert first.validation_summary == second.validation_summary


# ---------------------------------------------------------------------------
# Adapter from the OSW-EXP-092 persistence view-model.
# ---------------------------------------------------------------------------
def _build_persistence_viewmodel():
    schema = PSchema(schema_version_display="osw-exp-092-preview", schema_version_present=True)
    return build_optional_solver_plugin_manifest_persistence_viewmodel(
        [PCand(stack_id="user_stack", source_reference="C:/secret/manifest.json")],
        acknowledgements={},
        persistence_requested=True,
        schema=schema,
    )


def test_from_persistence_viewmodel_does_not_mutate_source() -> None:
    view_model = _build_persistence_viewmodel()
    before_candidates = view_model.candidate_rows
    before_sources = view_model.source_rows
    before_acks = view_model.acknowledgement_rows
    model = Model.from_persistence_viewmodel(view_model)
    assert view_model.candidate_rows is before_candidates
    assert view_model.source_rows is before_sources
    assert view_model.acknowledgement_rows is before_acks
    assert model.header.schema_version == PERSISTENCE_SCHEMA_VERSION
    assert model.this_gate_creates_schema_file is False


def test_from_persistence_viewmodel_carries_counts() -> None:
    view_model = _build_persistence_viewmodel()
    model = Model.from_persistence_viewmodel(view_model)
    assert model.validation_summary is not None
    assert model.validation_summary.candidate_count == len(view_model.candidate_rows)
    assert model.validation_summary.source_count == len(view_model.source_rows)
    # Redacted source references stay basename-only in the schema model.
    for source in model.sources:
        assert "/" not in source.source_reference_display
        assert chr(92) not in source.source_reference_display


# ---------------------------------------------------------------------------
# Docs.
# ---------------------------------------------------------------------------
def test_docs_mention_non_actions_relationships_and_future_gates() -> None:
    assert DOC.exists()
    text = _collapse(DOC.read_text(encoding="utf-8"))
    for phrase in (
        "non-actions",
        "future gates",
        "in-memory",
        "redaction-first",
        "built-ins win by default",
        "trust label is not certification",
        "relationship to osw-exp-090 design",
        "relationship to osw-exp-092 persistence view-model",
        "relationship to export-summary design",
        "relationship to projectschema",
        "relationship to live optional validation issues",
        "no persistence implementation",
        "no file writes",
        "no schema file creation",
        "no settings file creation",
        "no automatic activation",
        "no trust restoration",
        "no discovery execution",
        "no validation execution",
        "no solver execution",
    ):
        assert phrase in text, phrase
