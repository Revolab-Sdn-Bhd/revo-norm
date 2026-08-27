# Pronunciation Mappings

Explicit pronunciation mappings applied **first** in the normalization pipeline, before any other transformation — highest priority, so mapped terms survive downstream steps (acronym expansion, abbreviation expansion, ...) intact.

Mappings resolve in **layers**; later layers win:

1. **Legacy global** — `PRONUNCIATION_MAPPINGS`, written by `add_custom_mapping()`. Process-wide; kept for backward compatibility.
2. **Named profile** — `"builtin"` (default, ships with the library), `"none"`, or one you register via `register_pronunciation_profile()`.
3. **`Config.pronunciations`** — per-call, the company personalization path. Last say.

Every layer may be **language-scoped**: `{"*": {...}, "ms": {...}}` — a flat dict applies to all languages. A `None` value **deletes** the term from all lower layers ("my TTS model handles this, leave it alone").

Setting `Config.pronunciation_overrides = False` disables all pronunciation behavior, every layer.

## Quick Start

```python
from revonorm import Config, normalize_text

# Company personalization: your product name, your pronunciation
cfg = Config()
cfg.pronunciations = {"RevoPay": "revo pay"}
normalize_text("Top up RevoPay now", language="ms", config=cfg)
# "top up revo pay now"

# Model-specific: this TTS model says "wee fee", fix it — for this call only
cfg = Config()
cfg.pronunciations = {"WiFi": "wai fai"}
normalize_text("Sambung WiFi", language="ms", config=cfg)

# Unmap a builtin entry — your model handles it natively
cfg = Config()
cfg.pronunciations = {"WiFi": None}
normalize_text("Connect WiFi", language="en", config=cfg)  # "WiFi" survives

# Disable the builtin layer entirely
cfg = Config(pronunciation_profile="none")

# Language-scoped: different spoken forms per language
cfg = Config()
cfg.pronunciations = {
    "*": {"WiFi": "wi fi"},
    "ms": {"Dr": "Doktor"},
}
```

## `Config.pronunciations` / `Config.pronunciation_profile`

Request-scoped layers 3 and 2. Prefer these over `add_custom_mapping()` in servers — no global mutation, safe under concurrency.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `pronunciation_profile` | `str` | `"builtin"` | Named profile: `"builtin"`, `"none"`, or a registered one |
| `pronunciations` | `dict` | `{}` | Flat (all languages) or scoped (`{"*": {...}, "ms": {...}}`). `None` values delete |

Config entries that look like abbreviation expansions ("YOLO" → "you only live once") emit a `UserWarning` — surfaced, not blocking. You own your output.

## `register_pronunciation_profile`

::: revonorm.pronunciation_mappings_compat.register_pronunciation_profile

Register a named mapping set at process startup — the natural home for TTS-model-specific tables and company dictionaries.

```python
from revonorm import Config, normalize_text, register_pronunciation_profile

# Your TTS model's quirks — registered once at server startup
register_pronunciation_profile("my-vits", {
    "*": {"WiFi": "wai fai", "nginx": "engine x"},
    "ms": {"Dato": "Dato Sri"},
})

cfg = Config(pronunciation_profile="my-vits")
normalize_text("Restart nginx dan WiFi", language="ms", config=cfg)
# "restart engine x dan wai fai"
```

`get_registered_profiles()` lists all registered names.

## `pronunciations_from_file`

::: revonorm.pronunciation_mappings_compat.pronunciations_from_file

Load scoped mappings from a JSON file — for deployment-driven config:

```json
{"*": {"WiFi": "wai fai"}, "ms": {"Dato": "Dato Sri"}}
```

```python
from revonorm import Config, pronunciations_from_file

cfg = Config()
cfg.pronunciations = pronunciations_from_file("/etc/myapp/pronunciations.json")
```

## Built-in Profile

The `"builtin"` profile ships with the library and is the default. Slimmed in v0.6.0:

### Technology Terms (all languages)

| Term | Spoken Form |
|------|-------------|
| `GUI` | `gooey` |
| `ASCII` | `as key` |
| `IEEE` | `I triple E` |
| `GIF` | `gif` |
| `WiFi` | `wi fi` |
| `iOS` | `I O S` |
| `UiTM` | `U I T M` |

### Malay Honorifics (`ms` / `id` only — v0.6.0 change)

| Term | Spoken Form |
|------|-------------|
| `Hj` | `Haji` |
| `Hjh` | `Hajah` |
| `Dr` / `Dr.` | `Doktor` |
| `Prof` / `Prof.` | `Profesor` |
| `Dato` / `Dato'` | `Dato` (identity — protects the title from letter-splitting) |
| `Datin` | `Datin` (identity) |
| `Datuk` | `Datuk` (identity) |

Previously honorifics applied to every language; they now apply to Malay/Indonesian text only, so English output stops inheriting them. The `bias` → `bai yers` OCR patch was removed — fix OCR errors at the input source.

### Terms NOT in Pronunciation Mappings

Handled by the generalized `expand_acronym()` rule instead:

- `JSON`, `JPEG`, `PNG` → consonant-vowel-consonant pattern ("J son")
- `API`, `GPU`, `CPU` → letter-by-letter
- `AI`, `ML`, `LLM`, `DL`, `NLP`, `RL` → letter-by-letter
- `NASA` → preserved as-is

## `add_custom_mapping` (legacy)

::: revonorm.pronunciation_mappings_compat.add_custom_mapping

Writes the process-global legacy table — **layer 1**. Still functional, still raises `ValueError` on expansion-looking mappings. Prefer `Config.pronunciations` in servers: it is request-scoped, layerable, and warn-only.

```python
from revonorm.pronunciation_mappings import add_custom_mapping

add_custom_mapping("SQL", "sequel")        # ✅ pronunciation
add_custom_mapping("YOLO", "you only live once")  # ❌ raises ValueError
```

## `get_pronunciation_mappings`

::: revonorm.pronunciation_mappings_compat.get_pronunciation_mappings

Legacy single-layer view: legacy global + builtin profile for a language.

## `apply_pronunciation_mappings`

::: revonorm.pronunciation_mappings_compat.apply_pronunciation_mappings

Apply a resolved table to text — whole-word, case-insensitive, longest term first. Called internally with the resolved layers; pass `mappings=` to use directly.

## `remove_preservation_markers`

::: revonorm.pronunciation_mappings_compat.remove_preservation_markers

Strip `__PRESERVED__...__` markers left by the pipeline.

## Debugging Which Layer Fired

`normalize_text_detailed()` records every fired pronunciation replacement:

```python
from revonorm import normalize_text_detailed

result = normalize_text_detailed("Sambung WiFi sekarang", language="ms")
result.mappings
# [{'original': 'WiFi', 'normalized': 'wi fi', 'rule': 'pronunciation'}]
```

## Shape Reference

```python
# Flat — all languages
{"WiFi": "wai fai"}

# Scoped — "*" plus any language code
{"*": {"WiFi": "wai fai"}, "ms": {"Dr": "Doktor"}, "id": {"Dr": "Dokter"}}

# Deletion — removes the term from lower layers
{"WiFi": None}
{"ms": {"WiFi": None}}   # delete for ms only
```

Invalid shapes fail loudly: scope keys must map to dicts; a top-level dict whose keys are all language codes with scalar values is rejected as a likely scoping mistake (`{"ms": "Doktor"}` raises `TypeError`).
