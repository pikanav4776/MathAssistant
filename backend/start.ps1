# Local dev: FastAPI with auto-reload on 127.0.0.1:8000.
# Production (Render) uses render.yaml: uvicorn main:app --host 0.0.0.0 --port $PORT
Set-Location $PSScriptRoot
$venvActivate = Join-Path (Split-Path $PSScriptRoot -Parent) ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    . $venvActivate
}
Write-Host "Starting backend at http://127.0.0.1:8000"
Write-Host "Press Ctrl+C to stop."
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
