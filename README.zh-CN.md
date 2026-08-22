# Music Video Generator

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

这是一个仅包含代码的本地工具集，用于生成纯器乐音乐、跟踪生成进度、制作音乐视频、在局域网中预览结果，以及通过 Postiz 创建私密的 YouTube 草稿。

Git 仓库只保存编排代码和安全配置。生成的音频/视频、图片、模型权重、第三方源码目录、虚拟环境、日志、临时文件和真实凭据均不会提交到 Git。

## 功能

- 交互式终端向导：不带参数运行 `./music-video`；
- 面向用户、LLM 和 coding agent 的 CLI；
- 12 种无声乐流派：techno、lo-fi、classical、electronic、ambient、house、synthwave、jazz、drum & bass、cinematic、chillout 和 instrumental hip-hop；
- MusicGen、ACE-Step、DiffRhythm 2 和 Stable Audio 3 适配器；
- 在终端中显示当前阶段、可信进度数据存在时的百分比、已用时间和后端输出；
- 可选：使用本地图片合成 MP4；
- `genres`、`doctor` 和 `status` 命令支持 JSON 输出；
- 通过 Postiz 创建私密草稿；
- CLI 不会在后台自动下载模型或媒体文件。

## 许可证

Copyright 2026 Vasilii Bereznikov.

本项目采用 [PolyForm Noncommercial License 1.0.0](LICENSE)。在保留许可证和必要版权声明的前提下，您可以为许可证允许的非商业目的使用、研究、修改和向社区分享代码。

这是一个面向社区的 source-available 许可证，但不是 OSI 认可的开源许可证。项目有意不采用 Apache-2.0，因为 Apache-2.0 允许商业使用。商业使用本仓库需要另行取得所有者许可。

第三方模型代码、权重、服务、媒体和生成结果分别受其自身许可证和权利约束。模型代码采用宽松许可证，并不代表模型权重或生成音乐自动获得发布许可。

## 项目健康状况

- [贡献指南](CONTRIBUTING.md)
- [安全策略](SECURITY.md)
- [行为准则](CODE_OF_CONDUCT.md)
- [支持](SUPPORT.md)
- [变更日志](CHANGELOG.md)
- [依赖项和供应链清单](docs/DEPENDENCIES.md)

本项目的工程基线参考了 [OpenSSF 安全开发指南](https://best.openssf.org/Concise-Guide-for-Developing-More-Secure-Software)、面向维护者的 [Open Source Guides](https://opensource.guide/best-practices/)、[Linux Foundation 开源最佳实践培训](https://training.linuxfoundation.org/open-source-best-practice/) 以及 [Kristories / awesome-guidelines](https://github.com/Kristories/awesome-guidelines) 汇总的语言和风格指南。采用这些实践并不代表使用 PolyForm 许可证的本项目是 OSI Open Source。

## 快速开始

```bash
git clone git@github.com:Arnon-hs/music-video.git
cd music-video

./music-video doctor
./music-video genres
./music-video
```

交互模式会引导您：

1. 选择音乐流派；
2. 选择已安装的 backend；
3. 设置时长；
4. 可选：使用 `assets/images` 中的图片制作视频；
5. 可选：强制使用 CPU；
6. 查看生成进度，直到终端显示最终文件路径。

## 使用 CLI

```bash
./music-video --help
./music-video genres
./music-video genres --json
./music-video doctor
./music-video doctor --json
./music-video status
./music-video status --json
```

使用 ACE-Step 生成 techno：

```bash
./music-video generate \
  --backend ace-step \
  --genre techno \
  --duration 60
```

生成 classical 音乐并制作视频：

```bash
./music-video generate \
  --backend stable-audio3 \
  --genre classical \
  --duration 120 \
  --video
```

仅验证命令，不启动模型：

```bash
./music-video generate \
  --backend diffrhythm2 \
  --genre drum-and-bass \
  --duration 180 \
  --dry-run
```

使用 LLM 提供的自定义 prompt：

```bash
./music-video generate \
  --backend ace-step \
  --genre electronic \
  --duration 90 \
  --prompt "Instrumental modular electronic music, 118 BPM, evolving polyrhythms, deep bass, no vocals, no speech, original melody"
```

主要参数：

| 参数 | 用途 |
|---|---|
| `--backend` | `musicgen`、`ace-step`、`diffrhythm2` 或 `stable-audio3` |
| `--genre` | 流派 slug；支持别名 `classic`、`lo-fi`、`dnb` |
| `--duration` | 以秒为单位的时长，并校验 backend 的限制 |
| `--seed` | 用于可复现生成的 seed |
| `--prompt` | 最多 2000 个字符且不含控制字符的风格描述；系统仍会追加禁止人声的限制 |
| `--video` | 音乐生成后制作 MP4 |
| `--force-cpu` | 在 backend 支持时禁用 GPU/MPS |
| `--allow-downloads` | 明确允许 DiffRhythm/Stable Audio 下载缺失的模型 |
| `--dry-run` | 显示 prompt、路径和命令，但不启动模型 |

流派配置位于 [`config/genres.json`](config/genres.json)。每个内置或自定义 prompt 都会追加以下限制：禁止人声、讲话、说唱、合唱、吟唱、voice samples、模仿艺术家以及可识别的受版权保护旋律。

## 进度和文件

CLI 会显示当前阶段、可信数据存在时的百分比、当前 segment/diffusion step、已用时间、日志行和最终路径。

在另一个终端或 agent 中查看：

```bash
watch -n 2 './music-video status'
./music-video status --json
```

以下本地目录会自动创建，并被 Git 忽略：

```text
assets/images/                  本地图片
assets/music/<backend>/<genre>/ 生成的音频
output/                         最终 MP4
tmp/                            进度、日志和临时渲染文件
metadata/                       本地报告和素材许可证
models/ 和 .models/             模型权重和第三方仓库
```

## Backend 和 LLM

CLI 只负责调度本地模型。本仓库不包含模型代码和权重。

### [facebookresearch / AudioCraft (MusicGen)](https://github.com/facebookresearch/audiocraft)

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-musicgen.txt

./music-video generate --backend musicgen --genre lofi --duration 60
```

`facebook/musicgen-small` 权重采用 CC-BY-NC 4.0 许可证，因此生成结果始终标记为 `NON_COMMERCIAL_DEMO`。首次下载必须手动输入 `DOWNLOAD_MODEL`。

MusicGen 的直接依赖项已固定版本，以便 review 和 security monitoring；transitive dependencies 的解析结果仍可能发生变化。修改 requirements 后，请重新创建 venv，不要继续使用旧环境。

### [ACE-Step / ACE-Step-1.5](https://github.com/ace-step/ACE-Step-1.5)

当前适配器需要以下路径：

```text
ace-step-v1/.venv/bin/python
models/ace-step/
```

```bash
ACE_DEVICE=cpu ./music-video generate --backend ace-step --genre techno --duration 60
```

新版 ACE-Step 可能需要更新适配器。运行前请执行 `./music-video doctor`。

### [ASLP-lab / DiffRhythm](https://github.com/ASLP-lab/DiffRhythm)

### [ASLP-lab / DiffRhythm2](https://github.com/ASLP-lab/DiffRhythm2)

适配器需要 DiffRhythm 2：

```text
.models/DiffRhythm2/inference.py
.venv-diffrhythm2/bin/python
```

```bash
./music-video generate --backend diffrhythm2 --genre jazz --duration 180
```

Instrumental mode 通过 prompt 和 `[inst]` 结构设置。生成后仍需试听：文本限制无法保证完全没有类似人声的声音。

默认情况下，CLI 会为此 backend 启用 Hugging Face offline mode。只有在检查模型和预期下载大小后，才应添加 `--allow-downloads`。

### [Stability-AI / stable-audio-3](https://github.com/Stability-AI/stable-audio-3)

### [Stability-AI / stable-audio-tools](https://github.com/Stability-AI/stable-audio-tools)

```text
.venv-stable-audio3/bin/python
```

```bash
./music-video generate --backend stable-audio3 --genre ambient --duration 120
```

当前适配器单次运行最长 234 秒；更长的专辑由现有 queue 脚本组合生成。

默认情况下，CLI 会为此 backend 启用 Hugging Face offline mode。只有在检查模型和预期下载大小后，才应添加 `--allow-downloads`。

## 与 LLM 配合使用

LLM 应只准备 style prompt，不应生成可执行代码或 credentials。建议使用以下约定：

```text
Create one concise English music-generation prompt.
The output must be purely instrumental: no vocals, speech, rap, choir,
chants, vocal chops, or voice samples. Do not imitate artists or quote
recognisable melodies. Include genre, BPM range, instrumentation, mood,
rhythm, arrangement, and mix characteristics.
```

在执行耗时任务前，先检查 prompt 和命令：

```bash
./music-video generate --backend ace-step --genre electronic \
  --prompt "<LLM prompt>" --duration 60 --dry-run
```

## 与 coding agent 配合使用

Codex、Claude Code 或其他本地 agent 的安全操作顺序：

1. 执行 `./music-video doctor --json`；
2. 执行 `./music-video genres --json`；
3. 选择 `ready: true` 的 backend；
4. 使用 `--dry-run` 展示命令；
5. 在下载模型或媒体前取得用户确认；
6. 只启动一次有明确限制的生成任务；
7. 读取真实的 `./music-video status --json`；
8. 使用 `ffprobe` 并通过试听验证结果；
9. 不提交 `.env`、媒体、模型、checkpoint 和日志；
10. 未经用户明确要求，不上传或发布任何内容。

可直接交给 agent 的请求：

```text
在此仓库中运行 ./music-video doctor --json 和 genres --json。
使用 <backend> 准备一段 60 秒、<genre> 流派的纯器乐音乐。
先展示 dry-run。未经我的明确确认，不要下载模型或媒体，
不要上传或发布任何内容。显示真实的 status --json，并验证最终文件。
```

## 图片和视频

将您拥有使用权的图片放入 `assets/images`，或先使用 Pexels 搜索：

```bash
export PEXELS_API_KEY='your_key'
.venv/bin/python scripts/search_pexels_images.py
```

脚本会先显示候选图片，并且只有在准确输入 `DOWNLOAD` 后才会下载。Pexels 素材的使用权需要单独核实。

```bash
./music-video generate --backend ace-step --genre synthwave --duration 90 --video
```

## Postiz 和私密 YouTube 草稿

个人配置只能从环境变量读取。代码中不再包含 integration ID 或 API key。

```bash
cp .env.example .env
```

填写本地 `.env`：

```dotenv
POSTIZ_API_KEY=your_real_key
POSTIZ_INTEGRATION_ID=your_youtube_integration_id
POSTIZ_API_ROOT=https://api.postiz.com/public/v1
POSTIZ_VIDEO_ROOT=output
# 可选；如果此服务器未提供 POSTIZ_VIDEO_ROOT，请留空。
POSTIZ_LOCAL_BASE_URL=
```

```bash
set -a
source .env
set +a

python3 scripts/postiz_upload_ready_videos.py --dry-run
python3 scripts/postiz_upload_ready_videos.py
python3 scripts/postiz_upload_ready_videos.py --watch --interval 30
```

`--dry-run` 无需 credentials，也不会请求 Postiz，只会显示待处理的视频。真实运行会创建 top-level draft 并请求 YouTube 私密可见性，幂等状态保存在 `tmp/postiz-uploaded.json`。`POSTIZ_LOCAL_BASE_URL` 是可选项，只有明确配置后才会写入草稿。API 必须使用 HTTPS；仅在 loopback 场景中可使用 HTTP，或者在评估网络风险后明确设置 `POSTIZ_ALLOW_INSECURE_HTTP=1`。收到响应后，必须检查 post ID 和 Postiz 中的实际草稿，再手动发布。

## 局域网状态页面

服务器默认只监听 `127.0.0.1`。如需在可信局域网中明确访问现有 Stable Audio 队列：

```bash
STATUS_HOST=0.0.0.0 STATUS_PORT=8765 python3 scripts/status_server.py
```

在同一网络中打开 `http://<计算机IP>:8765`。没有单独的身份验证时，请勿将此服务器暴露到互联网。

## 底层脚本

CLI 是主要入口。原有队列命令仍然可用：

```bash
./scripts/check_dependencies.sh
./scripts/render_diffrhythm2_playlist.sh
./scripts/render_diffrhythm2_albums.sh
./scripts/render_stable_audio3_albums.sh
./scripts/render_one_hour_album.sh
```

## 开发和验证

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q music_video_cli.py scripts tests
for file in music-video scripts/*.sh; do bash -n "$file"; done
git diff --check
```

向社区贡献时：

- 保持 CLI 仅包含代码，并避免不必要的依赖；
- 行为发生变化时添加测试；
- 不添加媒体、模型、第三方 checkout 和 credentials；
- 保留 PolyForm 许可证要求的 Required Notice；
- 如实说明第三方模型和生成结果的许可证边界。

本地和 CI 使用同一条命令执行检查：

```bash
./scripts/check.sh
```
