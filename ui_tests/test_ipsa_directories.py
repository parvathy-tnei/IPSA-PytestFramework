import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

def get_ipsa_engine_version() -> str:
    try:
        import ipsa
    except ImportError as error:
        raise RuntimeError("Could not import the PyIPSA engine module.") from error

    try:
        version = ipsa.GetInterface().GetVersion()
    except Exception as error:
        raise RuntimeError(f"Could not read the IPSA engine version: {error}") from error

    if not version:
        raise RuntimeError("The IPSA engine returned an empty version.")
    return str(version)


def discover_ipsa_data_directories(
    engine_version: str,
    program_data_root: Path | None = None,
    public_root: Path | None = None,
) -> tuple[Path | None, Path | None]:
    program_data_root = program_data_root or Path(
        os.environ.get("ProgramData", r"C:\ProgramData")
    )
    public_root = public_root or Path(
        os.environ.get("PUBLIC", r"C:\Users\Public")
    )
    version_match = re.search(r"\d+\.\d+", engine_version)
    if not version_match:
        return None, None

    version_folder = f"IPSA {version_match.group(0)}"
    program_data_version = program_data_root / version_folder
    public_version = public_root / version_folder
    if not program_data_version.is_dir() or not public_version.is_dir():
        return None, None

    return (
        program_data_version / "Templates" / "Templates.i3f",
        public_version / "PyIPSA Examples",
    )

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

# ============================================================
# DISCLAIMER & COUNTDOWN
# ============================================================

def print_pretest_disclaimer():
    banner = """
===============================================================================
                             IMPORTANT DISCLAIMER
===============================================================================
1. DIRECTORY / FILE VERIFICATION:
   This test verifies templates and PyIPSA example scripts for the version
   reported by the active IPSA engine.

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
    try:
        engine_version = get_ipsa_engine_version()
        template_file, scripts_dir = discover_ipsa_data_directories(engine_version)
        record(results, "IPSA engine version", True, engine_version)
    except RuntimeError as error:
        engine_version = None
        template_file = None
        scripts_dir = None
        record(results, "IPSA engine version", False, str(error))

    # 1. Template directory and file checks
    template_directory = template_file.parent if template_file else None
    record(
        results,
        "Template directory exists",
        template_directory is not None and template_directory.is_dir(),
        str(template_directory) if template_directory else "No matching IPSA version found",
    )

    record(
        results,
        "Templates.i3f exists",
        template_file is not None and template_file.is_file(),
        str(template_file) if template_file else f"No IPSA data folders found for engine version {engine_version}",
    )

    # 2. Script directory check
    scripts_dir_exists = scripts_dir is not None and scripts_dir.is_dir()
    record(
        results,
        "Scripts directory exists",
        scripts_dir_exists,
        str(scripts_dir) if scripts_dir else f"No IPSA data folders found for engine version {engine_version}",
    )

    # 3. Individual script checks
    if scripts_dir_exists:
        for script_name in EXPECTED_SCRIPTS:
            candidates = [
                scripts_dir / f"{script_name}.py",
                scripts_dir / f"{script_name}.pyw",
            ]
            matches = [path for path in candidates if path.is_file()]

            if not matches:
                matches = [
                    path
                    for path in scripts_dir.rglob("*")
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

    print("\n".join(summary_lines))


def main() -> int:
    print_pretest_disclaimer()
    results = run_filesystem_checks()
    save_report(results)
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())