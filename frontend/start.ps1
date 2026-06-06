# Start the MathAssistant vanilla frontend on port 3000.
# Backend must already be running on port 8000 (see backend/start.ps1).
Set-Location $PSScriptRoot
Write-Host "Starting frontend at http://localhost:3000"
Write-Host "Press Ctrl+C to stop."
python -m http.server 3000
