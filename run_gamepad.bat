@echo off
cd /d "%~dp0"
echo === Auto Loot PoE2 Helper - Gamepad Mode ===
echo Controller: DualSense Wireless
echo Buttons: X=pickup, D-pad Down=HP, D-pad Right=MP
echo.
C:\Users\OLD\anaconda3\python.exe -m src.main --gui
pause
