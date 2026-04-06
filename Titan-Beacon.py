import os
import sys

# 📡 TITAN-BEACON: JARVIS SYSTEM DISCOVERY
def deploy_beacon():
    # 🌍 Part 1: Path Discovery
    current_path = os.path.dirname(os.path.abspath(__file__))
    print(f"\n[TITAN-BEACON] JARVIS Root Identified: {current_path}")
    
    # 📜 Part 2: Manual Recovery Generation
    manual_content = f"""# JARVIS V5 — TACTICAL MANUAL (RECOVERY)
═══════════════════════════════════════════════════════════════
Current System Path: {current_path}
Deployment Status: OPERATIONAL
Elevation Required: YES (For Steam/System Control)
═══════════════════════════════════════════════════════════════

🚀 HOW TO ACTIVATE JARVIS (STABLE MODE):
1. Locate 'Run_JARVIS_Admin.bat' in this folder.
2. Right-Click it and select 'Run as Administrator'.
3. Click 'Yes' on the Windows security prompt.
4. JARVIS will boot with full Titan-Object-Link vision.

🛠️ TROUBLESHOOTING:
- Mouse Circle (Hanging): Run 'taskkill /F /IM electron.exe /T; taskkill /F /IM powershell.exe /T' in a terminal.
- Not Clicking Steam: Ensure you ran the BAT file AS ADMINISTRATOR. Windows security blocks non-admin apps from clicking high-privilege apps like Steam.
- Voice Sensitivity: Increase FFT resolution in renderer/app.js to 512 for better whisper detection.

- [TITAN CORE]
"""
    
    try:
        manual_path = os.path.join(current_path, "JARVIS_MANUAL_CLEARANCE.txt")
        with open(manual_path, "w", encoding="utf-8") as f:
            f.write(manual_content)
        print(f"[TITAN-BEACON] Instructions generated at: {manual_path}")
    except Exception as e:
        print(f"[TITAN-ERROR] Failed to write manual: {e}")

    print("\n[TITAN-BEACON] Setup Complete. Use 'Run_JARVIS_Admin.bat' to launch with full power.\n")

if __name__ == "__main__":
    deploy_beacon()
