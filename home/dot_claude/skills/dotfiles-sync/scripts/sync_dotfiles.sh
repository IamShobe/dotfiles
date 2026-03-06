#!/bin/bash
set -euo pipefail

CHEZMOI_SOURCE="${HOME}/.local/share/chezmoi/home"
HOME_DIR="${HOME}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Tracked file mappings: local_path -> chezmoi_path
declare -A TRACKED_FILES=(
    ["${HOME_DIR}/.claude/hooks/start.py"]="dot_claude/hooks/executable_start.py"
    ["${HOME_DIR}/.claude/hooks/status.py"]="dot_claude/hooks/executable_status.py"
    ["${HOME_DIR}/.claude/hooks/notify.py"]="dot_claude/hooks/executable_notify.py"
    ["${HOME_DIR}/.claude/hooks/notify.sh"]="dot_claude/hooks/executable_notify.sh"
    ["${HOME_DIR}/.claude/hooks/focus-wezterm.sh"]="dot_claude/hooks/executable_focus-wezterm.sh"
    ["${HOME_DIR}/.claude/skills/chezmoi/SKILL.md"]="dot_claude/skills/chezmoi/SKILL.md"
    ["${HOME_DIR}/.claude/skills/chezmoi/evals/evals.json"]="dot_claude/skills/chezmoi/evals/evals.json"
    ["${HOME_DIR}/.claude/skills/wezterm-config/SKILL.md"]="dot_claude/skills/wezterm-config/SKILL.md"
    ["${HOME_DIR}/.claude/settings.json"]="dot_claude/dot_settings.json.tmpl"
    ["${HOME_DIR}/.claude/memory/MEMORY.md"]="dot_claude/memory/MEMORY.md"
    ["${HOME_DIR}/.config/wezterm/wezterm.lua"]="private_dot_config/wezterm/wezterm.lua"
    ["${HOME_DIR}/.mise.toml"]="dot_mise.toml"
    ["${HOME_DIR}/.mise.lock"]="dot_mise.lock"
)

echo -e "${BLUE}🔍 Scanning for changes in tracked files...${NC}\n"

# Check for changes
CHANGED_FILES=()
for local_path in "${!TRACKED_FILES[@]}"; do
    chezmoi_path="${TRACKED_FILES[$local_path]}"
    chezmoi_full_path="${CHEZMOI_SOURCE}/${chezmoi_path}"

    if [ ! -f "$local_path" ]; then
        continue
    fi

    if [ ! -f "$chezmoi_full_path" ]; then
        CHANGED_FILES+=("$local_path")
        continue
    fi

    # Compare files (ignoring executable bit and other metadata)
    if ! diff -q "$local_path" "$chezmoi_full_path" >/dev/null 2>&1; then
        CHANGED_FILES+=("$local_path")
    fi
done

if [ ${#CHANGED_FILES[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ No changes detected. Your dotfiles are in sync!${NC}"
    exit 0
fi

echo -e "${YELLOW}✏️  Modified files detected:${NC}"
for file in "${CHANGED_FILES[@]}"; do
    echo "  $file"
done
echo ""

# Show diffs
echo -e "${BLUE}📋 Showing diffs:${NC}\n"
for local_path in "${CHANGED_FILES[@]}"; do
    chezmoi_path="${TRACKED_FILES[$local_path]}"
    chezmoi_full_path="${CHEZMOI_SOURCE}/${chezmoi_path}"

    echo -e "${YELLOW}=== ${local_path} ===${NC}"
    if [ ! -f "$chezmoi_full_path" ]; then
        echo "[NEW FILE]"
        head -20 "$local_path"
    else
        diff -u "$chezmoi_full_path" "$local_path" || true
    fi
    echo ""
done

# Ask for confirmation
read -p "✅ Sync these changes to dotfiles? (yes/no): " -r
echo ""
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo -e "${YELLOW}Cancelled. No changes synced.${NC}"
    exit 0
fi

# Copy files to chezmoi
echo -e "${BLUE}📦 Syncing to dotfiles...${NC}"
for local_path in "${CHANGED_FILES[@]}"; do
    chezmoi_path="${TRACKED_FILES[$local_path]}"
    chezmoi_full_path="${CHEZMOI_SOURCE}/${chezmoi_path}"

    # Create directory if needed
    mkdir -p "$(dirname "$chezmoi_full_path")"

    # Copy file
    cp "$local_path" "$chezmoi_full_path"

    # Preserve executable bit if needed
    if [ -x "$local_path" ]; then
        chmod +x "$chezmoi_full_path"
    fi

    echo "✓ Copied $(basename "$local_path")"
done
echo ""

# Commit and push
cd "$CHEZMOI_SOURCE/.."
git add home/dot_claude home/private_dot_config home/dot_mise* home/run_onchange_after_3-install-mise-packages 2>/dev/null || true

# Create a descriptive commit message
COMMIT_MSG="Sync local configuration changes

Updated files:
$(printf '%s\n' "${CHANGED_FILES[@]}" | sed 's|^'"${HOME_DIR}"'||' | sed 's/^/  - /')"

git commit -m "$COMMIT_MSG" || {
    echo -e "${YELLOW}⚠️  No changes to commit (files may already be in sync)${NC}"
    exit 0
}

echo -e "${GREEN}✓ Committed: ${COMMIT_MSG:0:30}...${NC}"

# Push to remote
if git push origin main 2>/dev/null; then
    echo -e "${GREEN}✓ Pushed to origin/main${NC}"
    echo ""
    echo -e "${GREEN}Done! All changes synced to dotfiles repo.${NC}"
else
    echo -e "${YELLOW}⚠️  Could not push to remote. Please push manually.${NC}"
    echo "Run: cd ~/.local/share/chezmoi && git push origin main"
fi
