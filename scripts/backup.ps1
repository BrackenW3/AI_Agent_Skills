# ─────────────────────────────────────────────────────────────────────────────
# backup.ps1 — Back up Windows dotfiles and AppData configs
#
# Backs up:  SSH keys, Claude settings, Gemini settings, VSCode settings,
#            .gitconfig, AI_Agent_Skills, and optionally VSCodespace
#
# Destinations (pick one or both):
#   --local PATH    Copy to a local folder (external drive, NAS, etc.)
#   --remote USER@HOST:PATH   Rsync to remote machine over SSH
#   --gdrive        Copy to Google Drive folder (if mapped as a drive letter)
#
# Usage:
#   .\scripts\backup.ps1 --local D:\Backups\windows-config
#   .\scripts\backup.ps1 --remote wbracken@192.168.1.10:/backups/windows
#   .\scripts\backup.ps1 --local D:\Backups --remote user@host:/backups
#   .\scripts\backup.ps1 --local "C:\Users\User\Google Drive\My Drive\Backups\windows-config"
# ─────────────────────────────────────────────────────────────────────────────
param(
    [string]$Local    = "",
    [string]$Remote   = "",
    [switch]$GDrive,
    [string]$GDrivePath = "G:\My Drive\Backups\windows-config",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Root = $env:USERPROFILE
$Timestamp = Get-Date -Format "yyyy-MM-dd"

if ($GDrive -and -not $Local) { $Local = $GDrivePath }

if (-not $Local -and -not $Remote) {
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\scripts\backup.ps1 --local D:\Backups\windows-config"
    Write-Host "  .\scripts\backup.ps1 --remote user@host:/backups/windows"
    Write-Host "  .\scripts\backup.ps1 --gdrive"
    Write-Host "  .\scripts\backup.ps1 --local PATH --dry-run   (preview only)"
    exit 0
}

# ── What to back up ───────────────────────────────────────────────────────────
$Items = @(
    # SSH
    @{ Src = "$Root\.ssh";                           Dest = "ssh";          Note = "SSH keys + config" },

    # CLI configs
    @{ Src = "$Root\.claude";                        Dest = "claude";       Note = "Claude Code settings + skills" },
    @{ Src = "$Root\.claude.json";                   Dest = "claude.json";  Note = "Claude global MCP config" },
    @{ Src = "$Root\.gemini";                        Dest = "gemini";       Note = "Gemini CLI settings" },
    @{ Src = "$Root\.gitconfig";                     Dest = ".gitconfig";   Note = "Global git config" },

    # VSCode
    @{ Src = "$Root\AppData\Roaming\Code\User\settings.json";   Dest = "vscode\settings.json";   Note = "VSCode settings" },
    @{ Src = "$Root\AppData\Roaming\Code\User\keybindings.json"; Dest = "vscode\keybindings.json"; Note = "VSCode keybindings" },
    @{ Src = "$Root\AppData\Roaming\Code\User\snippets";         Dest = "vscode\snippets";         Note = "VSCode snippets" },

    # Claude Desktop
    @{ Src = "$Root\AppData\Roaming\Claude\claude_desktop_config.json"; Dest = "claude-desktop\claude_desktop_config.json"; Note = "Claude Desktop config" },

    # AI Agent Skills repo (already on GitHub but local copy)
    @{ Src = "$Root\AI_Agent_Skills";               Dest = "AI_Agent_Skills"; Note = "AI Agent Skills repo" }
)

# ── IMPORTANT: .env is backed up separately (never to a shared location) ─────
# Uncomment below ONLY for a personal encrypted backup destination:
# @{ Src = "$Root\VSCodespace\.env"; Dest = "env\VSCodespace.env"; Note = "API credentials" },

Write-Host ""
Write-Host "=== Windows Config Backup ===" -ForegroundColor Cyan
Write-Host "Date:    $Timestamp"
if ($Local)  { Write-Host "Local:   $Local" }
if ($Remote) { Write-Host "Remote:  $Remote" }
if ($DryRun) { Write-Host "Mode:    DRY RUN (no changes)" -ForegroundColor Yellow }
Write-Host ""

$Copied = 0
$Skipped = 0
$Errors = 0

foreach ($item in $Items) {
    $src  = $item.Src
    $note = $item.Note

    if (-not (Test-Path $src)) {
        Write-Host "  SKIP  $note ($src not found)" -ForegroundColor DarkGray
        $Skipped++
        continue
    }

    Write-Host "  ->  $note" -ForegroundColor White

    # ── Local copy ────────────────────────────────────────────────────────────
    if ($Local) {
        $dest = Join-Path $Local $item.Dest
        if (-not $DryRun) {
            try {
                $destParent = Split-Path $dest -Parent
                New-Item -ItemType Directory -Force -Path $destParent | Out-Null

                if (Test-Path $src -PathType Container) {
                    # Directory: use robocopy (handles locked files, preserves attrs)
                    $robocopyFlags = @("/E", "/XD", "node_modules", ".git", "__pycache__", ".venv",
                                      "/XF", "*.pyc", "*.log", "/NFL", "/NDL", "/NJH", "/NJS")
                    robocopy $src $dest @robocopyFlags | Out-Null
                } else {
                    Copy-Item -Path $src -Destination $dest -Force
                }
                $Copied++
            } catch {
                Write-Host "    ERROR: $_" -ForegroundColor Red
                $Errors++
            }
        } else {
            Write-Host "    [dry-run] would copy to: $dest" -ForegroundColor DarkYellow
            $Copied++
        }
    }

    # ── Remote rsync ─────────────────────────────────────────────────────────
    if ($Remote) {
        $destPath = "$Remote/$($item.Dest)"
        $rsyncExclude = @("--exclude=node_modules", "--exclude=.git",
                          "--exclude=__pycache__", "--exclude=.venv",
                          "--exclude=*.pyc", "--exclude=*.log")
        if (-not $DryRun) {
            try {
                # rsync via WSL or Git Bash rsync if available
                $rsyncCmd = Get-Command rsync -ErrorAction SilentlyContinue
                if ($rsyncCmd) {
                    & rsync -az --delete @rsyncExclude "$src" "$destPath" 2>&1
                } else {
                    # Fallback: scp for single files
                    if (-not (Test-Path $src -PathType Container)) {
                        & "C:\Windows\System32\OpenSSH\scp.exe" $src "${destPath}"
                    } else {
                        Write-Host "    rsync not found — install via: winget install WinSCP or use WSL" -ForegroundColor Yellow
                    }
                }
            } catch {
                Write-Host "    ERROR: $_" -ForegroundColor Red
                $Errors++
            }
        } else {
            Write-Host "    [dry-run] would rsync to: $destPath" -ForegroundColor DarkYellow
        }
    }
}

# ── Write a manifest ──────────────────────────────────────────────────────────
if ($Local -and -not $DryRun) {
    $manifest = @{
        created   = $Timestamp
        machine   = $env:COMPUTERNAME
        user      = $env:USERNAME
        backed_up = $Items | Where-Object { Test-Path $_.Src } | ForEach-Object { $_.Note }
    } | ConvertTo-Json -Depth 3
    $manifest | Out-File -FilePath (Join-Path $Local "manifest.json") -Encoding utf8
}

Write-Host ""
Write-Host "── Summary ──────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "  Copied:  $Copied"
Write-Host "  Skipped: $Skipped  (source not found)"
if ($Errors -gt 0) {
    Write-Host "  Errors:  $Errors" -ForegroundColor Red
} else {
    Write-Host "  Errors:  0" -ForegroundColor Green
}

if (-not $DryRun) {
    Write-Host ""
    Write-Host "Restore any item with:" -ForegroundColor DarkGray
    Write-Host "  Copy-Item -Recurse -Force 'BACKUP_PATH\ssh' `$env:USERPROFILE\.ssh" -ForegroundColor DarkGray
}
Write-Host ""
