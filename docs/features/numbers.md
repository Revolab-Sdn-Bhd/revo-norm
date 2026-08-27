# Number Normalization

## Overview

Number normalization converts numeric digits into their spoken word form for TTS. It handles cardinal numbers, ordinals, decimals, percentages, years, and numbers with commas -- with output in the selected language.

## Number-to-Words Engines

| Language | Engine | Range |
|----------|--------|-------|
| English  | `inflect` library | Arbitrary size |
| Malay    | Custom `num2word_ms` | Up to 10^36 (decillion) |

### Malay Number Scale

| Power | Malay Name |
|-------|-----------|
| 10^3  | ribu |
| 10^6  | juta |
| 10^9  | bilion |
| 10^12 | trilion |
| 10^15 | quadrillion |
| 10^18 | quintillion |
| 10^21 | sextillion |
| 10^24 | septillion |
| 10^27 | oktillion |
| 10^30 | nonillion |
| 10^33 | decillion |

### Malay Special Forms

Malay has special single-word forms for certain numbers:

| Number | Malay |
|--------|-------|
| 1      | satu  |
| 10     | sepuluh |
| 11     | sebelas |
| 100    | seratus |
| 1000   | seribu |

## Cardinal Numbers

```python
from revonorm import normalize_text

# English
normalize_text("42 items", language="en")
# "forty two items"

normalize_text("100 participants", language="en")
# "one hundred participants"

# Malay
normalize_text("42 item", language="ms")
# "empat puluh dua item"

normalize_text("100 peserta", language="ms")
# "seratus peserta"
```

### Large Numbers (5+ digits)

Numbers with more than 4 digits are spoken digit-by-digit rather than as a full number, unless they contain commas (which trigger the comma-number handler).

```python
# 5+ digits without commas: digit-by-digit
normalize_text("12345", language="en")
# "one two three four five"

# Numbers with commas: full number-to-words
normalize_text("1,000,000", language="en")
# "one million"

normalize_text("7,832", language="en")
# "seven thousand eight hundred thirty two"
```

## Ordinals

```python
from revonorm import normalize_text

# English ordinals
normalize_text("1st place", language="en")
# "first place"

normalize_text("22nd floor", language="en")
# "twenty second floor"

normalize_text("3rd attempt", language="en")
# "third attempt"

normalize_text("100th day", language="en")
# "one hundredth day"
```

## Decimals

Decimals are spoken as "X point Y" in English and "X perpuluhan Y" in Malay. Each digit after the decimal point is spoken individually.

```python
# English decimals
normalize_text("3.14", language="en")
# "three point one four"

normalize_text("99.99", language="en")
# "ninety nine point nine nine"

# Malay decimals
normalize_text("3.14", language="ms")
# "tiga perpuluhan satu empat"

normalize_text("99.99", language="ms")
# "sembilan puluh sembilan perpuluhan sembilan sembilan"
```

## Percentages

```python
# English percentages
normalize_text("25%", language="en")
# "twenty five percent"

normalize_text("99.5%", language="en")
# "ninety nine point five percent"

# Malay percentages
normalize_text("25%", language="ms")
# "dua puluh lima peratus"

normalize_text("99.5%", language="ms")
# "sembilan puluh sembilan perpuluhan lima peratus"
```

## Year Rendering

Four-digit numbers between 1000 and 2099 are rendered in year-reading style.

```python
# English year rendering
normalize_text("1984", language="en")
# "nineteen eighty four"

normalize_text("2025", language="en")
# "twenty oh twenty five"

normalize_text("2000", language="en")
# "two thousand"

normalize_text("1900", language="en")
# "nineteen hundred"

# Malay year rendering
normalize_text("1984", language="ms")
# "seribu sembilan ratus lapan puluh empat"

normalize_text("2025", language="ms")
# "dua ribu dua puluh lima"
```

English year rendering splits the number into two pairs and reads each pair. Numbers ending in `00` use "hundred" (or "two thousand" for 2000). Numbers with a single-digit second pair use "oh" (e.g., 2001 becomes "twenty oh one").

## Numbers with Commas

```python
# English
normalize_text("1,000,000 people", language="en")
# "one million people"

normalize_text("7,832 users", language="en")
# "seven thousand eight hundred thirty two users"

# Malay
normalize_text("1,000,000 orang", language="ms")
# "satu juta orang"

normalize_text("7,832 pengguna", language="ms")
# "tujuh ribu lapan ratus tiga puluh dua pengguna"
```

## Dashed Digit Sequences

Phone numbers and similar dashed-digit sequences are spoken digit-by-digit:

```python
normalize_text("call 03-1234-5678", language="en")
# "call zero three dash one two three four dash five six seven eight"

normalize_text("hubungi 03-1234-5678", language="ms")
# "hubungi kosong tiga satu dua tiga empat lima enam tujuh lapan"
```

## Malay Digit Words

| Digit | Malay |
|-------|-------|
| 0     | kosong |
| 1     | satu |
| 2     | dua |
| 3     | tiga |
| 4     | empat |
| 5     | lima |
| 6     | enam |
| 7     | tujuh |
| 8     | lapan |
| 9     | sembilan |

## Configuration

Number normalization is always active and cannot be disabled independently -- it is a core part of the language normalizer. To minimize processing, use the `minimal` profile:

```python
from revonorm import normalize_text

# Minimal profile: only spacing normalization
result = normalize_text("42 items", language="en", profile="minimal")
```

## Edge Cases

- **Single digits**: `7` becomes "seven" (EN) or "tujuh" (MS).
- **Zero**: `0` becomes "zero" (EN) or "kosong" (MS).
- **Negative numbers**: Not directly handled by the number regex (requires context like temperature).
- **Mixed alphanumeric**: Tokens like "v2" are split into "v two" (EN) or "v dua" (MS).
- **Decimals in currency**: Handled by the currency extractor, not the general decimal handler.
- **Numbers inside entity placeholders**: Protected by entity extraction and not double-processed.
