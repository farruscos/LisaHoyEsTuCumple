@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo Lisa Video App - Environment Setup
echo ========================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Checking Python version...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%
echo.

cd /d "%~dp0"

echo Step 1: Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Removing...
    rmdir /s /q venv >nul 2>&1
)

python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment created
echo.

echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

echo Step 3: Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
echo [OK] pip upgraded
echo.

echo Step 4: Installing dependencies...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies
    echo.
    echo Troubleshooting:
    echo - Try running: python -m pip install --upgrade pip
    echo - Check your internet connection
    echo - Try running CMD as Administrator
    echo.
    pause
    exit /b 1
)
echo.
echo [OK] Dependencies installed
echo.

echo ========================================
echo SUCCESS!
echo ========================================
echo.
echo Virtual environment setup complete.
echo.
echo To activate the environment in the future, run:
echo   venv\Scripts\activate.bat
echo.
echo To start the application:
echo   run_app.bat
echo.
echo Then open your browser to:
echo   http://localhost:5000
echo.
pause
