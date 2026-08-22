#!/usr/bin/env python3
"""Project adapter for the official DiffRhythm 2 inference script."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


STYLE_PROMPT = (
    "purely instrumental lo-fi hip hop for focused listening, absolutely no human voice, "
    "no singing, no spoken words, no rap, no choir, no vocal chops, no chants, no lyrics, "
    "cozy rainy late night or gentle morning mood, mid-tempo 80-90 BPM, "
    "mellow piano, acoustic guitar, soft brushed jazz drums, warm rounded bass, "
    "subtle vinyl crackle, quiet rain or cafe room tone, intimate analog texture, "
    "pleasant consonant harmony, jazzy seventh and ninth chords, smooth melodic phrasing, "
    "gentle tension and release, memorable but understated instrumental motif, "
    "balanced 8 and 16 bar phrases, golden-ratio-like balance of repetition and variation, "
    "minimal dynamics, no drop, no build-up, no sudden changes, no harsh sounds, study music"
)

VARIANT_SUFFIXES = {
    "rainy-cafe": "soft rainy cafe, brushed jazz drums, mellow rhodes, intimate and warm",
    "midnight-library": "late-night library, dusty piano, restrained boom bap drums, deep focus",
    "morning-window": "quiet morning window, gentle acoustic guitar, soft electric piano, hopeful calm",
    "fireplace": "cozy fireplace, muted guitar, round bass, brushed drums, warm tape character",
    "neon-street": "wet neon street at night, jazzy chords, soft breakbeat, subdued city glow",
    "cloudy-day": "overcast afternoon, muted keys, lazy swing, hazy analog texture, peaceful",
    "small-bookshop": "small bookshop, intimate piano, soft percussion, woody acoustic texture",
    "train-ride": "slow rainy train ride, wistful rhodes, gentle guitar, steady understated groove",
    "after-hours": "after-hours study room, minor seventh chords, soft drums, low-key nocturnal mood",
    "garden-rain": "rain in a quiet garden, delicate piano, brushed drums, organic and soothing",
    "vinyl-basement": "underground vinyl basement, dusty sampled drums, mellow keys, understated head-nod",
    "dawn": "blue-hour dawn, warm piano, soft guitar harmonics, spacious hopeful lo-fi atmosphere",
}

MELODIC_IDENTITIES = {
    "1": "a memorable four-note mellow piano motif, sparse and intimate",
    "2": "a gentle acoustic guitar melody answered by soft rhodes chords",
    "3": "a warm rhodes lead with a relaxed syncopated piano response",
    "4": "a simple jazzy piano ostinato with subtle harmonic color",
    "5": "a lyrical guitar phrase with understated brushed-drum pocket",
    "6": "a dusty cassette-like keyboard motif, calm and softly nostalgic",
    "7": "a mellow bass-led groove with small piano flourishes",
    "8": "a spacious electric-piano melody with a peaceful call and response",
    "9": "a gentle descending piano motif resolving into warm major-seventh harmony",
    "10": "a cozy guitar arpeggio with soft jazz piano fills",
    "11": "a restrained boom-bap piano hook with subtle swing and no aggression",
    "12": "a floating rhodes melody with delicate high-register piano accents",
    "13": "a fireplace-warm guitar motif and rounded bass conversation",
    "14": "a rainy-window piano melody with sparse ornamental notes",
    "15": "a hopeful dawn motif, soft guitar harmonics and tender piano resolution",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=180.0)
    parser.add_argument("--steps", type=int, default=24)
    parser.add_argument("--cfg-strength", type=float, default=1.5)
    parser.add_argument("--variant", default="rainy-cafe")
    parser.add_argument("--song-name", default="lofi_instrumental")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--track-index", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    repo = root / ".models" / "DiffRhythm2"
    python = root / ".venv-diffrhythm2" / "bin" / "python"
    if not python.exists():
        raise SystemExit(f"Missing {python}; create the DiffRhythm2 environment first")
    if not (repo / "inference.py").exists():
        raise SystemExit(f"Missing DiffRhythm2 checkout: {repo}")

    work = root / "tmp" / "diffrhythm2"
    result_dir = work / "results"
    work.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for old in result_dir.glob(f"{args.song_name}.*"):
        old.unlink()

    lyrics = work / "lofi_instrumental.lrc"
    lyrics.write_text(
        "[start]\n[inst]\n[inst]\n[inst]\n[inst]\n[outro]\n[end]\n",
        encoding="utf-8",
    )
    request = work / "request.jsonl"
    request.write_text(
        json.dumps(
            {
                "song_name": args.song_name,
                "style_prompt": (
                    f"{STYLE_PROMPT}, {VARIANT_SUFFIXES.get(args.variant, args.variant)}, "
                    f"track identity: {MELODIC_IDENTITIES.get(str(args.track_index), 'distinct original instrumental melody')}"
                ),
                "lyrics": str(lyrics),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    if args.seed is not None:
        env["DIFFRHYTHM2_SEED"] = str(args.seed)
    subprocess.run(
        [
            str(python),
            "inference.py",
            "--repo-id",
            "ASLP-lab/DiffRhythm2",
            "--output-dir",
            str(result_dir),
            "--input-jsonl",
            str(request),
            "--max-secs",
            str(min(args.duration, 210.0)),
            "--steps",
            str(args.steps),
            "--cfg-strength",
            str(args.cfg_strength),
        ],
        cwd=repo,
        env=env,
        check=True,
    )
    candidates = sorted(result_dir.glob(f"{args.song_name}.*"))
    if not candidates:
        raise SystemExit(f"DiffRhythm2 produced no file in {result_dir}")
    args.output.write_bytes(candidates[0].read_bytes())
    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
