@echo off
echo Starting Spotify Clone...
echo.

cd /d D:\spotify_project

echo Checking virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found! Please run setup first.
    echo Run: python -m venv venv
    echo Then: venv\Scripts\activate && pip install -r requirements.txt
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Checking if dependencies are installed...
python -c "import fastapi, uvicorn, jwt, requests" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo Checking database...
if not exist "music.db" (
    echo Initializing database...
    python database.py
)

echo Starting backend server...
start "Spotify Backend" cmd /k "cd /d D:\spotify_project && call venv\Scripts\activate.bat && python -m uvicorn main:app --reload"

timeout /t 3 /nobreak > nul

echo Starting frontend server...
start "Spotify Frontend" cmd /k "cd /d D:\spotify_project && python -m http.server 8080"

echo.
echo Servers starting up...
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:8080
echo.
echo Press any key to close this window...
pause > nul
