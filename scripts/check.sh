#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -m unittest discover -s tests -v
python3 -m compileall -q music_video_cli.py scripts tests

for file in music-video scripts/*.sh; do
  bash -n "$file"
done

python3 scripts/check_repo_hygiene.py

./music-video genres --json | python3 -c 'import json, sys; assert len(json.load(sys.stdin)) >= 10'
./music-video doctor --json | python3 -c 'import json, sys; assert len(json.load(sys.stdin)["backends"]) == 4'
./music-video status --json | python3 -c 'import json, sys; assert isinstance(json.load(sys.stdin), dict)'

for backend in musicgen ace-step diffrhythm2 stable-audio3; do
  ./music-video generate --backend "$backend" --genre techno --duration 60 --dry-run >/dev/null
done

git diff --check

if command -v shellcheck >/dev/null 2>&1; then
  shellcheck music-video scripts/*.sh
else
  echo "NOTE: shellcheck is not installed; bash syntax was checked."
fi

echo "All repository checks passed."
