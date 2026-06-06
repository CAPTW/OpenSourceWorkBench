#!/usr/bin/env python3
"""Detect OSW v0.1 scope drift in text or changed files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import build_base_arg, changed_files, repo_root, text_files

FORBIDDEN_PATTERNS = [
    ("Simulink", re.compile(r"\bSimulink\b|\.slx\b", re.IGNORECASE)),
    (".mlapp", re.compile(r"\.mlapp\b", re.IGNORECASE)),
    (
        "commercial native CAD",
        re.compile(
            r"\b(SolidWorks|CATIA|NX|Creo)\b|native commercial CAD|commercial CAD direct",
            re.IGNORECASE,
        ),
    ),
    (
        "full ANSYS clone",
        re.compile(r"full\s+ANSYS|ANSYS\s+Workbench|ANSYS clone", re.IGNORECASE),
    ),
    (
        "full OpenFOAM UI",
        re.compile(
            r"full\s+OpenFOAM|OpenFOAM\s+(solver\s+)?UI|broad\s+OpenFOAM",
            re.IGNORECASE,
        ),
    ),
    (
        "industrial certification",
        re.compile(
            r"industrial certification|certified|compliance claim|production CAE",
            re.IGNORECASE,
        ),
    ),
    (
        "GUI direct solver execution",
        re.compile(
            r"GUI direct .*subprocess|GUI-triggered direct|GUI.*runs?.*solver",
            re.IGNORECASE,
        ),
    ),
    (
        "automatic unreviewed solver execution",
        re.compile(
            r"automatic\s+unreviewed\s+solver\s+execution|"
            r"unreviewed\s+solver\s+execution\s+from\s+(image|VLM)",
            re.IGNORECASE,
        ),
    ),
    (
        "mandatory Abaqus",
        re.compile(
            r"mandatory\s+Abaqus|Abaqus\s+is\s+(required|mandatory)|requires\s+Abaqus",
            re.IGNORECASE,
        ),
    ),
    (
        "implemented VFEA claim",
        re.compile(
            r"VFEA\s+(is\s+)?implemented|implemented\s+VFEA|VFEA\s+support\s+is\s+available",
            re.IGNORECASE,
        ),
    ),
    ("nonlinear contact/plasticity", re.compile(r"nonlinear contact|plasticity", re.IGNORECASE)),
]

SAFE_CONTEXT = [
    "must not",
    "do not",
    "does not",
    "not a",
    "not full",
    "not support",
    "out of scope",
    "non-goal",
    "hard out-of-scope",
    "forbidden",
    "block",
    "reject",
    "stop",
    "defer",
    "park",
    "parking lot",
    "avoid",
    "ban",
    "never",
    "no ",
    "excluding",
    "without",
    "unless explicitly deferred",
    "future research",
    "review trigger risks",
]


def is_safe_context(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in SAFE_CONTEXT)


def findings_for_text(text: str, *, label: str) -> list[str]:
    findings: list[str] = []
    lines = text.splitlines()
    safe_section = False
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lower()
            safe_section = any(
                marker in heading
                for marker in (
                    "must not",
                    "out of scope",
                    "parking lot",
                    "review trigger",
                    "scope drift",
                    "hard blocker",
                    "stop / park / defer",
                    "prohibited",
                    "non-goal",
                )
            )
        elif "block merge" in stripped.lower() or "blocks merge" in stripped.lower():
            safe_section = True
        context = line + "\n" + "\n".join(lines[max(0, line_no - 4) : line_no])
        for name, pattern in FORBIDDEN_PATTERNS:
            if pattern.search(line) and not (safe_section or is_safe_context(context)):
                findings.append(f"{label}:{line_no}: possible scope drift ({name}): {line.strip()}")
    return findings


def default_scan_paths(root: Path, base: str) -> list[Path]:
    changed = [root / path for path in changed_files(base, root=root)]
    if changed:
        return text_files(
            [
                path
                for path in changed
                if not path.relative_to(root).as_posix().startswith("tests/")
                and path.relative_to(root).as_posix() != "tools/qa/check_scope_drift.py"
            ]
        )
    paths = [
        *Path(root, "README.md").parent.glob("README.md"),
        *Path(root, "docs").glob("*.md"),
        *Path(root, "src").rglob("*.py"),
    ]
    return text_files(paths)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", help="Scan a literal text snippet instead of files.")
    parser.add_argument("--path", action="append", default=[], help="Additional file path to scan.")
    build_base_arg(parser)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root()

    findings: list[str] = []
    if args.text is not None:
        findings.extend(findings_for_text(args.text, label="<text>"))
    else:
        paths = (
            [root / item for item in args.path]
            if args.path
            else default_scan_paths(root, args.base)
        )
        for path in text_files(paths):
            if path.exists():
                findings.extend(
                    findings_for_text(
                        path.read_text(encoding="utf-8"),
                        label=str(path.relative_to(root)),
                    )
                )

    if findings:
        print("[fail] Scope drift findings:")
        for finding in findings:
            print(f"  - {finding}")
        return 1

    print("[ok] No OSW scope drift found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
