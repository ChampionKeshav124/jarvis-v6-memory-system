@echo off
:: ═══════════════════════════════════════════════════════════════
::  JARVIS V5 — TITAN LAUNCHER (1-CLICK ADMIN)
::  Manages automatic folder-detection and high-fidelity startup
:: ═══════════════════════════════════════════════════════════════

:: Identify current folder automatically
set CURRENT_DIR=%~dp0
cd /d "%CURRENT_DIR%"

echo ═══════════════════════════════════════════════════════════════
echo  JARVIS V5 — TITAN CORE RELOADED
echo ═══════════════════════════════════════════════════════════════
echo [TITAN] System Root: %CURRENT_DIR%
echo [TITAN] Engaging High-Fidelity Startup Protocol...

:: Check if running as Admin (for user's visibility)
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [TITAN CLEARANCE] Administrative Access confirmed.
) else (
    echo [TITAN WARNING] Limited User Clearance! ⚠️
    echo Please RESTART this file by Right-Clicking and selecting "Run as Administrator".
    echo Steam control will be BLOCKED in Limited Mode.
    pause
    exit
)

:: Build and Launch
echo [TITAN] Syncing NPC Audio & Steam Object-Link...
npm run dev

echo [TITAN] JARVIS shutdown. You may now close this terminal.
pause
