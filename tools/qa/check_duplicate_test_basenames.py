#!/usr/bin/env python3
"""Fail when pytest test files share the same basename."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from _common import repo_root


def find_duplicate_test_basenames(tests_root: Path) -> dict[str, list[Path]]:
    """Return duplicate non-__init__.py basenames under the tests tree."""

    paths_by_name: dict[str, list[Path]] = defaultdict(list)
    if not tests_root.exists():
        return {}

    for path in sorted(tests_root.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        paths_by_name[path.name].append(path)

    return {
        name: paths
        for name, paths in sorted(paths_by_name.items())
        if len(paths) > 1
    }


def format_duplicate_report(duplicates: dict[str, list[Path]], *, root: Path) -> str:
    lines = ["Duplicate test file basenames found:"]
    for basename, paths in duplicates.items():
        lines.append(f"  - {basename}")
        for path in paths:
            lines.append(f"    - {path.relative_to(root).as_posix()}")
    return "\n".join(lines)


def main() -> int:
    root = repo_root()
    duplicates = find_duplicate_test_basenames(root / "tests")
    if duplicates:
        print(f"[fail] {format_duplicate_report(duplicates, root=root)}")
        return 1
    print("[ok] No duplicate test file basenames found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
