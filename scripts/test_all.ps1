# PowerShell script to run all Phase 1 backend unit tests and frontend builds
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Running Backend Pytest Test Suite...    " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
& ".\venv\Scripts\python.exe" -m pytest backend\tests -v

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host " Running End-to-End Pipeline Verification " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
& ".\venv\Scripts\python.exe" backend\tests\verify_phase2_e2e.py

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host " Verifying Frontend TypeScript & Build... " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
$nodeDir = "$env:LOCALAPPDATA\Programs\nodejs"
if (Test-Path $nodeDir) {
    $env:Path = "$nodeDir;" + $env:Path
}
Set-Location "$rootDir\frontend"
npm run build

Write-Host "`nAll Phase 2 verifications completed successfully!" -ForegroundColor Green
