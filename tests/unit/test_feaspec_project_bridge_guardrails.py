from __future__ import annotations

import json
import re
from pathlib import Path

from osw.experimental.feaspec import plan_project_from_feaspec

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_BRIDGE = REPO_ROOT / "src" / "osw" / "experimental" / "feaspec" / "project_bridge.py"
PROJECT_SCHEMA = REPO_ROOT / "src" / "osw" / "core" / "project_schema.py"
BRIDGE_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_to_projectschema_bridge_implementation.md"
)
EXAMPLES = REPO_ROOT / "examples" / "feaspec"


def _bridge_source() -> str:
    return PROJECT_BRIDGE.read_text(encoding="utf-8")


def test_bridge_does_not_write_files(tmp_path: Path) -> None:
    payload = json.loads((EXAMPLES / "cantilever_beam_approved.json").read_text(encoding="utf-8"))

    plan = plan_project_from_feaspec(payload)

    assert plan.is_draft_ready
    assert list(tmp_path.iterdir()) == []


def test_bridge_does_not_import_command_gui_solver_or_network_modules() -> None:
    text = _bridge_source()
    forbidden_import_patterns = (
        r"^\s*import\s+subprocess\b",
        r"^\s*from\s+subprocess\s+import\b",
        r"^\s*import\s+requests\b",
        r"^\s*from\s+requests\s+import\b",
        r"^\s*import\s+urllib\b",
        r"^\s*from\s+urllib\s+import\b",
        r"^\s*from\s+osw\.gui\b",
        r"^\s*import\s+osw\.gui\b",
        r"^\s*from\s+osw\..*runner\b",
        r"^\s*from\s+osw\..*adapter\b",
        r"^\s*from\s+osw\..*calculix\b",
        r"^\s*from\s+osw\..*openfoam\b",
    )
    for pattern in forbidden_import_patterns:
        assert re.search(pattern, text, re.MULTILINE) is None


def test_bridge_does_not_add_vlm_api_or_credentials() -> None:
    text = _bridge_source().lower()
    forbidden_tokens = (
        "openai_api_key",
        "anthropic_api_key",
        "gemini_api_key",
        "api_key",
        "credentials",
        "vlmprovider",
        "vision model",
    )
    for token in forbidden_tokens:
        assert token not in text


def test_bridge_does_not_introduce_solver_export_or_command_helpers() -> None:
    text = _bridge_source()
    forbidden_function_patterns = (
        r"def\s+export_",
        r"def\s+generate_.*deck",
        r"def\s+run_",
        r"def\s+execute_",
        r"def\s+call_",
    )
    for pattern in forbidden_function_patterns:
        assert re.search(pattern, text) is None


def test_bridge_does_not_mutate_project_schema_source() -> None:
    text = PROJECT_SCHEMA.read_text(encoding="utf-8")

    assert "FEASpec" not in text
    assert "BridgeStatus" not in text


def test_bridge_docs_avoid_forbidden_positive_claims() -> None:
    text = BRIDGE_DOC.read_text(encoding="utf-8").lower()
    forbidden_claims = (
        "full projectschema persistence exists",
        "projectschema mutation exists",
        "calculix export exists",
        "abaqus export exists",
        "solver execution is allowed",
        "vfea implementation is complete",
        "vlm integration exists",
        "automatic solver execution is allowed",
        "abaqus is mandatory",
        "industrial certification is provided",
        "stable production",
    )
    for claim in forbidden_claims:
        assert claim not in text
