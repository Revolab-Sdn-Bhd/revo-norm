# Date Normalization

## Overview

Date normalization converts written date expressions into their spoken form for TTS. It supports multiple common date formats, output in the selected language, and automatic disambiguation between DD/MM and MM/DD formats.

Dates are extracted as entities early in the pipeline to prevent the fraction normalizer from misinterpreting date separators (e.g., `15/08` as a fraction).

## Supported Formats

| Format | Example | Notes |
|--------|---------|-------|
| DD/MM/YYYY | `15/08/2025` | Day first when day > 12 |
| MM/DD/YYYY | `08/15/2025` | Month first when month <= 12 |
| YYYY-MM-DD | `2025-08-15` | ISO format |

## DD/MM vs MM/DD Ambiguity

When the slash format is used and the first number is greater than 12, it is unambiguously treated as DD/MM/YYYY (day/month/year). When both numbers are 12 or less, the format is treated as MM/DD/YYYY.

| Input | Interpretation | Reason |
|-------|---------------|--------|
| `15/08/2025` | DD/MM/YYYY | 15 cannot be a month |
| `08/15/2025` | MM/DD/YYYY | 15 cannot be a month |
| `05/08/2025` | MM/DD/YYYY | Ambiguous -- defaults to MM/DD |

## English Output

```python
from revonorm import normalize_text

# Slash format (DD/MM, day > 12)
normalize_text("15/08/2025", language="en")
# "fifteen of August twenty twenty-five"

# Slash format (MM/DD, ambiguous)
normalize_text("08/15/2025", language="en")
# "fifteen of August twenty twenty-five"

# ISO format (YYYY-MM-DD)
normalize_text("2025-08-15", language="en")
# "fifteen August two thousand and twenty-five"
```

## Malay Output

Malay uses localized month names and Malay number-to-words conversion.

### Malay Month Names

| Number | English    | Malay      |
|--------|-----------|------------|
| 01     | January   | Januari    |
| 02     | February  | Februari   |
| 03     | March     | Mac        |
| 04     | April     | April      |
| 05     | May       | Mei        |
| 06     | June      | Jun        |
| 07     | July      | Julai      |
| 08     | August    | Ogos       |
| 09     | September | September  |
| 10     | October   | Oktober    |
| 11     | November  | November   |
| 12     | December  | Disember   |

```python
from revonorm import normalize_text

# Slash format (DD/MM)
normalize_text("15/08/2025", language="ms")
# "lima belas Ogos dua ribu dua puluh lima"

# Slash format (MM/DD, ambiguous)
normalize_text("08/15/2025", language="ms")
# "lima belas Ogos dua ribu dua puluh lima"

# ISO format (YYYY-MM-DD)
normalize_text("2025-08-15", language="ms")
# "lima belas Ogos dua ribu dua puluh lima"
```

## Indonesian Output

Indonesian uses localized month names and Indonesian number-to-words conversion. `15/08/2025`, `08/15/2025`, and `2025-08-15` all resolve to the same spoken date.

### Indonesian Month Names

| Number | English    | Indonesian |
|--------|-----------|------------|
| 01     | January   | Januari    |
| 02     | February  | Februari   |
| 03     | March     | Maret      |
| 04     | April     | April      |
| 05     | May       | Mei        |
| 06     | June      | Juni       |
| 07     | July      | Juli       |
| 08     | August    | Agustus    |
| 09     | September | September  |
| 10     | October   | Oktober    |
| 11     | November  | November   |
| 12     | December  | Desember   |

```python
from revonorm import normalize_text

# Slash format (DD/MM)
normalize_text("15/08/2025", language="id")
# "lima belas Agustus dua ribu dua puluh lima"

# Slash format (MM/DD)
normalize_text("08/15/2025", language="id")
# "lima belas Agustus dua ribu dua puluh lima"

# ISO format (YYYY-MM-DD)
normalize_text("2025-08-15", language="id")
# "lima belas Agustus dua ribu dua puluh lima"
```

## Chinese Output

Chinese reads the year digit-by-digit, then the month and day as Chinese number words with the 日 suffix:

```python
from revonorm import normalize_text

normalize_text("15/08/2025", language="zh")
# "二零二五年八月十五日"

normalize_text("2025-12-25", language="zh")
# "二零二五年十二月二十五日"

normalize_text("2025-08-15", language="zh")
# "二零二五年八月十五日"
```

## How to Disable

```python
from revonorm import normalize_text

# Disable date normalization
result = normalize_text("15/08/2025", language="en", disable=["dates"])
# The date is still extracted as an entity for protection,
# but restored as the original text instead of spoken form.

# Use minimal profile (dates not spoken)
result = normalize_text("15/08/2025", language="en", profile="minimal")
```

When dates are disabled, they are still extracted from the text to protect them from being mangled by other normalizers (e.g., the fraction normalizer). However, they are restored as their original text rather than converted to spoken form.

## Edge Cases

- **Two-digit years**: `15/08/25` is matched, but four-digit years produce better spoken output.
- **Single-digit day/month**: `5/8/2025` is recognized the same as `05/08/2025`.
- **Month name variations**: `15 August 2025` and `August 15, 2025` are documented formats; the currently verified converters are the slash and ISO forms above.
- **Date vs fraction conflict**: Dates are extracted before fractions run, so `15/08/2025` is never misinterpreted as a fraction.
- **Dates in URLs**: URL extraction runs before date extraction, so dates inside URLs are handled as part of the URL, not as standalone dates.
