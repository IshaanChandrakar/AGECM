[CmdletBinding()]
param(
    [switch]$Build
)

$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw 'Install Docker Desktop and reopen PowerShell before running this script.'
    }
    docker compose version
    if ($LASTEXITCODE -ne 0) { throw 'Docker Compose is unavailable.' }
    docker info --format '{{.ServerVersion}}'
    if ($LASTEXITCODE -ne 0) {
        throw 'Start Docker Desktop, wait until the engine is running, then retry.'
    }
    if (-not (Test-Path -LiteralPath '.env')) {
        Copy-Item -LiteralPath '.env.example' -Destination '.env'
        Write-Host 'Created .env with local demo defaults. Review it before using live hardware.'
    }
    docker compose config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Docker Compose configuration is invalid.' }
    if ($Build) {
        docker compose up --build
    } else {
        docker compose up -d
    }
    if ($LASTEXITCODE -ne 0) { throw 'Docker Compose startup failed. Review the output above.' }
} finally {
    Pop-Location
}
