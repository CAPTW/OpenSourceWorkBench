from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_prepared_machine_validation_command_design.md"
)


def _collapsed(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8")).lower()


def _doc() -> str:
    return _collapsed(DOC_PATH)


def test_design_doc_exists_and_records_design_only_status() -> None:
    assert DOC_PATH.exists()
    text = _doc()
    for phrase in (
        "design-only",
        "no command implementation",
        "no source edits",
        "no cli source edits",
        "no dependency installation",
        "no solver installation",
        "no solver execution",
        "no live validation",
        "no projectschema mutation",
        "no projectschema evidence",
        "no issue mutation",
        "no release mutation",
        "no tag mutation",
        "no asset mutation",
        "no validation-pass claim",
        "no validation-fail claim",
        "no issue closure",
        "no bundled solver support claim",
        "no certification claim",
    ):
        assert phrase in text


def test_design_doc_references_gate_prerequisites_and_open_issues() -> None:
    text = _doc()
    for phrase in (
        "osw-valid-optional_prepared_machine_manifest_state_validation",
        "osw-exp-140_optional_solver_prepared_machine_validation_command_implementation",
        "issues #6 through #11",
        "42d687626955a516f4072ad07b058e0f665fceaf",
        "1872de79e87340821c4eeb274f7c6406d659c2ff",
        "parked",
        "skipped-missing",
    ):
        assert phrase in text


def test_prerequisite_model_names_required_optional_stacks() -> None:
    text = _doc()
    for phrase in (
        "gmsh",
        "python_gmsh",
        "octave",
        "ccx",
        "openfoam",
        "meshio",
        "pyvista",
        "vtk",
        "coolprop",
        "cantera",
    ):
        assert phrase in text


def test_design_doc_defines_command_family_and_subcommand_designs() -> None:
    text = _doc()
    for phrase in (
        "python -m osw.cli optional-solver-prepared-machine-validation",
        "future command name and location",
        "preflight subcommand design",
        "plan subcommand design",
        "run subcommand design",
        "prerequisite model",
        "solver discovery boundary",
        "solver execution boundary",
        "evidence policy",
        "exit-code policy",
        "output policy",
        "projectschema boundary",
        "issue/release boundary",
        "certification boundary",
        "security/privacy review",
        "future implementation test plan",
        "future gates",
    ):
        assert phrase in text


def test_meta_docs_reference_command_design_boundary() -> None:
    decision_log = _collapsed(REPO_ROOT / "docs" / "07_decision_log.md")
    guardrails = _collapsed(REPO_ROOT / "docs" / "08_scope_guardrails.md")
    risk = _collapsed(REPO_ROOT / "docs" / "09_risk_register.md")
    checklist = _collapsed(REPO_ROOT / "docs" / "10_release_checklist.md")
    matrix = _collapsed(REPO_ROOT / "docs" / "04_validation_matrix.md")
    changelog = _collapsed(REPO_ROOT / "CHANGELOG.md")

    assert "adr-0174" in decision_log
    assert (
        "optional solver prepared-machine validation requires an explicit local command"
        in decision_log
    )
    assert "prepared-machine validation command design" in guardrails
    assert "prepared-machine command design overreach" in risk
    assert "prepared-machine validation command design" in checklist
    assert "prepared-machine validation command design" in matrix
    assert "optional solver prepared-machine validation command design" in changelog
