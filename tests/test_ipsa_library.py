"""
DISCLAIMER:
1. FRESH SESSION REQUIRED:
   Ensure a clean/fresh session of IPSA 3 is open and running before execution.
   No active models or unsaved networks should be open.

2. DO NOT TOUCH MOUSE OR KEYBOARD:
   Automated keystrokes and clicks will control your system. Any manual input
   will interfere with window focus and cause test steps to fail.

3. EMERGENCY STOP (FAILSAFE):
   To terminate automation immediately at any point, force your mouse pointer
   into the TOP-LEFT CORNER of the screen (x=0, y=0).
"""

import ctypes
import glob
import os
import sys
import time
from pathlib import Path

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

ROOT = Path(__file__).resolve().parent.parent
RESOURCES_MODELS_DIR = ROOT / "Resources" / "models"

# ============================================================
# CONFIGURATION & DYNAMIC PATH RESOLUTION
# ============================================================

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

WINDOW_TIMEOUT = 15
DIALOG_TIMEOUT = 20
VISIBLE_PAUSE = 1

# Automatically create and use a dedicated folder inside the Current Working Directory
WORKING_DIR = Path.cwd()
EXPORT_DIR = WORKING_DIR / "reports_output"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

IMPORT_WORKBOOK_NAMES = (
    "harmonic import.xls",
    "harmonics_import.xlsx",
    "harmonics_import.xls",
    "harmonics_import.xlsm",
    "harmonics_import.xlsb",
)

BAD_WORDS = [
    "Error",
    "Traceback",
    "Exception",
    "No network loaded",
    "too large",
    "Invalid file location",
]

DOCK_PANELS = {
    "windows", "data", "database", "templates",
    "scenarios", "changes", "scripts", "progress",
}


def find_network_example_file(filename_pattern, subfolder=""):
    """Dynamically find network model files across project and public IPSA folders."""
    if RESOURCES_MODELS_DIR.exists():
        for file_path in RESOURCES_MODELS_DIR.rglob("*"):
            if file_path.is_file() and file_path.match(filename_pattern):
                return str(file_path.resolve())

    patterns = [
        rf"C:\Users\Public\IPSA*\Network Examples\{subfolder}\{filename_pattern}",
        rf"C:\Users\Public\IPSA*\Network Examples\**\{filename_pattern}",
    ]
    for p in patterns:
        matches = glob.glob(p, recursive=True)
        if matches and os.path.exists(matches[0]):
            return str(Path(matches[0]).resolve())

    for p in Path(r"C:\Users\Public").rglob(filename_pattern):
        return str(p.resolve())

    return None


def find_import_workbook():
    """Dynamically resolve the Harmonics Excel workbook location."""
    for name in IMPORT_WORKBOOK_NAMES:
        candidate = ROOT / name
        if candidate.is_file():
            return candidate.resolve()
        candidate = WORKING_DIR / name
        if candidate.is_file():
            return candidate.resolve()

    if RESOURCES_MODELS_DIR.exists():
        for candidate_pattern in ("*harmonic*import*.xls*", "*harmonic*import*.xlsx*"):
            for file_path in ROOT.rglob(candidate_pattern):
                if file_path.is_file():
                    return file_path.resolve()
    return None


def get_network_path(network_key):
    """Retrieve network paths dynamically by key."""
    if network_key == "loadflow":
        return find_network_example_file("*IEEE 9 Bus Network*.i3f", "IEEE Standard Networks")
    elif network_key == "harmonics":
        return find_network_example_file("*Windfarm Harmonics Example*.i3f", "Advanced Examples")
    elif network_key == "extendeddata":
        return find_network_example_file("*Distribution Network Example 1*.i3f", "Distribution Network Examples")
    elif network_key == "contingency":
        return (
            find_network_example_file("*Automation-Contingency Example*.i2f")
            or find_network_example_file("*Contingency*.i2f")
        )
    elif network_key == "arcflash":
        return (
            find_network_example_file("*SuperGrid R1*.i2f")
            or find_network_example_file("*SuperGrid*.i2f")
        )
    return None


LOADFLOW_SCRIPTS = [
    "loadflow_summary",
    "loadflow_results_by_busbar",
]

HARMONICS_SCRIPTS = [
    "harmonicsource_table_export",
    "harmonicsource_table_import",
]

EXTENDED_DATA_SCRIPTS = [
    "configure_extendeddata_dar",
    "configure_extendeddata_dcr",
]

CONTINGENCY_SCRIPTS = [
    "contingency_report",
    "contingency_report_with_word",
]

ARC_FLASH_SCRIPTS = [
    "arcflash_report",
    "arcflash_report_with_word",
]

APP = None
WIN = None
SCRIPT_RESULTS = {}


# ============================================================
# GENERAL HELPERS
# ============================================================

def pause():
    if VISIBLE_PAUSE:
        time.sleep(VISIBLE_PAUSE)


def report(message):
    pass


def wait_until(condition, timeout=15, interval=0.2):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if condition():
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


def clean(text):
    return (
        str(text).replace("&", "").replace("\u2026", "...")
        .split("\t")[0].strip()
    )


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
    except Exception:
        return None, None


def visible_windows():
    try:
        return [w for w in Desktop(backend="uia").windows() if w.is_visible()]
    except Exception:
        return []


def ipsa_dialogs():
    dialogs = []
    if APP is None or WIN is None:
        return dialogs
    try:
        main = WIN.wrapper_object()
        candidates = [
            child for child in main.children()
            if child.element_info.control_type == "Window"
        ]
        candidates += [
            window for window in Desktop(backend="uia").windows(process=APP.process)
            if window.handle != main.handle
        ]
    except Exception:
        return dialogs

    seen = set()
    for window in candidates:
        try:
            if window.handle in seen or not window.is_visible():
                continue
            seen.add(window.handle)
            if window.window_text().strip().casefold() in DOCK_PANELS:
                continue
            dialogs.append(window)
        except Exception:
            continue
    return dialogs


def find_button(parent, button_name):
    wanted = clean(button_name).casefold()
    try:
        for button in parent.descendants(control_type="Button"):
            try:
                if (clean(button.window_text()).casefold() == wanted
                        and button.is_visible() and button.is_enabled()):
                    return button
            except Exception:
                continue
    except Exception:
        pass
    return None


def find_named_control(parent, name):
    button = find_button(parent, name)
    if button is not None:
        return button
    wanted = clean(name).casefold()
    try:
        for control in parent.descendants():
            try:
                if (clean(control.window_text()).casefold() == wanted
                        and control.is_visible() and control.is_enabled()):
                    return control
            except Exception:
                continue
    except Exception:
        pass
    return None


def find_ok_control(dialog):
    return find_named_control(dialog, "OK")


def find_menu_item(text):
    wanted = clean(text).casefold()
    try:
        windows = Desktop(backend="uia").windows(process=APP.process)
    except Exception:
        return None
    for window in windows:
        try:
            for item in window.descendants(control_type="MenuItem"):
                try:
                    if (clean(item.window_text()).casefold() == wanted
                            and item.is_visible() and item.is_enabled()):
                        return item
                except Exception:
                    continue
        except Exception:
            continue
    return None


def click_menu_path(path):
    _, win = get_ipsa_window()
    if win is None:
        return False
    try:
        first = win.child_window(title=path[0], control_type="MenuItem")
        first.click_input()
        pause()
        for name in path[1:]:
            found = {}
            if not wait_until(lambda: (found.update(item=find_menu_item(name)) or found["item"] is not None), timeout=4):
                pyautogui.press("esc", presses=3)
                return False
            found["item"].click_input()
            pause()
        return True
    except Exception:
        return False


def click_named_dialog_button(dialog_title, button_name, timeout=DIALOG_TIMEOUT):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for dialog in ipsa_dialogs() + visible_windows():
            try:
                title = dialog.window_text().strip()
                if dialog_title.casefold() not in title.casefold():
                    continue
                button = find_button(dialog, button_name)
                if button is not None:
                    button.click_input()
                    return True
            except Exception:
                continue
        time.sleep(0.3)
    return False


def click_following_ok_dialog(timeout=3):
    found = {}
    def ready():
        for dialog in ipsa_dialogs():
            button = find_ok_control(dialog)
            if button is not None:
                found["dialog"], found["button"] = dialog, button
                return True
        return False
    if wait_until(ready, timeout=timeout, interval=0.3):
        found["button"].click_input()
        return True
    return False


def close_unrelated_login_if_present():
    for window in visible_windows():
        try:
            title = window.window_text().strip()
            if "Log In" in title or "TNEIAPPS" in title:
                try:
                    window.minimize()
                except Exception:
                    pass
        except Exception:
            pass
    return False


def wait_until_idle(timeout=30):
    if WIN is not None:
        wait_until(lambda: WIN.is_enabled() or len(ipsa_dialogs()) > 0,
                   timeout=timeout, interval=0.3)


# ============================================================
# NETWORK OPENING AND CLOSING
# ============================================================

def network_is_loaded():
    try:
        title = WIN.window_text().casefold()
        return ".i3f" in title or ".i2f" in title
    except Exception:
        return False


def open_network(network_path, timeout=60):
    if not network_path:
        return False

    network_path = os.path.abspath(network_path)
    if not (network_path.endswith(".i2f") or network_path.endswith(".i3f")):
        for ext in (".i2f", ".i3f"):
            if os.path.isfile(network_path + ext):
                network_path = network_path + ext
                break

    if not os.path.isfile(network_path):
        return False

    _, win = get_ipsa_window()
    if win is None:
        return False

    try:
        win.set_focus()
        pyautogui.hotkey("ctrl", "o")
        wait_until(
            lambda: gw.getActiveWindow() is not None
            and "IPSA 3" not in gw.getActiveWindow().title,
            timeout=5,
        )
        pause()
        pyautogui.hotkey("ctrl", "a")
        pyautogui.write(network_path, interval=0.01)
        pyautogui.press("enter")

        expected = os.path.splitext(os.path.basename(network_path))[0].casefold()
        if wait_until(lambda: expected in win.window_text().casefold(), timeout=timeout):
            return True
        return False
    except Exception:
        return False


def close_stray_dialogs():
    for _ in range(3):
        dialogs = ipsa_dialogs()
        if not dialogs:
            return
        dialog = dialogs[0]
        button = find_button(dialog, "Cancel") or find_button(dialog, "Close")
        try:
            if button is not None:
                button.click_input()
            else:
                dialog.set_focus()
                pyautogui.press("esc")
        except Exception:
            pass
        time.sleep(0.3)


def finish_close(timeout=10):
    deadline = time.time() + timeout
    answered = False
    while time.time() < deadline:
        if not network_is_loaded():
            return True
        if not answered:
            for dialog in ipsa_dialogs():
                for name in ("No", "Don't Save", "Don’t Save", "Discard"):
                    control = find_named_control(dialog, name)
                    if control is not None:
                        control.click_input()
                        answered = True
                        break
                if answered:
                    break
        time.sleep(0.2)
    if network_is_loaded():
        return False
    return True


def close_network():
    close_stray_dialogs()
    _, win = get_ipsa_window()
    if win is None or not network_is_loaded():
        return
    if not click_menu_path(["File", "Close..."]):
        pyautogui.hotkey("ctrl", "f4")
    finish_close()


# ============================================================
# SCRIPTS LIBRARY
# ============================================================

def visible_list_items(panel):
    items = []
    try:
        for item in panel.descendants(control_type="ListItem"):
            try:
                if item.is_visible() and item.parent().rectangle().width() > 0:
                    items.append(item)
            except Exception:
                pass
    except Exception:
        pass
    return items


def open_library_panel():
    _, win = get_ipsa_window()
    if win is None:
        return None
    try:
        checkbox = win.child_window(title="Scripts", control_type="CheckBox")
        if checkbox.get_toggle_state() == 0:
            checkbox.click_input()
        panel = win.child_window(title="Scripts", control_type="Window")
        if not wait_until(lambda: panel.exists(timeout=0.2) and panel.is_visible(), timeout=5):
            return None
        panel.child_window(title="Library", control_type="TabItem").click_input()
        if not wait_until(lambda: len(visible_list_items(panel)) > 0, timeout=5):
            return None
        return panel
    except Exception:
        return None


def select_script(panel, script_name):
    try:
        for item in visible_list_items(panel):
            if item.window_text().strip().casefold() == script_name.casefold():
                item.click_input()
                pause()
                return True
        return False
    except Exception:
        return False


def run_selected_script(panel, script_name):
    if not select_script(panel, script_name):
        return False
    try:
        found = {}
        def ready():
            found["button"] = find_button(panel, "Run script")
            return found["button"] is not None
        if not wait_until(ready, timeout=5):
            return False
        found["button"].click_input()
        time.sleep(0.5)
        return True
    except Exception:
        return False


# ============================================================
# SCRIPT RESULT CHECKING
# ============================================================

def read_log():
    try:
        progress = WIN.child_window(title="Progress", control_type="Window")
        return "\n".join(
            element.window_text()
            for element in progress.descendants(control_type="Edit")
        )
    except Exception:
        return ""


def wait_for_log(before, timeout=30):
    last = before
    quiet = 0
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(0.5)
        now = read_log()
        if now != last:
            last, quiet = now, 0
        else:
            quiet += 1
            if quiet >= 2 and (now != before or time.time() - start >= 3):
                break
    return last[len(before):] if last.startswith(before) else last


def log_problem(new_text):
    for line in new_text.splitlines():
        if any(word.casefold() in line.casefold() for word in BAD_WORDS):
            return line.strip()
    return ""


def record_script(name, ok, reason=""):
    SCRIPT_RESULTS[name] = ok
    tag = "[PASS]" if ok else "[FAIL]"
    print(f"{tag} {name}")
    if reason and not ok:
        print(f"  Reason: {reason}")
    return ok


def run_script_and_report(script_name, after_start=None, extra_check=None):
    panel = open_library_panel()
    if panel is None:
        return record_script(script_name, False, "The Scripts Library could not be opened.")

    before = read_log()
    if not run_selected_script(panel, script_name):
        return record_script(script_name, False, "The script could not be started.")

    if after_start is not None:
        try:
            if after_start() is False:
                return record_script(script_name, False, "The required dialog interaction failed.")
        except Exception as error:
            return record_script(script_name, False, f"Error handling the script dialog: {error}")

    if extra_check is not None:
        try:
            ok, reason = extra_check()
        except Exception as error:
            ok, reason = False, f"Result verification failed: {error}"
        new_text = wait_for_log(before, timeout=5)
        problem = log_problem(new_text)
        if ok and not problem:
            return record_script(script_name, True)
        if problem:
            reason = f"{reason}. Progress log: {problem}"
        return record_script(script_name, False, reason)

    new_text = wait_for_log(before)
    problem = log_problem(new_text)
    if problem:
        return record_script(script_name, False, problem)
    return record_script(script_name, True)


# ============================================================
# COMMON DIALOGS & FOLDER PICKERS
# ============================================================

def handle_select_folder_dialog(timeout=DIALOG_TIMEOUT):
    deadline = time.time() + timeout
    target_folder = str(EXPORT_DIR.resolve())

    while time.time() < deadline:
        active_w = gw.getActiveWindow()
        title = active_w.title.casefold() if active_w else ""

        if active_w is not None and any(w in title for w in ("save", "report", "arc", "contingency", "folder", "select")):
            time.sleep(0.4)

            # Type the target export folder path into the active 'Folder:' input box
            pyautogui.hotkey("ctrl", "a")
            pyautogui.press("backspace")
            time.sleep(0.1)
            pyautogui.write(target_folder, interval=0.01)
            time.sleep(0.3)
            pyautogui.press("enter")
            time.sleep(0.8)

            # Verify if the dialog dismissed immediately on enter
            active_now = gw.getActiveWindow()
            if not active_now or not any(w in active_now.title.casefold() for w in ("save", "report", "arc", "contingency", "folder")):
                return True

            # If still open, click the 'Select Folder' button
            for dialog in ipsa_dialogs() + visible_windows():
                try:
                    for btn in dialog.descendants(control_type="Button"):
                        t = clean(btn.window_text()).casefold()
                        if "select folder" in t or t in ("select", "save", "ok"):
                            btn.click_input()
                            wait_until(lambda: not dialog.is_visible(), timeout=4)
                            return True
                except Exception:
                    pass

            pyautogui.hotkey("alt", "s")
            time.sleep(0.2)
            pyautogui.press("enter")
            time.sleep(0.8)
            return True

        # Check in UIA desktop window hierarchy
        for dialog in ipsa_dialogs() + visible_windows():
            try:
                t = dialog.window_text().strip().casefold()
                if any(w in t for w in ("save", "report", "arc", "contingency", "folder")):
                    dialog.set_focus()
                    time.sleep(0.3)

                    edits = [e for e in dialog.descendants(control_type="Edit") if e.is_visible()]
                    if edits:
                        edits[-1].click_input()
                        pyautogui.hotkey("ctrl", "a")
                        pyautogui.press("backspace")
                        time.sleep(0.1)
                        pyautogui.write(target_folder, interval=0.01)
                        time.sleep(0.3)
                        pyautogui.press("enter")
                        time.sleep(0.6)

                    for btn in dialog.descendants(control_type="Button"):
                        b_text = clean(btn.window_text()).casefold()
                        if "select folder" in b_text or b_text in ("select", "save", "ok"):
                            btn.click_input()
                            wait_until(lambda: not dialog.is_visible(), timeout=4)
                            return True
            except Exception:
                continue

        time.sleep(0.4)

    return False


def find_dialog_by_title_match(name, timeout=DIALOG_TIMEOUT):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for dialog in ipsa_dialogs() + visible_windows():
            try:
                if name.casefold() in dialog.window_text().strip().casefold():
                    return dialog
            except Exception:
                continue
        time.sleep(0.3)
    return None


# ============================================================
# LOAD FLOW
# ============================================================

def find_loadflow_dialog():
    match = None
    for dialog in ipsa_dialogs():
        try:
            texts = dialog.window_text() + " " + " ".join(
                control.window_text() for control in dialog.descendants()
                if control.window_text()
            )
            if "load flow" not in texts.casefold():
                continue
            ok_control = find_ok_control(dialog)
            if ok_control is not None:
                return dialog, ok_control
            if match is None:
                match = dialog
        except Exception:
            continue
    return match, None


def run_load_flow_analysis():
    _, win = get_ipsa_window()
    if win is None:
        return False
    try:
        if not click_menu_path(["Analysis", "Run Load Flow"]):
            try:
                win.child_window(title="Run Load Flow", control_type="Button").click_input()
            except Exception:
                return False

        found = {}
        def dialog_ready():
            found["dialog"], found["ok"] = find_loadflow_dialog()
            return found["ok"] is not None

        if wait_until(dialog_ready, timeout=DIALOG_TIMEOUT):
            found["ok"].click_input()
        else:
            dialog, _ = find_loadflow_dialog()
            if dialog is None:
                return False
            dialog.set_focus()
            pyautogui.press("enter")
            found["dialog"] = dialog

        wait_until(lambda: not found["dialog"].is_visible(), timeout=5)
        wait_until_idle()
        return True
    except Exception:
        return False


def run_loadflow_stage():
    model_path = get_network_path("loadflow")
    if not open_network(model_path):
        print("[FAIL] Load Flow model network could not be found or loaded.")
        return False
    if not run_load_flow_analysis():
        return False
    results = [run_script_and_report(name) for name in LOADFLOW_SCRIPTS]
    return all(results)


# ============================================================
# HARMONICS
# ============================================================

def is_excel_workbook_window(title):
    lower = title.strip().casefold()
    if not lower:
        return False
    return "excel" in lower or lower.endswith((".xlsx", ".xls", ".xlsm", ".xlsb"))


def excel_window_titles():
    titles = set()
    try:
        for window in gw.getAllWindows():
            title = window.title.strip()
            if title and is_excel_workbook_window(title):
                titles.add(title)
    except Exception:
        pass
    return titles


def handle_optional_export_dialog():
    click_named_dialog_button("DAR Configuration", "Yes", timeout=3)
    return True


def check_excel_workbook_opened(previous_windows, timeout=30):
    deadline = time.time() + timeout
    last_titles = set()
    while time.time() < deadline:
        current_titles = excel_window_titles()
        last_titles = current_titles
        new_titles = current_titles - previous_windows
        if new_titles or current_titles:
            return True, ""
        time.sleep(0.5)
    return False, f"No Excel window detected. Visible: {sorted(last_titles)}"


def close_excel_workbook():
    try:
        windows = [w for w in gw.getAllWindows() if is_excel_workbook_window(w.title)]
        for window in windows:
            try:
                window.activate()
                time.sleep(0.5)
                pyautogui.hotkey("alt", "f4")
                time.sleep(0.8)
                for dialog in visible_windows():
                    try:
                        d_title = dialog.window_text().casefold()
                        if "excel" in d_title or "save" in d_title:
                            btn = find_button(dialog, "Don't Save") or find_button(dialog, "No")
                            if btn:
                                btn.click_input()
                    except Exception:
                        continue
            except Exception:
                pass
    except Exception:
        pass


def find_import_dialog(timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for dialog in Desktop(backend="uia").windows() + ipsa_dialogs():
            try:
                if "select excel file to import" in dialog.window_text().strip().casefold():
                    return dialog
            except Exception:
                continue
        time.sleep(0.3)
    return None


def select_import_file_dialog(workbook_path, timeout=30):
    workbook_path = str(Path(workbook_path).resolve())
    dialog = find_import_dialog(timeout=timeout)
    if dialog is None:
        return False
    
    try:
        dialog.set_focus()
        time.sleep(0.5)
        pyautogui.hotkey("alt", "n")
        time.sleep(0.3)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.2)
        pyautogui.press("backspace")
        time.sleep(0.2)
        
        pyautogui.write(workbook_path, interval=0.01)
        time.sleep(0.5)
        pyautogui.press("enter")
        
        deadline = time.time() + 10
        while time.time() < deadline:
            if find_import_dialog(timeout=1) is None:
                return True
            time.sleep(0.5)
            
        open_btn = find_button(dialog, "Open") or find_button(dialog, "&Open")
        if open_btn:
            open_btn.click_input()
            return True
    except Exception:
        pass
    return False


def run_harmonics_test():
    import_workbook = find_import_workbook()
    if import_workbook is None:
        print("[FAIL] Harmonics import workbook could not be located in workspace or models path.")
        return False

    model_path = get_network_path("harmonics")
    if not open_network(model_path):
        print("[FAIL] Harmonics model network could not be found or loaded.")
        return False

    prev_windows = excel_window_titles()
    export_ok = run_script_and_report(
        HARMONICS_SCRIPTS[0],
        after_start=handle_optional_export_dialog,
        extra_check=lambda: check_excel_workbook_opened(prev_windows, timeout=30),
    )
    close_excel_workbook()

    if not export_ok:
        return False

    return run_script_and_report(
        HARMONICS_SCRIPTS[1],
        after_start=lambda: select_import_file_dialog(import_workbook, timeout=30),
    )


# ============================================================
# EXTENDED DATA
# ============================================================

def handle_config_dialogs():
    click_named_dialog_button("DAR Configuration", "Yes", timeout=2)
    click_named_dialog_button("DCR Configuration", "Yes", timeout=2)
    click_following_ok_dialog(timeout=2)


def run_extendeddata_test():
    model_path = get_network_path("extendeddata")
    if not open_network(model_path):
        print("[FAIL] Extended data model network could not be found or loaded.")
        return False
    results = [run_script_and_report(name, after_start=handle_config_dialogs) for name in EXTENDED_DATA_SCRIPTS]
    return all(results)


# ============================================================
# CONTINGENCY
# ============================================================

def configure_new_contingency(voltage="11"):
    dialog = find_dialog_by_title_match("Contingency Properties", timeout=DIALOG_TIMEOUT)
    if dialog is None:
        return False
    dialog.set_focus()
    pause()

    target_item = None
    for item in dialog.descendants():
        try:
            t = item.window_text().strip()
            if voltage == t or t.endswith(f" {voltage}"):
                if item.is_visible():
                    target_item = item
                    break
        except Exception:
            continue

    if target_item:
        target_item.click_input()
    pause()

    btn_move = find_button(dialog, ">>")
    if btn_move:
        btn_move.click_input()
    pause()

    ok_btn = find_ok_control(dialog)
    if ok_btn:
        ok_btn.click_input()
    else:
        dialog.set_focus()
        pyautogui.press("enter")

    wait_until(lambda: not dialog.is_visible(), timeout=5)
    return True


def select_and_run_contingency(contingency_name="Contingency1"):
    dialog = find_dialog_by_title_match("Select Contingency", timeout=DIALOG_TIMEOUT)
    if dialog is None:
        return False
    dialog.set_focus()
    pause()

    for item in dialog.descendants():
        try:
            if contingency_name.casefold() in item.window_text().strip().casefold() and item.is_visible():
                item.click_input()
                break
        except Exception:
            continue
    pause()

    ok_btn = find_ok_control(dialog)
    if ok_btn:
        ok_btn.click_input()
    else:
        dialog.set_focus()
        pyautogui.press("enter")

    wait_until(lambda: not dialog.is_visible(), timeout=5)
    wait_until_idle(timeout=60)
    return True


def run_contingency_stage():
    model_path = get_network_path("contingency")
    if not open_network(model_path):
        print("[FAIL] Contingency model network could not be found or loaded.")
        return False

    if not click_menu_path(["Analysis", "Contingencies", "New contingency..."]):
        return False
    if not configure_new_contingency(voltage="11"):
        return False

    pause()
    if not click_menu_path(["Analysis", "Contingencies", "Run contingency..."]):
        return False
    if not select_and_run_contingency(contingency_name="Contingency1"):
        return False

    results = []
    for script_name in CONTINGENCY_SCRIPTS:
        results.append(
            run_script_and_report(
                script_name, 
                after_start=lambda: handle_select_folder_dialog(timeout=DIALOG_TIMEOUT)
            )
        )

    close_network()
    return all(results)


# ============================================================
# ARC FLASH
# ============================================================

def configure_and_run_arc_flash():
    if not click_menu_path(["Analysis", "Run Arc Flash"]):
        return False

    dialog = find_dialog_by_title_match("Arc Flash Settings", timeout=DIALOG_TIMEOUT)
    if dialog is None:
        dialog = find_dialog_by_title_match("Arc Flash", timeout=DIALOG_TIMEOUT)
    if dialog is None:
        return False

    dialog.set_focus()
    time.sleep(0.8)

    busbar_edit = None
    all_edits = [e for e in dialog.descendants(control_type="Edit") if e.is_visible()]
    all_edits.sort(key=lambda e: (e.rectangle().top, e.rectangle().left))

    if all_edits:
        busbar_edit = all_edits[0]

    if busbar_edit is not None:
        busbar_edit.set_focus()
        busbar_edit.click_input()
        pyautogui.hotkey("ctrl", "a")
        pyautogui.write("A0", interval=0.03)
    else:
        d_rect = dialog.rectangle()
        pyautogui.click(d_rect.left + 350, d_rect.top + 205)
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.write("A0", interval=0.03)

    time.sleep(0.5)

    specify_radio = None
    for rb in dialog.descendants(control_type="RadioButton"):
        try:
            if "specify fault clearing times" in rb.window_text().strip().casefold() and rb.is_visible():
                specify_radio = rb
                break
        except Exception:
            continue

    if specify_radio is not None:
        specify_radio.click_input()
    else:
        for ctrl in dialog.descendants():
            if "specify fault clearing" in ctrl.window_text().strip().casefold() and ctrl.is_visible():
                r = ctrl.rectangle()
                pyautogui.click(r.left - 10, r.top + r.height() // 2)
                break

    time.sleep(0.5)

    clearing_edits = []
    if specify_radio:
        s_top = specify_radio.rectangle().top
        for edit in dialog.descendants(control_type="Edit"):
            try:
                if edit.is_visible() and edit.rectangle().top >= s_top - 10:
                    clearing_edits.append(edit)
            except Exception:
                continue

    clearing_edits.sort(key=lambda e: (e.rectangle().top, e.rectangle().left))
    if len(clearing_edits) >= 2:
        clearing_edits[0].set_focus()
        clearing_edits[0].click_input()
        pyautogui.hotkey("ctrl", "a")
        pyautogui.write("0.1", interval=0.03)
        time.sleep(0.2)

        clearing_edits[1].set_focus()
        clearing_edits[1].click_input()
        pyautogui.hotkey("ctrl", "a")
        pyautogui.write("0.1", interval=0.03)
    else:
        edits_now = [e for e in dialog.descendants(control_type="Edit") if e.is_visible()]
        edits_now.sort(key=lambda e: (e.rectangle().top, e.rectangle().left))
        if len(edits_now) >= 2:
            edits_now[-2].click_input()
            pyautogui.hotkey("ctrl", "a")
            pyautogui.write("0.1", interval=0.03)
            time.sleep(0.2)
            edits_now[-1].click_input()
            pyautogui.hotkey("ctrl", "a")
            pyautogui.write("0.1", interval=0.03)

    time.sleep(0.5)

    ok_btn = None
    for btn in dialog.descendants(control_type="Button"):
        try:
            if clean(btn.window_text()).casefold() in ("ok", "&ok") and btn.is_visible():
                ok_btn = btn
                break
        except Exception:
            continue

    if ok_btn is not None:
        r = ok_btn.rectangle()
        pyautogui.click(r.left + r.width() // 2, r.top + r.height() // 2)
        time.sleep(0.2)
        try:
            ok_btn.click_input()
        except Exception:
            pass
    else:
        dialog.set_focus()
        pyautogui.press("enter")

    wait_until(lambda: not dialog.is_visible(), timeout=5)
    wait_until_idle(timeout=60)
    return True


def run_arcflash_stage():
    model_path = get_network_path("arcflash")
    if not open_network(model_path):
        print("[FAIL] Arc Flash model network could not be found or loaded.")
        return False

    if not configure_and_run_arc_flash():
        return False

    pause()

    results = []
    for script_name in ARC_FLASH_SCRIPTS:
        results.append(
            run_script_and_report(
                script_name, 
                after_start=lambda: handle_select_folder_dialog(timeout=DIALOG_TIMEOUT)
            )
        )

    close_network()
    return all(results)


# ============================================================
# STARTUP AND MAIN TEST RUNNER
# ============================================================

def main():
    banner = """
===============================================================================
                                IMPORTANT DISCLAIMER
===============================================================================
1. FRESH SESSION REQUIRED:
   Ensure a clean/fresh session of IPSA 3 is open and running before execution.
   No active models or unsaved networks should be open.

2. DO NOT TOUCH MOUSE OR KEYBOARD:
   Automated keystrokes and clicks will control your system. Any manual input
   will interfere with window focus and cause test steps to fail.

3. EMERGENCY STOP (FAILSAFE):
   To terminate automation immediately at any point, force your mouse pointer
   into the TOP-LEFT CORNER of the screen (x=0, y=0).
===============================================================================
"""
    print(banner)
    print("Automation will begin in 15 seconds. Please read the above instructions...")
    for remaining in range(15, 0, -1):
        sys.stdout.write(f"\rStarting tests in {remaining:2d} seconds... [Press Ctrl+C to cancel]")
        sys.stdout.flush()
        time.sleep(1.0)
    sys.stdout.write("\rStarting test execution now...                                  \n\n")
    sys.stdout.flush()

    import_workbook = find_import_workbook()
    if import_workbook is None:
        print("[FAIL] Harmonics import workbook could not be located in workspace or models directory.")
        sys.exit(1)

    _, win = get_ipsa_window()
    if win is None:
        print("STOPPED: Please open IPSA 3 and try again.")
        sys.exit(1)

    try:
        if win.get_show_state() == 2:
            win.restore()
        win.maximize()
    except Exception:
        pass

    close_unrelated_login_if_present()

    stages = [
        ("Load Flow", run_loadflow_stage),
        ("Harmonics", run_harmonics_test),
        ("Extended Data", run_extendeddata_test),
        ("Contingency", run_contingency_stage),
        ("Arc Flash", run_arcflash_stage),
    ]
    
    for name, stage in stages:
        close_network()
        try:
            stage()
        except Exception as error:
            print(f"[FAIL] {name} stopped with an error: {error}")

    close_network()


if __name__ == "__main__":
    main()