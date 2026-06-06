# Start the MathAssistant FastAPI backend on port 8000.
Set-Location $PSScriptRoot
$venvActivate = Join-Path (Split-Path $PSScriptRoot -Parent) ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    . $venvActivate
}
Write-Host "Starting backend at http://127.0.0.1:8000"
Write-Host "Press Ctrl+C to stop."
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
