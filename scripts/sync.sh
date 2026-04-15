#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=scripts/_platform.sh
source "$SCRIPT_DIR/_platform.sh"

command -v python3 >/dev/null 2>&1 || { echo "Error: python3 is required. Install Python 3 and retry." >&2; exit 1; }

# --- Parse arguments ---
ROOT="$HOME"
PROFILE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --root)
            [[ -z "${2:-}" ]] && { echo "Error: --root requires a path." >&2; exit 1; }
            ROOT="$2"; shift 2 ;;
        --profile)
            [[ -z "${2:-}" ]] && { echo "Error: --profile requires a name." >&2; exit 1; }
            PROFILE="$2"; shift 2 ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

PLATFORM="$(detect_platform)"
[[ -z "$PROFILE" ]] && PROFILE="$(get_mcp_profile "$PLATFORM")"

echo "=== AI Agent Skills Sync ==="
echo "Platform : $PLATFORM"
echo "Profile  : $PROFILE"
echo "Root     : $ROOT"
echo ""

# --- Load .env ---
ENV_FILE="$ROOT/VSCodespace/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    # Try common alternate locations
    for alt in "$ROOT/.env" "$REGISTRY_ROOT/.env.local" "$HOME/VSCodespace/.env"; do
        [[ -f "$alt" ]] && ENV_FILE="$alt" && break
    done
fi
[[ ! -f "$ENV_FILE" ]] && { echo "Error: .env not found. Copy env/template.env to ~/VSCodespace/.env and fill values." >&2; exit 1; }

set -a
while IFS='=' read -r key value; do
    [[ "$key" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${key// }" ]] && continue
    export "$key"="$value"
done < <(grep -E '^[A-Z_][A-Z0-9_]*=' "$ENV_FILE" 2>/dev/null)
set +a

# Set derived vars
export GITHUB_PERSONAL_ACCESS_TOKEN="${GITHUB_MCP_PAT:-}"
export GITHUB_TOKEN="${GITHUB_MCP_PAT:-}"
export FILESYSTEM_ALLOWED_PATH="${FILESYSTEM_ALLOWED_PATH:-$(get_default_filesystem_path "$PLATFORM")}"

# --- Load profile MCP servers ---
PROFILE_FILE="$REGISTRY_ROOT/mcp/profiles/${PROFILE}.mcp.json"
if [[ ! -f "$PROFILE_FILE" ]]; then
    echo "Warning: Profile $PROFILE not found, falling back to shared.mcp.json" >&2
    PROFILE_FILE="$REGISTRY_ROOT/mcp/shared.mcp.json"
fi

echo "-> Loading MCP profile: $PROFILE_FILE"
RESOLVED_MCP="$(resolve_tokens "$(cat "$PROFILE_FILE")")"

# --- Apply to Claude (~/.claude.json) ---
echo "-> Syncing Claude global MCPs..."
merge_mcp_servers "$RESOLVED_MCP" "$ROOT/.claude.json" '{"mcpServers":{}}'
echo "  ✓ ~/.claude.json updated"

# --- Apply to Gemini (~/.gemini/settings.json) ---
GEMINI_TEMPLATE="$REGISTRY_ROOT/agents/gemini/settings.patch.template.json"
if [[ -f "$GEMINI_TEMPLATE" ]]; then
    echo "-> Syncing Gemini settings..."
    RESOLVED_GEMINI="$(resolve_tokens "$(cat "$GEMINI_TEMPLATE")")"
    merge_mcp_servers "$RESOLVED_GEMINI" "$ROOT/.gemini/settings.json" '{"theme":"Default"}'
    echo "  ✓ ~/.gemini/settings.json updated"
fi

# --- Apply to Copilot/VS Code (.mcp.json) ---
COPILOT_TEMPLATE="$REGISTRY_ROOT/agents/copilot/mcp.template.json"
if [[ -f "$COPILOT_TEMPLATE" ]]; then
    echo "-> Syncing VS Code MCP config..."
    RESOLVED_COPILOT="$(resolve_tokens "$(cat "$COPILOT_TEMPLATE")")"
    mkdir -p "$ROOT/VSCodespace/.vscode"
    echo "$RESOLVED_COPILOT" > "$ROOT/VSCodespace/.mcp.json"
    echo "$RESOLVED_COPILOT" > "$ROOT/VSCodespace/.vscode/mcp.json"
    echo "  ✓ VSCodespace MCP configs updated"
fi

# --- Apply JetBrains XML (skip on Docker) ---
if [[ "$PLATFORM" != "docker" ]]; then
    JB_TEMPLATE="$REGISTRY_ROOT/agents/jetbrains/llm.mcpServers.template.xml"
    JB_BASE="$(get_jetbrains_base "$PLATFORM")"
    if [[ -f "$JB_TEMPLATE" ]] && [[ -n "$JB_BASE" ]]; then
        echo "-> Syncing JetBrains MCP configs at $JB_BASE..."
        RESOLVED_XML="$(resolve_tokens "$(cat "$JB_TEMPLATE")")"
        for dir in "$JB_BASE"/PyCharm* "$JB_BASE"/IntelliJIdea* "$JB_BASE"/WebStorm* "$JB_BASE"/GoLand*; do
            [[ -d "$dir" ]] || continue
            mkdir -p "$dir/options"
            echo "$RESOLVED_XML" > "$dir/options/llm.mcpServers.xml"
            echo "  ✓ $(basename "$dir")"
        done
    fi
fi

echo ""
echo "✓ Sync complete. Restart Claude Code / Gemini CLI to apply changes."
echo "  To re-apply after 'git pull': bash $SCRIPT_DIR/sync.sh"
