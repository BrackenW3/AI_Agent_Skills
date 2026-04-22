@echo off
:: Kill all node.exe processes in one shot — no PowerShell overhead
:: Safe to run: Claude MCP servers will restart automatically
taskkill /F /IM node.exe >nul 2>&1
echo Node processes killed.
timeout /t 3 /nobreak >nul
:: Count remaining
tasklist /FI "IMAGENAME eq node.exe" 2>nul | find /c "node.exe"
echo Done.
