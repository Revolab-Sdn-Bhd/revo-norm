# Time Normalization

## Overview

Time normalization converts written time expressions into their spoken form for TTS. It supports 12-hour and 24-hour formats, optional seconds, and AM/PM indicators with output in the selected language.

Times are extracted as entities early in the pipeline to prevent the normalizer from misinterpreting the colon separator.

## Supported Formats

| Format | Example | Notes |
|--------|---------|-------|
| HH:MM | `3:30` | Basic time without AM/PM |
| HH:MM AM/PM | `3:30 pm` | With meridian indicator |
| HH:MM A.M./P.M. | `3:30 p.m.` | Dotted meridian variant |
| HH:MM:SS | `14:30:45` | With seconds |

## English Output

```python
from revonorm import normalize_text

# Basic time (HH:MM)
normalize_text("3:30", language="en")
# "three thirty"

# Time with AM
normalize_text("3:30 am", language="en")
# "three thirty a m"

# Time with PM
normalize_text("11:59 PM", language="en")
# "eleven fifty nine p m"

# Time with seconds
normalize_text("14:30:45", language="en")
# "fourteen thirty forty five"

# Midnight and noon special cases
normalize_text("00:00", language="en")
# "midnight"

normalize_text("12:00", language="en")
# "noon"
```

## Malay Output

Malay uses `pagi` (morning) for AM and `petang` (afternoon) for PM.

```python
from revonorm import normalize_text

# Basic time (HH:MM)
normalize_text("3:30", language="ms")
# "tiga tiga puluh"

# Time with AM
normalize_text("3:30 am", language="ms")
# "tiga tiga puluh pagi"

# Time with PM
normalize_text("3:30 pm", language="ms")
# "tiga tiga puluh petang"

# Time with seconds
normalize_text("14:30:45", language="ms")
# "empat belas tiga puluh empat puluh lima"

# Midnight and noon special cases
normalize_text("00:00", language="ms")
# "tengah malam"

normalize_text("12:00", language="ms")
# "tengah hari"
```

### AM/PM Mapping

| English | Malay |
|---------|-------|
| AM / A.M. | pagi |
| PM / P.M. | petang |

## How to Disable

```python
from revonorm import normalize_text

# Disable time normalization
result = normalize_text("3:30 pm", language="en", disable=["times"])
# The time is still extracted as an entity for protection,
# but restored as original text instead of spoken form.

# Use minimal profile (times not spoken)
result = normalize_text("3:30 pm", language="en", profile="minimal")
```

When times are disabled, they are still extracted from the text to protect them from being mangled by other normalizers. However, they are restored as their original text rather than converted to spoken form.

## Edge Cases

- **Zero minutes**: `3:00` produces "three" in English (minute word "zero" is omitted).
- **Single-digit hour**: `3:30` and `03:30` both produce the same output.
- **24-hour format without meridian**: `14:30` is spoken as "fourteen thirty" in English, "empat belas tiga puluh" in Malay.
- **Meridian with dots**: `3:30 p.m.` is treated the same as `3:30 pm`.
- **Time vs percentage**: The regex excludes patterns followed by `%` to avoid conflict with percentage expressions like `3:30%`.
- **Time in URLs**: URL extraction runs before time extraction, so times inside URLs are handled as part of the URL.
- **Midnight (00:00)**: Rendered as "midnight" in English, "tengah malam" in Malay.
- **Noon (12:00)**: Rendered as "noon" in English, "tengah hari" in Malay.
