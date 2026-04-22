# ─────────────────────────────────────────────────────────────────────────────
# setup-ssh.ps1 — Windows SSH setup
# Run once on a new Windows machine to configure SSH for GitHub + WSL + Docker
#
# Usage:
#   .\scripts\setup-ssh.ps1
#   .\scripts\setup-ssh.ps1 -KeyName my_key -Comment "work-desktop"
# ─────────────────────────────────────────────────────────────────────────────
param(
    [string]$KeyName = "id_ed25519_wsl",
    [string]$Comment = "$env:USERNAME@$(hostname)"
)

$ErrorActionPreference = "Stop"
$sshDir = "$env:USERPROFILE\.ssh"
$keyPath = "$sshDir\$KeyName"

Write-Host ""
Write-Host "=== Windows SSH Setup ===" -ForegroundColor Cyan

# ── 1. Ensure SSH Agent service is running and set to Automatic ──────────────
Write-Host "`n[1/5] Checking Windows SSH Agent service..."
$svc = Get-Service ssh-agent -ErrorAction SilentlyContinue
if (-not $svc) {
    Write-Warning "OpenSSH not installed. Install via: Settings > Apps > Optional Features > OpenSSH Client"
    exit 1
}
if ($svc.StartType -ne "Automatic") {
    Set-Service ssh-agent -StartupType Automatic
    Write-Host "  Set ssh-agent startup to Automatic"
}
if ($svc.Status -ne "Running") {
    Start-Service ssh-agent
    Write-Host "  Started ssh-agent"
} else {
    Write-Host "  ssh-agent already running"
}

# ── 2. Create .ssh directory if needed ───────────────────────────────────────
Write-Host "`n[2/5] Checking .ssh directory..."
if (-not (Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    Write-Host "  Created $sshDir"
} else {
    Write-Host "  $sshDir exists"
}

# ── 3. Generate key if it doesn't exist ─────────────────────────────────────
Write-Host "`n[3/5] Checking SSH key ($KeyName)..."
if (-not (Test-Path $keyPath)) {
    Write-Host "  Generating new ED25519 key..."
    & "C:\Windows\System32\OpenSSH\ssh-keygen.exe" -t ed25519 -C $Comment -f $keyPath -N '""'
    Write-Host "  Key created: $keyPath"
} else {
    Write-Host "  Key already exists: $keyPath"
}

# ── 4. Add key to agent ──────────────────────────────────────────────────────
Write-Host "`n[4/5] Adding key to SSH agent..."
$loaded = & "C:\Windows\System32\OpenSSH\ssh-add.exe" -l 2>&1
if ($loaded -notmatch [regex]::Escape($KeyName) -and $loaded -notmatch "SHA256") {
    & "C:\Windows\System32\OpenSSH\ssh-add.exe" $keyPath
} else {
    # Check if this specific key is loaded by fingerprint
    $fp = (& "C:\Windows\System32\OpenSSH\ssh-keygen.exe" -l -f "$keyPath.pub" 2>&1) -replace " .*",""
    if ($loaded -match [regex]::Escape($fp.Split(" ")[1] ?? "")) {
        Write-Host "  Key already loaded in agent"
    } else {
        & "C:\Windows\System32\OpenSSH\ssh-add.exe" $keyPath
        Write-Host "  Key added to agent"
    }
}

# ── 5. Set Git to use Windows OpenSSH ────────────────────────────────────────
Write-Host "`n[5/5] Configuring Git to use Windows OpenSSH..."
git config --global core.sshCommand "C:/Windows/System32/OpenSSH/ssh.exe"
Write-Host "  git core.sshCommand set"

# ── Write SSH config if missing ──────────────────────────────────────────────
$configPath = "$sshDir\config"
if (-not (Test-Path $configPath) -or -not (Select-String -Path $configPath -Pattern "github.com" -Quiet)) {
    $configContent = @"

# ── GitHub ────────────────────────────────────────────────────────────────────
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/$KeyName
    AddKeysToAgent yes

# ── WSL ───────────────────────────────────────────────────────────────────────
Host wsl-local
    HostName localhost
    User $env:USERNAME
    IdentityFile ~/.ssh/$KeyName
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null

# ── Docker ────────────────────────────────────────────────────────────────────
Host docker-local
    HostName localhost
    User root
    IdentityFile ~/.ssh/$KeyName
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null

# ── Global defaults ───────────────────────────────────────────────────────────
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ConnectTimeout 10
"@
    Add-Content -Path $configPath -Value $configContent
    Write-Host "`n  SSH config written to $configPath"
}

# ── Show public key + test ────────────────────────────────────────────────────
Write-Host ""
Write-Host "=== Your public key (add to GitHub > Settings > SSH Keys) ===" -ForegroundColor Yellow
Get-Content "$keyPath.pub"

Write-Host ""
Write-Host "Testing GitHub connection..." -ForegroundColor Cyan
$result = & "C:\Windows\System32\OpenSSH\ssh.exe" -T git@github.com 2>&1
if ($result -match "successfully authenticated") {
    Write-Host "GitHub SSH: OK" -ForegroundColor Green
} else {
    Write-Host "GitHub SSH: Not yet authenticated — add the public key above to:" -ForegroundColor Yellow
    Write-Host "  https://github.com/settings/ssh/new"
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
