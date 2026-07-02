@echo off
echo Blender VFX Plugin Setup
echo ========================
powershell.exe -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if errorlevel 1 (
    echo.
    echo Setup failed. See errors above.
    pause
) else (
    pause
)
