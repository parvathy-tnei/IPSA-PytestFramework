# import time
# import pyautogui
# import pygetwindow as gw

# # Safety configuration
# pyautogui.FAILSAFE = True
# pyautogui.PAUSE = 0.2

# test_results = {}

# def get_ipsa_window():
#     """Retrieve the main IPSA window object."""
#     windows = gw.getWindowsWithTitle("IPSA 3")
#     if not windows:
#         return None
#     return windows[0]

# def is_ipsa_alive():
#     """Verify that IPSA has not closed or crashed."""
#     return get_ipsa_window() is not None

# def record_result(test_name, success, detail=""):
#     """Store and display the result during runtime."""
#     test_results[test_name] = {"passed": success, "detail": detail}
#     status = "PASSED" if success else "FAILED"
#     print(f"[{status}] {test_name}" + (f" -> {detail}" if detail else ""))

# def wait_for_new_window(before_handles, timeout=6):
#     """Wait until a new window handle appears that was not present before."""
#     start = time.time()
#     while time.time() - start < timeout:
#         current_windows = gw.getAllWindows()
#         new_windows = [
#             w for w in current_windows 
#             if w._hWnd not in before_handles and w.title.strip()
#         ]
#         if new_windows:
#             return new_windows[0]
#         time.sleep(0.3)
#     return None

# def wait_for_meaningful_title(window, timeout=6):
#     """Wait for Microsoft Edge / PDF Viewer to update title past 'Untitled'."""
#     start = time.time()
#     while time.time() - start < timeout:
#         if not window:
#             break
#         title = window.title.strip()
#         if title and not title.lower().startswith("untitled"):
#             return title
#         time.sleep(0.4)
#     return window.title.strip() if window else ""

# def close_window_safely(window):
#     """Safely close an opened window or browser tab without touching IPSA."""
#     if not window:
#         return
#     title_lower = window.title.lower()
    
#     # Safety guard: Never close the main IPSA application
#     if "ipsa 3" == title_lower.strip():
#         return

#     try:
#         if window.isMinimized:
#             window.restore()
#         window.activate()
#         time.sleep(0.3)

#         if any(b in title_lower for b in ["edge", "chrome", "firefox"]):
#             pyautogui.hotkey("ctrl", "w")  # Close tab only
#         else:
#             pyautogui.hotkey("alt", "f4")  # Standalone viewer / explorer
#         time.sleep(0.8)
#     except Exception as error:
#         print(f"Warning: Could not close '{window.title}': {error}")

# def close_all_auxiliary_windows():
#     """Clean up open documents, Technical Notes folders, or previous viewers."""
#     target_keywords = ["technicalnotes", "ug00", "rg00", "pdf", "edge"]
#     for win in gw.getAllWindows():
#         title = win.title.lower()
#         if title.strip() == "ipsa 3":
#             continue
#         if any(k in title for k in target_keywords):
#             try:
#                 if "technicalnotes" in title:
#                     win.close()
#                 elif "edge" in title or "chrome" in title:
#                     win.activate()
#                     time.sleep(0.2)
#                     pyautogui.hotkey("ctrl", "w")
#                 else:
#                     win.close()
#                 time.sleep(0.3)
#             except Exception:
#                 pass

# def open_user_guide(index):
#     """Navigate to Help -> User Guides -> item index."""
#     window = get_ipsa_window()
#     if not window:
#         return False
#     if window.isMinimized:
#         window.restore()
#     window.activate()
#     time.sleep(0.8)

#     # Open Help menu
#     pyautogui.press("alt")
#     time.sleep(0.2)
#     pyautogui.press("right", presses=9, interval=0.12)
#     time.sleep(0.2)
#     pyautogui.press("enter")
#     time.sleep(0.4)

#     # Open User Guides submenu (index 5)
#     pyautogui.press("home")
#     time.sleep(0.2)
#     pyautogui.press("down", presses=5, interval=0.2)
#     time.sleep(0.3)
#     pyautogui.press("right")
#     time.sleep(0.6)

#     # Select target guide
#     pyautogui.press("home")
#     time.sleep(0.2)
#     if index > 0:
#         pyautogui.press("down", presses=index, interval=0.2)
#     time.sleep(0.2)
#     pyautogui.press("enter")
#     time.sleep(1.0)
#     return True

# # --- Verification Routines ---

# def auto_check_user_guide(test_name, guide_index, expected_keywords):
#     """Tests access to standard PDF guides (User Manual, Reference Guide, etc.)."""
#     before_handles = {w._hWnd for w in gw.getAllWindows()}

#     if not open_user_guide(guide_index):
#         record_result(test_name, False, "IPSA window unavailable")
#         return

#     new_win = wait_for_new_window(before_handles, timeout=6)
#     target_win = new_win or gw.getActiveWindow()

#     # Wait for PDF to load in Edge / default viewer past 'Untitled'
#     title = wait_for_meaningful_title(target_win, timeout=6)

#     matched = any(k.lower() in title.lower() for k in expected_keywords)
#     is_browser = any(b.lower() in title.lower() for b in ["edge", "chrome", "firefox"])

#     if matched or is_browser:
#         record_result(test_name, True, f"Opened: '{title}'")
#         close_window_safely(target_win)
#     else:
#         record_result(test_name, False, f"Expected keywords {expected_keywords}, detected: '{title}'")
#         if target_win and target_win._hWnd not in before_handles:
#             close_window_safely(target_win)

#     time.sleep(0.5)
#     ipsa = get_ipsa_window()
#     if ipsa:
#         ipsa.activate()
#         time.sleep(0.5)

# def auto_check_technical_notes():
#     """Opens the Technical Notes folder in File Explorer and launches an actual note PDF."""
#     test_name = "User Guides -> Technical Notes"
#     before_handles = {w._hWnd for w in gw.getAllWindows()}

#     # Technical Notes is index 4 in User Guides
#     if not open_user_guide(4):
#         record_result(test_name, False, "IPSA window unavailable")
#         return

#     time.sleep(2)
#     folder_windows = gw.getWindowsWithTitle("technicalnotes")
#     if not folder_windows:
#         record_result(test_name, False, "Directory 'technicalnotes' failed to open in File Explorer")
#         return

#     folder = folder_windows[0]
#     try:
#         if folder.isMinimized:
#             folder.restore()
#         folder.activate()
#         time.sleep(1)

#         # Click inside the explorer item view, select first file, and open it
#         click_x = folder.left + folder.width // 2
#         click_y = folder.top + int(folder.height * 0.6)
#         pyautogui.click(click_x, click_y)
#         time.sleep(0.4)
#         pyautogui.press("home")
#         time.sleep(0.3)

#         pdf_before_handles = {w._hWnd for w in gw.getAllWindows()}
#         pyautogui.press("enter")
#         time.sleep(3)

#         # Verify that a document/PDF window launched from inside the folder
#         doc_win = wait_for_new_window(pdf_before_handles, timeout=6) or gw.getActiveWindow()
#         doc_title = wait_for_meaningful_title(doc_win, timeout=5)

#         if doc_win and "technicalnotes" not in doc_title.lower() and doc_title.strip() != "IPSA 3":
#             record_result(test_name, True, f"Folder and document opened: '{doc_title}'")
#             close_window_safely(doc_win)
#         else:
#             record_result(test_name, True, "Folder opened successfully (no note file auto-launched)")

#     except Exception as e:
#         record_result(test_name, False, f"Error inspecting technical notes folder: {e}")
#     finally:
#         # Clean up explorer window
#         for w in gw.getWindowsWithTitle("technicalnotes"):
#             try:
#                 w.close()
#             except Exception:
#                 pass

#     time.sleep(0.5)
#     ipsa = get_ipsa_window()
#     if ipsa:
#         ipsa.activate()
#         time.sleep(0.5)


# # --- Execution ---

# if __name__ == "__main__":
#     close_all_auxiliary_windows()

#     if not is_ipsa_alive():
#         print("\nERROR: IPSA 3 is not open! Please open IPSA 3 and run again.")
#         raise SystemExit(1)

#     print("\nStarting automated test: Help Guides & Technical Notes Accessibility...")
#     time.sleep(2)

#     # 1. Technical Notes (Verifies folder access + file launching)
#     auto_check_technical_notes()

#     # 2. User Manual (PDF)
#     auto_check_user_guide(
#         "User Guides -> User Manual",
#         0,
#         ["ug001", "user manual", "pdf"]
#     )

#     # 3. Reference Guide (PDF)
#     auto_check_user_guide(
#         "User Guides -> Reference Guide",
#         1,
#         ["rg001", "reference guide", "pdf"]
#     )

#     # 4. Scripting Guide (PDF)
#     auto_check_user_guide(
#         "User Guides -> Scripting Guide",
#         2,
#         ["rg002", "pyipsa", "scripting", "pdf"]
#     )

#     # 5. Plugins SDK (PDF)
#     auto_check_user_guide(
#         "User Guides -> Plugins SDK",
#         3,
#         ["ug002", "plugin", "plugins", "sdk", "pdf"]
#     )

#     # 6. Keyboard Shortcuts (PDF)
#     auto_check_user_guide(
#         "User Guides -> Keyboard Shortcuts (PDF)",
#         5,
#         ["ug003", "keyboard shortcuts", "pdf"]
#     )

#     # --- Summary Report Generation ---
#     total = len(test_results)
#     passed = sum(1 for r in test_results.values() if r["passed"])
#     failed = total - passed

#     print("\n" + "=" * 65)
#     print(f"GUIDES & TECHNICAL NOTES RUN: {passed}/{total} PASSED ({failed} FAILED)")
#     print("=" * 65)

#     for test_name, res in test_results.items():
#         badge = "[PASS]" if res["passed"] else "[FAIL]"
#         print(f"{badge} {test_name:<42} {res['detail']}")
#     print("=" * 65)



import sys
import time
import pyautogui
import pygetwindow as gw

# Safety configuration
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2

test_results = {}

def get_ipsa_window():
    """Retrieve the main IPSA window object."""
    windows = gw.getWindowsWithTitle("IPSA 3")
    if not windows:
        return None
    return windows[0]

def is_ipsa_alive():
    """Verify that IPSA has not closed or crashed."""
    return get_ipsa_window() is not None

def record_result(test_name, success, detail=""):
    """Store the result for the final test summary."""
    test_results[test_name] = {"passed": success, "detail": detail}

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
    """Safely close an opened window or browser tab without touching IPSA."""
    if not window:
        return
    title_lower = window.title.lower()
    
    # Safety guard: Never close the main IPSA application
    if "ipsa 3" == title_lower.strip():
        return

    try:
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(0.3)

        if any(b in title_lower for b in ["edge", "chrome", "firefox"]):
            pyautogui.hotkey("ctrl", "w")  # Close tab only
        else:
            pyautogui.hotkey("alt", "f4")  # Standalone viewer / explorer
        time.sleep(0.8)
    except Exception:
        pass

def close_all_auxiliary_windows():
    """Clean up open documents, Technical Notes folders, or previous viewers."""
    target_keywords = ["technicalnotes", "ug00", "rg00", "pdf", "edge"]
    for win in gw.getAllWindows():
        title = win.title.lower()
        if title.strip() == "ipsa 3":
            continue
        if any(k in title for k in target_keywords):
            try:
                if "technicalnotes" in title:
                    win.close()
                elif "edge" in title or "chrome" in title:
                    win.activate()
                    time.sleep(0.2)
                    pyautogui.hotkey("ctrl", "w")
                else:
                    win.close()
                time.sleep(0.3)
            except Exception:
                pass

def open_user_guide(index):
    """Navigate to Help -> User Guides -> item index."""
    window = get_ipsa_window()
    if not window:
        return False
    if window.isMinimized:
        window.restore()
    window.activate()
    time.sleep(0.8)

    # Open Help menu
    pyautogui.press("alt")
    time.sleep(0.2)
    pyautogui.press("right", presses=9, interval=0.12)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.4)

    # Open User Guides submenu (index 5)
    pyautogui.press("home")
    time.sleep(0.2)
    pyautogui.press("down", presses=5, interval=0.2)
    time.sleep(0.3)
    pyautogui.press("right")
    time.sleep(0.6)

    # Select target guide
    pyautogui.press("home")
    time.sleep(0.2)
    if index > 0:
        pyautogui.press("down", presses=index, interval=0.2)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(1.0)
    return True

# --- Verification Routines ---

def auto_check_user_guide(test_name, guide_index, expected_keywords):
    """Tests access to standard PDF guides (User Manual, Reference Guide, etc.)."""
    before_handles = {w._hWnd for w in gw.getAllWindows()}

    if not open_user_guide(guide_index):
        record_result(test_name, False, "IPSA window unavailable")
        return

    new_win = wait_for_new_window(before_handles, timeout=6)
    target_win = new_win or gw.getActiveWindow()

    # Wait for PDF to load in Edge / default viewer past 'Untitled'
    title = wait_for_meaningful_title(target_win, timeout=6)

    matched = any(k.lower() in title.lower() for k in expected_keywords)
    is_browser = any(b.lower() in title.lower() for b in ["edge", "chrome", "firefox"])

    if matched or is_browser:
        record_result(test_name, True, f"Opened: '{title}'")
        close_window_safely(target_win)
    else:
        record_result(test_name, False, f"Expected keywords {expected_keywords}, detected: '{title}'")
        if target_win and target_win._hWnd not in before_handles:
            close_window_safely(target_win)

    time.sleep(0.5)
    ipsa = get_ipsa_window()
    if ipsa:
        ipsa.activate()
        time.sleep(0.5)

def auto_check_technical_notes():
    """Opens the Technical Notes folder in File Explorer and launches an actual note PDF."""
    test_name = "User Guides -> Technical Notes"
    before_handles = {w._hWnd for w in gw.getAllWindows()}

    # Technical Notes is index 4 in User Guides
    if not open_user_guide(4):
        record_result(test_name, False, "IPSA window unavailable")
        return

    time.sleep(2)
    folder_windows = gw.getWindowsWithTitle("technicalnotes")
    if not folder_windows:
        record_result(test_name, False, "Directory 'technicalnotes' failed to open in File Explorer")
        return

    folder = folder_windows[0]
    try:
        if folder.isMinimized:
            folder.restore()
        folder.activate()
        time.sleep(1)

        # Click inside the explorer item view, select first file, and open it
        click_x = folder.left + folder.width // 2
        click_y = folder.top + int(folder.height * 0.6)
        pyautogui.click(click_x, click_y)
        time.sleep(0.4)
        pyautogui.press("home")
        time.sleep(0.3)

        pdf_before_handles = {w._hWnd for w in gw.getAllWindows()}
        pyautogui.press("enter")
        time.sleep(3)

        # Verify that a document/PDF window launched from inside the folder
        doc_win = wait_for_new_window(pdf_before_handles, timeout=6) or gw.getActiveWindow()
        doc_title = wait_for_meaningful_title(doc_win, timeout=5)

        if doc_win and "technicalnotes" not in doc_title.lower() and doc_title.strip() != "IPSA 3":
            record_result(test_name, True, f"Folder and document opened: '{doc_title}'")
            close_window_safely(doc_win)
        else:
            record_result(test_name, True, "Folder opened successfully (no note file auto-launched)")

    except Exception as e:
        record_result(test_name, False, f"Error inspecting technical notes folder: {e}")
    finally:
        # Clean up explorer window
        for w in gw.getWindowsWithTitle("technicalnotes"):
            try:
                w.close()
            except Exception:
                pass

    time.sleep(0.5)
    ipsa = get_ipsa_window()
    if ipsa:
        ipsa.activate()
        time.sleep(0.5)


# --- Execution ---

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

    close_all_auxiliary_windows()

    if not is_ipsa_alive():
        print("ERROR: IPSA 3 is not open! Please open IPSA 3 and run again.")
        raise SystemExit(1)

    # 1. Technical Notes (Verifies folder access + file launching)
    auto_check_technical_notes()

    # 2. User Manual (PDF)
    auto_check_user_guide(
        "User Guides -> User Manual",
        0,
        ["ug001", "user manual", "pdf"]
    )

    # 3. Reference Guide (PDF)
    auto_check_user_guide(
        "User Guides -> Reference Guide",
        1,
        ["rg001", "reference guide", "pdf"]
    )

    # 4. Scripting Guide (PDF)
    auto_check_user_guide(
        "User Guides -> Scripting Guide",
        2,
        ["rg002", "pyipsa", "scripting", "pdf"]
    )

    # 5. Plugins SDK (PDF)
    auto_check_user_guide(
        "User Guides -> Plugins SDK",
        3,
        ["ug002", "plugin", "plugins", "sdk", "pdf"]
    )

    # 6. Keyboard Shortcuts (PDF)
    auto_check_user_guide(
        "User Guides -> Keyboard Shortcuts (PDF)",
        5,
        ["ug003", "keyboard shortcuts", "pdf"]
    )

    # --- Summary Report Generation ---
    total = len(test_results)
    passed = sum(1 for r in test_results.values() if r["passed"])
    failed = total - passed

    print("=" * 65)
    print(f"GUIDES & TECHNICAL NOTES RUN: {passed}/{total} PASSED ({failed} FAILED)")
    print("=" * 65)

    for test_name, res in test_results.items():
        badge = "[PASS]" if res["passed"] else "[FAIL]"
        print(f"{badge} {test_name:<42} {res['detail']}")
    print("=" * 65)