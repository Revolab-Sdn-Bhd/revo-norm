# Entity Extraction

The entity extraction system protects structured patterns (URLs, emails, dates, etc.) from being mangled by other normalization steps.

## How It Works

The system uses a three-phase approach:

1. **Extract** — Scan text for entity patterns, replace each match with a `<<<TYPE_ID>>>` placeholder
2. **Process** — Apply normalization steps to the remaining text (placeholders are untouched)
3. **Restore** — Replace placeholders with the spoken form of each entity

This prevents cascading transformations. For example, without entity extraction, `"RM 450000"` could be transformed as:

> `"RM"` → `"R M"` (acronym expansion) → `"R meter"` (abbreviation expansion)

With entity extraction, `"RM 450000"` is replaced with `<<<CURRENCY_1>>>` before any other processing, then restored as `"empat ratus lima puluh ribu ringgit"` at the end.

## `EntityExtractor`

::: revonorm.compat.EntityExtractor

### Constructor

```python
from revonorm.entity_extractor import EntityExtractor

extractor = EntityExtractor()
```

Creates a new extractor instance with pre-compiled patterns for all entity types.

### `extract(text, enabled_entities)`

::: revonorm.compat.EntityExtractor.extract

Extract entities from text and replace them with placeholders.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `text` | `str` | required | Input text to extract entities from |
| `enabled_entities` | `list[EntityType] | None` | `None` | List of entity types to extract. `None` extracts all types. |

**Returns:** `tuple[str, list[Entity]]` — A tuple of:

- `str` — The protected text with entities replaced by `<<<TYPE_ID>>>` placeholders
- `list[Entity]` — The list of extracted `Entity` objects, sorted by position

**Placeholder format:** `<<<TYPE_ID>>>`

- `TYPE` is the uppercase entity type name (e.g., `URL`, `DATE`, `CURRENCY`)
- `ID` is a sequential integer starting from 1

Example placeholders: `<<<URL_1>>>`, `<<<DATE_2>>>`, `<<<CURRENCY_3>>>`

```python
extractor = EntityExtractor()

protected, entities = extractor.extract(
    "Send email to user@example.com about RM500 on 15/08/2025"
)

# protected: "Send email to <<<EMAIL_1>>> about <<<CURRENCY_2>>> on <<<DATE_3>>>"
# entities contains 3 Entity objects with original text and positions
```

### `restore(text, language)`

::: revonorm.compat.EntityExtractor.restore

Convert entity placeholders back to spoken form.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `text` | `str` | required | Text with entity placeholders |
| `language` | `str` | required | Target language code (see [Languages](../languages.md)) |

**Returns:** `str` — Text with all entity placeholders replaced by their spoken form.

```python
extractor = EntityExtractor()

protected, _ = extractor.extract("Price is RM500")
# protected: "Price is <<<CURRENCY_1>>>"

# ... other processing on protected text ...

result = extractor.restore(protected, "ms")
# result: "Price is lima ratus ringgit"
```

### `entities` attribute

`list[Entity]` — The list of entities found during the most recent `extract()` call. This list is cleared and repopulated each time `extract()` is called.

## `EntityType`

::: revonorm.compat.EntityType

Enum of all entity types that can be extracted. Each value is a lowercase string.

| Type | Value | What It Detects |
|------|-------|-----------------|
| `URL` | `"url"` | HTTP/HTTPS/FTP URLs, IP addresses with ports, domain names |
| `EMAIL` | `"email"` | Email addresses (`user@example.com`) |
| `DATE` | `"date"` | DD/MM/YYYY, YYYY-MM-DD, DD Month YYYY, Month DD, YYYY |
| `TIME` | `"time"` | HH:MM, HH:MM AM/PM, HH:MM:SS |
| `CURRENCY` | `"currency"` | RM, USD, EUR, GBP, MYR, $, £, € with amounts and optional K/M/B/T suffixes |
| `FRACTION` | `"fraction"` | Numeric fractions (3/4, 10/4) — excludes date-like patterns |
| `TEMPERATURE` | `"temperature"` | Temperature values (25C, -5F, 100K, 37.5C) |
| `IC` | `"ic"` | Malaysian IC numbers (YYMMDD-SS-NNNN) |
| `HARI_BULAN` | `"hari_bulan"` | Malay day-of-month format (e.g., `15hb`) |
| `HIJRI` | `"hijri"` | Hijri years (e.g., `1446H`) |
| `X_KALI` | `"x_kali"` | Multipliers (e.g., `5x`, `10X`) |

```python
from revonorm.entity_extractor import EntityType

# Access entity type values
EntityType.URL       # <EntityType.URL: 'url'>
EntityType.CURRENCY  # <EntityType.CURRENCY: 'currency'>
EntityType.DATE      # <EntityType.DATE: 'date'>
```

## `Entity`

::: revonorm.compat.Entity

Dataclass representing an extracted entity.

| Field | Type | Description |
|-------|------|-------------|
| `type` | `EntityType` | The entity type (URL, EMAIL, DATE, etc.) |
| `text` | `str` | The original matched text from the input |
| `start` | `int` | Start position in the original text |
| `end` | `int` | End position in the original text |
| `metadata` | `dict` | Additional information (language, format, etc.) — defaults to `{}` |
| `placeholder_id` | `int` | ID used for placeholder generation — defaults to `0` |

```python
from revonorm.entity_extractor import Entity, EntityType

entity = Entity(
    type=EntityType.URL,
    text="https://example.com",
    start=5,
    end=24,
    placeholder_id=1,
)

entity.type           # EntityType.URL
entity.text           # "https://example.com"
entity.placeholder_id # 1
```

## Extraction Order

Entities are extracted in the following order (most specific first to prevent false matches):

1. **URL** — Must be first to prevent IP addresses from being matched by other patterns
2. **EMAIL** — Must be early to prevent `@` from being replaced by special chars
3. **CURRENCY** — Must be early to protect currency codes from acronym/abbreviation expansion
4. **DATE** — Protects slash-format dates from fraction pattern
5. **TIME** — Protects colon-format times from other processing
6. **TEMPERATURE** — Matches `25C`, `-5F`, etc.
7. **FRACTION** — Matches `3/4`, `10/4` (with negative lookahead to skip dates)
8. **X_KALI** — Matches `5x`, `10X`
9. **IC** — Matches Malaysian IC format `YYMMDD-SS-NNNN`
10. **HARI_BULAN** — Matches `15hb`, `3HB`
11. **HIJRI** — Matches `1446H`, `1445h`
