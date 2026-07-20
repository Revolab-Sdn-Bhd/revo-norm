# Pronunciation Mappings

Explicit pronunciation mappings that are applied **first** in the normalization pipeline, before any other transformations. This gives them the highest priority and prevents downstream steps (acronym expansion, abbreviation expansion, etc.) from altering mapped terms.

## How It Works

1. When `normalize_text()` is called, pronunciation mappings are applied immediately after entity extraction
2. Each mapping is a whole-word, case-insensitive match
3. Mappings are sorted by key length (longest first) to handle overlapping terms correctly
4. The same mappings are used across languages, reflecting the code-mixed nature of Malaysian text

## `add_custom_mapping`

::: revo_norm.pronunciation_mappings.add_custom_mapping

Add a custom pronunciation mapping to the global mappings dictionary.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `term` | `str` | required | The term to map (e.g., `"YOLO"`) |
| `pronunciation` | `str` | required | The spoken form (e.g., `"you only live once"`) |
| `language` | `str` | `"en"` | Language code — currently ignored; mappings apply across all languages |

**Returns:** `None`

!!! warning "Thread Safety"
    `add_custom_mapping` modifies the global `PRONUNCIATION_MAPPINGS` dictionary. It is not thread-safe. Call it during application startup, not from concurrent request handlers.

```python
from revo_norm.pronunciation_mappings import add_custom_mapping

# Add a custom mapping
add_custom_mapping("YOLO", "you only live once", "en")

# Now normalize_text will use it
from revo_norm import normalize_text
result = normalize_text("YOLO approach", language="en")
# "you only live once approach"
```

## `get_pronunciation_mappings`

::: revo_norm.pronunciation_mappings.get_pronunciation_mappings

Get a copy of the current pronunciation mappings dictionary.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `language` | `str` | `"en"` | Language code — currently ignored; same mappings returned for all languages |

**Returns:** `dict[str, str]` — A copy of the pronunciation mappings. Modifications to the returned dict do not affect the global mappings.

```python
from revo_norm.pronunciation_mappings import get_pronunciation_mappings

mappings = get_pronunciation_mappings()
# {"GUI": "gooey", "WiFi": "why fi", "ASCII": "as key", ...}
```

## Built-in Mappings

The following mappings are included by default:

### Text Corrections / OCR Fixes

| Term | Spoken Form |
|------|-------------|
| `bias` | `bai yers` |

### Malay Honorifics

| Term | Spoken Form |
|------|-------------|
| `Hj` | `Haji` |
| `Hjh` | `Hajah` |
| `Dr` | `Doktor` |
| `Dr.` | `Doktor` |
| `Prof` | `Profesor` |
| `Prof.` | `Profesor` |
| `Dato` | `Dato` |
| `Dato'` | `Dato` |
| `Datin` | `Datin` |
| `Datuk` | `Datuk` |

### Technology Terms

| Term | Spoken Form |
|------|-------------|
| `GUI` | `gooey` |
| `ASCII` | `as key` |
| `IEEE` | `I triple E` |
| `GIF` | `gif` |
| `WiFi` | `why fi` |
| `iOS` | `I O S` |

### Terms NOT in Pronunciation Mappings

The following terms are handled by the generalized `expand_acronym()` rule instead, not by explicit mappings:

- `JSON` → Handled by generalized rule (consonant-vowel-consonant pattern)
- `JPEG` → Handled by generalized rule
- `PNG` → Handled by generalized rule
- `API`, `GPU`, `CPU` → Split letter-by-letter by `expand_acronym()`
- `AI`, `ML`, `LLM`, `DL`, `NLP`, `RL` → Split letter-by-letter by `expand_acronym()`
- `NASA` → Preserved as-is by `expand_acronym()`

## `apply_pronunciation_mappings`

::: revo_norm.pronunciation_mappings.apply_pronunciation_mappings

Apply all pronunciation mappings to text. Called internally by `normalize_text()`. You typically do not need to call this directly.

```python
from revo_norm.pronunciation_mappings import apply_pronunciation_mappings

result = apply_pronunciation_mappings("Build GUI interface", "en")
# "Build gooey interface"
```

## `remove_preservation_markers`

::: revo_norm.pronunciation_mappings.remove_preservation_markers

Remove `__PRESERVED__...__` markers from text. Called at the end of the normalization pipeline to clean up any markers that were inserted to protect terms from further transformation.

```python
from revo_norm.pronunciation_mappings import remove_preservation_markers

result = remove_preservation_markers("Train __PRESERVED__ML__ model")
# "Train ML model"
```

## `add_custom_mapping`

::: revo_norm.pronunciation_mappings.add_custom_mapping

!!! warning "TTS-Only: Pronunciation, not Expansion"
    Mappings must represent **how a term sounds when spoken**, not what it stands for.

    ```python
    # ✅ Correct — pronunciation (how you say it)
    add_custom_mapping("SQL", "sequel")

    # ❌ Wrong — abbreviation expansion (what it means)
    add_custom_mapping("YOLO", "you only live once")  # raises ValueError
    ```

    The validation rejects mappings where the replacement looks like an expansion:
    - Short abbreviations (≤4 chars) expanded to 3+ words
    - Replacements 3x+ longer than the original
    - Replacements containing connector words ("of", "the", "and") suggesting a full name/title

    If you're certain your mapping is valid pronunciation, set it directly:
    ```python
    from revo_norm.pronunciation_mappings import PRONUNCIATION_MAPPINGS
    PRONUNCIATION_MAPPINGS["YOLO"] = "you only live once"
    ```

## Examples

### Custom mapping for a tech term

```python
from revo_norm import normalize_text
from revo_norm.pronunciation_mappings import add_custom_mapping

add_custom_mapping("SQL", "sequel")

result = normalize_text("Query the SQL database", language="en")
# "Query the sequel database"
```

### Custom mapping for a brand name

```python
from revo_norm import normalize_text
from revo_norm.pronunciation_mappings import add_custom_mapping

add_custom_mapping("KDE", "K D E")

result = normalize_text("Launch KDE desktop", language="en")
# "Launch K D E desktop"
```

### Inspecting current mappings

```python
from revo_norm.pronunciation_mappings import get_pronunciation_mappings

mappings = get_pronunciation_mappings()
for term, spoken in sorted(mappings.items()):
    print(f"{term} → {spoken}")
```
