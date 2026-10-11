# import os
# from io import StringIO
# from pathlib import Path

# import pandas as pd


# def find_contingency_depth_index(contingency_depth):

#     match contingency_depth:

#         case "N-1":
#             return 1

#         case "N-2":
#             return 2

#         case "N-3":
#             return 3

#         case "N-1-1":
#             return 4

#         case _:
#             return -1


# def get_contingency_result_name(result_id):

#     match result_id:

#         case 0:
#             return "Otherwise"

#         case 1:
#             return "Busbar over voltage"

#         case 2:
#             return "Busbar under voltage"

#         case 3:
#             return "Branch over rating"

#         case 4:
#             return "Transformer over rating"

#         case _:
#             return f"Unknown result ({result_id})"


# def get_contingency_report_table(
#     net,
#     report_type=120
# ):
#     """
#     Get the contingency summary table directly from
#     IPSA's report APIs.

#     Report type 120:
#         All studies in order run

#     Columns returned by IPSA:

#         Switched
#         Run order
#         Solved?
#         Iter
#         Item
#         Severity
#         Over or Under
#         Items exceeding limits
#     """

#     # =========================================================
#     # GET IPSA REPORT COLUMN HEADERS
#     # =========================================================

#     header_html = net.GetStudyRowTitles(
#         report_type
#     )

#     # =========================================================
#     # GET STUDY TITLES
#     #
#     # Keep the titles exactly as IPSA returns them.
#     #
#     # For example:
#     #
#     # [1] - [2]
#     # [4] - [2]
#     # ''
#     # (1)
#     # (2)
#     #
#     # These are valid IPSA report entries.
#     # =========================================================

#     study_titles = net.GetStudies(
#         report_type
#     )

#     # =========================================================
#     # GET EVERY REPORT ROW
#     # =========================================================

#     rows_html = []

#     for title in study_titles:

#         row_html = net.GetStudyRowOutput(
#             report_type,
#             title
#         )

#         rows_html.append(
#             row_html
#         )

#     # =========================================================
#     # BUILD COMPLETE HTML TABLE
#     # =========================================================

#     html_table = f"""
#     <table>
#         {header_html}
#         {''.join(rows_html)}
#     </table>
#     """

#     # =========================================================
#     # CONVERT HTML TO PANDAS DATAFRAME
#     # =========================================================

#     tables = pd.read_html(
#         StringIO(html_table)
#     )

#     if not tables:

#         return pd.DataFrame()

#     dataframe = tables[0]

#     # =========================================================
#     # IPSA HEADER ROW
#     #
#     # pd.read_html() is treating the first row as data.
#     # Promote that row to the actual DataFrame header.
#     # =========================================================

#     dataframe.columns = dataframe.iloc[0]

#     dataframe = dataframe.iloc[1:].reset_index(
#         drop=True
#     )

#     return dataframe


# def runContingency(
#     ipsa_interface,
#     net,
#     cwd,
#     ipsa_version,
#     IPSA_file_name,
#     contingency_depth,
#     extend_to_breakers=False,
#     use_profiles=False
# ):

#     # =========================================================
#     # FIND CONTINGENCY DEPTH INDEX
#     # =========================================================

#     depth = find_contingency_depth_index(
#         contingency_depth
#     )

#     if depth == -1:

#         raise ValueError(
#             f"Invalid contingency depth: "
#             f"{contingency_depth}"
#         )

#     # =========================================================
#     # BASE OUTPUT DIRECTORY
#     #
#     # cwd:
#     #   ...\IPSA-PyTestFW\Resources
#     #
#     # os.path.dirname(cwd):
#     #   ...\IPSA-PyTestFW
#     #
#     # Result:
#     #
#     #   Test Results
#     #       └── <version>
#     #           └── <model>
#     #               └── Contingency Analysis
#     # =========================================================

#     folder = os.path.dirname(cwd)

#     folder_path = (
#         Path(folder)
#         / "Test Results"
#         / f"{ipsa_version}"
#     )

#     folder_path.mkdir(
#         parents=True,
#         exist_ok=True
#     )

#     # =========================================================
#     # GET MODEL NAME WITHOUT FILE EXTENSION
#     #
#     # Example:
#     #
#     # Automation-Contingency Example.i2f
#     #
#     # becomes:
#     #
#     # Automation-Contingency Example
#     # =========================================================

#     model_name = Path(
#         IPSA_file_name
#     ).stem

#     # =========================================================
#     # CREATE CONTINGENCY ANALYSIS DIRECTORY
#     #
#     # ...\Automation-Contingency Example\
#     #       Contingency Analysis
#     # =========================================================

#     contingency_analysis_folder = (
#         folder_path
#         / model_name
#         / "Contingency Analysis"
#     )

#     contingency_analysis_folder.mkdir(
#         parents=True,
#         exist_ok=True
#     )

#     # =========================================================
#     # CREATE DEPTH-SPECIFIC FOLDER
#     #
#     # Example:
#     #
#     # ...\Contingency Analysis\N-1
#     #
#     # or:
#     #
#     # ...\Contingency Analysis\N-2
#     # =========================================================

#     depth_folder = (
#         contingency_analysis_folder
#         / contingency_depth
#     )

#     depth_folder.mkdir(
#         parents=True,
#         exist_ok=True
#     )

#     # =========================================================
#     # CREATE CONTINGENCY
#     # =========================================================

#     print(
#         f"\n=========================================="
#     )

#     print(
#         f"Creating contingency: "
#         f"{contingency_depth}"
#     )

#     print(
#         f"Contingency depth index: "
#         f"{depth}"
#     )

#     print(
#         f"=========================================="
#     )

#     contingency_uid = net.CreateContingency(
#         depth,
#         extend_to_breakers
#     )

#     print(
#         f"Created contingency UID: "
#         f"{contingency_uid}"
#     )

#     # =========================================================
#     # RUN CONTINGENCY
#     # =========================================================

#     print(
#         f"Running contingency UID: "
#         f"{contingency_uid}"
#     )

#     net.RunContingency(
#         contingency_uid,
#         use_profiles
#     )

#     print(
#         "Contingency completed"
#     )

#     # =========================================================
#     # GET STUDY INFORMATION
#     # =========================================================

#     all_study_ids = net.GetStudyIDs(
#         120
#     )

#     solved_study_ids = net.GetStudyIDs(
#         121
#     )

#     failed_study_ids = net.GetStudyIDs(
#         124
#     )

#     # =========================================================
#     # PRINT STUDY COUNTS
#     # =========================================================

#     print(
#         "\n========== CONTINGENCY RESULTS =========="
#     )

#     print(
#         "Contingency depth:",
#         contingency_depth
#     )

#     print(
#         "Number of contingency studies:",
#         len(all_study_ids)
#     )

#     print(
#         "Solved studies:",
#         len(solved_study_ids)
#     )

#     print(
#         "Failed studies:",
#         len(failed_study_ids)
#     )

#     # =========================================================
#     # GET EXACT IPSA CONTINGENCY REPORT
#     #
#     # Report type 120:
#     #
#     # All studies in order run
#     #
#     # Columns:
#     #
#     # Switched
#     # Run order
#     # Solved?
#     # Iter
#     # Item
#     # Severity
#     # Over or Under
#     # Items exceeding limits
#     # =========================================================

#     print(
#         "\n========== CONTINGENCY REPORT =========="
#     )

#     report_type = 120

#     dataframe = get_contingency_report_table(
#         net,
#         report_type
#     )

#     # =========================================================
#     # CHECK REPORT
#     # =========================================================

#     # if dataframe.empty:

#     #     print(
#     #         "\nWARNING: "
#     #         "No contingency report rows were returned."
#     #     )

#     # else:

#     #     print(
#     #         "\nReport columns:"
#     #     )

#     #     print(
#     #         list(dataframe.columns)
#     #     )

#     #     print(
#     #         "\nReport table:"
#     #     )

#     #     print(
#     #         dataframe.to_string(
#     #             index=False
#     #         )
#     #     )

#     print(
#         "\n=========================================="
#     )

#     # =========================================================
#     # CREATE OUTPUT FILE
#     #
#     # Example:
#     #
#     # Automation-Contingency Example_N-1_Contingency_v3.3.0.xlsx
#     #
#     # Automation-Contingency Example_N-2_Contingency_v3.3.0.xlsx
#     #
#     # Automation-Contingency Example_N-3_Contingency_v3.3.0.xlsx
#     #
#     # Automation-Contingency Example_N-1-1_Contingency_v3.3.0.xlsx
#     # =========================================================

#     output_file = (
#         depth_folder
#         / f"{model_name}"
#         f"_{contingency_depth}"
#         f"_Contingency_{ipsa_version}.xlsx"
#     )

#     # =========================================================
#     # WRITE EXCEL
#     # =========================================================

#     dataframe.to_excel(
#         output_file,
#         index=False
#     )

#     # =========================================================
#     # PRINT OUTPUT LOCATION
#     # =========================================================

#     print(
#         "\nGenerated Contingency file:"
#     )

#     print(
#         output_file
#     )

#     # =========================================================
#     # RETURN OUTPUT FILE
#     #
#     # pytest framework expects a list of output files.
#     # =========================================================

#     return [
#         str(output_file)
#     ]



import os
from io import StringIO
from pathlib import Path

import pandas as pd


# =========================================================
# CONTINGENCY CONFIGURATION HELPERS
# =========================================================

def find_contingency_depth_index(contingency_depth):

    match contingency_depth:

        case "N-1":
            return 1

        case "N-2":
            return 2

        case "N-3":
            return 3

        case "N-1-1":
            return 4

        case _:
            return -1


def get_contingency_result_name(result_id):

    match result_id:

        case 0:
            return "Otherwise"

        case 1:
            return "Busbar over voltage"

        case 2:
            return "Busbar under voltage"

        case 3:
            return "Branch over rating"

        case 4:
            return "Transformer over rating"

        case _:
            return f"Unknown result ({result_id})"


# =========================================================
# ORIGINAL IPSA REPORT FUNCTION
#
# Kept unchanged.
# =========================================================

def get_contingency_report_table(
    net,
    report_type=120
):
    """
    Get the contingency summary table directly from
    IPSA's report APIs.
    """

    header_html = net.GetStudyRowTitles(
        report_type
    )

    study_titles = net.GetStudies(
        report_type
    )

    rows_html = []

    for title in study_titles:

        row_html = net.GetStudyRowOutput(
            report_type,
            title
        )

        rows_html.append(
            row_html
        )

    html_table = f"""
    <table>
        {header_html}
        {''.join(rows_html)}
    </table>
    """

    tables = pd.read_html(
        StringIO(html_table)
    )

    if not tables:
        return pd.DataFrame()

    dataframe = tables[0]

    dataframe.columns = dataframe.iloc[0]

    dataframe = dataframe.iloc[1:].reset_index(
        drop=True
    )

    return dataframe


# =========================================================
# NEW: BUSBAR NAME HELPER
# =========================================================

def get_busbar_name(net, busbar_uid):
    """
    Resolve a busbar UID to its IPSA component name.

    Busbar GetName() returns the busbar name.
    """

    if not busbar_uid:
        return ""

    try:
        busbar = net.GetBusbar(
            int(busbar_uid)
        )

        if busbar is not None:
            return str(
                busbar.GetName()
            )

    except Exception as exc:

        print(
            f"Could not resolve busbar UID "
            f"{busbar_uid}: {exc}"
        )

    return ""


# =========================================================
# NEW: BRANCH DETAILS HELPER
# =========================================================

def get_branch_details(net, branch_uid):
    """
    Retrieve branch name, endpoints and standard rating.

    Uses the verified PyIPSA methods:

        branch.GetFromBusbarUID()
        branch.GetToBusbarUID()

    Neither method takes an argument.
    """

    branch = net.GetBranch(
        int(branch_uid)
    )

    if branch is None:

        return {
            "line_name": "",
            "python_name": "",
            "from_bus": "",
            "to_bus": "",
            "rating_mva": ""
        }

    # Python component name, for example 38.36.Line.
    try:
        python_name = str(
            branch.GetName()
        )
    except Exception:
        python_name = ""

    # User-defined IPSA name.
    try:
        line_name = str(
            branch.GetRealName()
        )
    except Exception:
        line_name = ""

    if not line_name.strip():
        line_name = python_name

    # Retrieve actual endpoint UIDs.
    try:
        from_uid = branch.GetFromBusbarUID()
    except Exception as exc:
        print(
            f"Could not retrieve From busbar UID "
            f"for branch {branch_uid}: {exc}"
        )
        from_uid = 0

    try:
        to_uid = branch.GetToBusbarUID()
    except Exception as exc:
        print(
            f"Could not retrieve To busbar UID "
            f"for branch {branch_uid}: {exc}"
        )
        to_uid = 0

    # Resolve endpoint UIDs to busbar names.
    from_bus = get_busbar_name(
        net,
        from_uid
    )

    to_bus = get_busbar_name(
        net,
        to_uid
    )

    # Standard branch rating.
    rating_mva = ""

    try:
        rating_mva = branch.GetRatingMVA(0)
    except Exception:
        try:
            rating_mva = branch.GetRatingMVA(1, 0)
        except Exception as exc:
            print(
                f"Could not retrieve rating for "
                f"branch {branch_uid}: {exc}"
            )

    return {
        "line_name": line_name,
        "python_name": python_name,
        "from_bus": from_bus,
        "to_bus": to_bus,
        "rating_mva": rating_mva
    }


# =========================================================
# NEW: RESULT MAGNITUDE HELPER
# =========================================================

def get_contingency_result_magnitude(
    net,
    study_id,
    component_uid
):
    """
    Retrieve the result magnitude for a component
    in a particular contingency study.
    """

    try:
        return net.GetContingencyStudyResultMagnitude(
            int(study_id),
            int(component_uid)
        )

    except Exception as exc:

        print(
            f"Could not retrieve magnitude for "
            f"study {study_id}, component {component_uid}: "
            f"{exc}"
        )

        return ""


# =========================================================
# NEW: COLLECT BUSBAR VIOLATIONS AND OVERLOADED LINES
# =========================================================

def get_contingency_detail_tables(
    net,
    report_type=120
):
    """
    Build two detailed DataFrames from the contingency
    component results:

        1. Busbar Violations
        2. Overloaded Lines

    Uses report_type 120 for both study IDs and study
    titles so their order can be checked consistently
    against the IPSA report.

    Result codes:
        1 = Busbar overvoltage
        2 = Busbar undervoltage
        3 = Branch overrating
        4 = Transformer overrating
    """

    # -----------------------------------------------------
    # GET STUDY IDS AND TITLES
    # -----------------------------------------------------

    study_ids = net.GetStudyIDs(
        report_type
    )

    study_titles = net.GetStudies(
        report_type
    )

    if study_ids is None:
        study_ids = []

    if study_titles is None:
        study_titles = []

    study_ids = list(study_ids)
    study_titles = list(study_titles)

    print(
        "\n========== DETAILED CONTINGENCY RESULTS =========="
    )

    print(
        "Study IDs:",
        len(study_ids)
    )

    print(
        "Study titles:",
        len(study_titles)
    )

    if len(study_ids) != len(study_titles):

        print(
            "WARNING: Study ID count differs from "
            "the study title count. Verify ordering "
            "against the IPSA report."
        )

    # -----------------------------------------------------
    # OUTPUT ROW COLLECTIONS
    # -----------------------------------------------------

    busbar_rows = []
    overloaded_line_rows = []

    # -----------------------------------------------------
    # PROCESS EACH STUDY
    # -----------------------------------------------------

    for index, study_id in enumerate(study_ids):

        try:
            study_id = int(study_id)
        except (TypeError, ValueError):

            print(
                f"Skipping invalid study ID: {study_id}"
            )

            continue

        if index < len(study_titles):
            contingency_title = str(
                study_titles[index]
            )
        else:
            contingency_title = ""

        # print(
        #     f"Processing study {study_id}: "
        #     f"{contingency_title}"
        # )

        # Get component UID -> result code mapping.
        try:
            component_results = (
                net.GetContingencyStudyItemResults(
                    study_id
                )
            )
        except Exception as exc:

            print(
                f"Could not retrieve component results "
                f"for study {study_id}: {exc}"
            )

            continue

        if not component_results:
            continue

        # -------------------------------------------------
        # PROCESS COMPONENT RESULTS
        # -------------------------------------------------

        for component_uid, result_code in (
            component_results.items()
        ):

            try:
                component_uid = int(
                    component_uid
                )

                result_code = int(
                    result_code
                )

            except (TypeError, ValueError):
                continue

            result_name = get_contingency_result_name(
                result_code
            )

            # =============================================
            # A. BUSBAR VOLTAGE VIOLATIONS
            # =============================================

            if result_code in (1, 2):

                busbar_name = get_busbar_name(
                    net,
                    component_uid
                )

                voltage_pu = (
                    get_contingency_result_magnitude(
                        net,
                        study_id,
                        component_uid
                    )
                )

                busbar_rows.append([
                    index + 1,
                    study_id,
                    contingency_title,
                    component_uid,
                    busbar_name,
                    result_name,
                    voltage_pu
                ])

            # =============================================
            # B. OVERLOADED BRANCHES
            # =============================================

            elif result_code == 3:

                details = get_branch_details(
                    net,
                    component_uid
                )

                flow_mva = (
                    get_contingency_result_magnitude(
                        net,
                        study_id,
                        component_uid
                    )
                )

                overloaded_line_rows.append([
                    index + 1,
                    study_id,
                    contingency_title,
                    component_uid,
                    details["line_name"],
                    details["python_name"],
                    details["from_bus"],
                    details["to_bus"],
                    result_name,
                    flow_mva,
                    details["rating_mva"]
                ])

            # =============================================
            # C. TRANSFORMER OVERRATING
            #
            # Not added to the overloaded-lines sheet,
            # which is specifically for branches.
            # =============================================

    # -----------------------------------------------------
    # BUILD BUSBAR DATAFRAME
    # -----------------------------------------------------

    busbar_columns = [
        "Run Order",
        "Study ID",
        "Switching / Contingency",
        "Busbar UID",
        "Busbar Name",
        "Result Type",
        "Voltage Magnitude (pu)"
    ]

    busbar_dataframe = pd.DataFrame(
        busbar_rows,
        columns=busbar_columns
    )

    # -----------------------------------------------------
    # BUILD OVERLOADED-LINES DATAFRAME
    # -----------------------------------------------------

    overloaded_line_columns = [
        "Run Order",
        "Study ID",
        "Switching / Contingency",
        "Branch UID",
        "Line Name",
        "Python Component Name",
        "From Bus",
        "To Bus",
        "Result Type",
        "Flow (MVA)",
        "Standard Rating (MVA)"
    ]

    overloaded_line_dataframe = pd.DataFrame(
        overloaded_line_rows,
        columns=overloaded_line_columns
    )

    print(
        "\nBusbar violations:",
        len(busbar_dataframe)
    )

    print(
        "Overloaded line records:",
        len(overloaded_line_dataframe)
    )

    print(
        "=================================================="
    )

    return (
        busbar_dataframe,
        overloaded_line_dataframe
    )


# =========================================================
# MAIN CONTINGENCY FUNCTION
# =========================================================

def runContingency(
    ipsa_interface,
    net,
    cwd,
    ipsa_version,
    IPSA_file_name,
    contingency_depth,
    extend_to_breakers=False,
    use_profiles=False
):

    # =====================================================
    # FIND CONTINGENCY DEPTH INDEX
    # =====================================================

    depth = find_contingency_depth_index(
        contingency_depth
    )

    if depth == -1:

        raise ValueError(
            f"Invalid contingency depth: "
            f"{contingency_depth}"
        )

    # =====================================================
    # BASE OUTPUT DIRECTORY
    # =====================================================

    folder = os.path.dirname(cwd)

    folder_path = (
        Path(folder)
        / "Test Results"
        / f"{ipsa_version}"
    )

    folder_path.mkdir(
        parents=True,
        exist_ok=True
    )

    # =====================================================
    # MODEL NAME
    # =====================================================

    model_name = Path(
        IPSA_file_name
    ).stem

    # =====================================================
    # CONTINGENCY OUTPUT DIRECTORY
    # =====================================================

    contingency_analysis_folder = (
        folder_path
        / model_name
        / "Contingency Analysis"
    )

    contingency_analysis_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    # =====================================================
    # DEPTH-SPECIFIC DIRECTORY
    # =====================================================

    depth_folder = (
        contingency_analysis_folder
        / contingency_depth
    )

    depth_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    # =====================================================
    # CREATE CONTINGENCY
    # =====================================================

    print(
        "\n=========================================="
    )

    print(
        f"Creating contingency: {contingency_depth}"
    )

    print(
        f"Contingency depth index: {depth}"
    )

    print(
        "=========================================="
    )

    contingency_uid = net.CreateContingency(
        depth,
        extend_to_breakers
    )

    print(
        f"Created contingency UID: {contingency_uid}"
    )

    # =====================================================
    # RUN CONTINGENCY
    # =====================================================

    print(
        f"Running contingency UID: {contingency_uid}"
    )

    net.RunContingency(
        contingency_uid,
        use_profiles
    )

    print(
        "Contingency completed"
    )

    # =====================================================
    # GET STUDY INFORMATION
    #
    # Original report logic retained.
    # =====================================================

    all_study_ids = net.GetStudyIDs(
        120
    )

    solved_study_ids = net.GetStudyIDs(
        121
    )

    failed_study_ids = net.GetStudyIDs(
        124
    )

    # =====================================================
    # PRINT STUDY COUNTS
    # =====================================================

    print(
        "\n========== CONTINGENCY RESULTS =========="
    )

    print(
        "Contingency depth:",
        contingency_depth
    )

    print(
        "Number of contingency studies:",
        len(all_study_ids)
    )

    print(
        "Solved studies:",
        len(solved_study_ids)
    )

    print(
        "Failed studies:",
        len(failed_study_ids)
    )

    # =====================================================
    # ORIGINAL IPSA CONTINGENCY REPORT
    #
    # Do not change this DataFrame's construction.
    # =====================================================

    print(
        "\n========== CONTINGENCY REPORT =========="
    )

    report_type = 120

    dataframe = get_contingency_report_table(
        net,
        report_type
    )

    print(
        "\n=========================================="
    )

    # =====================================================
    # NEW: COLLECT DETAILED RESULTS
    #
    # These DataFrames are separate from the original
    # report DataFrame.
    # =====================================================

    (
        busbar_dataframe,
        overloaded_line_dataframe
    ) = get_contingency_detail_tables(
        net,
        report_type=120
    )

    # =====================================================
    # ORIGINAL OUTPUT FILE NAME
    #
    # Keep this unchanged for benchmark compatibility.
    # =====================================================

    output_file = (
        depth_folder
        / f"{model_name}"
        f"_{contingency_depth}"
        f"_Contingency_{ipsa_version}.xlsx"
    )

    # =====================================================
    # WRITE ALL THREE SHEETS TO THE SAME EXCEL FILE
    #
    # IMPORTANT:
    #
    # The original report is written first using the
    # same default sheet name ("Sheet1") and index=False.
    #
    # Do not rename the original sheet, since the
    # benchmark comparison may depend on it.
    # =====================================================

    with pd.ExcelWriter(
        output_file,
        engine="openpyxl"
    ) as writer:

        # ---------------------------------------------
        # ORIGINAL SHEET
        # Same DataFrame, same default sheet name,
        # same index setting as your original code.
        # ---------------------------------------------

        dataframe.to_excel(
            writer,
            index=False
        )

        # ---------------------------------------------
        # NEW SHEET 1: BUSBAR VIOLATIONS
        # ---------------------------------------------

        busbar_dataframe.to_excel(
            writer,
            sheet_name="Busbar Violations",
            index=False
        )

        # ---------------------------------------------
        # NEW SHEET 2: OVERLOADED LINES
        # ---------------------------------------------

        overloaded_line_dataframe.to_excel(
            writer,
            sheet_name="Overloaded Lines",
            index=False
        )

    # =====================================================
    # PRINT OUTPUT LOCATION
    # =====================================================

    print(
        "\nGenerated Contingency Excel file:"
    )

    print(
        output_file
    )

    print(
        "\nWorksheets created:"
    )

    print(
        "1. Sheet1 - Original IPSA contingency report"
    )

    print(
        "2. Busbar Violations"
    )

    print(
        "3. Overloaded Lines"
    )

    # =====================================================
    # RETURN OUTPUT FILE
    #
    # Keep one output path so the existing pytest
    # benchmark comparison loop remains unchanged.
    # =====================================================

    return [
        str(output_file)
    ]