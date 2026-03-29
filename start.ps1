# PowerShell script to start Spotify Clone
# Run with: .\start.ps1

Write-Host "Starting Spotify Clone..." -ForegroundColor Green
Write-Host ""

# Navigate to project directory
Set-Location "D:\spotify_project"

# Check if virtual environment exists
if (!(Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run setup first:" -ForegroundColor Yellow
    Write-Host "  python -m venv venv" -ForegroundColor Cyan
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Cyan
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Check dependencies
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import fastapi, uvicorn, jwt, requests" 2>$null
} catch {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Check database
if (!(Test-Path "music.db")) {
    Write-Host "Initializing database..." -ForegroundColor Yellow
    python database.py
}

# Start backend in new window
Write-Host "Starting backend server..." -ForegroundColor Yellow
$backendScript = @"
cd D:\spotify_project
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript

# Wait a moment
Start-Sleep -Seconds 3

# Start frontend in new window
Write-Host "Starting frontend server..." -ForegroundColor Yellow
$frontendScript = @"
cd D:\spotify_project
python -m http.server 8080
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript

Write-Host ""
Write-Host "Servers starting up..." -ForegroundColor Green
Write-Host "Backend: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Enter to exit this launcher..." -ForegroundColor Gray
Read-Host