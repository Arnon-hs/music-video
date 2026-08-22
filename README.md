# Music Video Generator

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

Local, code-only toolkit for generating instrumental music, tracking generation progress, assembling music videos, previewing results on a LAN, and creating private YouTube drafts through Postiz.

The repository contains orchestration code and safe configuration only. Generated audio/video, images, model weights, third-party source trees, virtual environments, logs, temporary files, and real credentials are excluded from Git.

## Features

- interactive terminal wizard: run `./music-video` with no arguments;
- scriptable CLI for people, LLMs, and coding agents;
- 12 voice-free genres, including techno, lo-fi, classical, electronic, ambient, house, synthwave, jazz, drum & bass, cinematic, chillout, and instrumental hip-hop;
- MusicGen, ACE-Step, DiffRhythm 2, and Stable Audio 3 adapters;
- live stage, percentage when available, elapsed time, and backend output in the terminal;
- optional MP4 assembly from local images;
- one-hour playlist videos with varied same-genre tracks, crossfades, and one fitted image;
- machine-readable `genres`, `doctor`, and `status` output;
- private Postiz/YouTube draft workflow;
- no model or media downloads without the underlying tool's explicit action.

## License

Copyright 2026 Vasilii Bereznikov.

This project uses the [PolyForm Noncommercial License 1.0.0](LICENSE). You may use, study, modify, and share the code for permitted noncommercial purposes, provided that the license and required notice remain with distributed copies.

This is a source-available community license, not an OSI-approved open-source license. Apache-2.0 was intentionally not used because it permits commercial use. Commercial use is not granted by this repository license and requires separate permission from the owner.

Third-party model code, weights, services, media, and generated outputs remain subject to their own licenses and rights. A permissive model-code license does not automatically clear model weights or generated music for publication.

## Project health

- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Support](SUPPORT.md)
- [Changelog](CHANGELOG.md)
- [Dependencies and supply-chain inventory](docs/DEPENDENCIES.md)

The repository engineering baseline draws from [OpenSSF secure development guidance](https://best.openssf.org/Concise-Guide-for-Developing-More-Secure-Software), [Open Source Guides for maintainers](https://opensource.guide/best-practices/), [Linux Foundation open-source practice training](https://training.linuxfoundation.org/open-source-best-practice/), and the language/style references collected by [Kristories / awesome-guidelines](https://github.com/Kristories/awesome-guidelines). These practices are adopted without claiming that the PolyForm-licensed project is OSI Open Source.

## Quick start

```bash
git clone git@github.com:Arnon-hs/music-video.git
cd music-video

./music-video doctor
./music-video genres
./music-video
```

The no-argument command starts a small interactive UI:

1. choose a genre;
2. choose an installed backend;
3. choose duration;
4. optionally build a video from `assets/images`;
5. optionally force CPU mode;
6. watch progress until the final path is printed.

## CLI reference

```bash
./music-video --help
./music-video genres
./music-video genres --json
./music-video doctor
./music-video doctor --json
./music-video status
./music-video status --json
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

## Progress and outputs

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

## Backends and LLMs

The CLI is an orchestrator. Model code and weights are installed locally and are never committed to this repository.

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

## Working with an LLM

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

## Working with a coding agent

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

Copy-ready agent request:

```text
In this repository, run ./music-video doctor --json and genres --json.
Prepare a 60-second instrumental <genre> generation using <backend>.
Show the dry-run command first. Do not download models/media, upload files,
or publish anything without my explicit approval. During execution, report
the exact status from ./music-video status --json and verify the output.
```

## Images and video

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

## Postiz and private YouTube drafts

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

## LAN status page

The existing Stable Audio album queue binds to `127.0.0.1` by default. To expose its detailed status page to a trusted LAN explicitly:

```bash
STATUS_HOST=0.0.0.0 STATUS_PORT=8765 python3 scripts/status_server.py
```

Open `http://<computer-ip>:8765` from the same local network. Do not expose this unauthenticated development server directly to the internet.

## Low-level scripts

The CLI is the recommended entry point. The original scripts remain available for album queues and manual control:

```bash
./scripts/check_dependencies.sh
./scripts/render_diffrhythm2_playlist.sh
./scripts/render_diffrhythm2_albums.sh
./scripts/render_stable_audio3_albums.sh
./scripts/render_one_hour_album.sh
```

## Development and verification

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
