#!/usr/bin/env python3
"""Placeholder-safe plugin manifest checker for early OSW harness work."""

from __future__ import annotations

from _common import repo_root

REQUIRED_FIELDS = {"id", "display_name", "version", "type", "entry_point", "capabilities"}


def main() -> int:
    root = repo_root()
    manifest_paths = list((root / "src" / "osw" / "plugins").rglob("*.manifest.*"))
    failures: list[str] = []
    for path in manifest_paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        missing = [field for field in REQUIRED_FIELDS if field not in text]
        if missing:
            failures.append(f"{path.relative_to(root)} missing fields: {', '.join(missing)}")

    if failures:
        print("[fail] Plugin manifest issues:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("[ok] Plugin manifest check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
