#!/usr/bin/env bash
set -euo pipefail
# bootstrap.sh — first-time setup on any Unix-like platform
# Usage: bash bootstrap.sh [--root /path/to/home] [--repo-dir /path/to/AI_Agent_Skills]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/_platform.sh"

PLATFORM="$(detect_platform)"
ROOT="${HOME}"
echo "=== AI Agent Skills Bootstrap ==="
echo "Platform: $PLATFORM  |  Registry: $REGISTRY_ROOT"
echo ""

# 1. Check prerequisites
echo "-> Checking prerequisites..."
MISSING=()
command -v python3 >/dev/null 2>&1 || MISSING+=("python3")
command -v git    >/dev/null 2>&1 || MISSING+=("git")
command -v node   >/dev/null 2>&1 || MISSING+=("node (nodejs)")
command -v npx    >/dev/null 2>&1 || MISSING+=("npx (included with node)")

if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo "Missing prerequisites: ${MISSING[*]}"
    case "$PLATFORM" in
        macos)
            echo "Install with: brew install python node git"
            echo "  (get Homebrew at https://brew.sh if needed)"
            ;;
        linux|wsl2)
            echo "Install with: sudo apt-get install -y python3 nodejs npm git"
            echo "  (or: curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo bash -)"
            ;;
        docker)
            echo "Install in Dockerfile: apt-get install -y python3 nodejs npm git"
            ;;
    esac
    exit 1
fi
echo "  ✓ All prerequisites present"

# 2. Locate or prompt for .env
echo ""
echo "-> Locating credentials (.env)..."
ENV_CANDIDATES=(
    "$ROOT/VSCodespace/.env"
    "$ROOT/.env"
    "$REGISTRY_ROOT/.env.local"
)
ENV_FILE=""
for c in "${ENV_CANDIDATES[@]}"; do
    [[ -f "$c" ]] && ENV_FILE="$c" && break
done

if [[ -z "$ENV_FILE" ]]; then
    echo "  ⚠  No .env found — skipping MCP sync."
    echo "  To enable MCP sync later, create ~/VSCodespace/.env with your API keys"
    echo "  then re-run: bash scripts/sync.sh"
    SKIP_SYNC=true
else
    echo "  ✓ Found credentials at: $ENV_FILE"
    SKIP_SYNC=false
fi

# 3. Run sync (only if .env exists)
if [[ "$SKIP_SYNC" == false ]]; then
    echo ""
    "$SCRIPT_DIR/sync.sh" --root "$ROOT"
fi

# 4. Platform-specific post-steps
echo ""
echo "-> Platform post-steps ($PLATFORM)..."
case "$PLATFORM" in
    macos)
        echo "  macOS: If Claude Code is not installed, run:"
        echo "    npm install -g @anthropic-ai/claude-code"
        echo "  Or download from https://claude.ai/download"
        ;;
    wsl2)
        echo "  WSL2: Claude Code can be run from Windows or inside WSL2."
        echo "  This sync wrote configs for the WSL2 environment."
        echo "  For Windows-side Claude Code, run scripts/sync.ps1 from PowerShell."
        ;;
    linux)
        echo "  Linux: Install Claude Code with:"
        echo "    npm install -g @anthropic-ai/claude-code"
        ;;
    docker)
        echo "  Docker: Configs written to /root (or current user home)."
        echo "  Mount /workspace and pass API keys via --env-file."
        ;;
esac

echo ""
echo "✓ Bootstrap complete!"
echo "  Update anytime: cd $REGISTRY_ROOT && git pull && bash scripts/sync.sh"
