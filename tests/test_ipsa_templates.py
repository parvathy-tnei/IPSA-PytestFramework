import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

import sys
import time

import pyautogui
import pygetwindow as gw
from pywinauto import Application, Desktop

# FailSafe triggers when the mouse cursor hits any screen corner (default: top-left (0, 0))
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

WINDOW_TIMEOUT = 15
APP = None
WIN = None


def report_error(message):
    """Prints only critical errors during test execution."""
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
   this suite. No active or modified networks should be open.

2. DO NOT TOUCH MOUSE OR KEYBOARD:
   Automated keystrokes and clicks will control your system. Any manual input
   will interfere with window focus and cause placement steps to fail.

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
    sys.stdout.write("\rRunning template tests quietly. Errors will be reported below...\n\n")
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


def open_file_item(index):
    _, win = get_ipsa_window()
    if win is None:
        return
    win.set_focus()
    time.sleep(0.2)
    pyautogui.hotkey("alt", "f")
    time.sleep(0.3)
    for _ in range(index):
        pyautogui.press("down")
        time.sleep(0.05)
    pyautogui.press("enter")
    time.sleep(0.5)


def wait_for_new_window(before_handles, timeout=3):
    deadline = time.time() + timeout
    while time.time() < deadline:
        current_windows = gw.getAllWindows()
        for w in current_windows:
            if w._hWnd not in before_handles and w.title.strip():
                return w
        time.sleep(0.2)
    return None


def create_new_network_wizard():
    """Opens File -> New network (index 0) and completes Next -> Next -> Finish."""
    before_handles = {w._hWnd for w in gw.getAllWindows()}
    open_file_item(0)

    wizard = wait_for_new_window(before_handles, timeout=4) or gw.getActiveWindow()
    title = wizard.title.strip().lower() if wizard else ""

    if wizard and ("new network" in title or "wizard" in title or wizard._hWnd not in before_handles):
        wizard.activate()
        time.sleep(0.4)
        
        # Step 1: Next
        pyautogui.press("enter")
        time.sleep(0.5)
        
        # Step 2: Next
        pyautogui.press("enter")
        time.sleep(0.5)
        
        # Step 3: Finish
        pyautogui.press("enter")
        time.sleep(1.0)
        return True
    else:
        report_error("New network wizard dialog did not appear.")
        pyautogui.press("esc")
        return False


def open_templates_panel():
    """Toggles and reveals the Templates dock panel."""
    _, win = get_ipsa_window()
    if win is None:
        return None

    try:
        # Check/click Templates button on the left dock
        for ctrl in win.descendants():
            try:
                title = ctrl.window_text().strip().casefold()
                c_type = ctrl.element_info.control_type
                if title == "templates" and c_type in ("CheckBox", "TabItem", "Button"):
                    if c_type == "CheckBox":
                        if ctrl.get_toggle_state() == 0:
                            ctrl.click_input()
                    else:
                        ctrl.click_input()
                    time.sleep(0.5)
                    break
            except Exception:
                continue

        # Locate the opened Templates panel
        for w in win.children() + win.descendants(control_type="Window"):
            try:
                if w.window_text().strip().casefold() == "templates" and w.is_visible():
                    return w
            except Exception:
                continue

        return None
    except Exception as error:
        report_error(f"Failed opening Templates panel: {error}")
        return None


def get_template_items(panel):
    """Finds all template entries inside the Templates panel."""
    items = []
    for item in panel.descendants(control_type="ListItem"):
        try:
            if item.is_visible() and item.rectangle().height() > 0:
                name = item.window_text().strip()
                if name and name.casefold() != "templates":
                    items.append((name, item))
        except Exception:
            continue

    if not items:
        known = [
            "33kV Double Busbar",
            "WF Collector String",
            "11kV RMU Loop (H)",
            "132kV Main and Reserve",
            "11kV RMU T (H)",
        ]
        for name in known:
            for elem in panel.descendants():
                try:
                    if name.casefold() in elem.window_text().strip().casefold() and elem.is_visible():
                        items.append((name, elem))
                        break
                except Exception:
                    continue

    seen = set()
    unique = []
    for name, ctrl in items:
        if name not in seen:
            seen.add(name)
            unique.append((name, ctrl))
    return unique


def clear_canvas(canvas_x, canvas_y):
    """Clicks the canvas, selects all components, and deletes them."""
    pyautogui.click(canvas_x, canvas_y)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.2)
    pyautogui.press("delete")
    time.sleep(0.3)

    # Dismiss any confirmation dialog if IPSA prompts "Are you sure you want to delete..."
    for w in Desktop(backend="uia").windows(process=APP.process):
        title = w.window_text().strip().casefold()
        if "delete" in title or "confirm" in title or "warning" in title:
            for b in w.descendants(control_type="Button"):
                t = clean(b.window_text()).casefold()
                if t in ("yes", "ok", "&yes", "&ok"):
                    b.click_input()
                    break
            break
    time.sleep(0.3)


def check_all_templates(overall_results):
    _, win = get_ipsa_window()
    if win is None:
        return

    # 1. Create fresh network
    if not create_new_network_wizard():
        report_error("Failed to initialize a new network canvas.")
        return

    # 2. Open Templates dock
    panel = open_templates_panel()
    if panel is None:
        report_error("Could not find or open the Templates panel.")
        return

    # 3. Read template list
    template_items = get_template_items(panel)
    if not template_items:
        report_error("No templates detected inside the Templates panel.")
        return

    # Canvas drop coordinate (middle area of the single-line diagram canvas)
    win_rect = win.rectangle()
    panel_rect = panel.rectangle()
    canvas_x = panel_rect.right + int((win_rect.right - panel_rect.right) * 0.4)
    canvas_y = panel_rect.top + int(panel_rect.height() * 0.35)

    # 4. Iterate over each template
    for name, item_ctrl in template_items:
        try:
            # Click template in list
            item_ctrl.click_input()
            time.sleep(0.4)

            # Click on diagram canvas to place
            pyautogui.click(canvas_x, canvas_y)
            time.sleep(0.5)

            # Exit placement mode
            pyautogui.press("esc", presses=2, interval=0.1)
            time.sleep(0.3)

            # Check for error popups
            has_error = False
            for w in Desktop(backend="uia").windows(process=APP.process):
                t = w.window_text().strip().casefold()
                if "error" in t or "exception" in t or "warning" in t:
                    has_error = True
                    report_error(f"Dialog '{w.window_text().strip()}' encountered while placing template '{name}'.")
                    for b in w.descendants(control_type="Button"):
                        if clean(b.window_text()).casefold() == "ok":
                            b.click_input()
                            break
                    break

            overall_results[name] = not has_error

            # Wipe canvas clean before testing the next template
            clear_canvas(canvas_x, canvas_y)

        except Exception as ex:
            report_error(f"Exception while placing '{name}': {ex}")
            overall_results[name] = False
            clear_canvas(canvas_x, canvas_y)


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
    check_all_templates(overall_results)

    # Final Combined Summary Table
    print("\n=======================================================")
    print("             TEMPLATES PLACEMENT SUMMARY               ")
    print("=======================================================")
    if overall_results:
        for template_name, passed in overall_results.items():
            status = "[PASS]" if passed else "[FAIL]"
            print(f"{status:<8} {template_name}")
    else:
        print("No templates were tested.")
    print("=======================================================\n")


if __name__ == "__main__":
    main()