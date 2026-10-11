
import os
from pathlib import Path

import pandas as pd

from Logger import debug, info, error




def profileBusbarData(net):
    """
    Collect the documented Profile Load Flow summary values
    for each busbar in the network.

    Returns a pandas DataFrame.
    """
    busbars = net.GetBusbars()

    if not busbars:
        raise RuntimeError(
            "Profile Load Flow cannot export results: "
            "the network contains no busbars."
        )

    rows = []

    for busbar_name, busbar in busbars.items():
        rows.append({
            "Busbar": busbar_name,
            "Minimum Voltage (pu)":
                busbar.GetProfileMinimumVoltagePU(),
            "Median Voltage (pu)":
                busbar.GetProfileMedianVoltagePU(),
            "Maximum Voltage (pu)":
                busbar.GetProfileMaximumVoltagePU()
        })

    return pd.DataFrame(rows)

def profileBranchData(net):
    """
    Collect minimum, median, and maximum profile flow in MVA
    for branches and cables.
    """
    branches = net.GetBranches()
    rows = []

    for name, branch in branches.items():
        rows.append({
            "Branch": name,
            "Minimum Flow (MVA)": (
                branch.GetProfileMinimumFlowMVA()
            ),
            "Median Flow (MVA)": (
                branch.GetProfileMedianFlowMVA()
            ),
            "Maximum Flow (MVA)": (
                branch.GetProfileMaximumFlowMVA()
            ),
        })

    return pd.DataFrame(rows)


def profileTransformerData(net):
    """
    Collect minimum, median, and maximum profile flow in MVA
    for two-winding transformers.
    """
    transformers = net.GetTransformers()
    rows = []

    for name, transformer in transformers.items():
        rows.append({
            "Transformer": name,
            "Minimum Flow (MVA)": (
                transformer.GetProfileMinimumFlowMVA()
            ),
            "Median Flow (MVA)": (
                transformer.GetProfileMedianFlowMVA()
            ),
            "Maximum Flow (MVA)": (
                transformer.GetProfileMaximumFlowMVA()
            ),
        })

    return pd.DataFrame(rows)


def run_profile_loadflow(
    ipsanetwork,
    net,
    cwd,
    ipsa_version,
    IPSA_file_name,
):
    """
    Run IPSA Profile Load Flow and export the documented
    busbar profile summary values to an Excel workbook.

    Returns the generated Excel file path.
    """
    debug(f"Starting Profile Load Flow: {IPSA_file_name}")

    try:
        # Execute Profile Load Flow.
        # The returned integer is the calculation UID.
        calculation_uid = net.RunProfile()

        info(
            "Profile Load Flow calculation UID: "
            f"{calculation_uid}"
        )

        # Read the results from the busbar objects.
        busbar_results = profileBusbarData(net)
        branch_results = profileBranchData(net)
        transformer_results = profileTransformerData(net)

        # Match the existing Loadflow.py folder convention.
        folder = os.path.dirname(cwd)

        results_folder = (
            Path(folder)
            / "Test Results"
            / str(ipsa_version)
        )

        model_name = Path(IPSA_file_name).stem

        output_folder = (
            results_folder
            / model_name
            / "Profile Load Flow"
        )

        output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file = (
            output_folder
            / f"{model_name}_ProfileLoadFlow_{ipsa_version}.xlsx"
        )

        # Export results to Excel.
        with pd.ExcelWriter(
            output_file,
            engine="openpyxl",
        ) as writer:
            busbar_results.to_excel(
                writer,
                sheet_name="Busbar Profile Results",
                index=False,
            )
            if not branch_results.empty:
                branch_results.to_excel(
                    writer,
                    sheet_name="Branch Profile Results",
                    index=False,
                )

            if not transformer_results.empty:
                transformer_results.to_excel(
                    writer,
                    sheet_name="Transformer Profile Results",
                    index=False,
                )
        info(
            "Profile Load Flow results exported to: "
            f"{output_file}"
        )

        return output_file

    except Exception as exc:
        error(
            f"Profile Load Flow failed for "
            f"{IPSA_file_name}: {exc}"
        )
        raise
