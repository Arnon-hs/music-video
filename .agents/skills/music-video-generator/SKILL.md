---
name: music-video-generator
description: Operate the Music Video Generator repository to inspect model readiness, generate local instrumental tracks or one-hour playlist videos, monitor progress, validate media, and prepare private Postiz drafts. Use for this project's CLI or remote GPU workflow; never download models/media or publish without explicit approval.
---

# Music Video Generator

Use the repository's CLI as the control plane. Prefer the current checkout when it contains `music_video_cli.py` and the executable `music-video`; otherwise resolve the repository from this skill's real path. Read `README.md` only when setup detail is needed.

## Start every job safely

1. Run `git status --short --branch` and preserve unrelated changes.
2. Run `./music-video doctor --json` and `./music-video genres --json`.
3. Select a backend with `ready: true`. If none is ready, report the exact missing paths and stop before installing or downloading anything.
4. Show a bounded `--dry-run` before using model time.
5. Ask for explicit approval before model/media downloads, remote GPU provisioning, Postiz upload, or publication.

## Generate one track

Use `./music-video generate` with an explicit backend, genre, duration, and optional prompt. Keep the instrumental/originality guard intact. Use `--video` only when a reviewed local image exists in `assets/images`.

## Build a one-hour playlist

Use `./music-video playlist` with an explicit backend, genre, and image. The CLI plans varied track durations and prompts, joins them with crossfades, fits one image without cropping, and targets exactly 3,600 seconds. Preserve valid completed tracks when resuming.

## Monitor and verify

- Read `./music-video status --json`; do not estimate progress from elapsed time.
- Validate every final artifact with `ffprobe` for duration and streams.
- Ask for human listening and visual review before calling the result ready.
- Keep generated media, model weights, logs, `.env`, and credentials out of Git.

## Remote GPU mode

For RunPod, Vast.ai, or another GPU VM, treat the remote machine as a Linux workstation reached through SSH. Keep the checkout, models, and outputs on persistent storage, run the same `doctor` and dry-run sequence, and retrieve the verified MP4 before stopping compute. Read `docs/REMOTE_GPU.md` for the current supported pattern.

The repository does not yet include a RunPod Serverless worker, Docker image, or public music-generation HTTP endpoint. Do not present those modes as ready.

## Postiz boundary

Postiz is an optional publishing API, not a music-generation backend. Only after explicit user request, load credentials from the environment, run `python3 scripts/postiz_upload_ready_videos.py --dry-run`, then create a private draft. Verify the returned post ID and the actual draft; never publish automatically.

## Rights boundary

Repository licensing does not clear third-party model weights, images, or generated outputs. Keep MusicGen results labelled `NON_COMMERCIAL_DEMO`; review the selected model and all media rights before external use.
