from __future__ import annotations

import os
import sys
import time
from pathlib import Path


def main() -> int:
    mode = os.environ.get("OSW_FAKE_OPENFOAM_MODE", "success")
    solver = Path(sys.argv[0]).stem or "icoFoam"
    if mode == "sleep":
        time.sleep(5.0)
        return 0
    if mode == "fail":
        print("Fake OpenFOAM fatal error", file=sys.stderr)
        return 3
    if mode == "partial":
        text = (
            "Time = 1\n"
            "Solving for Ux, Initial residual = 0.1, "
            "Final residual = 0.02, No Iterations 1\n"
        )
        Path(f"log.{solver}").write_text(text, encoding="utf-8")
        print(text, end="")
        return 0
    text = "\n".join(
        [
            "Time = 1",
            (
                "smoothSolver:  Solving for Ux, Initial residual = 0.1, "
                "Final residual = 0.01, No Iterations 2"
            ),
            (
                "smoothSolver:  Solving for Uy, Initial residual = 0.2, "
                "Final residual = 0.02, No Iterations 2"
            ),
            (
                "smoothSolver:  Solving for Uz, Initial residual = 0.3, "
                "Final residual = 0.03, No Iterations 2"
            ),
            (
                "GAMG:  Solving for p, Initial residual = 0.4, "
                "Final residual = 0.04, No Iterations 3"
            ),
            "End",
            "",
        ]
    )
    Path(f"log.{solver}").write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
