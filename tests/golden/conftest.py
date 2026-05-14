"""Golden-suite test path setup."""

from __future__ import annotations

import sys
from pathlib import Path

GOLDEN_ROOT = Path(__file__).parent
if str(GOLDEN_ROOT) not in sys.path:
    sys.path.insert(0, str(GOLDEN_ROOT))
