@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM --- ROOT DIRECTORY ---
cd /d "%~dp0"
set "ROOT=%~dp0"

REM --- FORCE CLEAN ABSOLUTE PATHS ---
set "CODE_DIR=%ROOT%src"
set "EMBEDDED_DIR=%ROOT%windows_python"
set "PYTHON=%EMBEDDED_DIR%\python.exe"

REM --- FORCE PYTHON TO REGISTER ITS OWN CORE DIRECTORIES ---
REM This tells Python exactly where its C-extensions (_socket) and packages live,
REM no matter what folder the command prompt is currently sitting in.
set "PYTHONPATH=%CODE_DIR%;%EMBEDDED_DIR%;%EMBEDDED_DIR%\Lib\site-packages"

REM --- CHECK PYTHON ---
if not exist "%PYTHON%" (
    echo.
    echo [ERROR] Embedded Python not found:
    echo %PYTHON%
    echo.
    pause
    exit /b 1
)

REM =============================================
REM ENABLE SITE PACKAGES FOR EMBEDDED PYTHON
REM =============================================
for %%f in ("%EMBEDDED_DIR%\python*._pth") do (
    findstr /C:"import site" "%%f" >nul
    if errorlevel 1 (
        echo import site>>"%%f"
    )
)

REM =============================================
REM ENSURE PIP EXISTS (PRE-INSTALLED CHECK)
REM =============================================
echo Checking embedded pip...

"%PYTHON%" -m pip --version >nul 2>&1 || (
    echo.
    echo [ERROR] Embedded pip could not be loaded via the script.
    echo Expected layout location: %EMBEDDED_DIR%\Lib\site-packages\pip
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] Embedded pip detected!

REM =============================================
REM INTERNET CHECK
REM =============================================
ping -n 1 8.8.8.8 >nul

IF %ERRORLEVEL% EQU 0 (
    echo Internet connection found.
    echo Checking for updates...

    REM =========================================
    REM GIT UPDATE
    REM =========================================
    where git >nul 2>nul
    IF %ERRORLEVEL% EQU 0 (
        if exist ".git" (
            echo Updating via Git...
            git pull origin main
        )
    ) ELSE (
        REM =====================================
        REM ZIP UPDATE
        REM =====================================
        echo Git not found.
        echo Downloading latest version...
        set "ZIP_URL=https://github.com/mironczuk-dar/Atomic-launcher/archive/refs/heads/main.zip"
        curl -L -o update.zip "%ZIP_URL%"
        if exist "update.zip" (
            echo Extracting update...
            powershell -Command "Expand-Archive -Path 'update.zip' -DestinationPath 'temp_update' -Force"
            for /d %%d in ("temp_update\*") do (
                xcopy "%%d\*" "%ROOT%" /s /e /y /i >nul
            )
            rd /s /q "temp_update"
            del update.zip
            echo Update complete.
        )
    )

    REM =========================================
    REM PYTHON PACKAGES
    REM =========================================
    echo Updating Python packages...
    
    REM Force pip to run with explicit pathing mapping
    "%PYTHON%" -m pip install --upgrade pip --disable-pip-version-check
    "%PYTHON%" -m pip install --upgrade pygame-ce pytmx opencv-python --disable-pip-version-check

) ELSE (
    echo No internet connection.
    echo Starting in offline mode.
)

REM =============================================
REM START APPLICATION
REM =============================================
echo.
echo Starting Atomic Launcher...
echo.

cd /d "%CODE_DIR%"
"%PYTHON%" main.py

echo.
echo Application closed.
pause