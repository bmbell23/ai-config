#!/bin/bash
# Link each skill in this repo into every agent's skills dir.
# Per-skill links only: the skills dirs also hold tool-managed content (synced/, .trash/).
# Never replaces a real file or dir; warns and skips instead.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGETS=("$HOME/.claude/skills" "$HOME/.claude-work/skills" "$HOME/.augment/skills")

for target in "${TARGETS[@]}"; do
    [ -d "$(dirname "$target")" ] || { echo "skip $target (no $(dirname "$target"))"; continue; }
    mkdir -p "$target"
    for skill in "$REPO"/skills/*/; do
        name="$(basename "$skill")"
        link="$target/$name"
        if [ -L "$link" ]; then
            ln -sfn "${skill%/}" "$link"
        elif [ -e "$link" ]; then
            echo "WARN $link exists and is not a link; left alone"
            continue
        else
            ln -s "${skill%/}" "$link"
        fi
        echo "ok   $link -> ${skill%/}"
    done
done
