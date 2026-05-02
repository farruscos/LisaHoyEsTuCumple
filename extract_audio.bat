@echo off
setlocal

cd /d "%~dp0"

if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe extract_audio.py
) else (
    python extract_audio.py
)

if errorlevel 1 (
    pause
    exit /b 1
)

pause
