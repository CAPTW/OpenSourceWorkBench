from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FEASPEC_SRC = REPO_ROOT / "src" / "osw" / "experimental" / "feaspec"
MODEL_DOC = REPO_ROOT / "docs" / "experimental" / "feaspec_python_models.md"


def _source_texts() -> dict[Path, str]:
    return {path: path.read_text(encoding="utf-8") for path in sorted(FEASPEC_SRC.glob("*.py"))}


def _lower_text() -> str:
    chunks = list(_source_texts().values())
    if MODEL_DOC.exists():
        chunks.append(MODEL_DOC.read_text(encoding="utf-8"))
    return "\n".join(chunks).lower()


def test_feaspec_model_modules_do_not_import_gui_solver_or_network_api_modules() -> None:
    forbidden_import_roots = {
        "osw.gui",
        "osw.solvers",
        "osw.core.project_schema",
        "subprocess",
        "socket",
        "requests",
        "httpx",
        "urllib",
        "openai",
        "anthropic",
        "google.generativeai",
    }
    for path, text in _source_texts().items():
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                imported = {node.module or ""}
            else:
                continue
            assert forbidden_import_roots.isdisjoint(imported), path


def test_feaspec_model_modules_do_not_execute_commands() -> None:
    forbidden_calls = {"run", "Popen", "system", "spawn", "execve"}
    for path, text in _source_texts().items():
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = ""
                if isinstance(func, ast.Attribute):
                    name = func.attr
                elif isinstance(func, ast.Name):
                    name = func.id
                assert name not in forbidden_calls, path


def test_feaspec_model_guardrail_text_does_not_claim_certification_or_stable_production() -> None:
    text = _lower_text()
    forbidden_claims = (
        "industrial certification is provided",
        "certification guaranteed",
        "stable production release",
        "production cae is supported",
        "production cae claim is supported",
        "vfea implementation exists",
        "vfea is implemented",
        "full validator is implemented",
    )
    for claim in forbidden_claims:
        assert claim not in text


def test_abaqus_remains_optional_non_default_if_mentioned() -> None:
    text = _lower_text()
    assert "abaqus" in text
    assert "optional" in text or "non-default" in text or "non_default" in text
    forbidden_claims = ("abaqus is mandatory", "abaqus is required", "requires abaqus")
    for claim in forbidden_claims:
        assert claim not in text


def test_vlm_api_credentials_and_provider_integration_are_not_implemented() -> None:
    text = _lower_text()
    forbidden_fragments = (
        "openai_api_key",
        "anthropic_api_key",
        "gemini_api_key",
        "vlmprovider(",
        "vlm api client",
        "api credential",
    )
    for fragment in forbidden_fragments:
        assert fragment not in text


def test_solver_execution_and_topology_optimization_are_not_implemented() -> None:
    text = _lower_text()
    forbidden_fragments = (
        "automatic unreviewed solver execution is allowed",
        "solver execution is implemented",
        "calculix input deck generation is implemented",
        "abaqus exporter is implemented",
        "topology optimization is implemented",
    )
    for fragment in forbidden_fragments:
        assert fragment not in text
