from __future__ import annotations

import tempfile
import threading
import unittest
import json
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
            body = response.read().decode("utf-8")
            self.assertIn('<html lang="en">', body)
            self.assertIn('data-lang="en"', body)
            self.assertIn('data-lang="ru"', body)
            self.assertIn('data-lang="zh"', body)
            self.assertIn("music-video-language", body)
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

    def test_status_reports_current_media_and_private_postiz_draft(self) -> None:
        root = Path(self.temporary.name)
        status = root / "status.txt"
        cli_log = root / "cli.log"
        postiz_state = root / "postiz.json"
        postiz_log = root / "postiz.log"
        audio = self.music / "ace-step" / "lofi" / "track.wav"
        video = self.output / "playlist.mp4"
        audio.parent.mkdir(parents=True)
        audio.write_bytes(b"audio")
        video.write_bytes(b"video")
        status.write_text(
            "state=complete\nrun_id=test-run\ncli_pid=999999\n"
            f"audio={audio}\nvideo={video}\n",
            encoding="utf-8",
        )
        cli_log.write_text("generation complete\n", encoding="utf-8")
        postiz_state.write_text(
            json.dumps({"playlist.mp4": {"post_id": "post-123"}}),
            encoding="utf-8",
        )
        postiz_log.write_text("draft created for playlist.mp4: post_id=post-123\n", encoding="utf-8")
        with (
            mock.patch.object(status_server, "STATUS", status),
            mock.patch.object(status_server, "CLI_LOG", cli_log),
            mock.patch.object(status_server, "POSTIZ_STATE", postiz_state),
            mock.patch.object(status_server, "POSTIZ_LOG", postiz_log),
            mock.patch.object(status_server, "probe_duration", return_value=60.0),
        ):
            payload = status_server.read_status()
        self.assertEqual(payload["audio_files"], 1)
        self.assertEqual(payload["video_files"], 1)
        self.assertEqual(payload["publication"]["summary"], "private_drafts_created")
        self.assertEqual(payload["publication"]["items"][0]["post_id"], "post-123")
        self.assertEqual(payload["log_tail"], "generation complete")


if __name__ == "__main__":
    unittest.main()
