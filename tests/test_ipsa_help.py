
import time
import pyautogui
import pygetwindow as gw

pyautogui.FAILSAFE = True

# Find and activate IPSA 3
windows = gw.getWindowsWithTitle("IPSA 3")

if not windows:
    print("IPSA 3 is not open!")
    raise SystemExit

window = windows[0]

if window.isMinimized:
    window.restore()

window.activate()
time.sleep(2)


def open_user_guide(index):
    # Open Help
    pyautogui.press("alt")
    time.sleep(1)

    pyautogui.press("right", presses=9, interval=0.2)
    pyautogui.press("enter")
    time.sleep(1)

    # Open User Guides
    pyautogui.press("down", presses=5, interval=0.2)
    pyautogui.press("right")
    time.sleep(1)

    # Select the requested guide
    pyautogui.press("down", presses=index, interval=0.2)
    pyautogui.press("enter")
    time.sleep(3)



# def close_window():
#     pyautogui.hotkey("alt", "f4")
#     time.sleep(2)

def close_window():
    active = gw.getActiveWindow()

    # Never close IPSA itself if the guide didn't open
    if not active or "ipsa 3" in active.title.lower():
        print("Guide window not active, nothing closed.")
        return

    if "edge" in active.title.lower():
        pyautogui.hotkey("ctrl", "w")   # close only the tab
    else:
        pyautogui.hotkey("alt", "f4")   # standalone help viewer
    time.sleep(2)

def open_technical_note():
    # Open Technical Notes folder from IPSA
    open_user_guide(4)
    time.sleep(3)

    # Activate the Technical Notes File Explorer window
    folder_windows = gw.getWindowsWithTitle("technicalnotes")

    if not folder_windows:
        print("Technical Notes folder was not found!")
        return

    folder = folder_windows[0]

    if folder.isMinimized:
        folder.restore()

    folder.activate()
    time.sleep(1)

    # Click inside the file list area (lower middle of the window)
    x = folder.left + folder.width // 2
    y = folder.top + int(folder.height * 0.6)
    pyautogui.click(x, y)
    time.sleep(0.5)

    # Select the first file and open it
    pyautogui.press("home")
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(5)

    print("Technical Notes item opened.")

    # Keep the document open for 3 seconds
    time.sleep(3)

    # Close the PDF viewer
    active = gw.getActiveWindow()

    if active and "technicalnotes" not in active.title.lower():
        if "microsoft edge" in active.title.lower():
            pyautogui.hotkey("ctrl", "w")
        else:
            active.close()
        time.sleep(1)
        print("Technical Notes item closed.")
    else:
        print("The folder is still active; the document may not have opened.")

    # Close the Explorer folder window
    for w in gw.getWindowsWithTitle("technicalnotes"):
        w.close()
    time.sleep(1)


# 1. Technical Notes
open_technical_note()
print("Accessing Technical Notes: SUCCESS")

# 2. User Manual
open_user_guide(0)
time.sleep(3)
close_window()
print("Accessing User Manual: SUCCESS")


# 3. Reference Guide
open_user_guide(1)
time.sleep(3)
close_window()
print("Accessing Reference Guide: SUCCESS")

# 4. Scripting Guide
open_user_guide(2)
time.sleep(3)   
close_window()
print("Accessing Scripting Guide: SUCCESS")

window.activate()
time.sleep(2)

print("\nAll user guide access tests completed.")


