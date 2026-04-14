#!/usr/bin/env bash
# sync.sh — Linux/macOS/WSL2 equivalent of sync.ps1
# Resolves ${VAR} placeholders in MCP templates and writes live agent configs.
# Usage: bash sync.sh [--root /path/to/home]

set -euo pipefail

# ── Argument parsing ──────────────────────────────────────────────────────────
ROOT="$HOME"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --root)
            ROOT="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

REGISTRY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VSCODE_ROOT="$ROOT/VSCodespace"
ENV_PATH="$VSCODE_ROOT/.env"

# ── Load env vars from ~/VSCodespace/.env ─────────────────────────────────────
declare -A ENV_MAP

if [[ -f "$ENV_PATH" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip blank lines and comments
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
            key="${BASH_REMATCH[1]// /}"
            val="${BASH_REMATCH[2]}"
            ENV_MAP["$key"]="$val"
        fi
    done < "$ENV_PATH"
else
    echo "Warning: $ENV_PATH not found — continuing with empty env map" >&2
fi

# ── Derived / default values ──────────────────────────────────────────────────
if [[ -n "${ENV_MAP[GITHUB_MCP_PAT]:-}" ]]; then
    ENV_MAP["GITHUB_PERSONAL_ACCESS_TOKEN"]="${ENV_MAP[GITHUB_MCP_PAT]}"
    ENV_MAP["GITHUB_TOKEN"]="${ENV_MAP[GITHUB_MCP_PAT]}"
fi

if [[ -z "${ENV_MAP[FILESYSTEM_ALLOWED_PATH]:-}" ]]; then
    ENV_MAP["FILESYSTEM_ALLOWED_PATH"]="$ROOT/VSCodespace"
fi

# Pull CLAUDE_AZURE_PATH from existing ~/.claude.json if present
CLAUDE_PATH="$ROOT/.claude.json"
if [[ -f "$CLAUDE_PATH" ]]; then
    azure_path="$(python3 - "$CLAUDE_PATH" <<'PYEOF'
import json, sys
try:
    data = json.load(open(sys.argv[1]))
    print(data.get("mcpServers", {}).get("azure", {}).get("env", {}).get("PATH", ""))
except Exception:
    print("")
PYEOF
)"
    if [[ -n "$azure_path" ]]; then
        ENV_MAP["CLAUDE_AZURE_PATH"]="$azure_path"
    fi
fi

if [[ -z "${ENV_MAP[CLAUDE_AZURE_PATH]:-}" ]]; then
    ENV_MAP["CLAUDE_AZURE_PATH"]="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
fi

# ── Helper: resolve ${VAR} placeholders in a string ──────────────────────────
resolve_text() {
    local text="$1"
    # Iterate over all known env keys and substitute
    for key in "${!ENV_MAP[@]}"; do
        local val="${ENV_MAP[$key]}"
        # Escape & in replacement value for sed
        val_escaped="${val//&/\\&}"
        text="${text//\$\{$key\}/$val_escaped}"
    done
    # Clear any remaining unresolved placeholders
    text="$(echo "$text" | sed 's/\${\([A-Z0-9_]*\)}\([^}]*\)/\2/g; s/\${\([A-Z0-9_]*\)}//g')"
    echo "$text"
}

# ── Helper: ensure parent directory exists ────────────────────────────────────
ensure_dir() {
    local path="$1"
    local dir
    dir="$(dirname "$path")"
    mkdir -p "$dir"
}

# ── Helper: merge mcpServers into an existing JSON file via python3 ───────────
# Usage: merge_mcp_servers <target_file> <resolved_servers_json> [default_base_json]
merge_mcp_servers() {
    local target="$1"
    local servers_json="$2"
    local default_base="${3:-{\}}"

    python3 - "$target" "$servers_json" "$default_base" <<'PYEOF'
import json, sys, os

target_path = sys.argv[1]
servers_json = sys.argv[2]
default_base = sys.argv[3]

# Load or create base document
if os.path.isfile(target_path):
    try:
        current = json.loads(open(target_path).read())
    except Exception:
        current = json.loads(default_base)
else:
    current = json.loads(default_base)

# Merge mcpServers (preserve existing keys, update/add from template)
new_servers = json.loads(servers_json)
existing_servers = current.get("mcpServers", {})
existing_servers.update(new_servers)
current["mcpServers"] = existing_servers

# Write back
os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
with open(target_path, "w", encoding="utf-8") as f:
    json.dump(current, f, indent=2, ensure_ascii=False)
    f.write("\n")
print(f"Written: {target_path}")
PYEOF
}

# ── Helper: write a plain JSON file ──────────────────────────────────────────
write_json_file() {
    local target="$1"
    local content="$2"
    ensure_dir "$target"
    python3 - "$target" "$content" <<'PYEOF'
import json, sys, os
target_path = sys.argv[1]
content = sys.argv[2]
data = json.loads(content)
os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
with open(target_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")
print(f"Written: {target_path}")
PYEOF
}

# ── 1. Copilot → ~/VSCodespace/.mcp.json and .vscode/mcp.json ────────────────
echo "Syncing Copilot MCP template..."
copilot_template_path="$REGISTRY_ROOT/agents/copilot/mcp.template.json"
copilot_raw="$(cat "$copilot_template_path")"
copilot_resolved="$(resolve_text "$copilot_raw")"

write_json_file "$VSCODE_ROOT/.mcp.json" "$copilot_resolved"
write_json_file "$VSCODE_ROOT/.vscode/mcp.json" "$copilot_resolved"

# ── 2. Claude → ~/.claude.json (merge mcpServers) ────────────────────────────
echo "Syncing Claude MCP template..."
claude_template_path="$REGISTRY_ROOT/agents/claude/global-mcps.template.json"
claude_raw="$(cat "$claude_template_path")"
claude_resolved="$(resolve_text "$claude_raw")"

# Extract just the mcpServers block for merging
claude_servers_json="$(python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
print(json.dumps(data.get('mcpServers', {})))
" <<< "$claude_resolved")"

merge_mcp_servers "$CLAUDE_PATH" "$claude_servers_json" "{}"

# ── 3. Gemini → ~/.gemini/settings.json (merge mcpServers) ───────────────────
echo "Syncing Gemini MCP template..."
gemini_path="$ROOT/.gemini/settings.json"
gemini_template_path="$REGISTRY_ROOT/agents/gemini/settings.patch.template.json"
gemini_raw="$(cat "$gemini_template_path")"
gemini_resolved="$(resolve_text "$gemini_raw")"

gemini_servers_json="$(python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
print(json.dumps(data.get('mcpServers', {})))
" <<< "$gemini_resolved")"

merge_mcp_servers "$gemini_path" "$gemini_servers_json" '{"theme":"Default"}'

# ── 4. JetBrains XML → ~/.config/JetBrains/PyCharm*/options/ ─────────────────
echo "Syncing JetBrains MCP template..."
jetbrains_template_path="$REGISTRY_ROOT/agents/jetbrains/llm.mcpServers.template.xml"
jetbrains_raw="$(cat "$jetbrains_template_path")"
jetbrains_resolved="$(resolve_text "$jetbrains_raw")"

jetbrains_base="$ROOT/.config/JetBrains"
if [[ -d "$jetbrains_base" ]]; then
    # Glob for any installed PyCharm version directory
    shopt -s nullglob
    pycharm_dirs=("$jetbrains_base"/PyCharm*)
    shopt -u nullglob
    if [[ ${#pycharm_dirs[@]} -gt 0 ]]; then
        for pycharm_dir in "${pycharm_dirs[@]}"; do
            target="$pycharm_dir/options/llm.mcpServers.xml"
            ensure_dir "$target"
            printf '%s\n' "$jetbrains_resolved" > "$target"
            echo "Written: $target"
        done
    else
        echo "No PyCharm installation found under $jetbrains_base — skipping JetBrains sync"
    fi
else
    echo "JetBrains config directory not found ($jetbrains_base) — skipping JetBrains sync"
fi

echo "MCP templates synced to local configs."
