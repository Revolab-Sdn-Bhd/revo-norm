# Acronym Normalization

## Overview

Acronym normalization converts written acronyms and initialisms into their spoken form for TTS. It handles letter-period sequences (I.B.M.), all-caps abbreviations (IBM, API), and hyphenated forms (GPU-accelerated). A pronunciation mappings system provides overrides for terms that should be spoken differently from letter-by-letter splitting.

Acronym expansion runs late in the pipeline, after pronunciation mappings, entity extraction, and language-specific normalization have already processed the text.

## Expansion Rules

The `expand_acronym()` function applies rules in priority order:

1. **Pronunciation mappings** -- applied first in the pipeline, before any other transformation (see below).
2. **Preserved as-is** -- certain acronyms are kept unchanged (e.g., `NASA`).
3. **Always split** -- specific tech acronyms are always split letter-by-letter.
4. **Always spell** -- Malaysian university/org acronyms that must be spelled out.
5. **Pronounceable word** -- 4+ letter acronyms with 30-60% vowel density are pronounced as words.
6. **C-V-C pattern** -- consonant-vowel-consonant tail pattern (e.g., `JSON` → `J son`).
7. **Default** -- split all letters.

### Preserved Acronyms

These acronyms are kept as-is because they are pronounceable as complete words:

| Acronym | Output |
|---------|--------|
| NASA    | NASA   |

### Always-Split Acronyms

These tech acronyms are always split letter-by-letter, regardless of pronounceability:

| Acronym | Output  |
|---------|---------|
| API     | A P I   |
| GPU     | G P U   |
| CPU     | C P U   |
| AI      | A I     |
| ML      | M L     |
| DL      | D L     |
| NLP     | N L P   |
| LLM     | L L M   |
| RL      | R L     |
| PLUS    | P L U S |

### Always-Spell (Malaysian Universities/Orgs)

These Malaysian university and organization acronyms are always spelled letter-by-letter, even though some look pronounceable:

| Acronym | Output    |
|---------|-----------|
| UITM    | U I T M   |
| UKM     | U K M     |
| USM     | U S M     |
| UTM     | U T M     |
| UPNM    | U P N M   |
| IIUM    | I I U M   |
| UM      | U M       |
| UPM     | U P M     |

### Pronounceable Word Detection

For 4+ letter acronyms not in any special list, the system checks vowel density. If 30-60% of the letters are vowels and the word has consonants, it's treated as a pronounceable word and converted to lowercase:

| Acronym  | Vowel Ratio | Output      |
|----------|-------------|-------------|
| MARA     | 50%         | mara        |
| JAKIM    | 40%         | jakim       |
| FELDA    | 40%         | felda       |
| BERNAMA  | 43%         | bernama     |
| PETRONAS | 38%         | petronas    |
| FINAS    | 40%         | finas       |
| RAPID    | 40%         | rapid       |
| BERNAS   | 33%         | bernas      |
| PTPTN    | 0%          | P T P T N   |

### C-V-C Pattern (Generalized Rule)

For 3+ letter acronyms that don't match the pronounceable word check, the generalized rule checks the tail (all letters after the first). If the tail has a consonant at the start, a vowel somewhere in the middle, and a consonant at the end, the first letter is spoken individually and the tail is pronounced as a word.

| Acronym | Tail Analysis | Output |
|---------|---------------|--------|
| JSON    | "son" -- consonant-vowel-consonant | J son |
| JPEG    | "peg" -- consonant-vowel-consonant | J peg |
| PNG     | "ng" -- too short | P N G |
| FBI     | "bi" -- too short | F B I |

Acronyms that don't match any rule are split letter-by-letter by default.

## Letter-Period Sequences

Letter-period sequences (with dots between letters) are expanded by removing the periods and inserting spaces:

```python
from revonorm import normalize_text

normalize_text("I.B.M. released a new chip", language="en")
# "I B M released a new chip"

normalize_text("U.S.A. today", language="en")
# "U S A today"

normalize_text("I.T. department", language="en")
# "I T department"
```

## Hyphenated Acronyms

Hyphens between letters or between an acronym and a word are replaced with spaces:

```python
normalize_text("GPU-accelerated rendering", language="en")
# "G P U accelerated rendering"

normalize_text("AI-powered tools", language="en")
# "A I powered tools"

normalize_text("state-of-the-art", language="en")
# "state of the art"
```

## Pronunciation Mappings Override

Pronunciation mappings are applied **before** acronym expansion and have the highest priority in the pipeline. They override the default behavior for specific terms.

```python
from revonorm import normalize_text

# GUI -> gooey (not "G U I")
normalize_text("Build a GUI interface", language="en")
# "Build a gooey interface"

# ASCII -> as key (not "A S C I I")
normalize_text("ASCII art", language="en")
# "as key art"

# GIF -> gif (not "G I F")
normalize_text("GIF format", language="en")
# "gif format"

# IEEE -> I triple E (not "I E E E")
normalize_text("IEEE standard", language="en")
# "I triple E standard"

# WiFi -> why fi (not "W I F I")
normalize_text("Connect to WiFi", language="en")
# "Connect to why fi"

# iOS -> I O S (not "i O S")
normalize_text("iOS update", language="en")
# "I O S update"
```

### Adding Custom Pronunciation Mappings

Mappings must represent **how a term sounds when spoken**, not what it stands for. The system validates against abbreviation expansions.

```python
from revonorm.pronunciation_mappings import add_custom_mapping
from revonorm import normalize_text

# Add a pronunciation mapping
add_custom_mapping("SQL", "sequel")

normalize_text("Query the SQL database", language="en")
# "Query the sequel database"

# This will raise ValueError -- it's an expansion, not a pronunciation
# add_custom_mapping("YOLO", "you only live once")
```

Custom mappings apply globally (across all languages) and are matched as whole words, case-insensitively.

### Built-in Pronunciation Mappings

| Term   | Spoken Form  |
|--------|--------------|
| GUI    | gooey        |
| ASCII  | as key       |
| IEEE   | I triple E   |
| GIF    | gif          |
| WiFi   | why fi       |
| iOS    | I O S        |
| bias   | bai yers     |
| Hj     | Haji         |
| Hjh    | Hajah        |
| Dr     | Doktor       |
| Prof   | Profesor     |
| Dato'  | Dato         |

## How to Disable

```python
from revonorm import normalize_text

# Disable acronym expansion entirely
result = normalize_text("The API is fast", language="en", disable=["acronyms"])
# "The API is fast"  (unchanged)

# Disable with minimal profile
result = normalize_text("The API is fast", language="en", profile="minimal")
# "The API is fast"  (no acronym expansion)
```

## Edge Cases

- **Length limit**: Only acronyms of 2-10 uppercase letters are expanded. Longer sequences are left as-is.
- **Lowercase/mixed case**: Only fully uppercase words are treated as acronyms. `Api` and `api` are not expanded.
- **Inside entity placeholders**: Acronyms inside entity placeholders (`<<<...>>>`) are protected from expansion.
- **Pronunciation mappings run first**: Even with acronyms disabled, pronunciation mappings still apply. They are a separate pipeline step.
- **After language normalizer**: Acronym expansion runs after language-specific normalization, so numbers have already been converted.
- **Letter-period minimum**: At least 2 letter-period pairs are required: `A.` is not expanded, but `A.B.` is.
