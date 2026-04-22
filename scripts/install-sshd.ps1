# install-sshd.ps1 — Right-click > Run with PowerShell as Administrator
# Installs OpenSSH Server, starts it, opens firewall, configures pubkey auth

$ErrorActionPreference = "Stop"
Write-Host "=== Installing OpenSSH Server ===" -ForegroundColor Cyan

# 1. Install
$cap = Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'
if ($cap.State -ne 'Installed') {
    Write-Host "Installing OpenSSH Server..." -ForegroundColor Yellow
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
    Write-Host "Installed." -ForegroundColor Green
} else {
    Write-Host "Already installed." -ForegroundColor Green
}

# 2. Start and enable
Set-Service -Name sshd -StartupType Automatic
Start-Service sshd
Write-Host "sshd running (auto-start)." -ForegroundColor Green

# 3. Firewall
$rule = Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue
if (-not $rule) {
    New-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -DisplayName "OpenSSH SSH" `
        -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
    Write-Host "Firewall rule created." -ForegroundColor Green
} else {
    Write-Host "Firewall rule exists." -ForegroundColor Green
}

# 4. Enable PubkeyAuthentication
$cfg = "$env:ProgramData\ssh\sshd_config"
$content = Get-Content $cfg -Raw
if ($content -match '#PubkeyAuthentication yes') {
    $content = $content -replace '#PubkeyAuthentication yes', 'PubkeyAuthentication yes'
    Set-Content $cfg $content
    Restart-Service sshd
    Write-Host "PubkeyAuthentication enabled." -ForegroundColor Green
}

# 5. Set up authorized_keys for admin users
$adminAuthKeys = "$env:ProgramData\ssh\administrators_authorized_keys"
$userPubKey = "$env:USERPROFILE\.ssh\id_ed25519.pub"
if ((Test-Path $userPubKey) -and -not (Test-Path $adminAuthKeys)) {
    Copy-Item $userPubKey $adminAuthKeys
    icacls $adminAuthKeys /inheritance:r /grant "SYSTEM:F" /grant "Administrators:F" | Out-Null
    Write-Host "Admin authorized_keys configured." -ForegroundColor Green
}

# 6. Show connection info
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.InterfaceAlias -notmatch 'Loopback' -and $_.IPAddress -ne '127.0.0.1'
} | Select-Object -First 1).IPAddress

Write-Host "`n=== Connection Info ===" -ForegroundColor Cyan
Write-Host "  Hostname: $(hostname)" -ForegroundColor White
Write-Host "  IP:       $ip" -ForegroundColor White
Write-Host "  User:     $env:USERNAME" -ForegroundColor White
Write-Host "  PubKey:   $(Get-Content $userPubKey)" -ForegroundColor Magenta
Write-Host "`nTest: ssh $env:USERNAME@$ip" -ForegroundColor Yellow
Write-Host "`nRun this SAME script on the laptop." -ForegroundColor Yellow
Write-Host "Then exchange public keys into each machine's:" -ForegroundColor Yellow
Write-Host "  $env:ProgramData\ssh\administrators_authorized_keys" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to close"
