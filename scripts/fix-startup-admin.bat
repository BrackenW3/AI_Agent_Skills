@echo off
:: Run this as Administrator
:: Right-click → "Run as administrator"
echo === Startup Item Cleanup (requires Admin) ===

:: Remove gaming launchers from startup (open them when you want to game)
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Steam" /f 2>nul && echo [REMOVED] Steam startup || echo [SKIPPED] Steam startup
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "GogGalaxy" /f 2>nul && echo [REMOVED] GOG Galaxy startup || echo [SKIPPED] GOG Galaxy startup
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "GalaxyClient" /f 2>nul && echo [REMOVED] GOG GalaxyClient (duplicate) || echo [SKIPPED] GOG GalaxyClient

:: Dev tools - only needed when actively developing
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "JetBrains Toolbox" /f 2>nul && echo [REMOVED] JetBrains Toolbox startup || echo [SKIPPED] JetBrains Toolbox
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Docker Desktop" /f 2>nul && echo [REMOVED] Docker Desktop startup || echo [SKIPPED] Docker Desktop

:: Comms apps - start when needed
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Teams" /f 2>nul && echo [REMOVED] Teams startup || echo [SKIPPED] Teams
reg delete "HKCU\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Run" /v "Discord" /f 2>nul && echo [REMOVED] Discord startup || echo [SKIPPED] Discord

:: PDF pre-loader (Foxit launches this just to make Foxit open 0.5s faster - not worth it)
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v "Reader_Sl" /f 2>nul && echo [REMOVED] Foxit PDF pre-loader || echo [SKIPPED] Foxit PDF pre-loader

:: Remove GpgEX shell extension (causes right-click lag if GPG agent is slow)
reg delete "HKCR\*\shellex\ContextMenuHandlers\GpgEX" /f 2>nul && echo [REMOVED] GpgEX from * context menu || echo [SKIPPED] GpgEX *
reg delete "HKCR\Directory\shellex\ContextMenuHandlers\GpgEX" /f 2>nul && echo [REMOVED] GpgEX from Directory context menu || echo [SKIPPED] GpgEX Directory
reg delete "HKCR\Folder\shellex\ContextMenuHandlers\GpgEX" /f 2>nul && echo [REMOVED] GpgEX from Folder context menu || echo [SKIPPED] GpgEX Folder
reg delete "HKCR\Drive\shellex\ContextMenuHandlers\GpgEX" /f 2>nul && echo [REMOVED] GpgEX from Drive context menu || echo [SKIPPED] GpgEX Drive

:: IDrive shell extension - slows right-click when IDrive service is busy
:: Uncomment if IDrive backup causes Explorer right-click freezes:
:: reg delete "HKCR\*\shellex\ContextMenuHandlers\IDriveMenu" /f 2>nul && echo [REMOVED] IDriveMenu context menu
:: reg delete "HKCR\Directory\shellex\ContextMenuHandlers\IDriveMenu" /f 2>nul

echo.
echo === Remaining HKCU startup items ===
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" 2>nul
echo.
echo === Remaining HKLM Wow6432Node startup items ===
reg query "HKLM\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Run" 2>nul
echo.
echo Done. Changes take effect on next login/reboot.
pause
