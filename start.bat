@echo off
setlocal enabledelayedexpansion

title AI Humanity - Launcher v3.1
color 0B

echo.
echo ========================================
echo    AI HUMANITY - Launcher v3.1
echo    Requires Python 3.11 for Coqui TTS
echo ========================================
echo.

:: Check for Python 3.11 specifically
set PYTHON_CMD=
set PYTHON_VERSION=

:: Try py -3.11 first (Windows Python Launcher)
py -3.11 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py -3.11
    goto :CHECK_VERSION
)

:: Try python command and check version
where python >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo Found Python version: !PYTHON_VERSION!
    
    :: Check if it's 3.11.x
    echo !PYTHON_VERSION! | findstr /B "3.11" >nul
    if !errorlevel!==0 (
        set PYTHON_CMD=python
        goto :FOUND_PYTHON
    )
    
    :: Check if it's 3.10.x (also compatible)
    echo !PYTHON_VERSION! | findstr /B "3.10" >nul
    if !errorlevel!==0 (
        set PYTHON_CMD=python
        goto :FOUND_PYTHON
    )
    
    echo.
    echo [WARNING] Your Python version is !PYTHON_VERSION!
    echo [WARNING] Coqui TTS requires Python 3.10 or 3.11
    echo.
)

:: Python 3.11 not found
echo ==========================================
echo [ERROR] Python 3.11 is required!
echo ==========================================
echo.
echo Coqui XTTS v2 (voice cloning) requires Python 3.10-3.11
echo.
echo Please follow these steps:
echo.
echo 1. Download Python 3.11 from:
echo    https://www.python.org/downloads/release/python-3119/
echo.
echo 2. During installation, CHECK:
echo    [x] Add Python 3.11 to PATH
echo    [x] Install py launcher
echo.
echo 3. If you have Python 3.13 installed:
echo    - You can have multiple Python versions
echo    - Use 'py -3.11' to run Python 3.11
echo.
echo 4. After installation, run this script again.
echo.
pause
exit /b 1

:CHECK_VERSION
for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python version: %PYTHON_VERSION%

:FOUND_PYTHON
echo.
echo [OK] Using: %PYTHON_CMD% (version %PYTHON_VERSION%)
echo.

:MENU
echo ========================================
echo Select action:
echo ========================================
echo.
echo [1] Run application (Python)
echo [2] Build EXE (PyInstaller)
echo [3] Run EXE (if built)
echo [4] Install ALL dependencies
echo [5] Create virtual environment
echo [6] Exit
echo.
set /p choice="Your choice (1-6): "

if "%choice%"=="1" goto RUN_PYTHON
if "%choice%"=="2" goto BUILD_EXE
if "%choice%"=="3" goto RUN_EXE
if "%choice%"=="4" goto INSTALL_DEPS
if "%choice%"=="5" goto CREATE_VENV
if "%choice%"=="6" exit /b 0

echo Invalid choice. Try again.
pause
goto :MENU

:CREATE_VENV
echo.
echo [INFO] Creating virtual environment with Python 3.11...
if exist venv (
    echo [INFO] Removing old venv...
    rmdir /s /q venv
)
%PYTHON_CMD% -m venv venv
if %errorlevel% NEQ 0 (
    echo [ERROR] Failed to create venv
    pause
    goto :MENU
)
echo [OK] Virtual environment created!
echo [INFO] Now run option [4] to install dependencies.
pause
goto :MENU

:INSTALL_DEPS
echo.
echo [INFO] Installing dependencies...
echo.

:: Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo [WARNING] Virtual environment not found!
    echo [INFO] Creating venv first...
    %PYTHON_CMD% -m venv venv
    if %errorlevel% NEQ 0 (
        echo [ERROR] Failed to create venv
        pause
        goto :MENU
    )
)

:: Use venv python directly
set VENV_PYTHON=venv\Scripts\python.exe

echo [1/5] Upgrading pip...
%VENV_PYTHON% -m pip install --upgrade pip
if %errorlevel% NEQ 0 (
    echo [ERROR] Failed to upgrade pip
    pause
    goto :MENU
)

echo.
echo [2/5] Installing PyQt6...
%VENV_PYTHON% -m pip install PyQt6
if %errorlevel% NEQ 0 (
    echo [WARNING] PyQt6 installation had issues, continuing...
)

echo.
echo [3/5] Installing core dependencies...
%VENV_PYTHON% -m pip install openai python-dotenv numpy requests pillow pygame pyttsx3
if %errorlevel% NEQ 0 (
    echo [WARNING] Some core dependencies had issues, continuing...
)

echo.
echo [4/5] Installing PyTorch (may take a while)...
%VENV_PYTHON% -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
if %errorlevel% NEQ 0 (
    echo [WARNING] PyTorch installation had issues
    echo [INFO] Trying CPU-only version...
    %VENV_PYTHON% -m pip install torch torchaudio
)

echo.
echo [5/5] Installing Coqui TTS (voice cloning)...
%VENV_PYTHON% -m pip install TTS
if %errorlevel% NEQ 0 (
    echo [WARNING] TTS installation had issues
    echo [INFO] TTS requires Python 3.10-3.11
)

echo.
echo [INFO] Installing remaining dependencies from requirements.txt...
if exist requirements.txt (
    %VENV_PYTHON% -m pip install -r requirements.txt
)

echo.
echo ==========================================
echo [OK] Dependencies installation complete!
echo ==========================================
echo.
echo NOTE: If you see errors above, some packages
echo may not have installed correctly.
echo.
pause
goto :MENU

:RUN_PYTHON
echo.
echo [INFO] Starting AI Humanity...
echo.

:: Use venv python if exists
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe main.py
) else (
    %PYTHON_CMD% main.py
)

if errorlevel 1 (
    echo.
    echo [ERROR] Application crashed or error occurred.
    echo.
    echo If you see "ModuleNotFoundError":
    echo   Run option [4] to install dependencies
    echo.
    echo If you see "TTS" error:
    echo   Make sure you have Python 3.11
    pause
)
goto :MENU

:BUILD_EXE
echo.
echo [INFO] Building EXE with PyInstaller...
echo.

if exist "venv\Scripts\python.exe" (
    set BUILD_PYTHON=venv\Scripts\python.exe
) else (
    set BUILD_PYTHON=%PYTHON_CMD%
)

%BUILD_PYTHON% -m pip install pyinstaller --quiet

if exist build.bat (
    call build.bat
) else (
    %BUILD_PYTHON% -m PyInstaller --onefile --windowed --name=AI_Humanity main.py
)

echo.
echo [INFO] Build complete! Check dist folder.
pause
goto :MENU

:RUN_EXE
echo.
if exist "dist\AI_Humanity.exe" (
    echo [INFO] Starting AI_Humanity.exe...
    start "" "dist\AI_Humanity.exe"
) else (
    echo [ERROR] EXE not found!
    echo Please build it first using option [2].
)
pause
goto :MENU
