from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="success", choices=("success", "fail", "sleep"))
    parser.add_argument("geo", nargs="?")
    parser.add_argument("-1", dest="dim1", action="store_true")
    parser.add_argument("-2", dest="dim2", action="store_true")
    parser.add_argument("-3", dest="dim3", action="store_true")
    parser.add_argument("-format", default="msh2")
    parser.add_argument("-o", dest="output", default="")
    args = parser.parse_args()
    if args.mode == "sleep":
        time.sleep(10)
        return 0
    if args.mode == "fail":
        print("fake gmsh failed intentionally", file=sys.stderr)
        return 3
    output = Path(args.output or "fake.msh")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "$MeshFormat\n2.2 0 8\n$EndMeshFormat\n",
        encoding="utf-8",
    )
    print(f"fake gmsh wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
