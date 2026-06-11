from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_DOC = REPO_ROOT / "docs" / "experimental" / "feaspec_validator_design.md"

REQUIRED_CODES = {
    "FS_SCHEMA_MISSING_FIELD",
    "FS_UNITS_MISSING_SYSTEM",
    "FS_UNITS_AMBIGUOUS",
    "FS_GEOM_DUPLICATE_ID",
    "FS_GEOM_MISSING_NODE",
    "FS_GEOM_DISCONNECTED_GRAPH",
    "FS_MATERIAL_MISSING",
    "FS_SECTION_MISSING",
    "FS_BC_INVALID_TARGET",
    "FS_BC_INSUFFICIENT_CONSTRAINTS",
    "FS_LOAD_INVALID_TARGET",
    "FS_LOAD_MISSING_UNITS",
    "FS_DIMENSION_CONFLICT",
    "FS_EVIDENCE_MISSING",
    "FS_CONFIDENCE_LOW",
    "FS_REVIEW_MISSING",
    "FS_REVIEW_NOT_APPROVED",
    "FS_SOLVER_UNSUPPORTED_ELEMENT",
    "FS_SOLVER_ABAQUS_NON_DEFAULT",
    "FS_BENCHMARK_METADATA_MISSING",
}

REQUIRED_CATEGORIES = {
    "schema",
    "units",
    "geometry",
    "material",
    "section",
    "boundary_condition",
    "load",
    "dimension",
    "evidence",
    "human_review",
    "solver_compatibility",
    "benchmark",
}


def _read() -> str:
    return DESIGN_DOC.read_text(encoding="utf-8")


def test_feaspec_validator_design_doc_exists() -> None:
    assert DESIGN_DOC.exists()


def test_validator_design_status_and_non_execution_boundaries() -> None:
    text = _read().lower()
    assert "design-only" in text
    assert "full validator is not implemented" in text
    assert "no solver execution" in text
    assert "no implementation in this gate" in text


def test_validator_design_defines_pipeline() -> None:
    text = _read().lower()
    assert "validator pipeline" in text
    for phase in (
        "schema phase",
        "unit phase",
        "geometry phase",
        "material/section phase",
        "boundary-condition phase",
        "load phase",
        "evidence/confidence phase",
        "human review phase",
        "solver compatibility phase",
        "benchmark readiness phase",
        "validation report output phase",
    ):
        assert phase in text


def test_validator_design_defines_diagnostic_model() -> None:
    text = _read()
    for field in (
        "code",
        "severity",
        "category",
        "message",
        "target_ref",
        "evidence_ref",
        "suggested_fix",
        "blocks_approval",
        "blocks_solver_handoff",
    ):
        assert field in text


def test_validator_design_defines_severity_taxonomy() -> None:
    text = _read().lower()
    assert "severity taxonomy" in text
    for severity in ("info", "warning", "error", "blocker"):
        assert severity in text


def test_validator_design_defines_diagnostic_categories() -> None:
    text = _read()
    assert "Diagnostic Categories" in text
    for category in REQUIRED_CATEGORIES:
        assert category in text


def test_validator_design_includes_required_diagnostic_codes() -> None:
    text = _read()
    for code in REQUIRED_CODES:
        assert code in text


def test_validator_design_defines_validation_states() -> None:
    text = _read()
    assert "Validation States" in text
    for state in ("unchecked", "invalid", "valid-with-warnings", "approved", "rejected"):
        assert state in text


def test_validator_design_approval_and_handoff_rules() -> None:
    text = _read().lower()
    assert "feaspeccandidate" in text
    assert "cannot be treated as solver-ready" in text
    assert "requires a `human_review` block" in text
    assert "only an approved feaspec may proceed toward future solver handoff" in text
    assert "no automatic unreviewed solver execution" in text
    assert "projectschema bridge plan layer is implemented separately" in text
    assert "full projectschema persistence" in text
    assert "projectschema mutation are future work" in text
    assert "solveradapter handoff is future work" in text


def test_validator_design_solver_and_benchmark_boundaries() -> None:
    text = _read().lower()
    assert "calculix-first" in text
    assert "abaqus handling is optional_non_default only" in text
    assert "abaqus is never required" in text
    assert "benchmark readiness is validated through metadata and ground truth" in text
    assert "no industrial certification" in text
    assert "no vlm api" in text
    assert "credentials" in text


def test_validator_design_does_not_claim_forbidden_implementation() -> None:
    text = _read().lower()
    forbidden_claims = (
        "full validator implementation exists",
        "full validator is implemented",
        "vfea implementation exists",
        "vfea is implemented",
        "automatic unreviewed solver execution is allowed",
        "full projectschema persistence is implemented",
        "projectschema mutation is implemented",
        "solveradapter is implemented",
        "calculix export is implemented",
        "abaqus exporter is implemented",
        "abaqus is mandatory",
        "requires abaqus",
        "industrial certification is provided",
    )
    for claim in forbidden_claims:
        assert claim not in text
