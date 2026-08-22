#!/usr/bin/env python3
"""Local Apache-2.0 ACE-Step generator for commercial-track drafts.

Run this file only through ace-step-v1/.venv. The default CPU offload is
intentional for Apple Silicon machines with 16 GB unified memory.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable, Iterator, TypeVar

import yaml

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = ROOT / "models" / "ace-step"
OUTPUT = Path(os.environ.get("MUSIC_OUTPUT_DIR", str(ROOT / "assets" / "music" / "ace-step")))
STATUS = ROOT / "tmp" / "render-progress.txt"
T = TypeVar("T")


def write_status(**values: object) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    current = {}
    if STATUS.exists():
        current = {
            line.split("=", 1)[0]: line.split("=", 1)[1]
            for line in STATUS.read_text(encoding="utf-8").splitlines()
            if "=" in line
        }
    current.update({key: str(value) for key, value in values.items()})
    STATUS.write_text(
        "".join(f"{key}={value}\n" for key, value in current.items()),
        encoding="utf-8",
    )


def progress_tqdm(iterable: Iterable[T] | None = None, *args: object, **kwargs: object) -> Iterator[T]:
    """Expose ACE-Step diffusion steps through the project's status file."""
    if iterable is None:
        return iter(())
    total = kwargs.get("total")
    if total is None:
        try:
            total = len(iterable)  # type: ignore[arg-type]
        except TypeError:
            total = 0
    total = int(total or 0)
    for index, item in enumerate(iterable, 1):
        percent = min(99, int(index * 100 / total)) if total else 0
        write_status(state="generating_music", music_percent=percent, music_step=f"{index}/{total}")
        yield item
    if total:
        write_status(state="saving_audio", music_percent=99, music_step=f"{total}/{total} — decoding/saving WAV")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--seed", type=int, default=20260725)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--steps", type=int, default=27)
    parser.add_argument("--no-cpu-offload", action="store_true")
    args = parser.parse_args()

    if not CHECKPOINT.exists():
        raise SystemExit(f"Missing ACE-Step checkpoint: {CHECKPOINT}")
    import torch
    force_cpu = os.environ.get("ACE_DEVICE", "mps").lower() == "cpu"
    if force_cpu:
        # ACE-Step's MPS path can deadlock in nonzero().item() on Apple Silicon.
        torch.backends.mps.is_available = lambda: False
    import acestep.pipeline_ace_step as ace_step_module
    ace_step_module.tqdm = progress_tqdm
    ACEStepPipeline = ace_step_module.ACEStepPipeline


    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    prompt = args.prompt or config["music_prompt"]
    commercial_prompt = f"{prompt} Original composition for commercial use; no artist imitation, no recognisable melody."
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / f"ace-step-{int(args.duration)}s-seed-{args.seed}.wav"
    write_status(state="loading_model", music_percent=0, music_step="loading checkpoint")

    pipeline = ACEStepPipeline(
        checkpoint_dir=str(CHECKPOINT),
        dtype="float32",  # ACE-Step requires this on macOS MPS.
        cpu_offload=not force_cpu and not args.no_cpu_offload,
        overlapped_decode=True,
    )
    write_status(state="generating_music", music_percent=0, music_step=f"0/{args.steps}")
    pipeline(
        format="wav",
        audio_duration=args.duration,
        prompt=commercial_prompt,
        lyrics="",
        infer_step=args.steps,
        guidance_scale=7.0,
        scheduler_type="euler",
        manual_seeds=[args.seed],
        task="text2music",
        save_path=str(target),
    )
    write_status(state="music_complete", music_percent=100, music_step=f"{args.steps}/{args.steps}", music_file=target)
    (ROOT / "metadata" / "ace-step-license.txt").write_text(
        "ACE-Step-v1-3.5B model weights: Apache-2.0.\n"
        "Commercial use is permitted by the model license; review generated output for originality and third-party rights before release.\n",
        encoding="utf-8",
    )
    print(f"Created {target} using ACE-Step Apache-2.0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
