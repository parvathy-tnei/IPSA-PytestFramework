# import ctypes
# import os
# import sys
# import time

# try:
#     ctypes.windll.shcore.SetProcessDpiAwareness(2)
# except Exception:
#     try:
#         ctypes.windll.user32.SetProcessDPIAware()
#     except Exception:
#         pass

# import pyautogui
# import pygetwindow as gw
# from pywinauto import Application, Desktop
# from PIL import ImageChops, ImageGrab

# pyautogui.FAILSAFE = True
# pyautogui.PAUSE = 0.2

# WINDOW_TIMEOUT = 15
# APP = None
# WIN = None


# def report(message):
#     print(f"[{time.strftime('%H:%M:%S')}] {message}")


# def clean(text):
#     return (
#         str(text)
#         .replace("&", "")
#         .replace("\u2026", "...")
#         .split("\t")[0]
#         .strip()
#     )


# def get_ipsa_window():
#     global APP, WIN
#     try:
#         if WIN is None:
#             APP = Application(backend="uia").connect(
#                 title_re=r".*IPSA 3.*",
#                 found_index=0,
#                 timeout=WINDOW_TIMEOUT,
#             )
#             main = APP.window(title_re=r".*IPSA 3.*", found_index=0)
#             WIN = APP.window(handle=main.wrapper_object().handle)
#         WIN.set_focus()
#         return APP, WIN
#     except Exception as error:
#         report(f"ERROR: Could not connect to IPSA 3: {error}")
#         return None, None


# def open_file_item(index):
#     _, win = get_ipsa_window()
#     if win is None:
#         return
#     win.set_focus()
#     time.sleep(0.2)
#     pyautogui.hotkey("alt", "f")
#     time.sleep(0.3)
#     for _ in range(index):
#         pyautogui.press("down")
#         time.sleep(0.05)
#     pyautogui.press("enter")
#     time.sleep(0.5)


# def wait_for_new_window(before_handles, timeout=4):
#     deadline = time.time() + timeout
#     while time.time() < deadline:
#         current_windows = gw.getAllWindows()
#         for w in current_windows:
#             if w._hWnd not in before_handles and w.title.strip():
#                 return w
#         time.sleep(0.2)
#     return None


# def create_new_network_wizard():
#     report("Creating New Network...")
#     before_handles = {w._hWnd for w in gw.getAllWindows()}
#     open_file_item(0)

#     wizard = wait_for_new_window(before_handles, timeout=4) or gw.getActiveWindow()
#     title = wizard.title.strip().lower() if wizard else ""

#     if wizard and ("new network" in title or "wizard" in title or wizard._hWnd not in before_handles):
#         wizard.activate()
#         time.sleep(0.4)
#         pyautogui.press("enter")
#         time.sleep(0.4)
#         pyautogui.press("enter")
#         time.sleep(0.4)
#         pyautogui.press("enter")
#         time.sleep(1.0)
#         report("New network wizard completed.")
#         return True
#     else:
#         report("Wizard dialog did not appear.")
#         pyautogui.press("esc")
#         return False


# def dismiss_any_dialog():
#     time.sleep(0.3)
#     try:
#         for w in Desktop(backend="uia").windows(process=APP.process):
#             title = w.window_text().strip().casefold()
#             if any(k in title for k in ("data", "parameters", "edit", "component", "bus", "line", "filter", "breaker", "protection", "machine", "converter", "convertor", "capacitor", "svc", "branch", "load", "equivalent")):
#                 for b in w.descendants(control_type="Button"):
#                     if clean(b.window_text()).casefold() in ("ok", "&ok", "done", "apply", "close"):
#                         b.click_input()
#                         time.sleep(0.2)
#                         return
#                 pyautogui.press("enter")
#     except Exception:
#         pass


# def did_canvas_change(box_before, bbox, min_pixel_threshold=35):
#     time.sleep(0.4)
#     box_after = ImageGrab.grab(bbox=bbox)
#     diff = ImageChops.difference(box_before, box_after)
#     stat = diff.getbbox()
#     if stat is None:
#         return False
#     changed_area = (stat[2] - stat[0]) * (stat[3] - stat[1])
#     return changed_area >= min_pixel_threshold


# def clear_canvas_all(canvas_x, canvas_y):
#     pyautogui.click(canvas_x, canvas_y)
#     time.sleep(0.15)
#     pyautogui.hotkey("ctrl", "a")
#     time.sleep(0.15)
#     pyautogui.press("delete")
#     time.sleep(0.2)
#     try:
#         for w in Desktop(backend="uia").windows(process=APP.process):
#             title = w.window_text().strip().casefold()
#             if any(k in title for k in ("delete", "confirm", "warning")):
#                 for b in w.descendants(control_type="Button"):
#                     if clean(b.window_text()).casefold() in ("yes", "ok", "&yes", "&ok"):
#                         b.click_input()
#                         break
#                 break
#     except Exception:
#         pass
#     time.sleep(0.2)


# def select_vertical_busbar(arrow_x, arrow_y):
#     pyautogui.click(arrow_x, arrow_y)
#     time.sleep(0.4)

#     menu_clicked = False
#     for w in Desktop(backend="uia").windows():
#         try:
#             if w.element_info.control_type == "Menu" or "menu" in w.element_info.class_name.lower():
#                 r = w.rectangle()
#                 item2_x = r.left + int(r.width() * 0.45)
#                 item2_y = r.top + 40
#                 pyautogui.moveTo(item2_x, item2_y, duration=0.1)
#                 pyautogui.click()
#                 menu_clicked = True
#                 break
#         except Exception:
#             continue

#     if not menu_clicked:
#         menu_x = arrow_x - 75
#         menu_y = arrow_y + 40
#         pyautogui.moveTo(menu_x, menu_y, duration=0.15)
#         pyautogui.click()

#     time.sleep(0.3)


# def test_components():
#     _, win = get_ipsa_window()
#     if win is None:
#         return

#     if not create_new_network_wizard():
#         report("Failed to create network.")
#         return

#     win.set_focus()
#     time.sleep(0.5)

#     wr = win.rectangle()

#     # Dynamic Canvas Positions
#     bus1_x = wr.left + int(wr.width() * 0.35)
#     bus1_y = wr.top + int(wr.height() * 0.45)

#     bus2_x = wr.left + int(wr.width() * 0.60)
#     bus2_y = bus1_y

#     neutral_x = wr.left + int(wr.width() * 0.15)
#     neutral_y = wr.top + int(wr.height() * 0.20)

#     # Right Toolbar Coordinates
#     tb_btn_x = wr.right - 22
#     tb_arrow_x = wr.right - 8
#     base_y = wr.top + 130

#     # Upper Group (Slots 0 to 15)[cite: 16]
#     busbar_btn_y      = base_y
#     gen_btn_y         = base_y + 36    # Slot 1: Generator (~)[cite: 16]
#     grid_btn_y        = base_y + 72    # Slot 2: Grid Infeed (mesh)[cite: 16]
#     load_btn_y        = base_y + 112   # Slot 3: Load (arrow)[cite: 16]
#     motor_btn_y       = base_y + 152   # Slot 4: Induction Motor (M)[cite: 16]
#     shunt_btn_y       = base_y + 192   # Slot 5: Shunt (ground)[cite: 16]
#     line_btn_y        = base_y + 232   # Slot 6: Line / Branch[cite: 16]
#     xfmr_btn_y        = base_y + 270   # Slot 7: Transformer (2-W)[cite: 16]
#     harm_source_btn_y = base_y + 308   # Slot 8: Harmonic Source (H)[cite: 16]
#     harm_filter_btn_y = base_y + 346   # Slot 9: Harmonic Filter (F)[cite: 16]
#     cb_btn_y          = base_y + 396   # Slot 10: Circuit Breaker (square)[cite: 16]
#     prot_btn_y        = base_y + 440   # Slot 11: Protection Container (P)[cite: 16]
#     univ_mach_btn_y   = base_y + 538   # Slot 13: Universal Machine (U)[cite: 16]
#     svc_btn_y         = base_y + 574   # Slot 14: Static VAr Compensator[cite: 16]
#     msc_btn_y         = base_y + 610   # Slot 15: Mechanically Switched Capacitor[cite: 16]

#     # Bottom Group anchored directly from bottom of window (works on laptop & monitor)[cite: 20]
#     acdc_btn_y        = wr.bottom - 225  # Slot 16: AC-DC Convertor (slash box)[cite: 20]
#     unbal_load_btn_y  = wr.bottom - 150  # Slot 17: Unbalanced Load (3 down arrows)[cite: 20]
#     equiv_br_btn_y    = wr.bottom - 75   # Slot 18: Equivalent Branch (diamond 'E')[cite: 20]

#     results = {}

#     clear_canvas_all(neutral_x, neutral_y)

#     # -------------------------------------------------------------
#     # 1. Place Vertical Busbars[cite: 18]
#     # -------------------------------------------------------------
#     report("Selecting 'Draw Vertical Busbar' from dropdown...")
#     select_vertical_busbar(tb_arrow_x, busbar_btn_y)

#     report("Placing Vertical Busbar 1...")
#     watch_bus1 = (bus1_x - 50, bus1_y - 60, bus1_x + 50, bus1_y + 60)
#     before_bus1 = ImageGrab.grab(bbox=watch_bus1)

#     pyautogui.click(bus1_x, bus1_y)
#     time.sleep(0.3)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.2)
#     results["Busbar 1"] = "PASS" if did_canvas_change(before_bus1, watch_bus1) else "FAIL"

#     report("Placing Vertical Busbar 2...")
#     watch_bus2 = (bus2_x - 50, bus2_y - 60, bus2_x + 50, bus2_y + 60)
#     before_bus2 = ImageGrab.grab(bbox=watch_bus2)

#     pyautogui.click(tb_btn_x, busbar_btn_y)
#     time.sleep(0.2)
#     pyautogui.click(bus2_x, bus2_y)
#     time.sleep(0.3)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.2)
#     results["Busbar 2"] = "PASS" if did_canvas_change(before_bus2, watch_bus2) else "FAIL"

#     if results["Busbar 1"] == "FAIL" or results["Busbar 2"] == "FAIL":
#         report("Busbars failed to place. Halting tests.")
#         return

#     # -------------------------------------------------------------
#     # 2. Generator[cite: 18]
#     # -------------------------------------------------------------
#     report("Testing Generator on Busbar 1...")
#     gen_x = bus1_x - 130
#     gen_y = bus1_y
#     watch_gen = (gen_x - 50, gen_y - 50, bus1_x + 30, gen_y + 50)
#     before_gen = ImageGrab.grab(bbox=watch_gen)

#     pyautogui.click(tb_btn_x, gen_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(bus1_x, bus1_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.3)
#     pyautogui.moveTo(gen_x, gen_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Generator"] = "PASS" if did_canvas_change(before_gen, watch_gen) else "FAIL"

#     # -------------------------------------------------------------
#     # 3. Grid Infeed[cite: 18]
#     # -------------------------------------------------------------
#     report("Testing Grid Infeed on Busbar 1...")
#     grid_x = bus1_x
#     grid_y = bus1_y - 110
#     watch_grid = (grid_x - 50, grid_y - 50, grid_x + 50, bus1_y + 30)
#     before_grid = ImageGrab.grab(bbox=watch_grid)

#     pyautogui.click(tb_btn_x, grid_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(bus1_x, bus1_y - 20, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.3)
#     pyautogui.moveTo(grid_x, grid_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Grid Infeed"] = "PASS" if did_canvas_change(before_grid, watch_grid) else "FAIL"

#     # -------------------------------------------------------------
#     # 4. Load[cite: 18]
#     # -------------------------------------------------------------
#     report("Testing Load on Busbar 2...")
#     load_x = bus2_x + 110
#     load_y = bus2_y
#     watch_load = (bus2_x - 30, load_y - 50, load_x + 50, load_y + 50)
#     before_load = ImageGrab.grab(bbox=watch_load)

#     pyautogui.click(tb_btn_x, load_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(bus2_x, bus2_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.3)
#     pyautogui.moveTo(load_x, load_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Load"] = "PASS" if did_canvas_change(before_load, watch_load) else "FAIL"

#     # -------------------------------------------------------------
#     # 5. Induction Motor[cite: 18]
#     # -------------------------------------------------------------
#     report("Testing Induction Motor on Busbar 2...")
#     motor_x = bus2_x
#     motor_y = bus2_y - 110
#     watch_motor = (motor_x - 50, motor_y - 50, motor_x + 50, bus2_y + 20)
#     before_motor = ImageGrab.grab(bbox=watch_motor)

#     pyautogui.click(tb_btn_x, motor_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(bus2_x, bus2_y - 20, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.3)
#     pyautogui.moveTo(motor_x, motor_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Induction Motor"] = "PASS" if did_canvas_change(before_motor, watch_motor) else "FAIL"

#     # -------------------------------------------------------------
#     # 6. Shunt[cite: 18]
#     # -------------------------------------------------------------
#     report("Testing Shunt on Busbar 1...")
#     shunt_x = bus1_x
#     shunt_y = bus1_y + 110
#     watch_shunt = (shunt_x - 50, bus1_y - 20, shunt_x + 50, shunt_y + 50)
#     before_shunt = ImageGrab.grab(bbox=watch_shunt)

#     pyautogui.click(tb_btn_x, shunt_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(bus1_x, bus1_y + 20, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.3)
#     pyautogui.moveTo(shunt_x, shunt_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Shunt"] = "PASS" if did_canvas_change(before_shunt, watch_shunt) else "FAIL"

#     # -------------------------------------------------------------
#     # 7. Line / Branch[cite: 18]
#     # -------------------------------------------------------------
#     report("Testing Line / Branch...")
#     line_y = bus1_y - 16
#     watch_line = (bus1_x + 15, line_y - 20, bus2_x - 15, line_y + 20)
#     before_line = ImageGrab.grab(bbox=watch_line)

#     pyautogui.click(tb_btn_x, line_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(bus1_x, line_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.3)
#     pyautogui.moveTo(bus2_x, line_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Line / Branch"] = "PASS" if did_canvas_change(before_line, watch_line) else "FAIL"

#     # -------------------------------------------------------------
#     # 8. Transformer (2-W)[cite: 18]
#     # -------------------------------------------------------------
#     report("Testing Transformer (2-W)...")
#     xfmr_y = bus1_y + 6
#     watch_xfmr = (bus1_x + 15, xfmr_y - 15, bus2_x - 15, xfmr_y + 25)
#     before_xfmr = ImageGrab.grab(bbox=watch_xfmr)

#     pyautogui.click(tb_btn_x, xfmr_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(bus1_x, xfmr_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.3)
#     pyautogui.moveTo(bus2_x, xfmr_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Transformer (2-W)"] = "PASS" if did_canvas_change(before_xfmr, watch_xfmr) else "FAIL"

#     # -------------------------------------------------------------
#     # 9. Harmonic Source[cite: 18]
#     # -------------------------------------------------------------
#     report("Testing Harmonic Source...")
#     harm_src_x = bus1_x - 70
#     harm_src_y = bus1_y - 50
#     watch_h_src = (harm_src_x - 45, harm_src_y - 45, bus1_x + 25, harm_src_y + 45)
#     before_h_src = ImageGrab.grab(bbox=watch_h_src)

#     pyautogui.click(tb_btn_x, harm_source_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(bus1_x, bus1_y - 10, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.3)
#     pyautogui.moveTo(harm_src_x, harm_src_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Harmonic Source"] = "PASS" if did_canvas_change(before_h_src, watch_h_src) else "FAIL"

#     # -------------------------------------------------------------
#     # 10. Harmonic Filter[cite: 18]
#     # -------------------------------------------------------------
#     report("Testing Harmonic Filter...")
#     harm_flt_x = bus2_x
#     harm_flt_y = bus2_y + 110
#     watch_h_flt = (harm_flt_x - 45, bus2_y - 20, harm_flt_x + 45, harm_flt_y + 45)
#     before_h_flt = ImageGrab.grab(bbox=watch_h_flt)

#     pyautogui.click(tb_btn_x, harm_filter_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(bus2_x, bus2_y + 20, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.3)
#     pyautogui.moveTo(harm_flt_x, harm_flt_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Harmonic Filter"] = "PASS" if did_canvas_change(before_h_flt, watch_h_flt) else "FAIL"

#     # -------------------------------------------------------------
#     # 11. Circuit Breaker[cite: 18]
#     # -------------------------------------------------------------
#     cb_x = bus1_x + int((bus2_x - bus1_x) * 0.30)
#     cb_y = line_y
#     report(f"Testing Circuit Breaker on Line at ({cb_x}, {cb_y})...")

#     watch_cb = (cb_x - 20, cb_y - 20, cb_x + 20, cb_y + 20)
#     before_cb = ImageGrab.grab(bbox=watch_cb)

#     pyautogui.click(tb_btn_x, cb_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(cb_x, cb_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Circuit Breaker"] = "PASS" if did_canvas_change(before_cb, watch_cb) else "FAIL"

#     # -------------------------------------------------------------
#     # 12. Protection Container[cite: 18]
#     # -------------------------------------------------------------
#     prot_x = bus1_x + int((bus2_x - bus1_x) * 0.70)
#     prot_y = line_y
#     report(f"Testing Protection Container on Line at ({prot_x}, {prot_y})...")

#     watch_prot = (prot_x - 25, prot_y - 25, prot_x + 25, prot_y + 25)
#     before_prot = ImageGrab.grab(bbox=watch_prot)

#     pyautogui.click(tb_btn_x, prot_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(prot_x, prot_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Protection Container"] = "PASS" if did_canvas_change(before_prot, watch_prot) else "FAIL"

#     # -------------------------------------------------------------
#     # 13. Universal Machine (U)[cite: 18]
#     # -------------------------------------------------------------
#     report("Testing Universal Machine (U)...")
#     um_x = bus1_x - 130
#     um_y = bus1_y - 60
#     watch_um = (um_x - 45, um_y - 45, bus1_x + 20, um_y + 45)
#     before_um = ImageGrab.grab(bbox=watch_um)

#     pyautogui.click(tb_btn_x, univ_mach_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(bus1_x, bus1_y - 10, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.3)
#     pyautogui.moveTo(um_x, um_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Universal Machine"] = "PASS" if did_canvas_change(before_um, watch_um) else "FAIL"

#     # -------------------------------------------------------------
#     # 14. Static VAr Compensator (SVC)[cite: 18]
#     # -------------------------------------------------------------
#     report("Testing Static VAr Compensator (SVC)...")
#     svc_x = bus1_x - 130
#     svc_y = bus1_y + 60
#     watch_svc = (svc_x - 45, svc_y - 45, bus1_x + 20, svc_y + 45)
#     before_svc = ImageGrab.grab(bbox=watch_svc)

#     pyautogui.click(tb_btn_x, svc_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(bus1_x, bus1_y + 10, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.3)
#     pyautogui.moveTo(svc_x, svc_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Static VAr Compensator"] = "PASS" if did_canvas_change(before_svc, watch_svc) else "FAIL"

#     # -------------------------------------------------------------
#     # 15. Mechanically Switched Capacitor (MSC)[cite: 18]
#     # -------------------------------------------------------------
#     report("Testing Mechanically Switched Capacitor (MSC)...")
#     msc_x = bus2_x + 110
#     msc_y = bus2_y - 60
#     watch_msc = (bus2_x - 20, msc_y - 45, msc_x + 45, msc_y + 45)
#     before_msc = ImageGrab.grab(bbox=watch_msc)

#     pyautogui.click(tb_btn_x, msc_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(bus2_x, bus2_y - 10, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.3)
#     pyautogui.moveTo(msc_x, msc_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Mechanically Switched Capacitor"] = "PASS" if did_canvas_change(before_msc, watch_msc) else "FAIL"

#     # -------------------------------------------------------------
#     # 16. AC-DC Convertor (Busbar 1 -> Busbar 2)[cite: 16]
#     # -------------------------------------------------------------
#     report("Testing AC-DC Convertor (Busbar 1 -> Busbar 2)...")
#     acdc_y = bus1_y - 8
#     watch_acdc = (bus1_x + 15, acdc_y - 14, bus2_x - 15, acdc_y + 14)
#     before_acdc = ImageGrab.grab(bbox=watch_acdc)

#     pyautogui.click(tb_btn_x, acdc_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(bus1_x, acdc_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.3)
#     pyautogui.moveTo(bus2_x, acdc_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["AC-DC Convertor"] = "PASS" if did_canvas_change(before_acdc, watch_acdc) else "FAIL"

#     # -------------------------------------------------------------
#     # 17. Unbalanced Load (Connect to Busbar 2)[cite: 17]
#     # -------------------------------------------------------------
#     report("Testing Unbalanced Load (Busbar 2 -> Right)...")
#     unbal_x = bus2_x + 110
#     unbal_y = bus2_y + 45
#     watch_unbal = (bus2_x - 20, unbal_y - 45, unbal_x + 50, unbal_y + 45)
#     before_unbal = ImageGrab.grab(bbox=watch_unbal)

#     pyautogui.click(tb_btn_x, unbal_load_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(bus2_x, bus2_y + 12, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.3)
#     pyautogui.moveTo(unbal_x, unbal_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Unbalanced Load"] = "PASS" if did_canvas_change(before_unbal, watch_unbal) else "FAIL"

#     # -------------------------------------------------------------
#     # 18. Equivalent Branch (Connect Busbar 1 to Busbar 2)[cite: 16]
#     # -------------------------------------------------------------
#     report("Testing Equivalent Branch (Busbar 1 -> Busbar 2)...")
#     equiv_y = bus1_y + 24
#     watch_equiv = (bus1_x + 15, equiv_y - 12, bus2_x - 15, equiv_y + 20)
#     before_equiv = ImageGrab.grab(bbox=watch_equiv)

#     pyautogui.click(tb_btn_x, equiv_br_btn_y)
#     time.sleep(0.3)
#     pyautogui.moveTo(bus1_x, equiv_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.3)
#     pyautogui.moveTo(bus2_x, equiv_y, duration=0.15)
#     pyautogui.click()
#     time.sleep(0.4)
#     dismiss_any_dialog()
#     pyautogui.press("esc", presses=2, interval=0.1)
#     pyautogui.click(neutral_x, neutral_y)
#     time.sleep(0.3)
#     results["Equivalent Branch"] = "PASS" if did_canvas_change(before_equiv, watch_equiv) else "FAIL"

#     # -------------------------------------------------------------
#     # Final Output
#     # -------------------------------------------------------------
#     print("\n" + "=" * 45)
#     print("           COMPONENT TEST RESULTS           ")
#     print("=" * 45)
#     for comp, status in results.items():
#         print(f"{comp:35} : {status}")
#     print("=" * 45)


# def main():
#     _, win = get_ipsa_window()
#     if win is None:
#         report("IPSA 3 window not found.")
#         sys.exit(1)

#     try:
#         if win.get_show_state() == 2:
#             win.restore()
#         win.maximize()
#     except Exception:
#         pass

#     test_components()


# if __name__ == "__main__":
#     main()
import ctypes
from ctypes import wintypes
import os
import sys
import time

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
from pywinauto import Application, Desktop
from PIL import ImageChops, ImageGrab

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2

WINDOW_TIMEOUT = 15
APP = None
WIN = None

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
POSSIBLE_ICON_DIRS = [
    os.path.join(CURRENT_DIR, "tests", "icons"),
    os.path.join(CURRENT_DIR, "icons"),
    os.path.join(os.path.dirname(CURRENT_DIR), "tests", "icons"),
    os.path.join(os.path.dirname(CURRENT_DIR), "icons"),
]

ICON_DIR = CURRENT_DIR
for p in POSSIBLE_ICON_DIRS:
    if os.path.exists(p):
        ICON_DIR = p
        break


def report(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}")


def clean(text):
    return (
        str(text)
        .replace("&", "")
        .replace("\u2026", "...")
        .split("\t")[0]
        .strip()
    )


def show_preflight_disclaimer(countdown_seconds=7):
    disclaimer = """
======================================================================
                         IMPORTANT DISCLAIMER                         
======================================================================
  1. Please ensure a FRESH IPSA 3 session is launched before starting.
  2. For the most accurate coordinate calibration, run this on a 
     standard laptop display (maximized).
  3. HANDS OFF: Do NOT move your mouse, click, or type on your keyboard 
     while the automated test is executing.
======================================================================
"""
    print(disclaimer)
    print("Starting tests in:")
    for remaining in range(countdown_seconds, 0, -1):
        print(f"  --> {remaining} seconds... (Press Ctrl+C to cancel)", end="\r", flush=True)
        time.sleep(1)
    # print("\n\nLaunching component placement suite now...\n")


def get_ipsa_window():
    global APP, WIN
    try:
        if WIN is None:
            APP = Application(backend="uia").connect(
                title_re=r".*IPSA 3.*",
                found_index=0,
                timeout=WINDOW_TIMEOUT,
            )
            main = APP.window(title_re=r".*IPSA 3.*", found_index=0)
            WIN = APP.window(handle=main.wrapper_object().handle)
        WIN.set_focus()
        return APP, WIN
    except Exception as error:
        report(f"ERROR: Could not connect to IPSA 3: {error}")
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


def wait_for_new_window(before_handles, timeout=4):
    deadline = time.time() + timeout
    while time.time() < deadline:
        current_windows = gw.getAllWindows()
        for w in current_windows:
            if w._hWnd not in before_handles and w.title.strip():
                return w
        time.sleep(0.2)
    return None


def create_new_network_wizard():
    # report("Creating New Network...")
    before_handles = {w._hWnd for w in gw.getAllWindows()}
    open_file_item(0)

    wizard = wait_for_new_window(before_handles, timeout=4) or gw.getActiveWindow()
    title = wizard.title.strip().lower() if wizard else ""

    if wizard and ("new network" in title or "wizard" in title or wizard._hWnd not in before_handles):
        wizard.activate()
        time.sleep(0.4)
        pyautogui.press("enter")
        time.sleep(0.4)
        pyautogui.press("enter")
        time.sleep(0.4)
        pyautogui.press("enter")
        time.sleep(1.0)
        # report("New network wizard completed.")
        return True
    else:
        report("Wizard dialog did not appear.")
        pyautogui.press("esc")
        return False


def dismiss_any_dialog():
    time.sleep(0.3)
    try:
        for w in Desktop(backend="uia").windows(process=APP.process):
            title = w.window_text().strip().casefold()
            dialog_keywords = (
                "data", "parameters", "edit", "component", "bus", "line",
                "filter", "breaker", "protection", "machine", "converter",
                "convertor", "capacitor", "svc", "branch", "load", "equivalent"
            )
            if any(k in title for k in dialog_keywords):
                for b in w.descendants(control_type="Button"):
                    if clean(b.window_text()).casefold() in ("ok", "&ok", "done", "apply", "close"):
                        b.click_input()
                        time.sleep(0.2)
                        return
                pyautogui.press("enter")
    except Exception:
        pass


def did_canvas_change(box_before, bbox, min_pixel_threshold=35):
    time.sleep(0.4)
    box_after = ImageGrab.grab(bbox=bbox)
    diff = ImageChops.difference(box_before, box_after)
    stat = diff.getbbox()
    if stat is None:
        return False
    changed_area = (stat[2] - stat[0]) * (stat[3] - stat[1])
    return changed_area >= min_pixel_threshold


def clear_canvas_all(canvas_x, canvas_y):
    pyautogui.click(canvas_x, canvas_y)
    time.sleep(0.15)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.15)
    pyautogui.press("delete")
    time.sleep(0.2)
    try:
        for w in Desktop(backend="uia").windows(process=APP.process):
            title = w.window_text().strip().casefold()
            if any(k in title for k in ("delete", "confirm", "warning")):
                for b in w.descendants(control_type="Button"):
                    if clean(b.window_text()).casefold() in ("yes", "ok", "&yes", "&ok"):
                        b.click_input()
                        break
                break
    except Exception:
        pass
    time.sleep(0.2)


def click_icon(icon_name, win=None, search_bbox=None, fallback_y=None, threshold=0.60):
    if win is None:
        _, win = get_ipsa_window()
        if win is None:
            return False

    win.set_focus()
    wr = win.rectangle()
    tb_btn_x = wr.right - 22

    if search_bbox is None:
        search_bbox = (wr.right - 90, wr.top + 90, wr.right - 5, wr.bottom - 5)

    template_file = os.path.join(ICON_DIR, f"{icon_name}.png")

    if os.path.exists(template_file):
        template = cv2.imread(template_file, cv2.IMREAD_GRAYSCALE)
        if template is not None:
            screen_crop = ImageGrab.grab(bbox=search_bbox)
            screen_gray = cv2.cvtColor(np.array(screen_crop), cv2.COLOR_RGB2GRAY)

            best_val = -1
            best_loc = None
            best_scale = 1.0

            for scale in [1.0, 0.8, 1.25, 0.75, 1.5]:
                scaled_w = int(template.shape[1] * scale)
                scaled_h = int(template.shape[0] * scale)
                if (
                    scaled_w >= screen_gray.shape[1]
                    or scaled_h >= screen_gray.shape[0]
                    or scaled_w < 5
                    or scaled_h < 5
                ):
                    continue

                resized = (
                    cv2.resize(template, (scaled_w, scaled_h), interpolation=cv2.INTER_AREA)
                    if scale != 1.0
                    else template
                )
                res = cv2.matchTemplate(screen_gray, resized, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)

                if max_val > best_val:
                    best_val = max_val
                    best_loc = max_loc
                    best_scale = scale

            if best_val >= threshold:
                tw = int(template.shape[1] * best_scale)
                th = int(template.shape[0] * best_scale)
                click_x = search_bbox[0] + best_loc[0] + tw // 2
                click_y = search_bbox[1] + best_loc[1] + th // 2

                if wr.left < click_x < wr.right and wr.top < click_y < wr.bottom:
                    # report(f"Found '{icon_name}' (conf: {best_val:.2f}) -> clicking ({click_x}, {click_y})")
                    pyautogui.moveTo(click_x, click_y, duration=0.12)
                    pyautogui.click()
                    time.sleep(0.2)
                    return True

    if fallback_y is not None:
        # report(f"Template '{icon_name}' below threshold -> fallback toolbar Y={fallback_y}")
        pyautogui.moveTo(tb_btn_x, fallback_y, duration=0.12)
        pyautogui.click()
        time.sleep(0.2)
        return True

    return False


def select_vertical_busbar(arrow_x, arrow_y, win=None):
    pyautogui.click(arrow_x, arrow_y)
    time.sleep(0.3)

    if win is not None:
        wr = win.rectangle()
        menu_search_box = (wr.right - 350, wr.top + 100, wr.right - 20, wr.top + 320)
        if click_icon("busbar_vertical", win=win, search_bbox=menu_search_box, threshold=0.65):
            time.sleep(0.3)
            return

    menu_clicked = False
    for w in Desktop(backend="uia").windows():
        try:
            if w.element_info.control_type == "Menu" or "menu" in w.element_info.class_name.lower():
                r = w.rectangle()
                item2_x = r.left + int(r.width() * 0.45)
                item2_y = r.top + 40
                pyautogui.moveTo(item2_x, item2_y, duration=0.1)
                pyautogui.click()
                menu_clicked = True
                break
        except Exception:
            continue

    if not menu_clicked:
        menu_x = arrow_x - 75
        menu_y = arrow_y + 40
        pyautogui.moveTo(menu_x, menu_y, duration=0.15)
        pyautogui.click()

    time.sleep(0.3)


def test_components():
    _, win = get_ipsa_window()
    if win is None:
        return

    if not create_new_network_wizard():
        report("Failed to create network.")
        return

    win.set_focus()
    time.sleep(0.5)

    wr = win.rectangle()

    # Dynamic Canvas Positions
    bus1_x = wr.left + int(wr.width() * 0.35)
    bus1_y = wr.top + int(wr.height() * 0.45)

    bus2_x = wr.left + int(wr.width() * 0.60)
    bus2_y = bus1_y

    neutral_x = wr.left + int(wr.width() * 0.15)
    neutral_y = wr.top + int(wr.height() * 0.20)

    # Right Toolbar Reference Coordinates
    tb_btn_x = wr.right - 22
    tb_arrow_x = wr.right - 8
    base_y = wr.top + 130

    busbar_btn_y      = base_y
    gen_btn_y         = base_y + 36
    grid_btn_y        = base_y + 72
    load_btn_y        = base_y + 112
    motor_btn_y       = base_y + 152
    shunt_btn_y       = base_y + 192
    line_btn_y        = base_y + 232
    xfmr_btn_y        = base_y + 270
    harm_source_btn_y = base_y + 308
    harm_filter_btn_y = base_y + 346
    cb_btn_y          = base_y + 396
    prot_btn_y        = base_y + 440
    univ_mach_btn_y   = base_y + 538
    svc_btn_y         = base_y + 574
    msc_btn_y         = base_y + 610

    acdc_btn_y        = wr.bottom - 225
    unbal_load_btn_y  = wr.bottom - 150
    equiv_br_btn_y    = wr.bottom - 75

    results = {}

    clear_canvas_all(neutral_x, neutral_y)

    # -------------------------------------------------------------
    # 1. Place Vertical Busbars
    # -------------------------------------------------------------
    # report("Selecting 'Draw Vertical Busbar' from dropdown...")
    select_vertical_busbar(tb_arrow_x, busbar_btn_y, win=win)

    # report("Placing Vertical Busbar 1...")
    watch_bus1 = (bus1_x - 50, bus1_y - 60, bus1_x + 50, bus1_y + 60)
    before_bus1 = ImageGrab.grab(bbox=watch_bus1)

    pyautogui.click(bus1_x, bus1_y)
    time.sleep(0.3)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.2)
    results["Busbar 1"] = "PASS" if did_canvas_change(before_bus1, watch_bus1) else "FAIL"

    # report("Placing Vertical Busbar 2...")
    watch_bus2 = (bus2_x - 50, bus2_y - 60, bus2_x + 50, bus2_y + 60)
    before_bus2 = ImageGrab.grab(bbox=watch_bus2)

    click_icon("busbar", win=win, fallback_y=busbar_btn_y)
    time.sleep(0.2)
    pyautogui.click(bus2_x, bus2_y)
    time.sleep(0.3)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.2)
    results["Busbar 2"] = "PASS" if did_canvas_change(before_bus2, watch_bus2) else "FAIL"

    if results["Busbar 1"] == "FAIL" or results["Busbar 2"] == "FAIL":
        report("Busbars failed to place. Halting tests.")
        return

    # -------------------------------------------------------------
    # 2. Generator
    # -------------------------------------------------------------
    # report("Testing Generator on Busbar 1...")
    gen_x = bus1_x - 130
    gen_y = bus1_y
    watch_gen = (gen_x - 50, gen_y - 50, bus1_x + 30, gen_y + 50)
    before_gen = ImageGrab.grab(bbox=watch_gen)

    click_icon("generator", win=win, fallback_y=gen_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(bus1_x, bus1_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.moveTo(gen_x, gen_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Generator"] = "PASS" if did_canvas_change(before_gen, watch_gen) else "FAIL"

    # -------------------------------------------------------------
    # 3. Grid Infeed
    # -------------------------------------------------------------
    # report("Testing Grid Infeed on Busbar 1...")
    grid_x = bus1_x
    grid_y = bus1_y - 110
    watch_grid = (grid_x - 50, grid_y - 50, grid_x + 50, bus1_y + 30)
    before_grid = ImageGrab.grab(bbox=watch_grid)

    click_icon("grid_infeed", win=win, fallback_y=grid_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(bus1_x, bus1_y - 20, duration=0.15)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.moveTo(grid_x, grid_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Grid Infeed"] = "PASS" if did_canvas_change(before_grid, watch_grid) else "FAIL"

    # -------------------------------------------------------------
    # 4. Load
    # -------------------------------------------------------------
    # report("Testing Load on Busbar 2...")
    load_x = bus2_x + 110
    load_y = bus2_y
    watch_load = (bus2_x - 30, load_y - 50, load_x + 50, load_y + 50)
    before_load = ImageGrab.grab(bbox=watch_load)

    click_icon("load", win=win, fallback_y=load_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(bus2_x, bus2_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.moveTo(load_x, load_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Load"] = "PASS" if did_canvas_change(before_load, watch_load) else "FAIL"

    # -------------------------------------------------------------
    # 5. Induction Motor
    # -------------------------------------------------------------
    # report("Testing Induction Motor on Busbar 2...")
    motor_x = bus2_x
    motor_y = bus2_y - 110
    watch_motor = (motor_x - 50, motor_y - 50, motor_x + 50, bus2_y + 20)
    before_motor = ImageGrab.grab(bbox=watch_motor)

    click_icon("motor", win=win, fallback_y=motor_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(bus2_x, bus2_y - 20, duration=0.15)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.moveTo(motor_x, motor_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Induction Motor"] = "PASS" if did_canvas_change(before_motor, watch_motor) else "FAIL"

    # -------------------------------------------------------------
    # 6. Shunt
    # -------------------------------------------------------------
    # report("Testing Shunt on Busbar 1...")
    shunt_x = bus1_x
    shunt_y = bus1_y + 110
    watch_shunt = (shunt_x - 50, bus1_y - 20, shunt_x + 50, shunt_y + 50)
    before_shunt = ImageGrab.grab(bbox=watch_shunt)

    click_icon("shunt", win=win, fallback_y=shunt_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(bus1_x, bus1_y + 20, duration=0.15)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.moveTo(shunt_x, shunt_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Shunt"] = "PASS" if did_canvas_change(before_shunt, watch_shunt) else "FAIL"

    # -------------------------------------------------------------
    # 7. Line / Branch
    # -------------------------------------------------------------
    # report("Testing Line / Branch...")
    line_y = bus1_y - 16
    watch_line = (bus1_x + 15, line_y - 20, bus2_x - 15, line_y + 20)
    before_line = ImageGrab.grab(bbox=watch_line)

    click_icon("line", win=win, fallback_y=line_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(bus1_x, line_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.moveTo(bus2_x, line_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Line / Branch"] = "PASS" if did_canvas_change(before_line, watch_line) else "FAIL"

    # -------------------------------------------------------------
    # 8. Transformer (2-W)
    # -------------------------------------------------------------
    # report("Testing Transformer (2-W)...")
    xfmr_y = bus1_y + 6
    watch_xfmr = (bus1_x + 15, xfmr_y - 15, bus2_x - 15, xfmr_y + 25)
    before_xfmr = ImageGrab.grab(bbox=watch_xfmr)

    click_icon("transformer", win=win, fallback_y=xfmr_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(bus1_x, xfmr_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.moveTo(bus2_x, xfmr_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Transformer (2-W)"] = "PASS" if did_canvas_change(before_xfmr, watch_xfmr) else "FAIL"

    # -------------------------------------------------------------
    # 9. Harmonic Source
    # -------------------------------------------------------------
    # report("Testing Harmonic Source...")
    harm_src_x = bus1_x - 70
    harm_src_y = bus1_y - 50
    watch_h_src = (harm_src_x - 45, harm_src_y - 45, bus1_x + 25, harm_src_y + 45)
    before_h_src = ImageGrab.grab(bbox=watch_h_src)

    click_icon("harm_source", win=win, fallback_y=harm_source_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(bus1_x, bus1_y - 10, duration=0.15)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.moveTo(harm_src_x, harm_src_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Harmonic Source"] = "PASS" if did_canvas_change(before_h_src, watch_h_src) else "FAIL"

    # -------------------------------------------------------------
    # 10. Harmonic Filter
    # -------------------------------------------------------------
    # report("Testing Harmonic Filter...")
    harm_flt_x = bus2_x
    harm_flt_y = bus2_y + 110
    watch_h_flt = (harm_flt_x - 45, bus2_y - 20, harm_flt_x + 45, harm_flt_y + 45)
    before_h_flt = ImageGrab.grab(bbox=watch_h_flt)

    click_icon("harm_filter", win=win, fallback_y=harm_filter_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(bus2_x, bus2_y + 20, duration=0.15)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.moveTo(harm_flt_x, harm_flt_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Harmonic Filter"] = "PASS" if did_canvas_change(before_h_flt, watch_h_flt) else "FAIL"

    # -------------------------------------------------------------
    # 11. Circuit Breaker
    # -------------------------------------------------------------
    cb_x = bus1_x + int((bus2_x - bus1_x) * 0.30)
    cb_y = line_y
    # report(f"Testing Circuit Breaker on Line at ({cb_x}, {cb_y})...")

    watch_cb = (cb_x - 20, cb_y - 20, cb_x + 20, cb_y + 20)
    before_cb = ImageGrab.grab(bbox=watch_cb)

    click_icon("breaker", win=win, fallback_y=cb_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(cb_x, cb_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Circuit Breaker"] = "PASS" if did_canvas_change(before_cb, watch_cb) else "FAIL"

    # -------------------------------------------------------------
    # 12. Protection Container
    # -------------------------------------------------------------
    prot_x = bus1_x + int((bus2_x - bus1_x) * 0.70)
    prot_y = line_y
    # report(f"Testing Protection Container on Line at ({prot_x}, {prot_y})...")

    watch_prot = (prot_x - 25, prot_y - 25, prot_x + 25, prot_y + 25)
    before_prot = ImageGrab.grab(bbox=watch_prot)

    click_icon("protection", win=win, fallback_y=prot_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(prot_x, prot_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Protection Container"] = "PASS" if did_canvas_change(before_prot, watch_prot) else "FAIL"

    # -------------------------------------------------------------
    # 13. Universal Machine (U)
    # -------------------------------------------------------------
    # report("Testing Universal Machine (U)...")
    um_x = bus1_x - 130
    um_y = bus1_y - 60
    watch_um = (um_x - 45, um_y - 45, bus1_x + 20, um_y + 45)
    before_um = ImageGrab.grab(bbox=watch_um)

    click_icon("universal_machine", win=win, fallback_y=univ_mach_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(bus1_x, bus1_y - 10, duration=0.15)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.moveTo(um_x, um_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Universal Machine"] = "PASS" if did_canvas_change(before_um, watch_um) else "FAIL"

    # -------------------------------------------------------------
    # 14. Static VAr Compensator (SVC)
    # -------------------------------------------------------------
    # report("Testing Static VAr Compensator (SVC)...")
    svc_x = bus1_x - 130
    svc_y = bus1_y + 60
    watch_svc = (svc_x - 45, svc_y - 45, bus1_x + 20, svc_y + 45)
    before_svc = ImageGrab.grab(bbox=watch_svc)

    click_icon("svc", win=win, fallback_y=svc_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(bus1_x, bus1_y + 10, duration=0.15)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.moveTo(svc_x, svc_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Static VAr Compensator"] = "PASS" if did_canvas_change(before_svc, watch_svc) else "FAIL"

    # -------------------------------------------------------------
    # 15. Mechanically Switched Capacitor (MSC)
    # -------------------------------------------------------------
    # report("Testing Mechanically Switched Capacitor (MSC)...")
    msc_x = bus2_x + 110
    msc_y = bus2_y - 60
    watch_msc = (bus2_x - 20, msc_y - 45, msc_x + 45, msc_y + 45)
    before_msc = ImageGrab.grab(bbox=watch_msc)

    click_icon("msc", win=win, fallback_y=msc_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(bus2_x, bus2_y - 10, duration=0.15)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.moveTo(msc_x, msc_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Mechanically Switched Capacitor"] = "PASS" if did_canvas_change(before_msc, watch_msc) else "FAIL"

    # -------------------------------------------------------------
    # 16. AC-DC Convertor (Busbar 1 -> Busbar 2)
    # -------------------------------------------------------------
    # report("Testing AC-DC Convertor (Busbar 1 -> Busbar 2)...")
    acdc_y = bus1_y - 8
    watch_acdc = (bus1_x + 15, acdc_y - 14, bus2_x - 15, acdc_y + 14)
    before_acdc = ImageGrab.grab(bbox=watch_acdc)

    click_icon("acdc", win=win, fallback_y=acdc_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(bus1_x, acdc_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.moveTo(bus2_x, acdc_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["AC-DC Convertor"] = "PASS" if did_canvas_change(before_acdc, watch_acdc) else "FAIL"

    # -------------------------------------------------------------
    # 17. Unbalanced Load (Connect to Busbar 2)
    # -------------------------------------------------------------
    # report("Testing Unbalanced Load (Busbar 2 -> Right)...")
    unbal_x = bus2_x + 110
    unbal_y = bus2_y + 45
    watch_unbal = (bus2_x - 20, unbal_y - 45, unbal_x + 50, unbal_y + 45)
    before_unbal = ImageGrab.grab(bbox=watch_unbal)

    click_icon("unbalanced_load", win=win, fallback_y=unbal_load_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(bus2_x, bus2_y + 12, duration=0.15)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.moveTo(unbal_x, unbal_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Unbalanced Load"] = "PASS" if did_canvas_change(before_unbal, watch_unbal) else "FAIL"

    # -------------------------------------------------------------
    # 18. Equivalent Branch (Connect Busbar 1 to Busbar 2)
    # -------------------------------------------------------------
    # report("Testing Equivalent Branch (Busbar 1 -> Busbar 2)...")
    equiv_y = bus1_y + 24
    watch_equiv = (bus1_x + 15, equiv_y - 12, bus2_x - 15, equiv_y + 20)
    before_equiv = ImageGrab.grab(bbox=watch_equiv)

    click_icon("equivalent_branch", win=win, fallback_y=equiv_br_btn_y)
    time.sleep(0.3)
    pyautogui.moveTo(bus1_x, equiv_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.moveTo(bus2_x, equiv_y, duration=0.15)
    pyautogui.click()
    time.sleep(0.4)
    dismiss_any_dialog()
    pyautogui.press("esc", presses=2, interval=0.1)
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)
    results["Equivalent Branch"] = "PASS" if did_canvas_change(before_equiv, watch_equiv) else "FAIL"

    # -------------------------------------------------------------
    # Final Output
    # -------------------------------------------------------------
    print("\n" + "=" * 45)
    print("           COMPONENT TEST RESULTS           ")
    print("=" * 45)
    for comp, status in results.items():
        print(f"{comp:35} : {status}")
    print("=" * 45)


def main():
    show_preflight_disclaimer(countdown_seconds=7)

    _, win = get_ipsa_window()
    if win is None:
        report("IPSA 3 window not found.")
        sys.exit(1)

    try:
        if win.get_show_state() == 2:
            win.restore()
        win.maximize()
    except Exception:
        pass

    test_components()


if __name__ == "__main__":
    main()