# Measurement Normalization

## Overview

Measurement normalization converts measurement expressions (distance, volume, weight, duration, area) into their spoken form for TTS. It handles metric and imperial units with output in the selected language.

Measurements are normalized before the language-specific normalizer and before acronym expansion to prevent units like "km" from being split into "k m".

## Supported Units

Chinese uses its own unit words, listed after each table. Indonesian words match Malay for most units except where noted.

### Distance

| Unit | English | Malay | Indonesian |
|------|---------|-------|------------|
| km   | kilometers | kilometer | kilometer |
| m    | meters | meter | meter |
| cm   | centimeters | sentimeter | sentimeter |
| mm   | millimeters | milimeter | milimeter |
| mi   | miles | batu | mil |
| ft   | feet | kaki | kaki |
| in   | inches | inci | inci |
| yd   | yards | ela | yard |
| batu | miles | batu | batu |
| kaki | feet | kaki | kaki |
| inci | inches | inci | inci |

Chinese distance words: 公里, 米, 厘米.

### Volume

| Unit | English | Malay | Indonesian |
|------|---------|-------|------------|
| ml   | milliliters | mililiter | mililiter |
| l    | liters | liter | liter |
| gal  | gallons | gelen | galon |

Chinese volume words: 毫升, 升.

### Weight

| Unit | English | Malay | Indonesian |
|------|---------|-------|------------|
| kg   | kilograms | kilogram | kilogram |
| g    | grams | gram | gram |
| mg   | milligrams | miligram | miligram |
| lb   | pounds | paun | pon |
| oz   | ounces | auns | ons |

Chinese weight words: 公斤, 克, 毫克.

### Duration

| Unit | English | Malay | Indonesian |
|------|---------|-------|------------|
| hour / hours | hour / hours | jam | jam |
| minute / minutes | minute / minutes | minit | menit |
| second / seconds | second / second | saat | detik |
| jam | hours | jam | jam |
| minit | minutes | minit | minit |
| saat | seconds | saat | saat |

### Area

| Unit | English | Malay | Indonesian |
|------|---------|-------|------------|
| sq ft / sqft | square feet | kaki persegi | kaki persegi |

Area units are Latin-script only; Chinese does not convert `sq ft` (see Edge Cases).

## Examples

### Distance

```python
from revonorm import normalize_text

# English
normalize_text("5km away", language="en")
# "five kilometers away"

normalize_text("100m sprint", language="en")
# "one hundred meters sprint"

normalize_text("30mi drive", language="en")
# "thirty miles drive"

# Malay
normalize_text("5km jauh", language="ms")
# "lima kilometer jauh"

normalize_text("100m lari", language="ms")
# "seratus meter lari"

# Indonesian
normalize_text("5km jauh", language="id")
# "lima kilometer jauh"

# Chinese
normalize_text("5km", language="zh")
# "五公里"

normalize_text("1.5km", language="zh")
# "一点五公里"
```

### Volume

```python
# English
normalize_text("500ml bottle", language="en")
# "five hundred milliliters bottle"

normalize_text("2l jug", language="en")
# "two liters jug"

# Malay
normalize_text("500ml botol", language="ms")
# "lima ratus mililiter botol"

# Indonesian
normalize_text("500ml botol", language="id")
# "lima ratus mililiter botol"

# Chinese
normalize_text("200ml", language="zh")
# "二百毫升"
```

### Weight

```python
# English
normalize_text("75kg person", language="en")
# "seventy five kilogram person"

normalize_text("500g flour", language="en")
# "five hundred grams flour"

# Malay
normalize_text("75kg orang", language="ms")
# "tujuh puluh lima kilogram orang"

normalize_text("500g tepung", language="ms")
# "lima ratus gram tepung"

# Indonesian
normalize_text("75kg orang", language="id")
# "tujuh puluh lima kilogram orang"

# Chinese
normalize_text("10kg", language="zh")
# "十公斤"
```

### Duration

```python
# English
normalize_text("5 hours to complete", language="en")
# "five hours to complete"

normalize_text("30 minutes wait", language="en")
# "thirty minutes wait"

# Malay
normalize_text("5 jam untuk siap", language="ms")
# "lima jam untuk siap"

normalize_text("30 minit tunggu", language="ms")
# "tiga puluh minit tunggu"

# Indonesian
normalize_text("5 jam", language="id")
# "lima jam"

normalize_text("30 menit", language="id")
# "tiga puluh menit"
```

### Area

```python
# English
normalize_text("1000 sq ft apartment", language="en")
# "one thousand square feet apartment"

# Malay
normalize_text("1000 sq ft pangsapuri", language="ms")
# "seribu kaki persegi pangsapuri"

# Indonesian
normalize_text("1.000 sq ft", language="id")
# "satu kaki persegi"
```

### Decimal Values

Measurements support decimal values. In Indonesian text the decimal separator is a comma, in English and Chinese text a dot.

```python
normalize_text("2.5kg of rice", language="en")
# "two point five kilogram of rice"

normalize_text("berat 10.000,50 kg", language="id")
# "berat sepuluh ribu koma lima nol kilogram"

normalize_text("3.14米", language="zh")
# "三点一四米"
```

## How to Disable

```python
from revonorm import normalize_text

# Disable measurement normalization
result = normalize_text("5km away", language="en", disable=["measurements"])
# "five K M away"  (number normalized, but unit split by acronym expander)

# Use minimal profile (measurements not normalized)
result = normalize_text("5km away", language="en", profile="minimal")
```

When measurements are disabled, the unit abbreviation may still be split by the acronym expander in a subsequent step (e.g., "km" becomes "k m").

## Edge Cases

- **Case insensitivity**: Both `5KM` and `5km` are recognized.
- **Space between number and unit**: Both `5km` and `5 km` are handled.
- **Negative values**: `-5C` is handled (primarily for temperature, but the measurement pattern also supports negative values). Under `zh`, `-5C` becomes 负 五摄氏度.
- **Duration English/Malay cross-use**: Malay duration words (jam, minit, saat) are recognized in both English and Malay contexts.
- **No area unit for sq m**: Currently only `sq ft` / `sqft` is supported for area. Square meters and other area units are not handled.
- **Chinese leaves `sq ft` alone**: `1000 sq ft` under `zh` becomes `一零零零 sq ft` — the number converts but the unit does not.
- **Indonesian unit words follow the number conventions**: dotted-thousands values inside measurements convert fully (`10.000,50 kg` → `sepuluh ribu koma lima nol kilogram`).
- **Unit after number-to-words**: Measurement normalization runs before the language normalizer, so the numeric value is still in digit form when matched. The language normalizer then converts the spoken number to words.
