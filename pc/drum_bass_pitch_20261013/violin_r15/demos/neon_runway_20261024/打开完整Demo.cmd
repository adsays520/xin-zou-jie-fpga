@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0open_demo.ps1"
if errorlevel 1 pause
endlocal
