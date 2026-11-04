@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch_gui.ps1" -Arrangement
if errorlevel 1 pause
endlocal
