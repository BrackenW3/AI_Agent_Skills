# Setup SSH keys on Windows Desktop (CLX-DESKTOP) for bidirectional access
# Run in PowerShell: powershell -ExecutionPolicy Bypass -File setup-desktop.ps1
# NOTE: Steps 2-3 in NEXT STEPS require Admin elevation

$ErrorActionPreference = "Stop"
Write-Host "=== Windows Desktop SSH Setup ===" -ForegroundColor Cyan

$sshDir = "$env:USERPROFILE\.ssh"
if (-not (Test-Path $sshDir)) { New-Item -ItemType Directory -Path $sshDir -Force | Out-Null }

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$keyDir = Join-Path $scriptDir "desktop"

# Install mesh private key (separate from existing id_ed25519)
Copy-Item "$keyDir\desktop_ed25519" "$sshDir\id_ed25519_mesh" -Force
Write-Host "[OK] Mesh private key installed (id_ed25519_mesh)" -ForegroundColor Green

# Install public key
Copy-Item "$keyDir\desktop_ed25519.pub" "$sshDir\id_ed25519_mesh.pub" -Force
Write-Host "[OK] Public key installed" -ForegroundColor Green

# Update user authorized_keys (append missing keys)
$authKeysPath = "$sshDir\authorized_keys"
$newKeys = Get-Content "$keyDir\authorized_keys"
if (Test-Path $authKeysPath) {
    $existing = Get-Content $authKeysPath
    foreach ($key in $newKeys) {
        if ($existing -notcontains $key) {
            Add-Content -Path $authKeysPath -Value $key
        }
    }
} else {
    Copy-Item "$keyDir\authorized_keys" $authKeysPath
}
Write-Host "[OK] authorized_keys updated (all 3 machines)" -ForegroundColor Green

# Update SSH config
$configPath = "$sshDir\config"
if (-not (Test-Path $configPath)) { New-Item -ItemType File -Path $configPath -Force | Out-Null }
$config = Get-Content $configPath -Raw -ErrorAction SilentlyContinue

$hosts = @{
    "laptop"  = "# Windows Laptop (i7) - fill in HostName"
    "macbook" = "# MacBook - fill in HostName"
}

foreach ($hostName in $hosts.Keys) {
    if ($config -notmatch "Host $hostName") {
        $entry = @"

$($hosts[$hostName])
Host $hostName
    IdentityFile ~\.ssh\id_ed25519_mesh
    User User
    StrictHostKeyChecking accept-new

"@
        Add-Content -Path $configPath -Value $entry
        Write-Host "[OK] Added SSH config: $hostName" -ForegroundColor Green
    } else {
        Write-Host "[SKIP] SSH config '$hostName' already exists" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== NEXT STEPS (need Admin for sshd) ===" -ForegroundColor Cyan
Write-Host "1. Fill in HostName in $sshDir\config for 'laptop' and 'macbook'" -ForegroundColor White
Write-Host "2. Run install-sshd.ps1 as Admin (installs OpenSSH Server):" -ForegroundColor White
Write-Host "   C:\Users\User\AI_Agent_Skills\scripts\install-sshd.ps1" -ForegroundColor Yellow
Write-Host "3. Copy authorized_keys for admin SSH access:" -ForegroundColor White
Write-Host "   Copy-Item $sshDir\authorized_keys $env:ProgramData\ssh\administrators_authorized_keys" -ForegroundColor Yellow
Write-Host "   icacls $env:ProgramData\ssh\administrators_authorized_keys /inheritance:r /grant 'SYSTEM:F' /grant 'Administrators:F'" -ForegroundColor Yellow
Write-Host "4. Test: ssh laptop   and   ssh macbook" -ForegroundColor White
Write-Host ""
Write-Host "NOTE: Your existing id_ed25519 key is untouched. The mesh key is id_ed25519_mesh." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to close"
