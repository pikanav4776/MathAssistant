# MathAssistant API smoke test — run against local, staging, or production.
# Usage:
#   .\scripts\smoke_test_api.ps1
#   .\scripts\smoke_test_api.ps1 -ApiBase https://mathassistant-api-staging.onrender.com

param(
    [string]$ApiBase = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"
$base = $ApiBase.TrimEnd("/")

function Invoke-Json {
    param(
        [string]$Method,
        [string]$Path,
        [object]$Body = $null,
        [hashtable]$Headers = @{}
    )
    $uri = "$base$Path"
    $params = @{
        Uri         = $uri
        Method      = $Method
        Headers     = $Headers
        ContentType = "application/json"
    }
    if ($null -ne $Body) {
        $params.Body = ($Body | ConvertTo-Json -Compress)
    }
    return Invoke-RestMethod @params
}

function Assert-Step {
    param([string]$Name, [scriptblock]$Action)
    Write-Host "  $Name..." -NoNewline
    & $Action
    Write-Host " OK"
}

Write-Host "MathAssistant API smoke test"
Write-Host "  Base URL: $base"
Write-Host ""

Assert-Step "GET /health" {
    $health = Invoke-Json GET "/health"
    if ($health.status -ne "ok") { throw "unexpected health response" }
}

Assert-Step "GET /ready" {
    $ready = Invoke-Json GET "/ready"
    if ($ready.status -ne "ok" -or $ready.db -ne "connected") {
        throw "database not ready"
    }
}

Assert-Step "GET /problems/starter" {
    $starters = Invoke-Json GET "/problems/starter"
    if ($starters.Count -lt 1) { throw "no starter problems" }
}

$sessionId = $null
Assert-Step "POST /start-session (guest)" {
    $start = Invoke-Json POST "/start-session" @{ problem_expression = "2(x+3)" }
    if (-not $start.session_id) { throw "missing session_id" }
    $script:sessionId = $start.session_id
}

Assert-Step "POST /submit-step (correct)" {
    $step = Invoke-Json POST "/submit-step" @{
        session_id = $sessionId
        step       = "2*x+6"
    }
    if (-not $step.is_equivalent) { throw "expected equivalent step" }
}

Assert-Step "GET /session/{id}" {
    $session = Invoke-Json GET "/session/$sessionId"
    if ($session.session_id -ne $sessionId) { throw "session mismatch" }
}

Assert-Step "POST /session/{id}/finalize" {
    $finalize = Invoke-Json POST "/session/$sessionId/finalize" @{
        completed         = $true
        revealed_solution = $false
    }
    if (-not $finalize.summarized) { throw "finalize failed" }
}

Write-Host ""
Write-Host "All smoke checks passed."
