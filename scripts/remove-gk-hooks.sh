#!/usr/bin/env bash
# remove-gk-hooks.sh
# Removes all GitKraken AI hooks from Claude Code settings.json
# Works on macOS, Linux, and WSL.
#
# Usage:
#   bash remove-gk-hooks.sh
#   CLAUDE_SETTINGS=/custom/path/.claude/settings.json bash remove-gk-hooks.sh

set -euo pipefail

SETTINGS="${CLAUDE_SETTINGS:-$HOME/.claude/settings.json}"

if [[ ! -f "$SETTINGS" ]]; then
    echo "No Claude settings found at $SETTINGS — nothing to do."
    exit 0
fi

# Backup
BACKUP="${SETTINGS}.bak-$(date +%Y%m%d-%H%M)"
cp "$SETTINGS" "$BACKUP"
echo "Backed up to: $BACKUP"

# Check if hooks exist
HOOK_COUNT=$(python3 -c "
import json, sys
with open('$SETTINGS') as f:
    d = json.load(f)
hooks = d.get('hooks', {})
print(len(hooks))
")

if [[ "$HOOK_COUNT" -eq 0 ]]; then
    echo "No hooks found in settings — already clean."
    exit 0
fi

echo "Found $HOOK_COUNT hook event types — removing all..."

# Remove hooks key and write back
python3 -c "
import json, sys

path = '$SETTINGS'
with open(path) as f:
    d = json.load(f)

if 'hooks' in d:
    del d['hooks']

with open(path, 'w') as f:
    json.dump(d, f, indent=2)
    f.write('\n')
"

echo "Done. Removed $HOOK_COUNT GitKraken hook entries from $SETTINGS"
echo ""
echo "To re-enable a single hook for GitKraken (if needed):"
echo "  gk ai hook install --host claude-code"
