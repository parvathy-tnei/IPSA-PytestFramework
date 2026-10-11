
import sys
from pathlib import Path

import pytest

from runtime_config import CONFIG

from Logger import debug, info, error, setLoggerMode

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT / "Resources"))

import profileloadflow

from utils import (
    compare_against_benchmark,
    assert_comparison_passed,
)

SUPPORTED_NETWORKS = [
    "IEEE 33 Bus Network (Profiles Example)",
]

@pytest.mark.comparison
@pytest.mark.loadflow
@pytest.mark.profile_loadflow
def test_profileloadflow(network, resources_dir):

    if network["name"] not in SUPPORTED_NETWORKS:
        pytest.skip(
            "Profile Load Flow not applicable to this network"
        )
    ipsa_interface = network["ipsa"]
    net = network["network"]

    ipsa_version = ipsa_interface.GetVersion()
    model_name = network["path"].name

    output_file = profileloadflow.run_profile_loadflow(
        ipsa_interface,
        net,
        str(resources_dir),
        ipsa_version,
        model_name,
    )
    

    comparison_status, differences, diff_file = (
        compare_against_benchmark(
            output_file,
            ipsa_version,
        )
    )

    assert_comparison_passed(
        comparison_status,
        differences,
        diff_file,
    )


@pytest.mark.generation
@pytest.mark.profile_loadflow
def test_profileloadflow_generation(network, resources_dir):

    if network["name"] not in SUPPORTED_NETWORKS:
        pytest.skip("Selected busbar study not applicable")
    ipsa_interface = network["ipsa"]
    net = network["network"]

    ipsa_version = ipsa_interface.GetVersion()
    model_name = network["path"].name

    output_file = profileloadflow.run_profile_loadflow(
        ipsa_interface,
        net,
        str(resources_dir),
        CONFIG.benchmark_version,
        model_name,
    )

    assert output_file is not None
    assert Path(output_file).exists(), (
        f"Profile Load Flow output was not created: {output_file}"
    )
