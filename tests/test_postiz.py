from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import postiz_upload_ready_videos as postiz  # noqa: E402


class UploadHandler(BaseHTTPRequestHandler):
    authorization = ""

    def do_POST(self) -> None:  # noqa: N802
        type(self).authorization = self.headers.get("Authorization", "")
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        body = b'{"id":"media-1","path":"/media/1"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class PostizSecurityTests(unittest.TestCase):
    def test_api_key_is_not_passed_in_process_arguments(self) -> None:
        completed = subprocess.CompletedProcess([], 0, stdout='{"id":"media-1","path":"/media/1"}')
        with mock.patch.object(postiz.subprocess, "run", return_value=completed) as run:
            response = postiz.upload_video("top-secret-value", Path("video.mp4"))

        command = run.call_args.args[0]
        self.assertNotIn("top-secret-value", " ".join(command))
        self.assertEqual(run.call_args.kwargs["input"], "Authorization: top-secret-value\n")
        self.assertEqual(response["id"], "media-1")

    @unittest.skipUnless(shutil.which("curl"), "curl is required for Postiz uploads")
    def test_curl_reads_authorization_header_from_stdin(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), UploadHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as directory:
                video = Path(directory) / "video.mp4"
                video.write_bytes(b"video")
                api_root = f"http://127.0.0.1:{server.server_port}"
                with mock.patch.object(postiz, "API_ROOT", api_root):
                    response = postiz.upload_video("integration-secret", video)
            self.assertEqual(UploadHandler.authorization, "integration-secret")
            self.assertEqual(response["id"], "media-1")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_api_root_requires_https_except_explicit_local_use(self) -> None:
        postiz.validate_api_root("https://api.postiz.com/public/v1")
        postiz.validate_api_root("http://127.0.0.1:4007/public/v1")
        postiz.validate_api_root("http://postiz.internal/public/v1", allow_insecure_http=True)
        with self.assertRaises(ValueError):
            postiz.validate_api_root("http://postiz.internal/public/v1")
        with self.assertRaises(ValueError):
            postiz.validate_api_root("file:///tmp/fake-api")

    def test_credentials_reject_header_injection(self) -> None:
        with self.assertRaises(ValueError):
            postiz.validate_credential("POSTIZ_API_KEY", "secret\nX-Evil: injected")

    def test_draft_response_requires_post_id(self) -> None:
        self.assertEqual(postiz.draft_item([{"postId": "post-1"}])["postId"], "post-1")
        with self.assertRaises(RuntimeError):
            postiz.draft_item([])
        with self.assertRaises(RuntimeError):
            postiz.draft_item({"status": "accepted"})

    def test_video_candidates_reject_symlinks_and_completed_items(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "videos"
            root.mkdir()
            ready = root / "ready.mp4"
            ready.write_bytes(b"video")
            completed = root / "completed.mp4"
            completed.write_bytes(b"video")
            outside = Path(directory) / "outside.mp4"
            outside.write_bytes(b"private")
            (root / "escape.mp4").symlink_to(outside)

            with mock.patch.object(postiz, "VIDEO_ROOT", root):
                candidates = postiz.video_candidates({"completed.mp4": {"post_id": "done"}})

        self.assertEqual([(key, path.name) for key, path in candidates], [("ready.mp4", "ready.mp4")])

    def test_invalid_state_has_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state.json"
            state.write_text("not json", encoding="utf-8")
            with mock.patch.object(postiz, "STATE_PATH", state):
                with self.assertRaisesRegex(RuntimeError, "Invalid Postiz state file"):
                    postiz.load_state()

    def test_dry_run_needs_no_credentials_or_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "pending.mp4"
            video.write_bytes(b"video")
            environment = os.environ.copy()
            environment.pop("POSTIZ_API_KEY", None)
            environment.pop("POSTIZ_INTEGRATION_ID", None)
            environment["POSTIZ_VIDEO_ROOT"] = directory
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "postiz_upload_ready_videos.py"), "--dry-run"],
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "pending.mp4")


if __name__ == "__main__":
    unittest.main()
