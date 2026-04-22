#!/bin/bash
# Setup SSH keys on MacBook for bidirectional access with Laptop & Desktop
# Run: chmod +x setup-macbook.sh && ./setup-macbook.sh

set -e
echo "=== MacBook SSH Setup ==="

SSH_DIR="$HOME/.ssh"
mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

SCRIPT_DIR="$(cd "$(dirname "$0")/macbook" && pwd)"

# Install private key
cp "$SCRIPT_DIR/macbook_ed25519" "$SSH_DIR/id_ed25519_mesh"
chmod 600 "$SSH_DIR/id_ed25519_mesh"
echo "[OK] Private key installed"

# Install public key
cp "$SCRIPT_DIR/macbook_ed25519.pub" "$SSH_DIR/id_ed25519_mesh.pub"
chmod 644 "$SSH_DIR/id_ed25519_mesh.pub"
echo "[OK] Public key installed"

# Add all three machines' public keys to authorized_keys
if [ -f "$SSH_DIR/authorized_keys" ]; then
    # Append only keys not already present
    while IFS= read -r key; do
        grep -qF "$key" "$SSH_DIR/authorized_keys" 2>/dev/null || echo "$key" >> "$SSH_DIR/authorized_keys"
    done < "$SCRIPT_DIR/authorized_keys"
else
    cp "$SCRIPT_DIR/authorized_keys" "$SSH_DIR/authorized_keys"
fi
chmod 600 "$SSH_DIR/authorized_keys"
echo "[OK] authorized_keys updated (all 3 machines)"

# Add SSH config entries (won't duplicate if already present)
CONFIG="$SSH_DIR/config"
touch "$CONFIG"
chmod 600 "$CONFIG"

add_host() {
    local name="$1" comment="$2"
    if ! grep -q "^Host $name$" "$CONFIG" 2>/dev/null; then
        cat >> "$CONFIG" << EOF

# $comment
Host $name
    IdentityFile ~/.ssh/id_ed25519_mesh
    User User
    StrictHostKeyChecking accept-new
EOF
        echo "[OK] Added SSH config: $name"
    else
        echo "[SKIP] SSH config '$name' already exists"
    fi
}

add_host "desktop" "Windows Desktop (CLX-DESKTOP) — fill in HostName"
add_host "laptop"  "Windows Laptop (i7) — fill in HostName"

echo ""
echo "=== MANUAL STEPS ==="
echo "1. Edit ~/.ssh/config and fill in HostName for 'desktop' and 'laptop'"
echo "   Use IP addresses or hostnames (e.g., 192.168.1.x or Tailscale addresses)"
echo "2. Enable Remote Login on this Mac:"
echo "   System Settings > General > Sharing > Remote Login > ON"
echo "3. Test: ssh desktop   and   ssh laptop"
echo ""
echo "Done!"
