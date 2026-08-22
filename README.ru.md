# Music Video Generator

[English](README.md) · [Русский](README.ru.md)

Локальный набор скриптов для генерации инструментальной музыки, отображения прогресса, сборки музыкальных видео, предпросмотра в локальной сети и создания приватных YouTube-черновиков через Postiz.

В Git хранятся только код и безопасная конфигурация. Сгенерированные аудио/видео, изображения, веса моделей, сторонние исходные репозитории, виртуальные окружения, журналы, временные файлы и настоящие ключи исключены.

## Возможности

- интерактивный мастер в терминале: `./music-video` без аргументов;
- CLI для пользователя, LLM и coding agent;
- 12 жанров без голоса: techno, lo-fi, classical, electronic, ambient, house, synthwave, jazz, drum & bass, cinematic, chillout и instrumental hip-hop;
- адаптеры MusicGen, ACE-Step, DiffRhythm 2 и Stable Audio 3;
- этап, процент при наличии достоверных данных, прошедшее время и вывод модели;
- опциональная сборка MP4 из локальных изображений;
- JSON-вывод команд `genres`, `doctor` и `status`;
- приватные черновики через Postiz;
- модели и медиа не скачиваются самим CLI скрытно.

## Лицензия

Copyright 2026 Vasilii Bereznikov.

Проект распространяется по [PolyForm Noncommercial License 1.0.0](LICENSE). Код можно использовать, изучать, изменять и передавать сообществу для разрешённых некоммерческих целей при сохранении лицензии и обязательного уведомления об авторских правах.

Это community-friendly source-available лицензия, но не OSI Open Source. Apache-2.0 не выбрана намеренно: она разрешает коммерческое использование. Коммерческое использование этого репозитория требует отдельного разрешения владельца.

Лицензии моделей, весов, сервисов и медиа проверяются отдельно. Лицензия кода модели не гарантирует права на веса или публикацию результата.

## Быстрый старт

```bash
git clone git@github.com:Arnon-hs/music-video.git
cd music-video

./music-video doctor
./music-video genres
./music-video
```

Интерактивный режим предлагает:

1. выбрать жанр;
2. выбрать установленный backend;
3. указать длительность;
4. при необходимости собрать видео из `assets/images`;
5. при необходимости принудительно использовать CPU;
6. наблюдать прогресс до появления пути готового файла.

## Работа с CLI

```bash
./music-video --help
./music-video genres
./music-video genres --json
./music-video doctor
./music-video doctor --json
./music-video status
./music-video status --json
```

Техно через ACE-Step:

```bash
./music-video generate \
  --backend ace-step \
  --genre techno \
  --duration 60
```

Классическая музыка с последующей сборкой видео:

```bash
./music-video generate \
  --backend stable-audio3 \
  --genre classical \
  --duration 120 \
  --video
```

Проверка команды без запуска модели:

```bash
./music-video generate \
  --backend diffrhythm2 \
  --genre drum-and-bass \
  --duration 180 \
  --dry-run
```

Собственный prompt от LLM:

```bash
./music-video generate \
  --backend ace-step \
  --genre electronic \
  --duration 90 \
  --prompt "Instrumental modular electronic music, 118 BPM, evolving polyrhythms, deep bass, no vocals, no speech, original melody"
```

Основные флаги:

| Флаг | Назначение |
|---|---|
| `--backend` | `musicgen`, `ace-step`, `diffrhythm2` или `stable-audio3` |
| `--genre` | slug жанра; есть aliases `classic`, `lo-fi`, `dnb` |
| `--duration` | длительность в секундах с проверкой лимита backend’а |
| `--seed` | seed для воспроизводимой генерации |
| `--prompt` | собственное описание стиля вместо жанрового; запрет на голос всё равно добавляется |
| `--video` | собрать MP4 после музыки |
| `--force-cpu` | отключить GPU/MPS, где это поддерживается |
| `--allow-downloads` | явно разрешить DiffRhythm/Stable Audio скачать отсутствующие модели |
| `--dry-run` | показать prompt, путь и команду без запуска модели |

Жанры находятся в [`config/genres.json`](config/genres.json). К каждому встроенному или собственному prompt добавляется запрет на вокал, речь, рэп, хор, chanting, voice samples, имитацию артистов и узнаваемые защищённые мелодии.

## Прогресс и файлы

CLI показывает этап, процент при наличии достоверных данных, текущий segment/diffusion step, время, строки журнала и финальные пути.

Из другого терминала или агента:

```bash
watch -n 2 './music-video status'
./music-video status --json
```

Локальные каталоги создаются автоматически и игнорируются Git:

```text
assets/images/                  локальные изображения
assets/music/<backend>/<genre>/ сгенерированное аудио
output/                         готовые MP4
tmp/                            прогресс, логи и временный рендер
metadata/                       локальные отчёты и лицензии материалов
models/ и .models/              веса и сторонние репозитории
```

## Backend’ы и LLM

CLI только оркестрирует локальные модели. Код моделей и веса не входят в этот репозиторий.

### [facebookresearch / AudioCraft (MusicGen)](https://github.com/facebookresearch/audiocraft)

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-musicgen.txt

./music-video generate --backend musicgen --genre lofi --duration 60
```

Веса `facebook/musicgen-small` имеют лицензию CC-BY-NC 4.0, поэтому результат всегда помечается `NON_COMMERCIAL_DEMO`. Первое скачивание требует ручной строки `DOWNLOAD_MODEL`.

### [ACE-Step / ACE-Step-1.5](https://github.com/ace-step/ACE-Step-1.5)

Текущий адаптер ожидает:

```text
ace-step-v1/.venv/bin/python
models/ace-step/
```

```bash
ACE_DEVICE=cpu ./music-video generate --backend ace-step --genre techno --duration 60
```

Новые версии ACE-Step могут потребовать обновления адаптера. Перед запуском используйте `./music-video doctor`.

### [ASLP-lab / DiffRhythm](https://github.com/ASLP-lab/DiffRhythm)

### [ASLP-lab / DiffRhythm2](https://github.com/ASLP-lab/DiffRhythm2)

Адаптер ожидает DiffRhythm 2:

```text
.models/DiffRhythm2/inference.py
.venv-diffrhythm2/bin/python
```

```bash
./music-video generate --backend diffrhythm2 --genre jazz --duration 180
```

Instrumental mode задаётся prompt’ом и структурой `[inst]`. Результат всё равно нужно прослушать: текстовый запрет не гарантирует отсутствие vocal-like звуков.

По умолчанию CLI включает для этого backend Hugging Face offline mode. Добавляйте `--allow-downloads` только после проверки модели и ожидаемого размера.

### [Stability-AI / stable-audio-3](https://github.com/Stability-AI/stable-audio-3)

### [Stability-AI / stable-audio-tools](https://github.com/Stability-AI/stable-audio-tools)

```text
.venv-stable-audio3/bin/python
```

```bash
./music-video generate --backend stable-audio3 --genre ambient --duration 120
```

Один запуск текущего адаптера ограничен 234 секундами; длинные альбомы собирают существующие queue-скрипты.

По умолчанию CLI включает для этого backend Hugging Face offline mode. Добавляйте `--allow-downloads` только после проверки модели и ожидаемого размера.

## Работа с LLM

LLM должна подготовить style prompt, а не исполняемый код или credentials. Рекомендуемый контракт:

```text
Create one concise English music-generation prompt.
The output must be purely instrumental: no vocals, speech, rap, choir,
chants, vocal chops, or voice samples. Do not imitate artists or quote
recognisable melodies. Include genre, BPM range, instrumentation, mood,
rhythm, arrangement, and mix characteristics.
```

Перед затратным запуском проверьте prompt и команду:

```bash
./music-video generate --backend ace-step --genre electronic \
  --prompt "<LLM prompt>" --duration 60 --dry-run
```

## Работа с coding agent

Безопасная последовательность для Codex, Claude Code или другого локального агента:

1. `./music-video doctor --json`;
2. `./music-video genres --json`;
3. выбрать backend с `ready: true`;
4. показать команду с `--dry-run`;
5. получить подтверждение до скачивания модели или медиа;
6. запустить одну ограниченную генерацию;
7. читать фактический `./music-video status --json`;
8. проверить результат через `ffprobe` и прослушивание;
9. не коммитить `.env`, медиа, модели, checkpoint’ы и логи;
10. не загружать и не публиковать без прямого запроса пользователя.

Готовый запрос агенту:

```text
В этом репозитории запусти ./music-video doctor --json и genres --json.
Подготовь 60-секундную инструментальную генерацию жанра <genre> через
<backend>. Сначала покажи dry-run. Не скачивай модели/медиа, не загружай
и не публикуй ничего без моего явного подтверждения. Показывай фактический
status --json и проверь готовый файл.
```

## Изображения и видео

Положите собственные разрешённые изображения в `assets/images` или используйте предварительный поиск Pexels:

```bash
export PEXELS_API_KEY='your_key'
.venv/bin/python scripts/search_pexels_images.py
```

Скрипт сначала показывает кандидатов и скачивает только после точной строки `DOWNLOAD`. Права на Pexels-материалы нужно проверять отдельно.

```bash
./music-video generate --backend ace-step --genre synthwave --duration 90 --video
```

## Postiz и приватные YouTube-черновики

Персональные значения берутся только из окружения. В коде больше нет integration ID или API key.

```bash
cp .env.example .env
```

Заполните локальный `.env`:

```dotenv
POSTIZ_API_KEY=your_real_key
POSTIZ_INTEGRATION_ID=your_youtube_integration_id
POSTIZ_API_ROOT=https://api.postiz.com/public/v1
POSTIZ_VIDEO_ROOT=output
# Необязательно; оставьте пустым, если POSTIZ_VIDEO_ROOT не раздается этим сервером.
POSTIZ_LOCAL_BASE_URL=
```

```bash
set -a
source .env
set +a

python3 scripts/postiz_upload_ready_videos.py
python3 scripts/postiz_upload_ready_videos.py --watch --interval 30
```

Скрипт запрашивает top-level draft и приватную видимость YouTube, а idempotency state хранит в `tmp/postiz-uploaded.json`. `POSTIZ_LOCAL_BASE_URL` необязателен и попадает в черновик только при явной настройке. После ответа обязательно проверьте post ID и сам черновик в Postiz до ручной публикации.

## Status page в локальной сети

Для существующей очереди Stable Audio albums:

```bash
STATUS_HOST=0.0.0.0 STATUS_PORT=8765 python3 scripts/status_server.py
```

Откройте `http://<IP-компьютера>:8765` в той же сети. Не публикуйте этот сервер в интернет без отдельной аутентификации.

## Низкоуровневые скрипты

CLI — основная точка входа. Старые команды для очередей остаются доступны:

```bash
./scripts/check_dependencies.sh
./scripts/render_diffrhythm2_playlist.sh
./scripts/render_diffrhythm2_albums.sh
./scripts/render_stable_audio3_albums.sh
./scripts/render_one_hour_album.sh
```

## Разработка и проверка

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q music_video_cli.py scripts tests
for file in music-video scripts/*.sh; do bash -n "$file"; done
git diff --check
```

Для community contribution:

- сохраняйте CLI code-only и без лишних зависимостей;
- добавляйте тесты при изменении поведения;
- не добавляйте медиа, модели, сторонние checkout’ы и credentials;
- сохраняйте Required Notice лицензии PolyForm;
- честно описывайте границы лицензий сторонних моделей и результатов.
