# Stop iCloud → Google Drive local download on i9

## What's Happening
iCloud Drive is syncing to a local folder on i9, then something 
(possibly the cloud indexer or manual setup) is re-uploading to Google Drive.
This runs continuously and wastes disk space.

## Does it run if PC is off?
The local sync STOPS when i9 is off — iCloud only syncs to local when Windows is running.
The Google Drive upload also stops. Nothing cloud-to-cloud happens automatically unless
there's a cloud job (GitHub Actions, n8n workflow) doing it.

## Fix Option 1: Stop iCloud syncing locally (recommended)
In iCloud for Windows:
1. Open iCloud for Windows (system tray)
2. Click Options next to iCloud Drive
3. Uncheck any folders you don't need locally
4. Or: Disable iCloud Drive sync entirely

This keeps your iCloud files in iCloud — just not downloaded locally.

## Fix Option 2: Stop the Google Drive re-upload
If there's an n8n workflow or script doing the upload:
1. Check n8n for any "iCloud upload to Google Drive" workflows — pause them
2. Check Task Scheduler on i9: `Get-ScheduledTask | Where-Object {$_.TaskName -like "*drive*" -or $_.TaskName -like "*icloud*"}`
3. Check startup apps: `Get-ItemProperty HKCU:\Software\Microsoft\Windows\CurrentVersion\Run`

## Fix Option 3: Use cloud-to-cloud (correct long-term)
The cloud_indexer.py in your repo is built to index Google Drive directly via API
without downloading locally. Once set up:
- Files stay in Google Drive
- Indexer reads metadata via API
- No local copy, no re-upload
- Works whether i9 is on or off (runs on Azure/GitHub Actions)

Needs: GDRIVE_SERVICE_ACCOUNT_JSON secret set in GitHub secrets

## Immediate stop (i9 PowerShell)
```powershell
# Stop iCloud sync temporarily
Stop-Process -Name "iCloudDrive" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "iCloud" -Force -ErrorAction SilentlyContinue

# Check what's uploading to Google Drive
Get-Process | Where-Object {$_.Name -like "*google*" -or $_.Name -like "*drive*"}
```
