@echo off
cd /d "%~dp0"

:: Check admin and auto-elevate if needed
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo === Auto Loot PoE2 Helper - Gamepad Mode ===
echo Controller: DualSense Wireless (will be hidden)
echo Virtual Xbox 360 will be created instead.
echo.
echo IMPORTANT: Start this BEFORE launching PoE2!
echo The bot will hide DualSense so PoE2 uses the virtual Xbox controller.
echo.
C:\Users\OLD\anaconda3\python.exe -m src.main --gui
pause
