#!/usr/bin/env bash
# _platform.sh — sourced by sync.sh and bootstrap.sh, never executed directly

# Detect running platform
detect_platform() {
    if [[ -f /.dockerenv ]] || [[ -n "${DOCKER_CONTAINER:-}" ]]; then
        echo "docker"
    elif [[ -f /proc/version ]] && grep -qi "microsoft\|wsl" /proc/version 2>/dev/null; then
        echo "wsl2"
    elif [[ "$(uname -s 2>/dev/null)" == "Darwin" ]]; then
        echo "macos"
    else
        echo "linux"
    fi
}

# Return the MCP profile name for a platform
get_mcp_profile() {
    case "${1:-}" in
        docker)         echo "docker" ;;
        macos)          echo "macos" ;;
        wsl2|linux)     echo "linux" ;;
        *)              echo "linux" ;;
    esac
}

# Return Claude plugin settings filename for a platform
get_settings_profile() {
    case "${1:-}" in
        docker)         echo "settings.thin.json" ;;
        macos)          echo "settings.macos.json" ;;
        wsl2|linux)     echo "settings.thin.json" ;;
        *)              echo "settings.base.json" ;;
    esac
}

# Return JetBrains config base dir for a platform
get_jetbrains_base() {
    case "${1:-}" in
        macos)          echo "$HOME/Library/Application Support/JetBrains" ;;
        wsl2)
            # Also write to Windows JetBrains path if accessible
            local win_path="/mnt/c/Users/$(cmd.exe /c echo %USERNAME% 2>/dev/null | tr -d '\r')/AppData/Roaming/JetBrains"
            if [[ -d "$(dirname "$win_path")" ]]; then
                echo "$win_path"
            else
                echo "$HOME/.config/JetBrains"
            fi
            ;;
        linux)          echo "$HOME/.config/JetBrains" ;;
        docker)         echo "" ;;  # skip JetBrains in Docker
        *)              echo "$HOME/.config/JetBrains" ;;
    esac
}

# Return default FILESYSTEM_ALLOWED_PATH for a platform
get_default_filesystem_path() {
    case "${1:-}" in
        macos)          echo "$HOME/VSCodespace" ;;
        wsl2)           echo "/mnt/c/Users/$(whoami | tr '[:lower:]' '[:upper:]' | head -c1)$(whoami | tail -c +2)/VSCodespace" ;;
        docker)         echo "/workspace" ;;
        linux)          echo "$HOME/VSCodespace" ;;
        *)              echo "$HOME/VSCodespace" ;;
    esac
}

# Resolve ${VAR} tokens in a string using current environment
resolve_tokens() {
    local text="$1"
    # Use python3 for reliable substitution (handles special chars in values)
    python3 -c "
import os, re, sys
text = sys.argv[1]
def replace(m):
    key = m.group(1)
    return os.environ.get(key, '')
print(re.sub(r'\\\$\{([A-Z0-9_]+)\}', replace, text), end='')
" "$text"
}

# Merge mcpServers from a JSON file into a target JSON file
# Usage: merge_mcp_servers <source_json_string> <target_file> [default_base_json]
merge_mcp_servers() {
    local src_json="$1"
    local target_file="$2"
    local default_base="${3:-'{}'}"
    python3 - "$target_file" "$default_base" <<PYEOF
import json, sys, os
target_path = sys.argv[1]
default_base = sys.argv[2]
src = json.loads("""$src_json""")
if os.path.exists(target_path):
    with open(target_path) as f:
        target = json.load(f)
else:
    target = json.loads(default_base)
target.setdefault('mcpServers', {}).update(src.get('mcpServers', {}))
os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
with open(target_path, 'w') as f:
    json.dump(target, f, indent=2)
    f.write('\n')
PYEOF
}
