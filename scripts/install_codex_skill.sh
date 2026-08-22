#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_skill="$repo_root/.agents/skills/music-video-generator"
user_skills_root="${CODEX_USER_SKILLS_DIR:-${HOME}/.agents/skills}"
target_skill="$user_skills_root/music-video-generator"

[ -f "$source_skill/SKILL.md" ] || { echo "Missing repository skill: $source_skill" >&2; exit 1; }
mkdir -p "$user_skills_root"

if [ -L "$target_skill" ] && [ "$(readlink "$target_skill")" = "$source_skill" ]; then
  echo "Skill is already connected: $target_skill"
  exit 0
fi
if [ -e "$target_skill" ] || [ -L "$target_skill" ]; then
  echo "Refusing to replace existing path: $target_skill" >&2
  echo "Move it aside or set CODEX_USER_SKILLS_DIR to another directory." >&2
  exit 1
fi

ln -s "$source_skill" "$target_skill"
echo "Connected Music Video Generator skill: $target_skill -> $source_skill"
echo "Invoke it with: \$music-video-generator"
echo "Codex detects skill changes automatically; restart Codex if it does not appear."
