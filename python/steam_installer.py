"""
JARVIS Steam Installer — Independent Automation Process
Launched by JARVIS as a detached subprocess. Runs independently.
Usage: python steam_installer.py <app_id> <game_name>
"""
import sys
import os
import time
import ctypes

# ── Arguments ─────────────────────────────────────────────────
app_id    = sys.argv[1] if len(sys.argv) > 1 else "228980"
game_name = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Unknown Game"

RADAR = r"C:\Users\defaultuser0\Desktop\Antigravity\jarvis\JARVIS_RADAR_LOG.txt"

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line)
    try:
        with open(RADAR, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except: pass

# ── DPI Awareness ──────────────────────────────────────────────
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    log("DPI Awareness: LOCKED")
except:
    log("DPI Awareness: already set")

# ── Imports ────────────────────────────────────────────────────
log(f"STEAM INSTALLER PROCESS STARTED for: {game_name} (AppID: {app_id})")

try:
    import pyautogui
    import win32api, win32con, win32gui
    import psutil
    pyautogui.FAILSAFE = False
    log("Core Win32/PyAutoGUI: OK")
except Exception as e:
    log(f"IMPORT FAILED: {e}")
    sys.exit(1)

auto = None
try:
    import pythoncom
    pythoncom.CoInitialize()
    import uiautomation
    auto = uiautomation
    log("uiautomation: OK")
except Exception as e:
    log(f"uiautomation IMPORT FAILED: {e} — coordinate fallback only")

# ── Main Strike Loop ───────────────────────────────────────────
log("Starting strike loop (45 seconds), waiting for dialog to appear...")
time.sleep(3) # Give system_tools.py time to manifest the dialog

start = time.time()
attempt = 0

btn_names = ["Install", "INSTALL", "Next", "Next >", "NEXT >", "Finish", "FINISH", "I Agree", "I AGREE", "Accept"]

while time.time() - start < 45:
    attempt += 1
    log(f"--- SCAN #{attempt} ---")
    
    # ── Method 1: UIAutomation Scan (Most Reliable) ────────────────────
    found_button = False
    if auto:
        try:
            root = auto.GetRootControl()
            # Iterate all top level windows to find Steam dialogs
            for win in root.GetChildren():
                name_lower = win.Name.lower()
                class_lower = win.ClassName.lower()
                
                # Identify if this window belongs to Steam
                if "steam" in name_lower or "install" in name_lower or "sdl_app" in class_lower or "chrome_widget" in class_lower:
                    # Look inside this specific window for the button
                    for btn_name in btn_names:
                        btn = win.ButtonControl(Name=btn_name, SearchDepth=8)
                        if btn.Exists(0.1):  # Very fast check
                            br = btn.BoundingRectangle
                            bx = br.left + br.width() // 2
                            by = br.top  + br.height() // 2
                            
                            log(f"UI-BUTTON '{btn_name}' found at ({bx}, {by}) in '{win.Name}'")
                            
                            # Force the matched window to the foreground if possible
                            try:
                                win.SetFocus()
                            except: pass
                            
                            # Slide and click
                            log("Sliding...")
                            pyautogui.moveTo(bx, by, duration=0.6)
                            time.sleep(0.05)
                            win32api.SetCursorPos((bx, by))
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                            time.sleep(0.08)
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                            log(f"MECHANICAL CLICK delivered on '{btn_name}'")
                            
                            found_button = True
                            if btn_name in ("Finish", "FINISH"):
                                log("INSTALL COMPLETE — SUCCESS")
                                sys.exit(0)
                            
                            time.sleep(1.5)
                            break
                    if found_button: break
        except Exception as e:
            log(f"UIAutomation error: {e}")

    # ── Method 2: Coordinate Fallback (If UI isn't found) ──────────────
    if not found_button:
        log("UIAutomation failed to see the Install button. Attempting coordinate fallback via EnumWindows.")
        try:
            import win32process
            steam_pids = [
                p.info['pid'] for p in psutil.process_iter(['name', 'pid'])
                if p.info['name'] and 'steam' in p.info['name'].lower()
            ]
            target_wins = []
            def _cb(hwnd, _):
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if pid in steam_pids and win32gui.IsWindowVisible(hwnd):
                        target_wins.append(hwnd)
                except: pass
            win32gui.EnumWindows(_cb, None)
            
            if target_wins:
                hwnd = target_wins[0]
                rect = win32gui.GetWindowRect(hwnd)
                wx, wy, wr, wb = rect
                ww, wh = wr - wx, wb - wy
                if ww > 200:
                    try:
                        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
                        win32gui.SetForegroundWindow(hwnd)
                    except: pass
                    
                    strike_x = wx + ww - 110
                    strike_y = wy + wh - 48
                    log(f"COORDINATE-STRIKE fallback: ({strike_x}, {strike_y})")
                    pyautogui.moveTo(strike_x, strike_y, duration=0.6)
                    time.sleep(0.1)
                    win32api.SetCursorPos((strike_x, strike_y))
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    time.sleep(0.08)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    log("COORDINATE-STRIKE delivered")
        except Exception as e:
            log(f"Coordinate Fallback Error: {e}")
            
    time.sleep(2)

log("TIMEOUT — 45 seconds. Automation complete.")
