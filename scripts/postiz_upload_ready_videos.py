#!/usr/bin/env python3
"""Upload completed music videos to Postiz as private YouTube drafts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
_video_root = Path(os.environ.get("POSTIZ_VIDEO_ROOT", "output")).expanduser()
VIDEO_ROOT = (_video_root if _video_root.is_absolute() else ROOT / _video_root).resolve()
STATE_PATH = ROOT / "tmp" / "postiz-uploaded.json"
LOG_PATH = ROOT / "tmp" / "postiz-upload.log"
API_ROOT = os.environ.get("POSTIZ_API_ROOT", "https://api.postiz.com/public/v1").rstrip("/")


def log(message: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {message}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")


def load_state() -> dict[str, dict]:
    if not STATE_PATH.exists():
        return {}
    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Invalid Postiz state file: {STATE_PATH}") from error
    if not isinstance(state, dict):
        raise RuntimeError(f"Postiz state must be a JSON object: {STATE_PATH}")
    return state


def save_state(state: dict[str, dict]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(STATE_PATH)


def validate_api_root(api_root: str, allow_insecure_http: bool = False) -> None:
    parsed = urlparse(api_root)
    if parsed.scheme == "https" and parsed.netloc:
        return
    loopback = parsed.hostname in {"127.0.0.1", "::1", "localhost"}
    if parsed.scheme == "http" and parsed.netloc and (loopback or allow_insecure_http):
        return
    raise ValueError(
        "POSTIZ_API_ROOT must use HTTPS. HTTP is allowed only for loopback, or with "
        "POSTIZ_ALLOW_INSECURE_HTTP=1 after a network-risk review."
    )


def validate_credential(name: str, value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be empty")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"{name} must not contain control characters")
    return value


def video_candidates(state: dict[str, dict]) -> list[tuple[str, Path]]:
    if not VIDEO_ROOT.exists():
        return []
    root = VIDEO_ROOT.resolve()
    candidates: list[tuple[str, Path]] = []
    for candidate in sorted(VIDEO_ROOT.rglob("*.mp4")):
        if candidate.is_symlink():
            continue
        resolved = candidate.resolve()
        try:
            key = resolved.relative_to(root).as_posix()
        except ValueError:
            continue
        if any(ord(character) < 32 or ord(character) == 127 for character in key):
            continue
        if resolved.is_file() and key not in state:
            candidates.append((key, resolved))
    return candidates


def upload_video(api_key: str, video: Path) -> dict:
    api_key = validate_credential("POSTIZ_API_KEY", api_key)
    result = subprocess.run(
        [
            "curl", "-fsS", "--max-time", "180", "-X", "POST", f"{API_ROOT}/upload",
            "-H", "@-", "-F", f"file=@{video}",
        ],
        check=True,
        capture_output=True,
        text=True,
        input=f"Authorization: {api_key}\n",
    )
    response = json.loads(result.stdout)
    if not isinstance(response, dict) or not response.get("id") or not response.get("path"):
        raise RuntimeError("Postiz upload response did not contain media id and path")
    return response


def create_draft(api_key: str, integration_id: str, media: dict, video: Path, source_label: str, preview_url: str) -> dict:
    api_key = validate_credential("POSTIZ_API_KEY", api_key)
    integration_id = validate_credential("POSTIZ_INTEGRATION_ID", integration_id)
    title = video.stem.replace("-", " ").replace("album ", "Album ").title()
    description_lines = [
        "AI-generated instrumental music video.",
        "",
    ]
    if preview_url:
        description_lines.append(f"Local preview URL: {preview_url}")
    description_lines.extend(
        [
            f"Source file: {source_label}",
            "Visibility: private YouTube draft; review before publishing.",
        ]
    )
    description = "\n".join(description_lines)
    payload = {
        "type": "draft",
        "shortLink": False,
        "tags": [],
        "posts": [
            {
                "integration": {"id": integration_id},
                "value": [{"content": description, "image": [{"id": media["id"], "path": media["path"]}]}],
                "settings": {
                    "__type": "youtube",
                    "title": title[:100],
                    "type": "private",
                    "selfDeclaredMadeForKids": "no",
                    "tags": [
                        {"value": "instrumental", "label": "instrumental"},
                        {"value": "ai music", "label": "AI music"},
                        {"value": "music video", "label": "music video"},
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


def draft_item(response: object) -> dict:
    if isinstance(response, list):
        item = response[0] if response else None
    else:
        item = response
    if not isinstance(item, dict):
        raise RuntimeError("Postiz draft response was not an object")
    if not (item.get("postId") or item.get("id")):
        raise RuntimeError("Postiz draft response did not contain a post ID")
    return item


def process_once(api_key: str, integration_id: str, base_url: str) -> int:
    state = load_state()
    videos = video_candidates(state)
    for key, video in videos:
        preview_url = f"{base_url.rstrip('/')}/media/video/{key}" if base_url else ""
        log(f"uploading {key}")
        media = upload_video(api_key, video)
        response = create_draft(api_key, integration_id, media, video, key, preview_url)
        item = draft_item(response)
        state[key] = {
            "post_id": item.get("postId") or item.get("id"),
            "integration": integration_id,
            "media_url": media.get("path"),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        if preview_url:
            state[key]["preview_url"] = preview_url
        save_state(state)
        log(f"draft created for {key}: post_id={state[key]['post_id']}")
    return len(videos)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true", help="list pending videos without contacting Postiz")
    args = parser.parse_args()
    if args.interval < 5:
        raise SystemExit("--interval must be at least 5 seconds")
    if args.dry_run:
        for key, _ in video_candidates(load_state()):
            print(key)
        return
    api_key = os.environ.get("POSTIZ_API_KEY")
    if not api_key:
        raise SystemExit("POSTIZ_API_KEY is required in the environment")
    integration_id = os.environ.get("POSTIZ_INTEGRATION_ID")
    if not integration_id:
        raise SystemExit("POSTIZ_INTEGRATION_ID is required in the environment")
    try:
        api_key = validate_credential("POSTIZ_API_KEY", api_key)
        integration_id = validate_credential("POSTIZ_INTEGRATION_ID", integration_id)
        validate_api_root(API_ROOT, os.environ.get("POSTIZ_ALLOW_INSECURE_HTTP") == "1")
    except ValueError as error:
        raise SystemExit(str(error)) from error
    base_url = os.environ.get("POSTIZ_LOCAL_BASE_URL", "").strip()
    while True:
        process_once(api_key, integration_id, base_url)
        if not args.watch:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
