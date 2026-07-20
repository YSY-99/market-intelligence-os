# Модель данных

Каноническая карточка находится в `data/sources.json`; одна строка `data/sources.jsonl` содержит одну такую карточку.

## Основные поля

| Поле | Тип | Назначение |
|---|---|---|
| `schema_version` | string | Версия контракта |
| `id` | string | Стабильный slug источника |
| `company` | string | Отображаемое имя |
| `category` | string | Одна из 36 контролируемых категорий |
| `subcategory` | string | Исходный `Source_Type` |
| `description` | string | Краткое описание |
| `best_for` | string[] | Практические сценарии использования |
| `topics` | string[] | Нормализованные темы |
| `keywords` | string[] | Автоматически извлечённые лексемы |
| `access` | object | Исходное описание и флаги free/paid/gated |
| `urls` | object | Website, research и blog URL |
| `flagship_resources` | object[] | Главный отчёт или ресурс |
| `priority` | string | high / medium / low |
| `authority_score` | number | Временный proxy, 0–10 |
| `publisher` | string | Издатель или ответственная организация |
| `data_origin` | string | primary / secondary / user_generated / owned / unspecified |
| `access_methods` | string[] | api / bulk download / web / manual и другие способы |
| `business_stages` | string[] | Стадии бизнеса, где источник применим |
| `decision_types` | string[] | Решения, которые поддерживает источник |
| `geographies` | string[] | Географическое покрытие |
| `geographic_granularity` | string[] | Country / state / county / city и т. п. |
| `industry_codes` | string[] | NAICS / NACE / SIC / CPV и другие классификации |
| `machine_readable` | boolean/null | Есть ли структурированный машинный доступ |
| `integration` | object | API URL, документация и тип авторизации |
| `integration.connector_status` | string | not_implemented / manual / available / degraded / disabled |
| `terms_or_scraping_restrictions` | string | Ограничения API, лицензии и автоматизированного сбора |
| `contribution` | object | Статус, submitter, reviewer и provenance URL |
| `verification` | object | Статус проверки metadata и отдельная дата обновления контента |
| `last_verified` | date | Дата последней проверки metadata карточки; freshness-бонус применяется только при `verification.status=verified` |
| `metadata.inferred_fields` | string[] | Поля, созданные автоматически |

Поля `synonyms`, `search_examples`, `example_prompts`, `when_not_to_use` и `related_sources` уже зарезервированы, но не заполняются выдуманными значениями. Их следует обогащать вручную или через отдельный проверяемый pipeline.

## Отдельный реестр отчётов

Отчёты не стоит бесконечно вкладывать в карточку компании. Следующая схема должна храниться отдельно и связываться через `source_id`:

```json
{
  "id": "revenuecat-state-of-subscription-apps-2026",
  "source_id": "revenuecat",
  "title": "State of Subscription Apps 2026",
  "url": "https://example.com/report",
  "published_at": "2026-03-01",
  "retrieved_at": "2026-07-20",
  "topics": ["conversion", "retention", "ltv"],
  "geographies": ["global"],
  "industries": ["mobile apps"],
  "methodology": null,
  "content_hash": null,
  "status": "available"
}
```

Это позволит выбирать свежий отчёт независимо от общего рейтинга компании и отслеживать обновления без перезаписи истории.
