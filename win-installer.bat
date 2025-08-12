@echo off
echo ======================================
echo   Project Setup Script
echo ======================================

REM Check Python installation
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Python is not installed or not in PATH.
    pause
    exit /b
)

REM Check pip installation
pip --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo pip is not installed or not in PATH.
    pause
    exit /b
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate

REM Install requirements
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Create run.bat
echo Creating run.bat...
(
echo @echo off
echo call venv\Scripts\activate
echo python src\main.py
) > run.bat

echo ======================================
echo Setup complete! 
echo To run the project, double-click run.bat
echo ======================================

pause