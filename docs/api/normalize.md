# `normalize_text`

The primary entry point for text normalization.

::: revo_norm.normalize_text

## Parameters

### `text` {: #text }

`str` — The input text to normalize. Leading and trailing whitespace is stripped before processing. If the string is empty after stripping, an empty string is returned immediately.

### `language` {: #language }

`str`, default `"en"` — Target language code. Must be one of the supported codes (see [Languages](../languages.md), exposed as `SUPPORTED_LANGUAGES`); an unrecognized code raises `ValueError`. Case and surrounding whitespace are ignored (`"ID"`, `" en "` are accepted).

| Value | Description |
|-------|-------------|
| `"en"` | English normalization (contractions, numbers via `inflect`, English date/time formats) |
| `"ms"` | Malay normalization (Malay grammar, numbers via `num2word_ms`, Malay-specific features) |

### `profile` {: #profile }

`str | None`, default `None` — A preset configuration profile. When provided, determines which feature groups are enabled.

| Profile | Description |
|---------|-------------|
| `"minimal"` | Spacing normalization only |
| `"basic"` | Spacing + acronyms + abbreviations + elongated + Malay-local + special chars |
| `"standard"` | All features enabled (same as default when `profile=None`) |
| `"aggressive"` | All features enabled + strips `[...]` content |

When `None`, the standard profile (all features on) is used.

### `disable` {: #disable }

`list[str] | None`, default `None` — A list of feature names to turn off. Feature names correspond to fields on [`Config`](config.md). Unknown names are ignored.

Common feature names:

- `"acronyms"` — Disable acronym expansion (I.B.M., API, etc.)
- `"measurements"` — Disable measurement normalization (5km, 10kg, etc.)
- `"temperature"` — Disable temperature normalization (25C, -5F, etc.)
- `"fractions"` — Disable fraction normalization (3/4, 10/4, etc.)
- `"dates"` — Disable date-to-spoken conversion
- `"times"` — Disable time-to-spoken conversion
- `"spacing"` — Disable whitespace normalization
- `"abbreviations"` — Disable abbreviation expansion (currently a no-op)
- `"elongated"` — Disable elongated word normalization
- `"special_chars"` — Disable special character replacement (&, +, %, etc.)
- `"pronunciation_overrides"` — Disable pronunciation overrides

### `**kwargs` (legacy flags)

Legacy boolean flags accepted for backward compatibility. Using any of these emits a `DeprecationWarning`.

Supported legacy names:

`normalize_spacing`, `fix_dot_letters`, `sound_words_field`, `apply_pronunciation_overrides_flag`, `expand_abbreviations_flag`, `expand_acronyms_flag`, `normalize_elongated_flag`, `normalize_fractions_flag`, `normalize_x_kali_flag`, `normalize_temperature_flag`, `normalize_ic_flag`, `normalize_measurements_flag`, `normalize_hari_bulan_flag`, `normalize_hijri_flag`, `extract_entities_first`, `config`

## Return Value

`str` — The normalized text, ready for TTS processing.

## Examples

### Basic usage

```python
from revo_norm import normalize_text

# English
result = normalize_text("The API is fast and costs $5.50", language="en")
# "The A P I is fast and costs five dollar fifty cents"

# Malay
result = normalize_text("RM30K untuk projek ML", language="ms")
# "tiga puluh ribu ringgit untuk projek M L"
```

### With a profile

```python
from revo_norm import normalize_text

# Minimal — only whitespace cleanup
result = normalize_text("The  API  is  fast", language="en", profile="minimal")
# "The API is fast"

# Basic — adds acronym/abbreviation/special chars
result = normalize_text("5km & 10kg", language="en", profile="basic")
```

### With disabled features

```python
from revo_norm import normalize_text

# Keep acronyms as-is (no letter splitting)
result = normalize_text("Build the API with ML", language="en", disable=["acronyms"])
# "Build the API with ML"

# Disable multiple features
result = normalize_text(
    "25C and 3/4 of 5km",
    language="en",
    disable=["temperature", "fractions", "measurements"],
)
```

### Legacy flags (deprecated)

```python
import warnings

# Legacy flags still work but emit DeprecationWarning
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    result = normalize_text(
        "25C outside",
        language="en",
        normalize_temperature_flag=False,
    )
```

## Pipeline Steps

When `normalize_text()` is called, the following steps execute in order:

1. **Currency suffix expansion** — `RM30K` becomes `RM30000`, `RM1M` becomes `RM1000000`
2. **Entity extraction** — Entities are detected and replaced with `<<<TYPE_ID>>>` placeholders
3. **Pronunciation mappings** — Explicit mappings (e.g., `GUI` to "gooey") applied first
4. **Placeholder stashing** — Entity placeholders are replaced with safe alphabetic tokens
5. **Feature-gated processing**:
    - Pronunciation overrides
    - Elongated word normalization
    - Measurement normalization
    - X-kali normalization
    - Language-specific normalization (per the selected language)
    - Spacing normalization
    - Sound word removal
    - Abbreviation expansion
    - Acronym expansion
    - Comma insertion for repeated words
    - Special character replacement
6. **Entity restoration** — Placeholders are restored as spoken form
