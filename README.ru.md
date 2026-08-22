# Music Video Generator

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

Превратите текстовое описание в инструментальный трек или часовое видео-плейлист прямо из терминала. Выберите жанр и модель, следите за реальным прогрессом, а готовый ролик при желании отправьте в Postiz как приватный YouTube-черновик.

Проект остаётся code-only и local-first: музыка, картинки, веса моделей, виртуальные окружения, логи и настоящие API-ключи не попадают в Git.

## Быстрый старт: от клона до безопасного dry-run

### 1. Откройте проект и посмотрите, что уже готово

```bash
git clone git@github.com:Arnon-hs/music-video.git
cd music-video

./music-video doctor
./music-video genres
```

`doctor` проверяет FFmpeg и окружения моделей. Если backend отмечен как отсутствующий, сначала настройте именно его — ставить сразу все модели не нужно.

### 2. Проверьте маленькую задачу без запуска модели

```bash
./music-video generate \
  --backend ace-step \
  --genre lofi \
  --duration 60 \
  --dry-run
```

Dry-run показывает prompt, путь результата и точную команду, но не загружает модель и ничего не генерирует.

### 3. Запустите команду или мастер в терминале

Уберите `--dry-run`, когда план устраивает, либо откройте пошаговый интерфейс:

```bash
./music-video
```

## Выберите свой сценарий

| Хочу… | С чего начать | Что получится |
|---|---|---|
| просто посмотреть проект | `./music-video genres` и `--dry-run` | готовая команда без затрат GPU |
| сделать один трек | `./music-video generate ...` | WAV или MP3 в `assets/music` |
| добавить обложку | добавить `--video`, картинку положить в `assets/images` | MP4 в `output` |
| собрать часовую подборку | `./music-video playlist ...` | разные треки одного жанра и MP4 ровно на 3600 секунд |
| поручить работу агенту | используйте prompt и skill ниже | ограниченный и наблюдаемый процесс |
| подготовить YouTube-загрузку | сначала Postiz `--dry-run` | приватный черновик для ручной проверки |

## Готовый запрос агенту

Замените значения в угловых скобках и отправьте этот текст в Codex, Claude Code или другой локальный coding agent:

```text
Работай в этом репозитории и оставляй все созданные файлы локально.
1. Запусти ./music-video doctor --json и ./music-video genres --json.
2. Выбери backend с ready: true для жанра <genre>.
3. Подготовь <60-секундный трек | часовое видео-плейлист> через <backend>.
   Используй assets/images/<cover-file> только если требуется видео.
4. Сначала покажи полный --dry-run. Не скачивай модели или медиа без
   моего подтверждения.
5. После подтверждения запусти одну ограниченную задачу и показывай
   фактический ./music-video status --json.
6. Проверь длительность и потоки через ffprobe и попроси меня прослушать результат.
7. Ничего не загружай и не публикуй. Для Postiz сначала сделай --dry-run
   и создавай только приватный черновик.
```

## Подключение к рабочей сессии Codex

В репозитории уже есть skill `.agents/skills/music-video-generator`. Он объясняет агенту, как проверить модели, сделать dry-run, сгенерировать трек или плейлист, проверить медиа, работать на удалённой GPU и не опубликовать результат случайно.

### Внутри этого репозитория — без установки

1. Откройте корень репозитория как workspace в Codex.
2. Создайте новую задачу из этой папки: Codex обнаруживает repo-scoped skills в `.agents/skills`.
3. Напишите `$music-video-generator` или просто попросите сделать инструментальный трек/плейлист.

```text
Используй $music-video-generator. Проверь doctor и genres, затем покажи
dry-run часового lo-fi плейлиста с cover.jpg. Пока ничего не устанавливай,
не скачивай, не загружай и не публикуй.
```

### Во всех рабочих папках Codex

```bash
./scripts/install_codex_skill.sh
```

Скрипт создаёт безопасную символическую ссылку `~/.agents/skills/music-video-generator` на skill в этом checkout и не перезаписывает существующий путь. Если skill не появился, перезапустите клиент. Отключение удаляет только ссылку:

```bash
unlink ~/.agents/skills/music-video-generator
```

Подробнее: [официальная инструкция OpenAI по skills](https://developers.openai.com/codex/skills/). Отдельное приложение или plugin пока не нужны: repo-skill легче установить и обновлять. Plugin имеет смысл позже, если потребуется публичная установка, несколько skills и встроенные connectors.

Skill сам не скачивает модели и не арендует GPU: это действия с расходами и внешними изменениями, поэтому агент должен получить явное подтверждение.

## Что удобно, а где есть ограничения

| Преимущества | Ограничения |
|---|---|
| один CLI для четырёх backend’ов и 12 инструментальных жанров | код и веса моделей ставятся отдельно |
| dry-run, прогресс, JSON-status и продолжение прерванного плейлиста | генерация может быть долгой и требовательной к памяти |
| один трек или ровно час видео с картинкой без обрезки | это не видеоредактор: одна статичная картинка, без сцен и анимации |
| запреты на голос и имитацию артистов добавляются к prompt | модель всё равно может создать vocal-like звук или вызвать Content ID |
| локальные файлы и приватные Postiz-черновики | встроенного публичного API генерации пока нет |

## Своё железо, RunPod или API

| Режим | Готов сейчас? | Как работает |
|---|---|---|
| Mac/Linux локально | да | установите один backend и запускайте CLI |
| RunPod Pod или GPU VPS | да | удалённая Linux-машина: SSH, постоянный диск, тот же CLI, затем копирование результата домой |
| RunPod Serverless API | пока нет | нужны Docker-образ, handler, хранилище артефактов, авторизация и очередь заданий |
| LLM API | подключается отдельно | LLM пишет prompt, а вы передаёте его в `--prompt`; ключ LLM проект не хранит |
| Pexels API | опционально | ищет картинки, скачивание требует подтверждения |
| Postiz API | опционально | принимает готовый MP4 и создаёт приватный черновик, но не генерирует музыку |

Короткий путь на RunPod: создайте обычный GPU Pod из PyTorch-шаблона, подключите постоянный диск к `/workspace`, войдите по SSH, клонируйте репозиторий, установите только один backend и сначала выполните `doctor` и `--dry-run`. Долгую генерацию запускайте в `tmux`, прогресс смотрите через `./music-video status --json`, результат проверяйте `ffprobe` и копируйте домой через `scp`. После копирования остановите GPU, но не удаляйте Pod/volume, пока не убедитесь, что нужные файлы сохранены.

Полные команды, хранение файлов и варианты Vast.ai/обычного NVIDIA VPS описаны в [инструкции по удалённой GPU](docs/REMOTE_GPU.md). Обычный Pod/VPS — рекомендуемый первый шаг: текущие адаптеры рассчитаны на локальные файлы и долгоживущий процесс. Serverless станет настоящим API только после отдельной упаковки worker’а.

## Лицензия и права

Copyright 2026 Vasilii Bereznikov.

Проект распространяется по [PolyForm Noncommercial License 1.0.0](LICENSE). Код можно использовать, изучать, изменять и передавать сообществу для разрешённых некоммерческих целей при сохранении лицензии и уведомления об авторских правах.

Это source-available лицензия для сообщества, но не OSI Open Source. Apache-2.0 намеренно не использована, потому что разрешает коммерческое применение. Для коммерческого использования нужно отдельное разрешение владельца.

У моделей, весов, API, изображений и результатов — собственные условия. Перед публикацией проверяйте выбранную модель и каждый медиафайл: лицензия этого кода не очищает права на веса или сгенерированную музыку автоматически.

## Готовые рецепты CLI

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

### Часовое видео с плейлистом

Положите разрешённую картинку-обложку в `assets/images`, сначала проверьте полный план, затем запустите генерацию:

```bash
./music-video playlist \
  --backend ace-step \
  --genre lofi \
  --image assets/images/cover.jpg \
  --dry-run

./music-video playlist \
  --backend ace-step \
  --genre lofi \
  --image assets/images/cover.jpg \
  --force-cpu
```

Команда генерирует отдельные треки одного жанра с разной длительностью, seed и вариациями аранжировки. Затем она соединяет их трёхсекундными crossfade-переходами и монтирует ровно 3600 секунд видео H.264/AAC. Выбранная картинка вписывается в кадр 1280x720 с полями, без обрезки и растягивания.

Количество треков подбирается автоматически с учётом лимита backend’а: обычно 12 для MusicGen/ACE-Step, 18 для Stable Audio 3 и 20 для DiffRhythm 2. Его можно изменить через `--tracks`, длительность перехода — через `--crossfade`, общий стиль альбома — через `--prompt`, а итоговый путь — через `--output`. Некорректные комбинации отклоняются до запуска модели.

Уже созданные корректные треки переиспользуются после проверки длительности через `ffprobe`, поэтому прерванную генерацию можно продолжить. DiffRhythm/Stable Audio остаются в offline mode без явного `--allow-downloads`, а MusicGen сохраняет отдельное ручное подтверждение `DOWNLOAD_MODEL`. CLI также проверяет длительность готового видео перед сообщением об успехе.

Для пошагового режима запустите `./music-video` без аргументов и выберите **One-hour playlist video**. Прогресс доступен через `./music-video status` и `./music-video status --json`. После просмотра готового MP4 используйте существующий Postiz `--dry-run`, прежде чем создавать приватный YouTube-черновик.

Основные флаги:

| Флаг | Назначение |
|---|---|
| `--backend` | `musicgen`, `ace-step`, `diffrhythm2` или `stable-audio3` |
| `--genre` | slug жанра; есть aliases `classic`, `lo-fi`, `dnb` |
| `--duration` | длительность в секундах с проверкой лимита backend’а |
| `--seed` | seed для воспроизводимой генерации |
| `--prompt` | описание стиля до 2000 символов без управляющих символов; запрет на голос всё равно добавляется |
| `--video` | собрать MP4 после музыки |
| `--force-cpu` | отключить GPU/MPS, где это поддерживается |
| `--allow-downloads` | явно разрешить DiffRhythm/Stable Audio скачать отсутствующие модели |
| `--dry-run` | показать prompt, путь и команду без запуска модели |

Жанры находятся в [`config/genres.json`](config/genres.json). К каждому встроенному или собственному prompt добавляется запрет на вокал, речь, рэп, хор, chanting, voice samples, имитацию артистов и узнаваемые защищённые мелодии.

## Как следить за задачей и найти файлы

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

## Выбор модели

CLI только оркестрирует локальные модели. Код моделей и веса не входят в этот репозиторий.

| Backend | Для чего удобен | Лимит одного трека | Практическое замечание | Права |
|---|---|---:|---|---|
| MusicGen | простой первый запуск и lo-fi эксперименты | 3600 с | Python 3.11; MPS/CPU может работать медленно | веса `facebook/musicgen-small` — CC-BY-NC 4.0, результат помечается `NON_COMMERCIAL_DEMO` |
| ACE-Step | длинные оригинальные треки и плейлисты | 600 с | адаптер ожидает проверенную локальную структуру v1; CPU — fallback, а не быстрый режим | проверяйте точную версию checkpoint и результат |
| DiffRhythm 2 | короткие треки и плейлисты из большого числа частей | 210 с | offline по умолчанию; возможен vocal-like звук | код, веса и права результата проверяются отдельно |
| Stable Audio 3 | ambient/electronic и продолжения треков | 234 с | текущий адаптер рассчитан на Small-Music и два сегмента | проверяйте лицензию выбранной модели и публикации |

### Чего ждать от железа

Ниже — консервативные профили именно для этого репозитория, а не универсальные минимумы моделей. Начните с задачи на 30–60 секунд: успешный `doctor` подтверждает наличие путей, но не скорость, запас памяти, совместимость версии модели или качество музыки.

#### Базовые системные требования

| Компонент | Только CLI, dry-run и FFmpeg | Практичная локальная генерация | Комфортная работа с плейлистами |
|---|---|---|---|
| Операционная система | macOS 14+ или актуальный 64-битный Linux | macOS 14+ на Apple Silicon либо Ubuntu 22.04/24.04 x86-64 | удалённый Linux с NVIDIA CUDA даёт лучшую совместимость |
| Процессор | 4 современных ядра | 8 современных ядер | 8–16 ядер; FFmpeg и CPU fallback используют дополнительные ядра |
| Оперативная память | 8 GB; стабильную генерацию моделей не ожидайте | 16 GB — практический минимум для одной короткой лёгкой задачи | рекомендуется 32 GB; 64 GB полезны для тяжёлого CPU fallback и нескольких кэшей моделей |
| Свободный диск | 20 GB для кода, инструментов и временной сборки видео | минимум 50 GB для одного backend’а и коротких результатов | рекомендуется 100 GB для часовых задач; 200 GB при хранении нескольких backend’ов/checkpoint’ов |
| Инструменты | Bash, Git, Python 3, FFmpeg, `ffprobe` | Python 3.11 и отдельное окружение одного backend’а | добавьте `tmux`; на NVIDIA подберите совместимые версии драйвера, CUDA, PyTorch и модели |
| Сеть | не нужна для уже подготовленного dry-run | нужна при первом скачивании кода и модели | стабильное соединение для настройки сервера; сама генерация может идти offline |

Адаптер MusicGen также не запускает MPS, если на внутреннем системном томе macOS свободно меньше 12 GiB. Веса можно держать на другом диске, но macOS и PyTorch всё равно требуется внутреннее место для временных данных.

#### Какие Mac подходят

Поддерживаемое семейство Mac — Apple Silicon. Apple [описывает PyTorch MPS](https://developer.apple.com/metal/pytorch/) для Apple Silicon с macOS 14 или новее. CPU и GPU используют unified memory, поэтому объём установленной памяти не менее важен, чем поколение процессора.

| Конфигурация Mac | Насколько подходит проекту |
|---|---|
| Intel Mac | CLI и FFmpeg могут работать, но локальная генерация моделей не проверена и не рекомендуется; лучше использовать удалённую NVIDIA GPU |
| M1/M2 с 8 GB | подходит для знакомства с проектом, dry-run, Postiz и монтажа видео; памяти недостаточно для надёжной локальной генерации |
| любой M1–M5 с 16 GB | минимальный практический уровень для одного backend’а и экспериментов на 30–60 секунд; закройте тяжёлые приложения и ожидайте swap или медленный CPU fallback |
| M1–M5 Pro/Max с 24 или 32 GB | рекомендуемый локальный уровень для регулярной генерации и подготовки плейлистов; 32 GB дают заметно более безопасный запас |
| Max/Ultra с 64 GB и больше | лучший локальный запас для тяжёлых моделей и CPU fallback, но CUDA-only сценарии всё равно потребуют Linux/NVIDIA |

Более новое поколение M-серии сокращает время работы, но дополнительная unified memory обычно сильнее повышает надёжность, чем переход на одно поколение вперёд с тем же небольшим объёмом памяти. Проект наблюдался на M4 с 16 GB: ACE-Step v1 пришлось запускать через очень медленный CPU fallback после зависания MPS, поэтому такую машину нельзя обещать как быстрый часовой рендерер.

#### NVIDIA-сервер или RunPod

| Профиль | VRAM GPU | RAM сервера | CPU | Постоянный диск | Для чего |
|---|---:|---:|---:|---:|---|
| Небольшой эксперимент | 12–16 GB | 32 GB | 8 vCPU | 80 GB | один проверенный лёгкий backend и короткие тесты; подходит не каждому адаптеру |
| Рекомендуемый | 24 GB | 64 GB | 8–16 vCPU | 150 GB | наиболее безопасный первый выбор для текущих backend’ов и часовых плейлистов |
| Большой запас | 48 GB+ | 64–128 GB | 16+ vCPU | 200 GB+ | большие/новые checkpoint’ы, меньше offload или несколько сохранённых окружений |

Часовой плейлист не должен целиком помещаться в VRAM: CLI генерирует отдельные треки и соединяет их позже. Но растут общее время, объём временных файлов и вероятность прерывания, поэтому используйте постоянное хранилище и возможность продолжения.

#### Реальные требования backend’ов

| Backend | Рекомендация для Mac | Рекомендация для NVIDIA |
|---|---|---|
| MusicGen small | минимум 16 GB, предпочтительно 24/32 GB; при ошибке MPS возможен CPU fallback | 12–16 GB может хватить этой небольшой модели, но сначала проверьте 30 секунд |
| адаптер ACE-Step v1 | в наблюдавшейся конфигурации 16 GB работали только через медленный fallback; безопаснее 32 GB+ | для старого 3.5B-адаптера этого репозитория начинайте с 24 GB VRAM |
| DiffRhythm 2 | upstream описывает установку на macOS, но полный MPS-путь этого проекта не подтверждён | используйте 24 GB VRAM как консервативную отправную точку |
| Stable Audio 3 Small-Music | минимум 16 GB, предпочтительно 24/32 GB; текущий адаптер использует PyTorch, а не новый оптимизированный MLX-путь | легче старших вариантов, но перед длинной очередью проверьте точный checkpoint/runtime |

Upstream-проекты могут заявлять меньшие требования благодаря quantization, offload, MLX или более новым вариантам моделей. Эти цифры применимы только тогда, когда адаптер репозитория действительно использует такой путь. Следуйте инструкции для точной совместимой версии, затем снова запустите `./music-video doctor` и короткую генерацию до аренды GPU на много часов.

Проверка Mac перед установкой:

```bash
system_profiler SPHardwareDataType
sw_vers
df -h /
./music-video doctor --json
```

Проверка Linux/NVIDIA-сервера:

```bash
nvidia-smi
lscpu
free -h
df -h /workspace
./music-video doctor --json
```

### [facebookresearch / AudioCraft (MusicGen)](https://github.com/facebookresearch/audiocraft)

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-musicgen.txt

./music-video generate --backend musicgen --genre lofi --duration 60
```

Веса `facebook/musicgen-small` имеют лицензию CC-BY-NC 4.0, поэтому результат всегда помечается `NON_COMMERCIAL_DEMO`. Первое скачивание требует ручной строки `DOWNLOAD_MODEL`.

Прямые MusicGen-зависимости закреплены для review и security monitoring; разрешение transitive dependencies всё ещё может измениться. После изменения requirements пересоздайте venv и не используйте старое окружение.

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

## Подключение своей LLM

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

## Чек-лист безопасности для агента

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

Для короткого старта вызовите `$music-video-generator` и используйте готовый запрос в начале инструкции. Repo-skill применяет этот чек-лист автоматически.

## Добавление обложки и сборка MP4

Положите собственные разрешённые изображения в `assets/images` или используйте предварительный поиск Pexels:

```bash
export PEXELS_API_KEY='your_key'
.venv/bin/python scripts/search_pexels_images.py
```

Скрипт сначала показывает кандидатов и скачивает только после точной строки `DOWNLOAD`. Права на Pexels-материалы нужно проверять отдельно.

```bash
./music-video generate --backend ace-step --genre synthwave --duration 90 --video
```

## Отправка готового видео в Postiz

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

python3 scripts/postiz_upload_ready_videos.py --dry-run
python3 scripts/postiz_upload_ready_videos.py
python3 scripts/postiz_upload_ready_videos.py --watch --interval 30
```

`--dry-run` показывает ожидающие видео без credentials и обращения к Postiz. Реальный запуск запрашивает top-level draft и приватную видимость YouTube, а idempotency state хранит в `tmp/postiz-uploaded.json`. `POSTIZ_LOCAL_BASE_URL` необязателен и попадает в черновик только при явной настройке. API должен использовать HTTPS; HTTP разрешён только для loopback, если явно не установлен `POSTIZ_ALLOW_INSECURE_HTTP=1` после проверки сетевого риска. После ответа обязательно проверьте post ID и сам черновик в Postiz до ручной публикации.

## Необязательно: просмотр с другого устройства

По умолчанию сервер слушает только `127.0.0.1`. Для явного доступа к существующей очереди Stable Audio из доверенной локальной сети:

```bash
STATUS_HOST=0.0.0.0 STATUS_PORT=8765 python3 scripts/status_server.py
```

Откройте `http://<IP-компьютера>:8765` в той же сети. Не публикуйте этот сервер в интернет без отдельной аутентификации.

## Для опытных: ручные скрипты очередей

CLI — основная точка входа. Старые команды для очередей остаются доступны:

```bash
./scripts/check_dependencies.sh
./scripts/render_diffrhythm2_playlist.sh
./scripts/render_diffrhythm2_albums.sh
./scripts/render_stable_audio3_albums.sh
./scripts/render_one_hour_album.sh
```

## Разработка и проверка изменений

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

Одинаковая локальная и CI-проверка запускается одной командой:

```bash
./scripts/check.sh
```
