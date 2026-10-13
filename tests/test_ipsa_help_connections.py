
# import time
# import pyautogui
# import pygetwindow as gw

# pyautogui.FAILSAFE = True
# EXPECTED_UPDATE_URL = "https://www.ipsa-power.com/latest-version/"


# def get_ipsa_window():
#     windows = gw.getWindowsWithTitle("IPSA 3")

#     if not windows:
#         print("\nERROR: IPSA 3 is not open!")
#         print("Please open IPSA 3 and run the test again.")
#         raise SystemExit(1)
#     return windows[0]


# def open_help_item(index):
#     window = get_ipsa_window()

#     if window.isMinimized:
#         window.restore()

#     window.activate()
#     time.sleep(1)

#     # Open the Help menu
#     pyautogui.press("alt")
#     pyautogui.press("right", presses=9, interval=0.15)
#     pyautogui.press("enter")
#     time.sleep(0.5)

#     # Select the required Help menu item
#     pyautogui.press("home")
#     pyautogui.press("down", presses=index, interval=0.2)
#     pyautogui.press("enter")
#     time.sleep(2)


# def check_dialog(name, index):
#     print(f"\nTesting Help -> {name.replace('_', ' ').title()}...")

#     open_help_item(index)

#     answer = input(
#         f"Did the {name.replace('_', ' ').title()} dialog open correctly? (y/n): "
#     ).strip().lower()

#     if answer == "y":
#         print(
#             f"{name.replace('_', ' ').title()} "
#             "connection successful!"
#         )
#     elif answer == "n":
#         print(
#             f"{name.replace('_', ' ').title()} "
#             "connection failed!"
#         )
#     else:
#         print("Invalid input. Please enter y or n.")

#     # Close the dialog automatically
#     print("Dialog will close in 2 seconds...")
#     time.sleep(1)

#     window = get_ipsa_window()
#     window.activate()
#     time.sleep(0.5)
#     pyautogui.hotkey("alt", "f4")
#     time.sleep(1)


# # Run tests
# get_ipsa_window()

# check_dialog("about", 0)
# check_dialog("about_qt", 1)

# print("\nAll IPSA Help connection tests completed.")




import time
import pyautogui
import pygetwindow as gw
import pyperclip

pyautogui.FAILSAFE = True

EXPECTED_UPDATE_URL = "https://www.ipsa-power.com/latest-version/"


def get_ipsa_window():
    windows = gw.getWindowsWithTitle("IPSA 3")

    if not windows:
        print("\nERROR: IPSA 3 is not open!")
        print("Please open IPSA 3 and run the test again.")
        raise SystemExit(1)

    return windows[0]


def close_document_or_browser(document_window_title):
    """Close the opened document, not the VS Code terminal."""

    if not document_window_title:
        print("Could not identify the document window. Leaving it open.")
        return

    print("Closing the opened document in 2 seconds...")
    time.sleep(2)

    windows = gw.getWindowsWithTitle(document_window_title)

    if windows:
        document_window = windows[0]

        try:
            if document_window.isMinimized:
                document_window.restore()

            document_window.activate()
            time.sleep(2)

            # Close the document window, not the VS Code terminal.
            pyautogui.hotkey("alt", "f4")
            time.sleep(2)

            print("Document close command sent.")

        except Exception as error:
            print(f"Could not close the document safely: {error}")
    else:
        print("Document window not found. Leaving it open.")

def open_help_item(index):
    window = get_ipsa_window()

    if window.isMinimized:
        window.restore()

    window.activate()
    time.sleep(1)

    # Open the Help menu
    pyautogui.press("alt")
    pyautogui.press("right", presses=9, interval=0.15)
    pyautogui.press("enter")
    time.sleep(0.5)

    # Select the required Help menu item
    pyautogui.press("home")
    pyautogui.press("down", presses=index, interval=0.2)
    pyautogui.press("enter")
    time.sleep(2)


def get_user_confirmation(prompt):
    while True:
        answer = input(prompt).strip().lower()

        if answer in ("y", "n"):
            return answer

        print("Invalid input. Please enter y or n.")


def check_dialog(name, index):
    display_name = name.replace("_", " ").title()

    print(f"\nTesting Help -> {display_name}...")

    open_help_item(index)

    answer = get_user_confirmation(
        f"Did the {display_name} dialog open correctly? (y/n): "
    )

    if answer == "y":
        print(f"{display_name} connection successful!")
    else:
        print(f"{display_name} connection failed!")

    # Close the dialog
    print("Dialog will close in 2 seconds...")
    time.sleep(1)

    window = get_ipsa_window()
    window.activate()
    time.sleep(0.5)
    pyautogui.hotkey("alt", "f4")
    time.sleep(2)


def open_user_guide(guide_index):
    window = get_ipsa_window()

    if window.isMinimized:
        window.restore()

    window.activate()
    time.sleep(2)

    # Open Help menu
    pyautogui.press("alt")
    pyautogui.press("right", presses=9, interval=0.15)
    pyautogui.press("enter")
    time.sleep(0.5)

    # Select User Guides submenu
    pyautogui.press("home")
    pyautogui.press("down", presses=5, interval=0.2)
    pyautogui.press("right")
    time.sleep(0.5)

    # Select the required guide
    pyautogui.press("home")
    pyautogui.press(
        "down", presses=guide_index, interval=0.2
    )
    pyautogui.press("enter")
    time.sleep(4)


def check_user_guide(name, guide_index):
    print(f"\nTesting User Guides -> {name}...")

    open_user_guide(guide_index)

     # Capture the active document window before input() changes focus.
    active_window = gw.getActiveWindow()
    document_title = active_window.title if active_window else None

    answer = get_user_confirmation(
        f"Did the correct {name} document open? (y/n): "
    )

    if answer == "y":
        print(f"{name} connection successful!")
        close_document_or_browser(document_title)
    else:
        print(f"{name} connection failed! Document is left open")

    print("Returning to IPSA in 2 seconds...")
    time.sleep(2)

    # Do not automatically close the document here.
    # The document might open in a shared browser window.
    get_ipsa_window().activate()
    time.sleep(2)


def open_interactive_help(guide_index):
    window = get_ipsa_window()

    if window.isMinimized:
        window.restore()

    window.activate()
    time.sleep(2)

    # Open Help menu
    pyautogui.press("alt")
    pyautogui.press("right", presses=9, interval=0.15)
    pyautogui.press("enter")
    time.sleep(0.5)

    # Navigate to Interactive Help
    # Assumes Interactive Help is Help menu item index 6
    pyautogui.press("home")
    pyautogui.press("down", presses=6, interval=0.2)
    pyautogui.press("right")
    time.sleep(0.5)

    # Select the required guide
    pyautogui.press("home")
    pyautogui.press(
        "down", presses=guide_index, interval=0.2
    )
    pyautogui.press("enter")
    time.sleep(4)


def check_interactive_help(name, guide_index):
    print(f"\nTesting Interactive Help -> {name}...")

    open_interactive_help(guide_index)

     # Capture the opened window before asking for confirmation.
    active_window = gw.getActiveWindow()
    document_title = (
        active_window.title if active_window else None
    )

    answer = get_user_confirmation(
        f"Did the correct {name} open? (y/n): "
    )

    if answer == "y":
        print(f"Interactive Help -> {name}: Connection successful!")
        close_document_or_browser(document_title)
    else:
        print(f"Interactive Help -> {name}: Connection failed! Document left open.")

    print("Returning to IPSA in 2 seconds...")
    time.sleep(2)

    get_ipsa_window().activate()
    time.sleep(2)

def open_help_submenu_item(submenu_index, item_index):
    window = get_ipsa_window()

    if window.isMinimized:
        window.restore()

    window.activate()
    time.sleep(2)

    # Open Help menu
    pyautogui.press("alt")
    pyautogui.press("right", presses=9, interval=0.15)
    pyautogui.press("enter")
    time.sleep(0.5)

    # Select the submenu
    pyautogui.press("home")
    pyautogui.press(
        "down", presses=submenu_index, interval=0.2
    )
    pyautogui.press("right")
    time.sleep(0.5)

    # Select the submenu item
    pyautogui.press("home")
    pyautogui.press(
        "down", presses=item_index, interval=0.2
    )
    pyautogui.press("enter")
    time.sleep(4)


def check_help_submenu_item(submenu_name, item_name,
                            submenu_index, item_index):
    print(f"\nTesting {submenu_name} -> {item_name}...")

    open_help_submenu_item(submenu_index, item_index)

    active_window = gw.getActiveWindow()
    document_title = active_window.title if active_window else None

    answer = get_user_confirmation(
        f"Did {submenu_name} -> {item_name} open correctly? (y/n): "
    )

    if answer == "y":
        print(f"{item_name} connection successful!")
        close_document_or_browser(document_title)
    else:
        print(f"{item_name} connection failed!")

    print("Test finished. Returning to IPSA in 2 seconds...")
    time.sleep(2)

    get_ipsa_window().activate()
    time.sleep(2)

def check_help_website(name, index):
    print(f"\nTesting Help -> {name}...")

    # Open the selected Help menu item
    open_help_item(index)

    # Allow time for the browser page to open
    time.sleep(3)

    active_window = gw.getActiveWindow()
    document_title = active_window.title if active_window else None

    answer = get_user_confirmation(
        f"Did the correct {name} page open? (y/n): "
    )

    if answer == "y":
        print(f"{name} connection successful!")
        close_document_or_browser(document_title)
    else:
        print(f"{name} connection failed!")

    print("Test completed.")
    time.sleep(2)

    # Return focus to IPSA without closing the browser
    get_ipsa_window().activate()
    time.sleep(2)

def check_for_updates():
    print("\nTesting Help -> Check for Updates...")

    open_help_item(2)

    print("\nExpected URL:")
    print(EXPECTED_UPDATE_URL)

    answer = get_user_confirmation(
        "Did the correct Check for Updates page open? (y/n): "
    )

    if answer == "y":
        print("Check for Updates connection successful!")
    else:
        print("Check for Updates connection failed!")

    # Close the browser tab after confirmation
    print("Browser tab will close in 2 seconds...")
    time.sleep(2)

    # Activate the browser window
    browser_titles = [
        "Microsoft Edge",
        "Google Chrome",
        "Mozilla Firefox"
    ]

    browser_window = None

    for title in browser_titles:
        windows = gw.getWindowsWithTitle(title)
        if windows:
            browser_window = windows[0]
            break

    if browser_window:
        if browser_window.isMinimized:
            browser_window.restore()

        browser_window.activate()
        time.sleep(2)

        pyautogui.hotkey("ctrl", "w")
        time.sleep(2)

        print("Browser tab closed.")
    else:
        print("Browser window not found. Please close it manually.")

# Run tests
get_ipsa_window()

print("\n" + "=" * 60)
print("WARNING: IPSA AUTOMATION TEST")
print("=" * 60)
print("1. Do not click or interact with IPSA during menu navigation.")
print("2. Avoid switching to other application windows.")
print("3. Move the mouse to the top-left corner for an emergency stop.")
print("=" * 60)

input("\nPress Enter to start the tests...")

check_dialog("about", 0)
check_dialog("about_qt", 1)
check_for_updates()

check_dialog("keyboard_shortcuts", 4)

check_user_guide("User Manual", 0)
check_user_guide("Reference Guide", 1)
check_user_guide("Scripting Guide", 2)
check_user_guide("Plugins SDK", 3)
check_user_guide("Technical Notes", 4)
check_user_guide("Keyboard Shortcuts (PDF)", 5)


# Interactive Help
check_help_submenu_item("Interactive Help", "User Manual", 6, 0)
check_help_submenu_item("Interactive Help", "Reference Guide", 6, 1)

# Examples
check_help_submenu_item("Examples", "Examples", 8, 0)
check_help_submenu_item("Examples", "Scripts", 8, 1)
check_help_submenu_item("Examples", "UDM Examples", 8, 2)


check_help_website("IPSA Knowledge Hub", 9)
check_help_website("PyIPSA ReadTheDocs", 10)
check_help_website("LinkedIn", 11)

check_dialog("licensing", 3)

print("\nAll IPSA Help connection tests completed.")



print("\nAll IPSA Help connection tests completed.")
