from __future__ import annotations

import os
import sys
import time
from pathlib import Path


def main() -> int:
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    script = Path(args[0]).name if args else ""
    mode = os.environ.get("OSW_FAKE_OCTAVE_MODE", "")
    if not mode:
        if "run_error" in script:
            mode = "fail"
        elif "run_long_sleep" in script:
            mode = "sleep"
        elif "run_artifact" in script:
            mode = "artifact"
        else:
            mode = "success"

    print(f"fake octave stdout: {script or '<none>'}")
    if mode == "sleep":
        time.sleep(10)
        return 0
    if mode == "fail":
        print("fake octave stderr: intentional failure", file=sys.stderr)
        return 7
    if mode == "artifact":
        Path("artifact.csv").write_text("x,y\n1,2\n", encoding="utf-8")
        print("fake octave wrote artifact.csv")
        return 0
    Path("result.txt").write_text("fake octave result\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
