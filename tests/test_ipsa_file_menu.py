


import time
import pyautogui
import pygetwindow as gw
import os

pyautogui.FAILSAFE = True

# ---------------------------------------------------
# Find IPSA 3
# ---------------------------------------------------
windows = gw.getWindowsWithTitle("IPSA 3")

if not windows:
    print("IPSA 3 is not open!")
    raise SystemExit

window = windows[0]

print("\n" + "=" * 60)
print("WARNING: IPSA AUTOMATION TEST")
print("=" * 60)
print("1. Do not click or interact with IPSA during menu navigation.")
print("2. Avoid switching to other application windows.")
print("3. Move the mouse to the top-left corner for an emergency stop.")
print("=" * 60)

input("\nPress Enter to start the tests...")

if window.isMinimized:
    window.restore()

window.activate()
time.sleep(2)


import os

notes = []     

def ask(question):
    os.system("cls")                       # clear the terminal
    print(f"IPSA File Menu Test | items done: {len(results)}")
    print("-" * 50)

    answer = ""
    while answer not in ("y", "n"):
        answer = input(question.replace("File > ", "") + " (y/n): ").strip().lower()
    return answer == "y"




def save_result(name, ok):
    if ok == "SKIPPED":
        result = "SKIPPED"
    else:
        result = "SUCCESS" if ok else "FAILURE"

    results[name] = result

    # Print the result immediately after each test.
    print(f"\n{name}: {result}")


def open_file_item(index, submenu=False):
    """Open the File menu, go down to the item and open it."""
    window.activate()
    time.sleep(2)
    pyautogui.press("alt")
    time.sleep(1)
    pyautogui.press("enter")
    time.sleep(1)
    pyautogui.press("down", presses=index, interval=0.3)
    time.sleep(1)
    pyautogui.press("right" if submenu else "enter")
    time.sleep(3)


# ---------------------------------------------------
# New network (3-page wizard)
# ---------------------------------------------------
def test_new_network():
    open_file_item(0)

    wizard = gw.getActiveWindow() or window
    ok = True

    pages = [
        "Page 1 (Diagram Choice)",
        "Page 2 (Single Line Diagram)",
        "Page 3 (Network Properties)",
    ]

    for i, page in enumerate(pages):
        if not ask(f"File > New network > {page} opened correctly?"):
            ok = False

        # Next on pages 1 and 2 (page 3 has Finish, so we stop there)
        if i < 2:
            wizard.activate()
            time.sleep(1)
            pyautogui.press("enter")
            time.sleep(2)

    # Cancel the wizard so no network is created
    wizard.activate()
    time.sleep(1)
    pyautogui.press("esc")
    time.sleep(1)

    save_result("New network", ok)


# ---------------------------------------------------
# Add diagram (4-page wizard + info message)
# ---------------------------------------------------
def test_add_diagram():
    open_file_item(1)

    wizard = gw.getActiveWindow() or window
    ok = True

    pages = [
        "Page 1 (Diagram Choice)",
        "Page 2 (Single Line Diagram)",
        "Page 3 (Copying)",
        "Page 4 (Complete)",
    ]

    for i, page in enumerate(pages):
        if not ask(f"File > Add diagram > {page} opened correctly?"):
            ok = False

        wizard.activate()
        time.sleep(1)

        # Type a name on page 2
        if i == 1:
            pyautogui.write("Test diagram", interval=0.05)

        # Enter = Next (pages 1-3) or Finish (page 4)
        pyautogui.press("enter")
        time.sleep(2)
    # "Draw Graphics Mode" message (optional, wait up to 10 seconds for it)
    message = None
    for _ in range(10):
        found = gw.getWindowsWithTitle("Draw Graphics Mode")
        if found:
            message = found[0]
            break
        time.sleep(1)

    if message:
        try:
            message.activate()
        except Exception:
            pass
        time.sleep(1)
        pyautogui.press("enter")   # click OK
        time.sleep(2)

    window.activate()
    time.sleep(1)

    # Success is decided by what you see, not by the popup
    if not ask("File > Add diagram > new diagram was added?"):
        ok = False

    save_result("Add diagram", ok)
    return ok

def test_delete_diagram():
    open_file_item(2)

    dialog = gw.getActiveWindow() or window

    if not ask("File > Delete diagram > 'Select a Diagram' dialog opened correctly?"):
        try:
            dialog.activate()
            pyautogui.press("esc", presses=2, interval=0.5)
        except Exception:
            window.activate()
        save_result("Delete diagram", False)
        return

   
    # Select "Test diagram" in the dialog.
    dialog.activate()
    time.sleep(1)

    pyautogui.write("Test diagram", interval=0.05)
    time.sleep(1)
    pyautogui.press("down")
    time.sleep(1)

    # Ask permission BEFORE confirming deletion.
    if not ask("Do you want to delete 'Test diagram'?"):
        pyautogui.press("esc")
        save_result("Delete diagram", False)
        print("Deletion cancelled by user.")
        return

    # Proceed with deletion only after the user answers y.
    dialog.activate()
    time.sleep(1)
    pyautogui.press("enter")
    time.sleep(3)

    window.activate()
    time.sleep(1)

    # Verify the outcome after deletion.
    ok = ask("'Test diagram' was deleted correctly?")
    save_result("Delete diagram", ok)


# ---------------------------------------------------
# Open (user loads a network)
# ---------------------------------------------------
def test_open():
    open_file_item(3)

    ok = ask("File > Open > file dialog opened correctly?")

    if ok:
        print("\nPlease select an IPSA network file in the dialog and click Open.")
        input("When the network has finished loading, press Enter here...")

        if not ask("File > Open > network loaded correctly?"):
            ok = False
    else:
        # Dialog did not open properly, close it
        pyautogui.press("esc")
        time.sleep(1)

    window.activate()
    time.sleep(2)
    save_result("Open...", ok)


# ---------------------------------------------------
# Close (closes the loaded network)
# ---------------------------------------------------
def test_close():
    open_file_item(4)

    ok = ask("File > Close > loaded network closed correctly?")
    save_result("Close...", ok)



def test_exit():
    print("\nTEST: File > Exit")

    answer = input("Do you want to test Exit? (y/n): ").strip().lower()

    if answer != "y":
        save_result("Exit", "SKIPPED")
        return

    window.activate()
    time.sleep(1)

    # Open File > Exit
    pyautogui.press("alt")
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(0.5)
    pyautogui.press("down", presses=18, interval=0.1)
    pyautogui.press("enter")
    time.sleep(2)

    # If a save confirmation appears, choose No
    pyautogui.press("n")
    pyautogui.press("enter")
    time.sleep(3)

    # Check whether the IPSA window has closed
    if not gw.getWindowsWithTitle("IPSA 3"):
        save_result("Exit", True)
        print("IPSA closed successfully.")
    else:
        save_result("Exit", False)
        print("IPSA is still open. Check for a dialog.")



def test_recent_files():
    open_file_item(5, True)  # Open the Recent Files submenu

    # Leave the submenu open for 3 seconds so you can see it
    time.sleep(3)

    # Load the first file in the Recent Files list
    pyautogui.press("enter")
    time.sleep(5)

    window.activate()
    time.sleep(1)

    ok = ask("File > Recent Files > recent file opened and network loaded correctly?")
    save_result("Recent Files...", ok)
def reload_network():
    open_file_item(5, submenu=True)    # Recent Files
    time.sleep(2)
    pyautogui.press("enter")           # first file in the list
    time.sleep(5)
    window.activate()
    time.sleep(1)


PROJECT_INDEX = 10          # position of "Project..." in the File menu
EXPORT_DOWN = 2             # Import Project > Close Project (greyed, but selectable) > Export Project


def test_project():
    # Same file is used for export and import
    file_path = os.path.join(
        os.path.expanduser("~"), "Downloads",
        "ipsa_test_" + time.strftime("%H%M%S") + ".i3p"
    )

    # ---------- Export Project ----------
    open_file_item(PROJECT_INDEX, submenu=True)
    pyautogui.press("down", presses=EXPORT_DOWN, interval=0.3)
    time.sleep(1)
    pyautogui.press("enter")
    time.sleep(3)

    dialog = gw.getActiveWindow() or window

    if not ask("File > Project > Export Project dialog opened correctly?"):
        pyautogui.press("esc", presses=2, interval=0.5)
        save_result("Project...", False)
        return

    # Dialog 1: press "Save As..." (the default button)
    dialog.activate()
    time.sleep(1)
    pyautogui.press("enter")
    time.sleep(3)

    # Dialog 2: "Save Project file" - type the file name and save
    dialog = gw.getActiveWindow() or window
    ok = ask("File > Project > 'Save Project file' dialog opened correctly?")

    dialog.activate()
    time.sleep(1)
    pyautogui.write(file_path, interval=0.03)
    time.sleep(1)
    pyautogui.press("enter")
    time.sleep(5)

    window.activate()
    time.sleep(1)

    if not os.path.exists(file_path):
        notes.append("Project export file not found: " + file_path)
        ok = False

    if not ask("File > Project > project exported correctly?"):
        ok = False

    # ---------- Import Project ----------
    open_file_item(PROJECT_INDEX, submenu=True)
    pyautogui.press("enter")        # Import Project is the first item
    time.sleep(3)

    dialog = gw.getActiveWindow() or window

    if not ask("File > Project > Import Project dialog opened correctly?"):
        pyautogui.press("esc", presses=2, interval=0.5)
        save_result("Project...", False)
        return

    dialog.activate()
    time.sleep(1)
    pyautogui.write(file_path, interval=0.03)
    time.sleep(1)
    pyautogui.press("enter")
    time.sleep(5)

    window.activate()
    time.sleep(1)

    if not ask("File > Project > project imported correctly?"):
        ok = False

    # ---------- Close Project ----------
    open_file_item(PROJECT_INDEX, submenu=True)
    pyautogui.press("down")         # Close Project is the second item
    time.sleep(1)
    pyautogui.press("enter")
    time.sleep(3)

    window.activate()
    time.sleep(1)

    if not ask("File > Project > project closed correctly?"):
        ok = False

    # Close Project may unload the network, so load one again for the next tests
    reload_network()

    save_result("Project...", ok)

# ---------------------------------------------------
# Save (saves the loaded network, no dialog)
# ---------------------------------------------------
def test_save():
    open_file_item(6)
    time.sleep(2)

    window.activate()
    time.sleep(1)

    ok = ask("File > Save > network saved without any error?")
    save_result("Save", ok)

# ---------------------------------------------------
# Import from / Export to (test every item in the submenu)
# ---------------------------------------------------
import_items = [
    "CGMES Import",
    "GBCIM Import",
    "PowerFactory",
    "PSS/E",
    "DINIS",
    "IPSA 1.6",      # the line above it is a separator, which keyboard keys skip
    "SQL",
]

export_items = [
    "CGMES Export",
    "GBCIM Export",
]


def test_submenu(menu_name, menu_index, items):
    for position, item in enumerate(items):
        # Open File > submenu, then move down to the item
        open_file_item(menu_index, submenu=True)
        pyautogui.press("down", presses=position, interval=0.3)
        time.sleep(1)
        pyautogui.press("enter")
        time.sleep(3)

        opened = gw.getActiveWindow() or window

        ok = ask(f"{menu_name} > {item} opened correctly?")
        save_result(f"{menu_name} > {item}", ok)

        # Cancel whatever opened and return to IPSA
            # Close the dialog / menu and move on
        try:
            opened.activate()
            time.sleep(1)
            pyautogui.press("esc", presses=2, interval=0.5)
        except Exception:
            # The dialog was already closed (for example, you saved the PDF)
            window.activate()
        time.sleep(1)
# ---------------------------------------------------
# Test one File menu item
# ---------------------------------------------------
def test_file_item(name, index, submenu=False):
    open_file_item(index, submenu)

    # Remember the window that opened, so we can close it later
    opened = gw.getActiveWindow() or window

    ok = ask(f"File > {name} opened correctly?")
    save_result(name, ok)

    # Close the dialog / menu and move on
    try:
        opened.activate()
        time.sleep(1)
        pyautogui.press("esc", presses=2, interval=0.5)
    except Exception:
        # The dialog was already closed (for example, you saved the PDF)
        window.activate()
    time.sleep(1)


# ---------------------------------------------------
# File menu items: (name, number of down presses, is submenu)
# ---------------------------------------------------
file_items = [
    ("Save as...",        7,  False),
    ("Save Area as...",   8,  False),
    ("Save Region as...", 9,  False),
    ("Merge...",          11, False),
    ("mRID Generator",    14, False),
    ("NetworkManager...", 15, True),
    ("Print...",          16, False),
    ("Print to PDF...",   17, False),
]

results = {}


# # 1. Wizards and diagram items (uncomment to test them)

test_new_network()

# # 2. Load a network, then close it
test_open()
test_close()



# 3. Load a network again from Recent Files
test_recent_files()

test_project()
test_save()

# # 4. Remaining File menu items (a network is loaded again)
for name, index, submenu in file_items:
    test_file_item(name, index, submenu)


# # Add diagram, then delete it only if the add worked
if test_add_diagram():
    test_delete_diagram()
else:
    results["Delete diagram"] = "SKIPPED (Add diagram failed)"

# import from and export to are not handled because ipsa is not responding 
# test_submenu("Import from", 12, import_items) 
# test_submenu("Export to", 13, export_items)

test_exit()


# ---------------------------------------------------
# Summary
# ---------------------------------------------------
print("\n====== FILE MENU SUMMARY ======")
for name, result in results.items():
    print(f"{name:<20} {result}")

failed = [n for n, r in results.items() if r == "FAILURE"]
print("\nFailed items:", ", ".join(failed) if failed else "None")

if notes:
    print("\nWarnings:")
    for n in notes:
        print(" -", n)