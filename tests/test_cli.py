from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


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
    def test_web_command_starts_dashboard_with_requested_address(self) -> None:
        with mock.patch.object(cli, "run_web", return_value=0) as run_web:
            self.assertEqual(cli.main(["web", "--host", "127.0.0.1", "--port", "9876"]), 0)
        run_web.assert_called_once_with("127.0.0.1", 9876)

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

    def test_playlist_duration_plan_is_varied_and_exactly_one_hour(self) -> None:
        for backend in cli.BACKENDS:
            count = cli.auto_playlist_track_count(backend, cli.DEFAULT_CROSSFADE_SECONDS)
            durations = cli.plan_track_durations(backend, count, cli.DEFAULT_CROSSFADE_SECONDS)
            self.assertGreater(len(set(durations)), 1)
            self.assertLessEqual(max(durations), cli.BACKEND_DURATION_LIMITS[backend])
            timeline = sum(durations) - cli.DEFAULT_CROSSFADE_SECONDS * (count - 1)
            self.assertEqual(timeline, cli.PLAYLIST_SECONDS)

    def test_playlist_rejects_too_few_tracks_for_backend(self) -> None:
        with self.assertRaisesRegex(ValueError, "use at least"):
            cli.plan_track_durations("diffrhythm2", 12, cli.DEFAULT_CROSSFADE_SECONDS)

    def test_playlist_ffmpeg_uses_one_image_without_crop_or_stretch(self) -> None:
        generations = tuple(
            cli.build_generation("ace-step", "lofi", duration, 42 + index)
            for index, duration in enumerate(cli.plan_track_durations("ace-step", 12, 3))
        )
        plan = cli.PlaylistPlan(
            "ace-step", "lofi", ROOT / "assets" / "images" / "cover.jpg",
            ROOT / "output" / "playlist.mp4", 3, generations,
        )
        command = cli.playlist_ffmpeg_command(plan)
        joined = " ".join(command)
        self.assertIn("force_original_aspect_ratio=decrease", joined)
        self.assertIn("pad=1280:720", joined)
        self.assertIn("acrossfade=d=3", joined)
        self.assertEqual(command[command.index("-t") + 1], "3600")
        self.assertEqual(command.count("-loop"), 1)

    def test_playlist_dry_run_needs_no_model_or_image(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "music_video_cli.py"),
                "playlist",
                "--backend",
                "ace-step",
                "--genre",
                "techno",
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Playlist: one-hour instrumental video", result.stdout)
        self.assertIn("Timeline: 3633s audio -> 3600s video", result.stdout)
        self.assertIn("Track 01/12", result.stdout)
        self.assertIn("Render: ffmpeg", result.stdout)


if __name__ == "__main__":
    unittest.main()
