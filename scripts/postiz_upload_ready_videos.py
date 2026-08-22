#!/usr/bin/env python3
"""Upload completed v4 videos to Postiz as private YouTube drafts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
VIDEO_ROOT = ROOT / "output" / "stable-audio3-albums-v4"
STATE_PATH = ROOT / "tmp" / "postiz-uploaded-v4.json"
LOG_PATH = ROOT / "tmp" / "postiz-upload.log"
API_ROOT = "https://api.postiz.com/public/v1"
INTEGRATION_ID = "cmrak761d0f54k90ywfawy5ql"


def log(message: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {message}"
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")


def load_state() -> dict[str, dict]:
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict[str, dict]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def upload_video(api_key: str, video: Path) -> dict:
    result = subprocess.run(
        [
            "curl", "-fsS", "--max-time", "180", "-X", "POST", f"{API_ROOT}/upload",
            "-H", f"Authorization: {api_key}", "-F", f"file=@{video}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def create_draft(api_key: str, media: dict, video: Path, preview_url: str) -> dict:
    title = video.stem.replace("-", " ").replace("album ", "Album ").title()
    description = (
        "AI-generated lo-fi instrumental album video.\n\n"
        f"Local preview URL: {preview_url}\n"
        f"Source file: {video}\n"
        "Visibility: private YouTube draft; review before publishing."
    )
    payload = {
        "type": "draft",
        "shortLink": False,
        "tags": [],
        "posts": [
            {
                "integration": {"id": INTEGRATION_ID},
                "value": [{"content": description, "image": [{"id": media["id"], "path": media["path"]}]}],
                "settings": {
                    "__type": "youtube",
                    "title": title[:100],
                    "type": "private",
                    "selfDeclaredMadeForKids": "no",
                    "tags": [
                        {"value": "lofi", "label": "lo-fi"},
                        {"value": "study music", "label": "study music"},
                        {"value": "instrumental", "label": "instrumental"},
                    ],
                },
            }
        ],
    }
    request = Request(
        f"{API_ROOT}/posts",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def process_once(api_key: str, base_url: str) -> int:
    state = load_state()
    videos = sorted(VIDEO_ROOT.rglob("*.mp4")) if VIDEO_ROOT.exists() else []
    for video in videos:
        key = video.relative_to(VIDEO_ROOT).as_posix()
        if key in state:
            continue
        preview_url = f"{base_url.rstrip('/')}/media/video/{key}"
        log(f"uploading {key}")
        media = upload_video(api_key, video)
        response = create_draft(api_key, media, video, preview_url)
        item = response[0] if isinstance(response, list) else response
        state[key] = {
            "post_id": item.get("postId") or item.get("id"),
            "integration": INTEGRATION_ID,
            "media_url": media.get("path"),
            "preview_url": preview_url,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        save_state(state)
        log(f"draft created for {key}: post_id={state[key]['post_id']}")
    return len(videos)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=int, default=30)
    args = parser.parse_args()
    api_key = os.environ.get("POSTIZ_API_KEY")
    if not api_key:
        raise SystemExit("POSTIZ_API_KEY is required in the environment")
    base_url = os.environ.get("POSTIZ_LOCAL_BASE_URL", "http://192.168.1.105:8765")
    while True:
        process_once(api_key, base_url)
        if not args.watch:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
