@echo off
echo Spotify Clone - Troubleshooting Script
echo ======================================
echo.

cd /d D:\spotify_project

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)
echo.

echo Checking virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment activation script not found!
    echo Try deleting venv folder and running: python -m venv venv
    pause
    exit /b 1
)
echo Virtual environment found.
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo Checking dependencies...
python -c "import fastapi, uvicorn, jwt, requests" 2>nul
if errorlevel 1 (
    echo Installing missing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
)
echo Dependencies OK.
echo.

echo Checking database...
if not exist "music.db" (
    echo Initializing database...
    python database.py
    if errorlevel 1 (
        echo ERROR: Failed to initialize database!
        pause
        exit /b 1
    )
)
echo Database OK.
echo.

echo Testing backend server...
timeout /t 1 /nobreak > nul
start /b uvicorn main:app --host 127.0.0.1 --port 8000 > backend_test.log 2>&1
timeout /t 3 /nobreak > nul
taskkill /f /im uvicorn.exe >nul 2>&1

if exist "backend_test.log" (
    findstr /c:"Application startup complete" backend_test.log >nul
    if errorlevel 1 (
        echo ERROR: Backend server failed to start!
        echo Check backend_test.log for details.
        pause
        exit /b 1
    ) else (
        echo Backend server OK.
    )
    del backend_test.log
) else (
    echo ERROR: Could not test backend server!
)
echo.

echo All checks passed! You can now run start.bat
echo.
pause