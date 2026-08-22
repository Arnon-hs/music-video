#!/usr/bin/env python3
"""Read-only web dashboard for the Music Video Generator CLI."""
from __future__ import annotations

import json
import mimetypes
import os
import re
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "tmp" / "render-progress.txt"
CLI_LOG = ROOT / "tmp" / "music-video-cli.log"
POSTIZ_STATE = ROOT / "tmp" / "postiz-uploaded.json"
POSTIZ_LOG = ROOT / "tmp" / "postiz-upload.log"
OUTPUT = ROOT / "output"
MUSIC = ROOT / "assets" / "music"
HOST = os.environ.get("STATUS_HOST", "127.0.0.1")
PORT = int(os.environ.get("STATUS_PORT", "8765"))
MEDIA_LIMIT = 50
_probe_cache: dict[tuple[str, int, int], float | None] = {}


def read_key_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {
        key: value
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if "=" in line
        for key, value in [line.split("=", 1)]
    }


def tail(path: Path, lines: int = 24) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    clean = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text).replace("\r", "\n")
    return "\n".join(clean.splitlines()[-lines:])


def process_is_running(value: str | None) -> bool:
    try:
        pid = int(value or "")
        os.kill(pid, 0)
        return True
    except (ValueError, OSError):
        return False


def probe_duration(path: Path) -> float | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    key = (str(path), stat.st_mtime_ns, stat.st_size)
    if key in _probe_cache:
        return _probe_cache[key]
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=4, check=False,
        )
        duration = float(result.stdout.strip()) if result.returncode == 0 else None
    except (OSError, ValueError, subprocess.SubprocessError):
        duration = None
    if len(_probe_cache) > 300:
        _probe_cache.clear()
    _probe_cache[key] = duration
    return duration


def resolve_media_path(base: Path, value: str) -> Path | None:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    try:
        resolved = candidate.resolve()
        resolved.relative_to(base.resolve())
    except (OSError, ValueError):
        return None
    return resolved


def collect_media(
    base: Path, suffixes: set[str], status: dict[str, str], keys: tuple[str, ...],
) -> list[dict[str, object]]:
    candidates: set[Path] = set()
    for key in keys:
        for value in status.get(key, "").split("|"):
            if not value:
                continue
            candidate = resolve_media_path(base, value)
            if candidate is not None:
                candidates.add(candidate)

    try:
        started_at = float(status.get("run_started_at", "0"))
    except ValueError:
        started_at = 0
    if started_at and base.exists():
        for candidate in base.rglob("*"):
            try:
                if (
                    candidate.is_file()
                    and candidate.suffix.lower() in suffixes
                    and candidate.stat().st_mtime >= started_at - 2
                ):
                    candidates.add(candidate.resolve())
            except OSError:
                continue

    items: list[dict[str, object]] = []
    for candidate in candidates:
        if not candidate.is_file() or candidate.suffix.lower() not in suffixes:
            continue
        duration = probe_duration(candidate)
        if duration is None or duration <= 1:
            continue
        try:
            name = candidate.relative_to(base.resolve()).as_posix()
            stat = candidate.stat()
        except (OSError, ValueError):
            continue
        items.append({"name": name, "duration": round(duration, 2), "size": stat.st_size, "modified": stat.st_mtime})
    items.sort(key=lambda item: float(item["modified"]), reverse=True)
    return items[:MEDIA_LIMIT]


def read_json_object(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def publication_status(videos: list[dict[str, object]]) -> dict[str, object]:
    state = read_json_object(POSTIZ_STATE)
    log_text = tail(POSTIZ_LOG, 30)
    items = []
    for video in videos:
        name = str(video["name"])
        saved = state.get(name)
        if isinstance(saved, dict) and saved.get("post_id"):
            item_status = "private_draft_created"
            post_id = str(saved["post_id"])
        else:
            uploading = f"uploading {name}" in log_text and f"draft created for {name}" not in log_text
            item_status = "uploading" if uploading else "ready_for_review"
            post_id = ""
        items.append({"name": name, "status": item_status, "post_id": post_id})

    statuses = {item["status"] for item in items}
    if not items:
        summary = "waiting_for_video"
    elif "uploading" in statuses:
        summary = "uploading"
    elif statuses == {"private_draft_created"}:
        summary = "private_drafts_created"
    else:
        summary = "ready_for_review"
    return {"summary": summary, "items": items, "log_tail": log_text}


def read_status() -> dict[str, object]:
    raw = read_key_values(STATUS)
    result: dict[str, object] = dict(raw)
    audio = collect_media(MUSIC, {".wav", ".mp3", ".flac", ".m4a", ".aac"}, raw, ("audio", "music_file", "audio_paths"))
    videos = collect_media(OUTPUT, {".mp4", ".mov", ".m4v"}, raw, ("video",))
    result["audio"] = audio
    result["videos"] = videos
    result["audio_files"] = len(audio)
    result["video_files"] = len(videos)
    terminal_states = {"complete", "blocked", "cancelled", "music_complete"}
    result["run_active"] = raw.get("state") not in terminal_states and process_is_running(raw.get("cli_pid"))
    result["log_tail"] = tail(CLI_LOG)
    result["publication"] = publication_status(videos)
    return result


PAGE = r"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Music Video Generator</title>
<style>
:root{color-scheme:dark;--bg:#0b0e14;--panel:#141a24;--line:#273244;--text:#edf3fb;--muted:#91a0b5;--green:#45d49b;--amber:#f7bd5b;--red:#ff6f91;--blue:#75a7ff}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 80% 0,#17243b 0,transparent 32%),var(--bg);color:var(--text);font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:1120px;margin:auto;padding:28px 16px 60px}h1{font-size:clamp(26px,5vw,42px);line-height:1.05;margin:0}.sub{color:var(--muted);margin-top:10px}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px;margin-top:18px}.card{grid-column:span 6;background:var(--panel);background:color-mix(in srgb,var(--panel) 94%,transparent);border:1px solid var(--line);border-radius:16px;padding:18px;min-width:0}.wide{grid-column:1/-1}.third{grid-column:span 4}.row{display:flex;justify-content:space-between;gap:16px;margin:8px 0}.value{text-align:right;font-weight:650;overflow-wrap:anywhere}.muted{color:var(--muted)}.pill{display:inline-flex;border:1px solid var(--line);border-radius:99px;padding:5px 9px;margin-top:12px}.bar{height:16px;background:#263043;border-radius:99px;overflow:hidden;margin:16px 0 8px}.fill{height:100%;background:linear-gradient(90deg,var(--blue),var(--green));width:0;transition:width .4s}.percent{font-size:32px;font-weight:760}.ok{color:var(--green)}.warn{color:var(--amber)}.bad{color:var(--red)}code{color:#c9b8ff;word-break:break-all}.media{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}.item{border:1px solid var(--line);border-radius:12px;padding:12px;min-width:0}audio,video{width:100%;margin-top:9px;border-radius:9px;background:#000}pre{max-height:340px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;background:#0a0d12;padding:14px;border-radius:12px;margin-bottom:0}.empty{padding:18px 0;color:var(--muted)}
@media(max-width:760px){.card,.third{grid-column:1/-1}main{padding-top:20px}.row{align-items:flex-start}}
</style></head><body><main>
<h1>Music Video Generator</h1><div class="sub">Web dashboard для <code>./music-video</code> · обновление каждые 2 секунды</div><div id="connection" class="pill warn">подключение…</div>
<div class="grid">
<section class="card wide"><div class="row"><span>Состояние</span><span id="state" class="value">—</span></div><div class="row"><span>Этап CLI</span><span id="stage" class="value">—</span></div><div class="bar"><div id="fill" class="fill"></div></div><div class="row"><span id="detail" class="muted">—</span><span id="percent" class="percent">0%</span></div></section>
<section class="card third"><div class="row"><span>Режим</span><span id="mode" class="value">—</span></div><div class="row"><span>Backend</span><span id="backend" class="value">—</span></div><div class="row"><span>Жанр</span><span id="genre" class="value">—</span></div></section>
<section class="card third"><div class="row"><span>Run ID</span><span id="runId" class="value">—</span></div><div class="row"><span>CLI процесс</span><span id="active" class="value">—</span></div><div class="row"><span>Прошло</span><span id="elapsed" class="value">—</span></div></section>
<section class="card third"><div class="row"><span>Аудио готово</span><span id="audioCount" class="value">0</span></div><div class="row"><span>Видео готово</span><span id="videoCount" class="value">0</span></div><div class="row"><span>Обновлено</span><span id="updated" class="value">—</span></div></section>
<section class="card wide"><h2>Публикация</h2><div class="row"><span>Postiz / YouTube</span><span id="publish" class="value">—</span></div><div id="publishItems" class="media"></div></section>
<section class="card wide"><h2>Предпросмотр аудио</h2><div id="audio" class="media"><div class="empty">готовых файлов пока нет</div></div></section>
<section class="card wide"><h2>Предпросмотр видео</h2><div id="videos" class="media"><div class="empty">готовых файлов пока нет</div></div></section>
<section class="card"><h2>CLI log</h2><pre id="log" class="muted">лог пока пуст</pre></section>
<section class="card"><h2>Postiz log</h2><pre id="postizLog" class="muted">лог пока пуст</pre></section>
</div></main><script>
const q=s=>document.querySelector(s), esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels={starting:'запуск',loading_model:'загрузка модели',generating_music:'генерация аудио',generating_playlist_music:'генерация треков',saving_audio:'сохранение аудио',assembling_audio:'сведение аудио',music_complete:'аудио готово',rendering_playlist_video:'рендер часового видео',complete:'готово',cancelled:'отменено',blocked:'ошибка'};
const pubLabels={waiting_for_video:'ожидание готового видео',ready_for_review:'видео готово — нужна проверка перед Postiz',uploading:'загрузка в Postiz',private_drafts_created:'приватный draft создан',private_draft_created:'приватный draft создан'};
const fmtTime=v=>{if(!v)return'—';const s=Math.max(0,Math.floor(Date.now()/1000-Number(v)));return`${Math.floor(s/3600)}ч ${Math.floor(s%3600/60)}м ${s%60}с`};
const mediaCard=(item,type)=>`<div class="item"><code>${esc(item.name)}</code><div class="muted">${Math.round(item.duration)} сек · ${(item.size/1048576).toFixed(1)} MB</div><${type} controls preload="metadata" src="/media/${type==='audio'?'audio':'video'}/${encodeURIComponent(item.name)}"></${type}></div>`;
function render(d){
 const state=d.state||'idle', p=Math.max(0,Math.min(100,Number(d.music_percent??d.percent??(state==='complete'?100:0))));
 q('#connection').textContent='dashboard online';q('#connection').className='pill ok';q('#state').textContent=labels[state]||state;
 q('#state').className='value '+(state==='blocked'?'bad':state==='complete'?'ok':'warn');q('#stage').textContent=d.stage||labels[state]||'ожидание CLI';
 q('#fill').style.width=p+'%';q('#percent').textContent=Math.round(p)+'%';q('#detail').textContent=d.playlist_total?`трек ${d.playlist_track||d.playlist_completed||0}/${d.playlist_total} · ${d.music_step||''}`:(d.music_step||d.error||'');
 q('#mode').textContent=d.mode||'—';q('#backend').textContent=d.backend||'—';q('#genre').textContent=d.genre||'—';q('#runId').textContent=d.run_id||'—';
 q('#active').textContent=d.run_active?'работает':(['complete','blocked','cancelled','music_complete'].includes(state)?'завершён':'не найден');q('#active').className='value '+(d.run_active?'ok':'muted');q('#elapsed').textContent=fmtTime(d.run_started_at);
 q('#audioCount').textContent=d.audio_files||0;q('#videoCount').textContent=d.video_files||0;q('#updated').textContent=new Date().toLocaleTimeString();
 q('#audio').innerHTML=d.audio?.length?d.audio.map(x=>mediaCard(x,'audio')).join(''):'<div class="empty">готовых файлов текущего запуска пока нет</div>';
 q('#videos').innerHTML=d.videos?.length?d.videos.map(x=>mediaCard(x,'video')).join(''):'<div class="empty">готовых файлов текущего запуска пока нет</div>';
 const pub=d.publication||{};q('#publish').textContent=pubLabels[pub.summary]||pub.summary||'—';q('#publish').className='value '+(pub.summary==='private_drafts_created'?'ok':pub.summary==='uploading'?'warn':'muted');
 q('#publishItems').innerHTML=pub.items?.length?pub.items.map(x=>`<div class="item"><code>${esc(x.name)}</code><div class="muted">${pubLabels[x.status]||x.status}${x.post_id?` · post ID ${esc(x.post_id)}`:''}</div></div>`).join(''):'<div class="empty">публиковать пока нечего</div>';
 q('#log').textContent=d.log_tail||'лог пока пуст';q('#postizLog').textContent=pub.log_tail||'лог пока пуст';
}
async function refresh(){try{const r=await fetch('/status.json?'+Date.now());if(!r.ok)throw Error(r.status);render(await r.json())}catch(e){q('#connection').textContent='нет связи';q('#connection').className='pill bad'}}
refresh();setInterval(refresh,2000);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
            "media-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
        )
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        super().end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path.startswith("/media/audio/") or parsed.path.startswith("/media/video/"):
            self.serve_media(parsed.path)
            return
        if parsed.path == "/status.json":
            body = json.dumps(read_status(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
        elif parsed.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        elif parsed.path == "/":
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        else:
            self.send_error(404, "Not found")
            return
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_media(self, path: str) -> None:
        prefix, base = ("/media/audio/", MUSIC) if path.startswith("/media/audio/") else ("/media/video/", OUTPUT)
        name = unquote(path[len(prefix):])
        if not name:
            self.send_error(400, "Invalid media name")
            return
        target = (base / name).resolve()
        try:
            target.relative_to(base.resolve())
        except ValueError:
            self.send_error(400, "Invalid media path")
            return
        if not target.is_file():
            self.send_error(404, "Media not found")
            return
        size = target.stat().st_size
        start, end = 0, size - 1
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            try:
                value = range_header[6:].split(",", 1)[0]
                first, last = value.split("-", 1)
                if not first:
                    suffix_length = int(last)
                    if suffix_length <= 0:
                        raise ValueError
                    start = max(0, size - suffix_length)
                else:
                    start = int(first)
                    end = int(last) if last else size - 1
                end = min(end, size - 1)
                if start < 0 or end < 0 or start >= size or start > end:
                    raise ValueError
            except ValueError:
                self.send_error(416, "Invalid range")
                return
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(str(target))[0] or "application/octet-stream")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        with target.open("rb") as stream:
            stream.seek(start)
            remaining = end - start + 1
            while remaining:
                chunk = stream.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def log_message(self, format: str, *args: object) -> None:
        print(format % args, flush=True)


def serve(host: str = HOST, port: int = PORT) -> None:
    print(f"Music Video Generator dashboard: http://{host}:{port}", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    serve()
