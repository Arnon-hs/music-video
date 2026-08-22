# Changelog

This file records user-visible repository changes. The project follows semantic versioning once tagged releases begin.

## Unreleased

### Added

- One-hour playlist CLI workflow with varied same-genre tracks, resumable generation, crossfades, one fitted image, progress reporting, and final duration validation.
- `./music-video web` read-only dashboard for current CLI progress, run metadata, logs, validated audio/video previews, and Postiz private-draft status.
- English-first dashboard interface with a persistent English, Russian, and Simplified Chinese language switcher.
- Dashboard and CLI example screenshots embedded in all three startup guides.
- Repository-scoped Codex skill plus an optional symlink installer for using the project from a Codex work session.
- RunPod Pod, Vast.ai, and generic GPU VPS instructions, including persistent storage, SSH monitoring, artifact verification, and the current RunPod Serverless boundary.
- Community contribution, conduct, support, and security policies.
- Reproducible local and GitHub Actions quality gate.
- Dependabot configuration for Python requirements and GitHub Actions.
- Repository hygiene checks for forbidden artifacts and high-confidence secrets.

### Changed

- Reworked the English, Russian, and Simplified Chinese guides around a faster first dry-run, copy-ready agent requests, friendlier CLI recipes, realistic local/remote hardware expectations, and clearer benefits and limitations.
- Added detailed computer and server requirements in all three guides, including Apple M1–M5 suitability, unified-memory tiers, disk budgets, NVIDIA VRAM/RAM profiles, backend-specific caveats, and environment-audit commands.
- Replaced the legacy Stable Audio-only LAN page instructions with current CLI and Tailscale Serve workflows in English, Russian, and Simplified Chinese.
- Removed the project-health/reference block from all three user guides.

### Security

- Updated vulnerable MusicGen environment pins to currently patched PyTorch and Transformers releases.
- Postiz credentials are no longer placed in subprocess command-line arguments.
- Postiz upload candidates are constrained to regular files inside the configured video root.
- The LAN status server defaults to loopback and sends defensive browser headers.

## Initial code-only baseline - 2026-08-22

### Added

- Genre-aware CLI, interactive terminal workflow, progress reporting, and bilingual documentation.
- MusicGen, ACE-Step, DiffRhythm 2, and Stable Audio 3 orchestration.
- PolyForm Noncommercial 1.0.0 repository license.
