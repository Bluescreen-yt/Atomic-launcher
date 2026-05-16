@echo off
REM =============================================
REM [RUN]_WINDOWS_UPDATER.bat (Embedded Python)
REM =============================================

:: Force the script to run from its own directory (The Root Folder)
cd /d "%~dp0"

REM --- SET EMBEDDED PYTHON PATHS ---
set "EMBEDDED_DIR=%~dp0windows_python_3.14.5"
set "PYTHON=%EMBEDDED_DIR%\python.exe"
set "PIP=%EMBEDDED_DIR%\Scripts\pip.exe"

REM --- FIX IMPORT PATHS FOR PYTHON ---
:: This tells Python to look inside the 'code' folder for modules like settings.py
set "PYTHONPATH=%~dp0code"

REM --- ENSURE PIP IS INSTALLED IN EMBEDDED PYTHON ---
if not exist "%PIP%" (
    echo [INFO] Pip not found in embedded Python. Installing pip...
    
    REM Download get-pip.py safely via curl
    curl -sL https://bootstrap.pypa.io/get-pip.py -o "%EMBEDDED_DIR%\get-pip.py"
    
    REM Run it using your embedded python
    "%PYTHON%" "%EMBEDDED_DIR%\get-pip.py" --no-warn-script-location
    
    REM Clean up the installer script
    del "%EMBEDDED_DIR%\get-pip.py"
    
    if not exist "%PIP%" (
        echo [ERROR] Failed to install pip in the embedded environment.
        pause
        exit /b 1
    )
)

REM --- SPRAWDZENIE INTERNETU ---
ping -n 1 8.8.8.8 >nul
IF %ERRORLEVEL% EQU 0 (
    echo Internet connection found. Checking for updates...

    REM --- PRÓBA AKTUALIZACJI PRZEZ GIT ---
    where git >nul 2>nul
    IF %ERRORLEVEL% EQU 0 (
        if exist ".git" (
            echo Updating via Git...
            git pull origin main
        )
    ) ELSE (
        REM --- OPCJA DLA UŻYTKOWNIKA BEZ GIT (POBIERANIE ZIP) ---
        echo Git not found. Downloading latest version via CURL...

        set "REPO_URL=https://github.com/mironczuk-dar/Atomic-launcher/archive/refs/heads/main.zip"

        curl -L -o update.zip "%REPO_URL%"

        if exist "update.zip" (
            echo Extracting updates...
            powershell -Command "Expand-Archive -Path 'update.zip' -DestinationPath 'temp_update' -Force"
            
            REM Excluding the python folder from being overwritten if it exists in the repo
            xcopy /s /e /y /exclude:%~dp0exclude_list.txt "temp_update\*-main\*" "." >nul 2>nul
            
            REM Fallback standard xcopy if no exclusion file exists
            if %ERRORLEVEL% NEQ 0 xcopy /s /e /y "temp_update\*-main\*" "."
            
            rd /s /q "temp_update"
            del update.zip
            echo Update complete!
        )
    )

    REM --- AKTUALIZACJA PAKIETÓW PYTHON ---
    echo Checking Python packages...
    "%PYTHON%" -m pip install --upgrade pip >nul
    "%PYTHON%" -m pip install --upgrade pygame-ce pytmx opencv-python >nul
) ELSE (
    echo No internet connection. Starting in offline mode.
)

REM --- URUCHAMIANIE GRY ---
echo Starting Atomic Launcher...

:: We stay in the root directory, pointing directly to code\main.py. 
:: The PYTHONPATH we set above handles the 'settings' import flawlessly.
"%PYTHON%" code\main.py

pause