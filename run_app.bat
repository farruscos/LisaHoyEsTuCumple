@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo Running Audio App
echo ========================================
echo.

cd /d "%~dp0"

REM Check if venv exists
if not exist venv (
    echo ERROR: Virtual environment not found!
    echo Please run: setup_venv_v2.bat first
    echo.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat >nul 2>&1

if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo [OK] Virtual environment activated
echo.

REM Check for song.mp3
if not exist song.mp3 (
    echo WARNING: song.mp3 not found!
    echo Please extract audio first: python extract_audio.py
    echo.
)

echo Starting Flask server...
echo.
echo ========================================
echo Flask server is starting...
echo ========================================
echo.
echo Open your browser to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py
