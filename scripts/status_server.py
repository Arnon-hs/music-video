#!/usr/bin/env python3
"""LAN-only mobile status page for Stable Audio 3 album rendering."""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse
import mimetypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "tmp" / "render-progress.txt"
LOG = ROOT / "tmp" / "stable-audio3-albums-v4.log"
OUTPUT = ROOT / "output" / "stable-audio3-albums-v4"
MUSIC = ROOT / "assets" / "music" / "stable-audio3-albums-v4"
HOST = os.environ.get("STATUS_HOST", "127.0.0.1")
PORT = int(os.environ.get("STATUS_PORT", "8765"))


def read_status() -> dict[str, str]:
    result: dict[str, str] = {}
    if STATUS.exists():
        for line in STATUS.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                result[key] = value
    # Backfill timers for a run started before timestamp fields were added.
    if LOG.exists() and "queue_started_at" not in result:
        lines = LOG.read_text(encoding="utf-8", errors="replace").splitlines()
        matches = [re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line) for line in lines]
        match = next((item for item in matches if item), None)
        if match:
            try:
                result["queue_started_at"] = str(int(datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S").timestamp()))
                result["music_started_at"] = result["queue_started_at"]
            except ValueError:
                pass
    if result.get("state") == "generating_music" and LOG.exists():
        # tqdm writes carriage-return progress into the log. Expose the last
        # observed diffusion block for the active model without touching the
        # long-running generator.
        text = LOG.read_text(encoding="utf-8", errors="replace")
        current_log = text.rsplit("START ", 1)[-1]
        step_limit = 8 if "Stable Audio 3" in result.get("model", "") else 90
        blocks = re.findall(rf"(\d+)\s*/\s*{step_limit}", current_log)
        if blocks:
            block = int(blocks[-1])
            total = max(1, int(result.get("track_count", result.get("tracks_per_album", "12"))))
            track = max(1, int(result.get("music_track", "1")))
            result["music_step"] = f"{block}/{step_limit}"
            if "Stable Audio 3" in result.get("model", ""):
                generated_segments = re.findall(r"generated segment (\d+)/2", current_log)
                segment = min(2, int(generated_segments[-1]) + 1) if generated_segments else 1
                result["music_segment"] = f"{segment}/2"
                result["music_percent"] = str(min(99, int(((track - 1) * 2 + segment - 1 + block / step_limit) * 100 / (total * 2))))
            else:
                result["music_percent"] = str(min(99, int(((track - 1) * step_limit + block) * 100 / (total * step_limit))))
    if LOG.exists():
        clean_log = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", LOG.read_text(encoding="utf-8", errors="replace"))
        log_lines = clean_log.replace("\r", "\n").splitlines()
        # These are expected optional-backend/deprecation notices on Apple
        # Silicon, not pipeline failures. The raw log remains on disk.
        log_lines = [
            line for line in log_lines
            if not re.search(r"flash_attn|FutureWarning|weight_norm.*deprecated", line, re.IGNORECASE)
        ]
        result["log_tail"] = "\n".join(log_lines[-10:])
    files = []
    if OUTPUT.exists():
        for candidate in sorted(OUTPUT.rglob("*.mp4")):
            # Do not expose a half-written MP4 while ffmpeg is still encoding.
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(candidate)],
                capture_output=True, text=True, timeout=3,
            )
            try:
                if float(probe.stdout.strip()) >= 3599:
                    files.append(candidate)
            except (ValueError, TypeError, subprocess.SubprocessError):
                pass
    result["video_files"] = str(len(files))
    result["video_names"] = ",".join(file.relative_to(OUTPUT).as_posix() for file in files)
    audio_files = sorted(MUSIC.rglob("*.mp3")) if MUSIC.exists() else []
    result["audio_files"] = str(len(audio_files))
    result["audio_names"] = ",".join(file.relative_to(MUSIC).as_posix() for file in audio_files)
    return result


PAGE = r"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pepe lo-fi · Stable Audio 3 albums</title>
<style>
body{margin:0;background:#10131a;color:#edf2f7;font:16px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif}
main{max-width:760px;margin:0 auto;padding:clamp(16px,5vw,32px) 14px 40px}h1{font-size:clamp(22px,6vw,30px);margin:0 0 8px}
.muted{color:#9aa7b5}.card{background:#1b2230;border:1px solid #303b4d;border-radius:14px;padding:18px;margin-top:16px}
.row{display:flex;justify-content:space-between;gap:16px;margin:10px 0}.value{font-weight:600;text-align:right;overflow-wrap:anywhere}
.bar{height:18px;background:#303b4d;border-radius:99px;overflow:hidden;margin:10px 0 8px}.fill{height:100%;background:#36d399;width:0%;transition:width .4s}
.percent{font-size:28px;font-weight:700}.ok{color:#36d399}.warn{color:#fbbf24}.bad{color:#fb7185}
code{word-break:break-all;color:#c4b5fd}ul{padding-left:20px;margin-bottom:0}
</style></head><body><main><h1>Pepe lo-fi render</h1><div class="muted">Обновление каждые 2 секунды · только локальная Wi‑Fi сеть</div>
<section class="card"><div class="row"><span>Состояние</span><span id="state" class="value">загрузка…</span></div>
<div class="row"><span>Текущий этап</span><span id="stage" class="value">—</span></div>
<div class="bar"><div id="fill" class="fill"></div></div><div class="row"><span id="detail">—</span><span id="percent" class="percent">0%</span></div></section>
<section class="card"><div class="row"><span>Видео</span><span id="videos" class="value">0/10</span></div><div class="row"><span>Изображений</span><span id="images" class="value">—</span></div><div class="row"><span>Последнее обновление</span><span id="updated" class="value">—</span></div></section>
<section class="card"><div class="row"><span>Аудио: время генерации</span><span id="audioTime" class="value">—</span></div><div class="row"><span>Видео: время текущего рендера</span><span id="videoTime" class="value">—</span></div><div class="row"><span>Общее время очереди</span><span id="totalTime" class="value">—</span></div></section>
<section class="card"><div>Готовые файлы</div><ul id="files"><li class="muted">пока нет</li></ul></section>
<section class="card"><div>Предпросмотр аудио</div><div id="audioList" class="muted">готовых треков пока нет</div></section>
<section class="card"><div>Предпросмотр всех готовых видео</div><div id="videoList"><div id="videoHint" class="muted" style="margin-top:10px">готовых видео пока нет</div></div></section>
<section class="card"><div>Ошибка / примечание</div><div id="error" class="muted" style="margin-top:10px;overflow-wrap:anywhere">—</div></section>
<section class="card"><div>Журнал Stable Audio 3</div><pre id="log" class="muted" style="white-space:pre-wrap;overflow-wrap:anywhere;max-height:260px;overflow:auto;margin-bottom:0">загрузка…</pre></section></main>
<script>
const escapeHtml=s=>s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels={starting:'запуск',loading_model:'загрузка модели',generating_music:'Stable Audio 3: генерация трека',assembling_track:'сборка трека',assembling_audio:'сведение альбома',rendering_video:'рендер видео',music_complete:'музыка готова',running:'рендер видео',complete:'готово',blocked:'ошибка'};
function render(d){
 const state=d.state||'starting', music=Number(d.music_percent||0), videos=Number(d.completed||0), total=Number(d.total||10);
 const isMusic=['starting','loading_model','generating_music','saving_audio'].includes(state), p=isMusic?music:state==='complete'?100:Number(d.percent||0);
 document.querySelector('#state').textContent=labels[state]||state;
 document.querySelector('#state').className='value '+(state==='blocked'?'bad':state==='complete'?'ok':'warn');
 document.querySelector('#stage').textContent=isMusic?(d.variant?`Stable Audio 3 · ${d.variant} · трек ${d.music_track||d.current||1}/${d.track_count||d.tracks_per_album||15} · сегмент ${d.music_segment||'1/2'}`:'Stable Audio 3'):state==='rendering_video'?`альбом ${d.album_index||videos+1}/${total} · фото + ${d.track_count||d.tracks_per_album||15} треков`:state==='assembling_audio'?'сведение альбома с переходами':state==='assembling_track'?'внутренний crossfade трека':state==='running'?`видео ${d.current||videos+1} из ${total}`:labels[state]||state;
 document.querySelector('#fill').style.width=Math.min(100,p)+'%'; document.querySelector('#percent').textContent=Math.round(p)+'%';
 document.querySelector('#detail').textContent=isMusic?(d.music_step?`diffusion step ${d.music_step} · segment ${d.music_segment||'1/2'}`:'подготовка Stable Audio 3'):state==='rendering_video'?'финальный MP4 ровно на 1 час':state==='blocked'?(d.error||d.reason||'pipeline остановлен'):`${d.track_count||d.tracks_per_album||15} треков · ${videos}/${total}`;
 document.querySelector('#videos').textContent=`${videos}/${total}`; document.querySelector('#images').textContent=d.images||'—';
 document.querySelector('#updated').textContent=new Date().toLocaleTimeString();
 document.querySelector('#error').textContent=d.error||d.reason||d.album||'—';
 document.querySelector('#log').textContent=d.log_tail||'лог пока пуст';
 const now=Math.floor(Date.now()/1000), elapsed=(from,to)=>{if(!from)return '—';const s=Math.max(0,(to||now)-Number(from));return `${Math.floor(s/3600)}ч ${Math.floor(s%3600/60)}м ${s%60}с`};
 document.querySelector('#audioTime').textContent=elapsed(d.music_started_at||d.track_started_at,d.music_finished_at);
 document.querySelector('#videoTime').textContent=state==='rendering_video'?elapsed(d.video_started_at):elapsed(d.video_started_at,d.video_finished_at);
 document.querySelector('#totalTime').textContent=elapsed(d.queue_started_at,d.queue_finished_at);
 const names=(d.video_names||'').split(',').filter(Boolean); document.querySelector('#files').innerHTML=names.length?names.map(n=>`<li><code>${escapeHtml(n)}</code></li>`).join(''):'<li class="muted">пока нет</li>';
 const audio=(d.audio_names||'').split(',').filter(Boolean), audioBox=document.querySelector('#audioList');
 audioBox.className=audio.length?'':'muted'; const audioKey=audio.join('|'); if(audioBox.dataset.key!==audioKey){audioBox.dataset.key=audioKey;audioBox.innerHTML=audio.length?audio.map(n=>`<div style="margin-top:12px"><div><code>${escapeHtml(n)}</code></div><audio controls preload="none" style="width:100%;margin-top:6px" src="/media/audio/${encodeURIComponent(n)}"></audio></div>`).join(''):'готовых треков пока нет'};
 const videoBox=document.querySelector('#videoList');
 const videoKey=names.join('|');
 if(videoBox.dataset.key!==videoKey){
  videoBox.dataset.key=videoKey;
  videoBox.innerHTML=names.length?names.map((n,i)=>{
   const src='/media/video/'+encodeURIComponent(n);
   const safe=escapeHtml(n);
   return `<div style="margin-top:16px"><div><strong>${i+1}. ${safe}</strong></div><video controls preload="metadata" style="width:100%;margin-top:8px;background:#000;border-radius:10px" src="${src}"></video></div>`;
  }).join(''):'<div id="videoHint" class="muted" style="margin-top:10px">готовых видео пока нет</div>';
 }
}
async function refresh(){try{const r=await fetch('/status.json?'+Date.now());render(await r.json())}catch(e){document.querySelector('#state').textContent='нет связи'}}
refresh();setInterval(refresh,2000);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
            "media-src 'self'; frame-ancestors 'none'",
        )
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
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
                    end = size - 1
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


if __name__ == "__main__":
    print(f"Pepe lo-fi status: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
