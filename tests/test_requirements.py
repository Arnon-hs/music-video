from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RequirementsTests(unittest.TestCase):
    def test_musicgen_dependencies_are_exactly_pinned(self) -> None:
        requirements = [
            line.strip()
            for line in (ROOT / "requirements-musicgen.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertGreater(len(requirements), 0)
        self.assertTrue(all(line.count("==") == 1 for line in requirements), requirements)
        names = [line.split("==", 1)[0].lower() for line in requirements]
        self.assertEqual(len(names), len(set(names)), "duplicate dependency")


if __name__ == "__main__":
    unittest.main()
