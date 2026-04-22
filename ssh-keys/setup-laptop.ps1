# Setup SSH keys on Windows 11 Laptop for bidirectional access
# Run in PowerShell: powershell -ExecutionPolicy Bypass -File setup-laptop.ps1

$ErrorActionPreference = "Stop"
Write-Host "=== Windows Laptop SSH Setup ===" -ForegroundColor Cyan

$sshDir = "$env:USERPROFILE\.ssh"
if (-not (Test-Path $sshDir)) { New-Item -ItemType Directory -Path $sshDir -Force | Out-Null }

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$keyDir = Join-Path $scriptDir "laptop"

# Install private key
Copy-Item "$keyDir\laptop_ed25519" "$sshDir\id_ed25519_mesh" -Force
Write-Host "[OK] Private key installed" -ForegroundColor Green

# Install public key
Copy-Item "$keyDir\laptop_ed25519.pub" "$sshDir\id_ed25519_mesh.pub" -Force
Write-Host "[OK] Public key installed" -ForegroundColor Green

# Update authorized_keys (append missing keys)
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
    "desktop" = "# Windows Desktop (CLX-DESKTOP) - fill in HostName"
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
Write-Host "=== NEXT STEPS ===" -ForegroundColor Cyan
Write-Host "1. Edit $sshDir\config and fill in HostName for 'desktop' and 'macbook'" -ForegroundColor White
Write-Host "2. Install OpenSSH Server (Admin PowerShell):" -ForegroundColor White
Write-Host "   Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0" -ForegroundColor Yellow
Write-Host "   Start-Service sshd; Set-Service sshd -StartupType Automatic" -ForegroundColor Yellow
Write-Host "3. Copy authorized_keys for admin users:" -ForegroundColor White
Write-Host "   Copy-Item $sshDir\authorized_keys $env:ProgramData\ssh\administrators_authorized_keys" -ForegroundColor Yellow
Write-Host "   icacls $env:ProgramData\ssh\administrators_authorized_keys /inheritance:r /grant 'SYSTEM:F' /grant 'Administrators:F'" -ForegroundColor Yellow
Write-Host "4. Test: ssh desktop   and   ssh macbook" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to close"
