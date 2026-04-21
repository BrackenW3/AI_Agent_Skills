# remove-gk-hooks.ps1
# Removes all GitKraken AI hooks from Claude Code settings.json
# Run this on any Windows machine where gk ai hook install was run.
#
# Usage:
#   .\remove-gk-hooks.ps1
#   .\remove-gk-hooks.ps1 -SettingsPath "C:\Users\OtherUser\.claude\settings.json"

param(
    [string]$SettingsPath = "$env:USERPROFILE\.claude\settings.json"
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $SettingsPath)) {
    Write-Host "No Claude settings found at $SettingsPath — nothing to do."
    exit 0
}

# Backup
$backup = "$SettingsPath.bak-$(Get-Date -Format 'yyyyMMdd-HHmm')"
Copy-Item $SettingsPath $backup
Write-Host "Backed up to: $backup"

# Load, remove hooks, save
$settings = Get-Content -Raw $SettingsPath | ConvertFrom-Json

if ($null -eq $settings.hooks) {
    Write-Host "No hooks found in settings — already clean."
    exit 0
}

# Count what we're removing
$hookCount = ($settings.hooks | Get-Member -MemberType NoteProperty).Count
Write-Host "Found $hookCount hook event types — removing all..."

# Remove hooks property
$settings.PSObject.Properties.Remove('hooks')

# Write back with consistent formatting
$settings | ConvertTo-Json -Depth 20 | Set-Content -Path $SettingsPath -Encoding UTF8

Write-Host "Done. Removed $hookCount GitKraken hook entries from $SettingsPath"
Write-Host ""
Write-Host "To re-enable a single hook for GitKraken (if needed):"
Write-Host "  gk ai hook install --host claude-code"
