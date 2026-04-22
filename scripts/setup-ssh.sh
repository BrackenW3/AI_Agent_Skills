#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# setup-ssh.sh — Mac/Linux SSH setup
# Run once on a new machine to configure SSH for GitHub
#
# Usage:
#   bash scripts/setup-ssh.sh
#   bash scripts/setup-ssh.sh --key my_key --comment "work-macbook"
# ─────────────────────────────────────────────────────────────────────────────

KEY_NAME="id_ed25519"
COMMENT="${USER}@$(hostname -s)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --key)     KEY_NAME="$2"; shift 2 ;;
    --comment) COMMENT="$2"; shift 2 ;;
    *) shift ;;
  esac
done

SSH_DIR="$HOME/.ssh"
KEY_PATH="$SSH_DIR/$KEY_NAME"
IS_MAC=false
[[ "$(uname)" == "Darwin" ]] && IS_MAC=true

echo ""
echo "=== SSH Setup ($(uname -s)) ==="

# ── 1. Create .ssh dir ────────────────────────────────────────────────────────
echo ""
echo "[1/4] Checking .ssh directory..."
mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"
echo "  $SSH_DIR ready"

# ── 2. Generate key if missing ────────────────────────────────────────────────
echo ""
echo "[2/4] Checking SSH key ($KEY_NAME)..."
if [[ ! -f "$KEY_PATH" ]]; then
  echo "  Generating new ED25519 key..."
  ssh-keygen -t ed25519 -C "$COMMENT" -f "$KEY_PATH" -N ""
  chmod 600 "$KEY_PATH"
  echo "  Key created: $KEY_PATH"
else
  echo "  Key already exists: $KEY_PATH"
fi

# ── 3. Add to SSH agent ───────────────────────────────────────────────────────
echo ""
echo "[3/4] Adding key to SSH agent..."

# Start agent if not running
if ! ssh-add -l &>/dev/null; then
  eval "$(ssh-agent -s)" > /dev/null
fi

if $IS_MAC; then
  # macOS: use Keychain so key persists across reboots
  ssh-add --apple-use-keychain "$KEY_PATH" 2>/dev/null || ssh-add "$KEY_PATH"

  # Ensure SSH config has UseKeychain entry
  CONFIG="$SSH_DIR/config"
  if [[ ! -f "$CONFIG" ]] || ! grep -q "UseKeychain" "$CONFIG"; then
    cat >> "$CONFIG" << EOF

# ── macOS Keychain ────────────────────────────────────────────────────────────
Host *
    AddKeysToAgent yes
    UseKeychain yes
    IdentityFile ~/.ssh/$KEY_NAME
EOF
    echo "  Added UseKeychain to SSH config"
  fi
else
  ssh-add "$KEY_PATH"
fi

echo "  Key loaded in agent"

# ── 4. Write SSH config for GitHub ───────────────────────────────────────────
echo ""
echo "[4/4] Checking SSH config..."
CONFIG="$SSH_DIR/config"
if [[ ! -f "$CONFIG" ]] || ! grep -q "github.com" "$CONFIG"; then
  cat >> "$CONFIG" << EOF

# ── GitHub ────────────────────────────────────────────────────────────────────
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/$KEY_NAME
    AddKeysToAgent yes

# ── Global defaults ───────────────────────────────────────────────────────────
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ConnectTimeout 10
EOF
  chmod 600 "$CONFIG"
  echo "  SSH config written"
else
  echo "  SSH config already has GitHub entry"
fi

# ── Show public key ───────────────────────────────────────────────────────────
echo ""
echo "=== Your public key (add to GitHub > Settings > SSH Keys) ==="
cat "${KEY_PATH}.pub"

# ── Test GitHub ───────────────────────────────────────────────────────────────
echo ""
echo "Testing GitHub connection..."
result=$(ssh -T git@github.com 2>&1)
if echo "$result" | grep -q "successfully authenticated"; then
  echo "GitHub SSH: OK"
else
  echo "GitHub SSH: Not yet authenticated"
  echo "Add the public key above to: https://github.com/settings/ssh/new"
  if $IS_MAC; then
    echo ""
    echo "Or copy it to clipboard:"
    echo "  pbcopy < ${KEY_PATH}.pub"
  fi
fi

echo ""
echo "Done."
