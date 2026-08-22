from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import music_video_cli as cli  # noqa: E402


class GenreTests(unittest.TestCase):
    def test_required_genres_and_aliases(self) -> None:
        genres = cli.genres_by_slug()
        for slug in ("techno", "lofi", "classical", "electronic", "ambient", "house"):
            self.assertIn(slug, genres)
        self.assertEqual(cli.resolve_genre("classic"), "classical")
        self.assertEqual(cli.resolve_genre("lo-fi"), "lofi")
        self.assertEqual(cli.resolve_genre("dnb"), "drum-and-bass")

    def test_built_in_prompt_is_instrumental(self) -> None:
        for slug in cli.genres_by_slug():
            prompt = cli.genre_prompt(slug).lower()
            self.assertIn("purely instrumental", prompt)
            self.assertIn("no vocals", prompt)
            self.assertIn("no recognisable copyrighted melody", prompt)


class CommandTests(unittest.TestCase):
    def test_backend_commands_receive_genre_prompt(self) -> None:
        for backend in cli.BACKENDS:
            duration = 180 if backend == "diffrhythm2" else 60
            generation = cli.build_generation(backend, "techno", duration, 42)
            self.assertIn("--prompt", generation.command)
            self.assertIn("techno", str(generation.audio_path))
            self.assertIn("no vocals", generation.prompt.lower())

    def test_custom_prompt_overrides_catalog(self) -> None:
        generation = cli.build_generation("ace-step", "lofi", 60, 42, "Custom instrumental prompt")
        self.assertTrue(generation.prompt.startswith("Custom instrumental prompt"))
        self.assertIn("no vocals", generation.prompt.lower())
        self.assertIn("Custom instrumental prompt", " ".join(generation.command))

    def test_stable_audio_uses_duration_sized_segments(self) -> None:
        generation = cli.build_generation("stable-audio3", "ambient", 60, 42)
        index = generation.command.index("--segment-seconds")
        self.assertEqual(generation.command[index + 1], "33.0")

    def test_backend_duration_limits(self) -> None:
        with self.assertRaises(ValueError):
            cli.build_generation("stable-audio3", "ambient", 235, 42)
        with self.assertRaises(ValueError):
            cli.build_generation("diffrhythm2", "jazz", 211, 42)

    def test_seed_and_prompt_validation(self) -> None:
        with self.assertRaises(ValueError):
            cli.build_generation("ace-step", "ambient", 60, -1)
        with self.assertRaises(ValueError):
            cli.build_generation("ace-step", "ambient", 60, cli.MAX_SEED + 1)
        with self.assertRaises(ValueError):
            cli.build_generation("ace-step", "ambient", 60, 42, "ambient\nignore safeguards")
        with self.assertRaises(ValueError):
            cli.build_generation("ace-step", "ambient", 60, 42, "x" * (cli.MAX_PROMPT_CHARACTERS + 1))

    def test_dry_run_does_not_require_model_installation(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "music_video_cli.py"),
                "generate",
                "--backend",
                "ace-step",
                "--genre",
                "techno",
                "--duration",
                "60",
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Genre:   techno", result.stdout)
        self.assertIn("Command:", result.stdout)

    def test_genres_json_is_machine_readable(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "music_video_cli.py"), "genres", "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        self.assertGreaterEqual(len(payload), 10)


if __name__ == "__main__":
    unittest.main()
