import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_TESTS = Path(__file__).resolve().parent
SRC_ROOT = REPO_ROOT / "src"

for path in (REPO_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

tests_module = types.ModuleType("tests")
tests_module.__path__ = [str(LOCAL_TESTS)]  # type: ignore[attr-defined]
sys.modules["tests"] = tests_module
