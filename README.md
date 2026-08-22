# Music Video Generator

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

Turn a music prompt into an instrumental track—or a full one-hour playlist video—without leaving your terminal. Pick a genre, choose a local model, watch real progress, and optionally turn the result into a private YouTube draft through Postiz.

This is a code-only, local-first project. Your music, images, model weights, logs, virtual environments, and real API keys stay outside Git.

## Start here: from clone to first dry-run

### 1. Open the project and check what is ready

```bash
git clone git@github.com:Arnon-hs/music-video.git
cd music-video

./music-video doctor
./music-video genres
```

`doctor` shows FFmpeg and the model environments already available on this machine. A backend marked as missing needs its own local setup before it can generate audio.

### 2. Preview a small job before spending model time

```bash
./music-video generate \
  --backend ace-step \
  --genre lofi \
  --duration 60 \
  --dry-run
```

A dry-run prints the prompt, output path, and exact command. It does not load a model or generate media.

### 3. Run it—or use the guided terminal UI

Remove `--dry-run` when the plan looks right, or start the interactive flow:

```bash
./music-video
```

The UI walks you through the result you want, genre, installed backend, duration, image/video choice, CPU fallback, and download permission.

## Pick your route

| I want to… | Start with | Result |
|---|---|---|
| explore without a model | `./music-video genres` and a `--dry-run` | validated command and prompt |
| make one instrumental track | `./music-video generate ...` | WAV or MP3 in `assets/music` |
| add artwork to a track | add `--video` and place an image in `assets/images` | MP4 in `output` |
| build a one-hour mix | `./music-video playlist ...` | varied same-genre tracks plus a 3,600-second MP4 |
| watch from a browser or phone | `./music-video web` | live CLI progress, logs, previews, and Postiz draft status |
| let an agent operate the CLI | use the copy-ready request below | bounded, observable workflow |
| prepare a YouTube upload | run the Postiz script with `--dry-run` first | private draft for human review |

## Give this to your coding agent

Replace the placeholders and paste this into Codex, Claude Code, or another local agent:

```text
Work in this repository and keep all generated files local.
1. Run ./music-video doctor --json and ./music-video genres --json.
2. Choose a backend with ready: true for <genre>.
3. Prepare <a 60-second track | a one-hour playlist video> using
   <backend>. Use assets/images/<cover-file> only if video is requested.
4. Show the complete --dry-run first. Do not download models or media
   without my approval.
5. After approval, run one bounded job and report the real output from
   ./music-video status --json.
6. Verify duration and streams with ffprobe, and ask me to listen/review.
7. Do not upload or publish anything. If I later request Postiz, run its
   --dry-run first and create only a private draft.
```

## Connect the project to a Codex work session

The repository includes a ready-to-use skill at `.agents/skills/music-video-generator`. This is the lightest integration: it teaches the agent how to inspect backends, require dry-runs, generate tracks/playlists, verify media, use a remote GPU, and keep Postiz private.

### Use it inside this repository—no installation

1. Clone the repository and open its root as the Codex workspace.
2. Start a new task from that folder. Codex discovers repository skills under `.agents/skills`.
3. Invoke it explicitly with `$music-video-generator`, or ask naturally for a track or playlist and let Codex match the skill.

Example first request:

```text
Use $music-video-generator. Inspect this checkout, show doctor and genres,
then prepare a dry-run for a one-hour lo-fi playlist with cover.jpg.
Do not install, download, upload, or publish anything yet.
```

### Make it available from any Codex workspace

Run the included installer once:

```bash
./scripts/install_codex_skill.sh
```

It creates a symlink at `~/.agents/skills/music-video-generator`, so updates from this checkout are picked up without copying the skill. It refuses to overwrite an existing path. Codex normally detects skill changes automatically; restart the client if the skill does not appear. To disconnect only this symlink:

```bash
unlink ~/.agents/skills/music-video-generator
```

See the [official OpenAI skill guide](https://developers.openai.com/codex/skills/) for discovery locations and invocation. A plugin is unnecessary for this single repo workflow; package it as a plugin later only if you need public installation, multiple skills, or bundled connectors.

The skill does not install models or rent infrastructure by itself. Those remain explicit, cost-bearing actions that require user approval.

## Why use it—and where it stops

| Advantages | Limitations |
|---|---|
| One CLI for four local music backends and 12 instrumental genres | Model code and weights are not bundled; each backend needs its own setup |
| Safe preview with `--dry-run`, visible progress, JSON status, and resumable playlists | Generation can be slow and memory-heavy, especially for one-hour playlists |
| Single-track MP4 and exact one-hour video with a fitted, uncropped image | The current video is intentionally simple: one image, no timeline editor or animated scene generation |
| Instrumental and originality guards are added to every prompt | A prompt cannot guarantee zero vocal-like sounds or clear every copyright/Content ID risk |
| Local-first files and private Postiz drafts | There is no built-in remote music-generation HTTP API and no automatic publication |

## Local machine, remote GPU, or API?

| Mode | Available now? | How it works |
|---|---|---|
| Local Mac/Linux workstation | Yes | Install one backend locally and run the CLI directly |
| RunPod Pod or GPU VPS | Yes | Treat it as a remote Linux workstation: SSH, persistent disk, same CLI, copy the verified result home |
| RunPod Serverless generation API | Not yet | Needs a container image, handler, artifact storage, authentication, and queue controls |
| LLM API | Bring your own | Ask any LLM for a prompt, then pass plain text through `--prompt`; this repo stores no LLM key and calls no LLM provider |
| Pexels API | Optional | Finds candidate images; download still requires explicit confirmation |
| Postiz API | Optional | Uploads a finished MP4 and creates a private draft; it does not generate music |

For the supported remote workflow, follow [RunPod or another GPU host](docs/REMOTE_GPU.md). A normal Pod/VM is the recommended first step because the current adapters expect local files and long-running processes.

## License and rights

Copyright 2026 Vasilii Bereznikov.

This project uses the [PolyForm Noncommercial License 1.0.0](LICENSE). You may use, study, modify, and share the code for permitted noncommercial purposes, provided that the license and required notice remain with distributed copies.

This is a source-available community license, not an OSI-approved open-source license. Apache-2.0 was intentionally not used because it permits commercial use. Commercial use of this repository requires separate permission from the owner.

Model code, weights, APIs, images, and generated outputs keep their own license and rights boundaries. Always review the selected model and every media asset before publishing; a permissive code license does not automatically clear model weights or generated music.

## Everyday CLI recipes

```bash
./music-video --help
./music-video genres
./music-video genres --json
./music-video doctor
./music-video doctor --json
./music-video status
./music-video status --json
./music-video web
```

Generate a 60-second techno track with ACE-Step:

```bash
./music-video generate \
  --backend ace-step \
  --genre techno \
  --duration 60
```

Generate classical music and assemble an MP4 from local images:

```bash
./music-video generate \
  --backend stable-audio3 \
  --genre classical \
  --duration 120 \
  --video
```

Preview the exact command and prompt without loading a model:

```bash
./music-video generate \
  --backend diffrhythm2 \
  --genre drum-and-bass \
  --duration 180 \
  --dry-run
```

Use an LLM-written instrumental prompt instead of the built-in genre prompt:

```bash
./music-video generate \
  --backend ace-step \
  --genre electronic \
  --duration 90 \
  --prompt "Instrumental modular electronic music, 118 BPM, evolving polyrhythms, deep bass, no vocals, no speech, original melody"
```

### One-hour playlist video

Put a permitted cover image in `assets/images`, inspect the complete plan, and then run it:

```bash
./music-video playlist \
  --backend ace-step \
  --genre lofi \
  --image assets/images/cover.jpg \
  --dry-run

./music-video playlist \
  --backend ace-step \
  --genre lofi \
  --image assets/images/cover.jpg \
  --force-cpu
```

The command generates distinct same-genre tracks with different durations, seeds, and arrangement prompts. It joins them with three-second crossfades and renders exactly 3,600 seconds of H.264/AAC video. The selected image is fitted inside 1280x720 with padding, never cropped or stretched.

Track count is selected automatically for each backend's duration limit: normally 12 for MusicGen/ACE-Step, 18 for Stable Audio 3, and 20 for DiffRhythm 2. Override it with `--tracks`, adjust transitions with `--crossfade`, provide an album-wide style with `--prompt`, or choose the final path with `--output`. Invalid combinations are rejected before model launch.

Valid existing track files are reused after an `ffprobe` duration check, so an interrupted playlist can resume. DiffRhythm/Stable Audio remain offline unless `--allow-downloads` is explicitly set; MusicGen keeps its separate manual `DOWNLOAD_MODEL` gate. The final video is also duration-checked before the CLI reports success.

Run `./music-video` without arguments and select **One-hour playlist video** for the guided workflow. Progress remains available through `./music-video status` and `./music-video status --json`. After reviewing the complete MP4, use the existing Postiz `--dry-run` workflow before creating a private YouTube draft.

Important flags:

| Flag | Meaning |
|---|---|
| `--backend` | `musicgen`, `ace-step`, `diffrhythm2`, or `stable-audio3` |
| `--genre` | genre slug; aliases include `classic`, `lo-fi`, and `dnb` |
| `--duration` | output duration in seconds; backend limits are validated before launch |
| `--seed` | deterministic generation seed |
| `--prompt` | custom style prompt, up to 2,000 characters without control characters; the instrumental guard is still appended |
| `--video` | render an MP4 after audio generation |
| `--force-cpu` | disable GPU/MPS use where supported |
| `--allow-downloads` | explicitly allow DiffRhythm/Stable Audio to fetch missing model files |
| `--dry-run` | print the prompt, output path, and command without running the model |

Genre definitions live in [`config/genres.json`](config/genres.json). Every built-in or custom prompt is combined with a strict instrumental guard that excludes vocals, speech, rap, choir, chants, voice samples, artist imitation, and recognisable copyrighted melodies.

## Watch the job and find your files

During generation the CLI shows:

- the current stage;
- percentage when the backend exposes reliable progress;
- current segment or diffusion step;
- elapsed time;
- backend log lines;
- final audio and video paths.

Another terminal or an agent can read the same state:

```bash
watch -n 2 './music-video status'
./music-video status --json
```

Runtime directories are created automatically and ignored by Git:

```text
assets/images/                 local input images
assets/music/<backend>/<genre>/ generated audio
output/                        generated MP4 files
tmp/                           progress, logs, and temporary renders
metadata/                      local build and rights notes
models/ and .models/           model weights and third-party checkouts
```

For `--video`, place at least one `.jpg`, `.jpeg`, `.png`, or `.webp` file in `assets/images`, or run the reviewed Pexels workflow described below.

## Choose a model

The CLI is an orchestrator: the model runs on the machine where you launch the command. Model code and weights are installed separately and are never committed to this repository.

| Backend | Good first use | CLI limit per track | Practical note | Rights note |
|---|---|---:|---|---|
| MusicGen | easiest included demo path, lo-fi experiments | 3,600 s | Python 3.11 environment; MPS/CPU fallback can be slow and needs local model cache | `facebook/musicgen-small` weights are CC-BY-NC 4.0; output is labelled `NON_COMMERCIAL_DEMO` |
| ACE-Step | longer original tracks and playlist work | 600 s | current adapter expects the exact local v1 layout; CPU is a stability fallback, not a speed option | verify the exact checkpoint/version and generated output before use |
| DiffRhythm 2 | short songs and many-track playlists | 210 s | offline by default; instrumental prompting can still produce vocal-like sound | verify code, weights, and output rights separately |
| Stable Audio 3 | ambient/electronic tracks and continuation-based playlists | 234 s | current adapter targets Small-Music and two generated segments | verify the selected model license and publication rights |

### What to expect from your hardware

These are conservative planning profiles for this repository, not universal model minimums. Start with a 30–60 second job: a successful `doctor` proves that paths exist, but not speed, memory headroom, model compatibility, or artistic quality.

#### Base computer requirements

| Component | CLI, dry-run, and FFmpeg only | Practical local generation | Comfortable playlist work |
|---|---|---|---|
| Operating system | macOS 14+ or a current 64-bit Linux distribution | macOS 14+ on Apple Silicon, or Ubuntu 22.04/24.04 on x86-64 | Linux with NVIDIA CUDA is the most compatible remote route |
| CPU | 4 modern cores | 8 modern cores | 8–16 cores; FFmpeg and CPU fallback benefit from more cores |
| Memory | 8 GB; do not expect dependable model generation | 16 GB is the practical floor for one short, lightweight job | 32 GB recommended; 64 GB is useful for heavy CPU fallback and multiple model caches |
| Free disk | 20 GB for code, tools, and temporary video work | at least 50 GB for one backend and short outputs | 100 GB recommended for one-hour work; 200 GB if keeping several backends/checkpoints |
| Required tools | Bash, Git, Python 3, FFmpeg, `ffprobe` | Python 3.11 plus one isolated backend environment | add `tmux`; on NVIDIA, use a driver/CUDA/PyTorch combination supported by that backend |
| Network | not needed for an already prepared dry-run | needed for the initial code/model download | stable connection for remote setup; generation itself can remain offline |

The MusicGen adapter also refuses MPS startup when the internal macOS volume has less than 12 GiB free. Model weights may live elsewhere, but macOS and PyTorch still need internal scratch space.

#### Which Macs are suitable?

Apple Silicon is the supported Mac family. Apple [documents PyTorch MPS](https://developer.apple.com/metal/pytorch/) on Apple Silicon and macOS 14 or later; CPU and GPU share unified memory, so the configured memory matters as much as the processor name.

| Mac configuration | Suitability for this project |
|---|---|
| Intel Mac | CLI and FFmpeg may work, but local model generation is untested and generally not recommended; use a remote NVIDIA GPU instead |
| M1/M2 with 8 GB | suitable for browsing the project, dry-runs, Postiz, and video assembly; too little headroom for dependable local generation |
| Any M1–M5 with 16 GB | minimum practical tier for one backend and 30–60 second experiments; close other memory-heavy apps and expect swapping or slow CPU fallback |
| M1–M5 Pro/Max with 24 or 32 GB | recommended local tier for repeated generation and playlist preparation; 32 GB gives noticeably safer headroom |
| Max/Ultra with 64 GB or more | best local headroom for heavier models and CPU fallback, but CUDA-only paths can still require a Linux/NVIDIA server |

Faster M-series generations reduce runtime, but extra unified memory usually improves reliability more than moving one chip generation forward with the same small memory capacity. This repository has been observed on an M4 with 16 GB; ACE-Step v1 required a very slow CPU fallback after an MPS deadlock, so that machine should not be presented as a fast one-hour renderer.

#### NVIDIA server or RunPod profile

| Profile | GPU VRAM | System RAM | CPU | Persistent disk | Use |
|---|---:|---:|---:|---:|---|
| Small experiment | 12–16 GB | 32 GB | 8 vCPU | 80 GB | one reviewed lightweight backend and short tests; not guaranteed for every adapter |
| Recommended | 24 GB | 64 GB | 8–16 vCPU | 150 GB | safest first choice for current backends and one-hour playlist jobs |
| High headroom | 48 GB+ | 64–128 GB | 16+ vCPU | 200 GB+ | larger/newer checkpoints, fewer offload compromises, or several retained environments |

A one-hour playlist does not need the entire hour in GPU memory: the CLI generates separate tracks and joins them later. It does increase total runtime, temporary storage, and failure exposure, so keep outputs on persistent storage and rely on resume support.

#### Backend-specific reality check

| Backend | Mac guidance | NVIDIA guidance |
|---|---|---|
| MusicGen small | 16 GB minimum, 24/32 GB preferred; MPS can fall back to CPU | 12–16 GB may be enough for this small model, but test 30 seconds first |
| ACE-Step v1 adapter | 16 GB runs only as a slow fallback in the observed setup; 32 GB+ is safer | start at 24 GB VRAM for this repository's older 3.5B adapter |
| DiffRhythm 2 | upstream installation mentions macOS, but this project's full MPS path is not validated | use 24 GB VRAM as the conservative first deployment |
| Stable Audio 3 Small-Music | 16 GB minimum, 24/32 GB preferred; current adapter is PyTorch-based, not the newer optimized MLX route | lightweight compared with larger variants; still test the exact checkpoint/runtime before a long queue |

Upstream projects can advertise lower requirements through quantization, offload, MLX, or newer model variants. Those numbers apply only when this repository's adapter actually uses that path. Always follow the upstream installation guide for the exact compatible model version, return to `./music-video doctor`, and run a short generation before renting hours of GPU time.

Check a Mac before setup:

```bash
system_profiler SPHardwareDataType
sw_vers
df -h /
./music-video doctor --json
```

Check a Linux/NVIDIA server:

```bash
nvidia-smi
lscpu
free -h
df -h /workspace
./music-video doctor --json
```

### [facebookresearch / AudioCraft (MusicGen)](https://github.com/facebookresearch/audiocraft)

MusicGen is the simplest included setup path. Its code and weights have different licenses; the `facebook/musicgen-small` weights are CC-BY-NC 4.0, so this backend is always labelled `NON_COMMERCIAL_DEMO`.

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-musicgen.txt

./music-video generate --backend musicgen --genre lofi --duration 60
```

The first model download requires typing `DOWNLOAD_MODEL` in the underlying generator. MusicGen keeps its own explicit confirmation flow.

The optional MusicGen environment pins its direct dependencies for safer review and security monitoring. Transitive resolution can still change. Rebuild the venv after dependency changes; do not reuse an environment created from older requirements.

### [ACE-Step / ACE-Step-1.5](https://github.com/ace-step/ACE-Step-1.5)

Expected local layout for the currently included adapter:

```text
ace-step-v1/.venv/bin/python
models/ace-step/
```

```bash
ACE_DEVICE=cpu ./music-video generate \
  --backend ace-step \
  --genre techno \
  --duration 60
```

The adapter targets the locally tested ACE-Step interface. New ACE-Step releases may require an adapter update; run `./music-video doctor` before generation.

### [ASLP-lab / DiffRhythm](https://github.com/ASLP-lab/DiffRhythm)

### [ASLP-lab / DiffRhythm2](https://github.com/ASLP-lab/DiffRhythm2)

The included adapter currently expects DiffRhythm 2:

```text
.models/DiffRhythm2/inference.py
.venv-diffrhythm2/bin/python
```

```bash
./music-video generate \
  --backend diffrhythm2 \
  --genre jazz \
  --duration 180
```

Instrumental mode is requested both through the style prompt and an `[inst]` lyric structure. Always listen to the result because a text constraint cannot guarantee that a generative model never produces vocal-like audio.

The CLI enables Hugging Face offline mode by default for this backend. Add `--allow-downloads` only after reviewing the expected model and size.

### [Stability-AI / stable-audio-3](https://github.com/Stability-AI/stable-audio-3)

### [Stability-AI / stable-audio-tools](https://github.com/Stability-AI/stable-audio-tools)

Expected local environment:

```text
.venv-stable-audio3/bin/python
```

```bash
./music-video generate \
  --backend stable-audio3 \
  --genre ambient \
  --duration 120
```

The current one-track adapter limits a run to 234 seconds. Longer albums are assembled by the existing queue scripts.

The CLI enables Hugging Face offline mode by default for this backend. Add `--allow-downloads` only after reviewing the expected model and size.

## Bring your own LLM

An LLM should produce a style prompt, not executable code or credentials. Keep the selected genre as a stable category and pass the detailed prompt through `--prompt`.

Recommended prompt contract:

```text
Create one concise English music-generation prompt.
The output must be purely instrumental: no vocals, speech, rap, choir,
chants, vocal chops, or voice samples. Do not imitate artists or quote
recognisable melodies. Include genre, BPM range, instrumentation, mood,
rhythm, arrangement, and mix characteristics.
```

Inspect the generated command before spending model time:

```bash
./music-video generate --backend ace-step --genre electronic \
  --prompt "<LLM prompt>" --duration 60 --dry-run
```

## Agent safety checklist

Use this safe sequence for Codex, Claude Code, or another local agent:

1. run `./music-video doctor --json`;
2. run `./music-video genres --json`;
3. select a backend that reports `ready: true`;
4. construct and show a `--dry-run` command;
5. obtain user approval before any model or media download;
6. run one bounded generation job;
7. poll `./music-video status --json` instead of guessing progress;
8. verify the resulting file with `ffprobe` and human listening/review;
9. never commit `.env`, media, models, checkpoints, logs, or generated output;
10. never upload or publish unless the user explicitly requests it.

For an even shorter start, invoke `$music-video-generator` and use the copy-ready request near the top of this guide. The repository skill applies this checklist automatically.

## Add artwork and build the MP4

Use your own cleared images by placing them in `assets/images`, or search Pexels candidates:

```bash
export PEXELS_API_KEY='your_key'
.venv/bin/python scripts/search_pexels_images.py
```

The script shows candidates first and downloads only after the exact confirmation `DOWNLOAD`. Pexels content remains subject to Pexels terms and human rights review.

With images ready:

```bash
./music-video generate --backend ace-step --genre synthwave --duration 90 --video
```

The CLI creates a temporary visual loop and uses a full H.264 re-encode for the final MP4.

## Send the finished video to Postiz

The uploader reads all account-specific values from environment variables. No integration ID or API key is stored in source code.

```bash
cp .env.example .env
```

Edit the local `.env`:

```dotenv
POSTIZ_API_KEY=your_real_key
POSTIZ_INTEGRATION_ID=your_youtube_integration_id
POSTIZ_API_ROOT=https://api.postiz.com/public/v1
POSTIZ_VIDEO_ROOT=output
# Optional; leave blank unless POSTIZ_VIDEO_ROOT is available through this server.
POSTIZ_LOCAL_BASE_URL=
```

Load it and create private drafts for new MP4 files:

```bash
set -a
source .env
set +a

python3 scripts/postiz_upload_ready_videos.py --dry-run
python3 scripts/postiz_upload_ready_videos.py
```

Watch for newly completed videos:

```bash
python3 scripts/postiz_upload_ready_videos.py --watch --interval 30
```

`--dry-run` lists pending videos without requiring credentials or contacting Postiz. The real run requests a top-level Postiz draft and private YouTube visibility. It stores local idempotency state in `tmp/postiz-uploaded.json`. `POSTIZ_LOCAL_BASE_URL` is optional and is added to the draft only when explicitly configured. The API endpoint must use HTTPS; plain HTTP is accepted only on loopback unless `POSTIZ_ALLOW_INSECURE_HTTP=1` is deliberately set after reviewing the network risk. A draft is not proof that upload succeeded: verify the returned post ID and review the item in Postiz before any manual publication.

## Use the web dashboard

The dashboard is now the read-only web face of the current CLI. It follows `generate` and `playlist` runs from the same checkout and displays:

- the run ID, active CLI process, backend, genre, stage, percentage, track number, and elapsed time;
- the current CLI log rather than a hard-coded Stable Audio queue log;
- only validated audio/video files associated with the current run, with HTTP Range playback on phones;
- Postiz status for each finished video: waiting for review, uploading, or private draft created with a returned post ID.

It does not start generation, download models, upload files, cancel work, or publish anything. The CLI remains the control plane; the browser is its status and preview surface.

### Start locally

Terminal 1:

```bash
./music-video web
```

Open `http://127.0.0.1:8765`. Keep the dashboard running and start the actual job in Terminal 2:

```bash
./music-video playlist \
  --backend ace-step \
  --genre lofi \
  --image assets/images/cover.jpg
```

The page refreshes every two seconds. The same machine-readable state remains available at `http://127.0.0.1:8765/status.json` and through `./music-video status --json`.

### Open it privately through Tailscale

Keep the dashboard on loopback and let Tailscale Serve proxy it only inside your tailnet:

```bash
tailscale status
tailscale serve --bg localhost:8765
tailscale serve status
```

Open the HTTPS URL printed by Tailscale on your phone or another tailnet device. Stop sharing when finished:

```bash
tailscale serve off
```

Use [Tailscale Serve](https://tailscale.com/docs/reference/tailscale-cli/serve), not Funnel: Serve is tailnet-only, while Funnel exposes a service to the public internet. Tailnet access still follows your Tailscale users and ACLs. The dashboard exposes generated media, prompts/log output, and Postiz post IDs to allowed tailnet users, so keep access narrow.

For a direct trusted-LAN connection without Tailscale:

```bash
./music-video web --host 0.0.0.0 --port 8765
```

Then open `http://<computer-ip>:8765`. This mode has no application login and must never be forwarded from the router or exposed directly to the internet.

## Advanced: manual queue scripts

The CLI is the recommended entry point. The original scripts remain available for album queues and manual control:

```bash
./scripts/check_dependencies.sh
./scripts/render_diffrhythm2_playlist.sh
./scripts/render_diffrhythm2_albums.sh
./scripts/render_stable_audio3_albums.sh
./scripts/render_one_hour_album.sh
```

## Develop and verify

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q music_video_cli.py scripts tests
for file in music-video scripts/*.sh; do bash -n "$file"; done
git diff --check
```

Before a contribution:

- keep the CLI code-only and dependency-light;
- add or update tests for behavior changes;
- do not add generated media, model files, third-party checkouts, or credentials;
- preserve the PolyForm required notice;
- document third-party license boundaries honestly.

The canonical local/CI gate is:

```bash
./scripts/check.sh
```
