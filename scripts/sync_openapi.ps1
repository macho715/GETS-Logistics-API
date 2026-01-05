# Sync OpenAPI schema from docs to repo root.

$ErrorActionPreference = "Stop"

$Source = "docs/openapi/openapi-gets-api.yaml"
$Target = "openapi-schema.yaml"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

Set-Location $RepoRoot

if (-not (Test-Path $Source)) {
    Write-Host "ERROR: Source file not found: $Source" -ForegroundColor Red
    exit 1
}

Copy-Item $Source $Target -Force

if (-not (Test-Path $Target)) {
    Write-Host "ERROR: Failed to create target file: $Target" -ForegroundColor Red
    exit 1
}

$LineCount = (Get-Content $Target | Measure-Object -Line).Lines
$FileSizeKb = (Get-Item $Target).Length / 1KB
$FileSizeFormatted = "{0:N2} KB" -f $FileSizeKb

Write-Host "Synced $Source -> $Target" -ForegroundColor Green
Write-Host "Lines: $LineCount" -ForegroundColor Gray
Write-Host "Size: $FileSizeFormatted" -ForegroundColor Gray
