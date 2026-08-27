# Measurement Normalization

## Overview

Measurement normalization converts measurement expressions (distance, volume, weight, duration, area) into their spoken form for TTS. It handles metric and imperial units with output in the selected language.

Measurements are normalized before the language-specific normalizer and before acronym expansion to prevent units like "km" from being split into "k m".

## Supported Units

### Distance

| Unit | English | Malay |
|------|---------|-------|
| km   | kilometers | kilometer |
| m    | meters | meter |
| cm   | centimeters | sentimeter |
| mm   | millimeters | milimeter |
| mi   | miles | batu |
| ft   | feet | kaki |
| in   | inches | inci |
| yd   | yards | ela |
| batu | miles | batu |
| kaki | feet | kaki |
| inci | inches | inci |

### Volume

| Unit | English | Malay |
|------|---------|-------|
| ml   | milliliters | mililiter |
| l    | liters | liter |
| gal  | gallons | gelen |

### Weight

| Unit | English | Malay |
|------|---------|-------|
| kg   | kilograms | kilogram |
| g    | grams | gram |
| mg   | milligrams | miligram |
| lb   | pounds | paun |
| oz   | ounces | auns |

### Duration

| Unit | English | Malay |
|------|---------|-------|
| hour / hours | hour / hours | jam |
| minute / minutes | minute / minutes | minit |
| second / seconds | second / second | saat |
| jam | hours | jam |
| minit | minutes | minit |
| saat | seconds | saat |

### Area

| Unit | English | Malay |
|------|---------|-------|
| sq ft / sqft | square feet | kaki persegi |

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
```

### Weight

```python
# English
normalize_text("75kg person", language="en")
# "seventy five kilograms person"

normalize_text("500g flour", language="en")
# "five hundred grams flour"

# Malay
normalize_text("75kg orang", language="ms")
# "tujuh puluh lima kilogram orang"

normalize_text("500g tepung", language="ms")
# "lima ratus gram tepung"
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
```

### Area

```python
# English
normalize_text("1000 sq ft apartment", language="en")
# "one thousand square feet apartment"

# Malay
normalize_text("1000 sq ft pangsapuri", language="ms")
# "seribu kaki persegi pangsapuri"
```

### Decimal Values

Measurements support decimal values. Commas in numbers are converted to decimal points.

```python
normalize_text("1,5km away", language="en")
# "one point five kilometers away"

normalize_text("2.5kg of rice", language="en")
# "two point five kilograms of rice"
```

## How to Disable

```python
from revonorm import normalize_text

# Disable measurement normalization
result = normalize_text("5km away", language="en", disable=["measurements"])
# "five k m away"  (number normalized, but unit split by acronym expander)

# Use minimal profile (measurements not normalized)
result = normalize_text("5km away", language="en", profile="minimal")
```

When measurements are disabled, the unit abbreviation may still be split by the acronym expander in a subsequent step (e.g., "km" becomes "k m").

## Edge Cases

- **Case insensitivity**: Both `5KM` and `5km` are recognized.
- **Space between number and unit**: Both `5km` and `5 km` are handled.
- **Negative values**: `-5C` is handled (primarily for temperature, but the measurement pattern also supports negative values).
- **Duration English/Malay cross-use**: Malay duration words (jam, minit, saat) are recognized in both English and Malay contexts.
- **No area unit for sq m**: Currently only `sq ft` / `sqft` is supported for area. Square meters and other area units are not handled.
- **Unit after number-to-words**: Measurement normalization runs before the language normalizer, so the numeric value is still in digit form when matched. The language normalizer then converts the spoken number to words.
