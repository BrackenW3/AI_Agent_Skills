# Emergency PC Recovery Guide
**Date:** 2026-04-22  
**Machine:** CLX-DESKTOP  
**Problem:** System critically overloaded, UAC elevation appears broken but admin rights are intact

---

## Root Cause (Diagnosed)

Your account `CLX-DESKTOP\User` **IS in the Administrators group**. Admin rights are NOT lost. The reason UAC elevation fails is:

1. **96 node.exe processes** eating 658 MB RAM (Gemini CLI crash loop still active)
2. **3 antivirus products** (Bitdefender + Malwarebytes + Defender) eating ~1.1 GB RAM
3. Every process start/stop triggers triple AV scanning
4. `consent.exe` (the UAC prompt) gets intercepted by all 3 AV products and times out before you can click "Yes"

**Fix strategy:** Reduce load enough that UAC works, then use admin elevation to finish the rest.

---

## Step 1: Kill Node Processes (do this FIRST)

Open a Command Prompt (just regular, not admin) and run:

```
taskkill /F /IM node.exe
```

Wait 10 seconds, then verify:

```
tasklist | find /c "node.exe"
```

Should show 0 or a small number. If processes respawn, close any open Gemini CLI terminal windows first, then re-run the kill command.

**Alternative:** Double-click this file:
```
C:\Users\User\AI_Agent_Skills\scripts\kill-nodes.bat
```

---

## Step 2: Disable Malwarebytes Real-Time Protection

This is the **single biggest performance gain** — removes the second AV scanner from every file operation.

1. Find the **Malwarebytes icon** in the system tray (bottom-right, may need to click the ^ arrow)
2. **Right-click** the Malwarebytes icon
3. Click **Open Malwarebytes**
4. Go to **Settings** (gear icon on left sidebar)
5. Click **Security** tab
6. Toggle OFF: **Real-Time Protection**
7. If it asks "Are you sure?" → click **Yes**
8. If it asks for UAC/admin → see Step 2b below

### Step 2b: If Malwarebytes requires admin to change settings

After killing node processes in Step 1, the system should be less loaded. Try:
1. Right-click the Malwarebytes tray icon
2. If UAC prompt appears → **wait patiently** (may take 15-30 seconds)
3. Click **Yes** when the prompt appears

If UAC still doesn't work after killing node processes, skip to Step 4 (Safe Mode).

---

## Step 3: Test UAC Elevation

After Steps 1 and 2, try running PowerShell as admin:

1. Press **Win key**, type `powershell`
2. Right-click **Windows PowerShell**
3. Click **Run as administrator**
4. Wait for UAC prompt (may take 10-20 seconds even after fixes)
5. Click **Yes**

If this works, run these scripts in the admin PowerShell:

```powershell
# Fix startup items and shell extensions (removes Discord startup, GpgEX right-click)
& "C:\Users\User\AI_Agent_Skills\scripts\fix-startup-admin.bat"

# Fix Windows Search scope (stops indexing game drives, cloud sync folders)
& "C:\Users\User\AI_Agent_Skills\scripts\fix-windows-search.bat"

# Add Bitdefender exclusions for dev tools
$bdExclusions = @(
    "C:\Users\User\AppData\Local\AnthropicClaude",
    "C:\Users\User\.claude",
    "C:\Users\User\AppData\Roaming\npm",
    "C:\Users\User\VSCodespace",
    "C:\Program Files\nodejs\node.exe",
    "C:\nvm4w\nodejs\node.exe"
)
Write-Host "Add these paths as exclusions in Bitdefender:" -ForegroundColor Yellow
$bdExclusions | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
Write-Host "`nOpen Bitdefender > Protection > Antivirus > Settings > Manage Exceptions > Add"
```

---

## Step 4: Safe Mode Recovery (ONLY if Step 3 fails)

If UAC elevation still doesn't work after killing nodes and disabling Malwarebytes:

### Enter Safe Mode:
1. Press **Win + I** to open Settings
2. Go to **System > Recovery**
3. Under "Advanced startup" click **Restart now**
4. Click **Restart now** again to confirm
5. You'll see a blue "Choose an option" screen
6. Click **Troubleshoot > Advanced options > Startup Settings > Restart**
7. Press **4** or **F4** for Safe Mode (or **5/F5** for Safe Mode with Networking)

### In Safe Mode:
Safe Mode only loads essential drivers — no Bitdefender, no Malwarebytes, no Defender real-time. Everything will be fast.

1. Open **Command Prompt** (it should have admin rights in Safe Mode)
2. Run:
```cmd
:: Verify your account is admin
net localgroup Administrators

:: If User is listed (it should be), just run the fix scripts:
powershell -ExecutionPolicy Bypass -File "C:\Users\User\AI_Agent_Skills\scripts\fix-performance-nonadmin.ps1"
"C:\Users\User\AI_Agent_Skills\scripts\fix-startup-admin.bat"
"C:\Users\User\AI_Agent_Skills\scripts\fix-windows-search.bat"

:: Uninstall Malwarebytes entirely (Bitdefender covers everything)
wmic product where "name like '%%Malwarebytes%%'" call uninstall /nointeractive

:: Install SSH server
powershell -ExecutionPolicy Bypass -File "C:\Users\User\AI_Agent_Skills\scripts\install-sshd.ps1"
```

3. Restart normally: `shutdown /r /t 0`

### After Restart:
- System should boot with 5 startup programs instead of 11
- Only Bitdefender running (not triple AV)
- No node.exe crash loops
- UAC should work normally
- Right-click should be fast (<0.5s)
- PowerShell should open in 1-2 seconds

---

## Step 5: Post-Recovery Checklist

After the system is responsive again:

- [ ] Verify Malwarebytes is gone: `tasklist | findstr MBAM`
- [ ] Verify node count is normal: `tasklist | find /c "node.exe"` (expect 15-20)
- [ ] Test UAC: right-click PowerShell → Run as administrator
- [ ] Add Bitdefender exclusions for dev tool paths (see Step 3)
- [ ] Verify Windows Defender is passive: Windows Security → Virus & threat protection
- [ ] Open Indexing Options → remove iCloudDrive, OneDrive, G:\, H:\ from search index
- [ ] Install Google Drive for Desktop (should work once system is responsive)
- [ ] Run SSH server install: `install-sshd.ps1` (needs admin PowerShell)

---

## Expected Results

| Metric | Current (broken) | After fix |
|--------|-----------------|-----------|
| Node.exe processes | 96 | 15-20 |
| AV products | 3 (1.1 GB) | 1 (700 MB) |
| Right-click delay | 3-20s | <0.5s |
| PowerShell startup | 10-30s | 1-2s |
| UAC prompt | Times out | <2s |
| Typing lag | 20-30s | Instant |
| RAM at idle | ~8-10 GB | ~5-6 GB |

---

*Generated 2026-04-22 by Claude | AI_Agent_Skills/docs/performance/recovery-guide.md*
