#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MUSIC_DIR="${MUSIC_DIR_OVERRIDE:-$ROOT/assets/music/diffrhythm2-playlist}"
OUTPUT_DIR="${OUTPUT_DIR_OVERRIDE:-$ROOT/output}"
WORK_DIR="${WORK_DIR_OVERRIDE:-$ROOT/tmp/diffrhythm2-playlist}"
STATUS="$ROOT/tmp/render-progress.txt"
LOG="$ROOT/tmp/diffrhythm2-playlist.log"
COUNT="${TRACK_COUNT:-12}"
BASE_SECONDS="${BASE_SECONDS:-180}"
TRACK_SECONDS="${TRACK_SECONDS:-303}"
FADE_SECONDS="${FADE_SECONDS:-3}"
TOTAL_SECONDS="${TOTAL_SECONDS:-3600}"
STEPS="${DIFFRHYTHM2_STEPS:-24}"
CFG="${DIFFRHYTHM2_CFG:-1.5}"

if [ "$COUNT" -lt 10 ] || [ "$COUNT" -gt 15 ]; then
  echo "TRACK_COUNT must be between 10 and 15" >&2
  exit 1
fi
mkdir -p "$MUSIC_DIR" "$OUTPUT_DIR" "$WORK_DIR" "$ROOT/tmp"
: > "$LOG"

on_error() {
  code=$?
  printf 'state=blocked\ncompleted=0\ntotal=%s\nmodel=DiffRhythm2\nreason=sequential_generation_failed\nerror=playlist pipeline exited with code %s\n' "$COUNT" "$code" > "$STATUS"
  exit "$code"
}
trap on_error ERR

IMAGE_DIR="$ROOT/assets/images"
IMAGES=()
while IFS= read -r image; do IMAGES+=("$image"); done < <(find "$IMAGE_DIR" -maxdepth 1 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webp' \) | sort)
[ "${#IMAGES[@]}" -gt 0 ] || { printf 'state=blocked\nreason=no-images\n' > "$STATUS"; exit 1; }

VARIANTS=(rainy-cafe midnight-library morning-window fireplace neon-street cloudy-day small-bookshop train-ride after-hours garden-rain vinyl-basement dawn)
QUEUE_STARTED_AT="$(date +%s)"
printf 'state=generating_music\ncompleted=0\ntotal=%s\nimages=%s\ntrack_seconds=%s\nbase_seconds=%s\nqueue_started_at=%s\nmodel=DiffRhythm2\n' \
  "$COUNT" "${#IMAGES[@]}" "$TRACK_SECONDS" "$BASE_SECONDS" "$QUEUE_STARTED_AT" > "$STATUS"

TRACKS=()
MISSING_BASE=0
for ((i=1; i<=COUNT; i++)); do
  variant="${VARIANTS[$(((i-1) % ${#VARIANTS[@]}))]}"
  base="$WORK_DIR/base-$(printf '%02d' "$i")-${variant}.mp3"
  final="$MUSIC_DIR/track-$(printf '%02d' "$i")-${variant}.mp3"
  TRACKS+=("$final")
  [ -s "$base" ] || MISSING_BASE=1
done
if [ "$MISSING_BASE" -eq 1 ]; then
  echo "Generating $COUNT DiffRhythm2 tracks sequentially (one process per track)" >> "$LOG"
  for ((i=1; i<=COUNT; i++)); do
    variant="${VARIANTS[$(((i-1) % ${#VARIANTS[@]}))]}"
    base="$WORK_DIR/base-$(printf '%02d' "$i")-${variant}.mp3"
    if [ ! -s "$base" ]; then
      printf 'state=generating_music\ncompleted=%d\ntotal=%d\nmusic_track=%d\nmusic_percent=0\nvariant=%s\nqueue_started_at=%s\nmodel=DiffRhythm2\nmode=sequential\n' \
        "$((i-1))" "$COUNT" "$i" "$variant" "$QUEUE_STARTED_AT" > "$STATUS"
      echo "Starting track $i/$COUNT: $variant" >> "$LOG"
      "$ROOT/.venv-diffrhythm2/bin/python" "$ROOT/scripts/generate_music_diffrhythm2.py" \
        --duration "$BASE_SECONDS" --steps "$STEPS" --cfg-strength "$CFG" \
        --variant "$variant" --song-name "base_$(printf '%02d' "$i")_${variant}" \
        --seed "$((424200 + i))" --output "$base" >> "$LOG" 2>&1
      test -s "$base"
      echo "Finished track $i/$COUNT: $base" >> "$LOG"
    fi
  done
fi
for ((i=1; i<=COUNT; i++)); do
  variant="${VARIANTS[$(((i-1) % ${#VARIANTS[@]}))]}"
  base="$WORK_DIR/base-$(printf '%02d' "$i")-${variant}.mp3"
  final="$MUSIC_DIR/track-$(printf '%02d' "$i")-${variant}.mp3"
  if [ ! -s "$final" ]; then
    printf 'state=assembling_track\ncompleted=%d\ntotal=%d\ncurrent=%d\nmusic_track=%d\nvariant=%s\nqueue_started_at=%s\nmodel=DiffRhythm2\n' \
      "$((i-1))" "$COUNT" "$i" "$i" "$variant" "$QUEUE_STARTED_AT" > "$STATUS"
    # One generated 180s piece becomes a ~303s track through a gentle internal
    # repeat/crossfade; the album itself gets another crossfade between tracks.
    ffmpeg -hide_banner -loglevel warning -y -i "$base" -i "$base" \
      -filter_complex "[0:a][1:a]acrossfade=d=8:c1=tri:c2=tri,atrim=duration=${TRACK_SECONDS},afade=t=in:st=0:d=2,afade=t=out:st=$((TRACK_SECONDS-2)):d=2[a]" \
      -map '[a]' -c:a libmp3lame -q:a 2 "$final" >> "$LOG" 2>&1
  fi
done

MUSIC_FINISHED_AT="$(date +%s)"
printf 'state=assembling_audio\ncompleted=0\ntotal=%s\nmusic_percent=100\ntrack_count=%s\nqueue_started_at=%s\nmusic_finished_at=%s\nmodel=DiffRhythm2\n' \
  "$COUNT" "$COUNT" "$QUEUE_STARTED_AT" "$MUSIC_FINISHED_AT" > "$STATUS"

INPUTS=(); for track in "${TRACKS[@]}"; do INPUTS+=("-i" "$track"); done
FILTER=""; CHAIN="[0:a]"
for ((i=1; i<COUNT; i++)); do
  next="mix$i"
  FILTER+="${CHAIN}[$i:a]acrossfade=d=${FADE_SECONDS}:c1=tri:c2=tri[$next];"
  CHAIN="[$next]"
done
FILTER+="${CHAIN}apad,atrim=duration=${TOTAL_SECONDS},loudnorm=I=-16:TP=-1.5:LRA=11[aout]"
MIX="$WORK_DIR/playlist-1h.wav"
ffmpeg -hide_banner -loglevel warning -y "${INPUTS[@]}" -filter_complex "$FILTER" -map '[aout]' -c:a pcm_s16le "$MIX" >> "$LOG" 2>&1

IMAGE="${IMAGES[$((RANDOM % ${#IMAGES[@]}))]}"
VIDEO="$OUTPUT_DIR/pepe-lofi-diffrhythm2-playlist.mp4"
printf 'state=rendering_video\ncompleted=%s\ntotal=%s\npercent=0\ncurrent=1\nmodel=DiffRhythm2\ntrack_count=%s\nvideo_started_at=%s\nqueue_started_at=%s\nmusic_finished_at=%s\nimage=%s\nfile=%s\n' \
  "$COUNT" "$COUNT" "$COUNT" "$(date +%s)" "$QUEUE_STARTED_AT" "$MUSIC_FINISHED_AT" "$IMAGE" "$VIDEO" > "$STATUS"
ffmpeg -hide_banner -loglevel warning -y -loop 1 -i "$IMAGE" -i "$MIX" -t "$TOTAL_SECONDS" \
  -map 0:v:0 -map 1:a:0 \
  -vf "scale=1280:720:force_original_aspect_ratio=increase:flags=lanczos,crop=1280:720,format=yuv420p" \
  -r 24 -c:v libx264 -preset medium -crf 28 -pix_fmt yuv420p \
  -af "afade=t=in:st=0:d=3,afade=t=out:st=$((TOTAL_SECONDS-3)):d=3" \
  -c:a aac -b:a 128k -ac 2 -movflags +faststart "$VIDEO" >> "$LOG" 2>&1

PLAYLIST="$MUSIC_DIR/playlist.m3u8"
{
  echo '#EXTM3U'
  for track in "${TRACKS[@]}"; do
    echo "#EXTINF:${TRACK_SECONDS},$(basename "$track" .mp3)"
    echo "$(basename "$track")"
  done
} > "$PLAYLIST"

QUEUE_FINISHED_AT="$(date +%s)"
printf 'state=complete\ncompleted=%s\ntotal=%s\npercent=100\nmodel=DiffRhythm2\ntrack_count=%s\nvideo_started_at=%s\nvideo_finished_at=%s\nqueue_started_at=%s\nqueue_finished_at=%s\nmusic_finished_at=%s\nimage=%s\nfile=%s\noutput=%s\nplaylist=%s\n' \
  "$COUNT" "$COUNT" "$COUNT" "$VIDEO_STARTED_AT" "$QUEUE_FINISHED_AT" "$QUEUE_STARTED_AT" "$QUEUE_FINISHED_AT" "$MUSIC_FINISHED_AT" "$IMAGE" "$VIDEO" "$OUTPUT_DIR" "$PLAYLIST" > "$STATUS"
echo "COMPLETE $VIDEO" >> "$LOG"
