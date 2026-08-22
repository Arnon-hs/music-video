#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_DIR="${IMAGE_DIR_OVERRIDE:-$ROOT/assets/images}"
OUT="${VISUAL_OUT:-$ROOT/assets/visual-loop.mp4}"
PROFILE="${VISUAL_PROFILE:-calm}"
FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1
if [ -e "$OUT" ] && [ "$FORCE" -ne 1 ]; then echo "Refusing to overwrite $OUT. Re-run with --force."; exit 1; fi
IMAGES=()
while IFS= read -r image; do
  IMAGES+=("$image")
done < <(find "$IMAGE_DIR" -maxdepth 1 -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) | sort)
if [ "${#IMAGES[@]}" -lt 1 ]; then echo "No images found in $IMAGE_DIR. Run search_pexels_images.py first."; exit 1; fi

mkdir -p "$ROOT/assets"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/agent-pepe-lofi.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
COUNT="${#IMAGES[@]}"
DURATION="$(awk "BEGIN {print 30 / $COUNT}")"
for i in "${!IMAGES[@]}"; do
  if [ "$PROFILE" = "energetic" ]; then
    FILTER="scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.00022,1.12)':x='iw/2-(iw/zoom/2)+sin(on/18)*90':y='ih/2-(ih/zoom/2)+cos(on/25)*40':d=1:s=1920x1080:fps=24,eq=contrast=1.18:saturation=1.55:brightness=0.01,hue=h=12*sin(n/16):s=1.25,colorbalance=rm=0.15:bm=0.20,noise=alls=14:allf=t+u"
  else
    FILTER="scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.00010,1.06)':x='iw/2-(iw/zoom/2)+sin(on/80)*40':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=24,eq=contrast=1.08:saturation=1.25:brightness=-0.04,colorbalance=rm=0.08:bm=0.11:bs=0.06,noise=alls=8:allf=t+u"
  fi
  ffmpeg -hide_banner -loglevel error -y -loop 1 -i "${IMAGES[$i]}" -t "$DURATION" -vf "$FILTER" -an -c:v libx264 -pix_fmt yuv420p "$TMP/clip-$i.mp4"
  printf "file '%s'\n" "$TMP/clip-$i.mp4" >> "$TMP/list.txt"
done
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$TMP/list.txt" -c copy "$TMP/base.mp4"
# Procedural rain/VHS layer: generated solely by ffmpeg, with no external asset.
ffmpeg -hide_banner -y -i "$TMP/base.mp4" -f lavfi -i "nullsrc=s=1920x1080:r=24:d=30,geq=r='if(gt(random(1),0.997),180,0)':g='if(gt(random(1),0.997),120,0)':b='if(gt(random(1),0.997),255,0)',boxblur=1:1,format=rgba,colorchannelmixer=aa=0.32" -filter_complex "[0:v]fps=24,format=rgba[v];[1:v]format=rgba[rain];[v][rain]overlay=0:0:shortest=1,noise=alls=5:allf=t+u,eq=contrast=1.05:saturation=1.12" -t 30 -an -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart "$OUT"
echo "Created $OUT (30-second original visual loop; no text added)."
