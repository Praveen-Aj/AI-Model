@echo off
title Local AI Model Manager
color 0B

echo ===================================================
echo   🤖 LOCAL AI MODEL MANAGER LAUNCHER
echo ===================================================
echo.
echo Checking dependencies and starting Ollama backend...
echo (This window will automatically close when the GUI opens)
echo.
echo ===================================================
echo.

cd /d "%~dp0"

REM Run the main startup powershell script to show the interactive menus
powershell -ExecutionPolicy Bypass -File "%~dp0ollama-manager.v2.ps1"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ===================================================
    echo   ❌ STARTUP ERROR
    echo ===================================================
    echo.
    echo An error occurred while launching the application.
    echo.
    pause
)
