import sys
from pathlib import Path

from runtime_config import CONFIG

import pytest

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT / "Resources"))

import Contingency

from utils import (
    compare_against_benchmark,
    assert_comparison_passed
)

@pytest.mark.comparison
@pytest.mark.contingency
def test_contingency(network, resources_dir):

    ipsa_interface = network["ipsa"]
    net = network["network"]

    ipsa_version = ipsa_interface.GetVersion()
    model_name = network["path"].name

    contingency_depths = [
        "N-1",
        "N-2",
        "N-3",
        "N-1-1"
    ]

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

    ipsa_interface = network["ipsa"]
    net = network["network"]

    model_name = network["path"].name

    contingency_depths = [
        "N-1",
        "N-2",
        "N-3",
        "N-1-1"
    ]

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

            print(
                output_file
            )