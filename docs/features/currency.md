# Currency Normalization

## Overview

Currency normalization converts written currency expressions into their spoken form for TTS. It supports multiple currencies, suffix-based magnitudes (K/M/B/T), decimal amounts, and produces output in the selected language.

Currency extraction runs early in the pipeline to prevent other normalizers (acronym expansion, abbreviation expansion) from splitting symbols like "RM" into "R M" or "R meter".

## Supported Currencies

| Symbol | Name | Sub-unit (EN) | Sub-unit (MS) |
|--------|------|---------------|----------------|
| `RM`   | Ringgit Malaysia | cent | sen |
| `MYR`  | Ringgit Malaysia | cent | sen |
| `$`    | US Dollar | cent | sen |
| `USD`  | US Dollar | cent | sen |
| `€`    | Euro | cent | sen |
| `EUR`  | Euro | cent | sen |
| `£`    | British Pound | pence | pence |
| `GBP`  | British Pound | pence | pence |

## Suffix Expansion

Currency amounts can include magnitude suffixes that are expanded to their full numeric value before conversion to spoken form.

| Suffix | Meaning | Multiplier |
|--------|---------|------------|
| `K`    | Thousand | x1,000 |
| `M`    | Million  | x1,000,000 |
| `B`    | Billion  | x1,000,000,000 |
| `T`    | Trillion | x1,000,000,000,000 |

Suffix expansion is the **first step** in the pipeline, running before entity extraction and URL processing.

## Examples

### Whole Amounts

```
Input:  "The price is RM450000"
Output: "The price is empat ratus lima puluh ribu ringgit"

Input:  "It costs $100"
Output: "It costs one hundred dollar"
```

### Decimal Amounts

```
Input:  "RM5.50"
Output: "lima ringgit lima puluh sen"

Input:  "$0.99"
Output: "ninety nine cents"

Input:  "$0.50"
Output: "fifty cents"
```

When the whole-number part is zero, the main unit is omitted. `$0.50` becomes "fifty cents", not "zero dollar fifty cents".

### Suffix Expansion

```
Input:  "RM30K"
Output: "tiga puluh ribu ringgit"

Input:  "RM1.5M"
Output: "satu juta lima ratus ribu ringgit"

Input:  "$5B"
Output: "five billion dollar"

Input:  "RM1T"
Output: "satu trilion ringgit"
```

### Currency with Magnitude Words

The language normalizers also handle magnitude words after the amount:

```
Input:  "RM2.5 million"    (English pipeline)
Output: "two point five million ringgit"

Input:  "RM2.5 juta"       (Malay pipeline)
Output: "dua perpuluhan lima juta ringgit"
```

### Currency with Commas

```
Input:  "RM1,000,000"
Output: "satu juta ringgit"

Input:  "$7,832"
Output: "seven thousand eight hundred thirty two dollar"
```

### Multiple Currencies in One Sentence

```
Input:  "USD100 and EUR50"
Output: "one hundred dollar and lima puluh euro"
```

## How Entity Extraction Protects Currency

Currency is extracted as an entity before other normalizers run. The entity extractor replaces the currency expression with a placeholder (e.g., `<<<CURRENCY_1>>>`), processes the rest of the text, then restores the currency in spoken form.

This prevents the following cascading failures:

| Without Entity Extraction | With Entity Extraction |
|--------------------------|----------------------|
| "RM 450" -> "R M 450" -> "R meter four hundred fifty" | "RM 450" -> "empat ratus lima puluh ringgit" |
| "$50K" -> "dollar five zero K" | "$50K" -> "fifty thousand dollar" |

## Configuration

Currency normalization **cannot be fully disabled** -- it always runs as part of the entity extraction system to protect currency symbols from being mangled by other normalizers. However, you can use a minimal profile to reduce other processing:

```python
from revonorm import normalize_text

# Currency always gets extracted and protected
result = normalize_text("RM450", language="ms")

# Use minimal profile (only spacing normalization besides entity extraction)
result = normalize_text("RM450", language="ms", profile="minimal")
```

## Edge Cases

- **Sub-unit only**: `RM0.50` produces "lima puluh sen" (ringgit unit omitted).
- **Decimal padding**: `RM5.5` is treated the same as `RM5.50` -- the fraction is padded to two digits.
- **Trailing decimal**: `RM5.` is treated as a whole number `RM5`.
- **Case insensitivity**: `rm30k` and `RM30K` are both handled.
- **Space between symbol and amount**: Both `RM100` and `RM 100` are recognized.
- **Comma-separated amounts**: `RM1,000,000` has commas stripped before number-to-words conversion.
