#!/usr/bin/env python3
"""Generate a non-commercial MusicGen demo locally, then make a 60-minute mix."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMPDIR = ROOT / "tmp"
TMPDIR.mkdir(parents=True, exist_ok=True)
# These are read by the libraries during import/initialisation. Keeping MPSGraph
# scratch files on the external work disk prevents large temporary files on macOS.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
os.environ.setdefault("TMPDIR", str(TMPDIR))
MODEL_ID = "facebook/musicgen-small"
MODEL_CACHE = ROOT / "models" / "huggingface"
MUSIC_DIR = Path(os.environ.get("MUSIC_DIR_OVERRIDE", str(ROOT / "assets" / "music")))
METADATA_DIR = ROOT / "metadata"
VARIATIONS = [
    "emphasize warm Rhodes chords and restrained drums",
    "add sparse, original muted guitar fragments",
    "make distant rain ambience slightly more present",
    "add subtle tape wow and flutter",
    "add a soft, low-volume synth pad",
    "emphasize dusty vinyl crackle without a melody",
]


def require(command: str) -> None:
    if not shutil.which(command):
        raise RuntimeError(f"Required command is missing: {command}")


def confirm_model_download() -> bool:
    model_marker = MODEL_CACHE / "models--facebook--musicgen-small"
    if model_marker.exists():
        return True
    print("MusicGen model is not cached locally.")
    print("Expected download: about 2.36 GB for model.safetensors; Hugging Face lists 5.81 GB total repository content.")
    print(f"Model: {MODEL_ID}; license: CC-BY-NC 4.0; output will be marked NON_COMMERCIAL_DEMO.")
    print(f"Cache location: {MODEL_CACHE}")
    return input("Type DOWNLOAD_MODEL to download the model, or press Enter to cancel: ").strip() == "DOWNLOAD_MODEL"


def main() -> int:
    try:
        require("ffmpeg")
        require("ffprobe")
        import numpy as np
        import soundfile as sf
        import torch
        import yaml
        from transformers import AutoProcessor, MusicgenForConditionalGeneration
    except Exception as exc:
        print(f"Cannot start generation: {exc}", file=sys.stderr)
        return 1

    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    count, seconds = int(config["music_segments"]), int(config["segment_seconds"])
    if count != 12 or seconds != 30:
        print("This demo is designed for exactly 12 x 30-second source segments.", file=sys.stderr)
        return 1
    if not confirm_model_download():
        print("Cancelled before model download. No model files were fetched.")
        return 0

    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(MODEL_CACHE))
    print("Loading local MusicGen. MPS will be used when supported; CPU fallback will be offered on an MPS error.")
    try:
        processor = AutoProcessor.from_pretrained(MODEL_ID, cache_dir=str(MODEL_CACHE))
        # Eager attention avoids a known MPS incompatibility in the SDPA path.
        model = MusicgenForConditionalGeneration.from_pretrained(
            MODEL_ID, cache_dir=str(MODEL_CACHE), use_safetensors=True, attn_implementation="eager"
        )
    except Exception as exc:
        print(f"Model loading failed: {exc}", file=sys.stderr)
        return 1

    device = "cpu" if os.environ.get("FORCE_CPU") == "1" else ("mps" if torch.backends.mps.is_available() else "cpu")
    if device == "mps":
        internal_free = shutil.disk_usage("/").free
        minimum_mps_scratch = 12 * 1024**3
        if internal_free < minimum_mps_scratch:
            print(
                "MPS cannot start safely: macOS MPSGraph needs at least 12 GiB free on the internal system volume "
                f"and only {internal_free / 1024**3:.1f} GiB is available."
            )
            if input("Use CPU instead? Type CPU to continue: ").strip() != "CPU":
                print("Cancelled before generation.")
                return 0
            device = "cpu"
    try:
        model.to(device).eval()
    except Exception as exc:
        print(f"MPS setup failed: {exc}")
        if input("Use CPU instead? Type CPU to continue: ").strip() != "CPU":
            return 1
        device = "cpu"
        model.to(device).eval()

    base_prompt = os.environ.get("MUSIC_PROMPT_OVERRIDE", config["music_prompt"])
    paths: list[Path] = []
    for index in range(count):
        seed = 20260724 + index * 7919
        prompt = f"{base_prompt} {VARIATIONS[index % len(VARIATIONS)]}. Original variation {index + 1}; no recognisable melody."
        destination = MUSIC_DIR / f"segment-{index + 1:02d}.wav"
        if destination.exists() and destination.stat().st_size > 100_000:
            print(f"Keeping existing segment {index + 1}/{count}: {destination.name}")
            paths.append(destination)
            continue
        print(f"Generating segment {index + 1}/{count} on {device} (seed {seed})...")
        try:
            torch.manual_seed(seed)
            if device == "mps":
                torch.mps.manual_seed(seed)
            inputs = processor(text=[prompt], padding=True, return_tensors="pt").to(device)
            with torch.inference_mode():
                audio = model.generate(**inputs, do_sample=True, guidance_scale=3.0, max_new_tokens=1500)
        except Exception as exc:
            if device != "mps":
                print(f"Generation failed: {exc}", file=sys.stderr)
                return 1
            print(f"MPS generation failed: {exc}")
            if input("Retry this segment on CPU? Type CPU to continue: ").strip() != "CPU":
                return 1
            device = "cpu"
            model.to(device).eval()
            torch.manual_seed(seed)
            inputs = processor(text=[prompt], padding=True, return_tensors="pt").to(device)
            with torch.inference_mode():
                audio = model.generate(**inputs, do_sample=True, guidance_scale=3.0, max_new_tokens=1500)
        sample_rate = model.config.audio_encoder.sampling_rate
        waveform = audio[0, 0].detach().float().cpu().numpy()
        target_samples = sample_rate * seconds
        waveform = waveform[:target_samples] if len(waveform) >= target_samples else np.pad(waveform, (0, target_samples - len(waveform)))
        sf.write(destination, waveform, sample_rate, subtype="PCM_16")
        paths.append(destination)

    filter_parts = []
    for index in range(len(paths)):
        filter_parts.append(f"[{index}:a]aresample=48000,asetpts=PTS-STARTPTS[a{index}]")
    chain = "[a0]"
    for index in range(1, len(paths)):
        label = f"x{index}"
        filter_parts.append(f"{chain}[a{index}]acrossfade=d=4:c1=tri:c2=tri[{label}]")
        chain = f"[{label}]"
    master = MUSIC_DIR / "lofi-demo-master.wav"
    subprocess.run(["ffmpeg", "-hide_banner", "-y", *sum((["-i", str(p)] for p in paths), []), "-filter_complex", ";".join(filter_parts), "-map", chain, "-c:a", "pcm_s16le", str(master)], check=True)
    final = MUSIC_DIR / "lofi-demo.wav"
    duration_seconds = int(config["duration_minutes"]) * 60
    subprocess.run(["ffmpeg", "-hide_banner", "-y", "-stream_loop", "-1", "-i", str(master), "-t", str(duration_seconds), "-af", "afade=t=in:st=0:d=2,afade=t=out:st=3596:d=4", "-c:a", "pcm_s16le", str(final)], check=True)
    (METADATA_DIR / "music-license.txt").write_text("NON_COMMERCIAL_DEMO — MusicGen CC-BY-NC 4.0\nGenerated locally with facebook/musicgen-small. Replace lofi-demo.wav with a fully cleared final track before any commercial release.\n", encoding="utf-8")
    (METADATA_DIR / "segments.txt").write_text(json.dumps({"source_segments": [p.name for p in paths], "crossfade_seconds": 4, "master_duration_seconds": 316, "final_duration_seconds": duration_seconds, "label": "NON_COMMERCIAL_DEMO"}, indent=2) + "\n", encoding="utf-8")
    print(f"Created {final.relative_to(ROOT)} — NON_COMMERCIAL_DEMO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
