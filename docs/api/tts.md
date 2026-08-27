# TTS Utilities

Post-processing utilities for TTS applications. These functions operate on already-normalized text and are **not** called by `normalize_text()`. Use them as separate post-processing steps after normalization.

## `parse_sound_word_field`

::: revonorm.tts_utils.parse_sound_word_field

Parse a user-provided sound word field into a list of `(pattern, replacement)` tuples.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `user_input` | `str` | required | Multi-line string. Each line is either `"pattern => replacement"` or `"pattern"` (removal) |

**Returns:** `list[tuple[str, str]]` — List of `(pattern, replacement)` tuples. If no `=>` separator is present, the replacement is an empty string (meaning the pattern will be removed entirely).

```python
from revonorm.tts_utils import parse_sound_word_field

# With replacements
result = parse_sound_word_field("[laughter] => haha\n[applause] => clap")
# [("[laughter]", "haha"), ("[applause]", "clap")]

# With removal (no =>)
result = parse_sound_word_field("[music]\n[breath]")
# [("[music]", ""), ("[breath]", "")]
```

## `smart_remove_sound_words`

::: revonorm.tts_utils.smart_remove_sound_words

Remove or replace sound words (like `[laughter]`, `[applause]`) from text. Handles possessives (`'s`), quoted occurrences, and cleans up resulting whitespace and punctuation artifacts.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `text` | `str` | required | Input text containing sound words |
| `sound_words` | `list[tuple[str, str]]` | required | List of `(pattern, replacement)` tuples, typically from `parse_sound_word_field` |

**Returns:** `str` — Text with sound words removed or replaced and whitespace cleaned up.

```python
from revonorm.tts_utils import parse_sound_word_field, smart_remove_sound_words

# Remove sound words
words = parse_sound_word_field("[laughter]\n[applause] => clapping")
text = "Hello [laughter] world [applause] end"
result = smart_remove_sound_words(text, words)
# "Hello world clapping end"

# Removal with possessive handling
words = parse_sound_word_field("[laughter]")
text = "That was [laughter]'s best moment"
result = smart_remove_sound_words(text, words)
# "That was best moment"
```

## `add_random_commas`

::: revonorm.tts_utils.add_random_commas

Insert random commas into long text to create natural pauses for TTS. Uses a smart algorithm that avoids inserting commas near existing punctuation, at sentence boundaries, or too close to sentence endings.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `text` | `str` | required | Input text |
| `min_words` | `int` | `8` | Minimum number of words before considering a comma |
| `max_words` | `int` | `15` | Maximum number of words before forcing a comma |

**Returns:** `str` — Text with optional commas inserted for natural pauses.

```python
from revonorm.tts_utils import add_random_commas

text = "The quick brown fox jumps over the lazy dog and then runs across the field"
result = add_random_commas(text)
# Comma inserted after a natural pause point (exact position varies due to randomness)

# Short text — no commas inserted
short = "Hello world"
result = add_random_commas(short)
# "Hello world" (unchanged, fewer than min_words=8 words)
```

## `split_text_by_words`

::: revonorm.tts_utils.split_text_by_words

Split text into chunks by word boundaries. Ensures words are never cut in half. Each chunk contains complete words and is approximately `max_chars` characters long.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `text` | `str` | required | Input text to split |
| `max_chars` | `int` | `150` | Target maximum characters per chunk |

**Returns:** `list[str]` — List of text chunks, each containing complete words.

```python
from revonorm.tts_utils import split_text_by_words

chunks = split_text_by_words("the secret passage under the cottage", 20)
# ["the secret passage", "under the cottage"]

chunks = split_text_by_words("Di halaman rumah nenek", 10)
# ["Di halaman", "rumah nenek"]
```

## Integration Example

These utilities are designed to be used as post-processing steps after `normalize_text()`:

```python
from revonorm import normalize_text
from revonorm.tts_utils import (
    add_random_commas,
    parse_sound_word_field,
    smart_remove_sound_words,
    split_text_by_words,
)

# Step 1: Normalize
text = "The API costs $5.50 and [laughter] runs on 5km of cable"
normalized = normalize_text(text, language="en")

# Step 2: Remove sound words
sound_words = parse_sound_word_field("[laughter]")
clean = smart_remove_sound_words(normalized, sound_words)

# Step 3: Add pauses for TTS
with_pauses = add_random_commas(clean)

# Step 4: Chunk for TTS synthesis
chunks = split_text_by_words(with_pauses, max_chars=200)
```
