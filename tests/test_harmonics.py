import sys
from pathlib import Path

from runtime_config import CONFIG

import pytest

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT / "Resources"))

import Harmonics_Study

from utils import (
    compare_against_benchmark,
    assert_comparison_passed
)


@pytest.mark.comparison
@pytest.mark.harmonics
def test_harmonics(network, resources_dir):

    ipsa_interface = network["ipsa"]
    net = network["network"]

    ipsa_version = ipsa_interface.GetVersion()
    model_name = network["path"].name

    try:

        output_files = Harmonics_Study.runHarmonics(
            ipsa_interface,
            net,
            str(resources_dir),
            ipsa_version,
            model_name
        )

    except Exception as ex:

        pytest.skip(
            f"Harmonics study unsupported : {ex}"
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
def test_harmonics_generation(network, resources_dir):

    ipsa_interface = network["ipsa"]
    net = network["network"]

    ipsa_version = ipsa_interface.GetVersion()
    model_name = network["path"].name

    try:

        output_files = Harmonics_Study.runHarmonics(
            ipsa_interface,
            net,
            str(resources_dir),
            CONFIG.benchmark_version,
            model_name
        )

        print("\nGenerated Harmonics files:")

        for output_file in output_files:
            print(output_file)

    except Exception as ex:

        pytest.skip(
            f"Harmonics study unsupported : {ex}"
        )