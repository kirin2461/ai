@echo off
setlocal enabledelayedexpansion

title AI Humanity - Build EXE
color 0A

echo ==========================================
echo    AI Humanity - EXE Builder
echo ==========================================
echo.

:: Find Python
set PYTHON_CMD=

where python >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python
    goto :FOUND_PYTHON
)

where py >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py
    goto :FOUND_PYTHON
)

echo [ERROR] Python not found!
echo Please install Python from https://python.org
pause
exit /b 1

:FOUND_PYTHON
echo [1/5] Checking Python...
%PYTHON_CMD% --version
echo.

:: Check/create virtual environment
if not exist "venv" (
    echo [2/5] Creating virtual environment...
    %PYTHON_CMD% -m venv venv
    if %errorlevel% NEQ 0 (
        echo [ERROR] Failed to create venv
        pause
        exit /b 1
    )
) else (
    echo [2/5] Virtual environment found
)
echo.

:: Activate venv
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

:: Install dependencies
echo [4/5] Installing dependencies...
pip install --upgrade pip --quiet
if exist requirements.txt (
    pip install -r requirements.txt --quiet
)
pip install pyinstaller --quiet
echo.

:: Build EXE
echo [5/5] Building EXE with PyInstaller...
echo.

if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "*.spec" del /q *.spec

pyinstaller --onefile --windowed --name=AI_Humanity --icon=assets/icon.ico main.py 2>nul
if %errorlevel% NEQ 0 (
    pyinstaller --onefile --windowed --name=AI_Humanity main.py
)

echo.
echo ==========================================
if exist "dist\AI_Humanity.exe" (
    echo [SUCCESS] Build complete!
    echo EXE file: dist\AI_Humanity.exe
) else (
    echo [ERROR] Build failed!
)
echo ==========================================

pause
