import ctypes
import sys
import time

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

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2

WINDOW_TIMEOUT = 15
APP = None
WIN = None


def report_error(message):
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
   Please ensure you launch a CLEAN / FRESH session of IPSA 3 before starting
   the test. No active or modified networks should be open.

2. DO NOT TOUCH MOUSE OR KEYBOARD:
   Automated keystrokes and clicks will control your system. Any manual input
   will interfere with window focus and cause steps to fail.

3. EMERGENCY STOP (FAILSAFE):
   To terminate automation immediately at any point, move your mouse pointer
   to the TOP-LEFT CORNER of the screen (x=0, y=0).
===============================================================================
"""
    print(banner)
    print("Automation will begin in 15 seconds. Please read the above instructions...")
    for remaining in range(15, 0, -1):
        sys.stdout.write(f"\rStarting test in {remaining:2d} seconds... [Press Ctrl+C to cancel]")
        sys.stdout.flush()
        time.sleep(1.0)
    sys.stdout.write("\rRunning test quietly. Errors will be reported below...\n\n")
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
    time.sleep(0.3)
    pyautogui.hotkey("alt", "f")
    time.sleep(0.3)
    for _ in range(index):
        pyautogui.press("down")
        time.sleep(0.05)
    pyautogui.press("enter")
    time.sleep(0.6)


def wait_for_wizard_dialog(timeout=6):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for w in gw.getAllWindows():
            if "create a new network" in w.title.strip().lower():
                try:
                    w.activate()
                    time.sleep(0.3)
                    return w
                except Exception:
                    pass
        time.sleep(0.2)
    return None


def handle_save_prompt():
    for w in gw.getAllWindows():
        title = w.title.strip().lower()
        if "save" in title or "confirm" in title:
            w.activate()
            time.sleep(0.2)
            pyautogui.press("n")
            time.sleep(0.3)
            return True
    return False


def click_wizard_next(wizard_win):
    wizard_win.activate()
    time.sleep(0.3)
    clicked = False
    try:
        wizard_uia = Desktop(backend="uia").window(title_re=r".*Create a New Network.*")
        if wizard_uia.exists(timeout=1):
            for b in wizard_uia.descendants(control_type="Button"):
                if clean(b.window_text()).casefold() == "next":
                    b.click_input()
                    clicked = True
                    break
    except Exception:
        pass

    if not clicked:
        btn_x = wizard_win.left + wizard_win.width - 165
        btn_y = wizard_win.top + wizard_win.height - 35
        pyautogui.click(btn_x, btn_y)

    time.sleep(1.2)


def click_wizard_finish(wizard_win):
    wizard_win.activate()
    time.sleep(0.3)
    clicked = False
    try:
        wizard_uia = Desktop(backend="uia").window(title_re=r".*Create a New Network.*")
        if wizard_uia.exists(timeout=1):
            for b in wizard_uia.descendants(control_type="Button"):
                if clean(b.window_text()).casefold() == "finish":
                    b.click_input()
                    clicked = True
                    break
    except Exception:
        pass

    if not clicked:
        btn_x = wizard_win.left + wizard_win.width - 165
        btn_y = wizard_win.top + wizard_win.height - 35
        pyautogui.click(btn_x, btn_y)

    time.sleep(2.0)


def detect_and_dismiss_query_failed(timeout=3.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for w in Desktop(backend="uia").windows():
            try:
                title = w.window_text().strip()
                if title == "IPSA 3" and w.rectangle().width() < 500:
                    texts = [c.window_text().strip() for c in w.descendants()]
                    if any("query failed" in t.lower() for t in texts):
                        for btn in w.descendants(control_type="Button"):
                            if clean(btn.window_text()).casefold() == "ok":
                                btn.click_input()
                                time.sleep(0.3)
                                return True
                        w.set_focus()
                        pyautogui.press("enter")
                        time.sleep(0.3)
                        return True
            except Exception:
                continue

        for w in gw.getAllWindows():
            if w.title.strip() == "IPSA 3" and w.width < 500:
                w.activate()
                time.sleep(0.2)
                pyautogui.press("enter")
                time.sleep(0.3)
                return True

        time.sleep(0.25)
    return False


def test_geographic_diagram_with_map(search_place="india", new_diagram_name="India Geographic", network_title="Geo_India_Grid"):
    _, win = get_ipsa_window()
    if win is None:
        report_error("IPSA 3 is not running.")
        print("\n==================================================")
        print("[FAIL] Geographic diagram with map created successfully.")
        print("==================================================\n")
        return False

    handle_save_prompt()
    open_file_item(0)

    # Page 1: Diagram Choice
    wizard = wait_for_wizard_dialog(timeout=6)
    if not wizard:
        report_error("'Create a New Network' dialog did not appear.")
        print("\n==================================================")
        print("[FAIL] Geographic diagram with map created successfully.")
        print("==================================================\n")
        return False

    wizard.activate()
    time.sleep(0.4)

    pyautogui.press("down")
    time.sleep(0.2)
    pyautogui.press("down")
    time.sleep(0.2)
    pyautogui.press("space")
    time.sleep(0.4)

    click_wizard_next(wizard)

    # Page 2: Geographic Diagram with Map & Place Search
    wizard = wait_for_wizard_dialog(timeout=6)
    if not wizard:
        report_error("Failed to open Map Properties page.")
        print("\n==================================================")
        print("[FAIL] Geographic diagram with map created successfully.")
        print("==================================================\n")
        return False

    wizard.activate()
    time.sleep(0.4)

    place_x = wizard.left + int(wizard.width * 0.28)
    place_y = wizard.top + int(wizard.height * 0.415)

    pyautogui.click(place_x, place_y)
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    time.sleep(0.1)
    pyautogui.typewrite(search_place, interval=0.04)
    time.sleep(0.4)

    search_x = wizard.left + int(wizard.width * 0.45)
    search_y = wizard.top + int(wizard.height * 0.415)
    pyautogui.click(search_x, search_y)
    time.sleep(1.5)

    has_failed = detect_and_dismiss_query_failed(timeout=3.0)

    if has_failed:
        report_error(f"Search place query failed for '{search_place}'.")
        time.sleep(0.4)
        pyautogui.press("esc")
        time.sleep(0.3)
        pyautogui.press("esc")
        print("\n==================================================")
        print("[FAIL] Geographic diagram with map created successfully.")
        print("==================================================\n")
        return False

    # Rename Diagram Name field
    wizard = wait_for_wizard_dialog(timeout=4)
    if wizard:
        wizard.activate()
        time.sleep(0.3)
        name_x = wizard.left + int(wizard.width * 0.35)
        name_y = wizard.top + int(wizard.height * 0.31)
        pyautogui.click(name_x, name_y)
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.typewrite(new_diagram_name, interval=0.03)
        time.sleep(0.4)

        click_wizard_next(wizard)
    else:
        report_error("Wizard lost after search.")
        print("\n==================================================")
        print("[FAIL] Geographic diagram with map created successfully.")
        print("==================================================\n")
        return False

    # Page 3: Network Properties -> Title & Finish
    wizard = wait_for_wizard_dialog(timeout=6)
    if not wizard:
        report_error("Failed to open Network Properties page.")
        print("\n==================================================")
        print("[FAIL] Geographic diagram with map created successfully.")
        print("==================================================\n")
        return False

    wizard.activate()
    time.sleep(0.4)

    title_x = wizard.left + int(wizard.width * 0.35)
    title_y = wizard.top + int(wizard.height * 0.25)
    pyautogui.click(title_x, title_y)
    time.sleep(0.2)

    pyautogui.hotkey("ctrl", "a")
    pyautogui.typewrite(network_title, interval=0.03)
    time.sleep(0.4)

    click_wizard_finish(wizard)

    # Verification
    time.sleep(1.0)
    all_titles = [w.title for w in gw.getAllWindows() if w.title]
    geo_active = any("Main geographic" in t or "geographic" in t.lower() or new_diagram_name.lower() in t.lower() for t in all_titles)

    print("\n==================================================")
    if geo_active:
        print("[PASS] Geographic diagram with map created successfully.")
    else:
        print("[FAIL] Geographic diagram did not load.")
    print("==================================================\n")
    return geo_active


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

    test_geographic_diagram_with_map(search_place="india", new_diagram_name="India Geographic", network_title="Geo_India_Grid")


if __name__ == "__main__":
    main()