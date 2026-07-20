# Quickstart Guide

Get started with revo-norm in under 5 minutes.

## Basic Usage

The library exposes a single entry point — `normalize_text()` — that handles the entire pipeline.

```python
from revo_norm import normalize_text
```

Pass your text and specify the language code (see [Languages](languages.md) for the full list):

```python
# English
result = normalize_text("The meeting is at 3:30 pm on 15/08/2025", language="en")
print(result)
# "The meeting is at three thirty p m on fifteen of August twenty twenty-five"

# Malay
result = normalize_text("RM450 untuk projek ini", language="ms")
print(result)
# "empat ratus lima puluh ringgit untuk projek ini"
```

!!! note
    Malay text often mixes in English terms (code-mixing). Revo-norm handles this naturally — English terms in Malay sentences are preserved unless a specific normalization rule applies.

## Configuration Profiles

Revo-norm ships with four preset profiles that control how aggressively text is normalized.

```python
# Use a profile via the profile parameter
normalize_text(text, language="en", profile="standard")
```

### Profile Comparison

| Feature | `minimal` | `basic` | `standard` | `aggressive` |
|---------|-----------|---------|------------|--------------|
| Spacing cleanup | Yes | Yes | Yes | Yes |
| Acronyms | — | Yes | Yes | Yes |
| Abbreviations | — | Yes | Yes | Yes |
| Elongated words | — | Yes | Yes | Yes |
| Malay-local features | — | Yes | Yes | Yes |
| Special characters | — | Yes | Yes | Yes |
| Numbers | — | — | Yes | Yes |
| Dates | — | — | Yes | Yes |
| Times | — | — | Yes | Yes |
| Temperature | — | — | Yes | Yes |
| Fractions | — | — | Yes | Yes |
| Measurements | — | — | Yes | Yes |
| IC numbers | — | — | Yes | Yes |
| Hijri years | — | — | Yes | Yes |
| Hari bulan | — | — | Yes | Yes |
| X-kali | — | — | Yes | Yes |
| Pronunciation overrides | — | — | Yes | Yes |
| Strip `[...]` content | — | — | — | Yes |

When no `profile` is specified, `standard` is used (all features enabled).

### When to Use Each Profile

!!! tip "`minimal`"
    Best for text that is already mostly clean. Only collapses extra whitespace. Use when you need raw text with no transformations.

!!! tip "`basic`"
    Good for conversational text where you want acronym expansion and basic cleanup, but don't need number-to-words or entity normalization.

!!! tip "`standard` (default)"
    The right choice for most TTS applications. Full normalization with entity protection for dates, currency, and URLs.

!!! tip "`aggressive`"
    Everything in standard **plus** strips all bracketed content like `[laughter]`, `[music]`, `[applause]`. Best for social media or noisy transcripts where `[...]` annotations are common.

## Disabling Specific Features

Use the `disable` parameter to turn off individual features without changing the overall profile.

```python
# Disable acronym expansion
normalize_text("The API is fast", language="en", disable=["acronyms"])
# "The API is fast"  (acronym preserved instead of expanded to "A P I")

# Disable multiple features
normalize_text(
    "Temperature is 25C and 3/4 done",
    language="en",
    disable=["temperature", "fractions"],
)
# Temperature and fractions left as-is
```

### Available Feature Names

These are the feature names you can pass in the `disable` list:

| Feature Name | Controls |
|-------------|----------|
| `acronyms` | Acronym expansion (`IBM` → "I B M") |
| `abbreviations` | Abbreviation expansion |
| `spacing` | Whitespace normalization |
| `measurements` | Measurement units (`5km` → "five kilometers") |
| `dates` | Date recognition and conversion |
| `times` | Time recognition and conversion |
| `temperature` | Temperature normalization (`25C` → "twenty-five celsius") |
| `fractions` | Fraction normalization (`3/4` → "three over four") |
| `x_kali` | Malay x-kali multiplier |
| `ic` | Malaysian IC number normalization |
| `hari_bulan` | Malay hari bulan format |
| `hijri` | Hijri year conversion |
| `elongated` | Elongated word normalization (`soooo` → "so") |
| `malay_local` | Malay-local features |
| `special_chars` | Special character replacement (`&` → "and", `%` → "percent") |
| `pronunciation_overrides` | Built-in pronunciation overrides |

## Common Examples

### Currency

```python
# English — K-suffix expansion
normalize_text("The budget is RM50K", language="en")
# "The budget is fifty thousand ringgit"

# Malay — full spoken form
normalize_text("Harga RM450", language="ms")
# "Harga empat ratus lima puluh ringgit"

# Large suffixes (M = million, B = billion, T = trillion)
normalize_text("Revenue hit $1.5M", language="en")
# "Revenue hit one million, five hundred thousand dollar"
```

### Dates

```python
# DD/MM/YYYY format
normalize_text("Due on 15/08/2025", language="en")
# "Due on fifteen of August twenty twenty-five"

# ISO format (YYYY-MM-DD)
normalize_text("Deadline: 2025-08-15", language="en")
# "Deadline: August the fifteenth, twenty twenty-five"
```

!!! warning
    Date parsing uses heuristics for ambiguous formats (e.g., `01/02/2025` could be DD/MM or MM/DD). The parser assumes DD/MM ordering. If your input uses MM/DD, results may differ.

### Times

```python
# With meridiem
normalize_text("Meeting at 3:30 pm", language="en")
# "Meeting at three thirty p m"

# 24-hour format
normalize_text("Departs at 14:00", language="en")
# "Departs at fourteen zero"
```

### Acronyms

```python
# Letter-by-letter splitting
normalize_text("IBM announced results", language="en")
# "I B M announced results"

# Pronounceable acronyms
normalize_text("Parse JSON data", language="en")
# "Parse J son data"

# Preserved acronyms (well-known words)
normalize_text("NASA launched", language="en")
# "NASA launched"
```

### Temperature

```python
# Celsius
normalize_text("It is 25C outside", language="en")
# "It is twenty-five celsius outside"

# Fahrenheit
normalize_text("Temperature is 98F", language="en")
# "Temperature is ninety-eight fahrenheit"
```

### Fractions

```python
# Common fractions
normalize_text("Pour 3/4 cup of water", language="en")
# "Pour three over four cup of water"

# Other fractions
normalize_text("Use 1/2 teaspoon", language="en")
# "Use one over two teaspoon"
```

### Measurements

```python
# Distance
normalize_text("Run 5km every day", language="en")
# "Run five kilometers every day"

# Weight
normalize_text("Buy 10kg of rice", language="en")
# "Buy ten kilogram of rice"

# Data
normalize_text("Download 3GB file", language="en")
# "Download three gigabyte file"
```

### Malay-Specific

```python
# Currency in Malay
normalize_text("RM450 untuk projek ini", language="ms")
# "empat ratus lima puluh ringgit untuk projek ini"

# X-kali multiplier (Malay)
normalize_text("5x ganda", language="ms")
# "lima kali ganda"

# Temperature in Malay
normalize_text("Suhu 25C hari ini", language="ms")
# "Suhu dua puluh lima celcius hari ini"
```

### Custom Pronunciation Mappings

Add your own pronunciation overrides. These take the highest priority in the pipeline and are applied before any other transformation.

```python
from revo_norm import normalize_text, add_custom_mapping

# Add a custom mapping
add_custom_mapping("YOLO", "you only live once", "en")

normalize_text("YOLO approach", language="en")
# "you only live once approach"
```

!!! warning
    `add_custom_mapping()` modifies module-level state and is **not thread-safe**. Add all custom mappings at application startup, before any calls to `normalize_text()`.

## Next Steps

- [API Reference](api/normalize.md) — full function signatures and parameters
- [Features](features/currency.md) — detailed guides for each normalization feature
