@echo off
echo VFX Core Plugin Setup
echo =====================
powershell.exe -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if errorlevel 1 (
    echo.
    echo Installation failed. See errors above.
    pause
) else (
    pause
)
