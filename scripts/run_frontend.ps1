# PowerShell script to run the React + Vite frontend development server
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location "$rootDir\frontend"

# Ensure portable node in AppData is on PATH
$nodeDir = "$env:LOCALAPPDATA\Programs\nodejs"
if (Test-Path $nodeDir) {
    $env:Path = "$nodeDir;" + $env:Path
}

Write-Host "Starting SkillBridge AI Frontend on http://localhost:5173..." -ForegroundColor Green
npm run dev
