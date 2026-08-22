from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from scripts import status_server


class StatusServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.music = root / "music"
        self.output = root / "output"
        self.music.mkdir()
        self.output.mkdir()
        self.log_patch = mock.patch.object(status_server.Handler, "log_message", lambda *args: None)
        self.log_patch.start()
        with (
            mock.patch.object(status_server, "MUSIC", self.music),
            mock.patch.object(status_server, "OUTPUT", self.output),
        ):
            self.server = ThreadingHTTPServer(("127.0.0.1", 0), status_server.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"
        self.music_patch = mock.patch.object(status_server, "MUSIC", self.music)
        self.output_patch = mock.patch.object(status_server, "OUTPUT", self.output)
        self.music_patch.start()
        self.output_patch.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.music_patch.stop()
        self.output_patch.stop()
        self.log_patch.stop()
        self.temporary.cleanup()

    def test_root_has_defensive_headers_and_unknown_path_is_404(self) -> None:
        with urllib.request.urlopen(f"{self.base_url}/", timeout=2) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            self.assertEqual(response.headers["X-Frame-Options"], "DENY")
            self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(f"{self.base_url}/unknown", timeout=2)
        self.assertEqual(error.exception.code, 404)
        error.exception.close()

    def test_media_path_cannot_escape_root(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(f"{self.base_url}/media/audio/%2e%2e%2fprivate.mp3", timeout=2)
        self.assertEqual(error.exception.code, 400)
        error.exception.close()

    def test_suffix_range_returns_last_bytes(self) -> None:
        media = self.music / "sample.mp3"
        media.write_bytes(b"0123456789")
        request = urllib.request.Request(
            f"{self.base_url}/media/audio/sample.mp3",
            headers={"Range": "bytes=-4"},
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            self.assertEqual(response.status, 206)
            self.assertEqual(response.headers["Content-Range"], "bytes 6-9/10")
            self.assertEqual(response.read(), b"6789")


if __name__ == "__main__":
    unittest.main()
