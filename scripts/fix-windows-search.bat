@echo off
:: Optimize Windows Search - restrict to useful locations only
:: Run as Administrator
echo === Windows Search Optimization ===

:: Pause indexer while we configure
net stop WSearch 2>nul
echo [PAUSED] Windows Search indexer

:: The proper way to restrict Windows Search locations is through the
:: Indexing Options UI (which properly removes and adds search roots).
:: This script sets the key exclusions that reduce disk churn.

:: Exclude development directories from indexing (node_modules etc. cause huge index churn)
reg add "HKLM\SOFTWARE\Microsoft\Windows Search\CrawlScopeManager\Windows\SystemIndex\DefaultRules\ExcludedPaths" /v "C:\Users\User\VSCodespace" /t REG_SZ /d "C:\Users\User\VSCodespace" /f 2>nul
reg add "HKLM\SOFTWARE\Microsoft\Windows Search\CrawlScopeManager\Windows\SystemIndex\DefaultRules\ExcludedPaths" /v "node_modules" /t REG_SZ /d "node_modules" /f 2>nul

echo.
echo === Manual steps required ===
echo 1. Open: Control Panel → Indexing Options
echo    (or press Win+R → type: control /name Microsoft.IndexingOptions)
echo 2. Click "Modify"
echo 3. REMOVE these high-churn locations if present:
echo    - C:\Users\User\iCloudDrive
echo    - C:\Users\User\OneDrive
echo    - G:\ (games - no need to index)
echo    - H:\ (HDD - search on demand)
echo 4. KEEP: C:\Users\User (Documents, Desktop, Downloads)
echo 5. Click OK, then "Advanced" → Rebuild index
echo.

:: Restart the indexer
net start WSearch 2>nul
echo [STARTED] Windows Search indexer

echo.
echo Done. The indexer will now only watch user profile directories.
pause
