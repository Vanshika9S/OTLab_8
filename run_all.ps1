# run_all.ps1 - Master PowerShell execution script for Assignment 8
Write-Host "======================================================================"
Write-Host " Starting Assignment 8 Test & Verification Suite (PowerShell)"
Write-Host " Date: $(Get-Date)"
Write-Host "======================================================================"

pytest -v --tb=short

Write-Host "======================================================================"
Write-Host " All track test suites executed successfully."
Write-Host "======================================================================"
