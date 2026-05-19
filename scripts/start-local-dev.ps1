[CmdletBinding()]
param(
    [switch]$ProvidersOnly,
    [switch]$SkipPull
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

try {
    function Invoke-CheckedCommand {
        param([scriptblock]$Command, [string]$FailureMessage)
        & $Command
        if ($LASTEXITCODE -ne 0) {
            throw $FailureMessage
        }
    }

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker is required for the local provider stack. Install Docker Desktop, then rerun this script."
    }

    if (-not $SkipPull) {
        Invoke-CheckedCommand { docker compose -f docker-compose.local.yml pull } "Docker Compose pull failed."
    }
    Invoke-CheckedCommand { docker compose -f docker-compose.local.yml up -d } "Docker Compose startup failed."

    if (-not $env:CRAWL4AI_BASE_URL) {
        $env:CRAWL4AI_BASE_URL = "http://localhost:11235"
    }
    if (-not $env:SEARXNG_BASE_URL) {
        $env:SEARXNG_BASE_URL = "http://localhost:8080"
    }
    if (-not $env:HOST) {
        $env:HOST = "127.0.0.1"
    }
    if (-not $env:PORT) {
        $env:PORT = "9622"
    }
    if ($env:PORT -eq "9621") {
        throw "PORT=9621 is reserved for Project Theseus. Ariadne local dev uses 9622 by default."
    }

    Write-Host "Crawl4AI: $env:CRAWL4AI_BASE_URL"
    Write-Host "SearXNG: $env:SEARXNG_BASE_URL"
    Write-Host "Ariadne: http://$env:HOST`:$env:PORT"

    if ($ProvidersOnly) {
        Write-Host "Provider stack is running. Start Ariadne separately with the same CRAWL4AI_BASE_URL and SEARXNG_BASE_URL values."
        return
    }

    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw "uv is required to start Ariadne. Install uv, then rerun this script."
    }

    uv run python app.py
}
finally {
    Pop-Location
}