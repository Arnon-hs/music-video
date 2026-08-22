#!/usr/bin/env python3
"""Small interactive and scriptable CLI for the music-video pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import shlex
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parent
GENRES_PATH = ROOT / "config" / "genres.json"
STATUS_PATH = ROOT / "tmp" / "render-progress.txt"

BACKENDS = {
    "musicgen": "MusicGen (NON_COMMERCIAL_DEMO)",
    "ace-step": "ACE-Step",
    "diffrhythm2": "DiffRhythm 2",
    "stable-audio3": "Stable Audio 3",
}

GENRE_ALIASES = {
    "lo-fi": "lofi",
    "lo_fi": "lofi",
    "classic": "classical",
    "dnb": "drum-and-bass",
    "drum-and-bass": "drum-and-bass",
    "hip-hop": "instrumental-hip-hop",
}
MAX_PROMPT_CHARACTERS = 2_000
MAX_SEED = 2**32 - 1
PLAYLIST_SECONDS = 3_600
DEFAULT_CROSSFADE_SECONDS = 3
MIN_TRACK_SECONDS = 10
BACKEND_DURATION_LIMITS = {
    "musicgen": 3_600,
    "ace-step": 600,
    "diffrhythm2": 210,
    "stable-audio3": 234,
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
PLAYLIST_VARIATIONS = (
    "open with a restrained groove and introduce one clear original motif",
    "use a fresh chord voicing and a contrasting lead instrument",
    "shift the percussion texture while preserving the genre and tempo range",
    "develop a new melodic answer with a lighter arrangement",
    "emphasise bass movement and subtle rhythmic syncopation",
    "use warmer harmony and a more spacious middle section",
    "feature a different genre-appropriate instrument as the lead",
    "create a calm bridge and return to a newly varied original motif",
)


@dataclass(frozen=True)
class Generation:
    command: list[str]
    environment: dict[str, str]
    audio_path: Path
    prompt: str


@dataclass(frozen=True)
class PlaylistPlan:
    backend: str
    genre: str
    image_path: Path
    video_path: Path
    crossfade_seconds: int
    tracks: tuple[Generation, ...]


def load_catalog() -> dict:
    return json.loads(GENRES_PATH.read_text(encoding="utf-8"))


def genres_by_slug() -> dict[str, dict]:
    return {item["slug"]: item for item in load_catalog()["genres"]}


def resolve_genre(value: str) -> str:
    slug = GENRE_ALIASES.get(value.strip().lower(), value.strip().lower())
    if slug not in genres_by_slug():
        available = ", ".join(genres_by_slug())
        raise ValueError(f"Unknown genre: {value}. Available: {available}")
    return slug


def genre_prompt(slug: str) -> str:
    catalog = load_catalog()
    genre = next(item for item in catalog["genres"] if item["slug"] == slug)
    return f"{genre['prompt']} {catalog['instrumental_guard']}"


def backend_requirements(backend: str) -> list[Path]:
    if backend == "musicgen":
        return [ROOT / ".venv" / "bin" / "python"]
    if backend == "ace-step":
        return [ROOT / "ace-step-v1" / ".venv" / "bin" / "python", ROOT / "models" / "ace-step"]
    if backend == "diffrhythm2":
        return [ROOT / ".venv-diffrhythm2" / "bin" / "python", ROOT / ".models" / "DiffRhythm2" / "inference.py"]
    return [ROOT / ".venv-stable-audio3" / "bin" / "python"]


def backend_available(backend: str) -> bool:
    return all(path.exists() for path in backend_requirements(backend))


def validate_duration(backend: str, duration: int) -> None:
    if duration < 10:
        raise ValueError("Duration must be at least 10 seconds")
    limit = BACKEND_DURATION_LIMITS[backend]
    if duration > limit:
        raise ValueError(f"{BACKENDS[backend]} supports at most {limit} seconds in one CLI run")


def validate_seed(seed: int) -> None:
    if not 0 <= seed <= MAX_SEED:
        raise ValueError(f"Seed must be between 0 and {MAX_SEED}")


def validate_custom_prompt(custom_prompt: str | None) -> str | None:
    if custom_prompt is None:
        return None
    prompt = custom_prompt.strip()
    if not prompt:
        return None
    if len(prompt) > MAX_PROMPT_CHARACTERS:
        raise ValueError(f"Prompt must not exceed {MAX_PROMPT_CHARACTERS} characters")
    if any(ord(character) < 32 or ord(character) == 127 for character in prompt):
        raise ValueError("Prompt must not contain control characters")
    return prompt


def build_generation(backend: str, genre: str, duration: int, seed: int, custom_prompt: str | None = None) -> Generation:
    validate_duration(backend, duration)
    validate_seed(seed)
    custom_prompt = validate_custom_prompt(custom_prompt)
    catalog = load_catalog()
    if custom_prompt:
        prompt = f"{custom_prompt} {catalog['instrumental_guard']}"
    else:
        prompt = genre_prompt(genre)
    environment = os.environ.copy()
    environment["MUSIC_GENRE"] = genre
    prompt_id = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8]
    target_dir = ROOT / "assets" / "music" / backend / genre / f"seed-{seed}-{prompt_id}"

    if backend == "musicgen":
        audio = target_dir / f"musicgen-{duration}s-seed-{seed}.wav"
        command = [
            str(ROOT / ".venv" / "bin" / "python"), "-u", str(ROOT / "scripts" / "generate_music.py"),
            "--duration", str(duration), "--seed", str(seed), "--prompt", prompt, "--output", str(audio),
        ]
    elif backend == "ace-step":
        audio = target_dir / f"ace-step-{duration}s-seed-{seed}.wav"
        environment["MUSIC_OUTPUT_DIR"] = str(target_dir)
        command = [
            str(ROOT / "ace-step-v1" / ".venv" / "bin" / "python"),
            str(ROOT / "scripts" / "generate_music_ace_step.py"),
            "--duration", str(duration), "--seed", str(seed), "--prompt", prompt,
        ]
    elif backend == "diffrhythm2":
        audio = target_dir / f"diffrhythm2-{duration}s-seed-{seed}.wav"
        command = [
            str(ROOT / ".venv-diffrhythm2" / "bin" / "python"),
            str(ROOT / "scripts" / "generate_music_diffrhythm2.py"),
            "--duration", str(duration), "--seed", str(seed), "--prompt", prompt, "--output", str(audio),
        ]
    else:
        audio = target_dir / f"stable-audio3-{duration}s-seed-{seed}.mp3"
        segment_seconds = min(120.0, (duration + 6.0) / 2)
        command = [
            str(ROOT / ".venv-stable-audio3" / "bin" / "python"),
            str(ROOT / "scripts" / "generate_music_stable_audio3.py"),
            "--duration", str(duration), "--segment-seconds", str(segment_seconds),
            "--seed", str(seed), "--prompt", prompt, "--output", str(audio),
        ]
    return Generation(command, environment, audio, prompt)


def auto_playlist_track_count(backend: str, crossfade_seconds: int) -> int:
    """Prefer roughly five-minute tracks while leaving room for duration variation."""
    count = 12
    safe_track_ceiling = int(BACKEND_DURATION_LIMITS[backend] * 0.9)
    while (PLAYLIST_SECONDS + crossfade_seconds * (count - 1)) / count > safe_track_ceiling:
        count += 1
    return count


def plan_track_durations(backend: str, count: int, crossfade_seconds: int) -> list[int]:
    if count < 2 or count > 50:
        raise ValueError("Playlist track count must be between 2 and 50")
    if crossfade_seconds < 0 or crossfade_seconds > 30:
        raise ValueError("Crossfade must be between 0 and 30 seconds")

    required_audio_seconds = PLAYLIST_SECONDS + crossfade_seconds * (count - 1)
    maximum = BACKEND_DURATION_LIMITS[backend]
    if required_audio_seconds < count * MIN_TRACK_SECONDS or required_audio_seconds > count * maximum:
        minimum_count = (PLAYLIST_SECONDS - crossfade_seconds + maximum - crossfade_seconds - 1) // (
            maximum - crossfade_seconds
        )
        raise ValueError(
            f"{BACKENDS[backend]} cannot fill one hour with {count} tracks; "
            f"use at least {minimum_count} tracks"
        )

    base, remainder = divmod(required_audio_seconds, count)
    durations = [base + (1 if index < remainder else 0) for index in range(count)]
    amplitude = min(base // 6, maximum - max(durations), min(durations) - MIN_TRACK_SECONDS)
    for pair in range(count // 2):
        low = pair * 2
        high = low + 1
        delta = max(1, amplitude * (pair + 2) // (count // 2 + 1)) if amplitude else 0
        delta = min(delta, durations[low] - MIN_TRACK_SECONDS, maximum - durations[high])
        durations[low] -= delta
        durations[high] += delta
    return durations


def playlist_prompt(genre: str, track_index: int, custom_prompt: str | None = None) -> str:
    base = validate_custom_prompt(custom_prompt) or genres_by_slug()[genre]["prompt"]
    variation = PLAYLIST_VARIATIONS[(track_index - 1) % len(PLAYLIST_VARIATIONS)]
    return (
        f"{base} Playlist track {track_index}: {variation}. "
        "Keep a coherent album identity while composing a distinct original arrangement."
    )


def image_candidates() -> list[Path]:
    directory = ROOT / "assets" / "images"
    if not directory.exists():
        return []
    return sorted(path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)


def resolve_image(value: str | None, dry_run: bool) -> Path:
    if value:
        image = Path(value).expanduser()
        if not image.is_absolute():
            image = ROOT / image
        image = image.resolve()
        if image.suffix.lower() not in IMAGE_SUFFIXES:
            raise ValueError("Playlist image must be JPG, JPEG, PNG, or WEBP")
        if not dry_run and not image.is_file():
            raise ValueError(f"Playlist image does not exist: {image}")
        return image
    images = image_candidates()
    if images:
        return images[0].resolve()
    if dry_run:
        return ROOT / "assets" / "images" / "cover.jpg"
    raise ValueError("No local images in assets/images. Add an image or pass --image PATH")


def resolve_playlist_output(value: str | None, genre: str, backend: str) -> Path:
    if value:
        output = Path(value).expanduser()
        if not output.is_absolute():
            output = ROOT / output
        output = output.resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output = ROOT / "output" / f"{backend}-{genre}-playlist-1h-{stamp}.mp4"
    if output.suffix.lower() != ".mp4":
        raise ValueError("Playlist output must use the .mp4 extension")
    return output


def build_playlist_plan(args: argparse.Namespace) -> PlaylistPlan:
    genre = resolve_genre(args.genre)
    validate_seed(args.seed)
    validate_custom_prompt(args.prompt)
    count = args.tracks if args.tracks is not None else auto_playlist_track_count(args.backend, args.crossfade)
    durations = plan_track_durations(args.backend, count, args.crossfade)
    image = resolve_image(args.image, args.dry_run)
    video = resolve_playlist_output(args.output, genre, args.backend)
    tracks = tuple(
        build_generation(
            args.backend,
            genre,
            duration,
            args.seed + (index - 1) * 7_919,
            playlist_prompt(genre, index, args.prompt),
        )
        for index, duration in enumerate(durations, 1)
    )
    return PlaylistPlan(args.backend, genre, image, video, args.crossfade, tracks)


def playlist_ffmpeg_command(plan: PlaylistPlan) -> list[str]:
    filters = [
        f"[{index}:a]aresample=48000,asetpts=PTS-STARTPTS[a{index - 1}]"
        for index in range(1, len(plan.tracks) + 1)
    ]
    chain = "[a0]"
    for index in range(1, len(plan.tracks)):
        label = f"mix{index}"
        filters.append(
            f"{chain}[a{index}]acrossfade=d={plan.crossfade_seconds}:c1=tri:c2=tri[{label}]"
        )
        chain = f"[{label}]"
    filters.append(
        f"{chain}apad,atrim=duration={PLAYLIST_SECONDS},"
        f"afade=t=in:st=0:d=1,afade=t=out:st={PLAYLIST_SECONDS - 3}:d=3[aout]"
    )
    audio_inputs = [item for track in plan.tracks for item in ("-i", str(track.audio_path))]
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
        "-loop", "1", "-framerate", "24", "-i", str(plan.image_path),
        *audio_inputs,
        "-filter_complex", ";".join(filters),
        "-map", "0:v:0", "-map", "[aout]",
        "-vf",
        "scale=1280:720:force_original_aspect_ratio=decrease:flags=lanczos,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p",
        "-t", str(PLAYLIST_SECONDS), "-r", "24",
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "medium", "-crf", "23",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ac", "2",
        "-movflags", "+faststart", "-progress", "pipe:1", "-nostats", str(plan.video_path),
    ]


def probe_duration(path: Path) -> float | None:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if result.returncode != 0:
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def read_status() -> dict[str, str]:
    if not STATUS_PATH.exists():
        return {}
    return {
        key: value
        for line in STATUS_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
        if "=" in line
        for key, value in [line.split("=", 1)]
    }


def write_status(**values: object) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text("".join(f"{key}={value}\n" for key, value in values.items()), encoding="utf-8")


def progress_text(stage: str, started_at: float) -> str:
    status = read_status()
    percent = status.get("music_percent") or status.get("percent")
    detail = status.get("music_step") or status.get("state") or "working"
    elapsed = int(time.monotonic() - started_at)
    progress = f" {percent}%" if percent is not None else ""
    return f"{stage}{progress} · {detail} · {elapsed // 60:02d}:{elapsed % 60:02d}"


def run_process(
    command: Sequence[str], environment: dict[str, str], stage: str,
    status_context: dict[str, object] | None = None,
) -> int:
    context = status_context or {}
    write_status(state="starting", stage=stage, music_percent=0, **context)
    process = subprocess.Popen(
        list(command), cwd=ROOT, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    output: queue.Queue[str | None] = queue.Queue()

    def read_output() -> None:
        assert process.stdout is not None
        for line in process.stdout:
            output.put(line)
        output.put(None)

    threading.Thread(target=read_output, daemon=True).start()
    started_at = time.monotonic()
    spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    index = 0
    reader_done = False
    last_plain_status = ""
    try:
        while process.poll() is None or not reader_done:
            while True:
                try:
                    line = output.get_nowait()
                except queue.Empty:
                    break
                if line is None:
                    reader_done = True
                    break
                if sys.stdout.isatty():
                    print("\r\033[K", end="")
                print(line.rstrip())
            current = progress_text(stage, started_at)
            if context:
                status = read_status()
                if any(status.get(key) != str(value) for key, value in context.items()):
                    write_status(**(status | context))
            if sys.stdout.isatty():
                print(f"\r\033[K{spinner[index % len(spinner)]} {current}", end="", flush=True)
            elif current != last_plain_status:
                print(f"... {current}")
                last_plain_status = current
            index += 1
            time.sleep(0.25)
    except KeyboardInterrupt:
        process.terminate()
        process.wait(timeout=10)
        write_status(state="cancelled", stage=stage)
        print("\nCancelled")
        return 130
    finally:
        if sys.stdout.isatty():
            print("\r\033[K", end="")
    code = process.wait()
    if code == 0:
        print(f"✓ {stage} complete")
    else:
        print(f"✗ {stage} failed with exit code {code}")
    return code


def print_genres(as_json: bool = False) -> None:
    items = load_catalog()["genres"]
    if as_json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return
    for item in items:
        print(f"{item['slug']:<22} {item['title']:<24} {item['bpm']} BPM")


def doctor_data() -> dict:
    return {
        "tools": {tool: shutil.which(tool) for tool in ("python3", "ffmpeg", "ffprobe", "curl", "jq")},
        "backends": {
            slug: {
                "ready": backend_available(slug),
                "required_paths": [str(path) for path in backend_requirements(slug)],
            }
            for slug in BACKENDS
        },
    }


def print_doctor(as_json: bool = False) -> None:
    data = doctor_data()
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    print("System tools:")
    for tool, path in data["tools"].items():
        print(f"  {'✓' if path else '✗'} {tool:<10} {path or 'not found'}")
    print("\nMusic backends:")
    for slug, title in BACKENDS.items():
        ready = data["backends"][slug]["ready"]
        state = "ready" if ready else "missing local environment/model"
        print(f"  {'✓' if ready else '·'} {slug:<16} {title} — {state}")


def render_video(audio: Path, genre: str, backend: str, environment: dict[str, str]) -> Path:
    images = ROOT / "assets" / "images"
    if not images.exists() or not any(path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} for path in images.iterdir()):
        raise ValueError("No local images in assets/images. Add images or run scripts/search_pexels_images.py first")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    visual = ROOT / "tmp" / f"visual-{genre}-{stamp}.mp4"
    video = ROOT / "output" / f"{backend}-{genre}-{stamp}.mp4"
    visual_env = environment | {
        "VISUAL_OUT": str(visual),
        "VISUAL_PROFILE": "energetic" if genre in {"techno", "electronic", "house", "synthwave", "drum-and-bass"} else "calm",
    }
    if run_process([str(ROOT / "scripts" / "render_visual_loop.sh"), "--force"], visual_env, "Visual loop") != 0:
        raise RuntimeError("Visual loop failed")
    label = "NON_COMMERCIAL_DEMO" if backend == "musicgen" else "RIGHTS_REVIEW_REQUIRED"
    build_env = environment | {
        "VISUAL_OVERRIDE": str(visual), "AUDIO_OVERRIDE": str(audio), "OUTPUT_OVERRIDE": str(video),
        "REENCODE_VIDEO": "1", "OUTPUT_LABEL": label,
        "MUSIC_LICENSE_NOTE": "Check the selected model, checkpoint, generated output, and media rights before publication.",
    }
    if run_process([str(ROOT / "scripts" / "build_video.sh")], build_env, "Final video") != 0:
        raise RuntimeError("Video build failed")
    return video


def run_generate(args: argparse.Namespace) -> int:
    try:
        genre = resolve_genre(args.genre)
        generation = build_generation(args.backend, genre, args.duration, args.seed, args.prompt)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    if args.dry_run:
        print(f"Backend: {BACKENDS[args.backend]}")
        print(f"Genre:   {genre}")
        print(f"Prompt:  {generation.prompt}")
        print(f"Audio:   {generation.audio_path}")
        print(f"Command: {shlex.join(generation.command)}")
        print(f"Video:   {'yes' if args.video else 'no'}")
        return 0
    missing = [str(path) for path in backend_requirements(args.backend) if not path.exists()]
    if missing:
        print(f"Backend {args.backend} is not ready. Missing:", file=sys.stderr)
        for path in missing:
            print(f"  - {path}", file=sys.stderr)
        print("Run ./music-video doctor and follow README.md.", file=sys.stderr)
        return 2
    generation.audio_path.parent.mkdir(parents=True, exist_ok=True)
    if args.force_cpu:
        generation.environment["FORCE_CPU"] = "1"
        generation.environment["ACE_DEVICE"] = "cpu"
    if not args.allow_downloads and args.backend in {"diffrhythm2", "stable-audio3"}:
        generation.environment["HF_HUB_OFFLINE"] = "1"
        generation.environment["TRANSFORMERS_OFFLINE"] = "1"
    code = run_process(generation.command, generation.environment, f"Generate {genre} with {args.backend}")
    if code != 0:
        return code
    write_status(state="music_complete", music_percent=100, genre=genre, backend=args.backend, audio=generation.audio_path)
    print(f"Audio: {generation.audio_path}")
    if args.video:
        try:
            video = render_video(generation.audio_path, genre, args.backend, generation.environment)
        except (ValueError, RuntimeError) as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1
        write_status(state="complete", percent=100, genre=genre, backend=args.backend, audio=generation.audio_path, video=video)
        print(f"Video: {video}")
    return 0


def print_playlist_plan(plan: PlaylistPlan) -> None:
    generated_seconds = sum(int(track.command[track.command.index("--duration") + 1]) for track in plan.tracks)
    print("Playlist: one-hour instrumental video")
    print(f"Backend:  {BACKENDS[plan.backend]}")
    print(f"Genre:    {plan.genre}")
    print(f"Image:    {plan.image_path}")
    print(f"Video:    {plan.video_path}")
    print(f"Tracks:   {len(plan.tracks)} with {plan.crossfade_seconds}s crossfades")
    print(f"Timeline: {generated_seconds}s audio -> {PLAYLIST_SECONDS}s video")
    for index, track in enumerate(plan.tracks, 1):
        duration = track.command[track.command.index("--duration") + 1]
        print(f"\nTrack {index:02d}/{len(plan.tracks)} · {duration}s")
        print(f"  Audio:   {track.audio_path}")
        print(f"  Prompt:  {track.prompt}")
        print(f"  Command: {shlex.join(track.command)}")
    print(f"\nRender: {shlex.join(playlist_ffmpeg_command(plan))}")


def run_playlist_render(plan: PlaylistPlan) -> int:
    plan.video_path.parent.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen(
        playlist_ffmpeg_command(plan), cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    assert process.stdout is not None
    started_at = time.monotonic()
    last_percent = -1
    try:
        for raw_line in process.stdout:
            line = raw_line.strip()
            if line.startswith("out_time_us="):
                try:
                    seconds = int(line.split("=", 1)[1]) / 1_000_000
                except ValueError:
                    continue
                percent = min(99, int(seconds * 100 / PLAYLIST_SECONDS))
                if percent != last_percent:
                    write_status(
                        state="rendering_playlist_video", percent=percent, genre=plan.genre,
                        backend=plan.backend, tracks=len(plan.tracks), image=plan.image_path,
                        video=plan.video_path,
                    )
                    elapsed = int(time.monotonic() - started_at)
                    if sys.stdout.isatty():
                        print(f"\r\033[KRendering one-hour video {percent}% · {elapsed // 60:02d}:{elapsed % 60:02d}", end="", flush=True)
                    elif percent == 0 or percent == 99 or percent // 10 > last_percent // 10:
                        print(f"... Rendering one-hour video {percent}%")
                    last_percent = percent
            elif line and "=" not in line:
                if sys.stdout.isatty():
                    print("\r\033[K", end="")
                print(line)
    except KeyboardInterrupt:
        process.terminate()
        process.wait(timeout=10)
        write_status(state="cancelled", stage="playlist video")
        print("\nCancelled")
        return 130
    finally:
        if sys.stdout.isatty():
            print("\r\033[K", end="")
    code = process.wait()
    if code == 0:
        print("✓ One-hour playlist video complete")
    else:
        print(f"✗ Playlist video failed with exit code {code}")
    return code


def run_playlist(args: argparse.Namespace) -> int:
    try:
        plan = build_playlist_plan(args)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    if args.dry_run:
        print_playlist_plan(plan)
        return 0

    missing_tools = [tool for tool in ("ffmpeg", "ffprobe") if not shutil.which(tool)]
    if missing_tools:
        print(f"Missing required tools: {', '.join(missing_tools)}", file=sys.stderr)
        return 2
    missing_backend = [str(path) for path in backend_requirements(plan.backend) if not path.exists()]
    if missing_backend:
        print(f"Backend {plan.backend} is not ready. Missing:", file=sys.stderr)
        for path in missing_backend:
            print(f"  - {path}", file=sys.stderr)
        print("Run ./music-video doctor and follow README.md.", file=sys.stderr)
        return 2
    if plan.video_path.exists():
        print(f"Refusing to overwrite existing video: {plan.video_path}", file=sys.stderr)
        return 2

    print(
        f"Starting one-hour playlist: {BACKENDS[plan.backend]} · {plan.genre} · "
        f"{len(plan.tracks)} varied tracks · image={plan.image_path.name}"
    )
    for index, generation in enumerate(plan.tracks, 1):
        duration = int(generation.command[generation.command.index("--duration") + 1])
        existing_duration = probe_duration(generation.audio_path) if generation.audio_path.is_file() else None
        if existing_duration is not None and duration - 1 <= existing_duration <= duration + 2:
            print(f"✓ Track {index:02d}/{len(plan.tracks)} already ready: {generation.audio_path}")
        else:
            generation.audio_path.parent.mkdir(parents=True, exist_ok=True)
            if args.force_cpu:
                generation.environment["FORCE_CPU"] = "1"
                generation.environment["ACE_DEVICE"] = "cpu"
            if not args.allow_downloads and plan.backend in {"diffrhythm2", "stable-audio3"}:
                generation.environment["HF_HUB_OFFLINE"] = "1"
                generation.environment["TRANSFORMERS_OFFLINE"] = "1"
            code = run_process(
                generation.command, generation.environment,
                f"Track {index:02d}/{len(plan.tracks)} · {duration}s · {plan.genre}",
                {
                    "playlist_track": index, "playlist_total": len(plan.tracks),
                    "track_duration": duration, "genre": plan.genre, "backend": plan.backend,
                    "image": plan.image_path,
                },
            )
            if code != 0:
                return code
            actual_duration = probe_duration(generation.audio_path)
            if actual_duration is None or not duration - 1 <= actual_duration <= duration + 2:
                print(
                    f"Generated track failed duration validation: {generation.audio_path} "
                    f"(expected about {duration}s, got {actual_duration})",
                    file=sys.stderr,
                )
                return 1
        write_status(
            state="generating_playlist_music", playlist_track=index,
            playlist_completed=index, playlist_total=len(plan.tracks), music_percent=100,
            genre=plan.genre, backend=plan.backend, image=plan.image_path,
        )

    write_status(
        state="rendering_playlist_video", percent=0, genre=plan.genre,
        backend=plan.backend, tracks=len(plan.tracks), image=plan.image_path,
        video=plan.video_path,
    )
    code = run_playlist_render(plan)
    if code != 0:
        return code
    video_duration = probe_duration(plan.video_path)
    if video_duration is None or not PLAYLIST_SECONDS - 1 <= video_duration <= PLAYLIST_SECONDS + 1:
        print(
            f"Final video failed duration validation: expected {PLAYLIST_SECONDS}s, got {video_duration}",
            file=sys.stderr,
        )
        return 1
    write_status(
        state="complete", percent=100, genre=plan.genre, backend=plan.backend,
        tracks=len(plan.tracks), image=plan.image_path, video=plan.video_path,
        duration=PLAYLIST_SECONDS,
    )
    print(f"Video: {plan.video_path}")
    print("Next: review the complete video, then use the existing Postiz dry-run before creating a private draft.")
    return 0


def choose(label: str, values: list[tuple[str, str]], default: int = 1) -> str:
    print(f"\n{label}")
    for index, (_, title) in enumerate(values, 1):
        print(f"  {index}. {title}")
    while True:
        answer = input(f"Choice [{default}]: ").strip()
        if not answer:
            return values[default - 1][0]
        if answer.isdigit() and 1 <= int(answer) <= len(values):
            return values[int(answer) - 1][0]
        print("Enter a number from the list")


def interactive() -> int:
    print("Music Video Generator")
    print("Instrumental music and video, locally on this computer.")
    mode = choose(
        "What do you want to create?",
        [
            ("single", "Single track with optional video"),
            ("playlist", "One-hour playlist video · varied tracks · one image"),
        ],
    )
    catalog = load_catalog()["genres"]
    genre = choose("Genre:", [(item["slug"], f"{item['title']} · {item['bpm']} BPM") for item in catalog])
    backend_values = [
        (slug, f"{title} [{'ready' if backend_available(slug) else 'setup required'}]")
        for slug, title in BACKENDS.items()
    ]
    backend = choose("Generator:", backend_values)
    if mode == "playlist":
        images = image_candidates()
        if not images:
            print("No local images in assets/images. Add an image before building a playlist video.", file=sys.stderr)
            return 2
        image = choose(
            "Image for the whole video:",
            [(str(path), path.name) for path in images],
        )
        force_cpu = input("Force CPU mode? [y/N]: ").strip().lower() in {"y", "yes", "д", "да"}
        allow_downloads = input("Allow this backend to download missing model files? [y/N]: ").strip().lower() in {"y", "yes", "д", "да"}
        count = auto_playlist_track_count(backend, DEFAULT_CROSSFADE_SECONDS)
        print(f"\nStarting: {BACKENDS[backend]} · {genre} · 1 hour · {count} varied tracks · {Path(image).name}")
        return run_playlist(argparse.Namespace(
            backend=backend, genre=genre, tracks=None, crossfade=DEFAULT_CROSSFADE_SECONDS,
            seed=20260822, prompt=None, image=image, output=None,
            force_cpu=force_cpu, allow_downloads=allow_downloads, dry_run=False,
        ))
    default_duration = 60
    answer = input(f"Duration in seconds [{default_duration}]: ").strip()
    try:
        duration = int(answer) if answer else default_duration
    except ValueError:
        print("Duration must be an integer", file=sys.stderr)
        return 2
    video = input("Build video from assets/images after music? [y/N]: ").strip().lower() in {"y", "yes", "д", "да"}
    force_cpu = input("Force CPU mode? [y/N]: ").strip().lower() in {"y", "yes", "д", "да"}
    allow_downloads = input("Allow this backend to download missing model files? [y/N]: ").strip().lower() in {"y", "yes", "д", "да"}
    print(f"\nStarting: {BACKENDS[backend]} · {genre} · {duration}s · video={'yes' if video else 'no'}")
    return run_generate(argparse.Namespace(
        backend=backend, genre=genre, duration=duration, seed=20260822,
        video=video, force_cpu=force_cpu, allow_downloads=allow_downloads, dry_run=False, prompt=None,
    ))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate instrumental music and optional video")
    subparsers = parser.add_subparsers(dest="command")
    genres_parser = subparsers.add_parser("genres", help="list available genres")
    genres_parser.add_argument("--json", action="store_true")
    doctor_parser = subparsers.add_parser("doctor", help="check local tools and model environments")
    doctor_parser.add_argument("--json", action="store_true")
    status_parser = subparsers.add_parser("status", help="show the last/current generation status")
    status_parser.add_argument("--json", action="store_true")
    generate = subparsers.add_parser("generate", help="generate music and optionally build a video")
    generate.add_argument("--backend", choices=BACKENDS, default="musicgen")
    generate.add_argument("--genre", default="lofi")
    generate.add_argument("--duration", type=int, default=60, help="seconds")
    generate.add_argument("--seed", type=int, default=20260822)
    generate.add_argument("--prompt", help="custom instrumental prompt; overrides the selected genre prompt")
    generate.add_argument("--video", action="store_true", help="build a video from assets/images")
    generate.add_argument("--force-cpu", action="store_true")
    generate.add_argument("--allow-downloads", action="store_true", help="allow a backend to fetch missing model files")
    generate.add_argument("--dry-run", action="store_true", help="show the command without running models")
    playlist = subparsers.add_parser(
        "playlist", help="generate varied tracks and build a one-hour video with one image"
    )
    playlist.add_argument("--backend", choices=BACKENDS, default="musicgen")
    playlist.add_argument("--genre", default="lofi")
    playlist.add_argument("--tracks", type=int, help="track count; automatically selected when omitted")
    playlist.add_argument("--crossfade", type=int, default=DEFAULT_CROSSFADE_SECONDS, help="seconds, default: 3")
    playlist.add_argument("--seed", type=int, default=20260822)
    playlist.add_argument("--prompt", help="custom album style prompt; each track still receives a distinct variation")
    playlist.add_argument("--image", help="JPG, PNG, or WEBP used for the whole video; defaults to the first local image")
    playlist.add_argument("--output", help="final .mp4 path")
    playlist.add_argument("--force-cpu", action="store_true")
    playlist.add_argument("--allow-downloads", action="store_true", help="allow a backend to fetch missing model files")
    playlist.add_argument("--dry-run", action="store_true", help="show every track and render command without running models")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        if not sys.stdin.isatty():
            parser.print_help()
            return 0
        return interactive()
    if args.command == "genres":
        print_genres(args.json)
        return 0
    if args.command == "doctor":
        print_doctor(args.json)
        return 0
    if args.command == "status":
        status = read_status()
        if not status:
            print("{}" if args.json else "No generation status yet")
            return 0
        if args.json:
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return 0
        for key, value in status.items():
            print(f"{key}: {value}")
        return 0
    if args.command == "playlist":
        return run_playlist(args)
    return run_generate(args)


if __name__ == "__main__":
    raise SystemExit(main())
