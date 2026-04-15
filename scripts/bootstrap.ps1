#Requires -Version 5.1
# bootstrap.ps1 — Windows first-time setup
param(
    [string]$Root = "$env:USERPROFILE",
    [string]$Profile = "windows-full"
)
$ErrorActionPreference = 'Stop'
$RegistryRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=== AI Agent Skills Bootstrap (Windows) ===" -ForegroundColor Cyan
Write-Host "Registry : $RegistryRoot"
Write-Host "Root     : $Root"
Write-Host "Profile  : $Profile"
Write-Host ""

# Check prerequisites
Write-Host "-> Checking prerequisites..."
$missing = @()
foreach ($cmd in @('python3','git','node','npx')) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { $missing += $cmd }
}
if ($missing) {
    Write-Host "Missing: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "Install Node.js from https://nodejs.org and Python from https://python.org"
    exit 1
}
Write-Host "  OK All prerequisites present" -ForegroundColor Green

# Find .env
$envCandidates = @(
    "$Root\VSCodespace\.env",
    "$Root\.env",
    "$RegistryRoot\.env.local"
)
$envPath = $envCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $envPath) {
    Write-Host ""
    Write-Host "No .env found. Copy env\template.env to $Root\VSCodespace\.env and fill values." -ForegroundColor Yellow
    exit 0
}
Write-Host "  OK Credentials: $envPath" -ForegroundColor Green

Write-Host ""
& "$PSScriptRoot\sync.ps1" -Root $Root -Profile $Profile

Write-Host ""
Write-Host "Bootstrap complete! Update anytime:" -ForegroundColor Green
Write-Host "  cd $RegistryRoot && git pull && .\scripts\sync.ps1"
