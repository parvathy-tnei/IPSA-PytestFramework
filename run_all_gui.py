"""Run the standalone PyAutoGUI UI test scripts sequentially."""

from datetime import datetime
from collections import Counter
from copy import copy
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import pyautogui
import pygetwindow as gw
from pywinauto import Application, Desktop
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

PROJECT_DIR = Path(__file__).resolve().parent
UI_TESTS_DIR = PROJECT_DIR / "ui_tests"
IPSA_EXE = Path(r"C:\Program Files\IPSA Software\IPSA 3.4\bin\ipsa3.exe")
REPORT_DIR = PROJECT_DIR / "Test Results"
GUI_REPORT_PATH = REPORT_DIR / "Latest_GUI_Test_Execution_Report.xlsx"
UI_TEST_ORDER = (
    "test_ipsa_templates.py",
    "test_ipsa_library.py",
    "test_ipsa_help.py",
    "test_ipsa_help_connections.py",
    "test_ipsa_directories.py",
    "test_ipsa_geographic_map.py",
    "test_ipsa_component.py",
    "test_ipsa_analysis.py",
    "test_ipsa_file_menu.py",
)


def discover_ui_tests() -> list[Path]:
    scripts = {script.name: script for script in UI_TESTS_DIR.glob("test_*.py")}
    ordered = [scripts[name] for name in UI_TEST_ORDER if name in scripts]
    ordered_names = set(UI_TEST_ORDER)
    remaining = sorted(
        (script for name, script in scripts.items() if name not in ordered_names),
        key=lambda script: script.name,
    )
    return ordered + remaining


def parse_ui_step_results(output: str) -> list[dict[str, str]]:
    steps = {}
    for line in output.splitlines():
        badge = re.match(r"^\s*\[(PASS|FAIL)\]\s+(.*?)\s*$", line, re.IGNORECASE)
        if badge:
            parts = re.split(r"\s{2,}", badge.group(2).strip(), maxsplit=1)
            name = parts[0].strip()
            detail = parts[1].strip() if len(parts) > 1 else ""
            steps[name] = {
                "name": name,
                "status": "PASSED" if badge.group(1).upper() == "PASS" else "FAILED",
                "detail": detail,
            }
            continue

        component = re.match(r"^\s*(.+?)\s*:\s*(PASS|FAIL)\s*$", line, re.IGNORECASE)
        if component:
            name = component.group(1).strip()
            steps[name] = {
                "name": name,
                "status": "PASSED" if component.group(2).upper() == "PASS" else "FAILED",
                "detail": "",
            }
            continue

        failed_step = re.search(r"Test step failed:\s*(.+?)\s*$", line, re.IGNORECASE)
        if failed_step:
            name = failed_step.group(1).strip()
            steps[name] = {
                "name": name,
                "status": "FAILED",
                "detail": line.strip(),
            }

    return list(steps.values())


def update_latest_gui_execution_report(runs: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if GUI_REPORT_PATH.is_file():
        workbook = load_workbook(GUI_REPORT_PATH)
    else:
        workbook = Workbook()
        workbook.active.title = "Test Details"
        workbook.create_sheet("Summary Matrix")

    details = workbook["Test Details"] if "Test Details" in workbook.sheetnames else workbook.create_sheet("Test Details")
    matrix = workbook["Summary Matrix"] if "Summary Matrix" in workbook.sheetnames else workbook.create_sheet("Summary Matrix")
    detail_headers = [
        "Test File",
        "Test Function",
        "Network Model",
        "Status",
        "Duration (s)",
        "Details / Skip Reason",
    ]

    if details.max_row == 1 and all(details.cell(1, col).value is None for col in range(1, 7)):
        for col, header in enumerate(detail_headers, start=1):
            details.cell(1, col, header)

    header_styles = [copy(details.cell(1, col)._style) for col in range(1, 7)]
    row_styles = (
        [copy(details.cell(2, col)._style) for col in range(1, 7)]
        if details.max_row >= 2
        else [None] * 6
    )
    ui_filenames = {script.name for script in UI_TESTS_DIR.glob("test_*.py")}
    for row_index in range(details.max_row, 1, -1):
        if details.cell(row_index, 1).value in ui_filenames:
            details.delete_rows(row_index)

    success_fill = PatternFill(fill_type="solid", fgColor="C6EFCE")
    success_font = Font(color="006100", bold=True)
    failure_fill = PatternFill(fill_type="solid", fgColor="FFC7CE")
    failure_font = Font(color="9C0006", bold=True)

    for run in runs:
        script = str(run["script"])
        steps = list(run.get("step_results", []))
        if not steps:
            status = "PASSED" if run["status"] == "PASSED" else "FAILED"
            detail = f"GUI script exit code: {run['return_code']}"
            steps = [{"name": "GUI script execution", "status": status, "detail": detail}]
        elif run["status"] != "PASSED" and not any(
            step["status"] == "FAILED" for step in steps
        ):
            steps.append(
                {
                    "name": "GUI script execution",
                    "status": "FAILED",
                    "detail": (
                        f"Script did not complete successfully "
                        f"(exit code: {run['return_code']})."
                    ),
                }
            )
        if run.get("cleanup_status") == "FAILED":
            steps.append(
                {
                    "name": "IPSA session cleanup",
                    "status": "FAILED",
                    "detail": "Could not close or reset the IPSA session.",
                }
            )

        for step in steps:
            row_index = details.max_row + 1
            row_values = [
                script,
                step["name"],
                "UI checks",
                step["status"],
                None,
                step.get("detail", ""),
            ]
            for col, value in enumerate(row_values, start=1):
                cell = details.cell(row_index, col, value)
                style = row_styles[col - 1]
                if style is not None:
                    cell._style = copy(style)
            status_cell = details.cell(row_index, 4)
            if step["status"] == "PASSED":
                status_cell.fill = success_fill
                status_cell.font = success_font
            else:
                status_cell.fill = failure_fill
                status_cell.font = failure_font

    for col, style in enumerate(header_styles, start=1):
        if style:
            details.cell(1, col)._style = copy(style)
    details.freeze_panes = "A2"
    details.auto_filter.ref = f"A1:F{details.max_row}"

    summary_headers = ["Test File", "Network Model", "FAILED", "PASSED", "SKIPPED", "Total"]
    matrix_header_styles = [copy(matrix.cell(1, col)._style) for col in range(1, 7)]
    matrix_row_styles = (
        [copy(matrix.cell(2, col)._style) for col in range(1, 7)]
        if matrix.max_row >= 2
        else [None] * 6
    )
    grouped_counts = {}
    for row_index in range(2, details.max_row + 1):
        script = details.cell(row_index, 1).value
        model = details.cell(row_index, 3).value
        status = details.cell(row_index, 4).value
        if not script:
            continue
        key = (script, model or "")
        counts = grouped_counts.setdefault(key, Counter())
        counts[status if status in ("FAILED", "PASSED", "SKIPPED") else "FAILED"] += 1

    matrix.delete_rows(1, matrix.max_row)
    for col, header in enumerate(summary_headers, start=1):
        cell = matrix.cell(1, col, header)
        if matrix_header_styles[col - 1]:
            cell._style = copy(matrix_header_styles[col - 1])
    for (script, model), counts in grouped_counts.items():
        values = [
            script,
            model,
            counts["FAILED"],
            counts["PASSED"],
            counts["SKIPPED"],
            sum(counts.values()),
        ]
        row_index = matrix.max_row + 1
        for col, value in enumerate(values, start=1):
            cell = matrix.cell(row_index, col, value)
            if matrix_row_styles[col - 1]:
                cell._style = copy(matrix_row_styles[col - 1])
    matrix.freeze_panes = "A2"
    matrix.auto_filter.ref = f"A1:F{matrix.max_row}"

    workbook.save(GUI_REPORT_PATH)
    workbook.close()


def launch_ipsa_application() -> subprocess.Popen | None:
    if not IPSA_EXE.is_file():
        print(f"ERROR: IPSA executable not found at: {IPSA_EXE}")
        return None

    print(f"Launching IPSA application: {IPSA_EXE}", flush=True)
    try:
        process = subprocess.Popen([str(IPSA_EXE)], cwd=PROJECT_DIR)
    except OSError as error:
        print(f"ERROR: Could not launch IPSA: {error}")
        return None

    deadline = time.monotonic() + 90
    last_readiness_error = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            print(f"ERROR: IPSA exited during startup (exit code {process.returncode}).")
            return None

        if get_ipsa_window() is not None:
            try:
                application = Application(backend="uia").connect(
                    process=process.pid,
                    timeout=2,
                )
                application.top_window().wait(
                    "visible enabled ready",
                    timeout=2,
                )
                time.sleep(3)
                print("IPSA main window is ready.")
                return process
            except Exception as error:
                last_readiness_error = error
                time.sleep(0.5)
        else:
            time.sleep(0.5)

    print(f"ERROR: IPSA did not become ready within 90 seconds. Last error: {last_readiness_error}")
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    return None


def get_ipsa_window():
    windows = [window for window in gw.getAllWindows() if "IPSA 3" in window.title]
    return windows[0] if windows else None


def close_ipsa_application(process: subprocess.Popen | None, timeout: float = 10) -> bool:
    window = get_ipsa_window()
    if window is not None:
        try:
            window.activate()
            time.sleep(0.3)
            pyautogui.hotkey("alt", "f4")
        except Exception as error:
            print(f"ERROR: Could not request IPSA shutdown: {error}")
            return False

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        window_open = get_ipsa_window() is not None
        process_running = process is not None and process.poll() is None
        if not window_open and not process_running:
            print("IPSA application closed.")
            return True
        time.sleep(0.5)

    if process is not None and process.poll() is None:
        print("IPSA did not close normally; stopping the process launched by this runner.")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    if get_ipsa_window() is None:
        print("IPSA application closed.")
        return True

    print("ERROR: IPSA window is still open; cannot start a guaranteed fresh session.")
    return False


def close_active_network() -> bool:
    window = get_ipsa_window()
    if window is None:
        print("Network cleanup skipped: no IPSA window is open.")
        return True

    window.activate()
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "f4")
    time.sleep(0.5)

    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        dialog_found = False
        try:
            for dialog in Desktop(backend="uia").windows():
                title = dialog.window_text().strip()
                if title != "IPSA 3" or dialog.rectangle().width() >= 550:
                    continue

                texts = [
                    control.window_text().strip()
                    for control in dialog.descendants()
                ]
                if not any(
                    "modified" in text.casefold()
                    or "save your changes" in text.casefold()
                    for text in texts
                ):
                    continue

                dialog_found = True
                no_button = next(
                    (
                        button
                        for button in dialog.descendants(control_type="Button")
                        if button.window_text().strip().replace("&", "").casefold()
                        == "no"
                    ),
                    None,
                )
                if no_button is not None:
                    no_button.click_input()
                else:
                    dialog.set_focus()
                    pyautogui.press("n")
                time.sleep(0.5)
                print("Closed active network and selected No to discard changes.")
                return True
        except Exception as error:
            print(f"WARNING: Could not inspect IPSA save dialog: {error}")

        if not dialog_found:
            try:
                for candidate in gw.getAllWindows():
                    if candidate.title.strip() == "IPSA 3" and candidate.width < 550:
                        candidate.activate()
                        time.sleep(0.2)
                        pyautogui.press("n")
                        time.sleep(0.5)
                        print("Dismissed IPSA save dialog with No.")
                        return True
            except Exception as error:
                print(f"WARNING: Could not use keyboard fallback for save dialog: {error}")

        time.sleep(0.2)

    print("Network close requested; no save-changes dialog remained.")
    return True


def run_gui_suite() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")

    print("=" * 75)
    print("IPSA PYAUTOGUI AUTOMATION RUNNER")
    print(f"UI tests folder: {UI_TESTS_DIR}")
    print("WARNING: These tests control the mouse and keyboard.")
    print("Do not use the computer while the tests are running.")
    print("Move the mouse to the top-left corner to trigger PyAutoGUI's failsafe.")
    print("=" * 75, flush=True)

    if not UI_TESTS_DIR.is_dir():
        print(f"ERROR: UI tests folder not found: {UI_TESTS_DIR}")
        return 2

    test_scripts = discover_ui_tests()
    if not test_scripts:
        print(f"ERROR: No test_*.py scripts found in {UI_TESTS_DIR}")
        return 2

    reuse_initial_ipsa = get_ipsa_window() is not None
    if reuse_initial_ipsa:
        print("An IPSA session is already open; it will be used for the first GUI test.")

    runs: list[dict[str, object]] = []
    cancelled = False
    for index, script in enumerate(test_scripts, start=1):
        cleanup_status = "PASSED"
        cleanup_output = []
        use_existing_session = index == 1 and reuse_initial_ipsa
        if use_existing_session:
            try:
                if not close_active_network():
                    cleanup_status = "FAILED"
                    cleanup_output.append(
                        "ERROR: Could not close the active IPSA network before the first test."
                    )

                window = get_ipsa_window()
                if window is None:
                    cleanup_status = "FAILED"
                    cleanup_output.append(
                        "ERROR: The existing IPSA window closed before the first test."
                    )
                else:
                    if window.isMinimized:
                        window.restore()
                    window.activate()
                    time.sleep(1)
                    print("Using the existing IPSA session for the first test.")
            except Exception as error:
                cleanup_status = "FAILED"
                message = f"ERROR: Could not prepare the existing IPSA session: {error}"
                print(message)
                cleanup_output.append(message)
        else:
            try:
                if not close_active_network():
                    cleanup_status = "FAILED"
                    cleanup_output.append(
                        "ERROR: Could not close the active IPSA network before starting a fresh session."
                    )
                if not close_ipsa_application(None):
                    cleanup_status = "FAILED"
                    cleanup_output.append(
                        "ERROR: Could not close the existing IPSA application before the test."
                    )
            except Exception as error:
                cleanup_status = "FAILED"
                message = f"ERROR: Could not prepare a fresh IPSA session: {error}"
                print(message)
                cleanup_output.append(message)

        if cleanup_status == "FAILED":
            runs.append(
                {
                    "script": script.name,
                    "status": "ERROR",
                    "return_code": None,
                    "cleanup_status": cleanup_status,
                    "started": datetime.now().isoformat(sep=" ", timespec="seconds"),
                    "finished": datetime.now().isoformat(sep=" ", timespec="seconds"),
                    "duration": 0.0,
                    "output": "\n".join(cleanup_output),
                }
            )
            continue

        if use_existing_session:
            ipsa_process = None
        else:
            ipsa_process = launch_ipsa_application()
            if ipsa_process is None:
                print(f"ERROR: Cannot run {script.name} because IPSA could not be started.")
                runs.append(
                    {
                        "script": script.name,
                        "status": "ERROR",
                        "return_code": None,
                        "cleanup_status": cleanup_status,
                        "started": datetime.now().isoformat(sep=" ", timespec="seconds"),
                        "finished": datetime.now().isoformat(sep=" ", timespec="seconds"),
                        "duration": 0.0,
                        "output": "\n".join(cleanup_output + ["IPSA could not be started."]),
                    }
                )
                continue

        print(f"\n[{index}/{len(test_scripts)}] Running {script.name}", flush=True)
        started_at = datetime.now()
        start_time = time.monotonic()
        output_lines = []
        try:
            child_env = os.environ.copy()
            child_env["PYTHONIOENCODING"] = "utf-8:backslashreplace"
            process = subprocess.Popen(
                [sys.executable, "-u", str(script)],
                cwd=PROJECT_DIR,
                env=child_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as error:
            print(f"ERROR: Could not start {script.name}: {error}")
            output_lines.append(f"ERROR: Could not start script: {error}")
            try:
                close_active_network()
                if not close_ipsa_application(ipsa_process):
                    cleanup_status = "FAILED"
                    output_lines.append(
                        "ERROR: IPSA application did not close after script startup failed."
                    )
            except Exception as cleanup_error:
                cleanup_status = "FAILED"
                output_lines.append(
                    f"ERROR: IPSA cleanup failed after script startup error: {cleanup_error}"
                )
            finished_at = datetime.now()
            runs.append(
                {
                    "script": script.name,
                    "status": "ERROR",
                    "return_code": None,
                    "cleanup_status": cleanup_status,
                    "started": started_at.isoformat(sep=" ", timespec="seconds"),
                    "finished": finished_at.isoformat(sep=" ", timespec="seconds"),
                    "duration": round(time.monotonic() - start_time, 2),
                    "output": "\n".join(cleanup_output + output_lines),
                }
            )
            continue

        else:
            assert process.stdout is not None
            try:
                for line in process.stdout:
                    print(line, end="", flush=True)
                    output_lines.append(line.rstrip("\r\n"))
                return_code = process.wait()
            except KeyboardInterrupt:
                process.terminate()
                return_code = process.wait()
                cancelled = True
                output_lines.append("Cancelled by user.")

        if cancelled:
            status = "CANCELLED"
        elif return_code:
            status = "FAILED"
        else:
            status = "PASSED"

        step_results = parse_ui_step_results("\n".join(output_lines))
        if any(step["status"] == "FAILED" for step in step_results):
            status = "FAILED"

        finished_at = datetime.now()
        runs.append(
            {
                "script": script.name,
                "status": status,
                "return_code": return_code,
                "cleanup_status": cleanup_status,
                "started": started_at.isoformat(sep=" ", timespec="seconds"),
                "finished": finished_at.isoformat(sep=" ", timespec="seconds"),
                "duration": round(time.monotonic() - start_time, 2),
                "output": "\n".join(cleanup_output + output_lines),
                "step_results": step_results,
            }
        )

        try:
            if not close_active_network():
                cleanup_status = "FAILED"
                cleanup_output.append(
                    "ERROR: Could not close the active IPSA network after the test."
                )
        except Exception as error:
            cleanup_status = "FAILED"
            message = f"ERROR: Could not close the network after the test: {error}"
            print(message)
            cleanup_output.append(message)

        if not close_ipsa_application(ipsa_process):
            cleanup_status = "FAILED"
            cleanup_output.append(
                "ERROR: IPSA application did not close successfully after the test."
            )

        runs[-1]["cleanup_status"] = cleanup_status
        runs[-1]["output"] = "\n".join(cleanup_output + output_lines)

        if status == "PASSED":
            print(f"PASSED: {script.name}")
        elif status == "CANCELLED":
            print(f"CANCELLED: {script.name}")
        elif return_code == 0:
            print(f"FAILED: {script.name} (one or more reported checks failed)")
        else:
            print(f"FAILED: {script.name} (exit code {return_code})")

        if cancelled:
            break

    try:
        update_latest_gui_execution_report(runs)
    except OSError as error:
        print(f"ERROR: Could not update GUI execution report at '{GUI_REPORT_PATH}': {error}")
        return 1
    print(f"\nUpdated GUI execution report: {GUI_REPORT_PATH}")

    print("\n" + "=" * 75)
    failures = [
        run["script"]
        for run in runs
        if run["status"] in ("FAILED", "ERROR")
        or run["cleanup_status"] == "FAILED"
    ]
    if cancelled:
        print("RESULT: UI test run cancelled by user.")
        print("=" * 75)
        return 130
    if failures:
        print(f"RESULT: {len(failures)} of {len(test_scripts)} UI scripts failed.")
        for script_name in failures:
            print(f"  - {script_name}")
        print("=" * 75)
        return 1

    print(f"RESULT: All {len(test_scripts)} UI scripts exited successfully.")
    print("=" * 75)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_gui_suite())
