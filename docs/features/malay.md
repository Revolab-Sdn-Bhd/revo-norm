# Malay-Specific Features

## Overview

Revo-norm provides several normalization features specific to Malaysian Malay text. These handle local formats like IC numbers, multiplier notation, day-of-month expressions, Hijri calendar years, and elongated words common in informal Malay writing.

These features are primarily designed for Malay (`language="ms"`) but also produce English output when `language="en"` is used.

## Malaysian IC Numbers

Malaysian Identity Card (IC) numbers follow the format `YYMMDD-SS-NNNN` (6 digits, dash, 2 digits, dash, 4 digits). They are spoken as individual digits.

### Formats Recognized

| Format | Example |
|--------|---------|
| With dashes | `900101-10-1234` |
| Without dashes | `900101101234` |

### Examples

```python
from revonorm import normalize_text

# English: each digit spoken individually
normalize_text("IC: 911111-01-1111", language="en")
# "IC: nine one one one one one zero one one one one one"

# Malay: each digit spoken individually
normalize_text("IC: 911111-01-1111", language="ms")
# "IC: satu satu satu satu satu satu kosong satu satu satu satu satu"
```

### How to Disable

```python
result = normalize_text("IC: 911111-01-1111", language="ms", disable=["ic"])
# "IC: 911111-01-1111"  (not spoken)
```

---

## X-Kali Multiplier

The `x` or `X` notation after a number indicates multiplication in Malay (e.g., "10x" means "10 times" or "sepuluh kali"). This is common in Malaysian product descriptions and comparisons.

### Examples

```python
from revonorm import normalize_text

# English
normalize_text("10x faster", language="en")
# "ten times faster"

# Malay
normalize_text("10x lebih cepat", language="ms")
# "sepuluh kali lebih cepat"

# With space
normalize_text("5 x magnification", language="en")
# "five times magnification"

# Uppercase X
normalize_text("3X bonus", language="ms")
# "tiga kali bonus"
```

### How to Disable

```python
result = normalize_text("10x faster", language="en", disable=["x_kali"])
# "ten faster"  (number normalized, but "x" not converted to "times")
```

---

## Hari Bulan (Day of Month)

The `HB` suffix after a number indicates "hari bulan" (day of the month) in formal Malay writing. It is commonly used in official documents and legal text.

### Formats Recognized

| Format | Example | Day Range |
|--------|---------|-----------|
| Number + HB | `10HB` | 1-31 |
| Number + Hb | `10Hb` | 1-31 |
| Number + hb | `10hb` | 1-31 |
| With space | `10 HB` | 1-31 |

### Examples

```python
from revonorm import normalize_text

# English (hari bulan kept as-is)
normalize_text("Due on 10hb", language="en")
# "Due on ten hari bulan"

# Malay
normalize_text("Tamat pada 10hb", language="ms")
# "Tamat pada sepuluh hari bulan"

# Different day values
normalize_text("1hb meeting", language="ms")
# "satu hari bulan meeting"

normalize_text("31hb deadline", language="ms")
# "tiga puluh satu hari bulan deadline"
```

The internal implementation uses a placeholder (`__HARI_BULAN__`) to prevent other normalizers from interfering with the "hari bulan" phrase during processing.

### How to Disable

```python
result = normalize_text("Due on 10hb", language="ms", disable=["hari_bulan"])
# "Due on sepuluh hb"  (number normalized, but "hb" kept as-is)
```

---

## Hijri Years

Hijri (Islamic calendar) years are denoted by an `H` suffix after a 3-4 digit year number. They are spoken as individual digits followed by the word "Hijri".

### Formats Recognized

| Format | Example |
|--------|---------|
| Year + H | `1445H` |
| Year + h | `1445h` |
| Year + space + H | `1445 H` |
| 3-digit year | `123H` |

### Examples

```python
from revonorm import normalize_text

# English: digits spoken individually + "Hijri"
normalize_text("Year 1445H", language="en")
# "Year one four four five Hijri"

# Malay: digits spoken individually + "Hijri"
normalize_text("Tahun 1445H", language="ms")
# "Tahun satu empat empat lima Hijri"

# 3-digit year
normalize_text("123H", language="en")
# "one two three Hijri"
```

Note that Hijri years are spoken digit-by-digit (like phone numbers) rather than as full numbers. This is the convention for Islamic calendar years.

### How to Disable

```python
result = normalize_text("Year 1445H", language="en", disable=["hijri"])
# "Year one four four five H"  (digits normalized, but "H" kept as-is)
```

---

## Elongated Words

Elongated words with 3 or more consecutive repeated characters are normalized by reducing the repetition to 2 characters. This is common in informal Malay social media text.

### Examples

```python
from revonorm import normalize_text

normalize_text("soooo good", language="en")
# "soo good"

normalize_text("saya betuii sangat celakaaa", language="ms")
# "saya betui sangat celaka"

normalize_text("teruuuus", language="ms")
# "teruus"
```

### Rules

- **Minimum 3 repetitions**: Only characters repeated 3 or more times are reduced. `oo` stays as `oo`.
- **Preserves acronyms**: Words that are all uppercase (potential acronyms) are not normalized.
- **Preserves digits**: Words containing digits are not normalized.
- **Preserves `ke-` prefix**: Words starting with `ke-` (Malay ordinal prefix) are not normalized.

### How to Disable

```python
result = normalize_text("soooo good", language="en", disable=["elongated"])
# "soooo good"  (unchanged)
```

---

## Disabling Multiple Features

You can disable multiple Malay-specific features at once:

```python
from revonorm import normalize_text

result = normalize_text(
    "IC: 900101-10-1234, 10x faster, 10hb, 1445H, soooo good",
    language="ms",
    disable=["ic", "x_kali", "hari_bulan", "hijri", "elongated"]
)
```

Using the `minimal` profile disables all of these features:

```python
result = normalize_text("soooo good", language="ms", profile="minimal")
# "soooo good"  (minimal profile: spacing only)
```

## Edge Cases

- **IC number without dashes**: `900101101234` is recognized but must be exactly 12 digits in the pattern `6-2-4`.
- **X-kali word boundary**: `10x` is matched at word boundaries. `10extra` is not matched because `x` is followed by letters.
- **Hari bulan day range**: Only days 1-31 are recognized. `32hb` is not matched.
- **Hijri year length**: Only 3-4 digit years are matched. `12H` is not matched.
- **Elongated preservation**: The `ke-` prefix check prevents breaking Malay ordinals like `ke-empat`.
- **Feature interactions**: When multiple features are enabled, they may interact. For example, `10x 5hb` has both x-kali and hari bulan -- both are processed independently.
