#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_DIR="${IMAGE_DIR_OVERRIDE:-$ROOT/assets/images}"
OUTPUT_DIR="${OUTPUT_DIR_OVERRIDE:-$ROOT/output/generated-10}"
WORK_DIR="${WORK_DIR_OVERRIDE:-$ROOT/tmp/generated-10}"
ACE_DURATION="${ACE_DURATION:-30}"
ACE_STEPS="${ACE_STEPS:-8}"
DIFFRHYTHM2_DURATION="${DIFFRHYTHM2_DURATION:-180}"
DIFFRHYTHM2_STEPS="${DIFFRHYTHM2_STEPS:-24}"
if [ "${DIFFRHYTHM2:-0}" = "1" ]; then
  MUSIC="${MUSIC_OVERRIDE:-$ROOT/assets/music/diffrhythm2/lofi-${DIFFRHYTHM2_DURATION}s.mp3}"
else
  MUSIC="${MUSIC_OVERRIDE:-$ROOT/assets/music/ace-step/ace-step-${ACE_DURATION}s-seed-20260725.wav}"
fi
COUNT="${COUNT:-10}"
DURATION="${DURATION:-3600}"
STATUS="$ROOT/tmp/render-progress.txt"
LOG="$ROOT/tmp/render-10.log"

mkdir -p "$OUTPUT_DIR" "$WORK_DIR" "$(dirname "$STATUS")"
QUEUE_STARTED_AT="$(date +%s)"
printf 'state=starting\ncompleted=0\ntotal=%s\nqueue_started_at=%s\n' "$COUNT" "$QUEUE_STARTED_AT" > "$STATUS"

for cmd in ffmpeg ffprobe; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Missing command: $cmd" >&2; exit 1; }
done

IMAGES=()
while IFS= read -r image; do
  IMAGES+=("$image")
done < <(find "$IMAGE_DIR" -maxdepth 1 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webp' \) | sort)
if [ "${#IMAGES[@]}" -eq 0 ]; then
  printf 'state=blocked\nreason=no-images\n' > "$STATUS"
  echo "No images found in $IMAGE_DIR" >&2
  exit 1
fi

if [ ! -s "$MUSIC" ]; then
  MUSIC_STARTED_AT="$(date +%s)"
  printf 'state=generating_music\ncompleted=0\ntotal=%s\nimages=%s\nqueue_started_at=%s\nmusic_started_at=%s\n' \
    "$COUNT" "${#IMAGES[@]}" "$QUEUE_STARTED_AT" "$MUSIC_STARTED_AT" > "$STATUS"
  echo "Generating $([ "${DIFFRHYTHM2:-0}" = "1" ] && echo DiffRhythm2 || echo ACE-Step) music: $MUSIC" >> "$LOG"
  mkdir -p "$(dirname "$MUSIC")"
  if [ "${DIFFRHYTHM2:-0}" = "1" ]; then
    "$ROOT/.venv-diffrhythm2/bin/python" "$ROOT/scripts/generate_music_diffrhythm2.py" \
      --duration "$DIFFRHYTHM2_DURATION" --steps "$DIFFRHYTHM2_STEPS" --output "$MUSIC" >> "$LOG" 2>&1
  else
    ACE_DEVICE=cpu "$ROOT/scripts/run_ace_step_music.sh" --duration "$ACE_DURATION" --seed 20260725 --steps "$ACE_STEPS" >> "$LOG" 2>&1
  fi
fi

if [ ! -s "$MUSIC" ]; then
  printf 'state=blocked\nreason=music-generation-failed\n' > "$STATUS"
  echo "Music generation failed: $MUSIC" >&2
  exit 1
fi

MUSIC_FINISHED_AT="$(date +%s)"
printf 'state=running\ncompleted=0\ntotal=%s\nimages=%s\nqueue_started_at=%s\nmusic_started_at=%s\nmusic_finished_at=%s\n' \
  "$COUNT" "${#IMAGES[@]}" "$QUEUE_STARTED_AT" "${MUSIC_STARTED_AT:-$QUEUE_STARTED_AT}" "$MUSIC_FINISHED_AT" > "$STATUS"
echo "Using ${#IMAGES[@]} images and $MUSIC" >> "$LOG"

for ((i=1; i<=COUNT; i++)); do
  OUT=$(printf '%s/pepe-lofi-%02d.mp4' "$OUTPUT_DIR" "$i")
  if [ -s "$OUT" ]; then
    printf 'state=running\ncompleted=%d\ntotal=%d\ncurrent=%d\npercent=%d\nfile=%s\nqueue_started_at=%s\nmusic_finished_at=%s\n' \
      "$i" "$COUNT" "$i" "$((i*100/COUNT))" "$OUT" "$QUEUE_STARTED_AT" "$MUSIC_FINISHED_AT" > "$STATUS"
    continue
  fi

  # Random choice, then deterministic input for reproducible progress/restarts.
  IMAGE="${IMAGES[$((RANDOM % ${#IMAGES[@]}))]}"
  CURRENT_STARTED_AT="$(date +%s)"
  printf 'state=running\ncompleted=%d\ntotal=%d\ncurrent=%d\npercent=%d\nimage=%s\nfile=%s\n' \
    "$((i-1))" "$COUNT" "$i" "$(((i-1)*100/COUNT))" "$IMAGE" "$OUT" > "$STATUS"
  printf 'queue_started_at=%s\nmusic_finished_at=%s\ncurrent_started_at=%s\n' \
    "$QUEUE_STARTED_AT" "$MUSIC_FINISHED_AT" "$CURRENT_STARTED_AT" >> "$STATUS"
  echo "[$i/$COUNT] $IMAGE -> $OUT" >> "$LOG"

  ffmpeg -hide_banner -loglevel warning -y \
    -loop 1 -i "$IMAGE" -stream_loop -1 -i "$MUSIC" -t "$DURATION" \
    -map 0:v:0 -map 1:a:0 \
    -vf "scale=1280:720:force_original_aspect_ratio=increase:flags=lanczos,crop=1280:720,format=yuv420p" \
    -r 24 -c:v libx264 -preset medium -crf 28 -pix_fmt yuv420p \
    -af "aresample=async=1:first_pts=0,afade=t=in:st=0:d=3,afade=t=out:st=$((DURATION-3)):d=3,loudnorm=I=-16:TP=-1.5:LRA=11" \
    -c:a aac -b:a 128k -ac 2 -movflags +faststart "$OUT" >> "$LOG" 2>&1

  printf 'state=running\ncompleted=%d\ntotal=%d\ncurrent=%d\npercent=%d\nimage=%s\nfile=%s\n' \
    "$i" "$COUNT" "$i" "$((i*100/COUNT))" "$IMAGE" "$OUT" > "$STATUS"
  printf 'queue_started_at=%s\nmusic_finished_at=%s\ncurrent_started_at=%s\ncurrent_finished_at=%s\n' \
    "$QUEUE_STARTED_AT" "$MUSIC_FINISHED_AT" "$CURRENT_STARTED_AT" "$(date +%s)" >> "$STATUS"
done

printf 'state=complete\ncompleted=%d\ntotal=%d\npercent=100\noutput=%s\nqueue_started_at=%s\nqueue_finished_at=%s\n' \
  "$COUNT" "$COUNT" "$OUTPUT_DIR" "$QUEUE_STARTED_AT" "$(date +%s)" > "$STATUS"
echo "COMPLETE: $COUNT videos in $OUTPUT_DIR" >> "$LOG"
