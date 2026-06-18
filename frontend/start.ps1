# Start the MathAssistant frontend on port 3000.
# Backend must already be running on port 8000 (see backend/start.ps1).
Set-Location $PSScriptRoot

if (Get-Command npm -ErrorAction SilentlyContinue) {
  if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm dependencies..."
    npm install
  }
  Write-Host "Starting Vite dev server at http://localhost:3000"
  Write-Host "Press Ctrl+C to stop."
  npm run dev
} else {
  Write-Host "Node.js/npm not found. Falling back to legacy static server."
  Write-Host "Starting legacy frontend at http://localhost:3000"
  Write-Host "Press Ctrl+C to stop."
  python -m http.server 3000
}
