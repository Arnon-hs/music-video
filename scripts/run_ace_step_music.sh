#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT/ace-step-v1/.venv/bin/python" "$ROOT/scripts/generate_music_ace_step.py" "$@"
