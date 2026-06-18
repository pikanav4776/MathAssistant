# Start the MathAssistant frontend (Vite dev server) on port 3000.
# Backend must already be running on port 8000 (see backend/start.ps1).
Set-Location $PSScriptRoot

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  Write-Error "Node.js/npm is required. Install Node.js 18+ and run this script again."
  exit 1
}

if (-not (Test-Path "node_modules")) {
  Write-Host "Installing npm dependencies..."
  npm install
}

Write-Host "Starting Vite dev server at http://localhost:3000"
Write-Host "Press Ctrl+C to stop."
npm run dev
