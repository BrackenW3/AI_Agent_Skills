#!/bin/bash
# quickstart.sh - Quick start script for vector search indexing pipeline
# 
# Usage:
#   ./quickstart.sh
#   ./quickstart.sh --skip-bootstrap
#   ./quickstart.sh --skip-index
#
# This script:
#   1. Installs Python dependencies (pip install -r requirements.txt)
#   2. Runs bootstrap validation (python bootstrap.py)
#   3. Starts first index run (python indexer.py)

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments
SKIP_BOOTSTRAP=false
SKIP_INDEX=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-bootstrap)
            SKIP_BOOTSTRAP=true
            shift
            ;;
        --skip-index)
            SKIP_INDEX=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-bootstrap] [--skip-index]"
            exit 1
            ;;
    esac
done

# Helper functions
print_header() {
    echo -e "\n${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check Python is installed
print_header "QUICKSTART: Vector Search Indexing Pipeline"
echo "Checking Python installation..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    echo "See: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_success "Python $PYTHON_VERSION found"

# Step 1: Install dependencies
print_header "Step 1: Installing Dependencies"

if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found in $SCRIPT_DIR"
    exit 1
fi

echo "Installing packages from requirements.txt..."
if python3 -m pip install -q -r requirements.txt; then
    print_success "Dependencies installed"
else
    print_error "Failed to install dependencies"
    echo "Try running: pip3 install -r requirements.txt"
    exit 1
fi

# Step 2: Run bootstrap
if [ "$SKIP_BOOTSTRAP" = false ]; then
    print_header "Step 2: Running Bootstrap Validation"
    
    if [ ! -f "bootstrap.py" ]; then
        print_warning "bootstrap.py not found - skipping validation"
    else
        echo "Running system validation..."
        if python3 bootstrap.py; then
            print_success "Bootstrap validation passed"
        else
            print_error "Bootstrap validation failed"
            echo "Review the messages above and fix any configuration issues"
            exit 1
        fi
    fi
else
    print_header "Step 2: Bootstrap (Skipped)"
    print_warning "Skipped bootstrap validation as requested"
fi

# Step 3: Run indexer
if [ "$SKIP_INDEX" = false ]; then
    print_header "Step 3: Starting Indexing Pipeline"
    
    if [ ! -f "indexer.py" ]; then
        print_error "indexer.py not found"
        exit 1
    fi
    
    echo "Starting document indexing..."
    echo "This may take a while depending on your file count and network speed"
    echo ""
    
    if python3 indexer.py; then
        print_success "Indexing completed successfully"
    else
        print_error "Indexing failed - check the output above for details"
        exit 1
    fi
else
    print_header "Step 3: Indexing (Skipped)"
    print_warning "Skipped indexing as requested"
    echo "Run 'python3 indexer.py' when ready to index documents"
fi

# Final status
print_header "Quickstart Complete"
echo "Pipeline setup and initialization finished!"
echo ""
echo "Next steps:"
echo "  • Interactive search:    python3 search.py"
echo "  • View indexing logs:    cat index_metadata.db"
echo "  • Check configuration:   cat .env"
echo ""
print_success "Vector search pipeline is ready to use"
