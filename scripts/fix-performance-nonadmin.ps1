# fix-performance-nonadmin.ps1
# Fixes everything possible WITHOUT admin elevation
# Double-click to run, or: powershell -ExecutionPolicy Bypass -File fix-performance-nonadmin.ps1

$ErrorActionPreference = "Continue"
Write-Host "=== Performance Fix (No Admin Required) ===" -ForegroundColor Cyan
Write-Host ""

# ── 1. Kill ALL node.exe processes ──────────────────────────────────────────
Write-Host "[1/6] Killing node.exe processes..." -ForegroundColor Yellow
$before = (Get-Process node -EA 0 | Measure-Object).Count
if ($before -gt 0) {
    # Use taskkill which is faster than Stop-Process for bulk kills
    & "$env:SystemRoot\System32\taskkill.exe" /F /IM node.exe 2>$null
    Start-Sleep -Seconds 3
    $after = (Get-Process node -EA 0 | Measure-Object).Count
    Write-Host "  Killed $($before - $after) of $before node processes. Remaining: $after" -ForegroundColor Green
} else {
    Write-Host "  No node.exe processes found." -ForegroundColor Green
}

# ── 2. Kill Gemini CLI if running ───────────────────────────────────────────
Write-Host "[2/6] Checking for Gemini CLI crash loop..." -ForegroundColor Yellow
$geminiNodes = Get-CimInstance Win32_Process -Filter "Name='node.exe'" -EA 0 |
    Where-Object { $_.CommandLine -match 'gemini' }
if ($geminiNodes) {
    $geminiNodes | ForEach-Object {
        & "$env:SystemRoot\System32\taskkill.exe" /F /PID $_.ProcessId 2>$null
    }
    Write-Host "  Killed $($geminiNodes.Count) Gemini CLI processes." -ForegroundColor Green
} else {
    Write-Host "  No Gemini CLI crash loop detected." -ForegroundColor Green
}

# ── 3. Remove startup items (HKCU — no admin needed) ───────────────────────
Write-Host "[3/6] Cleaning startup items (current user)..." -ForegroundColor Yellow
$startupPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$toRemove = @("Steam", "GogGalaxy", "GalaxyClient", "JetBrains Toolbox",
              "Docker Desktop", "com.squirrel.Teams.Teams", "FoxitPhantomPDF",
              "Foxit Reader Tray")

foreach ($item in $toRemove) {
    $val = Get-ItemProperty -Path $startupPath -Name $item -EA SilentlyContinue
    if ($val) {
        Remove-ItemProperty -Path $startupPath -Name $item -EA SilentlyContinue
        Write-Host "  Removed: $item" -ForegroundColor Green
    }
}
Write-Host "  Startup cleanup complete." -ForegroundColor Green

# ── 4. Disable Gemini CLI auto-MCP to prevent respawn ──────────────────────
Write-Host "[4/6] Fixing Gemini CLI config..." -ForegroundColor Yellow
$geminiSettings = "$env:USERPROFILE\.gemini\settings.json"
if (Test-Path $geminiSettings) {
    $content = Get-Content $geminiSettings -Raw -EA 0
    if ($content -match 'z-?ai|zai-mcp') {
        Write-Host "  WARNING: Gemini config still has z-ai/zai-mcp entries!" -ForegroundColor Red
        Write-Host "  Edit $geminiSettings and remove the z-ai MCP server entry." -ForegroundColor Red
    } else {
        Write-Host "  Gemini config looks clean (no z-ai entries)." -ForegroundColor Green
    }
} else {
    Write-Host "  No Gemini settings file found." -ForegroundColor Green
}

# ── 5. Clear temp files that AV scans repeatedly ───────────────────────────
Write-Host "[5/6] Clearing temp directories..." -ForegroundColor Yellow
$tempDirs = @("$env:TEMP", "$env:LOCALAPPDATA\Temp")
$cleared = 0
foreach ($dir in $tempDirs) {
    if (Test-Path $dir) {
        $old = Get-ChildItem $dir -Recurse -File -EA 0 | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) }
        $cleared += $old.Count
        $old | Remove-Item -Force -EA SilentlyContinue
    }
}
Write-Host "  Removed $cleared temp files older than 7 days." -ForegroundColor Green

# ── 6. Report current state ────────────────────────────────────────────────
Write-Host ""
Write-Host "[6/6] Current system state:" -ForegroundColor Yellow

$nodeCount = (Get-Process node -EA 0 | Measure-Object).Count
$totalRAM = [math]::Round((Get-Process | Measure-Object WorkingSet -Sum).Sum / 1GB, 1)
$avProcs = Get-Process -Name MBAMService, Malwarebytes, MbamBgNativeMsg, bdservicehost, bdagent, MsMpEng, MpDefenderCoreService -EA 0
$avRAM = [math]::Round(($avProcs | Measure-Object WorkingSet -Sum).Sum / 1MB, 0)

Write-Host "  Node.exe count:    $nodeCount" -ForegroundColor White
Write-Host "  Total RAM in use:  $totalRAM GB" -ForegroundColor White
Write-Host "  AV processes RAM:  $avRAM MB" -ForegroundColor White
Write-Host "  AV products found:" -ForegroundColor White
if (Get-Process bdservicehost -EA 0) { Write-Host "    - Bitdefender (KEEP)" -ForegroundColor Green }
if (Get-Process MBAMService -EA 0) { Write-Host "    - Malwarebytes (DISABLE REAL-TIME!)" -ForegroundColor Red }
if (Get-Process MsMpEng -EA 0) { Write-Host "    - Windows Defender (should be passive)" -ForegroundColor Yellow }

Write-Host ""
Write-Host "=== MANUAL STEPS STILL NEEDED ===" -ForegroundColor Cyan
Write-Host "1. Open Malwarebytes > Settings > Security > toggle OFF Real-Time Protection" -ForegroundColor White
Write-Host "2. After step 1: try 'Run as Administrator' on PowerShell" -ForegroundColor White
Write-Host "   If UAC prompt appears and works, run:" -ForegroundColor White
Write-Host "   C:\Users\User\AI_Agent_Skills\scripts\fix-startup-admin.bat" -ForegroundColor Yellow
Write-Host "   C:\Users\User\AI_Agent_Skills\scripts\fix-windows-search.bat" -ForegroundColor Yellow
Write-Host "   C:\Users\User\AI_Agent_Skills\scripts\install-sshd.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. If UAC still fails, use Safe Mode recovery (see recovery-guide.md)" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to close"
