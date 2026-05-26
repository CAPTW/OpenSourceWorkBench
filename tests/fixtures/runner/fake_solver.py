"""Cross-platform fake solver used by runner tests."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="OSW fake solver test helper")
    parser.add_argument("--mode", choices=["success", "stderr", "fail", "sleep", "artifact"])
    parser.add_argument("--artifact", default="result.dat")
    parser.add_argument("--sleep-seconds", type=float, default=5.0)
    args = parser.parse_args()

    if args.mode == "success":
        print("fake solver stdout: success")
        return 0
    if args.mode == "stderr":
        print("fake solver stderr: warning", file=sys.stderr)
        return 0
    if args.mode == "fail":
        print("fake solver stderr: error", file=sys.stderr)
        return 7
    if args.mode == "sleep":
        time.sleep(args.sleep_seconds)
        print("fake solver woke")
        return 0
    if args.mode == "artifact":
        Path(args.artifact).write_text("fake artifact\n", encoding="utf-8")
        print(f"wrote {args.artifact}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
