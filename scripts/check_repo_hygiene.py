#!/usr/bin/env python3
"""Fail when forbidden artifacts or high-confidence secrets are tracked."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_SOURCE_BYTES = 5 * 1024 * 1024
FORBIDDEN_DIRECTORIES = {
    ".models",
    "ace-step-v1",
    "assets",
    "metadata",
    "models",
    "output",
    "tmp",
}
FORBIDDEN_SUFFIXES = {
    ".aac", ".aif", ".aiff", ".avi", ".bin", ".ckpt", ".flac", ".gif",
    ".jpeg", ".jpg", ".key", ".log", ".m4a", ".mkv", ".mov", ".mp3",
    ".mp4", ".ogg", ".onnx", ".p12", ".pem", ".pfx", ".pid", ".png",
    ".pt", ".pth", ".safetensors", ".tif", ".tiff", ".wav", ".webm", ".webp",
}
FORBIDDEN_NAMES = {".DS_Store"}
SECRET_PATTERNS = {
    "AWS access key": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "GitHub token": re.compile(rb"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}"),
    "OpenAI key": re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [Path(item.decode("utf-8")) for item in result.stdout.split(b"\0") if item]


def violations(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for relative in paths:
        if relative == Path(".env") or (relative.name.startswith(".env.") and relative.name != ".env.example"):
            errors.append(f"forbidden environment file: {relative}")
        if relative.name in FORBIDDEN_NAMES:
            errors.append(f"forbidden operating-system file: {relative}")
        if relative.parts and relative.parts[0] in FORBIDDEN_DIRECTORIES:
            errors.append(f"forbidden generated/vendor directory: {relative}")
        if relative.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden binary/media extension: {relative}")

        absolute = ROOT / relative
        if absolute.is_symlink():
            errors.append(f"tracked or untracked symlink is not allowed: {relative}")
            continue
        if not absolute.is_file():
            continue
        size = absolute.stat().st_size
        if size > MAX_SOURCE_BYTES:
            errors.append(f"tracked file exceeds 5 MiB: {relative} ({size} bytes)")
            continue
        content = absolute.read_bytes()
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                errors.append(f"possible {label} in {relative}")
    return errors


def main() -> int:
    errors = violations(tracked_files())
    if errors:
        print("Repository hygiene check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Repository hygiene check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
