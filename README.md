# Market Intelligence OS

Локальная база знаний и объяснимый маршрутизатор, который по исследовательскому вопросу выбирает наиболее подходящие источники из каталога. English quick start is included below.

Текущая версия `0.1` не делает вид, что уже прочитала интернет. Она решает первый слой задачи: понимает намерение запроса, ранжирует источники, объясняет выбор и отдаёт правильную ссылку. Результат можно использовать вручную, из shell-скриптов или передавать в AI-агента как JSON.

## Что уже работает

- импорт исходного CSV в канонические `JSON` и `JSONL`;
- 213 источников и 36 нормализованных категорий;
- запросы на русском и английском;
- прозрачный скоринг по намерению, тематике, описанию, приоритету, условному authority score и свежести проверки;
- фильтр источников с бесплатным доступом;
- текстовый и машинный JSON-вывод;
- просмотр полной карточки источника;
- автоматические тесты без внешних Python-зависимостей.

## Быстрый старт

Требуется Python 3.9+.

```bash
git clone https://github.com/YSY-99/market-intelligence-os.git
cd market-intelligence-os
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
market-intel search "mobile subscription conversion benchmark" --limit 5
```

Пересобрать базу из repository-owned каталогов:

```bash
PYTHONPATH=src python3 scripts/build_kb.py \
  catalog/market_intelligence_sources.csv \
  catalog/public_primary_sources.csv \
  catalog/global_public_sources.csv \
  catalog/community_reviewed_sources.csv \
  --output-dir data
```

Найти источники:

```bash
./bin/market-intel search "бенчмарк удержания для мобильных подписок" --limit 5
```

Только источники, у которых есть бесплатный доступ:

```bash
./bin/market-intel search "consumer search behavior" --free-only
```

JSON для Claude, Codex или другого агента:

```bash
./bin/market-intel search "AI industry trends and investment" --limit 5 --json
```

Посмотреть карточку источника и список поддерживаемых намерений:

```bash
./bin/market-intel inspect revenuecat
./bin/market-intel intents
```

После установки те же команды доступны как `market-intel`. Поддерживаемый Python API показан в [docs/api.md](docs/api.md) и [examples/search_sources.py](examples/search_sources.py).

## English quick start

Market Intelligence OS routes a business research question to relevant sources and explains the ranking. It does not fetch or summarize third-party content in v0.1.

```bash
python -m pip install -e .
market-intel search "government procurement Germany" --limit 5 --json
python examples/search_sources.py
```

## Как устроен рабочий цикл

1. Seed-каталоги редактируются в `catalog/` — это удобный human-editable source of truth.
2. `scripts/build_kb.py` валидирует строки и создаёт `data/sources.json` и `data/sources.jsonl`.
3. CLI определяет категории намерения и оценивает релевантность каждого источника.
4. Пользователь или следующий AI-агент открывает рекомендованные URL и уже там выполняет фактическое исследование с цитатами.

Мы не отказываемся от CSV полностью: CSV удобен для массового редактирования, а JSON лучше подходит как runtime-формат для агентов. Генерируемые поля явно отмечены в `metadata.inferred_fields`.

## Проверка

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/evaluate_router.py
python3 scripts/check_repository.py
```

В `eval/routing_queries.json` лежит regression-набор. Сейчас маршрутизация проходит 53/53 сценария: исходные digital-задачи, новые глобальные домены, русские/английские запросы, jurisdiction-specific источники и безопасные negative cases без подходящей юрисдикции.

Проверить покрытие и backlog метаданных:

```bash
PYTHONPATH=src python3 scripts/coverage_report.py
```

## Общественные вклады

Новые источники не попадают в production автоматически. Произвольный внешний CSV не может сам себя одобрить полями `reviewed`. Возьмите `catalog/community_submission_template.csv`, заполните источник и запустите:

```bash
PYTHONPATH=src python3 scripts/validate_submission.py path/to/proposal.csv
```

Требования к provenance, лицензиям, ограничениям сбора и редакционной проверке описаны в [CONTRIBUTING.md](CONTRIBUTING.md).

## Статус публичного релиза

Код распространяется по Apache-2.0, а созданные проектом метаданные каталога — по CC BY 4.0. Ссылки в каталоге не передают проекту права на содержимое внешних сайтов и отчётов; подробнее см. `NOTICE` и `LICENSE-DATA`.

Перед включением любого сетевого connector необходимо отдельно проверить права конкретного источника. Пустое поле лицензии или `review_required` не означает разрешение на копирование либо автоматический сбор.

## License

- Software: [Apache License 2.0](LICENSE).
- Original catalog metadata: [Creative Commons Attribution 4.0 International](LICENSE-DATA).
- Third-party reports, APIs, websites, datasets, and trademarks remain under their owners' terms; see [NOTICE](NOTICE).

## Следующие версии

Наиболее полезная последовательность развития:

1. Реестр отдельных отчётов с датой публикации, темами и статусом доступности.
2. Набор проверочных запросов и метрики качества ранжирования (`Precision@5`, `MRR`).
3. Адаптеры получения страниц и документов с обязательными цитатами.
4. Полнотекстовый индекс содержимого отчётов; embeddings добавлять только если лексического поиска станет недостаточно.
5. Тонкий MCP-сервер с инструментами `search_sources`, `get_source` и `research` поверх того же ядра.

Подробности: [архитектура](docs/architecture.md), [модель данных](docs/data-model.md), [план реализации](docs/plans/2026-07-20-market-intelligence-os.md).
