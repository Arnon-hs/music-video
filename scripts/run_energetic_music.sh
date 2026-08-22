#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export FORCE_CPU=1
export MUSIC_DIR_OVERRIDE="$ROOT/assets/music/energetic"
export MUSIC_PROMPT_OVERRIDE="Instrumental energetic lo-fi hip-hop, 96 BPM, minor key, punchy swung drums, crisp vinyl texture, warm sub bass, jazzy Rhodes stabs, chopped original guitar fragments, bright soft synth arpeggios, neon rainy night ambience, playful surreal internet mood, no lead vocal, no singing, no recognisable melody."
exec "$ROOT/.venv/bin/python" -u "$ROOT/scripts/generate_music.py"
