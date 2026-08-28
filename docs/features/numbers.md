# Number Normalization

## Overview

Number normalization converts numeric digits into their spoken word form for TTS. It handles cardinal numbers, ordinals, decimals, percentages, years, and numbers with commas -- with output in the selected language.

## Number-to-Words Engines

| Language | Engine | Range |
|----------|--------|-------|
| English  | `inflect` library | Arbitrary size |
| Malay    | Custom `num2word_ms` | Up to 10^36 (decillion) |
| Indonesian | Custom `num2word_id` | nol through desiliun |
| Chinese  | Custom `num2word_zh` | 零 through 兆 |

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

### Indonesian Number Scale

Indonesian follows the "long-scale" convention shared with Malay for the short names but uses `miliar`/`triliun` at 10^9 and 10^12:

| Power | Indonesian Name |
|-------|----------------|
| 10^3  | ribu |
| 10^6  | juta |
| 10^9  | miliar |
| 10^12 | triliun |

### Malay Special Forms

Malay has special single-word forms for certain numbers:

| Number | Malay |
|--------|-------|
| 1      | satu  |
| 10     | sepuluh |
| 11     | sebelas |
| 100    | seratus |
| 1000   | seribu |

### Chinese Special Forms

| Number | Chinese |
|--------|---------|
| 0 | 零 |
| 10 | 十 |
| 11 | 十一 |
| 100 | 一百 |
| 101 | 一百零一 |
| 1000 | 一千 |
| 10000 | 一万 |
| 10^8 | 一亿 |
| 10^12 | 一兆 |

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

# Indonesian
normalize_text("42 item", language="id")
# "empat puluh dua item"

normalize_text("1.000.000 pengguna", language="id")
# "satu juta pengguna"

# Chinese
normalize_text("100", language="zh")
# "一百"

normalize_text("10001", language="zh")
# "一万零一"

normalize_text("123456789", language="zh")
# "一亿二千三百四十五万六千七百八十九"
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
# "seven thousand, eight hundred and thirty two"
```

Chinese is exempt: any length of digits converts to full Chinese number words.

### Written Number Conventions

English and Malay use comma thousands with a dot decimal. Indonesian is the reverse — dots group thousands and a comma marks the decimal:

```python
# English / Malay
normalize_text("1,000,000 people", language="en")
# "one million people"

# Indonesian
normalize_text("1.000.000", language="id")
# "satu juta"

normalize_text("1.000.000.000", language="id")
# "satu miliar"

normalize_text("2,5", language="id")
# "dua koma lima"
```

The Indonesian comma-decimal reader handles a single digit after the comma. Multi-digit fractions without a preceding dotted group (`3,14`, `12,75`) fall through to the general number path and read as two separate numbers — reword such text or use a dotted integer part (`10.000,50` works).

Malay dotted groups are not thousands separators — `1.000.000` under `language="ms"` is parsed as a decimal chain, so pass comma-grouped numbers to Malay text.

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

# Chinese ordinals use the 第 prefix
normalize_text("第3", language="zh")
# "第三"

normalize_text("第1名", language="zh")
# "第一名"
```

## Decimals

Decimals are spoken as "X point Y" in English, "X perpuluhan Y" in Malay, "X koma Y" in Indonesian, and 点 in Chinese. Each digit after the separator is spoken individually.

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

# Indonesian decimals (comma separator)
normalize_text("3,5", language="id")
# "tiga koma lima"

normalize_text("berat 10.000,50 kg", language="id")
# "berat sepuluh ribu koma lima nol kilogram"

# Chinese decimals
normalize_text("3.14", language="zh")
# "三点一四"
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

# Indonesian percentages
normalize_text("25%", language="id")
# "dua puluh lima persen"

normalize_text("naik 3,5%", language="id")
# "naik tiga koma lima persen"

# Chinese percentages
normalize_text("50%", language="zh")
# "百分之五十"
```

## Year Rendering

Four-digit numbers between 1000 and 2099 are rendered in year-reading style. Chinese reads these digit-by-digit.

```python
# English year rendering
normalize_text("1984", language="en")
# "nineteen eighty four"

normalize_text("2025", language="en")
# "twenty twenty five"

normalize_text("2000", language="en")
# "two thousand"

normalize_text("1900", language="en")
# "nineteen hundred"

# Malay year rendering
normalize_text("1984", language="ms")
# "seribu sembilan ratus lapan puluh empat"

normalize_text("2025", language="ms")
# "dua ribu dua puluh lima"

# Indonesian year rendering
normalize_text("1984", language="id")
# "seribu sembilan ratus delapan puluh empat"

# Chinese year rendering (digit-by-digit)
normalize_text("2025", language="zh")
# "二零二五"

normalize_text("1999", language="zh")
# "一九九九"
```

English year rendering splits the number into two pairs and reads each pair. Numbers ending in `00` use "hundred" (or "two thousand" for 2000). Numbers with a single-digit second pair use "oh" (e.g., 2001 becomes "twenty oh one").

## Numbers with Commas

```python
# English
normalize_text("1,000,000 people", language="en")
# "one million people"

normalize_text("7,832 users", language="en")
# "seven thousand, eight hundred and thirty two users"

# Malay
normalize_text("1,000,000 orang", language="ms")
# "satu juta orang"

normalize_text("7,832 pengguna", language="ms")
# "tujuh ribu lapan ratus tiga puluh dua pengguna"

# Chinese
normalize_text("1,000", language="zh")
# "一千"

normalize_text("1,000,000", language="zh")
# "一百万"
```

## Dashed Digit Sequences

Phone numbers and similar dashed-digit sequences are spoken digit-by-digit:

```python
normalize_text("call 03-1234-5678", language="en")
# "call zero three one two three four five six seven eight"

normalize_text("hubungi 03-1234-5678", language="ms")
# "hubungi kosong tiga satu dua tiga empat lima enam tujuh lapan"
```

## Digit Words

| Digit | Malay | Indonesian | Chinese |
|-------|-------|------------|---------|
| 0 | kosong | nol | 零 |
| 1 | satu | satu | 一 |
| 2 | dua | dua | 二 |
| 3 | tiga | tiga | 三 |
| 4 | empat | empat | 四 |
| 5 | lima | lima | 五 |
| 6 | enam | enam | 六 |
| 7 | tujuh | tujuh | 七 |
| 8 | lapan | delapan | 八 |
| 9 | sembilan | sembilan | 九 |

## Configuration

Number normalization is always active and cannot be disabled independently -- it is a core part of the language normalizer. To minimize processing, use the `minimal` profile:

```python
from revonorm import normalize_text

# Minimal profile: only spacing normalization
result = normalize_text("42 items", language="en", profile="minimal")
```

## Edge Cases

- **Single digits**: `7` becomes "seven" (EN), "tujuh" (MS), "tujuh" (ID), or 七.
- **Zero**: `0` becomes "zero" (EN), "kosong" (MS), "nol" (ID), or 零.
- **Negative numbers**: Only converted with supporting context (e.g., temperature: `-5C` under `zh` becomes 负 五摄氏度).
- **Mixed alphanumeric**: Tokens like "v2" are split into "V two" (EN) or "V dua" (MS).
- **Decimals in currency**: Handled by the currency extractor, not the general decimal handler.
- **Numbers inside entity placeholders**: Protected by entity extraction and not double-processed.
- **High ordinals (EN)**: `100th` is not converted — it reads as "one zero zero T H". Use `1st`, `2nd`, `3rd`, or two-digit forms like `22nd`.
- **Malay dotted groups are decimals**: `1.000.000` under `language="ms"` is not one million; use `1,000,000`.
- **Indonesian multi-digit comma fractions**: `3,14` reads as "tiga empat belas", not "tiga koma satu empat" — see [Written Number Conventions](#written-number-conventions).
