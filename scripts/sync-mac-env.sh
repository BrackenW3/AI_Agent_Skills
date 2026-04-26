#!/bin/bash
# Run this on Mac to sync all env vars from master.env to ~/.zshrc
# Usage: bash sync-mac-env.sh

GH_TOKEN="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"

echo "Fetching master.env from GitHub..."
curl -s -H "Authorization: Bearer $GH_TOKEN" \
  "https://api.github.com/repos/BrackenW3/AI_Agent_Skills/contents/.env" \
  | python3 -c "import sys,json,base64; d=json.load(sys.stdin); print(base64.b64decode(d['content']).decode())" \
  > /tmp/master.env

echo "Found $(grep -c '=' /tmp/master.env) env var lines"

# Back up zshrc
cp ~/.zshrc ~/.zshrc.bak.$(date +%Y%m%d)

# Remove old env var block if exists
sed -i '' '/# BEGIN AUTO-ENV/,/# END AUTO-ENV/d' ~/.zshrc 2>/dev/null || true

# Add new block
echo "" >> ~/.zshrc
echo "# BEGIN AUTO-ENV - synced $(date)" >> ~/.zshrc

while IFS= read -r line; do
  # Skip comments, empty lines, Windows-only vars
  [[ "$line" =~ ^#.*$ ]] && continue
  [[ -z "$line" ]] && continue
  [[ "$line" =~ ^NPM_CONFIG_PREFIX ]] && continue
  [[ "$line" =~ ^WRANGLER_HOME ]] && continue
  [[ "$line" =~ NEEDS_SETTING ]] && continue
  
  key="${line%%=*}"
  val="${line#*=}"
  
  # Skip if already set in zshrc above the auto block
  grep -q "export $key=" ~/.zshrc 2>/dev/null && continue
  
  echo "export $key=\"$val\"" >> ~/.zshrc
done < /tmp/master.env

echo "# END AUTO-ENV" >> ~/.zshrc

echo "Done! Run: source ~/.zshrc"
