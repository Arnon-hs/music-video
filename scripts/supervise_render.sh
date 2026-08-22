#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MUSIC="$ROOT/assets/music/ace-step/ace-step-60s-seed-20260725.wav"
STATUS="$ROOT/tmp/render-progress.txt"
LOG="$ROOT/tmp/render-10.log"
MUSIC_PID="${1:-}"

while [ -n "$MUSIC_PID" ] && kill -0 "$MUSIC_PID" 2>/dev/null; do
  sleep 10
done

if [ ! -s "$MUSIC" ]; then
  printf 'state=blocked\nreason=ace-step-did-not-produce-audio\n' > "$STATUS"
  echo "ACE-Step ended without producing $MUSIC" >> "$LOG"
  exit 1
fi

exec "$ROOT/scripts/render_random_10h_videos.sh"
