#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ALBUM_COUNT="${ALBUM_COUNT:-10}"
TRACK_COUNT="${TRACK_COUNT:-15}"
TRACK_SECONDS="${TRACK_SECONDS:-234}"
TOTAL_SECONDS="${TOTAL_SECONDS:-3600}"
FADE_SECONDS="${FADE_SECONDS:-3}"
SEGMENT_SECONDS="${SEGMENT_SECONDS:-120}"
STEPS="${STABLE_AUDIO3_STEPS:-8}"
CFG="${STABLE_AUDIO3_CFG:-1.3}"
MUSIC_ROOT="$ROOT/assets/music/stable-audio3-albums-v4"
OUTPUT_ROOT="$ROOT/output/stable-audio3-albums-v4"
WORK_ROOT="$ROOT/tmp/stable-audio3-albums-v4"
STATUS="$ROOT/tmp/render-progress.txt"
LOG="$ROOT/tmp/stable-audio3-albums-v4.log"

[ "$TRACK_COUNT" -ge 10 ] && [ "$TRACK_COUNT" -le 15 ] || { echo "TRACK_COUNT must be between 10 and 15" >&2; exit 1; }
mkdir -p "$MUSIC_ROOT" "$OUTPUT_ROOT" "$WORK_ROOT" "$ROOT/tmp"
: > "$LOG"

on_error() {
  code=$?
  printf 'state=blocked\ncompleted=%s\ntotal=%s\nmodel=Stable Audio 3 Small-Music\nreason=stable_audio3_pipeline_failed\nerror=pipeline exited with code %s\n' \
    "${album_index:-0}" "$ALBUM_COUNT" "$code" > "$STATUS"
  exit "$code"
}
trap on_error ERR

IMAGE_DIR="$ROOT/assets/images"
IMAGES=()
while IFS= read -r image; do IMAGES+=("$image"); done < <(find "$IMAGE_DIR" -maxdepth 1 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webp' \) | sort)
[ "${#IMAGES[@]}" -gt 0 ] || { printf 'state=blocked\nreason=no-images\n' > "$STATUS"; exit 1; }

VARIANTS=(rainy-cafe midnight-library morning-window fireplace neon-street cloudy-day small-bookshop train-ride after-hours garden-rain vinyl-basement dawn)
ALBUM_NAMES=(study-focused cafe-warm nostalgic-chill rainy-cafe vintage-vinyl-night cosmic-dreams forest-retreat sunset-serenade winter-cozy night-drive)
TRACK_NAMES=(piano-focus guitar-answer rhodes-response descending-keys guitar-harmonics cassette-keys bass-led arpeggio-candlelight major-seventh resolution guitar-piano-dialogue swung-piano-hook floating-rhodes warm-bass-dialogue rainy-piano-ornament hopeful-resolution)
TRACK_DURATIONS=(210 214 218 222 226 230 234 212 216 220 224 228 232 211 217)
QUEUE_STARTED_AT="$(date +%s)"
printf 'state=starting\ncompleted=0\ntotal=%s\nalbums=%s\ntracks_per_album=%s\nimages=%s\ntrack_seconds=%s\nsegment_seconds=%s\ntotal_seconds=%s\nqueue_started_at=%s\nmodel=Stable Audio 3 Small-Music\nmode=two-segment-continuation\n' \
  "$ALBUM_COUNT" "$ALBUM_COUNT" "$TRACK_COUNT" "${#IMAGES[@]}" "$TRACK_SECONDS" "$SEGMENT_SECONDS" "$TOTAL_SECONDS" "$QUEUE_STARTED_AT" > "$STATUS"

for ((album_index=1; album_index<=ALBUM_COUNT; album_index++)); do
  album_name="${ALBUM_NAMES[$(((album_index-1) % ${#ALBUM_NAMES[@]}))]}"
  album_slug="album-$(printf '%02d' "$album_index")-$album_name"
  album_music="$MUSIC_ROOT/$album_slug"
  album_output="$OUTPUT_ROOT/$album_slug"
  album_work="$WORK_ROOT/$album_slug"
  mkdir -p "$album_music" "$album_output" "$album_work"
  image="${IMAGES[$(((album_index-1) % ${#IMAGES[@]}))]}"
  image_copy="$album_output/$(basename "$image")"
  [ -e "$image_copy" ] || cp "$image" "$image_copy"
  tracks=()

  for ((track_index=1; track_index<=TRACK_COUNT; track_index++)); do
    variant="$album_name"
    track_name="${TRACK_NAMES[$((track_index-1))]}"
    track_duration="${TRACK_DURATIONS[$((track_index-1))]}"
    track="$album_music/track-$(printf '%02d' "$track_index")-${track_name}.mp3"
    tracks+=("$track")
    if [ ! -s "$track" ]; then
      printf 'state=generating_music\ncompleted=%s\ntotal=%s\nalbum=%s\nalbum_index=%s\ntrack_count=%s\nmusic_track=%s\nmusic_percent=0\nvariant=%s\ntrack_duration=%s\nimage=%s\nqueue_started_at=%s\nmodel=Stable Audio 3 Small-Music\nmode=album-profile-track-specific-prompts\n' \
        "$((album_index-1))" "$ALBUM_COUNT" "$album_slug" "$album_index" "$TRACK_COUNT" "$track_index" "$variant" "$track_duration" "$image" "$QUEUE_STARTED_AT" > "$STATUS"
      echo "START album=$album_index/$ALBUM_COUNT track=$track_index/$TRACK_COUNT album_profile=$variant track_name=$track_name duration=$track_duration" >> "$LOG"
      "$ROOT/.venv-stable-audio3/bin/python" -u "$ROOT/scripts/generate_music_stable_audio3.py" \
        --duration "$track_duration" --segment-seconds "$SEGMENT_SECONDS" --steps "$STEPS" --cfg-scale "$CFG" \
        --album-style "$variant" --track-index "$track_index" --track-name "$track_name" --seed "$((710000 + album_index * 100 + track_index))" \
        --output "$track" >> "$LOG" 2>&1
      test -s "$track"
      echo "DONE album=$album_index/$ALBUM_COUNT track=$track_index/$TRACK_COUNT" >> "$LOG"
    fi
  done

  playlist="$album_music/playlist.m3u8"
  {
    echo '#EXTM3U'
    for ((playlist_index=1; playlist_index<=TRACK_COUNT; playlist_index++)); do
      echo "#EXTINF:${TRACK_DURATIONS[$((playlist_index-1))]},album-${album_index}-${TRACK_NAMES[$((playlist_index-1))]}"
      echo "$(basename "${tracks[$((playlist_index-1))]}")"
    done
  } > "$playlist"

  printf 'state=assembling_audio\ncompleted=%s\ntotal=%s\nalbum=%s\nalbum_index=%s\ntrack_count=%s\nmusic_percent=100\nqueue_started_at=%s\nmodel=Stable Audio 3 Small-Music\n' \
    "$((album_index-1))" "$ALBUM_COUNT" "$album_slug" "$album_index" "$TRACK_COUNT" "$QUEUE_STARTED_AT" > "$STATUS"
  inputs=(); for track in "${tracks[@]}"; do inputs+=("-i" "$track"); done
  filter=""; chain="[0:a]"
  for ((i=1; i<TRACK_COUNT; i++)); do
    next="mix$i"
    filter+="${chain}[$i:a]acrossfade=d=${FADE_SECONDS}:c1=tri:c2=tri[$next];"
    chain="[$next]"
  done
  filter+="${chain}apad,atrim=duration=${TOTAL_SECONDS},loudnorm=I=-16:TP=-1.5:LRA=11[aout]"
  mix="$album_work/$album_slug.wav"
  if ! ffprobe -v error -show_entries format=duration -of csv=p=0 "$mix" 2>/dev/null | awk -v target="$TOTAL_SECONDS" 'NF && $1 >= target-1 {ok=1} END {exit ok ? 0 : 1}'; then
    ffmpeg -hide_banner -loglevel warning -y "${inputs[@]}" -filter_complex "$filter" -map '[aout]' -c:a pcm_s16le "$mix" >> "$LOG" 2>&1
  else
    echo "REUSE valid album master=$mix" >> "$LOG"
  fi

  video="$album_output/$album_slug.mp4"
  if [ ! -s "$video" ]; then
    printf 'state=rendering_video\ncompleted=%s\ntotal=%s\nalbum=%s\nalbum_index=%s\ntrack_count=%s\npercent=0\nimage=%s\nfile=%s\nvideo_started_at=%s\nqueue_started_at=%s\nmodel=Stable Audio 3 Small-Music\n' \
      "$((album_index-1))" "$ALBUM_COUNT" "$album_slug" "$album_index" "$TRACK_COUNT" "$image" "$video" "$(date +%s)" "$QUEUE_STARTED_AT" > "$STATUS"
    # Preserve the source photo completely: fit inside the 16:9 canvas and
    # pad with black bars; never crop or stretch the source image.
    ffmpeg -hide_banner -loglevel warning -y -loop 1 -i "$image" -i "$mix" -t "$TOTAL_SECONDS" \
      -map 0:v:0 -map 1:a:0 \
      -vf "scale=1280:720:force_original_aspect_ratio=decrease:flags=lanczos,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p" \
      -r 24 -c:v libx264 -preset medium -crf 28 -pix_fmt yuv420p \
      -af "afade=t=in:st=0:d=3,afade=t=out:st=$((TOTAL_SECONDS-3)):d=3" \
      -c:a aac -b:a 128k -ac 2 -movflags +faststart "$video" >> "$LOG" 2>&1
  fi
  echo "COMPLETE album=$album_index/$ALBUM_COUNT video=$video" >> "$LOG"
done

QUEUE_FINISHED_AT="$(date +%s)"
printf 'state=complete\ncompleted=%s\ntotal=%s\nalbums=%s\ntracks_per_album=%s\npercent=100\nmodel=Stable Audio 3 Small-Music\nmode=two-segment-continuation\nqueue_started_at=%s\nqueue_finished_at=%s\noutput=%s\nmusic_root=%s\n' \
  "$ALBUM_COUNT" "$ALBUM_COUNT" "$ALBUM_COUNT" "$TRACK_COUNT" "$QUEUE_STARTED_AT" "$QUEUE_FINISHED_AT" "$OUTPUT_ROOT" "$MUSIC_ROOT" > "$STATUS"
echo "COMPLETE ALL $ALBUM_COUNT albums" >> "$LOG"
