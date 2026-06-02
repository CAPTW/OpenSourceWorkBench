#!/usr/bin/env python3
"""Check static release-gate invariants for OSW functional queue completion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _common import capture, repo_root

FUNC_STEPS = [
    "OSW-FUNC-001_PROJECT_SCHEMA_INTEGRATION",
    "OSW-FUNC-002_PLUGIN_CONTRACT_DISCOVERY",
    "OSW-FUNC-003_RUNNER_DIAGNOSTICS",
    "OSW-FUNC-004_PLUGIN_MANAGER_DIALOG_BINDING",
    "OSW-FUNC-005_MESH_IMPORT_BRIDGE",
    "OSW-FUNC-006_MSCRIPT_IMPORT_PREVIEW",
    "OSW-FUNC-007_OCTAVE_RUNNER",
    "OSW-FUNC-008_FIGURE_CAPTURE_DATASET",
    "OSW-FUNC-009_MAT_READER",
    "OSW-FUNC-010_BOUNDARY_CURVE_BRIDGE",
    "OSW-FUNC-011_REPORT_GENERATOR_BINDING",
    "OSW-FUNC-012_GMSH_ADAPTER",
    "OSW-FUNC-013_CALCULIX_INPUT_DECK",
    "OSW-FUNC-014_CALCULIX_RUNNER_BINDING",
    "OSW-FUNC-015_CALCULIX_RESULT_PARSER",
    "OSW-FUNC-016_OPENFOAM_TEMPLATE_BINDING",
    "OSW-FUNC-017_RESULT_VIEWER_DATASET_BINDING",
    "OSW-FUNC-018_CHM_COOLPROP_CANTERA_BINDING",
    "OSW-FUNC-019_RESULT_VIEWER_FIELD_RENDERING",
    "OSW-FUNC-020_RELEASE_VALIDATION_GATE",
]

UI_STEPS = [
    "UI-000_REFERENCE_SPEC_DOCS",
    "UI-001_THEME_MANAGER",
    "UI-002_MAIN_SHELL_LAYOUT",
    "UI-003_LEFT_PROJECT_TREE",
    "UI-004_TOP_TOOLBAR_AND_STEPPER",
    "UI-005_CENTRAL_VIEWPORT_MOCK",
    "UI-006_RUN_MONITOR_AND_CHARTS",
    "UI-007_RIGHT_PROPERTIES_PANEL",
    "UI-008_REPORT_PREVIEW_AND_STATUS_BAR",
    "UI-009_VISUAL_QA_AND_SCREENSHOT_CAPTURE",
    "UI-010_FINAL_POLISH_PASS",
]

ALLOWED_NEXT_STEPS = {
    "OSW-FUNC-021_PLUGIN_INSTALL_HARDENING",
    "OSW-FUNC-021_PACKAGING_RELEASE_DOCS",
    None,
}

FORBIDDEN_STAGED_PARTS = (
    ".codex/reports/",
    "artifacts/release/",
    "artifacts/ui/",
    "artifacts/mesh/",
    "artifacts/mat/",
    "artifacts/curves/",
    "artifacts/report/",
    "artifacts/calculix/",
    "artifacts/openfoam/",
    "artifacts/chm/",
    "artifacts/field/",
)


def load_json(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def missing_completed(data: dict[str, object], expected: list[str], *, label: str) -> list[str]:
    completed = data.get("completed")
    if not isinstance(completed, list):
        return [f"{label} queue has no completed list"]
    completed_set = {str(item) for item in completed}
    return [f"{label} queue missing {step}" for step in expected if step not in completed_set]


def staged_paths(root: Path) -> list[str]:
    proc = capture(["git", "diff", "--cached", "--name-only"], cwd=root)
    if proc.returncode != 0:
        raise ValueError(proc.stderr.strip() or "git staged path check failed")
    return [line.replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]


def duplicate_paths(root: Path) -> list[str]:
    proc = capture(["git", "ls-files", "--others", "--exclude-standard"], cwd=root)
    if proc.returncode != 0:
        raise ValueError(proc.stderr.strip() or "git untracked path check failed")
    return [
        line
        for line in proc.stdout.splitlines()
        if " (1)." in line or line.endswith(" (1).json") or line.endswith(" (1).md")
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-missing-report",
        action="store_true",
        help="Do not fail when the release report file is absent.",
    )
    args = parser.parse_args()

    root = repo_root()
    failures: list[str] = []
    warnings: list[str] = []

    func_state = load_json(root / ".codex" / "func_queue_state.json")
    ui_state = load_json(root / ".codex" / "ui_queue_state.json")

    failures.extend(missing_completed(func_state, FUNC_STEPS, label="functional"))
    failures.extend(missing_completed(ui_state, UI_STEPS, label="UI"))

    if func_state.get("current_step") is not None:
        failures.append("functional current_step must be null after release-gate completion")
    if func_state.get("next_step") not in ALLOWED_NEXT_STEPS:
        failures.append(f"unexpected functional next_step: {func_state.get('next_step')!r}")
    if ui_state.get("status") != "complete":
        failures.append("UI queue status must remain complete")

    report_value = func_state.get("last_report")
    report_path = root / str(report_value) if report_value else root / "_missing_report"
    if not report_value:
        failures.append("functional last_report is missing")
    elif not report_path.exists() and not args.allow_missing_report:
        failures.append(f"release report is missing: {report_value}")

    staged = staged_paths(root)
    forbidden_staged = [
        path
        for path in staged
        if any(path.startswith(part) for part in FORBIDDEN_STAGED_PARTS) or " (1)." in path
    ]
    if forbidden_staged:
        failures.append("forbidden runtime/report/duplicate files are staged:")
        failures.extend(f"  - {path}" for path in forbidden_staged)

    duplicates = duplicate_paths(root)
    if duplicates:
        warnings.append(f"untracked duplicate desktop files present: {len(duplicates)}")

    if failures:
        print("[fail] Release gate invariants failed:")
        for failure in failures:
            print(f"  - {failure}")
        for warning in warnings:
            print(f"[warn] {warning}")
        return 1

    print("[ok] Release gate queue, report, UI, and staged-artifact invariants passed.")
    for warning in warnings:
        print(f"[warn] {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
