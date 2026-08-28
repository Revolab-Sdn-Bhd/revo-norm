# Currency Normalization

## Overview

Currency normalization converts written currency expressions into their spoken form for TTS. It supports multiple currencies, suffix-based magnitudes (K/M/B/T), decimal amounts, and produces output in the selected language.

Currency extraction runs early in the pipeline to prevent other normalizers (acronym expansion, abbreviation expansion) from splitting symbols like "RM" into "R M" or "R meter".

## Supported Currencies

| Symbol | Name | Sub-unit (EN) | Sub-unit (MS) | Sub-unit (ID) |
|--------|------|---------------|----------------|----------------|
| `RM`   | Ringgit Malaysia | cent | sen | sen |
| `MYR`  | Ringgit Malaysia | cent | sen | sen |
| `$`    | US Dollar | cent | sen | sen |
| `USD`  | US Dollar | cent | sen | sen |
| `€`    | Euro | cent | sen | sen |
| `EUR`  | Euro | cent | sen | sen |
| `£`    | British Pound | pence | pence | pence |
| `GBP`  | British Pound | pence | pence | pence |

`Rp` and `IDR` are Indonesian-only and always speak as `rupiah` with `sen` as the sub-unit. Chinese (`zh` / `zh_my`) uses its own unit words — see the table under [Chinese Output](#chinese-output).

Indonesian also recognizes money shorthand suffixes that only apply to rupiah amounts: `rb` = ribu (thousand), `jt` = juta (million), `M` = **miliar** (billion, not million), `T` = triliun (trillion).

## Suffix Expansion

Currency amounts can include magnitude suffixes that are expanded to their full numeric value before conversion to spoken form.

| Suffix | Meaning | Multiplier |
|--------|---------|------------|
| `K`    | Thousand | x1,000 |
| `M`    | Million  | x1,000,000 |
| `B`    | Billion  | x1,000,000,000 |
| `T`    | Trillion | x1,000,000,000,000 |

For Indonesian rupiah, `rb`/`jt` replace `K`/`M` and `M` means miliar (10^9), so `Rp5M` is five billion rupiah, not five million.

Suffix expansion is the **first step** in the pipeline, running before entity extraction and URL processing.

## Examples

### Whole Amounts

```
Input:  "The price is RM450000"     (Malay pipeline)
Output: "The price is empat ratus lima puluh ribu ringgit"

Input:  "It costs $100"
Output: "It costs one hundred dollar"
```

### Decimal Amounts

```
Input:  "RM5.50"
Output: "lima ringgit lima puluh sen"

Input:  "$0.99"
Output: "ninety-nine cents"

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

### Indonesian Rupiah

Rupiah amounts use Indonesian number words, and the number itself follows Indonesian conventions — dots group thousands and a comma marks the decimal:

```
Input:  "Harga Rp1.500.000"
Output: "Harga satu juta lima ratus ribu rupiah"

Input:  "Dana Rp5M"
Output: "Dana lima miliar rupiah"

Input:  "Cuma Rp10rb"
Output: "Cuma sepuluh ribu rupiah"

Input:  "Dana Rp2jt"
Output: "Dana dua juta rupiah"

Input:  "IDR 500.000"
Output: "lima ratus ribu rupiah"

Input:  "Rp50.000,75"
Output: "lima puluh ribu rupiah tujuh puluh lima sen"
```

### Chinese Output

Chinese speaks the main unit and sub-unit as Chinese words, with `zh_my` using the colloquial Malaysian forms:

| Symbol | zh (main) | zh (sub) | zh_my (main) | zh_my (sub) |
|--------|-----------|----------|--------------|-------------|
| `RM, MYR` | 令吉 | 仙 | 令吉 | 仙 |
| `$, USD`  | 美元 | 分 | 美金 | 仙 |
| `£, GBP`  | 英镑 | 便士 | 英磅 | 仙 |
| `€, EUR`  | 欧元 | 分 | 欧元 | 仙 |

```
Input:  "RM100.50"    (zh)
Output: "一百令吉五十仙"

Input:  "$100.50"     (zh)
Output: "一百美元五十分"

Input:  "$50.20"      (zh_my)
Output: "五十美金二十仙"

Input:  "RM30K"       (zh)
Output: "三万令吉"

Input:  "RM1M"        (zh_my)
Output: "一百万令吉"
```

### Currency with Magnitude Words

The language normalizers also handle magnitude words after the amount:

```
Input:  "RM2.5 juta"       (Malay pipeline)
Output: "dua juta lima ratus ribu ringgit"
```

### Currency with Commas

```
Input:  "RM1,000,000"
Output: "satu juta ringgit"

Input:  "$7,832"
Output: "seven thousand, eight hundred and thirty-two dollar"
```

### Multiple Currencies in One Sentence

```
Input:  "USD100 and EUR50"
Output: "one hundred dollar and fifty euro"
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
