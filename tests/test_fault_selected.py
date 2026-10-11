import sys
from pathlib import Path

from runtime_config import CONFIG
import pytest

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT / "Resources"))

import Fault_Level

from utils import (
    compare_against_benchmark,
    assert_comparison_passed
)


SUPPORTED_NETWORKS = {
    "IEEE 14 Bus Dynamic Model",
    "SuperGrid R1",
    "ENWL_INM_AllGen_240423",
    "NGED-West Midlands-Connected_CDP",
    "SPM Current Model CIM R0.69",
    "Simple Defined Fault"
} 

@pytest.mark.comparison
@pytest.mark.fault_selected
def test_fault_selected_busbars(network, resources_dir):

    if network["name"] not in SUPPORTED_NETWORKS:
        pytest.skip(
            "Selected busbar study not applicable"
        )

    ipsa_interface = network["ipsa"]
    net = network["network"]

    ipsa_version = ipsa_interface.GetVersion()

    model_name = network["path"].name

    output_file = Fault_Level.run_fault_level(
        net,
        str(resources_dir),
        ipsa_version,
        model_name,
        "Fault levels on selected busbars"
    )

    comparison_status, differences, diff_file = \
        compare_against_benchmark(
            output_file,
            ipsa_version
        )

    assert_comparison_passed(
        comparison_status,
        differences,
        diff_file
    )

@pytest.mark.generation
def test_fault_selected_generation(network, resources_dir):

    if network["name"] not in SUPPORTED_NETWORKS:
        pytest.skip(
            "Selected busbar study not applicable"
        )

    ipsa_interface = network["ipsa"]
    net = network["network"]

    ipsa_version = ipsa_interface.GetVersion()

    model_name = network["path"].name

    output_file = Fault_Level.run_fault_level(
        net,
        str(resources_dir),
        CONFIG.benchmark_version,
        model_name,
        "Fault levels on selected busbars"
    )