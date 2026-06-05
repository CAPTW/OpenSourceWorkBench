from __future__ import annotations

import os
import sys
import time
from pathlib import Path


def main() -> int:
    args = sys.argv[1:]
    mode = os.environ.get("OSW_FAKE_CCX_MODE", "success")
    if args[:1] == ["--mode"]:
        mode = args[1] if len(args) > 1 else mode
        args = args[2:]
    job_name = args[0] if args else "calculix"
    cwd = Path.cwd()
    print(f"fake ccx stdout for {job_name}")
    if mode == "sleep":
        time.sleep(5)
    if mode == "fail":
        print(f"fake ccx stderr for {job_name}", file=sys.stderr)
        return 7
    if mode == "partial":
        (cwd / f"{job_name}.sta").write_text("fake sta\n", encoding="utf-8")
        return 0
    (cwd / f"{job_name}.dat").write_text("fake dat\n", encoding="utf-8")
    (cwd / f"{job_name}.frd").write_text("fake frd\n", encoding="utf-8")
    (cwd / f"{job_name}.sta").write_text("fake sta\n", encoding="utf-8")
    (cwd / f"{job_name}.log").write_text("fake log\n", encoding="utf-8")
    print(f"fake ccx stderr for {job_name}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
