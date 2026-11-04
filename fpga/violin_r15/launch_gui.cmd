@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch_gui.ps1" %*
set "launch_result=%ERRORLEVEL%"
if not "%launch_result%"=="0" pause
exit /b %launch_result%
