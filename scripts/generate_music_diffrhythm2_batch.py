#!/usr/bin/env python3
"""Generate a varied DiffRhythm2 playlist in one model process."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from generate_music_diffrhythm2 import STYLE_PROMPT, VARIANT_SUFFIXES


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--duration", type=float, default=180.0)
    parser.add_argument("--steps", type=int, default=24)
    parser.add_argument("--cfg-strength", type=float, default=1.5)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    repo = root / ".models" / "DiffRhythm2"
    python = root / ".venv-diffrhythm2" / "bin" / "python"
    work = root / "tmp" / "diffrhythm2-playlist"
    work.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    variants = list(VARIANT_SUFFIXES)[: args.count]
    requests = []
    for index, variant in enumerate(variants, 1):
        lyrics = work / f"base_{index:02d}_{variant}.lrc"
        lyrics.write_text("[start]\n[intro]\n[inst]\n[verse]\n[inst]\n[outro]\n[end]\n", encoding="utf-8")
        requests.append(
            {
                "song_name": f"base_{index:02d}_{variant}",
                "style_prompt": f"{STYLE_PROMPT}, {VARIANT_SUFFIXES[variant]}",
                "lyrics": str(lyrics),
            }
        )
    request_file = work / "playlist.jsonl"
    request_file.write_text("\n".join(json.dumps(item) for item in requests) + "\n", encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo) + os.pathsep + str(Path(__file__).resolve().parent)
    env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    env["DIFFRHYTHM2_SEED"] = str(20260725)
    subprocess.run(
        [
            str(python), "inference.py", "--repo-id", "ASLP-lab/DiffRhythm2",
            "--output-dir", str(args.output_dir), "--input-jsonl", str(request_file),
            "--max-secs", str(min(args.duration, 210.0)), "--steps", str(args.steps),
            "--cfg-strength", str(args.cfg_strength),
        ], cwd=repo, env=env, check=True,
    )


if __name__ == "__main__":
    main()
