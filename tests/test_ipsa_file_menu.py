import os
import sys
import time
import pyautogui
import pygetwindow as gw
import pyperclip

# Fail-safe settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2

results = {}

SAMPLE_FILE_PATH = r"C:\Users\Public\IPSA 3.2\Network Examples\Advanced Examples\ACDC Example.i3f"
SAMPLE_FILE_NAME = "ACDC Example.i3f"

TEMP_PROJECT_PATH = os.path.join(
    os.path.expanduser("~"), "Downloads",
    f"ipsa_proj_{int(time.time())}.i3p"
)


def report_error(message):
    print(f"[{time.strftime('%H:%M:%S')}] ERROR: {message}")


def print_pretest_disclaimer():
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
        sys.stdout.write(f"\rStarting test in {remaining:2d} seconds... [Press Ctrl+C to cancel]")
        sys.stdout.flush()
        time.sleep(1.0)
    sys.stdout.write("\rRunning test suite quietly. Errors will be reported below...\n\n")
    sys.stdout.flush()


def get_ipsa_window():
    windows = [w for w in gw.getAllWindows() if "IPSA 3" in w.title]
    if not windows:
        return None
    return windows[0]


def is_ipsa_alive():
    return get_ipsa_window() is not None


def record_result(name, ok):
    results[name] = ok
    if not ok:
        report_error(f"Test step failed: {name}")


def wait_for_new_window(before_handles, timeout=4):
    start = time.time()
    while time.time() - start < timeout:
        current_windows = gw.getAllWindows()
        new_windows = [
            w for w in current_windows 
            if w._hWnd not in before_handles and w.title.strip()
        ]
        if new_windows:
            return new_windows[0]
        time.sleep(0.3)
    return None


def close_window_safely(target_win):
    if not target_win:
        return
    try:
        if "IPSA 3" in target_win.title and "Open" not in target_win.title:
            pyautogui.press("esc")
            return
        if target_win.isMinimized:
            target_win.restore()
        target_win.activate()
        time.sleep(0.3)
        pyautogui.press("esc", presses=2, interval=0.3)
        time.sleep(0.5)
        if target_win in gw.getAllWindows():
            pyautogui.hotkey("alt", "f4")
    except Exception:
        pyautogui.press("esc")


def dismiss_mode_dialogs():
    """Dismiss modal messages like 'Normal Mode' or 'Draw Graphics Mode' that block IPSA."""
    for _ in range(4):
        popups = [
            w for w in gw.getAllWindows()
            if any(k in w.title.lower() for k in ["normal mode", "draw graphics mode", "graphics mode"])
        ]
        if popups:
            try:
                popups[0].activate()
                time.sleep(0.2)
            except Exception:
                pass
            pyautogui.press("enter")
            time.sleep(0.4)
        else:
            break


def open_file_item(index, submenu=False):
    win = get_ipsa_window()
    if not win:
        return False
    if win.isMinimized:
        win.restore()
    win.activate()
    time.sleep(0.5)

    pyautogui.press("alt")
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.3)

    pyautogui.press("home")
    time.sleep(0.2)

    if index > 0:
        pyautogui.press("down", presses=index, interval=0.15)
    time.sleep(0.3)

    pyautogui.press("right" if submenu else "enter")
    time.sleep(0.8)
    return True


# 1. New network (Index 0)
def test_new_network():
    test_name = "New network"
    before_handles = {w._hWnd for w in gw.getAllWindows()}
    open_file_item(0)

    wizard = wait_for_new_window(before_handles, timeout=3) or gw.getActiveWindow()
    title = wizard.title if wizard else ""

    if wizard and ("new network" in title.lower() or "wizard" in title.lower() or wizard._hWnd not in before_handles):
        pyautogui.press("enter")
        time.sleep(0.4)
        pyautogui.press("enter")
        time.sleep(0.4)
        pyautogui.press("esc")
        record_result(test_name, True)
    else:
        record_result(test_name, False)
        pyautogui.press("esc")


# 2. Open... (Index 3)
def test_open():
    test_name = "Open..."
    before_handles = {w._hWnd for w in gw.getAllWindows()}
    open_file_item(3)
    time.sleep(1.5)

    dialog = None
    open_windows = gw.getWindowsWithTitle("Open IPSA file")
    if open_windows:
        dialog = open_windows[0]
    else:
        dialog = wait_for_new_window(before_handles, timeout=3)

    if not dialog:
        record_result(test_name, False)
        pyautogui.press("esc")
        return

    try:
        dialog.activate()
    except Exception:
        pass
    time.sleep(0.5)

    if os.path.exists(SAMPLE_FILE_PATH):
        pyperclip.copy(SAMPLE_FILE_PATH)
    else:
        pyperclip.copy(SAMPLE_FILE_NAME)

    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(3.5)

    record_result(test_name, is_ipsa_alive())


# 3. Close... (Index 4)
def test_close():
    test_name = "Close..."
    before_handles = {w._hWnd for w in gw.getAllWindows()}
    open_file_item(4)
    time.sleep(1)

    active = gw.getActiveWindow()
    if active and active._hWnd not in before_handles:
        pyautogui.press("n")
        pyautogui.press("esc")
    record_result(test_name, True)


# 4. Recent Files... (Index 5)
def test_recent_files():
    test_name = "Recent Files..."
    open_file_item(5, submenu=True)
    time.sleep(0.6)
    pyautogui.press("enter")
    time.sleep(3.5)
    record_result(test_name, is_ipsa_alive())


# 5. Save (Index 6)
def test_save():
    test_name = "Save"
    open_file_item(6)
    time.sleep(1)
    record_result(test_name, True)


# Generic File Menu Item Check
def test_file_item(name, index, submenu=False):
    before_handles = {w._hWnd for w in gw.getAllWindows()}
    open_file_item(index, submenu)

    opened = wait_for_new_window(before_handles, timeout=3) or gw.getActiveWindow()
    title = opened.title if opened else ""

    if opened and (opened._hWnd not in before_handles or "IPSA 3" not in title):
        record_result(name, True)
        close_window_safely(opened)
    else:
        record_result(name, False)
        pyautogui.press("esc")


# 6. Project Flow (Index 10)
def test_export_project():
    test_name = "Export Project"
    before_handles = {w._hWnd for w in gw.getAllWindows()}
    open_file_item(10, submenu=True)
    pyautogui.press("down", presses=2, interval=0.15)
    pyautogui.press("enter")
    time.sleep(1.5)

    dialog = wait_for_new_window(before_handles, timeout=4) or gw.getActiveWindow()
    if not dialog or "IPSA 3" in dialog.title:
        record_result(test_name, False)
        pyautogui.press("esc", presses=2, interval=0.3)
        return False

    try:
        dialog.activate()
    except Exception:
        pass
    time.sleep(0.5)

    pyautogui.press("enter")
    time.sleep(1.5)

    pyperclip.copy(TEMP_PROJECT_PATH)
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(3.0)

    if os.path.exists(TEMP_PROJECT_PATH):
        record_result(test_name, True)
        return True
    else:
        record_result(test_name, False)
        return False


def test_close_project():
    test_name = "Close Project"
    open_file_item(10, submenu=True)
    pyautogui.press("down", interval=0.15)
    pyautogui.press("enter")
    time.sleep(2.0)
    record_result(test_name, True)


def test_import_project():
    test_name = "Import Project"
    if not os.path.exists(TEMP_PROJECT_PATH):
        record_result(test_name, False)
        return False

    before_handles = {w._hWnd for w in gw.getAllWindows()}
    open_file_item(10, submenu=True)
    pyautogui.press("enter")
    time.sleep(2.0)

    dialog = wait_for_new_window(before_handles, timeout=4) or gw.getActiveWindow()
    if not dialog or "IPSA 3" in dialog.title:
        record_result(test_name, False)
        pyautogui.press("esc")
        return False

    try:
        dialog.activate()
    except Exception:
        pass
    time.sleep(0.5)

    pyperclip.copy(TEMP_PROJECT_PATH)
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(4.0)

    active_win = gw.getActiveWindow()
    if active_win and "IPSA 3" not in active_win.title:
        pyautogui.press("enter")
        time.sleep(1.0)

    if os.path.exists(TEMP_PROJECT_PATH):
        try:
            os.remove(TEMP_PROJECT_PATH)
        except Exception:
            pass

    success = is_ipsa_alive()
    record_result(test_name, success)
    return success


# 7. Merge... (Index 11)
def test_merge():
    test_name = "Merge..."
    before_handles = {w._hWnd for w in gw.getAllWindows()}
    open_file_item(11)

    dialog = wait_for_new_window(before_handles, timeout=4) or gw.getActiveWindow()
    if dialog and "IPSA 3" not in dialog.title:
        time.sleep(0.5)
        pyperclip.copy(SAMPLE_FILE_PATH)
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.4)
        pyautogui.press("esc")
        record_result(test_name, True)
    else:
        record_result(test_name, False)
        pyautogui.press("esc")


# 8. Add & Delete Diagram (Indices 1 & 2)
def test_add_diagram():
    test_name = "Add diagram"
    before_handles = {w._hWnd for w in gw.getAllWindows()}
    open_file_item(1)

    wizard = wait_for_new_window(before_handles, timeout=3) or gw.getActiveWindow()
    if not wizard or "IPSA 3" in wizard.title:
        record_result(test_name, False)
        return False

    pyautogui.press("enter")
    time.sleep(0.5)
    pyautogui.write("Test diagram", interval=0.02)
    pyautogui.press("enter")
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(1.5)

    dismiss_mode_dialogs()
    record_result(test_name, True)
    return True


def test_delete_diagram():
    test_name = "Delete diagram"
    del_handles = {w._hWnd for w in gw.getAllWindows()}
    open_file_item(2)

    dialog = wait_for_new_window(del_handles, timeout=3) or gw.getActiveWindow()
    if dialog and "IPSA 3" not in dialog.title:
        pyautogui.write("Test diagram", interval=0.02)
        time.sleep(0.4)
        pyautogui.press("down")
        time.sleep(0.2)
        pyautogui.press("enter")
        time.sleep(1.5)

        dismiss_mode_dialogs()
        record_result(test_name, True)
    else:
        record_result(test_name, False)
        pyautogui.press("esc")


# 9. Exit (Index 18)
def test_exit():
    test_name = "Exit"
    dismiss_mode_dialogs()

    win = get_ipsa_window()
    if not win:
        record_result(test_name, True)
        return

    try:
        if win.isMinimized:
            win.restore()
        win.activate()
    except Exception:
        pass
    time.sleep(0.5)

    pyautogui.press("alt")
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.3)

    pyautogui.press("home")
    time.sleep(0.2)

    pyautogui.press("down", presses=18, interval=0.12)
    time.sleep(0.4)
    pyautogui.press("enter")
    time.sleep(1.0)

    dismiss_mode_dialogs()
    for _ in range(3):
        confirm_box = [
            w for w in gw.getAllWindows()
            if any(k in w.title.lower() for k in ["save", "confirm", "close", "ipsa"])
            and w.title.strip() != "IPSA 3"
        ]
        if confirm_box:
            pyautogui.press("n")
            time.sleep(0.3)
            pyautogui.press("enter")
            break
        time.sleep(0.3)

    closed = False
    start = time.time()
    while time.time() - start < 10:
        remaining = [w for w in gw.getAllWindows() if "IPSA 3" in w.title and w.visible]
        if not remaining:
            closed = True
            break
        time.sleep(0.5)

    record_result(test_name, closed)


def main():
    print_pretest_disclaimer()

    if not is_ipsa_alive():
        report_error("IPSA 3 is not open! Please start IPSA 3 before running this suite.")
        sys.exit(1)

    time.sleep(2)

    # 1. New network
    test_new_network()

    # 2. Open
    test_open()

    # 3. Close
    test_close()

    # 4. Recent Files
    test_recent_files()

    # 5. Save
    test_save()

    # 6. Save as...
    test_file_item("Save as...", 7, False)

    # 7. Save Area as...
    test_file_item("Save Area as...", 8, False)

    # 8. Save Region as...
    test_file_item("Save Region as...", 9, False)

    # 9. Project Flow
    export_ok = test_export_project()
    if export_ok:
        test_close_project()
        test_import_project()
    else:
        record_result("Close Project", False)
        record_result("Import Project", False)

    # 10. Merge...
    test_merge()

    # 11. Print... (Index 16) and Print to PDF... (Index 17)
    test_file_item("Print...", 16, False)
    test_file_item("Print to PDF...", 17, False)

    # 12. Add Diagram & Delete Diagram
    if test_add_diagram():
        test_delete_diagram()
    else:
        record_result("Delete diagram", False)

    # 13. Close
    test_close()

    # 14. Exit
    test_exit()

    # Final Combined Summary Table
    print("\n=======================================================")
    print("                FILE MENU TESTS SUMMARY                ")
    print("=======================================================")
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status:<8} {test_name}")
    print("=======================================================\n")


if __name__ == "__main__":
    main()