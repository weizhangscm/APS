# PowerShell script to start the backend server
# Usage: .\start_backend.ps1

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  APS Backend Server Startup Script  " -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check required environment variable from system
if (-not $env:OPENAI_API_KEY) {
    Write-Host "[ERROR] OPENAI_API_KEY is not set in system environment." -ForegroundColor Red
    Write-Host "        Please set it in system/user environment variables and reopen terminal." -ForegroundColor Yellow
    exit 1
}

# Apply safe defaults for optional variables
if (-not $env:OPENAI_BASE_URL) { $env:OPENAI_BASE_URL = "https://api.chataiapi.com/v1" }
if (-not $env:OPENAI_MODEL) { $env:OPENAI_MODEL = "gemini-3-flash-preview" }

Write-Host "[1/3] Environment variables loaded" -ForegroundColor Green
Write-Host "      OPENAI_API_KEY = configured" -ForegroundColor Gray
Write-Host ""

# Check if we're in the correct directory
if (-not (Test-Path "app\main.py")) {
    Write-Host "[ERROR] Not in backend directory!" -ForegroundColor Red
    Write-Host "        Please run: cd backend" -ForegroundColor Yellow
    exit 1
}

Write-Host "[2/3] Directory check passed" -ForegroundColor Green
Write-Host ""

# Check if dependencies are installed
Write-Host "[3/3] Starting uvicorn server..." -ForegroundColor Green
Write-Host "      URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host "      API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
