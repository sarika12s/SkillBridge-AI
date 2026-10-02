# PowerShell script to run the FastAPI backend server
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

Write-Host "Activating Python virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

Write-Host "Starting SkillBridge AI FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
Write-Host "Interactive Swagger documentation: http://localhost:8000/api/v1/docs" -ForegroundColor Yellow

Set-Location "$rootDir\backend"
& "$rootDir\venv\Scripts\uvicorn.exe" app.main:app --reload --host 0.0.0.0 --port 8000
