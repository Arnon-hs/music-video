#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export VISUAL_OVERRIDE="$ROOT/assets/visual-loop-energetic.mp4"
export AUDIO_OVERRIDE="$ROOT/assets/music/energetic/lofi-demo.wav"
export OUTPUT_OVERRIDE="$ROOT/output/agent-pepe-lofi-energetic-noncommercial-demo.mp4"
export REENCODE_VIDEO=1
exec "$ROOT/scripts/build_video.sh" --force
