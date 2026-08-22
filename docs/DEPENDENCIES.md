# Dependencies and supply-chain inventory

This repository contains orchestration code, not vendored model implementations or weights. Review this inventory before changing a dependency or preparing a release.

| Component | Source | Purpose | Boundary |
|---|---|---|---|
| Python 3.11 or 3.13 | python.org / system package manager | CLI, adapters, tests | Core CLI uses the standard library; MusicGen setup uses Python 3.11 |
| FFmpeg and ffprobe | ffmpeg.org / system package manager | Audio/video assembly and validation | External executable; not installed by this repository |
| MusicGen Python packages | `requirements-musicgen.txt` | Optional MusicGen backend | Direct versions pinned; transitive resolution, code, and weights require separate review |
| AudioCraft / MusicGen | facebookresearch/audioCraft | Optional generation backend | Third-party source and weights are excluded from Git |
| ACE-Step | ACE-Step/ACE-Step-1.5 | Optional generation backend | Local checkout and checkpoints are excluded from Git |
| DiffRhythm 2 | ASLP-lab/DiffRhythm2 | Optional generation backend | Local checkout and checkpoints are excluded from Git |
| Stable Audio 3 | Stability-AI/stable-audio-3 | Optional generation backend | Local environment and weights are excluded from Git |
| Pexels API | pexels.com | Optional reviewed image discovery | Requires a local API key; media rights need human review |
| Postiz API | postiz.com or self-hosted instance | Optional private draft creation | Requires local credentials; no automatic publication |

## Update policy

Before merging an update:

1. verify the canonical project and package name to reduce typosquatting risk;
2. review changelog, maintenance state, license, transitive dependencies, and known vulnerabilities;
3. test on a bounded sample without downloading unreviewed models or media;
4. update both user guides when setup or behavior changes;
5. record model code, weights, data/provenance, and output-rights conclusions separately.

Dependabot proposes updates for declared Python requirements and pinned GitHub Actions. It does not validate optional model weights or local third-party checkouts.

The current requirements file pins direct dependencies but is not a hash-locked, cross-platform lockfile. Add a reviewed lock and hashes before publishing a reproducible release artifact.

## Release gate

Before the first public tagged release, create a machine-readable SBOM, publish checksums, sign the release artifact or provenance attestation, enable GitHub vulnerability alerts and secret scanning, protect `main`, require CI review, and run OpenSSF Scorecard. Do not claim an OpenSSF Best Practices badge while the project is licensed as non-OSI source-available software unless the badge program confirms eligibility.
