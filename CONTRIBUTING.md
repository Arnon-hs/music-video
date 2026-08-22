# Contributing

Thank you for helping improve Music Video Generator. The project is maintained on a best-effort basis by Vasilii Bereznikov. There is no support SLA; if a thread has no response after 14 days, one polite follow-up is welcome.

## Before writing code

1. Read `README.md`, `SECURITY.md`, and `docs/DEPENDENCIES.md`.
2. Search existing issues and pull requests.
3. Open an issue before a large change, new backend, network integration, or dependency.
4. Keep the proposal within the code-only, local-first scope.

Do not use a public issue for a confidential vulnerability. Follow `SECURITY.md` instead.

## Development workflow

Create a focused branch and keep commits small enough to review. The CLI supports Python 3.11 and 3.13 in CI.

Run the same quality gate used by CI:

```bash
./scripts/check.sh
```

For generation changes, show a bounded dry-run before using model time:

```bash
./music-video doctor --json
./music-video generate --backend <backend> --genre <genre> --duration 60 --dry-run
```

Tests must cover success and relevant failure cases. User-facing changes must update both `README.md` and `README.ru.md`.

## Repository boundaries

Never commit:

- API keys, tokens, passwords, `.env`, or private paths;
- generated audio, video, images, logs, or metadata;
- model weights, checkpoints, virtual environments, or third-party source trees;
- material that you do not have the right to distribute.

New dependencies must be necessary, obtained from the canonical source, recorded in `docs/DEPENDENCIES.md`, and reviewed for code license, weights license, provenance, maintenance, and known vulnerabilities. AI-generated contributions require the same human review, tests, and rights checks as any other contribution.

## Pull requests

A pull request should explain the problem, smallest solution, verification evidence, risks, and rollback. Maintainers may decline changes that expand scope, add unclear rights, or cannot be tested locally.

By submitting a contribution, you confirm that you have the right to provide it and agree that it will be distributed under the repository license. This repository is source-available under PolyForm Noncommercial 1.0.0; it does not claim OSI Open Source status.
