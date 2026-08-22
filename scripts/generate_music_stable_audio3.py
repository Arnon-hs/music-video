#!/usr/bin/env python3
"""Stable Audio 3 Small-Music adapter for instrumental tracks."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import subprocess
import tempfile
import time
import warnings
from pathlib import Path

import torch
import torchaudio

# Stable Audio 3 optionally imports FlashAttention. It is CUDA-specific and is
# unavailable on Apple Silicon, so the model already has a native PyTorch
# fallback. Keep the expected fallback diagnostic out of the operator log.
warnings.filterwarnings(
    "ignore",
    message=r".*torch\.nn\.utils\.weight_norm.*deprecated.*",
    category=FutureWarning,
)
_stable_audio_import_output = io.StringIO()
with contextlib.redirect_stdout(_stable_audio_import_output), contextlib.redirect_stderr(_stable_audio_import_output):
    from stable_audio_3 import StableAudioModel


INSTRUMENTAL_GUARD = (
    "purely instrumental original composition, no human voice, no vocals, no singing, "
    "no spoken words, no rap, no choir, no chants, no vocal chops, no lyrics, "
    "no artist imitation, no recognisable copyrighted melody"
)

BASE_PROMPT = (
    "clean lo-fi hip hop, "
    "cozy rainy late-night coffee shop mood, pleasant uplifting calm feeling, "
    "80-90 BPM, mellow piano, acoustic guitar, soft brushed jazz drums, warm rounded bass, "
    "subtle vinyl crackle, very quiet rain ambience, smooth consonant jazz harmony, "
    "gentle 8 and 16 bar phrases, memorable understated melody, balanced repetition and variation, "
    "golden-ratio-like proportion of motif and variation, no drop, no build-up, no sudden dynamics, "
    "no distortion, no clipping, no harsh noise, no horror atmosphere, suitable for studying, "
    "original melody for this track, do not copy any other track"
)

NEGATIVE_PROMPT = (
    "vocals, singing, human voice, speech, spoken word, rap, lyrics, choir, chant, "
    "vocal sample, vocal chop, crowd, shouting, screaming, horror, scary, ominous, "
    "harsh noise, white noise, static, hiss, distortion, clipping, glitch, siren, "
    "copied hook, repeated melody from another track"
)

ALBUM_PROFILES = {
    "rainy-cafe": "soft rainy cafe as the constant album identity, intimate room tone, mellow piano, acoustic guitar, brushed jazz drums, warm coffee-shop ambience",
    "midnight-library": "quiet midnight library as the constant album identity, dusty piano, low warm room tone, restrained brushed swing",
    "morning-window": "gentle morning window as the constant album identity, acoustic guitar, soft electric piano, warm natural room tone",
    "fireplace": "cozy fireplace as the constant album identity, muted guitar, round bass, brushed drums, warm tape character",
    "neon-street": "wet neon street at night as the constant album identity, jazzy chords, soft understated breakbeat, peaceful city glow",
    "cloudy-day": "overcast afternoon as the constant album identity, muted keys, lazy swing, hazy analog texture",
    "small-bookshop": "small bookshop as the constant album identity, intimate piano, soft percussion, woody acoustic texture",
    "train-ride": "slow rainy train ride as the constant album identity, wistful rhodes, gentle guitar, steady understated groove",
    "after-hours": "after-hours study room as the constant album identity, minor seventh chords, soft drums, low-key nocturnal mood",
    "garden-rain": "rain in a quiet garden as the constant album identity, delicate piano, brushed drums, organic soothing atmosphere",
    "vinyl-basement": "underground vinyl basement as the constant album identity, dusty drums, mellow keys, understated head-nod",
    "dawn": "blue-hour dawn as the constant album identity, warm piano, soft guitar harmonics, spacious hopeful lo-fi atmosphere",
}

IDENTITIES = [
    "four-note mellow piano motif",
    "gentle acoustic guitar melody answered by rhodes chords",
    "warm rhodes lead with relaxed syncopated piano response",
    "simple jazzy piano ostinato with subtle harmonic color",
    "lyrical guitar phrase with understated brushed-drum pocket",
    "dusty cassette keyboard motif, calm and nostalgic",
    "mellow bass-led groove with small piano flourishes",
    "spacious electric-piano call and response melody",
    "descending piano motif resolving into warm major-seventh harmony",
    "cozy guitar arpeggio with soft jazz piano fills",
    "restrained swung piano hook with no aggression",
    "floating rhodes melody with delicate high-register piano accents",
    "warm guitar motif and rounded bass conversation",
    "rainy-window piano melody with sparse ornamental notes",
    "hopeful dawn motif with soft guitar harmonics and tender piano resolution",
]

RHYTHMS = [
    "straight relaxed pocket", "slight lazy swing", "soft two-step pocket", "light triplet feel",
    "gentle behind-the-beat groove", "quiet head-nod pulse", "sparse brushed shuffle", "steady candlelit pulse",
    "subtle syncopated pocket", "unhurried half-time feel", "soft broken-beat pocket", "delicate swing",
    "minimal four-on-the-floor pulse", "loose jazz pocket", "calm offbeat groove",
]


def save_audio(audio: torch.Tensor, sample_rate: int, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    audio = audio.detach().float().cpu()
    if audio.ndim == 3:
        audio = audio[0]
    if audio.ndim == 1:
        audio = audio.unsqueeze(0)
    peak = audio.abs().max().item()
    if peak > 0:
        audio = audio / max(peak, 1.0)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            torchaudio.save(str(path), audio, sample_rate)
            return
        except Exception as error:  # transient macOS/filesystem failures can occur under load
            last_error = error
            if attempt < 2:
                time.sleep(1.0)
    raise last_error  # type: ignore[misc]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=234.0)
    parser.add_argument("--segment-seconds", type=float, default=120.0)
    parser.add_argument("--segment-fade", type=float, default=6.0)
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--cfg-scale", type=float, default=1.0)
    parser.add_argument("--album-style", default="rainy-cafe")
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--variant", default=None, help="Deprecated alias for --album-style")
    parser.add_argument("--track-index", type=int, default=1)
    parser.add_argument("--track-name", default="original-instrumental-motif")
    parser.add_argument("--seed", type=int, default=424301)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.segment_seconds > 120:
        raise SystemExit("Stable Audio 3 Small-Music supports segments up to 120 seconds")
    root = Path(__file__).resolve().parents[1]
    config_path = root / "config" / "stable_audio3_prompt_library.json"
    library = json.loads(config_path.read_text(encoding="utf-8"))
    profiles = {item["slug"]: item for item in library["albums"]}
    album_style = args.album_style or args.variant or "rainy-cafe"
    profile = profiles.get(album_style, {"prompt": album_style, "bpm": 85})
    identity_index = (args.track_index - 1) % len(IDENTITIES)
    track_variation = library["track_variations"][identity_index]
    if args.prompt:
        prompt = (
            f"{INSTRUMENTAL_GUARD}, {args.prompt}, "
            f"track title concept: {args.track_name}, "
            "compose a fresh genre-appropriate motif, arrangement, instrumentation, and chord voicing"
        )
        negative_prompt = NEGATIVE_PROMPT
    else:
        prompt = (
            f"{INSTRUMENTAL_GUARD}, {BASE_PROMPT}, album profile: {profile['prompt']}, "
            f"album tempo anchor: {profile.get('bpm', 85)} BPM, "
            f"track title concept: {args.track_name}, "
            f"distinct track identity: {IDENTITIES[identity_index]}, "
            f"track-specific arrangement and instrumentation: {track_variation['prompt']}, "
            f"do not use these competing lead instruments: {track_variation['avoid']}, "
            "keep the album profile unchanged while composing a fresh melody and fresh chord voicing"
        )
        negative_prompt = f"{NEGATIVE_PROMPT}, {track_variation['avoid']}"
    status = root / "tmp" / "render-progress.txt"
    status.parent.mkdir(parents=True, exist_ok=True)
    status.write_text("state=loading_model\nmusic_percent=0\nmusic_step=loading Stable Audio 3\n", encoding="utf-8")
    model = StableAudioModel.from_pretrained("small-music", model_half=False)
    sample_rate = int(model.model.sample_rate)

    segment_root = root / "tmp" / "stable-audio3-segments"
    segment_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="stable-audio3-", dir=segment_root) as tmp:
        tmp_dir = Path(tmp)
        parts: list[Path] = []
        for index in range(2):
            segment_prompt = prompt
            if index == 1:
                segment_prompt += ", seamless continuation of this exact track, preserve its motif and groove, no intro, no ending, no new section"
            audio = model.generate(
                prompt=segment_prompt,
                negative_prompt=negative_prompt,
                duration=args.segment_seconds,
                steps=args.steps,
                cfg_scale=args.cfg_scale,
                seed=args.seed + index,
                chunked_decode=True,
            )
            part = tmp_dir / f"part-{index}.wav"
            save_audio(audio, sample_rate, part)
            parts.append(part)
            print(f"generated segment {index + 1}/2", flush=True)
            status.write_text(
                f"state=generating_music\nmusic_percent={(index + 1) * 40}\nmusic_step=segment {index + 1}/2\n",
                encoding="utf-8",
            )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        status.write_text("state=assembling_audio\nmusic_percent=90\nmusic_step=crossfading segments\n", encoding="utf-8")
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
                "-i", str(parts[0]), "-i", str(parts[1]),
                "-filter_complex",
                f"[0:a][1:a]acrossfade=d={args.segment_fade}:c1=tri:c2=tri,atrim=duration={args.duration},afade=t=in:st=0:d=2,afade=t=out:st={max(0, args.duration - 2)}:d=2[a]",
                "-map", "[a]", "-ar", "44100", "-c:a", "libmp3lame", "-q:a", "2", str(args.output),
            ],
            check=True,
        )
    status.write_text(f"state=music_complete\nmusic_percent=100\nmusic_step=complete\nmusic_file={args.output}\n", encoding="utf-8")
    print(f"Generated {args.output}", flush=True)


if __name__ == "__main__":
    main()
