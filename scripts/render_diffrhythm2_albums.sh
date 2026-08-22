#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ALBUM_COUNT="${ALBUM_COUNT:-10}"
TRACK_COUNT="${TRACK_COUNT:-15}"
BASE_SECONDS="${BASE_SECONDS:-180}"
TRACK_SECONDS="${TRACK_SECONDS:-240}"
TOTAL_SECONDS="${TOTAL_SECONDS:-3600}"
FADE_SECONDS="${FADE_SECONDS:-3}"
STEPS="${DIFFRHYTHM2_STEPS:-24}"
CFG="${DIFFRHYTHM2_CFG:-1.5}"
MUSIC_ROOT="$ROOT/assets/music/diffrhythm2-albums-v2"
OUTPUT_ROOT="$ROOT/output/diffrhythm2-albums-v2"
WORK_ROOT="$ROOT/tmp/diffrhythm2-albums-v2"
STATUS="$ROOT/tmp/render-progress.txt"
LOG="$ROOT/tmp/diffrhythm2-albums.log"

[ "$ALBUM_COUNT" -ge 1 ] || { echo "ALBUM_COUNT must be positive" >&2; exit 1; }
[ "$TRACK_COUNT" -ge 1 ] && [ "$TRACK_COUNT" -le 15 ] || { echo "TRACK_COUNT must be between 1 and 15" >&2; exit 1; }

mkdir -p "$MUSIC_ROOT" "$OUTPUT_ROOT" "$WORK_ROOT" "$ROOT/tmp"
: > "$LOG"

on_error() {
  code=$?
  printf 'state=blocked\ncompleted=%s\ntotal=%s\nmodel=DiffRhythm2\nreason=album_pipeline_failed\nerror=multi-album pipeline exited with code %s\n' \
    "${album_index:-0}" "$ALBUM_COUNT" "$code" > "$STATUS"
  exit "$code"
}
trap on_error ERR

IMAGE_DIR="$ROOT/assets/images"
IMAGES=()
while IFS= read -r image; do IMAGES+=("$image"); done < <(find "$IMAGE_DIR" -maxdepth 1 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webp' \) | sort)
[ "${#IMAGES[@]}" -gt 0 ] || { printf 'state=blocked\nreason=no-images\n' > "$STATUS"; exit 1; }

VARIANTS=(rainy-cafe midnight-library morning-window fireplace neon-street cloudy-day small-bookshop train-ride after-hours garden-rain vinyl-basement dawn)
ALBUM_NAMES=(rainy-cafe midnight-library morning-window fireplace neon-street cloudy-day small-bookshop train-ride after-hours garden-rain)
QUEUE_STARTED_AT="$(date +%s)"

printf 'state=starting\ncompleted=0\ntotal=%s\nalbums=%s\ntracks_per_album=%s\nimages=%s\ntrack_seconds=%s\nbase_seconds=%s\ntotal_seconds=%s\nqueue_started_at=%s\nmodel=DiffRhythm2\nmode=sequential-albums\n' \
  "$ALBUM_COUNT" "$ALBUM_COUNT" "$TRACK_COUNT" "${#IMAGES[@]}" "$TRACK_SECONDS" "$BASE_SECONDS" "$TOTAL_SECONDS" "$QUEUE_STARTED_AT" > "$STATUS"

for ((album_index=1; album_index<=ALBUM_COUNT; album_index++)); do
  album_slug="album-$(printf '%02d' "$album_index")-${ALBUM_NAMES[$(((album_index-1) % ${#ALBUM_NAMES[@]}))]}"
  album_music="$MUSIC_ROOT/$album_slug"
  album_output="$OUTPUT_ROOT/$album_slug"
  album_work="$WORK_ROOT/$album_slug"
  mkdir -p "$album_music" "$album_output" "$album_work"
  image="${IMAGES[$(((album_index-1) % ${#IMAGES[@]}))]}"
  image_copy="$album_output/$(basename "$image")"
  [ -e "$image_copy" ] || cp "$image" "$image_copy"

  printf 'state=generating_music\ncompleted=%s\ntotal=%s\nalbum=%s\nalbum_index=%s\ntrack_count=%s\nmusic_track=1\nmusic_percent=0\nvariant=%s\nimage=%s\nqueue_started_at=%s\nmodel=DiffRhythm2\nmode=sequential\n' \
    "$((album_index-1))" "$ALBUM_COUNT" "$album_slug" "$album_index" "$TRACK_COUNT" \
    "${VARIANTS[$(((album_index-1) % ${#VARIANTS[@]}))]}" "$image" "$QUEUE_STARTED_AT" > "$STATUS"
  echo "ALBUM $album_index/$ALBUM_COUNT: $album_slug" >> "$LOG"

  TRACKS=()
  for ((track_index=1; track_index<=TRACK_COUNT; track_index++)); do
    variant_index=$(( ((album_index - 1) * 3 + track_index - 1) % ${#VARIANTS[@]} ))
    variant="${VARIANTS[$variant_index]}"
    base="$album_work/base-$(printf '%02d' "$track_index")-${variant}.mp3"
    final="$album_music/track-$(printf '%02d' "$track_index")-${variant}.mp3"
    TRACKS+=("$final")
    if [ ! -s "$base" ]; then
      printf 'state=generating_music\ncompleted=%s\ntotal=%s\nalbum=%s\nalbum_index=%s\ntrack_count=%s\nmusic_track=%s\nmusic_percent=0\nvariant=%s\nimage=%s\nqueue_started_at=%s\nmodel=DiffRhythm2\nmode=sequential\n' \
        "$((album_index-1))" "$ALBUM_COUNT" "$album_slug" "$album_index" "$TRACK_COUNT" "$track_index" "$variant" "$image" "$QUEUE_STARTED_AT" > "$STATUS"
      echo "START track $album_index/$ALBUM_COUNT $track_index/$TRACK_COUNT: $variant" >> "$LOG"
      "$ROOT/.venv-diffrhythm2/bin/python" "$ROOT/scripts/generate_music_diffrhythm2.py" \
        --duration "$BASE_SECONDS" --steps "$STEPS" --cfg-strength "$CFG" \
        --variant "$variant" --song-name "${album_slug}_base_$(printf '%02d' "$track_index")" \
        --track-index "$track_index" \
        --seed "$((424200 + album_index * 100 + track_index))" --output "$base" >> "$LOG" 2>&1
      test -s "$base"
      echo "DONE track $album_index/$ALBUM_COUNT $track_index/$TRACK_COUNT" >> "$LOG"
    fi
    if [ ! -s "$final" ]; then
      printf 'state=assembling_track\ncompleted=%s\ntotal=%s\nalbum=%s\nalbum_index=%s\ntrack_count=%s\nmusic_track=%s\nvariant=%s\nqueue_started_at=%s\nmodel=DiffRhythm2\n' \
        "$((album_index-1))" "$ALBUM_COUNT" "$album_slug" "$album_index" "$TRACK_COUNT" "$track_index" "$variant" "$QUEUE_STARTED_AT" > "$STATUS"
      ffmpeg -hide_banner -loglevel warning -y -i "$base" -i "$base" \
        -filter_complex "[0:a][1:a]acrossfade=d=8:c1=tri:c2=tri,atrim=duration=${TRACK_SECONDS},afade=t=in:st=0:d=2,afade=t=out:st=$((TRACK_SECONDS-2)):d=2[a]" \
        -map '[a]' -c:a libmp3lame -q:a 2 "$final" >> "$LOG" 2>&1
    fi
  done

  PLAYLIST="$album_music/playlist.m3u8"
  {
    echo '#EXTM3U'
    for track in "${TRACKS[@]}"; do
      echo "#EXTINF:${TRACK_SECONDS},$(basename "$track" .mp3)"
      echo "$(basename "$track")"
    done
  } > "$PLAYLIST"

  printf 'state=assembling_audio\ncompleted=%s\ntotal=%s\nalbum=%s\nalbum_index=%s\ntrack_count=%s\nmusic_percent=100\nqueue_started_at=%s\nmodel=DiffRhythm2\n' \
    "$((album_index-1))" "$ALBUM_COUNT" "$album_slug" "$album_index" "$TRACK_COUNT" "$QUEUE_STARTED_AT" > "$STATUS"
  INPUTS=(); for track in "${TRACKS[@]}"; do INPUTS+=("-i" "$track"); done
  FILTER=""; CHAIN="[0:a]"
  for ((i=1; i<TRACK_COUNT; i++)); do
    next="mix$i"
    FILTER+="${CHAIN}[$i:a]acrossfade=d=${FADE_SECONDS}:c1=tri:c2=tri[$next];"
    CHAIN="[$next]"
  done
  FILTER+="${CHAIN}apad,atrim=duration=${TOTAL_SECONDS},loudnorm=I=-16:TP=-1.5:LRA=11[aout]"
  mix="$album_work/$album_slug.wav"
  ffmpeg -hide_banner -loglevel warning -y "${INPUTS[@]}" -filter_complex "$FILTER" -map '[aout]' -c:a pcm_s16le "$mix" >> "$LOG" 2>&1

  VIDEO="$album_output/$album_slug.mp4"
  if [ ! -s "$VIDEO" ]; then
    printf 'state=rendering_video\ncompleted=%s\ntotal=%s\nalbum=%s\nalbum_index=%s\ntrack_count=%s\npercent=0\nimage=%s\nfile=%s\nvideo_started_at=%s\nqueue_started_at=%s\nmodel=DiffRhythm2\n' \
      "$((album_index-1))" "$ALBUM_COUNT" "$album_slug" "$album_index" "$TRACK_COUNT" "$image" "$VIDEO" "$(date +%s)" "$QUEUE_STARTED_AT" > "$STATUS"
    ffmpeg -hide_banner -loglevel warning -y -loop 1 -i "$image" -i "$mix" -t "$TOTAL_SECONDS" \
      -map 0:v:0 -map 1:a:0 \
      -vf "scale=1280:720:force_original_aspect_ratio=increase:flags=lanczos,crop=1280:720,format=yuv420p" \
      -r 24 -c:v libx264 -preset medium -crf 28 -pix_fmt yuv420p \
      -af "afade=t=in:st=0:d=3,afade=t=out:st=$((TOTAL_SECONDS-3)):d=3" \
      -c:a aac -b:a 128k -ac 2 -movflags +faststart "$VIDEO" >> "$LOG" 2>&1
  fi
  echo "COMPLETE ALBUM $album_index/$ALBUM_COUNT: $VIDEO" >> "$LOG"
done

QUEUE_FINISHED_AT="$(date +%s)"
printf 'state=complete\ncompleted=%s\ntotal=%s\nalbums=%s\ntracks_per_album=%s\npercent=100\nmodel=DiffRhythm2\nmode=sequential-albums\nqueue_started_at=%s\nqueue_finished_at=%s\noutput=%s\nmusic_root=%s\n' \
  "$ALBUM_COUNT" "$ALBUM_COUNT" "$ALBUM_COUNT" "$TRACK_COUNT" "$QUEUE_STARTED_AT" "$QUEUE_FINISHED_AT" "$OUTPUT_ROOT" "$MUSIC_ROOT" > "$STATUS"
echo "COMPLETE ALL $ALBUM_COUNT albums" >> "$LOG"
