#!/usr/bin/env bash
# Install cd-skills for Claude Code and/or Antigravity.
#
#   ./install.sh claude                     # ~/.claude/skills (all your Claude Code projects)
#   ./install.sh claude-project ~/code/app  # <project>/.claude/skills
#   ./install.sh antigravity ~/code/app     # <project>/.agents/skills (Antigravity workspace)
#   ./install.sh --dest /some/skills/dir    # any other skills folder (e.g. Antigravity global)
#
# Options:
#   --only cd-a,cd-b   install just these skills (default: every skill in skills/)
#   --copy             copy instead of symlink (symlinks mean `git pull` updates every install)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="link"; ONLY=""; DEST=""

usage() { sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }

pos=()
while [ $# -gt 0 ]; do
  case "$1" in
    --copy) MODE="copy" ;;
    --only) ONLY="${2:-}"; shift ;;
    --dest) DEST="${2:-}"; [ -n "$DEST" ] || usage; shift ;;
    -h|--help) usage ;;
    *) pos+=("$1") ;;
  esac
  shift
done

if [ -z "$DEST" ]; then
  case "${pos[0]:-}" in
    claude)         DEST="$HOME/.claude/skills" ;;
    claude-project) [ -n "${pos[1]:-}" ] || usage; DEST="${pos[1]}/.claude/skills" ;;
    antigravity)    [ -n "${pos[1]:-}" ] || usage; DEST="${pos[1]}/.agents/skills" ;;
    *)              usage ;;
  esac
fi

mkdir -p "$DEST"
count=0
for dir in "$REPO"/skills/*/; do
  s="$(basename "$dir")"
  [ -f "$dir/SKILL.md" ] || continue
  if [ -n "$ONLY" ] && [[ ",$ONLY," != *",$s,"* ]]; then continue; fi
  target="$DEST/$s"
  if [ -e "$target" ] || [ -L "$target" ]; then rm -rf "$target"; fi
  if [ "$MODE" = "copy" ]; then cp -R "$REPO/skills/$s" "$target"; else ln -s "$REPO/skills/$s" "$target"; fi
  echo "Installed $s -> $target ($MODE)"
  count=$((count + 1))
done
[ "$count" -gt 0 ] || { echo "No skills matched."; exit 1; }
echo "Done ($count skill(s)). Start a new agent session so they're picked up."
