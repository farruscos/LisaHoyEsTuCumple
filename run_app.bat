@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo Running Video App
echo ========================================
echo.

cd /d "%~dp0"

REM Check if venv exists
if not exist venv (
    echo ERROR: Virtual environment not found!
    echo Please run: setup_venv.bat first
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

REM Check for local media when environment URLs are not set.
if not exist song.mp3 (
    echo WARNING: song.mp3 not found!
    echo Set AUDIO_URL or extract audio first: python extract_audio.py
    echo.
)

if not exist "Lisa hoy es tu cumple - YouTube.mp4" (
    echo WARNING: source MP4 not found locally.
    echo Set VIDEO_URL in deployment or place the base MP4 in the project root for local testing.
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

python src\app.py
