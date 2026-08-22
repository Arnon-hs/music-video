#!/usr/bin/env bash
set -u

missing=0
for tool in python3 ffmpeg ffprobe curl jq; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf 'OK      %-8s %s\n' "$tool" "$(command -v "$tool")"
  else
    printf 'MISSING %-8s install it yourself, then run this check again.\n' "$tool"
    missing=1
  fi
done

if [ "$missing" -eq 1 ]; then
  echo 'No software was installed.'
  exit 1
fi

echo 'Required system dependencies are available. No software was installed.'
