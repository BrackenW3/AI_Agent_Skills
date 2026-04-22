# setup-ssh-mesh.ps1
# Sets up bidirectional SSH + Tailscale mesh for Windows 11 machines
# Run as Administrator on EACH machine
# Usage: .\setup-ssh-mesh.ps1 -MachineName "workstation" | "laptop"

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("workstation", "laptop")]
    [string]$MachineName
)

$ErrorActionPreference = "Stop"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host " SSH + Tailscale Mesh Setup" -ForegroundColor Cyan
Write-Host " Machine: $MachineName" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# --- Step 1: Install and Enable OpenSSH Server ---
Write-Host "`n[1/5] Configuring OpenSSH Server..." -ForegroundColor Yellow

$sshCapability = Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'
if ($sshCapability.State -ne 'Installed') {
    Write-Host "  Installing OpenSSH Server..."
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
} else {
    Write-Host "  OpenSSH Server already installed."
}

# Start and enable the service
Set-Service -Name sshd -StartupType Automatic
Start-Service sshd
Write-Host "  OpenSSH Server is running and set to auto-start." -ForegroundColor Green

# Configure firewall
$rule = Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue
if (-not $rule) {
    New-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -DisplayName "OpenSSH Server (sshd)" `
        -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
    Write-Host "  Firewall rule created for SSH (port 22)." -ForegroundColor Green
} else {
    Write-Host "  Firewall rule already exists."
}

# --- Step 2: Configure SSH for key-based auth ---
Write-Host "`n[2/5] Configuring SSH authentication..." -ForegroundColor Yellow

$sshdConfig = "$env:ProgramData\ssh\sshd_config"
$configContent = Get-Content $sshdConfig -Raw

# Enable PubkeyAuthentication
if ($configContent -match '#PubkeyAuthentication yes') {
    $configContent = $configContent -replace '#PubkeyAuthentication yes', 'PubkeyAuthentication yes'
    Set-Content $sshdConfig $configContent
    Write-Host "  Enabled PubkeyAuthentication."
}

# Disable password auth for security (optional - uncomment after keys are set up)
# $configContent = $configContent -replace '#PasswordAuthentication yes', 'PasswordAuthentication no'

Restart-Service sshd
Write-Host "  SSH configured and restarted." -ForegroundColor Green

# --- Step 3: Generate SSH key pair ---
Write-Host "`n[3/5] Setting up SSH keys..." -ForegroundColor Yellow

$sshDir = "$env:USERPROFILE\.ssh"
if (-not (Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
}

$keyFile = "$sshDir\id_ed25519"
if (-not (Test-Path $keyFile)) {
    Write-Host "  Generating ED25519 key pair..."
    ssh-keygen -t ed25519 -C "$MachineName-$(hostname)" -f $keyFile -N '""'
    Write-Host "  Key pair generated at $keyFile" -ForegroundColor Green
} else {
    Write-Host "  SSH key already exists at $keyFile"
}

# Display public key for cross-machine setup
$pubKey = Get-Content "$keyFile.pub"
Write-Host "`n  PUBLIC KEY (copy this to the OTHER machine's authorized_keys):" -ForegroundColor Magenta
Write-Host "  $pubKey" -ForegroundColor White

# --- Step 4: Install Tailscale ---
Write-Host "`n[4/5] Setting up Tailscale..." -ForegroundColor Yellow

$tailscale = Get-Command tailscale -ErrorAction SilentlyContinue
if (-not $tailscale) {
    Write-Host "  Tailscale not found. Installing via winget..."
    winget install --id Tailscale.Tailscale --accept-package-agreements --accept-source-agreements
    Write-Host "  Tailscale installed. Please run 'tailscale up' after setup." -ForegroundColor Yellow
    Write-Host "  Then enable SSH in Tailscale: tailscale up --ssh" -ForegroundColor Yellow
} else {
    Write-Host "  Tailscale is installed."

    # Enable Tailscale SSH
    Write-Host "  Enabling Tailscale SSH..."
    & tailscale up --ssh

    # Get Tailscale IP
    $tsIP = & tailscale ip -4 2>$null
    if ($tsIP) {
        Write-Host "  Tailscale IP: $tsIP" -ForegroundColor Green
    }
}

# --- Step 5: Create SSH config for easy access ---
Write-Host "`n[5/5] Creating SSH config..." -ForegroundColor Yellow

$sshConfig = "$sshDir\config"
$hostnames = @{
    "workstation" = @{ alias = "ws"; desc = "Main workstation" }
    "laptop"      = @{ alias = "laptop"; desc = "i7 laptop" }
}

$otherMachine = if ($MachineName -eq "workstation") { "laptop" } else { "workstation" }
$otherAlias = $hostnames[$otherMachine].alias

$configEntry = @"

# --- $($hostnames[$otherMachine].desc) via Tailscale ---
Host $otherAlias
    HostName $otherAlias  # Replace with Tailscale hostname or IP
    User $env:USERNAME
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3

"@

if (-not (Test-Path $sshConfig) -or -not (Select-String -Path $sshConfig -Pattern "Host $otherAlias" -Quiet)) {
    Add-Content $sshConfig $configEntry
    Write-Host "  SSH config entry added for '$otherAlias'." -ForegroundColor Green
} else {
    Write-Host "  SSH config entry for '$otherAlias' already exists."
}

# --- Summary ---
Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host " Setup Complete for: $MachineName" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run this script on the OTHER machine with -MachineName '$otherMachine'"
Write-Host "  2. Copy each machine's public key to the other's authorized_keys:"
Write-Host "     Add to $sshDir\authorized_keys on the other machine"
Write-Host "  3. Sign into Tailscale on both machines (same account)"
Write-Host "  4. Test: ssh $otherAlias"
Write-Host ""
Write-Host "For cloud agent access:" -ForegroundColor Yellow
Write-Host "  - Tailscale Funnel: tailscale funnel 22"
Write-Host "  - Or use Tailscale API keys for programmatic access"
Write-Host "  - Agents connect via Tailscale hostname: $(hostname).tail[net-name].ts.net"
Write-Host ""
Write-Host "Tailscale Admin Console: https://login.tailscale.com/admin/machines" -ForegroundColor Cyan
