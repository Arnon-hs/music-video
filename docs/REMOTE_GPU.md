# Run on RunPod or another GPU host

The repository can run on a rented GPU machine today, but it does so as a normal Linux CLI over SSH. It does **not** yet ship a RunPod Serverless worker or a public music-generation HTTP API.

## Choose the simplest remote shape

| Option | Fit for this repository | Trade-off |
|---|---|---|
| [RunPod Pod](https://docs.runpod.io/pods/overview) | Recommended first remote run: full shell, GPU, templates, SSH, persistent `/workspace` storage | You manage the running Pod and stop it when finished |
| [Vast.ai instance](https://docs.vast.ai/guides/instances/overview) | Similar SSH/container workflow with marketplace GPU offers | Host quality, storage, and availability vary by offer |
| Any Ubuntu/NVIDIA GPU VM | Works when it provides SSH, compatible CUDA/PyTorch, enough disk, Python, and FFmpeg | More environment setup and provider-specific operations |
| [RunPod Serverless](https://docs.runpod.io/serverless/overview) | Future product/API mode | Requires a worker image, handler, artifact storage, request validation, and tests that this repository does not yet include |

Prices and GPU availability change frequently. Check the provider console at deployment time instead of copying a price from this guide.

## RunPod Pod: practical first run

### 1. Create the machine

Choose an official PyTorch template, an NVIDIA GPU, SSH access, and persistent storage mounted at `/workspace`. If you are unsure, start with a 24 GB VRAM class for compatibility headroom, then measure a short track before committing to an hour-long playlist. This is an operational starting point, not a guaranteed minimum for every model version.

RunPod distinguishes temporary container storage from persistent volume/network storage. Keep the checkout, model cache, and outputs under `/workspace`: the Pod volume persists across stop/restart until the Pod is deleted, while a network volume has an independent lifecycle. See the official [RunPod storage guide](https://docs.runpod.io/pods/storage/types).

### 2. Connect and audit the environment

Use the SSH command shown in the provider console, then run:

```bash
nvidia-smi
python3 --version
ffmpeg -version
git --version
df -h /workspace
```

If the template does not include FFmpeg or `tmux`, install them with the package manager provided by that image. Do not start model downloads until GPU, Python, CUDA/PyTorch compatibility, and free disk have been checked.

### 3. Clone the code onto persistent storage

```bash
cd /workspace
git clone https://github.com/Arnon-hs/music-video.git
cd music-video

./music-video doctor --json
./music-video genres --json
```

Install **one** selected backend using its official upstream instructions and the expected paths documented in `README.md`. Run `doctor` again; continue only when that backend reports `ready: true`.

### 4. Transfer a reviewed cover image

From your local machine, use the host and SSH port shown by the provider:

```bash
# On the remote GPU machine
mkdir -p /workspace/music-video/assets/images

# On your local machine
scp -P <ssh-port> ./cover.jpg \
  root@<ssh-host>:/workspace/music-video/assets/images/cover.jpg
```

### 5. Preview, then generate

```bash
cd /workspace/music-video

./music-video playlist \
  --backend ace-step \
  --genre lofi \
  --image assets/images/cover.jpg \
  --dry-run
```

For a long run, use a persistent terminal such as `tmux` so a dropped SSH connection does not kill the foreground job:

```bash
tmux new -s music-video

./music-video playlist \
  --backend ace-step \
  --genre lofi \
  --image assets/images/cover.jpg
```

From another SSH session:

```bash
cd /workspace/music-video
./music-video status --json
```

### 6. Verify and copy the result home

```bash
ffprobe -v error \
  -show_entries format=duration:stream=codec_type,width,height \
  -of json output/<video>.mp4
```

Then download it from your local machine:

```bash
scp -P <ssh-port> \
  root@<ssh-host>:/workspace/music-video/output/<video>.mp4 ./
```

Listen to and watch the complete result before Postiz or YouTube. Back up anything important, then stop the GPU compute; confirm separately which provider storage survives stop versus destroy.

## Keep the status page private

Do not expose the unauthenticated status server directly to the internet. Keep it on loopback and use an SSH tunnel:

```bash
# On the remote GPU machine
STATUS_HOST=127.0.0.1 STATUS_PORT=8765 python3 scripts/status_server.py

# On your local machine
ssh -L 8765:127.0.0.1:8765 -p <ssh-port> root@<ssh-host>
```

Open `http://127.0.0.1:8765` locally.

## What an API version would still need

RunPod Serverless executes a custom container and handler. A production adapter for this project still needs:

- a pinned CUDA/Python container image and one model backend;
- request validation for genre, prompt, duration, seed, and image input;
- a queued job model with real progress and cancellation;
- persistent/object storage for large audio and MP4 artifacts;
- authenticated status/result URLs instead of returning a one-hour MP4 inline;
- concurrency, timeout, cost, cleanup, rights, and abuse controls;
- integration tests on the chosen GPU class.

Until that exists, use a Pod/VM through SSH. It is simpler, observable, and runs the same CLI described in the three user guides.
