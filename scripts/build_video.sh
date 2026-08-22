#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VISUAL="${VISUAL_OVERRIDE:-$ROOT/assets/visual-loop.mp4}"
AUDIO="${AUDIO_OVERRIDE:-$ROOT/assets/music/lofi-demo.wav}"
OUT="${OUTPUT_OVERRIDE:-$ROOT/output/agent-pepe-lofi-noncommercial-demo.mp4}"
REPORT="${REPORT_OVERRIDE:-$ROOT/metadata/build-report.txt}"
LABEL="${OUTPUT_LABEL:-NON_COMMERCIAL_DEMO}"
MUSIC_LICENSE_NOTE="${MUSIC_LICENSE_NOTE:-MusicGen CC-BY-NC 4.0; replace the MusicGen WAV before commercial release.}"
FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1
for file in "$VISUAL" "$AUDIO"; do [ -f "$file" ] || { echo "Missing input: $file"; exit 1; }; done
if [ -e "$OUT" ] && [ "$FORCE" -ne 1 ]; then echo "Refusing to overwrite $OUT. Re-run with --force."; exit 1; fi
mkdir -p "$(dirname "$OUT")" "$(dirname "$REPORT")"
DURATION="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")"
if [ "${REENCODE_VIDEO:-0}" = "1" ]; then
  ffmpeg -hide_banner -y -stream_loop -1 -i "$VISUAL" -i "$AUDIO" -t "$DURATION" -map 0:v:0 -map 1:a:0 -vf "fps=24,scale=1920:1080:flags=lanczos" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 320k -movflags +faststart "$OUT"
else
  # Faster assembly; use REENCODE_VIDEO=1 for a fully decoded/re-encoded delivery file.
  ffmpeg -hide_banner -y -stream_loop -1 -i "$VISUAL" -i "$AUDIO" -t "$DURATION" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 320k -movflags +faststart "$OUT"
fi
{
  echo "label=$LABEL"
  echo "output=$OUT"
  echo "duration_seconds=$DURATION"
  echo "size_bytes=$(wc -c < "$OUT" | tr -d ' ')"
  echo "video=H.264, 1920x1080, 24 fps, yuv420p"
  echo "audio=AAC, 320 kbps"
  echo "music_license=$MUSIC_LICENSE_NOTE"
  echo "image_credits=$ROOT/metadata/image-credits.json"
  [ -f "$ROOT/metadata/image-credits.json" ] && jq -r '.[] | "image_source=\(.file) | author=\(.author) | page=\(.pexels_page)"' "$ROOT/metadata/image-credits.json"
} > "$REPORT"
echo "Created $OUT — $LABEL"
echo "Report: $REPORT"
