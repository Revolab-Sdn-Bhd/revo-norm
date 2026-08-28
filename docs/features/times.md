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
# "eleven fifty-nine p m"

# Time with seconds
normalize_text("14:30:45", language="en")
# "fourteen thirty:forty five"

# 24-hour clock spoken directly
normalize_text("00:00", language="en")
# "zero zero"

normalize_text("12:00", language="en")
# "twelve zero"
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
# "empat belas tiga puluh:empat puluh lima"

# 24-hour clock
normalize_text("00:00", language="ms")
# "kosong kosong"

normalize_text("12:00", language="ms")
# "dua belas kosong"
```

### AM/PM Mapping

| English | Malay |
|---------|-------|
| AM / A.M. | pagi |
| PM / P.M. | petang |

## Indonesian Output

Indonesian recognizes its own meridian words and maps `pm` to `sore`:

| English | Indonesian |
|---------|------------|
| AM / A.M. | pagi |
| PM / P.M. | sore |
| — | pagi / siang / sore / malam (written out in the input) |

```python
from revonorm import normalize_text

# Written meridian words pass through with the hour spoken
normalize_text("rapat 7:30 pagi, selesai 3:30 sore", language="id")
# "rapat tujuh tiga puluh pagi, selesai tiga tiga puluh sore"

# Latin meridian is translated
normalize_text("rapat 3:30 pm", language="id")
# "rapat tiga tiga puluh sore"

# 24-hour clock
normalize_text("14:30", language="id")
# "empat belas tiga puluh"

normalize_text("00:00", language="id")
# "nol nol"

normalize_text("12:00", language="id")
# "dua belas nol"
```

## Chinese Output

Chinese uses 上午 (AM) / 下午 (PM) with 点 (hour) and 分 (minute). Zero minutes omit the 分 word, and `00:00` reads as 零点:

```python
from revonorm import normalize_text

normalize_text("3:30 pm", language="zh")
# "下午三点三十分"

normalize_text("9:00 am", language="zh")
# "上午九点"

normalize_text("14:30", language="zh")
# "十四点三十分"

normalize_text("00:00", language="zh")
# "零点"

normalize_text("12:00", language="zh")
# "十二点"

normalize_text("3:00", language="zh")
# "三点"

normalize_text("早上13:15", language="zh")
# "早上十三点十五分"
```

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

- **Zero minutes**: `3:00` produces "three zero" in English, "tiga nol" in Indonesian, and 三点 in Chinese (the 分 word is omitted).
- **Single-digit hour**: `3:30` and `03:30` both produce the same output.
- **24-hour format without meridian**: `14:30` is spoken as "fourteen thirty" in English, "empat belas tiga puluh" in Malay, "empat belas tiga puluh" in Indonesian, and 十四点三十分 in Chinese.
- **Meridian with dots**: `3:30 p.m.` is treated the same as `3:30 pm`.
- **Time vs percentage**: The regex excludes patterns followed by `%` to avoid conflict with percentage expressions like `3:30%`.
- **Time in URLs**: URL extraction runs before time extraction, so times inside URLs are handled as part of the URL.
- **Seconds keep their separator**: `14:30:45` reads as "fourteen thirty:forty five" in English — the seconds separator is spoken as a colon rather than a space.
