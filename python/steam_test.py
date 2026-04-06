"""
JARVIS Steam Installer Diagnostic Script
Run this DIRECTLY (python steam_test.py) to test if the automation works.
This will tell us EXACTLY what fails and why.
"""
import sys
import time
import os

print("[1] Starting diagnostic...")

# Test win32
try:
    import pythoncom
    import win32gui
    import win32con
    import win32api
    print("[OK] win32gui, win32con, win32api, pythoncom imported OK")
except Exception as e:
    print(f"[FAIL] win32 import failed: {e}")
    sys.exit(1)

# Test pyautogui
try:
    import pyautogui
    pyautogui.FAILSAFE = False  # Disable failsafe for testing
    print("[OK] pyautogui imported OK")
except Exception as e:
    print(f"[FAIL] pyautogui import failed: {e}")
    sys.exit(1)

# Test psutil
try:
    import psutil
    print("[OK] psutil imported OK")
except Exception as e:
    print(f"[FAIL] psutil import failed: {e}")
    sys.exit(1)

# Test uiautomation
try:
    import uiautomation as auto
    print("[OK] uiautomation imported OK")
except Exception as e:
    print(f"[FAIL] uiautomation import failed: {e}")
    sys.exit(1)

print("\n[2] Finding Steam processes...")
steam_pids = [p.info['pid'] for p in psutil.process_iter(['name', 'pid'])
              if p.info['name'] and 'steam' in p.info['name'].lower()]
print(f"    Steam PIDs found: {steam_pids}")

print("\n[3] Enumerating all visible windows...")
all_wins = []
def _enum_cb(hwnd, results):
    _, pid = win32gui.GetWindowThreadProcessId(hwnd)
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if title.strip():
            results.append((hwnd, pid, title))

win32gui.EnumWindows(_enum_cb, all_wins)

steam_wins = [(h, p, t) for h, p, t in all_wins if p in steam_pids]
print(f"    Total visible windows: {len(all_wins)}")
print(f"    Steam windows found: {len(steam_wins)}")
for h, p, t in steam_wins:
    rect = win32gui.GetWindowRect(h)
    print(f"      HWND={h} PID={p} Title='{t}' Rect={rect}")

if not steam_wins:
    print("\n[!] No Steam windows found. Is Steam running?")
    print("    Launching install dialog...")
    os.startfile("steam://install/228980")
    print("    Waiting 5 seconds for dialog...")
    time.sleep(5)
    steam_wins = []
    win32gui.EnumWindows(_enum_cb, steam_wins)
    steam_wins = [(h, p, t) for h, p, t in steam_wins if p in steam_pids]
    print(f"    After launch, Steam windows: {steam_wins}")

print("\n[4] Checking screen size and DPI...")
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    print("    DPI Awareness: SET")
except:
    print("    DPI Awareness: FAILED (already set)")

w, h = pyautogui.size()
print(f"    Screen size: {w}x{h}")

if steam_wins:
    print("\n[5] Testing UI Automation on first Steam window...")
    hwnd, pid, title = steam_wins[0]
    
    # Force foreground
    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
    try:
        win32gui.SetForegroundWindow(hwnd)
        print("    Window brought to foreground")
    except Exception as e:
        print(f"    SetForegroundWindow failed: {e}")
    
    time.sleep(1)
    
    # Get window rect via win32
    rect = win32gui.GetWindowRect(hwnd)
    wx, wy, wr, wb = rect
    ww, wh = wr - wx, wb - wy
    print(f"    Window rect: left={wx} top={wy} width={ww} height={wh}")
    
    # Try UIAutomation
    print("    Searching for buttons via UIAutomation...")
    try:
        pythoncom.CoInitialize()
        win_ctrl = auto.ControlFromHandle(hwnd)
        if win_ctrl:
            print(f"    Got control: {win_ctrl.Name} | {win_ctrl.ControlType}")
            all_btns = win_ctrl.GetChildren()
            print(f"    Children: {len(all_btns)}")
            for btn_name in ["Install", "Next", "Next >", "Finish", "I Agree", "INSTALL", "NEXT"]:
                btn = win_ctrl.ButtonControl(Name=btn_name, SearchDepth=10)
                if btn.Exists(0):
                    br = btn.BoundingRectangle
                    bx = br.left + (br.width() // 2)
                    by = br.top + (br.height() // 2)
                    print(f"    [FOUND] Button '{btn_name}' at ({bx}, {by})")
        else:
            print("    Could not get control from handle")
    except Exception as e:
        print(f"    UIAutomation error: {e}")
    
    print(f"\n[6] Coordinate-strike fallback: ({wx + ww - 110}, {wy + wh - 48})")
    print("    (This is where the 'Install' button SHOULD be)")

print("\n[DONE] Diagnostic complete.")
input("Press Enter to exit...")
