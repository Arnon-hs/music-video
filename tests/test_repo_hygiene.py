from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import check_repo_hygiene as hygiene


class RepositoryHygieneTests(unittest.TestCase):
    def test_forbidden_media_and_secret_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "song.mp3").write_bytes(b"media")
            (root / "token.txt").write_text("ghp_" + "a" * 32, encoding="utf-8")
            with mock.patch.object(hygiene, "ROOT", root):
                errors = hygiene.violations([Path("song.mp3"), Path("token.txt")])
        self.assertTrue(any("forbidden binary/media extension" in error for error in errors))
        self.assertTrue(any("possible GitHub token" in error for error in errors))

    def test_normal_source_file_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "module.py").write_text("print('hello')\n", encoding="utf-8")
            with mock.patch.object(hygiene, "ROOT", root):
                errors = hygiene.violations([Path("module.py")])
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
