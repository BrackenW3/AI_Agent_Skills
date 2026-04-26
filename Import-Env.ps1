# Import-Env.ps1 — Set all env vars as Windows User Environment Variables
# Run from: C:\Users\User\VSCodespace\
# Usage: powershell -ExecutionPolicy Bypass -File Import-Env.ps1

$envFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envFile)) {
    $envFile = Join-Path $PSScriptRoot "master.env"
}

if (-not (Test-Path $envFile)) {
    Write-Error "No .env or master.env found in $PSScriptRoot"
    exit 1
}

$set = 0
$skip = 0

Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    # Skip comments and empty lines
    if ($line -eq "" -or $line.StartsWith("#")) { return }
    
    # Parse KEY=VALUE
    $idx = $line.IndexOf("=")
    if ($idx -lt 1) { return }
    
    $key = $line.Substring(0, $idx).Trim()
    $val = $line.Substring($idx + 1).Trim()
    
    # Skip placeholder values
    if ($val -eq "NEEDS_SETTING" -or $val -eq "" -or $val -eq "REPLACE_ME") {
        $skip++
        Write-Host "SKIP: $key (needs setting)" -ForegroundColor Yellow
        return
    }
    
    # Set as User environment variable
    [Environment]::SetEnvironmentVariable($key, $val, "User")
    $set++
    Write-Host "SET:  $key" -ForegroundColor Green
}

Write-Host ""
Write-Host "Done: $set variables set, $skip skipped" -ForegroundColor Cyan
Write-Host "Restart your terminal for changes to take effect." -ForegroundColor Cyan
