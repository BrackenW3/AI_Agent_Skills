# setup-ssh-simple.ps1
# Simple bidirectional SSH between two Windows 11 machines
# Run as Administrator on EACH machine
# Usage: .\setup-ssh-simple.ps1

param(
    [switch]$SkipKeyGen
)

$ErrorActionPreference = "Stop"

Write-Host "=== Simple Bidirectional SSH Setup ===" -ForegroundColor Cyan

# 1. Install OpenSSH Server
Write-Host "`n[1/3] OpenSSH Server..." -ForegroundColor Yellow
$ssh = Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'
if ($ssh.State -ne 'Installed') {
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
    Write-Host "  Installed." -ForegroundColor Green
} else {
    Write-Host "  Already installed." -ForegroundColor Green
}

Set-Service -Name sshd -StartupType Automatic
Start-Service sshd

$rule = Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue
if (-not $rule) {
    New-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -DisplayName "OpenSSH SSH" `
        -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
}
Write-Host "  sshd running, firewall open." -ForegroundColor Green

# 2. Generate key
Write-Host "`n[2/3] SSH Key..." -ForegroundColor Yellow
$keyFile = "$env:USERPROFILE\.ssh\id_ed25519"
if (-not (Test-Path "$env:USERPROFILE\.ssh")) {
    New-Item -ItemType Directory -Path "$env:USERPROFILE\.ssh" -Force | Out-Null
}

if (-not $SkipKeyGen -and -not (Test-Path $keyFile)) {
    ssh-keygen -t ed25519 -C "$(hostname)" -f $keyFile -N '""'
    Write-Host "  Generated: $keyFile" -ForegroundColor Green
} elseif (Test-Path $keyFile) {
    Write-Host "  Key exists: $keyFile" -ForegroundColor Green
} else {
    Write-Host "  Skipped." -ForegroundColor Yellow
}

# 3. Show info
Write-Host "`n[3/3] Connection Info" -ForegroundColor Yellow

$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.InterfaceAlias -notmatch 'Loopback' -and $_.IPAddress -ne '127.0.0.1'
} | Select-Object -First 1).IPAddress

$pubKey = if (Test-Path "$keyFile.pub") { Get-Content "$keyFile.pub" } else { "(no key)" }

Write-Host "`n  Hostname: $(hostname)" -ForegroundColor White
Write-Host "  IP:       $ip" -ForegroundColor White
Write-Host "  User:     $env:USERNAME" -ForegroundColor White
Write-Host "`n  Public Key:" -ForegroundColor Magenta
Write-Host "  $pubKey"

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "  1. Run this same script on the OTHER machine"
Write-Host "  2. Copy this public key to the other machine's:"
Write-Host "     $env:USERPROFILE\.ssh\authorized_keys"
Write-Host "  3. Copy the other machine's public key HERE to:"
Write-Host "     $env:USERPROFILE\.ssh\authorized_keys"
Write-Host "  4. Test: ssh $env:USERNAME@<other-machine-ip>"
Write-Host ""

# For admin users, fix authorized_keys location
$adminAuthKeys = "$env:ProgramData\ssh\administrators_authorized_keys"
if ((whoami) -match 'Administrators' -or (net localgroup Administrators 2>$null | Select-String $env:USERNAME)) {
    Write-Host "  NOTE: You're an admin. Keys go in:" -ForegroundColor Yellow
    Write-Host "  $adminAuthKeys" -ForegroundColor Yellow
    Write-Host "  Run: icacls `"$adminAuthKeys`" /inheritance:r /grant `"SYSTEM:F`" /grant `"Administrators:F`""
}
