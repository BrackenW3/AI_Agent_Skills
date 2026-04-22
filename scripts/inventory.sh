#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# inventory.sh — Clean directory inventory (gitignore-style filtering)
#
# Usage:
#   bash inventory.sh [TARGET_DIR] [OPTIONS]
#
# Options:
#   --depth N        Max folder depth shown (default: 4)
#   --min-size N     Only show dirs larger than N KB (default: 0)
#   --top N          Show top N largest directories (default: 20)
#   --no-tree        Skip tree view, just show summary
#   --output FILE    Save report to FILE (default: prints to stdout)
#
# Examples:
#   bash inventory.sh ~/williambracken
#   bash inventory.sh ~/williambracken --top 30 --output ~/inventory-report.txt
# ─────────────────────────────────────────────────────────────────────────────

TARGET="${1:-$HOME}"
DEPTH=4
TOP=20
MIN_SIZE=0
OUTPUT=""
SHOW_TREE=true

# ── Parse flags ───────────────────────────────────────────────────────────────
shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --depth)    DEPTH="$2"; shift 2 ;;
    --min-size) MIN_SIZE="$2"; shift 2 ;;
    --top)      TOP="$2"; shift 2 ;;
    --output)   OUTPUT="$2"; shift 2 ;;
    --no-tree)  SHOW_TREE=false; shift ;;
    *) shift ;;
  esac
done

# ── Directories to prune entirely (never enter) ───────────────────────────────
PRUNE_DIRS=(
  node_modules .npm .pnpm-store
  .venv venv env .env __pycache__ .mypy_cache .ruff_cache .pytest_cache
  .tox .nox site-packages eggs
  dist build out .next .nuxt .svelte-kit .parcel-cache .turbo .cache
  .cargo/registry .cargo/git
  .gradle .m2 target
  vendor Pods
  .git "*.git"
  Library "Application Support" Caches Containers
  ".Trash" ".Spotlight-V100" ".fseventsd" ".DocumentRevisions-V100"
  ".TemporaryItems" ".DS_Store"
  ".ollama/models"  # large model blobs
  ".lmstudio/models"
  "huggingface/hub"
  ".keras/datasets"
  ".local/share/trash"
)

# ── Files to ignore in listings ──────────────────────────────────────────────
IGNORE_FILES=(
  "*.pyc" "*.pyo" "*.class" "*.o" "*.a" "*.so" "*.dylib"
  "*.log" "*.tmp" "*.temp" "*.lock"
  ".DS_Store" "Thumbs.db"
  "package-lock.json" "yarn.lock" "pnpm-lock.yaml" "poetry.lock"
  "*.min.js" "*.min.css" "*.map"
)

# Build prune expression for find
PRUNE_EXPR=()
for d in "${PRUNE_DIRS[@]}"; do
  PRUNE_EXPR+=(-name "$d" -prune -o)
done

# ── Output setup ──────────────────────────────────────────────────────────────
REPORT=""
print_line() { REPORT+="$1"$'\n'; }

# ─────────────────────────────────────────────────────────────────────────────
print_line "════════════════════════════════════════════════════════════"
print_line " DIRECTORY INVENTORY: $(realpath "$TARGET")"
print_line " Generated: $(date '+%Y-%m-%d %H:%M')"
print_line "════════════════════════════════════════════════════════════"
print_line ""

# ── Total size (fast, excludes pruned dirs) ───────────────────────────────────
print_line "── TOTAL SIZE (excluding node_modules, .venv, models, etc.) ──"
TOTAL=$(find "$TARGET" \
  "${PRUNE_EXPR[@]}" \
  -name ".git" -prune -o \
  -type f -print 2>/dev/null \
  | xargs du -sk 2>/dev/null | awk '{sum+=$1} END {printf "%.1f GB", sum/1024/1024}')
print_line "  $TOTAL  (real content, noise stripped)"
print_line ""

# ── Top N largest dirs ────────────────────────────────────────────────────────
print_line "── TOP $TOP LARGEST DIRECTORIES (content only) ──"
find "$TARGET" \
  "${PRUNE_EXPR[@]}" \
  -mindepth 1 -maxdepth $((DEPTH)) \
  -type d -print 2>/dev/null \
  | while read -r dir; do
      size=$(find "$dir" \
        "${PRUNE_EXPR[@]}" \
        -type f -print 2>/dev/null \
        | xargs du -sk 2>/dev/null | awk '{s+=$1} END {print s+0}')
      echo "$size $dir"
    done \
  | sort -rn \
  | head -"$TOP" \
  | awk '{
      size=$1; $1="";
      path=substr($0,2);
      if (size >= 1048576) printf "  %6.1f GB  %s\n", size/1048576, path
      else if (size >= 1024) printf "  %6.1f MB  %s\n", size/1024, path
      else printf "  %6.0f KB  %s\n", size, path
    }' \
  | while read -r line; do print_line "$line"; done
print_line ""

# ── Git repos found ───────────────────────────────────────────────────────────
print_line "── GIT REPOSITORIES ──"
find "$TARGET" \
  -name node_modules -prune -o \
  -name .venv -prune -o \
  -maxdepth $((DEPTH + 1)) \
  -name ".git" -type d -print 2>/dev/null \
  | sed 's|/.git$||' \
  | sort \
  | while read -r repo; do
      branch=$(git -C "$repo" branch --show-current 2>/dev/null || echo "?")
      last=$(git -C "$repo" log -1 --format="%cr" 2>/dev/null || echo "no commits")
      remote=$(git -C "$repo" remote get-url origin 2>/dev/null | sed 's|https://github.com/||; s|git@github.com:||' || echo "local only")
      print_line "  $(basename "$repo")/"
      print_line "    branch: $branch | last commit: $last"
      print_line "    remote: $remote"
    done
print_line ""

# ── Config / dotfile summary ──────────────────────────────────────────────────
print_line "── CONFIG & DOTFILES (hidden dirs at depth 1) ──"
find "$TARGET" -maxdepth 1 -name ".*" -type d 2>/dev/null | sort | while read -r d; do
  size=$(du -sk "$d" 2>/dev/null | awk '{print $1}')
  if (( size >= 1024 )); then
    printf "  %-30s  %6.1f MB\n" "$(basename "$d")/" "$(echo "scale=1; $size/1024" | bc)" | while read -r l; do print_line "$l"; done
  else
    printf "  %-30s  %6d KB\n" "$(basename "$d")/" "$size" | while read -r l; do print_line "$l"; done
  fi
done
print_line ""

# ── Tree view ─────────────────────────────────────────────────────────────────
if $SHOW_TREE; then
  print_line "── DIRECTORY TREE (depth $DEPTH, noise excluded) ──"
  if command -v tree &>/dev/null; then
    TREE_IGNORE="node_modules|.venv|venv|__pycache__|.git|dist|build|.next|.cache|Library|Caches|Pods|vendor|*.pyc"
    tree "$TARGET" \
      -d \
      -L $DEPTH \
      -I "$TREE_IGNORE" \
      --noreport \
      2>/dev/null | while read -r l; do print_line "$l"; done
  else
    # fallback: find-based tree
    find "$TARGET" \
      "${PRUNE_EXPR[@]}" \
      -mindepth 1 -maxdepth $DEPTH \
      -type d -print 2>/dev/null \
      | sed "s|$TARGET/||; s|[^/]*/|  |g; s|  \([^/]*\)$|└─ \1|" \
      | while read -r l; do print_line "$l"; done
  fi
  print_line ""
fi

# ── Model/AI assets ───────────────────────────────────────────────────────────
print_line "── AI MODELS & LARGE ASSETS (if any) ──"
find "$HOME" -maxdepth 5 \( \
  -name "*.gguf" -o -name "*.ggml" -o \
  -name "*.safetensors" -o -name "*.bin" -o \
  -name "*.pt" -o -name "*.pth" \
  \) -type f 2>/dev/null \
  | while read -r f; do
      size=$(du -sh "$f" 2>/dev/null | awk '{print $1}')
      print_line "  $size  $f"
    done | head -20
print_line ""

# ── Summary stats ─────────────────────────────────────────────────────────────
print_line "── QUICK STATS ──"
repo_count=$(find "$TARGET" -name ".git" -type d -not -path "*/node_modules/*" 2>/dev/null | wc -l | tr -d ' ')
py_count=$(find "$TARGET" "${PRUNE_EXPR[@]}" -name "*.py" -type f -print 2>/dev/null | wc -l | tr -d ' ')
js_count=$(find "$TARGET" "${PRUNE_EXPR[@]}" -name "*.js" -o -name "*.ts" -type f -print 2>/dev/null | wc -l | tr -d ' ')
print_line "  Git repos:        $repo_count"
print_line "  Python files:     $py_count"
print_line "  JS/TS files:      $js_count"
print_line ""
print_line "════════════════════════════════════════════════════════════"

# ── Output ────────────────────────────────────────────────────────────────────
if [[ -n "$OUTPUT" ]]; then
  echo "$REPORT" > "$OUTPUT"
  echo "Report saved to: $OUTPUT"
else
  echo "$REPORT"
fi
