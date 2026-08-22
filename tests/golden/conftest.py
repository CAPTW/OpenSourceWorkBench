"""Golden-suite test path setup."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

GOLDEN_ROOT = Path(__file__).parent
HELPER_PATH = GOLDEN_ROOT / "helpers.py"

if str(GOLDEN_ROOT) not in sys.path:
    sys.path.insert(0, str(GOLDEN_ROOT))

# Pytest 9 prepends ``tests/``, which would otherwise import ``tests/helpers``
# as top-level ``helpers`` and hide this suite's normalizer. Bind the golden
# helper module explicitly so collection is host- and import-mode-independent.
_spec = importlib.util.spec_from_file_location("helpers", HELPER_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load golden helpers from {HELPER_PATH}")
_helpers = importlib.util.module_from_spec(_spec)
sys.modules["helpers"] = _helpers
_spec.loader.exec_module(_helpers)
