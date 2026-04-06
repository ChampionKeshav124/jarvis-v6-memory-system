"""
 ═══════════════════════════════════════════════════════════════
  JARVIS V6 — System Control Tools
  BYTEFORGE SYSTEM
 
  V6: Memory-Integrated System Control & Steam Automation.
 ═══════════════════════════════════════════════════════════════
"""

import os
import sys
import glob
import subprocess
import webbrowser
import psutil
import json
import threading
import time
import re
import winreg
import ctypes
from pathlib import Path

# TITAN CORE: Global Automation Libraries (Stable Path)
_AUTOMATION_ERRORS = []
try:
    import uiautomation as auto
except Exception as e:
    _AUTOMATION_ERRORS.append(f"uiautomation: {e}")

try:
    import pyautogui
except Exception as e:
    _AUTOMATION_ERRORS.append(f"pyautogui: {e}")

try:
    # Ensure psutil is responsive
    _temp = psutil.cpu_percent()
except Exception as e:
    _AUTOMATION_ERRORS.append(f"psutil: {e}")

try:
    import numpy as np
except ImportError:
    _AUTOMATION_ERRORS.append("numpy: Missing (Profile bypass disabled)")

try:
    from computer_control import computer_control
except ImportError:
    def computer_control(p, **k): return "ComputerControl module missing."

class SystemTools:
    def __init__(self):
        # Dynamic App Cache — loaded from disk (instant) or rebuilt in background
        self.app_cache = {}
        self.cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_index.json")
        self._load_cache()  # Fast sync load from disk
        # Rebuild in background if cache is old/missing
        self._maybe_refresh_in_background()

    def _load_cache(self):
        """Instant load from disk — < 50ms."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.app_cache = json.load(f)
        except Exception:
            self.app_cache = {}

    def _maybe_refresh_in_background(self):
        """Only refresh if cache is missing or older than 24 hours."""
        import time
        needs_refresh = True
        if os.path.exists(self.cache_file):
            mtime = os.path.getmtime(self.cache_file)
            if (time.time() - mtime) < 86400:
                needs_refresh = False
        if needs_refresh:
            threading.Thread(target=self._rebuild_cache, daemon=True).start()

    def _rebuild_cache(self):
        """Runs PowerShell Get-StartApps in background and saves to disk."""
        try:
            cmd = 'powershell -Command "Get-StartApps | Select-Object Name, AppID | ConvertTo-Json"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=12)
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                items = data if isinstance(data, list) else [data]
                new_cache = {}
                for item in items:
                    name  = item.get('Name', '').lower().strip()
                    appid = item.get('AppID', '')
                    if name and appid:
                        new_cache[name] = appid
                self.app_cache = new_cache
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self.app_cache, f)
        except Exception as e:
            pass  # Silent — will retry next startup

    def _find_in_start_menu(self, app_lower: str):
        """Fast scan of Start Menu .lnk shortcuts only (no os.walk of full drives)."""
        app_lower_nospace = app_lower.replace(" ", "")
        start_menu_paths = [
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs"),
        ]
        for sm_path in start_menu_paths:
            if not os.path.exists(sm_path):
                continue
            for lnk in glob.glob(os.path.join(sm_path, "**", "*.lnk"), recursive=True):
                lnk_name = os.path.splitext(os.path.basename(lnk))[0].lower().replace(" ", "")
                if app_lower_nospace in lnk_name or lnk_name in app_lower_nospace:
                    return lnk
    
    # ── ADVANCED STEAM ENGINE (SUPER-TITAN) ───────────────────
    def _find_steam_path(self) -> Path | None:
        registry_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
            (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Valve\Steam"),
        ]
        for hive, key_path in registry_keys:
            try:
                key = winreg.OpenKey(hive, key_path)
                val, _ = winreg.QueryValueEx(key, "InstallPath")
                winreg.CloseKey(key)
                p = Path(val)
                if p.exists() and (p / "steam.exe").exists():
                    return p
            except Exception: continue
        return None

    def _get_steam_libraries(self, steam_path: Path) -> list[Path]:
        libraries = [steam_path / "steamapps"]
        vdf_path  = steam_path / "steamapps" / "libraryfolders.vdf"
        if not vdf_path.exists(): return libraries
        try:
            content = vdf_path.read_text(encoding="utf-8", errors="ignore")
            for raw_path in re.findall(r'"path"\s+"([^"]+)"', content):
                lib = Path(raw_path.replace("\\\\", "/")) / "steamapps"
                if lib.exists() and lib not in libraries:
                    libraries.append(lib)
        except Exception: pass
        return libraries

    def _get_local_steam_games(self, steam_path: Path) -> list[dict]:
        games = []
        for lib in self._get_steam_libraries(steam_path):
            for acf in lib.glob("appmanifest_*.acf"):
                try:
                    # 60-second timeout (V6)
                    content = acf.read_text(encoding="utf-8", errors="ignore")
                    app_id  = re.search(r'"appid"\s+"(\d+)"',     content)
                    name    = re.search(r'"name"\s+"([^"]+)"',     content)
                    state   = re.search(r'"StateFlags"\s+"(\d+)"', content)
                    if app_id and name:
                        games.append({"id": app_id.group(1), "name": name.group(1), "state": int(state.group(1)) if state else 0})
                except Exception: continue
        return games

    def _handle_steam_profile_selection(self):
        """Bypass 'Who's playing?' using physical screenshot analysis or direct coordinate clicking."""
        try:
            import uiautomation as auto
            import pyautogui
            import numpy as np
            time.sleep(1.5)
            # Find Steam windows
            for win in auto.GetRootControl().GetChildren():
                if "steam" in win.Name.lower() or "who's playing" in win.Name.lower():
                    rect = win.BoundingRectangle
                    ww = rect.width()
                    wh = rect.height()
                    if ww > 300:
                        wx, wy = rect.left, rect.top
                        
                        # Try Vision fallback for colorful avatar
                        try:
                            screenshot = pyautogui.screenshot(region=(wx, wy, ww, wh))
                            img = np.array(screenshot)
                            search_y1, search_y2 = wh // 3, wh * 3 // 4
                            search_x1, search_x2 = ww // 5, ww * 4 // 5
                            region = img[search_y1:search_y2, search_x1:search_x2]
                            
                            r, g, b = region[:,:,0].astype(int), region[:,:,1].astype(int), region[:,:,2].astype(int)
                            max_c = np.maximum(np.maximum(r, g), b)
                            sat = max_c - np.minimum(np.minimum(r, g), b)
                            colorful = (max_c > 60) & (sat > 40)
                            
                            if colorful.any():
                                cols = np.where(colorful.any(axis=0))[0]
                                rows = np.where(colorful.any(axis=1))[0]
                                abs_x = wx + search_x1 + int(cols.mean())
                                abs_y = wy + search_y1 + int(rows.mean())
                                pyautogui.click(abs_x, abs_y)
                                return True
                        except: pass
                        
                        # Absolute fallback: click center-left
                        px = wx + (ww // 2) - 100
                        py = wy + (wh // 2)
                        pyautogui.click(px, py)
                        return True
            return False
        except Exception: 
            return False


    def open_application(self, app_name: str) -> str:
        """Opens an application — uses cache, start menu, then web fallback."""
        app_lower = app_name.lower().strip()

        # --- TITAN HARD-PATHS (Prioritize these) ---
        titan_apps = {
            "steam": r"C:\Program Files (x86)\Steam\Steam.exe",
            "epic": r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
            "epic games": r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
            "epic launcher": r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe"
        }
        for name, path in titan_apps.items():
            if name in app_lower or app_lower in name:
                if os.path.exists(path):
                    try:
                        subprocess.Popen([path], shell=False)
                        return f"Launching {app_name} via primary system path."
                    except Exception: pass

        # 1. Check dynamic cache (Microsoft Store + Start Menu AppIDs)
        best_match = None
        # Exact match first
        if app_lower in self.app_cache:
            best_match = self.app_cache[app_lower]
        else:
            # Partial match
            for name, appid in self.app_cache.items():
                if app_lower in name or name in app_lower:
                    best_match = appid
                    break

        if best_match:
            try:
                subprocess.Popen(f'explorer.exe shell:AppsFolder\\{best_match}', shell=True)
                return f"Launching {app_name}."
            except Exception:
                pass

        # 2. Try Windows 'start' command (handles many EXEs in PATH)
        try:
            result = subprocess.run(
                f'start "" "{app_name}"', shell=True,
                capture_output=True, timeout=3
            )
            if result.returncode == 0:
                return f"Launching {app_name}."
        except Exception:
            pass

        # 3. Search Start Menu shortcuts only (fast — no full drive scan)
        lnk = self._find_in_start_menu(app_lower)
        if lnk:
            try:
                os.startfile(lnk)
                return f"Launching {app_name} via shortcut."
            except Exception:
                pass

        # 4. Universal fallback → open web version
        if " " not in app_lower:
            url = app_lower if "." in app_lower else f"www.{app_lower}.com"
            webbrowser.open(f"https://{url}")
            return f"I could not find {app_name} locally, so I am opening the web version."
        else:
            search_url = "https://www.google.com/search?q=" + app_lower.replace(" ", "+")
            webbrowser.open(search_url)
            return f"I could not locate {app_name}. Opening web search instead."

    def close_application(self, app_name: str) -> str:
        """Terminates a running process by name."""
        app_lower = app_name.lower().strip()
        closed = 0
        try:
            for proc in psutil.process_iter(['name']):
                pname = proc.info['name'].lower()
                if app_lower in pname or pname.startswith(app_lower):
                    try:
                        proc.terminate()
                        closed += 1
                    except Exception:
                        pass
            if closed > 0:
                return f"Terminated {app_name} ({closed} process(es))."
            return f"No active process found for {app_name}."
        except Exception as e:
            return f"Error during termination: {e}"

    def open_url(self, url: str) -> str:
        """Opens a URL using native Windows Shell for maximum speed."""
        url = url.strip()
        if not url.startswith("http"):
            if "." not in url:
                url = f"www.{url}.com"
            url = f"https://{url}"
        try:
            # os.startfile is significantly faster than webbrowser.open on Windows
            os.startfile(url)
            return f"Opening {url}."
        except Exception as e:
            return f"Failed to open URL: {e}"

    def search_google(self, query: str) -> str:
        """Performs a Google search using native shell for speed."""
        search_url = "https://www.google.com/search?q=" + query.strip().replace(" ", "+")
        try:
            os.startfile(search_url)
            return f"Searching Google for '{query}'."
        except Exception as e:
            return f"Failed to perform search: {e}"

    # --- TITAN UPGRADE: Gaming, Messaging, WebScout ---

    def steam_action(self, action: str, app_id: str = "", game_name: str = "") -> str:
        """
        Steam actions — Bypasses Chromium Store Engine completely.
        Uses Small Mode (minigameslist) to avoid the fastly CDN chunk error.
        """
        import time
        steam_exe = r"C:\Program Files (x86)\Steam\Steam.exe"
        if not os.path.exists(steam_exe):
            return "Steam not found at the default path."

        # V6: Rapid multi-command workflow — keep input active
        if action == "launch" or action == "home":
            subprocess.Popen([steam_exe], shell=False)
            return "Launching Steam application."

        if action == "install":
            if not app_id:
                return f"I need a Steam App ID to install '{game_name}'."
            try:
                # 1. WAKE STEAM & BYPASS PROFILE ("Who's playing?" popup)
                os.startfile("steam://open/main")
                time.sleep(3.0) 
                if hasattr(self, '_handle_steam_profile_selection'):
                    self._handle_steam_profile_selection() 
                time.sleep(1.0)
                
                # 2. TRIGGER INSTALL DIALOG
                os.startfile(f"steam://install/{app_id}")

                installer_script = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "steam_installer.py"
                )
                
                radar_path = r"C:\Users\defaultuser0\Desktop\Antigravity\jarvis\JARVIS_RADAR_LOG.txt"
                with open(radar_path, "w", encoding="utf-8") as f:
                    f.write(f"[JARVIS] Launching installer for: {game_name} (AppID: {app_id})\n")

                p = subprocess.Popen(
                    [sys.executable, installer_script, app_id, game_name],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
                return f"Installer launched for '{game_name}' — PID: {p.pid}"
            except Exception as e:
                return f"Failed to launch installer: {e}"




        elif action == "search" and game_name:
            # Cannot use the native web store, so just launch mini library and tell the user.
            try:
                os.startfile("steam://open/minigameslist")
            except Exception:
                pass
            return f"Steam is launching in Small Library mode. You must use the web browser to search for '{game_name}' because your Steam Store connection is blocked."
        
        else:
            return "Steam is launching."

    def epic_action(self, action: str, game_name: str) -> str:
        """Triggers Epic actions. action can be 'launcher', 'store', or 'search'."""
        if action == "launcher":
            return self.epic_launcher()
        
        # Epic store search deep-link
        search_query = game_name.strip().replace(" ", "%20")
        url = f"com.epicgames.launcher://store/browse?q={search_query}&sortBy=relevancy&sortDir=DESC&count=40"
        try:
            webbrowser.open(url)
            return f"Opening Epic Games Store to install '{game_name}'."
        except Exception as e:
            return f"Failed to open Epic Store: {e}"

    def get_steam_details(self, app_id: str) -> dict:
        """Fetches real-time price and info from Steam API."""
        try:
            import requests
            url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
            response = requests.get(url, timeout=5).json()
            if response and response.get(app_id, {}).get("success"):
                data = response[app_id]["data"]
                return {
                    "name": data.get("name"),
                    "is_free": data.get("is_free", False),
                    "price": data.get("price_overview", {}).get("final_formatted", "Free") if not data.get("is_free") else "Free",
                    "id": app_id
                }
        except Exception: pass
        return None

    def search_steam_api(self, query: str) -> str:
        """Searches the Steam catalog API and returns the AppID of the closest match."""
        try:
            import requests
            search_url = f"https://store.steampowered.com/api/storesearch/?term={query.replace(' ', '+')}&l=english&cc=US"
            response = requests.get(search_url, timeout=5).json()
            if response and response.get("total", 0) > 0 and response.get("items"):
                return str(response["items"][0]["id"])
        except Exception:
            pass
        return None

    def scout_game_price(self, game_name: str) -> dict:
        """Scouts both stores for the best info. Returns a result dict."""
        # This will be used by the Aegis Engine in jarvis.py
        # We search Steam first as it has the best API
        return {"name": game_name, "source": "search"}

    def send_whatsapp(self, phone: str, message: str) -> str:
        """Prepares a WhatsApp message via web bridge."""
        # Clean phone number (remove non-digits)
        phone = "".join(filter(str.isdigit, phone))
        url = f"https://api.whatsapp.com/send?phone={phone}&text={message.replace(' ', '%20')}"
        try:
            webbrowser.open(url)
            return f"Preparing WhatsApp message to {phone}. Please hit 'Send' in the browser."
        except Exception as e:
            return f"Failed to open WhatsApp: {e}"

    def send_telegram(self, username: str, message: str) -> str:
        """Prepares a Telegram message via app/web bridge."""
        # username can be a tag or a number
        url = f"tg://msg?text={message.replace(' ', '%20')}&to={username}"
        try:
            # Try app scheme first, then fallback to web if needed
            webbrowser.open(url)
            return f"Opening Telegram to message {username}."
        except Exception:
            web_url = f"https://t.me/{username.replace('@', '')}"
            webbrowser.open(web_url)
            return f"Opening Telegram Web for {username}."

    def web_scout(self, platform: str, query: str) -> str:
        """Performs site-specific searches (Amazon, GitHub, Reddit, YouTube)."""
        search_urls = {
            "amazon": "https://www.amazon.com/s?k=",
            "github": "https://github.com/search?q=",
            "reddit": "https://www.reddit.com/search/?q=",
            "youtube": "https://www.youtube.com/results?search_query="
        }
        base_url = search_urls.get(platform.lower())
        if not base_url: return self.search_google(f"{platform} {query}")
        
        full_url = base_url + query.strip().replace(" ", "+")
        try:
            webbrowser.open(full_url)
            return f"Scouting {platform} for '{query}'."
        except Exception as e:
            return f"Failed to scout {platform}: {e}"

    # --- END TITAN UPGRADE ---

    def search_files(self, query: str) -> str:
        """Searches Desktop, Documents, and Downloads for matching files."""
        user_home = os.path.expanduser("~")
        search_dirs = [
            os.path.join(user_home, "Desktop"),
            os.path.join(user_home, "Documents"),
            os.path.join(user_home, "Downloads"),
        ]
        results = []
        for path in search_dirs:
            if not os.path.exists(path):
                continue
            for root, _, files in os.walk(path):
                depth = root.count(os.sep) - path.count(os.sep)
                if depth > 5:
                    continue
                for f in files:
                    if query.lower() in f.lower():
                        results.append(os.path.join(root, f))
                        if len(results) >= 5:
                            break
                if len(results) >= 5:
                    break
        if results:
            return "Found your matches:\n" + "\n".join(f"📍 {r}" for r in results)
        return f"I searched your system, but could not find '{query}'."

    def type_text(self, text: str) -> str:
        """Physically types the given string on the keyboard."""
        try:
            import pyautogui
            pyautogui.write(text, interval=0.02)
            return "Done typing."
        except Exception as e:
            return f"Failed to access keyboard: {e}"

    def play_youtube(self, query: str) -> str:
        """Searches YouTube and plays the top match directly."""
        try:
            import urllib.request
            import re
            search_url = "https://www.youtube.com/results?search_query=" + query.replace(" ", "+")
            html = urllib.request.urlopen(search_url).read().decode()
            video_ids = re.findall(r"watch\?v=(\S{11})", html)
            if video_ids:
                # Open the first matching video directly
                os.startfile(f"https://www.youtube.com/watch?v={video_ids[0]}")
                return f"Playing '{query}' on YouTube."
            else:
                return f"Couldn't find video for '{query}'."
        except Exception as e:
            return f"YouTube API error: {e}"

    def update_system(self) -> str:
        """Launches native Microsoft Winget updates and Steam game downloads natively."""
        try:
            # 1. PC Software Update via Winget in a physical hacker terminal popup
            os.system('start cmd /k "color 0A && echo [JARVIS UPDATE PROTOCOL INITIATED] && echo Checking installed packages... && winget upgrade --all"')
            
            # 2. Steam Game Updates
            try:
                os.startfile("steam://open/downloads")
            except Exception:
                pass
            
            return "Updating all software and games on your system now."
        except Exception as e:
            return f"Update protocol failed: {e}"

    def computer_action(self, parameters: dict) -> str:
        """Universal computer control: Click, Type, AI-Screen-Find."""
        return computer_control(parameters)


# Singleton — instantiates instantly (loads cache from disk in ms)
tools = SystemTools()
