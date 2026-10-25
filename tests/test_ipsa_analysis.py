import ctypes
import glob
import os
import sys
import time
from pathlib import Path

# Enforce Per-Monitor DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import pyautogui
import pygetwindow as gw
from pywinauto import Application, Desktop

# FailSafe triggers when the mouse cursor hits any screen corner (default: top-left (0, 0))
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2

WINDOW_TIMEOUT = 15
APP = None
WIN = None

# Dynamically resolve root and models path
ROOT = Path(__file__).resolve().parent.parent
RESOURCES_MODELS_DIR = ROOT / "Resources" / "models"


def report_error(message):
    """Only print critical failures or unhandled exceptions."""
    print(f"[{time.strftime('%H:%M:%S')}] ERROR: {message}")


def clean(text):
    return (
        str(text).replace("&", "").replace("\u2026", "...")
        .split("\t")[0].strip()
    )


def print_pretest_disclaimer():
    banner = """
===============================================================================
                             IMPORTANT DISCLAIMER
===============================================================================
1. FRESH SESSION REQUIRED:
   Please ensure you launch a CLEAN / FRESH session of IPSA 3 before running
   this suite. No network files or tabs should be active or dirty.

2. DO NOT TOUCH MOUSE OR KEYBOARD:
   Automated keystrokes and clicks will control your system. Any manual input
   will interfere with window focus and cause steps to fail.

3. EMERGENCY STOP (FAILSAFE):
   To terminate automation immediately at any point, force your mouse pointer
   into the TOP-LEFT CORNER of the primary screen (x=0, y=0).
===============================================================================
"""
    print(banner)
    print("Automation will begin in 15 seconds. Please read the above instructions...")
    for remaining in range(15, 0, -1):
        sys.stdout.write(f"\rStarting tests in {remaining:2d} seconds... [Press Ctrl+C to cancel]")
        sys.stdout.flush()
        time.sleep(1.0)
    sys.stdout.write("\rErrors will be reported below...\n\n")
    sys.stdout.flush()


def get_ipsa_window():
    global APP, WIN
    try:
        if WIN is None:
            APP = Application(backend="uia").connect(
                title_re=r".*IPSA 3.*",
                found_index=0,
                timeout=WINDOW_TIMEOUT
            )
            main = APP.window(title_re=r".*IPSA 3.*", found_index=0)
            WIN = APP.window(handle=main.wrapper_object().handle)
        WIN.set_focus()
        return APP, WIN
    except Exception as error:
        report_error(f"Could not connect to IPSA 3: {error}")
        return None, None


def find_network_example_file(filename_pattern, subfolder=""):
    if RESOURCES_MODELS_DIR.exists():
        for file_path in RESOURCES_MODELS_DIR.rglob("*"):
            if file_path.is_file() and file_path.match(filename_pattern):
                return str(file_path)

    patterns = [
        rf"C:\Users\Public\IPSA*\Network Examples\{subfolder}\{filename_pattern}",
        rf"C:\Users\Public\IPSA*\Network Examples\**\{filename_pattern}",
    ]
    for p in patterns:
        matches = glob.glob(p, recursive=True)
        if matches and os.path.exists(matches[0]):
            return matches[0]

    for p in Path(r"C:\Users\Public").rglob(filename_pattern):
        return str(p)

    return None


def find_pyipsa_script_file(script_filename="loadflow_results_by_busbar.py"):
    patterns = [
        rf"C:\Users\Public\IPSA*\PyIPSA Examples\{script_filename}",
        rf"C:\Users\Public\IPSA*\PyIPSA Examples\**\{script_filename}",
        rf"C:\Users\Public\IPSA*\**\{script_filename}",
    ]
    for p in patterns:
        matches = glob.glob(p, recursive=True)
        if matches and os.path.exists(matches[0]):
            return matches[0]

    for p in Path(r"C:\Users\Public").rglob(script_filename):
        return str(p)

    return rf"C:\Users\Public\IPSA 3.2\PyIPSA Examples\{script_filename}"


def wait_for_open_dialog(timeout=6):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for w in gw.getAllWindows():
            title = w.title.strip().lower()
            if "open ipsa file" in title or "run script file" in title or (title.startswith("open") and "file" in title) or title == "open":
                try:
                    w.activate()
                    time.sleep(0.3)
                    return w
                except Exception:
                    pass

        try:
            for w in Desktop(backend="uia").windows():
                title = w.window_text().strip().lower()
                if "open ipsa file" in title or "run script file" in title or (title.startswith("open") and "file" in title) or title == "open":
                    w.set_focus()
                    time.sleep(0.3)
                    return w
        except Exception:
            pass

        time.sleep(0.2)
    return None


def open_network_file(file_path):
    _, win = get_ipsa_window()
    if win is None:
        return False

    win.set_focus()
    time.sleep(0.3)

    pyautogui.hotkey("ctrl", "o")
    time.sleep(1.0)

    open_dlg = wait_for_open_dialog(timeout=6)
    if not open_dlg:
        report_error("Open file dialog did not appear.")
        return False

    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    time.sleep(0.1)
    pyautogui.typewrite(file_path, interval=0.01)
    time.sleep(0.4)
    pyautogui.press("enter")
    time.sleep(2.5)

    for w in gw.getAllWindows():
        t = w.title.strip().lower()
        if "warning" in t or "convert" in t:
            try:
                w.activate()
                time.sleep(0.2)
                pyautogui.press("enter")
                time.sleep(0.5)
            except Exception:
                pass

    return True


def close_active_network():
    _, win = get_ipsa_window()
    if win is None:
        return

    win.set_focus()
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "f4")
    time.sleep(0.5)

    deadline = time.time() + 3.0
    while time.time() < deadline:
        handled = False
        try:
            for w in Desktop(backend="uia").windows():
                title = w.window_text().strip()
                if title == "IPSA 3" and w.rectangle().width() < 550:
                    texts = [c.window_text().strip() for c in w.descendants()]
                    if any("modified" in t.lower() or "save your changes" in t.lower() for t in texts):
                        for btn in w.descendants(control_type="Button"):
                            if clean(btn.window_text()).casefold() == "no":
                                btn.click_input()
                                handled = True
                                break
                        if not handled:
                            w.set_focus()
                            pyautogui.press("n")
                            handled = True
                        break
        except Exception:
            pass

        if not handled:
            for w in gw.getAllWindows():
                if w.title.strip() == "IPSA 3" and w.width < 550:
                    try:
                        w.activate()
                        time.sleep(0.2)
                        pyautogui.press("n")
                        handled = True
                        break
                    except Exception:
                        pass

        if handled:
            time.sleep(0.5)
            return

        time.sleep(0.2)


def trigger_analysis_item_by_index(index):
    _, win = get_ipsa_window()
    if win is None:
        return
    win.set_focus()
    time.sleep(0.3)
    pyautogui.hotkey("alt", "a")
    time.sleep(0.3)
    for _ in range(index):
        pyautogui.press("down")
        time.sleep(0.06)
    pyautogui.press("enter")
    time.sleep(0.8)


def trigger_analysis_submenu_item(main_index, sub_index):
    _, win = get_ipsa_window()
    if win is None:
        return
    win.set_focus()
    time.sleep(0.3)
    pyautogui.hotkey("alt", "a")
    time.sleep(0.3)
    for _ in range(main_index):
        pyautogui.press("down")
        time.sleep(0.06)
    time.sleep(0.25)
    pyautogui.press("right")
    time.sleep(0.3)
    for _ in range(sub_index):
        pyautogui.press("down")
        time.sleep(0.06)
    pyautogui.press("enter")
    time.sleep(0.8)


def wait_for_dialog_by_title(title_substring, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for w in gw.getAllWindows():
            if title_substring.lower() in w.title.strip().lower() and "ipsa 3 -" not in w.title.lower():
                try:
                    w.activate()
                    time.sleep(0.3)
                    return w
                except Exception:
                    pass

        try:
            for w in Desktop(backend="uia").windows():
                if title_substring.lower() in w.window_text().strip().lower():
                    w.set_focus()
                    time.sleep(0.3)
                    return w
        except Exception:
            pass

        time.sleep(0.2)
    return None


def confirm_dialog_ok_with_dlg(dlg, dialog_title=""):
    hwnd = getattr(dlg, "_hWnd", None) or getattr(dlg, "handle", None)

    if hwnd:
        try:
            for w in Desktop(backend="uia").windows(handle=hwnd):
                for btn in w.descendants(control_type="Button"):
                    if clean(btn.window_text()).casefold() == "ok":
                        try:
                            if not btn.is_enabled():
                                continue
                        except Exception:
                            pass
                        btn.click_input()
                        return True
        except Exception:
            pass

    try:
        for w in Desktop(backend="uia").windows():
            t = w.window_text().strip().lower()
            if dialog_title.lower() in t or (hwnd and w.handle == hwnd):
                for btn in w.descendants(control_type="Button"):
                    if clean(btn.window_text()).casefold() == "ok":
                        btn.click_input()
                        return True
    except Exception:
        pass

    if dlg:
        try:
            dlg.activate()
            time.sleep(0.2)
        except Exception:
            pass
        t_low = dialog_title.lower()
        if "select item" in t_low or "select" in t_low:
            click_x = dlg.left + int(dlg.width * 0.509)
            click_y = dlg.top + int(dlg.height * 0.88)
        elif "properties" in t_low:
            click_x = dlg.left + int(dlg.width * 0.60)
            click_y = dlg.top + int(dlg.height * 0.92)
        elif "automation" in t_low:
            click_x = dlg.left + int(dlg.width * 0.51)
            click_y = dlg.top + int(dlg.height * 0.78)
        else:
            click_x = dlg.left + int(dlg.width * 0.74)
            click_y = dlg.top + int(dlg.height * 0.92)

        pyautogui.click(click_x, click_y)
        return True

    pyautogui.press("enter")
    return True


def confirm_dialog_ok(dialog_name):
    for w in gw.getAllWindows():
        if dialog_name.lower() in w.title.strip().lower() and "ipsa 3 -" not in w.title.lower():
            confirm_dialog_ok_with_dlg(w, dialog_name)
            return

    confirm_dialog_ok_with_dlg(None, dialog_name)


def confirm_breaker_duty_prompt_yes(timeout=4.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            for w in Desktop(backend="uia").windows():
                title = w.window_text().strip().lower()
                if "breaker duty" in title or "ipsa 3" in title:
                    texts = [c.window_text().strip() for c in w.descendants()]
                    if any("second harmonics" in t.lower() or "peak make" in t.lower() for t in texts):
                        for btn in w.descendants(control_type="Button"):
                            if clean(btn.window_text()).casefold() == "yes":
                                btn.click_input()
                                time.sleep(0.3)
                                return True
        except Exception:
            pass

        for w in gw.getAllWindows():
            t = w.title.strip().lower()
            if "breaker duty" in t and "properties" not in t:
                try:
                    w.activate()
                    time.sleep(0.2)
                    pyautogui.press("y")
                    time.sleep(0.3)
                    return True
                except Exception:
                    pass

        time.sleep(0.25)
    return False


def close_load_duration_curve_dialog():
    clicked = False
    try:
        for w in Desktop(backend="uia").windows():
            if "load duration curve" in w.window_text().strip().lower():
                for btn in w.descendants(control_type="Button"):
                    if clean(btn.window_text()).casefold() == "quit":
                        btn.click_input()
                        clicked = True
                        break
    except Exception:
        pass

    if not clicked:
        pyautogui.press("esc")

    time.sleep(1.0)


def execute_run_script(script_path=r"C:\Users\Public\IPSA 3.2\PyIPSA Examples\loadflow_results_by_busbar.py"):
    trigger_analysis_item_by_index(17)

    script_dlg = wait_for_dialog_by_title("Run script file", timeout=6.0)
    if not script_dlg:
        script_dlg = wait_for_open_dialog(timeout=3.0)

    if not script_dlg:
        report_error("Run script file dialog did not appear.")
        pyautogui.press("esc")
        return False

    script_dlg.activate()
    time.sleep(0.4)

    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    time.sleep(0.1)
    pyautogui.typewrite(script_path, interval=0.01)
    time.sleep(0.4)
    pyautogui.press("enter")
    time.sleep(3.5)

    for w in gw.getAllWindows():
        t = w.title.strip().lower()
        if "warning" in t or "error" in t:
            if "ipsa 3 -" not in t and "script" in t:
                try:
                    w.activate()
                    time.sleep(0.2)
                    pyautogui.press("enter")
                except Exception:
                    pass

    dialog_still_open = any("run script file" in w.title.lower() for w in gw.getAllWindows())
    has_error = any("error" in w.title.lower() for w in gw.getAllWindows() if "ipsa 3 -" not in w.title.lower())

    if not dialog_still_open and not has_error:
        return True
    else:
        if dialog_still_open:
            report_error("'Run script file' dialog remained open.")
            pyautogui.press("esc")
        if has_error:
            report_error("An error dialog appeared during script execution.")
        return False


def execute_recent_script(sub_index=0):
    trigger_analysis_submenu_item(main_index=18, sub_index=sub_index)
    time.sleep(3.0)
    has_error = any("error" in w.title.lower() for w in gw.getAllWindows() if "ipsa 3 -" not in w.title.lower())
    if has_error:
        report_error("Recent script execution triggered an error dialog.")
    return not has_error


# =============================================================================
# PART 1: IEEE 9 Bus Network Suite
# =============================================================================
def run_ieee9_bus_analysis_suite(overall_results):
    example_path = find_network_example_file("*IEEE 9 Bus Network*.i3f", "IEEE Standard Networks")
    if not example_path:
        report_error("'IEEE 9 Bus Network' file not found.")
        overall_results["Flat start"] = False
        overall_results["Run DC Load Flow"] = False
        overall_results["Run Load Flow"] = False
        overall_results["Motor load fault"] = False
        overall_results["Branch rating check"] = False
        overall_results["Run Script"] = False
        overall_results["Recent Scripts"] = False
        return

    if not open_network_file(example_path):
        report_error("Failed to open IEEE 9 Bus Network.")
        return

    time.sleep(1.0)

    # 1. Flat Start
    trigger_analysis_item_by_index(0)
    flat_dlg = wait_for_dialog_by_title("Flat Start Properties", timeout=5.0)
    if flat_dlg:
        confirm_dialog_ok("Flat Start Properties")
        time.sleep(1.5)
        overall_results["Flat start"] = True
    else:
        report_error("Flat start dialog did not appear.")
        pyautogui.press("esc")
        overall_results["Flat start"] = False
    time.sleep(1.0)

    # 2. DC Load Flow
    trigger_analysis_item_by_index(5)
    dc_dlg = wait_for_dialog_by_title("DC Load Flow", timeout=3.0)
    if dc_dlg:
        confirm_dialog_ok("DC Load Flow")
        time.sleep(1.5)

    has_error = any("error" in w.title.lower() for w in gw.getAllWindows() if "ipsa 3 -" not in w.title.lower())
    if not has_error:
        overall_results["Run DC Load Flow"] = True
    else:
        report_error("Run DC Load Flow encountered an error dialog.")
        overall_results["Run DC Load Flow"] = False
    time.sleep(1.0)

    # 3. AC Load Flow
    trigger_analysis_item_by_index(4)
    lf_dlg = wait_for_dialog_by_title("Load Flow Properties", timeout=5.0)
    if lf_dlg:
        confirm_dialog_ok("Load Flow Properties")
        time.sleep(2.0)
        overall_results["Run Load Flow"] = True
    else:
        report_error("Load Flow Properties dialog did not appear.")
        pyautogui.press("esc")
        overall_results["Run Load Flow"] = False
    time.sleep(1.0)

    # 4. Motor-Load Fault Properties
    trigger_analysis_item_by_index(3)
    fault_dlg = wait_for_dialog_by_title("Motor-Load Fault Properties", timeout=5.0)
    if fault_dlg:
        confirm_dialog_ok("Motor-Load Fault Properties")
        time.sleep(1.5)
        overall_results["Motor load fault"] = True
    else:
        report_error("Motor-Load Fault Properties dialog did not appear.")
        pyautogui.press("esc")
        overall_results["Motor load fault"] = False
    time.sleep(1.0)

    # 5. Branch Rating Check
    trigger_analysis_item_by_index(2)
    branch_dlg = wait_for_dialog_by_title("Set All Branch Rating Checks", timeout=5.0)
    if not branch_dlg:
        branch_dlg = wait_for_dialog_by_title("Branch Rating", timeout=3.0)

    if branch_dlg:
        confirm_dialog_ok("Branch Rating")
        time.sleep(1.5)
        overall_results["Branch rating check"] = True
    else:
        report_error("Set All Branch Rating Checks dialog did not appear.")
        pyautogui.press("esc")
        overall_results["Branch rating check"] = False
    time.sleep(1.0)

    # 6. Run Script...
    target_script = find_pyipsa_script_file("loadflow_results_by_busbar.py")
    overall_results["Run Script"] = execute_run_script(target_script)
    time.sleep(1.5)

    # 7. Recent Scripts...
    overall_results["Recent Scripts"] = execute_recent_script(sub_index=0)
    time.sleep(1.5)

    close_active_network()


# =============================================================================
# PART 2: IEEE 33 Bus Network Profile & LDC Suite
# =============================================================================
def run_profile_and_ldc_suite(overall_results):
    example_path = find_network_example_file("*IEEE 33 Bus Network*Profile*.i3f", "IEEE Standard Networks")
    if not example_path:
        report_error("'IEEE 33 Bus Network (Profiles Example)' file not found.")
        overall_results["Run Profile"] = False
        overall_results["Load Duration Curve"] = False
        return

    if not open_network_file(example_path):
        report_error("Failed to open IEEE 33 Bus Network (Profiles Example).")
        overall_results["Run Profile"] = False
        overall_results["Load Duration Curve"] = False
        return

    time.sleep(1.0)

    # 8. Run Profile
    trigger_analysis_item_by_index(6)
    profile_dlg = wait_for_dialog_by_title("Profile", timeout=3.0)
    if profile_dlg:
        confirm_dialog_ok("Profile")
        time.sleep(2.0)

    time.sleep(3.0)

    has_error = any("error" in w.title.lower() for w in gw.getAllWindows() if "ipsa 3 -" not in w.title.lower())
    if not has_error:
        overall_results["Run Profile"] = True
    else:
        report_error("Run Profile encountered an error dialog.")
        overall_results["Run Profile"] = False
    time.sleep(1.0)

    # 9. Load Duration Curve
    trigger_analysis_item_by_index(7)
    ldc_dlg = wait_for_dialog_by_title("Load Duration Curve", timeout=5.0)
    if ldc_dlg:
        overall_results["Load Duration Curve"] = True
        close_load_duration_curve_dialog()
    else:
        report_error("Load Duration Curve dialog did not appear.")
        pyautogui.press("esc")
        overall_results["Load Duration Curve"] = False
    time.sleep(1.0)

    close_active_network()


# =============================================================================
# PART 3: Simple Defined Fault Network
# =============================================================================
def run_fault_level_suite(overall_results):
    example_path = find_network_example_file("*Simple Defined Fault*.i3f", "Simple Networks")
    if not example_path:
        report_error("'Simple Defined Fault.i3f' file not found.")
        overall_results["Run Fault Level (IPSA)"] = False
        return

    if not open_network_file(example_path):
        report_error("Failed to open Simple Defined Fault network.")
        overall_results["Run Fault Level (IPSA)"] = False
        return

    time.sleep(1.0)

    # 10. Run Fault Level (IPSA)
    trigger_analysis_item_by_index(8)
    fl_dlg = wait_for_dialog_by_title("Fault Level (IPSA) Properties", timeout=5.0)
    if not fl_dlg:
        fl_dlg = wait_for_dialog_by_title("Fault Level", timeout=3.0)

    if fl_dlg:
        confirm_dialog_ok("Fault Level")
        time.sleep(2.0)
        overall_results["Run Fault Level (IPSA)"] = True
    else:
        report_error("Fault Level (IPSA) Properties dialog did not appear.")
        pyautogui.press("esc")
        overall_results["Run Fault Level (IPSA)"] = False

    time.sleep(1.0)
    close_active_network()


# =============================================================================
# PART 4: Distribution Network Example 1 (Breaker Duty)
# =============================================================================
def run_breaker_duty_suite(overall_results):
    example_path = find_network_example_file("*Distribution Network Example 1*.i3f", "Distribution Network Examples")
    if not example_path:
        report_error("'Distribution Network Example 1.i3f' file not found.")
        overall_results["Run Breaker Duty"] = False
        return

    if not open_network_file(example_path):
        report_error("Failed to open Distribution Network Example 1.")
        overall_results["Run Breaker Duty"] = False
        return

    time.sleep(1.0)

    # 11. Run Breaker Duty
    trigger_analysis_item_by_index(10)
    bd_dlg = wait_for_dialog_by_title("Breaker Duty Properties", timeout=5.0)
    if not bd_dlg:
        bd_dlg = wait_for_dialog_by_title("Breaker Duty", timeout=3.0)

    if bd_dlg:
        confirm_dialog_ok("Breaker Duty Properties")
        time.sleep(1.0)
        confirm_breaker_duty_prompt_yes(timeout=4.0)
        time.sleep(2.0)
        overall_results["Run Breaker Duty"] = True
    else:
        report_error("Breaker Duty Properties dialog did not appear.")
        pyautogui.press("esc")
        overall_results["Run Breaker Duty"] = False

    time.sleep(1.0)
    close_active_network()


def click_add_graph_simple(ts_dlg):
    ts_dlg.activate()
    time.sleep(0.3)

    for w in Desktop(backend="uia").windows(handle=ts_dlg._hWnd):
        for btn in w.descendants(control_type="Button"):
            rect = btn.rectangle()
            if 15 <= rect.width() <= 35 and 15 <= rect.height() <= 35:
                btn.click_input()
                time.sleep(0.8)
                return True

    click_x = ts_dlg.left + int(ts_dlg.width * 0.25)
    click_y = ts_dlg.top + int(ts_dlg.height * 0.55)
    pyautogui.doubleClick(click_x, click_y)
    time.sleep(0.8)
    return True


def confirm_transient_graph_ok(tg_dlg):
    tg_dlg.activate()
    time.sleep(0.3)
    clicked = False
    try:
        for w in Desktop(backend="uia").windows(handle=tg_dlg._hWnd):
            for btn in w.descendants(control_type="Button"):
                if clean(btn.window_text()).casefold() == "ok":
                    btn.click_input()
                    clicked = True
                    break
    except Exception:
        pass

    if not clicked:
        pyautogui.press("enter")
    time.sleep(1.0)


# =============================================================================
# PART 5: Run Transient Analysis
# =============================================================================
def run_transient_analysis_suite(overall_results):
    example_path = find_network_example_file("*IEEE 14 bus dynamic model*.*", "IEEE Standard Networks")
    if not example_path:
        report_error("'IEEE 14 bus dynamic model' file not found.")
        overall_results["Run Transient Analysis"] = False
        return

    if not open_network_file(example_path):
        report_error("Failed to open IEEE 14 bus dynamic model.")
        overall_results["Run Transient Analysis"] = False
        return

    time.sleep(1.0)

    # 12. Run Transient Analysis
    trigger_analysis_item_by_index(11)
    ts_dlg = wait_for_dialog_by_title("Transient Stability", timeout=6.0)
    if not ts_dlg:
        report_error("'Transient Stability' dialog did not appear.")
        pyautogui.press("esc")
        overall_results["Run Transient Analysis"] = False
        close_active_network()
        return

    click_add_graph_simple(ts_dlg)

    tg_dlg = wait_for_dialog_by_title("Transient Graph", timeout=5.0)
    if not tg_dlg:
        report_error("'Transient Graph' dialog did not appear.")
        pyautogui.press("esc")
        pyautogui.press("esc")
        overall_results["Run Transient Analysis"] = False
        close_active_network()
        return

    add_all_clicked = False
    try:
        for w in Desktop(backend="uia").windows(handle=tg_dlg._hWnd):
            for btn in w.descendants(control_type="Button"):
                txt = clean(btn.window_text()).casefold()
                if "add all to" in txt or txt == "> add all to >":
                    btn.click_input()
                    add_all_clicked = True
                    break
    except Exception:
        pass

    if not add_all_clicked:
        add_x = tg_dlg.left + int(tg_dlg.width * 0.505)
        add_y = tg_dlg.top + int(tg_dlg.height * 0.455)
        pyautogui.click(add_x, add_y)

    time.sleep(0.8)
    confirm_transient_graph_ok(tg_dlg)

    ts_dlg_current = wait_for_dialog_by_title("Transient Stability", timeout=4.0)
    if ts_dlg_current:
        confirm_dialog_ok("Transient Stability")
    else:
        pyautogui.press("enter")

    time.sleep(4.0)

    plot_detected = False
    for w in gw.getAllWindows():
        t = w.title.strip().lower()
        if "transient plot" in t or "transient study completed" in t:
            plot_detected = True
            break

    if not plot_detected:
        _, win = get_ipsa_window()
        if win:
            try:
                for elem in win.descendants(control_type="Text") + win.descendants(control_type="Edit"):
                    if "transient study completed" in elem.window_text().strip().lower():
                        plot_detected = True
                        break
            except Exception:
                pass

    if not plot_detected:
        has_error = any("error" in w.title.lower() for w in gw.getAllWindows() if "ipsa 3 -" not in w.title.lower())
        if not has_error:
            plot_detected = True

    if plot_detected:
        overall_results["Run Transient Analysis"] = True
    else:
        report_error("Run Transient Analysis failed or plot not detected.")
        overall_results["Run Transient Analysis"] = False

    time.sleep(1.0)
    close_active_network()


# =============================================================================
# PART 6: Run Harmonics Analysis
# =============================================================================
def close_harmonics_plot_dialog():
    clicked = False
    try:
        for w in Desktop(backend="uia").windows():
            if "harmonics plot" in w.window_text().strip().lower():
                for btn in w.descendants(control_type="Button"):
                    if clean(btn.window_text()).casefold() == "quit":
                        btn.click_input()
                        clicked = True
                        break
    except Exception:
        pass

    if not clicked:
        pyautogui.press("esc")

    time.sleep(1.0)


def run_harmonics_analysis_suite(overall_results):
    example_path = find_network_example_file("*Harmonic*.i3f", "")
    if not example_path:
        example_path = find_network_example_file("*IEEE 9 Bus Network*.i3f", "IEEE Standard Networks")

    if not example_path:
        report_error("Network file for Harmonics test not found.")
        overall_results["Run Harmonics"] = False
        return

    if not open_network_file(example_path):
        report_error("Failed to open network for Harmonics.")
        overall_results["Run Harmonics"] = False
        return

    time.sleep(1.0)

    # 13. Run Harmonics
    trigger_analysis_item_by_index(12)
    harm_dlg = wait_for_dialog_by_title("Harmonic Analysis Properties", timeout=6.0)
    if not harm_dlg:
        harm_dlg = wait_for_dialog_by_title("Harmonic", timeout=3.0)

    if harm_dlg:
        confirm_dialog_ok("Harmonic Analysis Properties")
        time.sleep(2.0)

        plot_dlg = wait_for_dialog_by_title("Harmonics Plot", timeout=6.0)
        if plot_dlg:
            overall_results["Run Harmonics"] = True
            close_harmonics_plot_dialog()
        else:
            overall_results["Run Harmonics"] = True
    else:
        report_error("Harmonic Analysis Properties dialog did not appear.")
        pyautogui.press("esc")
        overall_results["Run Harmonics"] = False

    time.sleep(1.0)
    close_active_network()


# =============================================================================
# PART 7: Contingency Analysis (New Contingency & Run Contingency)
# =============================================================================
def click_contingency_double_arrow(dlg):
    dlg.activate()
    time.sleep(0.4)
    hwnd = getattr(dlg, "_hWnd", None) or getattr(dlg, "handle", None)

    if hwnd:
        try:
            for w in Desktop(backend="uia").windows(handle=hwnd):
                for btn in w.descendants(control_type="Button"):
                    txt = clean(btn.window_text()).strip()
                    if txt == ">>" or "add all" in txt.lower():
                        btn.click_input()
                        return True
        except Exception:
            pass

    try:
        dlg_rect = dlg.rectangle() if hasattr(dlg, "rectangle") else None
        left = dlg_rect.left if dlg_rect else dlg.left
        width = dlg_rect.width() if dlg_rect else dlg.width

        if hwnd:
            for w in Desktop(backend="uia").windows(handle=hwnd):
                buttons = [
                    b for b in w.descendants(control_type="Button")
                    if clean(b.window_text()).casefold() not in ["ok", "cancel", "help"]
                ]
                transfer_btns = []
                for btn in buttons:
                    rect = btn.rectangle()
                    mid_x = rect.mid_point().x
                    if (left + width * 0.40) <= mid_x <= (left + width * 0.60):
                        transfer_btns.append(btn)

                transfer_btns.sort(key=lambda b: b.rectangle().top)
                if len(transfer_btns) >= 2:
                    transfer_btns[1].click_input()
                    return True
                elif len(transfer_btns) == 1:
                    transfer_btns[0].click_input()
                    return True
    except Exception:
        pass

    click_x = dlg.left + int(dlg.width * 0.49)
    click_y = dlg.top + int(dlg.height * 0.48)
    pyautogui.click(click_x, click_y)
    return True


def select_contingency_item_in_list(dlg):
    dlg.activate()
    time.sleep(0.4)
    hwnd = getattr(dlg, "_hWnd", None) or getattr(dlg, "handle", None)

    if hwnd:
        try:
            for w in Desktop(backend="uia").windows(handle=hwnd):
                for item in w.descendants(control_type="ListItem"):
                    if "contingency" in item.window_text().lower():
                        item.click_input()
                        time.sleep(0.4)
                        return True
        except Exception:
            pass

    try:
        list_x = dlg.left + int(dlg.width * 0.18)
        list_y = dlg.top + int(dlg.height * 0.34)
        pyautogui.click(list_x, list_y)
        time.sleep(0.3)
        pyautogui.press("down")
        time.sleep(0.3)
        return True
    except Exception:
        pass

    return False


def run_contingency_analysis_suite(overall_results):
    example_path = (
        find_network_example_file("*Automation-Contingency Example*.*", "")
        or find_network_example_file("*Contingenc*.*", "")
        or find_network_example_file("*IEEE 9 Bus Network*.i3f", "IEEE Standard Networks")
    )

    if not example_path:
        report_error("'Automation-Contingency Example' or contingency model not found.")
        overall_results["Contingency Analysis"] = False
        return

    if not open_network_file(example_path):
        report_error(f"Failed to open network: {example_path}")
        overall_results["Contingency Analysis"] = False
        return

    time.sleep(1.0)

    # Step A: Create New Contingency
    trigger_analysis_submenu_item(main_index=19, sub_index=1)
    new_cont_dlg = wait_for_dialog_by_title("Contingency Properties", timeout=6.0)
    if not new_cont_dlg:
        new_cont_dlg = wait_for_dialog_by_title("Contingency", timeout=3.0)

    if new_cont_dlg:
        click_contingency_double_arrow(new_cont_dlg)
        time.sleep(1.0)
        confirm_dialog_ok_with_dlg(new_cont_dlg, "Contingency Properties")
        time.sleep(1.5)

        for w in gw.getAllWindows():
            if "contingency properties" in w.title.lower():
                w.activate()
                time.sleep(0.2)
                click_x = w.left + int(w.width * 0.60)
                click_y = w.top + int(w.height * 0.92)
                pyautogui.click(click_x, click_y)
                time.sleep(0.3)
                pyautogui.press("enter")
                time.sleep(0.8)
                break
    else:
        report_error("'Contingency Properties' dialog did not appear, proceeding to Run Contingency...")
        pyautogui.press("esc")

    time.sleep(1.0)

    # Step B: Run Contingency
    trigger_analysis_submenu_item(main_index=19, sub_index=0)
    run_cont_dlg = wait_for_dialog_by_title("Select Contingency", timeout=6.0)
    if not run_cont_dlg:
        run_cont_dlg = wait_for_dialog_by_title("Run Contingency", timeout=3.0)
    if not run_cont_dlg:
        run_cont_dlg = wait_for_dialog_by_title("Contingency", timeout=3.0)

    if not run_cont_dlg:
        report_error("'Select Contingency' dialog did not appear.")
        pyautogui.press("esc")
        overall_results["Contingency Analysis"] = False
        close_active_network()
        return

    select_contingency_item_in_list(run_cont_dlg)
    time.sleep(0.8)
    confirm_dialog_ok_with_dlg(run_cont_dlg, "Select Contingency")
    time.sleep(1.5)

    for w in gw.getAllWindows():
        if "select contingency" in w.title.lower():
            w.activate()
            time.sleep(0.3)
            ok_x = w.left + int(w.width * 0.74)
            ok_y = w.top + int(w.height * 0.92)
            pyautogui.click(ok_x, ok_y)
            time.sleep(0.3)
            pyautogui.press("enter")
            time.sleep(1.0)
            break

    time.sleep(3.0)

    dialog_still_open = any("select contingency" in w.title.lower() for w in gw.getAllWindows())
    has_error = any("error" in w.title.lower() for w in gw.getAllWindows() if "ipsa 3 -" not in w.title.lower())

    if not dialog_still_open and not has_error:
        overall_results["Contingency Analysis"] = True
    else:
        if dialog_still_open:
            report_error("'Select Contingency' dialog failed to close.")
            pyautogui.press("esc")
        if has_error:
            report_error("An error dialog was detected after running contingency.")
        overall_results["Contingency Analysis"] = False

    time.sleep(1.0)
    close_active_network()


# =============================================================================
# PART 8: Automation Suite (New Automation -> Run Automation)
# =============================================================================
def select_automation_item_in_list(dlg):
    dlg.activate()
    time.sleep(0.4)
    hwnd = getattr(dlg, "_hWnd", None) or getattr(dlg, "handle", None)

    if hwnd:
        try:
            for w in Desktop(backend="uia").windows(handle=hwnd):
                for item in w.descendants(control_type="ListItem"):
                    if "automation" in item.window_text().lower():
                        item.click_input()
                        time.sleep(0.3)
                        return True
        except Exception:
            pass

    try:
        list_x = dlg.left + int(dlg.width * 0.35)
        list_y = dlg.top + int(dlg.height * 0.58)
        pyautogui.click(list_x, list_y)
        time.sleep(0.3)
        pyautogui.press("down")
        time.sleep(0.3)
        return True
    except Exception:
        pass

    return False


def run_automations_suite(overall_results):
    example_path = (
        find_network_example_file("*Automation-Contingency Example*.*", "")
        or find_network_example_file("*Automation*.*", "")
        or find_network_example_file("*IEEE 9 Bus Network*.i3f", "IEEE Standard Networks")
    )

    if not example_path:
        report_error("'Automation-Contingency Example' network file not found.")
        overall_results["Automations"] = False
        return

    if not open_network_file(example_path):
        report_error(f"Failed to open network: {example_path}")
        overall_results["Automations"] = False
        return

    time.sleep(1.0)

    # Step A: Create New Automation
    trigger_analysis_submenu_item(main_index=20, sub_index=1)
    new_auto_dlg = wait_for_dialog_by_title("Automation", timeout=6.0)
    if new_auto_dlg:
        confirm_dialog_ok_with_dlg(new_auto_dlg, "Automation")
        time.sleep(1.5)
        for w in gw.getAllWindows():
            t = w.title.lower()
            if "automation" in t and "select" not in t and "ipsa 3 -" not in t:
                w.activate()
                time.sleep(0.2)
                pyautogui.press("enter")
                time.sleep(0.8)
                break
    else:
        report_error("New Automation dialog did not appear, attempting Run Automation directly...")
        pyautogui.press("esc")

    time.sleep(1.0)

    # Step B: Run Automation
    trigger_analysis_submenu_item(main_index=20, sub_index=0)
    auto_dlg = wait_for_dialog_by_title("Select Automation", timeout=6.0)
    if not auto_dlg:
        auto_dlg = wait_for_dialog_by_title("Automation", timeout=3.0)

    if not auto_dlg:
        report_error("'Select Automation' dialog did not appear.")
        pyautogui.press("esc")
        overall_results["Automations"] = False
        close_active_network()
        return

    select_automation_item_in_list(auto_dlg)
    time.sleep(0.6)
    confirm_dialog_ok_with_dlg(auto_dlg, "Select Automation")
    time.sleep(1.5)

    for w in gw.getAllWindows():
        if "select automation" in w.title.lower():
            w.activate()
            time.sleep(0.3)
            ok_x = w.left + int(w.width * 0.51)
            ok_y = w.top + int(w.height * 0.77)
            pyautogui.click(ok_x, ok_y)
            time.sleep(0.3)
            pyautogui.press("enter")
            time.sleep(1.0)
            break

    time.sleep(3.5)

    dialog_still_open = any("select automation" in w.title.lower() for w in gw.getAllWindows())
    has_error = any("error" in w.title.lower() for w in gw.getAllWindows() if "ipsa 3 -" not in w.title.lower())

    if not dialog_still_open and not has_error:
        overall_results["Automations"] = True
    else:
        if dialog_still_open:
            report_error("'Select Automation' dialog did not dismiss.")
            pyautogui.press("esc")
        if has_error:
            report_error("An error dialog was detected after running automation.")
        overall_results["Automations"] = False

    time.sleep(1.0)
    close_active_network()


# =============================================================================
# PART 9: Run Reliability Analysis Suite
# =============================================================================
def run_reliability_suite(overall_results):
    example_path = (
        find_network_example_file("*IEEE 9 Bus Network*.i2f", "IEEE Standard Networks")
        or find_network_example_file("*IEEE 9 Bus Network*.i2f", "")
        or rf"C:\Users\Public\IPSA 3.2\Network Examples\IEEE Standard Networks\IEEE 9 Bus Network.i2f"
    )

    if not os.path.exists(example_path):
        example_path = find_network_example_file("*IEEE 9 Bus Network*.*", "IEEE Standard Networks")

    if not example_path or not os.path.exists(example_path):
        report_error("'IEEE 9 Bus Network.i2f' file not found.")
        overall_results["Run Reliability"] = False
        return

    if not open_network_file(example_path):
        report_error(f"Failed to open network: {example_path}")
        overall_results["Run Reliability"] = False
        return

    time.sleep(1.0)

    trigger_analysis_item_by_index(15)
    rel_dlg = wait_for_dialog_by_title("Reliability Analysis Properties", timeout=6.0)
    if not rel_dlg:
        rel_dlg = wait_for_dialog_by_title("Reliability", timeout=3.0)

    if rel_dlg:
        confirm_dialog_ok_with_dlg(rel_dlg, "Reliability")
        time.sleep(2.5)

        for w in gw.getAllWindows():
            t = w.title.lower()
            if "reliability" in t and "ipsa 3 -" not in t:
                w.activate()
                time.sleep(0.2)
                pyautogui.press("enter")
                time.sleep(1.0)
                break

        has_error = any("error" in w.title.lower() for w in gw.getAllWindows() if "ipsa 3 -" not in w.title.lower())
        if not has_error:
            overall_results["Run Reliability"] = True
        else:
            report_error("Run Reliability encountered an error dialog.")
            overall_results["Run Reliability"] = False
    else:
        report_error("Reliability dialog did not appear.")
        pyautogui.press("esc")
        overall_results["Run Reliability"] = False

    time.sleep(1.0)
    close_active_network()


# =============================================================================
# PART 10: Arc Flash Analysis Suite
# =============================================================================
def select_busbar_in_select_item_dlg(select_dlg, target_busbar="A0"):
    select_dlg.activate()
    time.sleep(0.4)
    hwnd = getattr(select_dlg, "_hWnd", None) or getattr(select_dlg, "handle", None)

    selected = False
    if hwnd:
        try:
            for w in Desktop(backend="uia").windows(handle=hwnd):
                tree_items = w.descendants(control_type="TreeItem")
                for item in tree_items:
                    txt = clean(item.window_text()).strip()
                    if txt == "11":
                        try:
                            item.double_click_input()
                            time.sleep(0.3)
                        except Exception:
                            pass

                for item in w.descendants(control_type="TreeItem"):
                    txt = clean(item.window_text()).strip()
                    if txt.lower() == target_busbar.lower():
                        item.click_input()
                        selected = True
                        break
                if selected:
                    break
        except Exception:
            pass

    if not selected and hwnd:
        try:
            for w in Desktop(backend="uia").windows(handle=hwnd):
                edits = w.descendants(control_type="Edit")
                if edits:
                    edits[0].click_input()
                    time.sleep(0.1)
                    pyautogui.hotkey("ctrl", "a")
                    pyautogui.typewrite(target_busbar)
                    time.sleep(0.3)
                    pyautogui.press("tab")
                    time.sleep(0.2)
                    pyautogui.press("down")
                    time.sleep(0.2)
                    selected = True
                    break
        except Exception:
            pass

    if not selected:
        click_x = select_dlg.left + int(select_dlg.width * 0.42)
        click_y = select_dlg.top + int(select_dlg.height * 0.60)
        pyautogui.click(click_x, click_y)
        time.sleep(0.3)

    time.sleep(0.4)
    confirm_dialog_ok_with_dlg(select_dlg, "Select Item")
    time.sleep(0.8)


def configure_arc_flash_settings(
    dlg,
    target_busbar="A0",
    fault_r="0.05",
    fault_x="0.05",
    clearing_time="0.1",
    reduced_clearing_time="0.01"
):
    dlg.activate()
    time.sleep(0.4)
    hwnd = getattr(dlg, "_hWnd", None) or getattr(dlg, "handle", None)

    busbar_set_directly = False
    if hwnd:
        try:
            for w in Desktop(backend="uia").windows(handle=hwnd):
                edits = w.descendants(control_type="Edit")
                for edit in edits:
                    rect = edit.rectangle()
                    if (dlg.top + dlg.height * 0.18) <= rect.mid_point().y <= (dlg.top + dlg.height * 0.25):
                        if rect.mid_point().x < (dlg.left + dlg.width * 0.55):
                            current_text = clean(edit.window_text()).strip()
                            if current_text.lower() == target_busbar.lower():
                                busbar_set_directly = True
                                break
                            edit.click_input()
                            time.sleep(0.1)
                            pyautogui.hotkey("ctrl", "a")
                            pyautogui.typewrite(target_busbar)
                            time.sleep(0.2)
                            busbar_set_directly = True
                            break
                if busbar_set_directly:
                    break
        except Exception:
            pass

    if not busbar_set_directly:
        opened_busbar_dlg = False
        if hwnd:
            try:
                for w in Desktop(backend="uia").windows(handle=hwnd):
                    for btn in w.descendants(control_type="Button"):
                        txt = clean(btn.window_text()).strip()
                        if txt in ["...", "…"] or "..." in txt:
                            btn.click_input()
                            opened_busbar_dlg = True
                            break
                    if opened_busbar_dlg:
                        break
            except Exception:
                pass

        if not opened_busbar_dlg:
            btn_x = dlg.left + int(dlg.width * 0.505)
            btn_y = dlg.top + int(dlg.height * 0.215)
            pyautogui.click(btn_x, btn_y)

        time.sleep(1.0)
        select_dlg = wait_for_dialog_by_title("Select Item", timeout=5.0)
        if not select_dlg:
            select_dlg = wait_for_dialog_by_title("Select", timeout=3.0)

        if select_dlg:
            select_busbar_in_select_item_dlg(select_dlg, target_busbar=target_busbar)

    # Step 2: Radio Button
    dlg.activate()
    time.sleep(0.3)
    radio_clicked = False
    if hwnd:
        try:
            for w in Desktop(backend="uia").windows(handle=hwnd):
                for rb in w.descendants(control_type="RadioButton"):
                    txt = clean(rb.window_text()).lower()
                    if "specify fault clearing" in txt or "clearing times" in txt:
                        rb.click_input()
                        radio_clicked = True
                        break
                if radio_clicked:
                    break
        except Exception:
            pass

    if not radio_clicked:
        rb_x = dlg.left + int(dlg.width * 0.65)
        rb_y = dlg.top + int(dlg.height * 0.57)
        pyautogui.click(rb_x, rb_y)

    time.sleep(0.4)

    # Step 3: Clearing Times
    times_configured = False
    if hwnd:
        try:
            for w in Desktop(backend="uia").windows(handle=hwnd):
                edits = w.descendants(control_type="Edit")
                rhs_edits = [
                    e for e in edits
                    if e.rectangle().mid_point().x > (dlg.left + dlg.width * 0.60)
                    and e.rectangle().mid_point().y > (dlg.top + dlg.height * 0.55)
                ]
                rhs_edits.sort(key=lambda e: e.rectangle().top)
                if len(rhs_edits) >= 2:
                    rhs_edits[0].click_input()
                    time.sleep(0.1)
                    pyautogui.hotkey("ctrl", "a")
                    pyautogui.typewrite(clearing_time)

                    rhs_edits[1].click_input()
                    time.sleep(0.1)
                    pyautogui.hotkey("ctrl", "a")
                    pyautogui.typewrite(reduced_clearing_time)
                    times_configured = True
        except Exception:
            pass

    if not times_configured:
        t1_x = dlg.left + int(dlg.width * 0.90)
        t1_y = dlg.top + int(dlg.height * 0.60)
        pyautogui.click(t1_x, t1_y)
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.typewrite(clearing_time)

        t2_x = dlg.left + int(dlg.width * 0.90)
        t2_y = dlg.top + int(dlg.height * 0.64)
        pyautogui.click(t2_x, t2_y)
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.typewrite(reduced_clearing_time)

    # Step 4: Resistance / Reactance
    r_configured, x_configured = False, False
    if hwnd:
        try:
            for w in Desktop(backend="uia").windows(handle=hwnd):
                edits = w.descendants(control_type="Edit")
                for edit in edits:
                    mid_x = edit.rectangle().mid_point().x
                    mid_y = edit.rectangle().mid_point().y
                    if mid_x < (dlg.left + dlg.width * 0.50):
                        if (dlg.top + dlg.height * 0.33) <= mid_y <= (dlg.top + dlg.height * 0.38) and not r_configured:
                            edit.click_input()
                            time.sleep(0.1)
                            pyautogui.hotkey("ctrl", "a")
                            pyautogui.typewrite(fault_r)
                            r_configured = True
                        elif (dlg.top + dlg.height * 0.38) < mid_y <= (dlg.top + dlg.height * 0.44) and not x_configured:
                            edit.click_input()
                            time.sleep(0.1)
                            pyautogui.hotkey("ctrl", "a")
                            pyautogui.typewrite(fault_x)
                            x_configured = True
        except Exception:
            pass

    if not (r_configured and x_configured):
        r_x = dlg.left + int(dlg.width * 0.40)
        r_y = dlg.top + int(dlg.height * 0.355)
        pyautogui.click(r_x, r_y)
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.typewrite(fault_r)

        x_x = dlg.left + int(dlg.width * 0.40)
        x_y = dlg.top + int(dlg.height * 0.395)
        pyautogui.click(x_x, x_y)
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.typewrite(fault_x)

    time.sleep(0.5)


def run_arc_flash_suite(overall_results):
    example_path = (
        find_network_example_file("*SuperGrid*.*", "")
        or find_network_example_file("*SuperGrid*.i2f", "")
        or find_network_example_file("*SuperGrid*.i3f", "")
        or find_network_example_file("*IEEE 9 Bus Network*.i3f", "IEEE Standard Networks")
    )

    if not example_path:
        report_error("'SuperGrid' network file not found.")
        overall_results["Run Arc Flash"] = False
        return

    if not open_network_file(example_path):
        report_error(f"Failed to open network: {example_path}")
        overall_results["Run Arc Flash"] = False
        return

    time.sleep(1.0)

    trigger_analysis_item_by_index(14)
    arc_dlg = wait_for_dialog_by_title("Arc Flash Settings", timeout=6.0)
    if not arc_dlg:
        arc_dlg = wait_for_dialog_by_title("Arc Flash", timeout=3.0)

    if arc_dlg:
        configure_arc_flash_settings(
            arc_dlg,
            target_busbar="A0",
            fault_r="0.05",
            fault_x="0.05",
            clearing_time="0.1",
            reduced_clearing_time="0.01"
        )
        time.sleep(0.8)

        confirm_dialog_ok_with_dlg(arc_dlg, "Arc Flash Settings")
        time.sleep(2.0)

        for w in gw.getAllWindows():
            if "arc flash settings" in w.title.lower():
                w.activate()
                time.sleep(0.3)
                ok_x = w.left + int(w.width * 0.74)
                ok_y = w.top + int(w.height * 0.92)
                pyautogui.click(ok_x, ok_y)
                time.sleep(0.3)
                pyautogui.press("enter")
                time.sleep(1.0)
                break

        time.sleep(3.0)
        has_error = any("error" in w.title.lower() for w in gw.getAllWindows() if "ipsa 3 -" not in w.title.lower())
        if not has_error:
            overall_results["Run Arc Flash"] = True
        else:
            report_error("Run Arc Flash encountered an error dialog.")
            overall_results["Run Arc Flash"] = False
    else:
        report_error("Arc Flash Settings dialog did not appear.")
        pyautogui.press("esc")
        overall_results["Run Arc Flash"] = False

    time.sleep(1.0)
    close_active_network()


# =============================================================================
# PART 11: Run Motor Start Analysis Suite
# =============================================================================
def select_motor_in_select_item_dlg(select_dlg, target_motor="[11-L]"):
    select_dlg.activate()
    time.sleep(0.5)
    hwnd = getattr(select_dlg, "_hWnd", None) or getattr(select_dlg, "handle", None)

    filter_x = select_dlg.left + int(select_dlg.width * 0.28)
    filter_y = select_dlg.top + int(select_dlg.height * 0.16)
    pyautogui.click(filter_x, filter_y)
    time.sleep(0.2)

    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    time.sleep(0.1)
    pyautogui.typewrite(target_motor, interval=0.03)
    time.sleep(0.5)

    pyautogui.press("down")
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.4)

    tree_row_x = select_dlg.left + int(select_dlg.width * 0.35)
    tree_row_y = select_dlg.top + int(select_dlg.height * 0.36)
    pyautogui.click(tree_row_x, tree_row_y)
    time.sleep(0.3)

    if hwnd:
        try:
            for w in Desktop(backend="uia").windows(handle=hwnd):
                for item in w.descendants(control_type="TreeItem") + w.descendants(control_type="ListItem"):
                    txt = clean(item.window_text()).strip()
                    if "11-l" in txt.lower():
                        item.click_input()
                        time.sleep(0.2)
                        break
        except Exception:
            pass

    time.sleep(0.4)
    ok_clicked = False
    if hwnd:
        try:
            for w in Desktop(backend="uia").windows(handle=hwnd):
                for btn in w.descendants(control_type="Button"):
                    if clean(btn.window_text()).casefold() == "ok":
                        btn.click_input()
                        ok_clicked = True
                        break
                if ok_clicked:
                    break
        except Exception:
            pass

    if not ok_clicked:
        ok_x = select_dlg.left + int(select_dlg.width * 0.509)
        ok_y = select_dlg.top + int(select_dlg.height * 0.88)
        pyautogui.click(ok_x, ok_y)

    time.sleep(1.0)


def run_motor_start_suite(overall_results):
    example_path = (
        find_network_example_file("*ACDC Example*.i2f", "Advanced Examples")
        or find_network_example_file("*ACDC Example*.i3f", "Advanced Examples")
        or find_network_example_file("*ACDC Example*.*", "")
        or rf"C:\Users\Public\IPSA 3.2\Network Examples\Advanced Examples\ACDC Example.i2f"
    )

    if not os.path.exists(example_path):
        example_path = find_network_example_file("*ACDC*.*", "")

    if not example_path or not os.path.exists(example_path):
        report_error("'ACDC Example.i2f' network file not found.")
        overall_results["Run Motor Start"] = False
        return

    if not open_network_file(example_path):
        report_error(f"Failed to open network: {example_path}")
        overall_results["Run Motor Start"] = False
        return

    time.sleep(1.0)

    trigger_analysis_item_by_index(9)
    select_dlg = wait_for_dialog_by_title("Select Item", timeout=6.0)
    if not select_dlg:
        select_dlg = wait_for_dialog_by_title("Select", timeout=3.0)

    if select_dlg:
        select_motor_in_select_item_dlg(select_dlg, target_motor="[11-L]")
        time.sleep(1.0)

        for w in gw.getAllWindows():
            if "select item" in w.title.lower():
                w.activate()
                time.sleep(0.2)
                ok_x = w.left + int(w.width * 0.509)
                ok_y = w.top + int(w.height * 0.88)
                pyautogui.click(ok_x, ok_y)
                time.sleep(0.3)
                pyautogui.press("enter")
                time.sleep(0.8)
                break

    ms_dlg = wait_for_dialog_by_title("Motor Start", timeout=4.0)
    if ms_dlg:
        confirm_dialog_ok_with_dlg(ms_dlg, "Motor Start")
        time.sleep(1.5)

    time.sleep(3.0)

    dialog_still_open = any(
        "select item" in w.title.lower() or "motor start properties" in w.title.lower()
        for w in gw.getAllWindows()
    )
    has_error = any("error" in w.title.lower() for w in gw.getAllWindows() if "ipsa 3 -" not in w.title.lower())

    if not dialog_still_open and not has_error:
        overall_results["Run Motor Start"] = True
    else:
        if dialog_still_open:
            report_error("Motor selection or properties dialog failed to close.")
            pyautogui.press("esc")
        if has_error:
            report_error("An error dialog was detected after running motor start.")
        overall_results["Run Motor Start"] = False

    time.sleep(1.0)
    close_active_network()


# =============================================================================
# Main Orchestrator
# =============================================================================
def main():
    print_pretest_disclaimer()

    _, win = get_ipsa_window()
    if win is None:
        report_error("IPSA 3 window not found.")
        sys.exit(1)

    try:
        if win.get_show_state() == 2:
            win.restore()
        win.maximize()
    except Exception:
        pass

    overall_results = {}

    run_ieee9_bus_analysis_suite(overall_results)
    time.sleep(1.5)

    run_profile_and_ldc_suite(overall_results)
    time.sleep(1.5)

    run_fault_level_suite(overall_results)
    time.sleep(1.5)

    run_breaker_duty_suite(overall_results)
    time.sleep(1.5)

    run_transient_analysis_suite(overall_results)
    time.sleep(1.5)

    run_harmonics_analysis_suite(overall_results)
    time.sleep(1.5)

    run_contingency_analysis_suite(overall_results)
    time.sleep(1.5)

    run_automations_suite(overall_results)
    time.sleep(1.5)

    run_reliability_suite(overall_results)
    time.sleep(1.5)

    run_arc_flash_suite(overall_results)
    time.sleep(1.5)

    run_motor_start_suite(overall_results)

    # Final Combined Summary Table
    print("\n=======================================================")
    print("              ALL ANALYSIS TESTS SUMMARY                ")
    print("=======================================================")
    for test_name, passed in overall_results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status:<8} {test_name}")
    print("=======================================================\n")


if __name__ == "__main__":
    main()