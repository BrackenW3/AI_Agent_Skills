#!/bin/bash
# Mac Ollama Setup - Download optimized models to external SSD
# Run from Mac terminal: bash mac_ollama_setup.sh

set -e
MODELS_DIR="/Volumes/APFS_1TB/Ollama"
mkdir -p "$MODELS_DIR"

# Point Ollama to external SSD
export OLLAMA_MODELS="$MODELS_DIR"

# Add to zshrc if not already there
if ! grep -q "OLLAMA_MODELS" ~/.zshrc 2>/dev/null; then
    echo "export OLLAMA_MODELS=\"$MODELS_DIR\"" >> ~/.zshrc
    echo "Added OLLAMA_MODELS to ~/.zshrc"
fi

# Start Ollama if not running
if ! pgrep -x "ollama" > /dev/null; then
    open /Applications/Ollama.app
    sleep 5
fi

echo "=== Downloading optimized Mac M3 Pro models ==="
echo "Models will be saved to: $MODELS_DIR"

# Tier 0 - Always available, fast
echo "--- Tier 0: Fast/embedding ---"
ollama pull nomic-embed-text          # embeddings
ollama pull llama3.2:3b               # ultra fast, 2GB

# Tier 1 - Daily driver  
echo "--- Tier 1: Daily driver ---"
ollama pull qwen2.5:7b                # best 7B general
ollama pull qwen2.5-coder:7b         # coding

# Tier 2 - Quality (M3 Pro can handle these well)
echo "--- Tier 2: Quality ---"
ollama pull gemma3:12b                # Google's best for Mac
ollama pull qwen3:8b                  # latest Qwen, strong reasoning
ollama pull deepseek-r1:8b            # reasoning specialist

# Tier 3 - Heavy (will be slow but possible on 18GB M3 Pro)
echo "--- Tier 3: Heavy (slow but capable) ---"
ollama pull qwen2.5-coder:14b        # best local coder
# ollama pull gemma3:27b             # uncomment if you have space

echo ""
echo "=== Models downloaded to $MODELS_DIR ==="
echo ""
echo "Test with: ollama run qwen2.5:7b 'Hello, test'"
echo ""
echo "Add to your tools:"
echo "  n8n: HTTP node -> http://localhost:11434/api/generate"
echo "  Claude Code: export OLLAMA_BASE_URL=http://localhost:11434"
