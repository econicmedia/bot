@echo off
echo ========================================
echo    AI Trading Bot - Quick Start
echo ========================================
echo.

echo Checking environment...
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please ensure venv is set up correctly.
    pause
    exit /b 1
)

echo Virtual environment found: OK
echo.

echo Starting AI Trading Bot Server...
echo Dashboard will be available at: http://localhost:8080/dashboard
echo API docs will be available at: http://localhost:8080/docs
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

venv\Scripts\python.exe main_server_fixed.py

echo.
echo Server stopped.
pause
