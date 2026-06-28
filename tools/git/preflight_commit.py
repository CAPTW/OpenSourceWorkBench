#!/usr/bin/env python3
"""Pre-commit safety checks for OpenSolver Workbench."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

MAX_SECRET_SCAN_BYTES = 2 * 1024 * 1024

RUNTIME_ARTIFACT_PATTERNS = [
    re.compile(r"(^|/)processor[0-9]+(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)postProcessing(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)dynamicCode(/|$)", re.IGNORECASE),
    re.compile(
        r"(^|/)log\.(blockMesh|checkMesh|decomposePar|icoFoam|simpleFoam|"
        r"snappyHexMesh|reconstructPar)$",
        re.IGNORECASE,
    ),
    re.compile(r"\.(frd|sta|cvg|12d|eig|mtx|nam|fcv|rout)$", re.IGNORECASE),
    re.compile(
        r"(^|/)(solver_runs|solver-runs|run_cases|scratch|work|tmp|temp)(/|$)",
        re.IGNORECASE,
    ),
    re.compile(r"(^|/)[0-9]+(\.[0-9]+)?/(U|p|phi|T|nut|k|epsilon|omega)$"),
    re.compile(
        r"(^|/)(reports|generated_reports|generated-reports|report-output)(/|$)",
        re.IGNORECASE,
    ),
    re.compile(r"(^|/)octave-workspace$", re.IGNORECASE),
    re.compile(r"\.(asv|octave-tmp|mat\.tmp)$", re.IGNORECASE),
]

SECRET_PATTERNS = [
    ("private key", re.compile(rb"-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("aws access key", re.compile(rb"AKIA[0-9A-Z]{16}")),
    ("openai-style key", re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b")),
    (
        "secret assignment",
        re.compile(
            rb"(?i)\b(api[_-]?key|secret|token|password|passwd|pwd|private[_-]?key|client[_-]?secret)\b"
            rb"\s*[:=]\s*['\"]?[A-Za-z0-9_./+=:-]{20,}"
        ),
    ),
]

SCOPE_DRIFT_CHECKERS = [
    Path("tools/check_scope_drift.py"),
    Path("tools/scope/check_scope_drift.py"),
    Path("tools/quality/check_scope_drift.py"),
    Path("tools/scope_drift_checker.py"),
]

ARCHITECTURE_CHECKERS = [
    Path("tools/check_architecture.py"),
    Path("tools/architecture/check_architecture.py"),
    Path("tools/arch/check_architecture.py"),
]


@dataclass(frozen=True)
class ExternalCheckResult:
    name: str
    path: Path | None
    returncode: int


def run_git(
    args: Sequence[str],
    *,
    cwd: Path | None = None,
    text: bool = True,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=text,
        check=False,
    )


def repo_root() -> Path:
    proc = run_git(["rev-parse", "--show-toplevel"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "not a git repository")
    return Path(proc.stdout.strip())


def git_status_summary(root: Path) -> str:
    proc = run_git(["status", "--short", "--branch"], cwd=root)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git status failed")
    return proc.stdout.rstrip()


def staged_files(root: Path) -> list[str]:
    proc = run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"], cwd=root)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git diff --cached failed")
    return [item for item in proc.stdout.split("\0") if item]


def is_allowed_fixture_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("/").lower()
    return normalized.startswith("examples/") or normalized.startswith("tests/")


def is_runtime_artifact(path: str) -> bool:
    if is_allowed_fixture_path(path):
        return False
    normalized = path.replace("\\", "/")
    return any(pattern.search(normalized) for pattern in RUNTIME_ARTIFACT_PATTERNS)


def staged_blob(root: Path, path: str) -> bytes | None:
    proc = run_git(["show", f":{path}"], cwd=root, text=False)
    if proc.returncode != 0:
        return None
    return proc.stdout


def redacted_line(line: bytes) -> str:
    text = line.decode("utf-8", errors="replace").strip()
    return re.sub(r"([:=]\s*['\"]?)[^'\"\s]+", r"\1<redacted>", text)


def find_secret_findings(path: str, content: bytes) -> list[str]:
    if b"\0" in content or len(content) > MAX_SECRET_SCAN_BYTES:
        return []

    findings: list[str] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append(f"{path}:{line_number}: possible {label}: {redacted_line(line)}")
    return findings


def run_first_available_checker(
    name: str,
    candidates: Iterable[Path],
    root: Path,
) -> ExternalCheckResult:
    for relative_path in candidates:
        checker_path = root / relative_path
        if checker_path.exists():
            proc = subprocess.run([sys.executable, str(checker_path)], cwd=root, check=False)
            return ExternalCheckResult(name=name, path=relative_path, returncode=proc.returncode)
    return ExternalCheckResult(name=name, path=None, returncode=0)


def print_external_result(result: ExternalCheckResult) -> None:
    if result.path is None:
        print(f"[skip] {result.name}: checker not present")
    elif result.returncode == 0:
        print(f"[ok] {result.name}: {result.path}")
    else:
        print(f"[fail] {result.name}: {result.path} exited {result.returncode}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run OSW staged-file Git safety checks.")
    parser.add_argument("--hook", default="manual", help="Hook name for reporting context.")
    parser.add_argument(
        "--skip-external-checkers",
        action="store_true",
        help="Skip optional scope drift and architecture checkers.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    hard_failures: list[str] = []

    try:
        root = repo_root()
        print(f"OSW preflight ({args.hook})")
        print(git_status_summary(root))

        staged = staged_files(root)
        if not staged:
            print("[info] No staged files detected.")
        else:
            print(f"[info] Staged files: {len(staged)}")

        artifact_paths = [path for path in staged if is_runtime_artifact(path)]
        for path in artifact_paths:
            hard_failures.append(f"runtime artifact staged: {path}")

        for path in staged:
            content = staged_blob(root, path)
            if content is None:
                continue
            hard_failures.extend(find_secret_findings(path, content))

        if not args.skip_external_checkers:
            for result in (
                run_first_available_checker("scope drift", SCOPE_DRIFT_CHECKERS, root),
                run_first_available_checker("architecture", ARCHITECTURE_CHECKERS, root),
            ):
                print_external_result(result)
                if result.returncode != 0:
                    hard_failures.append(f"{result.name} checker failed")

    except Exception as exc:
        print(f"[fail] preflight crashed safely: {exc}", file=sys.stderr)
        return 2

    if hard_failures:
        print("[fail] Hard failures:")
        for failure in hard_failures:
            print(f"  - {failure}")
        return 1

    print("[ok] Preflight checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
