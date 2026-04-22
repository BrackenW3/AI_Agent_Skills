param(
    [switch]$DryRun = $false,
    [string]$LogPath = (Join-Path -Path $PSScriptRoot -ChildPath "fix-onedrive.log")
)

# ============================================================================
# OneDrive Account Manager & Documents Folder Reorganizer
# ============================================================================

# Initialize logging
function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARN", "ERROR", "SUCCESS")]
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    Add-Content -Path $LogPath -Value $logMessage -ErrorAction SilentlyContinue
    
    $color = @{
        "INFO"    = "White"
        "WARN"    = "Yellow"
        "ERROR"   = "Red"
        "SUCCESS" = "Green"
    }
    
    Write-Host $logMessage -ForegroundColor $color[$Level]
}

# ============================================================================
# PART 1: Check OneDrive Accounts
# ============================================================================

function Get-OneDriveAccounts {
    Write-Log "Checking OneDrive accounts configured in registry..." "INFO"
    
    try {
        $regPath = "HKCU:\Software\Microsoft\OneDrive\Accounts"
        
        if (Test-Path $regPath) {
            $accountsReg = Get-Item -Path $regPath
            $accounts = @()
            
            foreach ($account in $accountsReg.GetSubKeyNames()) {
                if ($account -ne "Personal" -and $account -ne "Business1") {
                    continue
                }
                
                $accountPath = Join-Path -Path $regPath -ChildPath $account
                $accountKey = Get-Item -Path $accountPath
                
                $userEmail = $accountKey.GetValue("UserEmail") -or "Unknown"
                $tenantId = $accountKey.GetValue("TenantId") -or "N/A"
                $businessPath = $accountKey.GetValue("BusinessResourceUriString") -or "N/A"
                
                $accounts += [PSCustomObject]@{
                    AccountType = $account
                    UserEmail   = $userEmail
                    TenantId    = $tenantId
                    Path        = $accountPath
                }
            }
            
            return $accounts
        }
        else {
            Write-Log "OneDrive registry path not found" "WARN"
            return @()
        }
    }
    catch {
        Write-Log "Error reading OneDrive accounts: $_" "ERROR"
        return @()
    }
}

function Report-OneDriveStatus {
    param([array]$Accounts)
    
    Write-Log "========== OneDrive Account Status ==========" "INFO"
    
    if ($Accounts.Count -eq 0) {
        Write-Log "No OneDrive accounts found in registry" "WARN"
        return
    }
    
    foreach ($account in $Accounts) {
        Write-Log "Account Type: $($account.AccountType)" "INFO"
        Write-Log "  User Email: $($account.UserEmail)" "INFO"
        Write-Log "  Tenant ID: $($account.TenantId)" "INFO"
    }
    
    Write-Log "========== End Account Status ==========" "INFO"
}

# ============================================================================
# PART 2: Check for will.bracken.3@outlook and Add if Missing
# ============================================================================

function Test-AccountExists {
    param([string]$Email)
    
    $accounts = Get-OneDriveAccounts
    $found = $accounts | Where-Object { $_.UserEmail -like "*$Email*" }
    
    return $null -ne $found
}

function Invoke-OneDriveAddAccount {
    Write-Log "will.bracken.3@outlook not found. Opening OneDrive Add Account flow..." "WARN"
    
    try {
        # Launch the OneDrive Add Account dialog
        Start-Process -FilePath "shlvl:root" -ArgumentList "shell:appsFolder\Microsoft.OneDriveSync_8wekyb3d8bbwe!App" -ErrorAction SilentlyContinue
        
        Write-Log "OneDrive Add Account dialog launched. Please complete the sign-in process." "INFO"
        Write-Log "Waiting 10 seconds for user to interact..." "INFO"
        
        Start-Sleep -Seconds 10
        
        Write-Log "Continuing with script execution..." "INFO"
    }
    catch {
        Write-Log "Error launching OneDrive Add Account: $_" "WARN"
        Write-Log "Please manually add the account: Settings > Accounts > Add account" "INFO"
    }
}

# ============================================================================
# PART 3: Get Documents Path and Validate
# ============================================================================

function Get-OneDriveDocumentsPath {
    param([string]$Email)
    
    Write-Log "Attempting to locate OneDrive Documents folder..." "INFO"
    
    # Try common OneDrive paths
    $possiblePaths = @(
        "$env:USERPROFILE\OneDrive\Documents",
        "$env:USERPROFILE\OneDrive - $Email\Documents",
        "$env:USERPROFILE\OneDrive - $(($Email -split '@')[0])\Documents"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path -Path $path) {
            Write-Log "Found OneDrive Documents at: $path" "SUCCESS"
            return $path
        }
    }
    
    # Fallback to Windows Documents
    $windowsDocsPath = [Environment]::GetFolderPath("MyDocuments")
    if (Test-Path -Path $windowsDocsPath) {
        Write-Log "Using Windows Documents folder: $windowsDocsPath" "INFO"
        return $windowsDocsPath
    }
    
    Write-Log "Could not locate Documents folder" "ERROR"
    return $null
}

# ============================================================================
# PART 4: Folder Organization Taxonomy
# ============================================================================

function Get-FolderTaxonomy {
    return @{
        "Work"     = @(
            "AI Agents", "Cline", "Cloudflare", "Development Work", 
            "Git", "Programming", "Computer Issues"
        )
        "Personal" = @(
            "Current Resumes", "Resumes", "Music", "Pictures", 
            "Personal Account", "Videos"
        )
        "Office"   = @(
            "Excel Documents", "Custom Office Templates", "Microsoft Office", 
            "Microsoft Copilot Chat Files", "Work Documents"
        )
        "Archive"  = @(
            "Baldur's Gate II - Enhanced Edition", "Game Mods", 
            "Mount and Blade II Bannerlord", "My Games", "My Shapes", 
            "Corsair iCUE Profiles"
        )
        "System"   = @(
            "AdGuard", "Bookmark Backup", "CCleaner Registry", 
            "Chrome Bookmarks Backup", "Desktop", "Icon Files", "Fonts"
        )
    }
}

function Get-RootLevelFolders {
    return @(
        "Cloud Date", "Downloads", "File Backup", "Files", "GitHub", 
        "Security", "Shared Folders and Files", "Shared OneDrive", "Archive"
    )
}

# ============================================================================
# PART 5: Reorganize Documents Folder
# ============================================================================

function Reorganize-DocumentsFolder {
    param(
        [string]$DocumentsPath,
        [bool]$DryRun = $false
    )
    
    if (-not (Test-Path -Path $DocumentsPath)) {
        Write-Log "Documents path does not exist: $DocumentsPath" "ERROR"
        return
    }
    
    Write-Log "========== Starting Documents Reorganization ==========" "INFO"
    Write-Log "Target path: $DocumentsPath" "INFO"
    if ($DryRun) {
        Write-Log "DRY RUN MODE - No actual moves will be performed" "WARN"
    }
    
    # Get folder taxonomy
    $taxonomy = Get-FolderTaxonomy
    $rootFolders = Get-RootLevelFolders
    
    # Get all items in Documents
    $items = Get-ChildItem -Path $DocumentsPath -ErrorAction SilentlyContinue
    
    if (-not $items) {
        Write-Log "No items found in Documents folder" "INFO"
        return
    }
    
    Write-Log "Found $($items.Count) items in Documents folder" "INFO"
    
    # Track what will be moved
    $moveLog = @()
    
    # Process each category in taxonomy
    foreach ($category in $taxonomy.Keys) {
        $targetFolder = Join-Path -Path $DocumentsPath -ChildPath $category
        
        # Create category folder if it doesn't exist and not in dry run
        if (-not (Test-Path -Path $targetFolder)) {
            if ($DryRun) {
                Write-Log "[DRY RUN] Would create folder: $category" "INFO"
            }
            else {
                try {
                    New-Item -Path $targetFolder -ItemType Directory -ErrorAction Stop | Out-Null
                    Write-Log "Created folder: $category" "SUCCESS"
                }
                catch {
                    Write-Log "Error creating folder $category : $_" "ERROR"
                    continue
                }
            }
        }
        
        # Process items that belong in this category
        foreach ($folderName in $taxonomy[$category]) {
            $sourceItem = $items | Where-Object { $_.Name -eq $folderName -and $_.PSIsContainer }
            
            if ($sourceItem) {
                $sourcePath = $sourceItem.FullName
                $destPath = Join-Path -Path $targetFolder -ChildPath $folderName
                
                # Check if destination already exists
                if (Test-Path -Path $destPath) {
                    Write-Log "[SKIP] Already exists at destination: $folderName -> $category/" "WARN"
                    continue
                }
                
                if ($DryRun) {
                    Write-Log "[DRY RUN] Would move: $folderName -> $category/" "INFO"
                    $moveLog += @{ Source = $folderName; Dest = "$category/" }
                }
                else {
                    try {
                        Move-Item -Path $sourcePath -Destination $destPath -ErrorAction Stop
                        Write-Log "Moved: $folderName -> $category/" "SUCCESS"
                        $moveLog += @{ Source = $folderName; Dest = "$category/" }
                    }
                    catch {
                        Write-Log "Error moving $folderName : $_" "ERROR"
                    }
                }
            }
        }
    }
    
    # Summary of items that will stay at root level
    Write-Log "========== Items Remaining at Root Level ==========" "INFO"
    $items = Get-ChildItem -Path $DocumentsPath -ErrorAction SilentlyContinue
    
    foreach ($item in $items) {
        if ($item.PSIsContainer) {
            # Check if it's in root level folders list or in a category subfolder
            if ($rootFolders -contains $item.Name) {
                Write-Log "Root-level folder: $($item.Name)" "INFO"
            }
            elseif ($taxonomy.Values -contains $item.Name) {
                # This is an item that should have been moved (already categorized)
                continue
            }
            else {
                Write-Log "Category folder: $($item.Name)" "INFO"
            }
        }
    }
    
    Write-Log "========== Reorganization Complete ==========" "INFO"
    Write-Log "Total items moved: $($moveLog.Count)" "SUCCESS"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

function Main {
    Write-Log "========== OneDrive Account Manager & Reorganizer ==========" "INFO"
    Write-Log "Script started at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "INFO"
    
    # Check existing accounts
    $accounts = Get-OneDriveAccounts
    Report-OneDriveStatus -Accounts $accounts
    
    # Check for will.bracken.3@outlook
    Write-Log "Checking for will.bracken.3@outlook account..." "INFO"
    if (-not (Test-AccountExists "will.bracken.3@outlook")) {
        Write-Log "will.bracken.3@outlook not found in registered accounts" "WARN"
        Invoke-OneDriveAddAccount
    }
    else {
        Write-Log "will.bracken.3@outlook is already registered" "SUCCESS"
    }
    
    # Get Documents path (prioritize will.bracken.3@outlook if it exists)
    $targetEmail = "will.bracken.3@outlook"
    $docsPath = Get-OneDriveDocumentsPath -Email $targetEmail
    
    if ($docsPath) {
        Reorganize-DocumentsFolder -DocumentsPath $docsPath -DryRun $DryRun
    }
    else {
        Write-Log "Could not determine Documents path. Skipping reorganization." "ERROR"
    }
    
    Write-Log "========== Script Completed ==========" "INFO"
    Write-Log "Log file saved to: $LogPath" "INFO"
}

# Execute main
Main
