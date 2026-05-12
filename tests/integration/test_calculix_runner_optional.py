from __future__ import annotations

import shutil

import pytest

from osw.solvers.calculix.ccx_runner import CalculixCcxRunner


def test_real_ccx_detection_is_optional() -> None:
    if shutil.which("ccx") is None:
        pytest.skip("CalculiX ccx executable is not installed.")

    lookup = CalculixCcxRunner().detect_executable()

    assert lookup.found
    assert lookup.path is not None
