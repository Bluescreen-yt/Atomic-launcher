@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM --- ROOT DIRECTORY ---
cd /d "%~dp0"
set "ROOT=%~dp0"

REM --- ABSOLUTE PATHS ---
set "CODE_DIR=%ROOT%src"
set "EMBEDDED_DIR=%ROOT%windows_python"
set "PYTHON=python.exe"

REM --- CHECK PYTHON EXISTS ---
if not exist "%EMBEDDED_DIR%\%PYTHON%" (
    echo.
    echo [ERROR] Embedded Python not found:
    echo %EMBEDDED_DIR%\%PYTHON%
    echo.
    pause
    exit /b 1
)

REM =============================================
REM ENSURE PIP EXISTS (NATIVE RUNTIME CHECK)
REM =============================================
echo Checking embedded pip...

REM Temporarily move directly into the python directory to satisfy internal pathing rules
cd /d "%EMBEDDED_DIR%"

%PYTHON% -m pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Embedded pip could not be loaded via the script.
    echo Expected layout location: %EMBEDDED_DIR%\Lib\site-packages\pip
    echo.
    cd /d "%ROOT%"
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

    REM Move back to root to perform file adjustments safely
    cd /d "%ROOT%"

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
    
    REM Return to the embedded folder so Python finds its core C modules natively
    cd /d "%EMBEDDED_DIR%"
    
    %PYTHON% -m pip install --upgrade pip --disable-pip-version-check
    %PYTHON% -m pip install --upgrade pygame-ce pytmx opencv-python --disable-pip-version-check

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

REM Transition to source directory to kick off main loop
cd /d "%CODE_DIR%"
"..\\windows_python\\%PYTHON%" main.py

echo.
echo Application closed.
pause