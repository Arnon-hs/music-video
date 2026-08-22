#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_DIR="$ROOT/assets/images"
MUSIC_DIR="$ROOT/assets/music/album-20260725"
OUTPUT_DIR="$ROOT/output"
WORK_DIR="$ROOT/tmp/album-20260725"
STATUS="$ROOT/tmp/render-progress.txt"
LOG="$ROOT/tmp/album-render.log"
COUNT="${TRACK_COUNT:-10}"
TRACK_SECONDS="${TRACK_SECONDS:-360}"
FADE_SECONDS="${FADE_SECONDS:-3}"
TOTAL_SECONDS="${TOTAL_SECONDS:-3600}"
STEPS="${ACE_STEPS:-16}"
PROMPT_BASE="Clean polished instrumental lo-fi hip-hop beat, 86 BPM, steady swung drums, warm round sub bass, mellow Rhodes chord progression, musical electric piano, tasteful muted guitar, subtle soft synth accents, coherent tonal harmony, clear stereo mix, gentle tape saturation, dusty vinyl texture, relaxed rainy-night atmosphere, no vocals, no speech, no sound effects, no harsh noise, no distortion, no screaming, no glitch, no experimental abstract noise."

mkdir -p "$MUSIC_DIR" "$OUTPUT_DIR" "$WORK_DIR"
IMAGES=()
while IFS= read -r image; do IMAGES+=("$image"); done < <(find "$IMAGE_DIR" -maxdepth 1 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webp' \) | sort)
[ "${#IMAGES[@]}" -gt 0 ] || { printf 'state=blocked\nreason=no-images\n' > "$STATUS"; exit 1; }

QUEUE_STARTED_AT="$(date +%s)"
IMAGE="${IMAGES[$((RANDOM % ${#IMAGES[@]}))]}"
printf 'state=generating_music\ncompleted=0\ntotal=%s\nimages=%s\nqueue_started_at=%s\nimage=%s\ntrack_seconds=%s\nfade_seconds=%s\n' \
  "$COUNT" "${#IMAGES[@]}" "$QUEUE_STARTED_AT" "$IMAGE" "$TRACK_SECONDS" "$FADE_SECONDS" > "$STATUS"
: > "$LOG"

TRACKS=()
for ((i=1; i<=COUNT; i++)); do
  seed=$((20260725 + i * 7919))
  track=$(printf '%s/ace-step-%ss-seed-%s.wav' "$MUSIC_DIR" "$TRACK_SECONDS" "$seed")
  TRACKS+=("$track")
  if [ -s "$track" ]; then
    printf 'state=generating_music\ncompleted=%d\ntotal=%d\ncurrent=%d\nmusic_track=%d\nmusic_percent=100\nmusic_step=ready\ntrack_file=%s\nqueue_started_at=%s\nimage=%s\n' \
      "$((i-1))" "$COUNT" "$i" "$i" "$track" "$QUEUE_STARTED_AT" "$IMAGE" > "$STATUS"
    continue
  fi
  TRACK_STARTED_AT="$(date +%s)"
  printf 'state=generating_music\ncompleted=%d\ntotal=%d\ncurrent=%d\nmusic_track=%d\nmusic_percent=0\nmusic_step=0/%s\ntrack_started_at=%s\nqueue_started_at=%s\nimage=%s\n' \
    "$((i-1))" "$COUNT" "$i" "$i" "$STEPS" "$TRACK_STARTED_AT" "$QUEUE_STARTED_AT" "$IMAGE" > "$STATUS"
  echo "[$i/$COUNT] Generating $track" >> "$LOG"
  ACE_DEVICE=cpu MUSIC_OUTPUT_DIR="$MUSIC_DIR" "$ROOT/scripts/run_ace_step_music.sh" \
    --duration "$TRACK_SECONDS" --seed "$seed" --steps "$STEPS" \
    --prompt "$PROMPT_BASE Variation $i: change the chord voicing, drum groove, and lead texture while keeping the same lo-fi atmosphere." >> "$LOG" 2>&1
done

MUSIC_FINISHED_AT="$(date +%s)"
printf 'state=assembling_audio\ncompleted=0\ntotal=%d\nmusic_percent=100\nqueue_started_at=%s\nmusic_finished_at=%s\nimage=%s\n' \
  "$COUNT" "$QUEUE_STARTED_AT" "$MUSIC_FINISHED_AT" "$IMAGE" > "$STATUS"

FILTER=""
CHAIN="[0:a]"
for ((i=1; i<COUNT; i++)); do
  next="x$i"
  FILTER+="${CHAIN}[$i:a]acrossfade=d=${FADE_SECONDS}:c1=tri:c2=tri[$next];"
  CHAIN="[$next]"
done
FILTER+="${CHAIN}apad,atrim=duration=${TOTAL_SECONDS}[aout]"
INPUTS=()
for track in "${TRACKS[@]}"; do INPUTS+=("-i" "$track"); done
MIX="$WORK_DIR/lofi-album-1h.wav"
ffmpeg -hide_banner -loglevel warning -y "${INPUTS[@]}" -filter_complex "$FILTER" -map '[aout]' -c:a pcm_s16le "$MIX" >> "$LOG" 2>&1

VIDEO="$OUTPUT_DIR/pepe-lofi-one-hour.mp4"
VIDEO_STARTED_AT="$(date +%s)"
printf 'state=rendering_video\ncompleted=0\ntotal=%d\npercent=0\ncurrent=1\nvideo_started_at=%s\nqueue_started_at=%s\nmusic_finished_at=%s\nimage=%s\nfile=%s\n' \
  "$COUNT" "$VIDEO_STARTED_AT" "$QUEUE_STARTED_AT" "$MUSIC_FINISHED_AT" "$IMAGE" "$VIDEO" > "$STATUS"
VIDEO_PROGRESS="$WORK_DIR/video-progress.txt"
ffmpeg -hide_banner -loglevel warning -y -progress "$VIDEO_PROGRESS" -loop 1 -i "$IMAGE" -i "$MIX" -t "$TOTAL_SECONDS" \
  -map 0:v:0 -map 1:a:0 \
  -vf "scale=1280:720:force_original_aspect_ratio=decrease:flags=lanczos,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p" \
  -r 24 -c:v libx264 -preset medium -crf 28 -pix_fmt yuv420p \
  -c:a aac -b:a 96k -ac 2 -movflags +faststart "$VIDEO" >> "$LOG" 2>&1 &
FFMPEG_PID=$!
while kill -0 "$FFMPEG_PID" 2>/dev/null; do
  OUT_US="$(awk -F= '$1=="out_time_us"{v=$2} END{print v+0}' "$VIDEO_PROGRESS" 2>/dev/null || echo 0)"
  PERCENT=$((OUT_US * 100 / 1000000 / TOTAL_SECONDS))
  [ "$PERCENT" -gt 99 ] && PERCENT=99
  printf 'state=rendering_video\ncompleted=0\ntotal=%d\npercent=%d\ncurrent=1\nvideo_started_at=%s\nqueue_started_at=%s\nmusic_finished_at=%s\nimage=%s\nfile=%s\n' \
    "$COUNT" "$PERCENT" "$VIDEO_STARTED_AT" "$QUEUE_STARTED_AT" "$MUSIC_FINISHED_AT" "$IMAGE" "$VIDEO" > "$STATUS"
  sleep 5
done
wait "$FFMPEG_PID"

QUEUE_FINISHED_AT="$(date +%s)"
printf 'state=complete\ncompleted=10\ntotal=10\npercent=100\nvideo_started_at=%s\nvideo_finished_at=%s\nqueue_started_at=%s\nqueue_finished_at=%s\nmusic_finished_at=%s\nimage=%s\nfile=%s\noutput=%s\n' \
  "$VIDEO_STARTED_AT" "$QUEUE_FINISHED_AT" "$QUEUE_STARTED_AT" "$QUEUE_FINISHED_AT" "$MUSIC_FINISHED_AT" "$IMAGE" "$VIDEO" "$OUTPUT_DIR" > "$STATUS"
echo "COMPLETE $VIDEO" >> "$LOG"
