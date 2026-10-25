import sys
import time
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

# Hardcoded system directories
TEMPLATE_FILE = Path(r"C:\ProgramData\IPSA 3.3\Templates\Templates.i3f")
SCRIPTS_DIR = Path(r"C:\Users\Public\IPSA 3.3\PyIPSA Examples")

EXPECTED_SCRIPTS = [
    "All_Data_Tables",
    "all_loadflow_results",
    "arcflash_report",
    "arcflash_report_with_word",
    "configure_extendeddata_dar",
    "configure_extendeddata_dcr",
    "contingency_report",
    "contingency_report_with_word",
    "harmonicsource_table_export",
    "loadflow_results_by_busbar",
    "loadflow_summary",
]

REPORT_FILE = Path.cwd() / "ipsa_directories_check.txt"


# ============================================================
# DISCLAIMER & COUNTDOWN
# ============================================================

def print_pretest_disclaimer():
    banner = """
===============================================================================
                             IMPORTANT DISCLAIMER
===============================================================================
1. DIRECTORY / FILE VERIFICATION:
   This test verifies installation integrity and standard paths for IPSA 3.3
   templates and PyIPSA example scripts.

2. DO NOT MODIFY FILESYSTEM DURING TEST:
   Ensure no installation, update, or file transfer processes are modifying
   IPSA program or public directories while this test runs.

3. EXECUTION CONTROL:
   Press Ctrl+C at any time during the countdown to abort the test.
===============================================================================
"""
    print(banner)
    print("Verification will begin in 15 seconds. Please read the above instructions...")
    for remaining in range(15, 0, -1):
        sys.stdout.write(f"\rStarting verification in {remaining:2d} seconds... [Press Ctrl+C to cancel]")
        sys.stdout.flush()
        time.sleep(1.0)
    sys.stdout.write("\rRunning filesystem checks quietly. Errors will be reported below...\n\n")
    sys.stdout.flush()


# ============================================================
# TEST HELPERS
# ============================================================

def report_error(message):
    print(f"[{time.strftime('%H:%M:%S')}] ERROR: {message}")


def record(results_dict, description, passed, details=""):
    results_dict[description] = passed
    if not passed:
        err_msg = f"{description}"
        if details:
            err_msg += f" - {details}"
        report_error(err_msg)


# ============================================================
# MAIN VERIFICATION
# ============================================================

def run_filesystem_checks():
    results = {}

    # 1. Template directory and file checks
    record(
        results,
        "Template directory exists",
        TEMPLATE_FILE.parent.is_dir(),
        str(TEMPLATE_FILE.parent),
    )

    record(
        results,
        "Templates.i3f exists",
        TEMPLATE_FILE.is_file(),
        str(TEMPLATE_FILE),
    )

    # 2. Script directory check
    scripts_dir_exists = SCRIPTS_DIR.is_dir()
    record(
        results,
        "Scripts directory exists",
        scripts_dir_exists,
        str(SCRIPTS_DIR),
    )

    # 3. Individual script checks
    if scripts_dir_exists:
        for script_name in EXPECTED_SCRIPTS:
            candidates = [
                SCRIPTS_DIR / f"{script_name}.py",
                SCRIPTS_DIR / f"{script_name}.pyw",
            ]
            matches = [path for path in candidates if path.is_file()]

            if not matches:
                matches = [
                    path
                    for path in SCRIPTS_DIR.rglob("*")
                    if path.is_file()
                    and path.name.lower()
                    in {
                        f"{script_name}.py".lower(),
                        f"{script_name}.pyw".lower(),
                    }
                ]

            record(
                results,
                f"Script: {script_name}",
                bool(matches),
                "File not found (.py or .pyw)",
            )
    else:
        for script_name in EXPECTED_SCRIPTS:
            record(
                results,
                f"Script: {script_name}",
                False,
                "Cannot check because scripts directory is missing",
            )

    return results


def save_report(results):
    passed_count = sum(1 for passed in results.values() if passed)
    failed_count = sum(1 for passed in results.values() if not passed)

    report_lines = [
        f"[{'PASS' if passed else 'FAIL'}] {desc}"
        for desc, passed in results.items()
    ]

    summary_lines = [
        "",
        "=======================================================",
        "                 DIRECTORY CHECK SUMMARY               ",
        "=======================================================",
        f"Date: {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"Total checks: {len(results)}",
        f"Passed: {passed_count}",
        f"Failed: {failed_count}",
        "=======================================================",
    ]

    for desc, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        summary_lines.append(f"{status:<8} {desc}")
    summary_lines.append("=======================================================\n")

    full_report = "\n".join(report_lines + summary_lines)
    REPORT_FILE.write_text(full_report, encoding="utf-8")

    # Print summary to console
    print("\n".join(summary_lines))
    print(f"Report saved to: {REPORT_FILE}")


def main():
    print_pretest_disclaimer()
    results = run_filesystem_checks()
    save_report(results)


if __name__ == "__main__":
    main()