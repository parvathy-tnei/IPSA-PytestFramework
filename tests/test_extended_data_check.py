
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Resources"))

import ExtendedDataCheck


@pytest.mark.extended_data
def test_extended_data_check(network):
    net = network["network"]

    results = ExtendedDataCheck.run_extended_data_check(net)

    assert results, "No Extended Data tests were executed."

    for result in results:
        assert result["Add"] == "PASS"
        assert result["Delete"] == "PASS"