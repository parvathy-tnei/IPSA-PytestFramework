import sys
from pathlib import Path

from runtime_config import CONFIG
from runtime_config import is_network_applicable

from importlib.metadata import version
import ipsa

import pytest

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT / "Resources"))

import Contingency

from utils import (
    compare_against_benchmark,
    assert_comparison_passed
)


SUPPORTED_NETWORKS = {
    "Automation-Contingency Example"
}

CONTINGENCY_DEPTHS = {
    "quick": ["N-1", "N-2"],
    "full": ["N-1", "N-2", "N-3", "N-1-1"],
}


@pytest.mark.comparison
@pytest.mark.contingency
def test_contingency(network, resources_dir):

    if not is_network_applicable(network["name"], SUPPORTED_NETWORKS):
        pytest.skip(
            "Contingency study not applicable for this network"
        )

    ipsa_interface = network["ipsa"]

    print(f"PyIPSA package version: {version('PyIPSA')}")
    print(f"Loaded ipsa module: {ipsa.__file__}")
    print(f"IPSA engine version: {ipsa_interface.GetVersion()}")

    net = network["network"]

    ipsa_version = ipsa_interface.GetVersion()
    model_name = network["path"].name

    contingency_depths = CONTINGENCY_DEPTHS[CONFIG.contingency_depth]
    print(f"Contingency run mode: {CONFIG.contingency_depth}")

    for contingency_depth in contingency_depths:

        print(
            f"\n\nComparing contingency: "
            f"{contingency_depth}"
        )

        output_files = Contingency.runContingency(
            ipsa_interface,
            net,
            str(resources_dir),
            ipsa_version,
            model_name,
            contingency_depth=contingency_depth
        )

        for output_file in output_files:

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
@pytest.mark.contingency
def test_contingency_generation(network, resources_dir):

    if not is_network_applicable(network["name"], SUPPORTED_NETWORKS):
        pytest.skip(
            "Contingency study not applicable for this network"
        )

    ipsa_interface = network["ipsa"]
    net = network["network"]

    model_name = network["path"].name

    contingency_depths = CONTINGENCY_DEPTHS[CONFIG.contingency_depth]
    print(f"Contingency run mode: {CONFIG.contingency_depth}")

    print(
        "\n=========================================="
    )

    print(
        "CONTINGENCY GENERATION"
    )

    print(
        "=========================================="
    )

    for contingency_depth in contingency_depths:

        print(
            f"\n\nRunning contingency depth: "
            f"{contingency_depth}"
        )

        output_files = Contingency.runContingency(
            ipsa_interface,
            net,
            str(resources_dir),
            CONFIG.benchmark_version,
            model_name,
            contingency_depth=contingency_depth
        )

        print(
            f"\nGenerated files for {contingency_depth}:"
        )

        for output_file in output_files:
            print(output_file)