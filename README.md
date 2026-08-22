# Music Video Generator

Локальный набор скриптов для генерации lo-fi музыки, сборки часовых музыкальных видео, просмотра прогресса в локальной сети и создания приватных черновиков YouTube через Postiz.

Репозиторий содержит только код и конфигурацию. Видео, аудио, изображения, модели, веса, сторонние исходные репозитории, виртуальные окружения, журналы, временные файлы и реальные ключи API намеренно не включены.

## Владелец и лицензия

Оригинальный код, конфигурация и документация в этом репозитории являются собственностью **Vasilii Bereznikov**.

Copyright © 2026 Vasilii Bereznikov. All Rights Reserved. Использование, копирование, изменение и распространение без предварительного письменного разрешения владельца запрещены. Полный текст находится в [LICENSE](LICENSE).

Эта лицензия не распространяется на сторонние модели, библиотеки, сервисы и материалы. Для каждого выбранного генератора и каждого медиафайла необходимо отдельно проверить актуальную лицензию и права на коммерческое использование. В частности, `facebook/musicgen-small` использует некоммерческие веса; результаты этого режима должны оставаться помеченными `NON_COMMERCIAL_DEMO`.

## Что находится в репозитории

- `scripts/` — генерация музыки, сборка видео, очереди альбомов, локальная status page и Postiz uploader;
- `config.yaml` — параметры MusicGen и Pexels-поиска;
- `config/stable_audio3_prompt_library.json` — профили альбомов и вариации треков;
- `.env.example` — только имена переменных и безопасные примеры;
- `requirements-musicgen.txt` — проверенный набор базовых Python-зависимостей для MusicGen-режима.

Во время работы скрипты создают локальные каталоги `assets/`, `models/`, `output/`, `tmp/` и `metadata/`. Все они исключены из Git.

## Системные требования

- macOS или Linux;
- Python 3.9+;
- `ffmpeg`, `ffprobe`, `curl` и `jq`;
- достаточно свободного места для выбранной модели, временного аудио и финального видео;
- для Apple Silicon: перед MPS-генерацией проверьте свободное место и оставьте возможность CPU fallback.

На macOS системные утилиты можно установить так:

```bash
brew install ffmpeg jq
```

Проверка окружения:

```bash
./scripts/check_dependencies.sh
```

## Быстрый запуск: MusicGen (только NON_COMMERCIAL_DEMO)

```bash
git clone git@github.com:Arnon-hs/music-video.git
cd music-video

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-musicgen.txt

cp .env.example .env
set -a
source .env
set +a

./scripts/check_dependencies.sh
.venv/bin/python scripts/search_pexels_images.py
.venv/bin/python scripts/generate_music.py
./scripts/render_visual_loop.sh
REENCODE_VIDEO=1 ./scripts/build_video.sh
```

Перед скачиванием Pexels-изображений скрипт показывает кандидатов и ждёт точную строку `DOWNLOAD`. Перед скачиванием MusicGen он показывает объём и лицензионную границу и ждёт `DOWNLOAD_MODEL`. Настоящий `.env` не коммитьте.

## Другие генераторы

Код содержит адаптеры для трёх внешних генераторов. Их исходный код и веса не входят в репозиторий.

### ACE-Step

Ожидаемая локальная структура:

```text
ace-step-v1/.venv/          # окружение с пакетом acestep
models/ace-step/            # checkpoint
```

После установки выбранной совместимой версии ACE-Step и загрузки checkpoint:

```bash
ACE_DEVICE=cpu ./scripts/run_ace_step_music.sh --duration 60 --seed 20260725
```

CPU-режим является безопасным значением для Mac с 16 ГБ unified memory, где MPS-путь может зависать. Проверьте актуальную лицензию конкретного checkpoint и каждый результат до публикации.

### DiffRhythm 2

Ожидаемая локальная структура:

```text
.models/DiffRhythm2/inference.py
.venv-diffrhythm2/bin/python
```

Пример одного запуска через проектный адаптер:

```bash
.venv-diffrhythm2/bin/python scripts/generate_music_diffrhythm2.py \
  --duration 180 \
  --variant rainy-cafe \
  --output assets/music/diffrhythm2/track-01.mp3
```

Для часового плейлиста:

```bash
TRACK_COUNT=12 BASE_SECONDS=180 TRACK_SECONDS=303 \
  ./scripts/render_diffrhythm2_playlist.sh
```

### Stable Audio 3

Ожидается отдельное окружение `.venv-stable-audio3` с доступным импортом `stable_audio_3` и локально установленной выбранной версией модели.

```bash
.venv-stable-audio3/bin/python scripts/generate_music_stable_audio3.py \
  --album-style rainy-cafe \
  --track-index 1 \
  --output assets/music/stable-audio3/track-01.mp3
```

Очередь десяти часовых альбомов:

```bash
ALBUM_COUNT=10 TRACK_COUNT=15 ./scripts/render_stable_audio3_albums.sh
```

## Локальная страница статуса

```bash
STATUS_HOST=0.0.0.0 STATUS_PORT=8765 python3 scripts/status_server.py
```

Откройте `http://<IP-компьютера>:8765` в той же локальной сети. Сервер показывает прогресс и отдаёт только готовые аудио/видео из локальных каталогов с поддержкой HTTP Range. Не публикуйте этот порт в интернет без отдельной аутентификации и reverse proxy.

## Postiz: приватные черновики YouTube

Скрипт использует интеграцию, заданную в `scripts/postiz_upload_ready_videos.py`, и берёт секрет только из `POSTIZ_API_KEY`:

```bash
export POSTIZ_API_KEY='your_key'
export POSTIZ_LOCAL_BASE_URL='http://your-lan-host:8765'
python3 scripts/postiz_upload_ready_videos.py
```

Режим наблюдения:

```bash
python3 scripts/postiz_upload_ready_videos.py --watch --interval 30
```

Перед запуском проверьте интеграцию, приватность канала и каждый подготовленный материал. Скрипт создаёт приватные draft-записи, но не заменяет ручную проверку прав и содержания.

## Проверка перед коммитом

```bash
python3 -m compileall -q scripts
for file in scripts/*.sh; do bash -n "$file"; done
git status --short
git ls-files | rg '\.(mp4|mov|mkv|wav|mp3|flac|jpg|jpeg|png|webp)$' && exit 1 || true
```
