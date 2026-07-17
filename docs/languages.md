# Language Support

Revo-norm supports five language codes with awareness of code-mixing patterns common in Southeast Asian contexts.

## Supported Languages

| Code | Language | Notes |
|------|----------|-------|
| `en` | English | Full normalization with contractions, ordinals, abbreviations |
| `ms` | Malay (Bahasa Melayu) | Full normalization with Malay number words, currency, local features |
| `id` | Indonesian (Bahasa Indonesia) | Indonesian number words, rupiah, and written number conventions (dotted thousands, comma decimals) |
| `zh` | Chinese (Standard) | Numbers, dates, times, currency, measurements in 普通话 spoken form |
| `zh_my` | Malaysian Chinese | Same as `zh` with colloquial currency (`$` → 块) and code-mixing support |

```python
from revo_norm import normalize_text

result_en = normalize_text("25C outside", language="en")
# "twenty five degrees celsius outside"

result_ms = normalize_text("25C di luar", language="ms")
# "dua puluh lima darjah selsius di luar"

result_zh = normalize_text("25C", language="zh")
# "二十五摄氏度"

result_zh_my = normalize_text("花了 RM50 吃饭", language="zh_my")
# "花了 五十令吉 吃饭"
```

---

## Code-Mixing

Malaysian text frequently mixes languages. Revo-norm handles this naturally -- the language parameter controls which normalizer runs on the non-entity text, but English technical terms (API, ML, GPU, etc.) are handled consistently regardless of language. Malaysian Chinese (`zh_my`) is specifically designed for code-mixed CJK + Latin text.

```python
# English terms in a Malay sentence
result = normalize_text("Projek ML ni guna 5GB RAM", language="ms")
# "Projek M L ni guna lima gigabyte R A M"

# Malay terms in an English sentence
result = normalize_text("The ringgit fell 5% today", language="en")
# "The ringgit fell five percent today"
```

Pronunciation mappings apply across all languages equally -- terms like `GUI`, `ASCII`, and `IEEE` are mapped to their spoken forms regardless of the `language` parameter.

---

## English Specifics (`language="en"`)

### Contractions

Common English contractions are expanded to their full forms for clean TTS output:

```python
normalize_text("I'm happy they can't come", language="en")
# "I am happy they cannot come"
```

Supported contractions include:
- **Pronoun + verb:** `I'm` -> `I am`, `you're` -> `you are`, `it's` -> `it is`
- **Negations:** `don't` -> `do not`, `can't` -> `cannot`, `won't` -> `will not`
- **Perfect tense:** `should've` -> `should have`, `could've` -> `could have`
- **Question words:** `what's` -> `what is`, `where's` -> `where is`

Over 60 contractions are handled, including negative forms, possessive-like forms, and perfect tense contractions.

### Ordinals

English ordinal numbers are converted to their spoken form:

```python
normalize_text("She finished 1st in the 21st century", language="en")
# "She finished first in the twenty first century"
```

### Abbreviations

Common title and place abbreviations are expanded:

| Abbreviation | Spoken Form |
|-------------|-------------|
| `Mr.` | `Mister` |
| `Mrs.` | `Misess` |
| `Dr.` | `Doctor` |
| `St.` | `Saint` |
| `Jr.` | `Junior` |
| `Ltd.` | `Limited` |
| `Capt.` | `Captain` |
| `Gen.` | `General` |
| `Sgt.` | `Sergeant` |

### Numbers and Currency

```python
normalize_text("1,000,000 dollars at 3.5%", language="en")
# "one million dollars at three point five percent"

normalize_text("The price is $45.99", language="en")
# "The price is forty five dollar ninety nine cent"
```

### Years

Four-digit numbers in the 1000-2099 range are read as years:

```python
normalize_text("Born in 1990, graduated 2012", language="en")
# "Born in nineteen ninety, graduated twenty twelve"
```

### Dates and Times

```python
normalize_text("Meeting on 15/08/2025 at 3:30 pm", language="en")
# "Meeting on fifteenth of August, two thousand and twenty five at three thirty p m"
```

---

## Malay Specifics (`language="ms"`)

### Number Words

Numbers are converted to Malay number words:

| Number | Malay |
|--------|-------|
| 0 | kosong |
| 1 | satu |
| 10 | sepuluh |
| 11 | sebelas |
| 42 | empat puluh dua |
| 100 | seratus |
| 1000 | seribu |
| 1,000,000 | satu juta |

The special contracted forms are used automatically:
- `sebelas` (eleven, not `satu belas`)
- `sepuluh` (ten, but the combined form in compounds)
- `seratus` (one hundred, not `satu ratus`)
- `seribu` (one thousand, not `satu ribu`)

```python
normalize_text("Ada 115 orang", language="ms")
# "Ada seratus lima belas orang"
```

### Currency

Ringgit Malaysia (RM) is the primary currency, with `ringgit` as the main unit and `sen` as the subunit:

```python
normalize_text("Harga RM 450.50", language="ms")
# "Harga empat ratus lima puluh ringgit lima puluh sen"

normalize_text("RM30K untuk projek ni", language="ms")
# "tiga puluh ribu ringgit untuk projek ni"
```

Supported currency symbols: `RM`, `$`, `£`, `EUR`, `USD`, `GBP`, `MYR`. Amount suffixes `K`, `M`, `B`, `T` are expanded to full numbers.

### Date Months

Malay month names are used when normalizing dates:

| Month | Malay |
|-------|-------|
| January | Januari |
| February | Februari |
| March | Mac |
| April | April |
| May | Mei |
| June | Jun |
| July | Julai |
| August | Ogos |
| September | September |
| October | Oktober |
| November | November |
| December | Disember |

```python
normalize_text("Tarikh: 15/08/2025", language="ms")
# "Tarikh: lima belas Ogos dua ribu dua puluh lima"
```

### Time Meridians

Malay time expressions use `pagi` (morning/AM) and `petang` (afternoon/PM):

```python
normalize_text("Jumpa pukul 8:30 pagi", language="ms")
# "Jumpa pukul lapan tiga puluh pagi"
```

### Malaysian Identity Card Numbers (IC)

Malaysian IC numbers (12 digits in `YYMMDD-SS-XXXX` format) are normalized to spoken form:

```python
normalize_text("No IC: 901231-10-5678", language="ms")
# The IC number is expanded digit by digit with structural grouping
```

### Elongated Words

Common in informal Malay text, repeated characters are reduced:

```python
normalize_text("Sedihhh sangat laa", language="ms")
# "Sedih sangat la"
```

### Measurements

Unit abbreviations are expanded to their spoken Malay forms:

```python
normalize_text("Berat 5kg, jarak 10km", language="ms")
# "Berat lima kilogram, jarak sepuluh kilometer"
```

### Decimals and Percentages

```python
normalize_text("Kadar 3.5% setahun", language="ms")
# "Kadar tiga perpuluhan lima peratus setahun"
```

### Hijri Calendar

Islamic/Hijri year conversion is supported:

```python
normalize_text("Tahun Hijri 1446", language="ms")
# Hijri year converted to spoken form
```

---

## Indonesian Specifics (`language="id"`)

### Number Words

Numbers are spoken with Indonesian number words, `koma` for decimal points,
`persen` for percentages, and `miliar`/`triliun` for large magnitudes:

```python
normalize_text("Ada 8 orang, sisa 0", language="id")
# "Ada delapan orang, sisa nol"
```

### Dates

Dates are spoken with Indonesian month names:

```python
normalize_text("pada 15/08/2025", language="id")
# "pada lima belas Agustus dua ribu dua puluh lima"
```

### Written Number Conventions

Indonesian text uses dots as thousands separators and a comma as the decimal
separator. Both are handled, including combined forms:

```python
normalize_text("1.000.000 pengguna", language="id")
# "satu juta pengguna"

normalize_text("naik 3,5%", language="id")
# "naik tiga koma lima persen"

normalize_text("berat 10.000,50 kg", language="id")
# "berat sepuluh ribu koma lima nol kilogram"
```

### Rupiah Currency

`Rp` and `IDR` amounts are spoken as rupiah, including Indonesian money
shorthand where `rb` = ribu, `jt` = juta, and `M` = **miliar** (not million):

```python
normalize_text("Harga Rp1.500.000", language="id")
# "Harga satu juta lima ratus ribu rupiah"

normalize_text("Dana Rp5M", language="id")
# "Dana lima miliar rupiah"

normalize_text("Cuma Rp10rb", language="id")
# "Cuma sepuluh ribu rupiah"
```

### Times

Indonesian meridian words (`pagi`, `siang`, `sore`, `malam`) are recognised,
and `pm` maps to `sore`:

```python
normalize_text("rapat 7:30 pagi, selesai 3:30 sore", language="id")
# "rapat tujuh tiga puluh pagi, selesai tiga tiga puluh sore"
```

---

## Chinese Specifics (`language="zh"` / `language="zh_my"`)

### Number Words

Numbers are converted to Chinese cardinal words following standard conventions:

| Number | Chinese |
|--------|---------|
| 0 | 零 |
| 1 | 一 |
| 10 | 十 |
| 11 | 十一 |
| 100 | 一百 |
| 101 | 一百零一 |
| 1000 | 一千 |
| 10000 | 一万 |
| 100000000 | 一亿 |
| 1000000000000 | 一兆 |

```python
normalize_text("100", language="zh")       # "一百"
normalize_text("10001", language="zh")     # "一万零一"
normalize_text("123456789", language="zh") # "一亿二千三百四十五万六千七百八十九"
```

### Years

Four-digit numbers in the 1000-2099 range are read digit-by-digit:

```python
normalize_text("2025", language="zh")  # "二零二五"
normalize_text("1999", language="zh")  # "一九九九"
```

### Decimals, Percentages and Fraction

```python
normalize_text("一年3.3%的利率。", language="zh") # "一年百分之三点三的利率。"
normalize_text("一年3.3%的利率。", language="zh_my") # "一年三点三巴仙的利率。"
normalize_text("一年1/4的收益。", language="zh") # "一年四分之一的收益。"
```

### Currency

| Symbol | zh (main unit) | zh (sub unit) | zh_my (main unit) | zh_my (sub unit)
|--------|----|-------|
| `RM, MYR` | 令吉 | 仙 | 令吉 | 仙 |
| `$` | 美元 | 分 | 块 | 仙 |
| `USD` | 美元 | 分 | 美元 | 仙 |
| `£, GBP` | 英镑 | 便士 | 英镑 | 仙 |
| `€, EUR` | 欧元 | 分 | 欧元 | 仙 |

```python
normalize_text("RM100.50", language="zh")    # "一百令吉五十仙"
normalize_text("$100.50", language="zh")         # "一百美元五十分"
normalize_text("$50.20", language="zh_my")      # "一百块二十仙"
normalize_text("USD50.20", language="zh_my")     # "五十美元二十仙"
```

### Dates

Dates use Chinese year (digit-by-digit), month, and day names:

```python
normalize_text("15/08/2025", language="zh")   # "二零二五年八月十五日"
normalize_text("2025-12-25", language="zh")    # "二零二五年十二月二十五日"
```

### Times

Time expressions use 上午/下午 (AM/PM) with 点 and 分:

```python
normalize_text("3:30 pm", language="zh")    # "下午三点三十分"
normalize_text("9:00 am", language="zh")    # "上午九点"
normalize_text("14:30", language="zh")      # "十四点三十分"
normalize_text("早上13:15", language="zh")   # "早上十三点十五分" 
```

### Temperature and Measurements

```python
normalize_text("25C", language="zh")      # "二十五摄氏度"
normalize_text("36.5C", language="zh")    # "三十六点五摄氏度"
normalize_text("5km", language="zh")      # "五公里"
normalize_text("10kg", language="zh")     # "十公斤"
normalize_text("200ml", language="zh")    # "二百毫升"
```

### Malaysian Identity Card Numbers (IC)

Malaysian IC numbers (12 digits in `YYMMDD-SS-XXXX` format) are normalized to spoken form:

```python
normalize_text("No IC: 901231-10-5678", language="zh")  # 九 零 一 二 三 一 一 零 五 六 七 八
```

### Feature Toggles

All config flags (`disable`, `profile`) work consistently for Chinese:

```python
normalize_text("25C", language="zh", disable=["temperature"])  # "25C"
normalize_text("25C", language="zh", profile="minimal")         # "25C"
normalize_text("25C", language="zh", profile="standard")        # "二十五摄氏度"
```

---

## Common Gotchas

### DD/MM vs MM/DD Date Ambiguity

The library assumes **DD/MM/YYYY** format (common in Malaysia and most of the world), not MM/DD/YYYY (US format). This is a heuristic-based approach and ambiguous dates where both day and month are 12 or less may be parsed incorrectly.

```python
# Unambiguous: day > 12
normalize_text("15/08/2025", language="en")
# "fifteenth of August, two thousand and twenty five" (correct)

# Ambiguous: both <= 12
normalize_text("05/06/2025", language="en")
# Treated as 5th of June (DD/MM), not June 5th (MM/DD)
```

If your source text uses US date format (MM/DD/YYYY), consider pre-processing dates before passing them to revo-norm.

### "RM" in Currency vs Other Meanings

`RM` is recognized as Ringgit Malaysia in currency contexts. In non-currency contexts, it may be treated differently:

```python
# Currency context -- handled correctly
normalize_text("Harga RM 450", language="ms")
# "Harga empat ratus lima puluh ringgit"

# As part of a word or acronym -- protected by pronunciation mappings
normalize_text("The RM team", language="en")
# "The R M team" (split as acronym)
```

### All-Caps Tech Terms (AI, ML, LLM)

All-caps tech terms like `AI`, `ML`, `LLM`, `GPU`, `API` are handled by the pronunciation mappings and acronym expansion systems. The pipeline applies pronunciation mappings first (highest priority), then acronym expansion:

```python
# AI, ML, LLM -- split letter by letter by expand_acronym()
normalize_text("Train ML models with AI", language="en")
# "Train M L models with A I"

# GUI -- mapped to "gooey" by pronunciation mappings (applied first)
normalize_text("Build a GUI app", language="en")
# "Build a gooey app"

# Custom pronunciation
from revo_norm.pronunciation_mappings import add_custom_mapping
add_custom_mapping("YOLO", "you only live once", "en")
normalize_text("YOLO approach", language="en")
# "you only live once approach"
```

### Entity Extraction Protects Patterns

The entity extraction system runs early in the pipeline and protects recognized patterns from being mangled by downstream transformations. This prevents issues like:

- `RM 450` being split into `R M 450` by acronym expansion (currency is extracted as an entity first)
- Dates like `15/08/2025` being interpreted as fractions
- URLs containing numbers from being partially converted

If a specific entity type is causing issues, you can disable it:

```python
normalize_text(text, language="ms", disable=["fractions"])
```
