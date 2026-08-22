# Промпт агенту: опубликовать Music Video Generator как AtlasRepo Solution

Скопируйте весь блок ниже в новую задачу Codex или другого coding agent.

```text
Цель: добавить https://github.com/Arnon-hs/music-video в AtlasRepo как полноценное проверяемое solution, а не как рекламную карточку или временный hardcode.

Репозитории:
- AtlasRepo: Arnon-hs/reposearchengine, целевая ветка origin/main.
- Публичный каталог: Arnon-hs/open-source, ветка main.
- Solution source: Arnon-hs/music-video, ветка main.

Важная граница: сначала проверь точные checkout, ветки, remotes и git status. Не работай поверх грязного AtlasRepo checkout. Создай отдельный чистый worktree от свежего origin/main. Не используй GitHub Pages и не добавляй ссылки на arnon-hs.github.io/reposearchengine.

## Что требуется

1. Изучи текущую модель данных AtlasRepo, ingestion/review pipeline, repo-detail route, content/story templates и механизм публикации в Arnon-hs/open-source. Найди существующий канонический способ представить runnable solution. Не изобретай параллельный каталог, если текущая архитектура уже поддерживает нужный тип сущности.
2. Проверь, нет ли дубликата по canonical URL и owner/name `Arnon-hs/music-video`. Все новые данные должны проходить normalisation/deduplication и review gate; не публикуй автоматически непроверенный candidate.
3. Собери только проверяемые данные из официальных источников:
   - https://github.com/Arnon-hs/music-video
   - README EN/RU/ZH и LICENSE из этого репозитория;
   - https://www.youtube.com/@ATLASREPO
   - https://atlasrepo.com/
   - https://forum.atlasrepo.com/
   Не копируй веса моделей, media outputs, API keys или локальные пути.
4. Создай/обнови AtlasRepo record и публичную solution page для `Music Video Generator`. Страница должна объяснять:
   - проблему: разрозненные model-specific scripts не дают цельный creator workflow;
   - решение: единый CLI, instrumental genres, single-track video, one-hour varied playlist, web dashboard, FFprobe validation, remote GPU guide и private Postiz draft;
   - быстрый dry-run и запуск двумя терминалами;
   - преимущества, ограничения, hardware/API варианты и publication safety;
   - ссылки Website · Forum · YouTube · Repository · Open-source solution;
   - тексты на английском, русском и упрощённом китайском.
5. Лицензии описывай раздельно и без домыслов:
   - код проекта: фактическая лицензия из LICENSE;
   - лицензии MusicGen/ACE-Step/DiffRhythm 2/Stable Audio и checkpoints проверяются отдельно;
   - model license не гарантирует права на generated output, training data или отсутствие Content ID claims;
   - MusicGen должен оставаться явно обозначенным non-commercial demo backend, пока исходные условия это требуют.
6. Не присваивай вручную score или production-ready статус. Используй текущую versioned scoring model AtlasRepo и покажи score breakdown/evidence. Если данных недостаточно, отобрази честный unknown/review-required state.
7. Сделай публикацию устойчивой к следующему RepoScout auto-sync. Если `solutions/` в Arnon-hs/open-source сейчас не является поддерживаемым persisted source, добавь минимальный manifest/preservation contract и тест, вместо ручного изменения generated `index.json`, которое будет перезаписано.
8. На публичном UI используй существующий repo detail route (сейчас ожидается форма `/#/repos/<owner>/<name>`) или документированный новый clean route, если он уже предусмотрен архитектурой. Не ухудшай SSR/prerender/SEO: добавь canonical, title, description и индексируемый fallback для solution page.
9. Добавь события аналитики без чувствительных данных:
   - solution_view;
   - solution_repo_click;
   - solution_video_click;
   - solution_forum_click;
   - solution_dry_run_copy.
10. Покрой изменения тестами и проверь desktop, constrained-width и mobile, а также loading/empty/error states. Запусти repository quality gate, затем подготовь отдельную ветку/PR. Не выполняй production deploy и не меняй внешние сервисы без отдельного разрешения.

## Acceptance criteria

- AtlasRepo API возвращает ровно одну canonical запись `Arnon-hs/music-video` без дублей.
- Публичная solution/repo page открывается из каталога и содержит EN/RU/ZH.
- На странице работают ссылки на GitHub, AtlasRepo, Forum, YouTube и curated open-source solution.
- Отображаются подтверждённая лицензия кода, раздельные model-license caveats, hardware/API варианты и private-draft publication boundary.
- Ни один score, benchmark, license claim или publication result не добавлен без source evidence.
- RepoScout sync сохраняет solution и не удаляет curated page/manifest; это покрыто тестом.
- Пройдены unit/integration tests, link check, desktop/mobile browser checks и CI.
- PR содержит список изменённых файлов, screenshots, проверенные URLs, риски, rollback и evidence/assumptions/blockers.

## Owners и gates

- Product/content owner: подтверждает позиционирование, тексты EN/RU/ZH и место solution в навигации.
- Engineering owner: подтверждает schema, ingestion, dedupe, API/UI route и sync preservation.
- Legal/content gate: подтверждает фактическую code license и отдельные ограничения каждого model/checkpoint/media asset.
- Release gate: clean worktree, green CI, review, merge commit, затем отдельная production verification.

## Метрики после релиза

- unique solution views;
- repository/video/forum click-through rate;
- dry-run copy events;
- доля пользователей, дошедших от solution page до repo detail/installation docs;
- отсутствие duplicate records и broken links после минимум двух RepoScout sync cycles.

## Stop conditions

- Если нет чистого checkout, доступа к origin/main, schema/migration context или подтверждённого канонического publisher path — остановись и зафиксируй BLOCKED с точным недостающим условием.
- Если production/Zeabur/DB credentials недоступны, заверши локальный код, fixtures, tests и PR, но не заявляй, что production обновлён.
- Если лицензия модели или checkpoint не подтверждена официальным источником, пометь её review required; не делай разрешающий вывод по аналогии.

В финале раздели FACT / INFERENCE / ASSUMPTION / BLOCKER, приложи команды проверки и ссылки на PR/CI. Не называй задачу завершённой до merge и отдельной production verification.
```
