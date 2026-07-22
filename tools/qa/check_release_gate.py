#!/usr/bin/env python3
"""Check static release-gate invariants against tracked canonical evidence.

The strict static gate reads canonical release evidence and the functional/UI
queues from the current committed ``HEAD`` only. It binds a small tracked
manifest to the exact Git blob bytes of the two queue files, so a clean checkout
reproduces the result from tracked state alone. No local, untracked runtime
report is required or inspected. Passing this gate means the tracked static
invariants hold; it is not fresh full-range validation, publication readiness,
or a release authorization.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
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
    "OSW-FUNC-021_PACKAGING_RELEASE_DOCS",
    "OSW-FUNC-022_PLUGIN_INSTALL_HARDENING",
    "OSW-FUNC-023_V0_1_FREEZE_AND_HANDOFF",
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
    "OSW-FUNC-022_PLUGIN_INSTALL_HARDENING",
    "OSW-FUNC-022_V0_1_FREEZE_AND_HANDOFF",
    "OSW-FUNC-023_V0_1_FREEZE_AND_HANDOFF",
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

CANONICAL_EVIDENCE_PATH = ".codex/release_gate_evidence.json"
FUNCTIONAL_QUEUE_PATH = ".codex/func_queue_state.json"
UI_QUEUE_PATH = ".codex/ui_queue_state.json"
CANONICAL_PATHS = (CANONICAL_EVIDENCE_PATH, FUNCTIONAL_QUEUE_PATH, UI_QUEUE_PATH)

REQUIRED_FUNCTIONAL_STEP = "OSW-FUNC-023_V0_1_FREEZE_AND_HANDOFF"
REQUIRED_RELEASE_STATE = "v0.1-internal-rc-frozen"
REQUIRED_UI_STATUS = "complete"

EXPECTED_MANIFEST = {
    "claim_scope": "tracked-static-release-gate-invariants-only",
    "evidence_kind": "osw-release-gate-canonical",
    "functional_queue_path": FUNCTIONAL_QUEUE_PATH,
    "required_functional_step": REQUIRED_FUNCTIONAL_STEP,
    "required_release_state": REQUIRED_RELEASE_STATE,
    "required_ui_status": REQUIRED_UI_STATUS,
    "runtime_report_policy": "local-untracked-noncanonical",
    "schema_version": 1,
    "ui_queue_path": UI_QUEUE_PATH,
    "validation_evidence": "separate-fresh-full-range-required",
}
DIGEST_KEYS = ("functional_queue_sha256", "ui_queue_sha256")
EXPECTED_KEYS = frozenset(EXPECTED_MANIFEST) | frozenset(DIGEST_KEYS)
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class GateInternalError(RuntimeError):
    """Raised when a required read-only Git invocation fails unexpectedly."""


def _git_bytes(root: Path, args: list[str]) -> bytes:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise GateInternalError(f"git {' '.join(args)} failed")
    return proc.stdout


def _ls_tree_entry(root: Path, path: str) -> tuple[str, str] | None:
    """Return ``(mode, object_type)`` for ``path`` at ``HEAD`` or ``None``."""
    proc = subprocess.run(
        ["git", "ls-tree", "HEAD", "--", path],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise GateInternalError("git ls-tree HEAD failed")
    line = proc.stdout.strip()
    if not line:
        return None
    header = line.split("\t", 1)[0]
    fields = header.split()
    if len(fields) < 2:
        raise GateInternalError("git ls-tree returned an unparsable entry")
    return fields[0], fields[1]


def _path_clean(root: Path, path: str) -> bool:
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", path],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise GateInternalError("git status failed")
    return proc.stdout.strip() == ""


def _head_blob(root: Path, path: str) -> bytes:
    return _git_bytes(root, ["cat-file", "blob", f"HEAD:{path}"])


def _noncanonical_path(value: object) -> bool:
    if not isinstance(value, str) or not value or value != value.strip():
        return True
    if "\\" in value or value.startswith("/") or ":" in value:
        return True
    return any(part in ("", ".", "..") for part in value.split("/"))


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def parse_manifest(blob: bytes) -> tuple[dict[str, object] | None, str | None]:
    """Return ``(manifest, None)`` or ``(None, diagnostic)`` for canonical bytes."""
    if blob.startswith(b"\xef\xbb\xbf"):
        return None, "release_evidence_malformed_json: byte-order mark is not allowed"
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError:
        return None, "release_evidence_malformed_json: evidence is not valid UTF-8"
    try:
        obj = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except ValueError as exc:
        return None, f"release_evidence_malformed_json: {exc}"
    if not isinstance(obj, dict):
        return None, "release_evidence_schema_mismatch: evidence must be a JSON object"
    keys = frozenset(obj)
    if keys != EXPECTED_KEYS:
        missing = sorted(EXPECTED_KEYS - keys)
        unknown = sorted(keys - EXPECTED_KEYS)
        return None, (
            f"release_evidence_schema_mismatch: missing={missing} unknown={unknown}"
        )
    for key in ("functional_queue_path", "ui_queue_path"):
        if _noncanonical_path(obj[key]):
            return None, f"release_evidence_path_invalid: {key} is not a canonical path"
    for key, expected in EXPECTED_MANIFEST.items():
        if obj[key] != expected:
            return None, f"release_evidence_schema_mismatch: {key} has an unexpected value"
    for key in DIGEST_KEYS:
        if not isinstance(obj[key], str) or DIGEST_RE.match(obj[key]) is None:
            return None, f"release_evidence_schema_mismatch: {key} is not a lowercase sha256"
    return obj, None


def missing_completed(data: dict[str, object], expected: list[str], *, label: str) -> list[str]:
    completed = data.get("completed")
    if not isinstance(completed, list):
        return [f"{label} queue has no completed list"]
    completed_set = {str(item) for item in completed}
    return [f"{label} queue missing {step}" for step in expected if step not in completed_set]


def staged_paths(root: Path) -> list[str]:
    proc = capture(["git", "diff", "--cached", "--name-only"], cwd=root)
    if proc.returncode != 0:
        raise GateInternalError(proc.stderr.strip() or "git staged path check failed")
    return [line.replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]


def duplicate_paths(root: Path) -> list[str]:
    proc = capture(["git", "ls-files", "--others", "--exclude-standard"], cwd=root)
    if proc.returncode != 0:
        raise GateInternalError(proc.stderr.strip() or "git untracked path check failed")
    return [
        line
        for line in proc.stdout.splitlines()
        if " (1)." in line or line.endswith(" (1).json") or line.endswith(" (1).md")
    ]


def _load_queue(blob: bytes, label: str) -> tuple[dict[str, object] | None, str | None]:
    try:
        obj = json.loads(blob.decode("utf-8"))
    except ValueError as exc:
        return None, f"release_evidence_malformed_json: {label} queue is invalid: {exc}"
    if not isinstance(obj, dict):
        return None, f"release_evidence_schema_mismatch: {label} queue must be a JSON object"
    return obj, None


def evaluate(root: Path) -> tuple[list[str], list[str]]:
    """Return ``(failures, warnings)`` for the tracked static gate at ``HEAD``."""
    failures: list[str] = []
    warnings: list[str] = []

    blobs: dict[str, bytes] = {}
    tree_ok = True
    for path in CANONICAL_PATHS:
        entry = _ls_tree_entry(root, path)
        if entry is None:
            if (root / path).exists():
                failures.append(
                    f"release_evidence_untracked: {path} exists but is not tracked at HEAD"
                )
            else:
                failures.append(f"release_evidence_missing: {path} is not tracked at HEAD")
            tree_ok = False
            continue
        mode, object_type = entry
        if object_type != "blob" or mode != "100644":
            failures.append(f"release_evidence_non_blob: {path} is not a regular tracked blob")
            tree_ok = False
            continue
        if not _path_clean(root, path):
            failures.append(
                f"release_evidence_dirty: {path} differs from HEAD (staged, unstaged, or untracked)"
            )
            tree_ok = False
            continue
        blobs[path] = _head_blob(root, path)

    if not tree_ok:
        return failures, warnings

    manifest, manifest_error = parse_manifest(blobs[CANONICAL_EVIDENCE_PATH])
    if manifest_error is not None:
        failures.append(manifest_error)
        return failures, warnings

    func_digest = hashlib.sha256(blobs[FUNCTIONAL_QUEUE_PATH]).hexdigest()
    if func_digest != manifest["functional_queue_sha256"]:
        failures.append(
            "release_evidence_digest_mismatch: functional queue blob does not match evidence"
        )
    if hashlib.sha256(blobs[UI_QUEUE_PATH]).hexdigest() != manifest["ui_queue_sha256"]:
        failures.append("release_evidence_digest_mismatch: UI queue blob does not match evidence")

    func_state, func_error = _load_queue(blobs[FUNCTIONAL_QUEUE_PATH], "functional")
    ui_state, ui_error = _load_queue(blobs[UI_QUEUE_PATH], "UI")
    if func_error is not None:
        failures.append(func_error)
    if ui_error is not None:
        failures.append(ui_error)
    if func_state is None or ui_state is None:
        return failures, warnings

    failures.extend(missing_completed(func_state, FUNC_STEPS, label="functional"))
    if REQUIRED_FUNCTIONAL_STEP not in {str(item) for item in func_state.get("completed", [])}:
        failures.append(
            "release_evidence_pointer_mismatch: required functional step is not completed"
        )
    if func_state.get("current_step") is not None:
        failures.append("functional current_step must be null after release-gate completion")
    if func_state.get("next_step") not in ALLOWED_NEXT_STEPS:
        failures.append(f"unexpected functional next_step: {func_state.get('next_step')!r}")
    if func_state.get("release_state") != REQUIRED_RELEASE_STATE:
        failures.append(
            "release_evidence_release_state_mismatch: functional release_state is not "
            f"{REQUIRED_RELEASE_STATE!r}"
        )
    if func_state.get("last_report") != CANONICAL_EVIDENCE_PATH:
        failures.append(
            "release_evidence_pointer_mismatch: functional last_report must point to "
            f"{CANONICAL_EVIDENCE_PATH}"
        )

    failures.extend(missing_completed(ui_state, UI_STEPS, label="UI"))
    if ui_state.get("status") != REQUIRED_UI_STATUS:
        failures.append(
            f"release_evidence_ui_status_mismatch: UI status must be {REQUIRED_UI_STATUS!r}"
        )

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

    return failures, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    try:
        root = repo_root()
    except RuntimeError as exc:
        print(f"[fail] release_evidence_internal_git: {exc}")
        return 2

    try:
        failures, warnings = evaluate(root)
    except GateInternalError as exc:
        print(f"[fail] release_evidence_internal_git: {exc}")
        return 2

    if failures:
        print("[fail] Release gate invariants failed:")
        for failure in failures:
            print(f"  - {failure}")
        for warning in warnings:
            print(f"[warn] {warning}")
        return 1

    print("[ok] Tracked static release-gate invariants passed.")
    for warning in warnings:
        print(f"[warn] {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
