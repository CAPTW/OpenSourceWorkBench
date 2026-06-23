from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GUI_TEST_DIR = REPO_ROOT / "tests" / "gui"


@dataclass(frozen=True)
class FileResult:
    file: str
    command: list[str]
    returncode: int
    status: str


def discover_gui_tests() -> list[Path]:
    return sorted(GUI_TEST_DIR.glob("test_*.py"), key=lambda path: path.name)


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _command_for(path: Path) -> list[str]:
    return [sys.executable, "-m", "pytest", _relative(path), "-q"]


def _write_summary(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_files(paths: list[Path]) -> tuple[list[FileResult], int]:
    results: list[FileResult] = []
    worst_returncode = 0

    for test_file in paths:
        relative = _relative(test_file)
        command = _command_for(test_file)
        print(f"[gui-fallback] RUN {relative}", flush=True)
        completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
        status = "passed" if completed.returncode == 0 else "failed"
        print(f"[gui-fallback] {status.upper()} {relative}", flush=True)
        results.append(
            FileResult(
                file=relative,
                command=command,
                returncode=completed.returncode,
                status=status,
            )
        )
        if completed.returncode != 0 and worst_returncode == 0:
            worst_returncode = completed.returncode

    return results, worst_returncode


def build_summary(mode: str, paths: list[Path], results: list[FileResult]) -> dict[str, object]:
    passed = sum(1 for result in results if result.status == "passed")
    failed = sum(1 for result in results if result.status == "failed")
    return {
        "mode": mode,
        "total": len(paths),
        "passed": passed,
        "failed": failed,
        "files": [_relative(path) for path in paths],
        "results": [asdict(result) for result in results],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run GUI tests one file at a time after an aggregate timeout."
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="List discovered GUI test files without running pytest.",
    )
    parser.add_argument(
        "--json-summary",
        type=Path,
        help="Write a JSON summary to this explicit path.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    paths = discover_gui_tests()

    if args.list_only:
        for path in paths:
            print(_relative(path))
        if args.json_summary is not None:
            _write_summary(args.json_summary, build_summary("list-only", paths, []))
        return 0

    results, returncode = run_files(paths)
    if args.json_summary is not None:
        _write_summary(args.json_summary, build_summary("run", paths, results))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
