#!/usr/bin/env python3
"""Download a reviewed, small Pexels image set without persisting the API key."""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing PyYAML. Activate .venv and install the documented dependencies.", file=sys.stderr)
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config.yaml"
IMAGES = ROOT / "assets" / "images"
CREDITS = ROOT / "metadata" / "image-credits.json"
UNSAFE_TERMS = {
    "logo", "brand", "celebrity", "actor", "singer", "character", "mascot",
    "anime", "movie", "game", "gun", "firearm", "weapon",
}


def load_config() -> dict:
    with CONFIG.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def api_request(url: str, key: str) -> dict:
    request = urllib.request.Request(url, headers={"Authorization": key, "User-Agent": "agent-pepe-lofi/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def acceptable(photo: dict) -> bool:
    searchable = " ".join(str(photo.get(k, "")) for k in ("alt", "url", "photographer")).lower()
    return not any(term in searchable for term in UNSAFE_TERMS)


def main() -> int:
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    if not key:
        print("PEXELS_API_KEY is not set. Create a free API key at https://www.pexels.com/api/ and export it:")
        print("export PEXELS_API_KEY='your_key_here'")
        print("No request was made and this is not an error.")
        return 0

    config = load_config()
    selected: list[dict] = []
    seen: set[int] = set()
    for query in config["image_queries"]:
        endpoint = "https://api.pexels.com/v1/search?query=" + urllib.parse.quote(query) + "&per_page=4&orientation=landscape"
        try:
            result = api_request(endpoint, key)
        except Exception as exc:
            print(f"Pexels search failed for {query!r}: {exc}", file=sys.stderr)
            return 1
        for photo in result.get("photos", []):
            if photo.get("id") not in seen and acceptable(photo):
                selected.append({"query": query, **photo})
                seen.add(photo["id"])
            if len(selected) == 12:
                break
        if len(selected) == 12:
            break

    selected = selected[:12]
    if len(selected) < 8:
        print(f"Only {len(selected)} suitable images were returned; no files were downloaded.", file=sys.stderr)
        return 1

    print("Selected images. Review them before downloading:")
    for index, photo in enumerate(selected, start=1):
        print(f"{index:02d}. {photo['photographer']} | {photo.get('alt') or 'no description'} | {photo['url']}")
    answer = input("Type DOWNLOAD to save these 8–12 images, or press Enter to cancel: ").strip()
    if answer != "DOWNLOAD":
        print("Cancelled. No images were downloaded.")
        return 0

    IMAGES.mkdir(parents=True, exist_ok=True)
    credits = []
    for index, photo in enumerate(selected, start=1):
        source_url = photo["src"].get("large2x") or photo["src"]["large"]
        extension = ".jpg"
        destination = IMAGES / f"pexels-{photo['id']:d}{extension}"
        print(f"Downloading {index}/{len(selected)}: {destination.name}")
        request = urllib.request.Request(source_url, headers={"User-Agent": "agent-pepe-lofi/1.0"})
        with urllib.request.urlopen(request, timeout=90) as response, destination.open("wb") as handle:
            handle.write(response.read())
        credits.append({"file": str(destination.relative_to(ROOT)), "query": photo["query"], "author": photo["photographer"], "pexels_page": photo["url"], "source_url": source_url, "license_note": "Pexels content; verify suitability before any public use."})
    CREDITS.parent.mkdir(parents=True, exist_ok=True)
    CREDITS.write_text(json.dumps(credits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(credits)} images and {CREDITS.relative_to(ROOT)}. API key was not written to disk.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
