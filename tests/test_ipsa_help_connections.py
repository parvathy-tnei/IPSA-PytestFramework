import time
import sys
import pyautogui
import pygetwindow as gw

# Safety setup
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2

test_results = {}

def close_all_ipsa_related():
    """Closes all existing IPSA auxiliary windows, dialogs, and viewers before starting tests."""
    target_titles = [
        "IPSA 3 Help",
        "About IPSA",
        "About Qt",
        "Keyboard Shortcuts",
        "Licence",
        "License",
        "Preferences",
        "Options",
        "technicalnotes"
    ]
    
    for title_keyword in target_titles:
        for win in gw.getWindowsWithTitle(title_keyword):
            try:
                # Never kill the primary main application window in the cleanup step
                if win.title.strip() == "IPSA 3":
                    continue
                if win.isMinimized:
                    win.restore()
                win.activate()
                time.sleep(0.3)
                pyautogui.hotkey("alt", "f4")
                time.sleep(0.5)
            except Exception:
                pass
    time.sleep(1)

def get_ipsa_window():
    """Retrieve the main IPSA window object."""
    windows = gw.getWindowsWithTitle("IPSA 3")
    if not windows:
        return None
    return windows[0]

def is_ipsa_alive():
    """Verify that IPSA has not closed or crashed."""
    return get_ipsa_window() is not None

def wait_for_new_window(before_handles, timeout=6):
    """Wait until a new window handle appears that was not present before."""
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

def wait_for_meaningful_title(window, timeout=6):
    """Wait for Microsoft Edge / PDF Viewer to update title past 'Untitled'."""
    start = time.time()
    while time.time() - start < timeout:
        if not window:
            break
        title = window.title.strip()
        if title and not title.lower().startswith("untitled"):
            return title
        time.sleep(0.4)
    return window.title.strip() if window else ""

def close_window_safely(window):
    """Safely close an opened window or dialog."""
    if not window:
        return
    try:
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(0.4)
        pyautogui.hotkey("alt", "f4")
        time.sleep(0.8)
    except Exception:
        pass

def record_result(test_name, success, detail=""):
    """Store the result for the final test summary."""
    test_results[test_name] = {"passed": success, "detail": detail}

# --- Menu Navigation Helpers ---

def open_help_item(index):
    window = get_ipsa_window()
    if not window:
        return False
    if window.isMinimized:
        window.restore()
    window.activate()
    time.sleep(0.8)

    pyautogui.press("alt")
    time.sleep(0.2)
    pyautogui.press("right", presses=9, interval=0.12)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.4)

    pyautogui.press("home")
    time.sleep(0.2)
    if index > 0:
        pyautogui.press("down", presses=index, interval=0.15)
    time.sleep(0.2)
    pyautogui.press("enter")
    return True

def open_help_submenu_item(submenu_index, item_index):
    window = get_ipsa_window()
    if not window:
        return False
    if window.isMinimized:
        window.restore()
    window.activate()
    time.sleep(0.8)

    # 1. Open Help menu
    pyautogui.press("alt")
    time.sleep(0.2)
    pyautogui.press("right", presses=9, interval=0.12)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.4)

    # 2. Navigate down to submenu
    pyautogui.press("home")
    time.sleep(0.2)
    if submenu_index > 0:
        pyautogui.press("down", presses=submenu_index, interval=0.2)
    time.sleep(0.3)

    # 3. Expand submenu flyout
    pyautogui.press("right")
    time.sleep(0.6)

    # 4. Select child item
    pyautogui.press("home")
    time.sleep(0.2)
    if item_index > 0:
        pyautogui.press("down", presses=item_index, interval=0.2)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(1.0)
    return True

# --- Verification Routines ---

def auto_check_dialog(name, index, expected_keywords):
    display_name = f"Help -> {name.replace('_', ' ').title()}"
    before_handles = {w._hWnd for w in gw.getAllWindows()}

    if not open_help_item(index):
        record_result(display_name, False, "IPSA window unavailable")
        return

    new_win = wait_for_new_window(before_handles, timeout=4)
    target = new_win or gw.getActiveWindow()
    title = target.title if target else ""

    if target and any(k.lower() in title.lower() for k in expected_keywords):
        record_result(display_name, True, f"Found: '{title}'")
        close_window_safely(target)
    else:
        record_result(display_name, False, f"Expected {expected_keywords}, detected: '{title}'")
        pyautogui.press("esc")

def auto_check_document_or_web(test_name, trigger_fn, expected_keywords, is_browser=False):
    before_handles = {w._hWnd for w in gw.getAllWindows()}

    if not trigger_fn():
        record_result(test_name, False, "IPSA window unavailable")
        return

    new_win = wait_for_new_window(before_handles, timeout=6)
    target_win = new_win or gw.getActiveWindow()

    # Poll until Edge / browser updates title past "Untitled"
    title = wait_for_meaningful_title(target_win, timeout=6)

    matched = any(k.lower() in title.lower() for k in expected_keywords)

    if matched or (is_browser and any(b.lower() in title.lower() for b in ["edge", "chrome", "firefox"])):
        record_result(test_name, True, f"Opened window: '{title}'")
        if "edge" in title.lower() or "chrome" in title.lower():
            pyautogui.hotkey("ctrl", "w")  # Close the specific tab only
            time.sleep(0.5)
        else:
            close_window_safely(target_win)
    else:
        record_result(test_name, False, f"Window title mismatch: '{title}'")
        if target_win and target_win._hWnd not in before_handles:
            close_window_safely(target_win)

    time.sleep(0.5)
    ipsa = get_ipsa_window()
    if ipsa:
        ipsa.activate()
        time.sleep(0.5)

def auto_check_interactive_help(test_name, trigger_fn):
    """Specifically checks the Qt 'IPSA 3 Help' viewer window and avoids window re-use issues."""
    existing = gw.getWindowsWithTitle("IPSA 3 Help")
    for w in existing:
        close_window_safely(w)
        time.sleep(0.5)

    if not trigger_fn():
        record_result(test_name, False, "IPSA window unavailable")
        return

    target_win = None
    start = time.time()
    while time.time() - start < 6:
        help_windows = gw.getWindowsWithTitle("IPSA 3 Help")
        if help_windows:
            target_win = help_windows[0]
            break
        time.sleep(0.4)

    if target_win:
        record_result(test_name, True, f"Opened window: '{target_win.title}'")
        close_window_safely(target_win)
    else:
        active = gw.getActiveWindow()
        actual = active.title if active else "None"
        record_result(test_name, False, f"Expected 'IPSA 3 Help', detected: '{actual}'")
        pyautogui.press("esc")

    time.sleep(1)
    ipsa = get_ipsa_window()
    if ipsa:
        ipsa.activate()
        time.sleep(0.5)

def auto_check_licensing(index=3):
    display_name = "Help -> Licensing"
    before_handles = {w._hWnd for w in gw.getAllWindows()}

    if not open_help_item(index):
        record_result(display_name, False, "IPSA window unavailable")
        return

    keywords = ["licence", "license", "licensing", "licencing", "hasp", "sentinel", "key", "dongle"]
    target_dialog = None
    start = time.time()

    while time.time() - start < 7:
        current_windows = gw.getAllWindows()
        candidates = [w for w in current_windows if w._hWnd not in before_handles and w.title.strip()]
        
        active = gw.getActiveWindow()
        if active and active not in candidates:
            candidates.append(active)

        for win in candidates:
            if any(k in win.title.lower() for k in keywords):
                target_dialog = win
                break
                
        if target_dialog:
            break
        time.sleep(0.5)

    if not is_ipsa_alive():
        record_result(display_name, False, "CRASH DETECTED: IPSA terminated during licensing check")
        return

    if target_dialog:
        record_result(display_name, True, f"Found: '{target_dialog.title}'")
        close_window_safely(target_dialog)
    else:
        active_title = gw.getActiveWindow().title if gw.getActiveWindow() else "None"
        record_result(display_name, False, f"Expected license keywords, detected: '{active_title}'")
        pyautogui.press("esc")


# --- Main Test Runner ---

if __name__ == "__main__":
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
    sys.stdout.write("\rRunning test suite...                                            \n\n")
    sys.stdout.flush()

    # 0. Clean slate before starting tests
    close_all_ipsa_related()

    if not is_ipsa_alive():
        print("\nERROR: Main IPSA 3 window is not open! Please open IPSA 3 and run again.")
        raise SystemExit(1)

    # 1. Dialog Tests
    auto_check_dialog("about", 0, ["about", "ipsa"])
    auto_check_dialog("about_qt", 1, ["qt"])
    auto_check_dialog("keyboard_shortcuts", 4, ["shortcut", "keyboard"])

    # 2. Check for Updates (Web page)
    auto_check_document_or_web(
        "Help -> Check for Updates",
        lambda: open_help_item(2),
        ["latest-version", "update", "ipsa", "edge", "chrome"],
        is_browser=True
    )

    # 3. User Guides (PDFs)
    guides = [
        ("User Manual", 0, ["ug001", "user manual", "pdf"]),
        ("Reference Guide", 1, ["rg001", "reference guide", "pdf"]),
        ("Scripting Guide", 2, ["rg002", "pyipsa", "scripting", "pdf"]),
        ("Plugins SDK", 3, ["ug002", "plugin", "plugins", "sdk", "pdf"]),
        ("Technical Notes", 4, ["technical", "notes", "file explorer"]),
        ("Keyboard Shortcuts (PDF)", 5, ["ug003", "keyboard shortcuts", "pdf"])
    ]

    for name, idx, keywords in guides:
        auto_check_document_or_web(
            f"User Guides -> {name}",
            lambda i=idx: open_help_submenu_item(5, i),
            keywords,
            is_browser=True
        )

    # 4. Interactive Help (Qt Help Viewer)
    auto_check_interactive_help(
        "Interactive Help -> User Manual",
        lambda: open_help_submenu_item(6, 0)
    )
    auto_check_interactive_help(
        "Interactive Help -> Reference Guide",
        lambda: open_help_submenu_item(6, 1)
    )

    # 5. External Websites
    websites = [
        ("IPSA Knowledge Hub", 9, ["knowledge", "ipsa", "hub"]),
        ("PyIPSA ReadTheDocs", 10, ["readthedocs", "pyipsa", "python"]),
        ("LinkedIn", 11, ["linkedin"])
    ]

    for name, idx, keywords in websites:
        auto_check_document_or_web(
            f"Help -> {name}",
            lambda i=idx: open_help_item(i),
            keywords,
            is_browser=True
        )

    # 6. Licensing Check (Runs last)
    auto_check_licensing(3)

    # --- Summary Report Generation ---
    total = len(test_results)
    passed = sum(1 for r in test_results.values() if r["passed"])
    failed = total - passed

    print("=" * 60)
    print(f"AUTOMATION TEST RUN COMPLETED: {passed}/{total} PASSED ({failed} FAILED)")
    print("=" * 60)

    for test_name, res in test_results.items():
        badge = "[PASS]" if res["passed"] else "[FAIL]"
        print(f"{badge} {test_name:<40} {res['detail']}")
    print("=" * 60)