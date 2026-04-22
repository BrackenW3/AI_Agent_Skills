# quickstart.ps1 - Quick start script for vector search indexing pipeline
# 
# Usage:
#   .\quickstart.ps1
#   .\quickstart.ps1 -SkipBootstrap
#   .\quickstart.ps1 -SkipIndex
#
# This script:
#   1. Installs Python dependencies (pip install -r requirements.txt)
#   2. Runs bootstrap validation (python bootstrap.py)
#   3. Starts first index run (python indexer.py)
#
# Note: You may need to allow script execution first:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

param(
    [switch]$SkipBootstrap = $false,
    [switch]$SkipIndex = $false
)

# Error handling
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Header {
    param([string]$Message)
    Write-Host "`n================================================" -ForegroundColor Cyan
    Write-Host "$Message" -ForegroundColor Cyan
    Write-Host "================================================`n" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

# Check Python is installed
Write-Header "QUICKSTART: Vector Search Indexing Pipeline"
Write-Host "Checking Python installation..."

try {
    $PythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Python $PythonVersion found"
    }
    else {
        throw "Python not found"
    }
}
catch {
    Write-Error "Python 3 is not installed or not in PATH"
    Write-Host "Please install Python 3.8+ and try again"
    Write-Host "See: https://www.python.org/downloads/"
    exit 1
}

# Step 1: Install dependencies
Write-Header "Step 1: Installing Dependencies"

if (-not (Test-Path "requirements.txt")) {
    Write-Error "requirements.txt not found in $ScriptDir"
    exit 1
}

Write-Host "Installing packages from requirements.txt..."
try {
    python -m pip install -q -r requirements.txt
    Write-Success "Dependencies installed"
}
catch {
    Write-Error "Failed to install dependencies"
    Write-Host "Try running: pip install -r requirements.txt"
    exit 1
}

# Step 2: Run bootstrap
if (-not $SkipBootstrap) {
    Write-Header "Step 2: Running Bootstrap Validation"
    
    if (-not (Test-Path "bootstrap.py")) {
        Write-Warning "bootstrap.py not found - skipping validation"
    }
    else {
        Write-Host "Running system validation..."
        try {
            python bootstrap.py
            Write-Success "Bootstrap validation passed"
        }
        catch {
            Write-Error "Bootstrap validation failed"
            Write-Host "Review the messages above and fix any configuration issues"
            exit 1
        }
    }
}
else {
    Write-Header "Step 2: Bootstrap (Skipped)"
    Write-Warning "Skipped bootstrap validation as requested"
}

# Step 3: Run indexer
if (-not $SkipIndex) {
    Write-Header "Step 3: Starting Indexing Pipeline"
    
    if (-not (Test-Path "indexer.py")) {
        Write-Error "indexer.py not found"
        exit 1
    }
    
    Write-Host "Starting document indexing..."
    Write-Host "This may take a while depending on your file count and network speed"
    Write-Host ""
    
    try {
        python indexer.py
        Write-Success "Indexing completed successfully"
    }
    catch {
        Write-Error "Indexing failed - check the output above for details"
        exit 1
    }
}
else {
    Write-Header "Step 3: Indexing (Skipped)"
    Write-Warning "Skipped indexing as requested"
    Write-Host "Run 'python indexer.py' when ready to index documents"
}

# Final status
Write-Header "Quickstart Complete"
Write-Host "Pipeline setup and initialization finished!"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  • Interactive search:    python search.py"
Write-Host "  • View indexing logs:    Get-Content index_metadata.db"
Write-Host "  • Check configuration:   Get-Content .env"
Write-Host ""
Write-Success "Vector search pipeline is ready to use"
