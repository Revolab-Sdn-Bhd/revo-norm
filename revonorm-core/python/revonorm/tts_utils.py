"""
TTS-specific utility functions for the ChatterBox backend.

This module contains features specific to TTS processing that should NOT
be in the general text normalization library (revo-norm).

Features:
- Sentence splitting and chunking for TTS
- Random comma insertion for pauses
- Sound word removal (laughter, applause, etc.)
- Repetitive sequence detection
"""

import random
import re


def normalize_problematic_chars(text: str) -> str:
    """
    Normalize problematic Unicode characters that confuse TTS models.
    - Em dashes to commas (for pauses)
    - Smart quotes to straight quotes
    - Excessive quote sequences
    """
    # Replace em dashes and en dashes with commas or spaces (for pauses)
    text = re.sub(r"[—–]", ", ", text)

    # Normalize all quote variations to straight single quotes
    text = text.replace('"', "'").replace('"', "'")
    text = text.replace(""", "'").replace(""", "'")
    text = text.replace("`", "'")  # Backtick to quote

    # Remove excessive quote sequences but keep single quotes for dialogue
    text = re.sub(r"'+", "'", text)
    text = re.sub(r'"+', '"', text)

    # Clean up any double spaces or commas
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r",\s*,", ",", text)

    return text.strip()


def parse_sound_word_field(user_input: str) -> list[tuple[str, str]]:
    """Parse sound word field input into list of (pattern, replacement) tuples."""
    lines = [line.strip() for line in user_input.split("\n") if line.strip()]
    result = []
    for line in lines:
        if "=>" in line:
            pattern, replacement = line.split("=>", 1)
            result.append((pattern.strip(), replacement.strip()))
        else:
            result.append((line, ""))
    return result


def smart_remove_sound_words(text: str, sound_words: list[tuple[str, str]]) -> str:
    """Remove or replace sound words like [laughter], [applause] from text."""
    for pattern, replacement in sound_words:
        if replacement:
            text = re.sub(
                rf"(?i)({re.escape(pattern)})([" "']s?)",
                lambda m, repl=replacement: repl + "'s" if m.group(2) else repl,
                text,
            )
            text = re.sub(
                rf'(["\']){re.escape(pattern)}(["\'])',
                lambda m, repl=replacement: f"{m.group(1)}{repl}{m.group(2)}",
                text,
                flags=re.IGNORECASE,
            )
            if all(char in "-——" for char in pattern.strip()):
                text = re.sub(re.escape(pattern), replacement, text)
            else:
                text = re.sub(
                    rf"\b{re.escape(pattern)}\b", replacement, text, flags=re.IGNORECASE
                )
        else:
            text = re.sub(rf"{re.escape(pattern)}", "", text, flags=re.IGNORECASE)

    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"([,\s]+,)+", ",", text)
    text = re.sub(r",\s*,+", ",", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"(\s+,|,\s+)", ", ", text)
    text = re.sub(r"(^|[\.!\?]\s*),+", r"\1", text)
    text = re.sub(r",+\s*([\.!\?])", r"\1", text)
    return text.strip()


def split_repetitive_sequences(
    text: str, min_repeat_length: int = 1, repeat_threshold: int = 3
) -> list[str]:
    """Split text with repetitive sequences into separate segments."""
    original_words = text.split()
    clean_words = [re.sub(r"[^\w\s]", "", w).lower() for w in original_words]

    if len(clean_words) < min_repeat_length * repeat_threshold:
        return [text]

    segments = []
    current_segment_words = []

    i = 0
    while i < len(clean_words):
        found_repetition = False
        for length in range(min_repeat_length, (len(clean_words) - i) // repeat_threshold + 1):
            if i + length * repeat_threshold <= len(clean_words):
                pattern = clean_words[i : i + length]
                is_repetitive = True
                for k in range(1, repeat_threshold):
                    if clean_words[i + k * length : i + (k + 1) * length] != pattern:
                        is_repetitive = False
                        break

                if is_repetitive:
                    if current_segment_words:
                        segments.append(" ".join(current_segment_words))
                        current_segment_words = []

                    segments.append(
                        " ".join(original_words[i : i + length * repeat_threshold]) + "."
                    )
                    i += length * repeat_threshold
                    found_repetition = True
                    break

        if not found_repetition:
            current_segment_words.append(original_words[i])
            i += 1

    if current_segment_words:
        segments.append(" ".join(current_segment_words))

    return [s.strip() for s in segments if s.strip()]


# Malay, Indonesian and English digit words produced by num2word expansion
_DIGIT_WORDS = frozenset({
    "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "lapan", "sembilan", "kosong",
    "puluh", "ratus", "ribu", "juta", "belas", "perpuluhan",
    "delapan", "nol", "koma", "miliar", "triliun",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "zero",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty",
    "sixty", "seventy", "eighty", "ninety",
    "hundred", "thousand", "million", "billion", "point",
})


def _is_digit_word(word: str) -> bool:
    return word.strip(",.;:!?").lower() in _DIGIT_WORDS


def add_random_commas(
    text: str, min_words: int = 8, max_words: int = 15, digit_group_size: int = 4
) -> str:
    """
    Add random commas for pauses in TTS output.

    Rules:
    - Only add commas after many words (min_words=8, not 2-5)
    - Don't add comma if there's already punctuation within 8 words
    - Don't add comma if near end of sentence
    - Insert commas between digit-word groups (every digit_group_size words)
    - Deterministic: same input always produces same output (seeded by text hash)

    Args:
        text: Input text
        min_words: Minimum words before considering a comma (default=8)
        max_words: Maximum words before forcing a comma (default=15)
        digit_group_size: Insert comma every N digit words (default=4)
    """
    words = text.split()
    if len(words) < min_words:
        return text

    rng = random.Random(hash(text))

    # Pre-compute digit-word runs: 2+ consecutive digit words (e.g. number expansions)
    in_digit_run = [False] * len(words)
    i = 0
    while i < len(words):
        if _is_digit_word(words[i]):
            start = i
            while i < len(words) and _is_digit_word(words[i]):
                i += 1
            run_len = i - start
            if run_len >= 2:
                for j in range(start, i):
                    in_digit_run[j] = True
        else:
            i += 1

    new_words = []
    word_count = 0
    digit_count = 0  # Track consecutive digit words within a run

    for i, word in enumerate(words):
        new_words.append(word)

        # Reset counter on any existing punctuation (sentence end or comma)
        ends_sentence = re.search(r"[.!?]$", word)
        has_comma = "," in word

        if ends_sentence or has_comma:
            word_count = 0
            digit_count = 0
            continue

        # Within digit-word runs: insert comma every digit_group_size words
        if in_digit_run[i]:
            digit_count += 1
            if digit_count >= digit_group_size and i + 1 < len(words) and in_digit_run[i + 1]:
                new_words.append(",")
                digit_count = 0
            continue

        word_count += 1

        # Only consider adding comma if enough words have passed
        if word_count >= min_words and i < len(words) - 1:
            # Check if there's punctuation coming up soon (within 8 words)
            upcoming_punctuation = False
            for j in range(i + 1, min(i + 9, len(words))):
                if re.search(r"[.!?,:;]", words[j]):
                    upcoming_punctuation = True
                    break

            # Add comma with probability proportional to word count
            if not upcoming_punctuation and word_count <= max_words:
                # Higher chance as word count increases
                chance = word_count / max_words
                if rng.random() < chance:
                    new_words.append(",")
                    word_count = 0
            elif word_count >= max_words:
                # Force comma if max words reached (but still check for upcoming punctuation)
                if not upcoming_punctuation and i < len(words) - 3:
                    new_words.append(",")
                    word_count = 0

    return " ".join(new_words).replace(" ,", ",")


def split_text_by_words(text: str, max_chars: int = 150) -> list[str]:
    """
    Split text into chunks by word boundaries (respects word integrity).

    This function ensures that words are never cut in half. It splits
    text into chunks that are approximately max_chars long, but will
    exceed this limit if necessary to avoid cutting a word.

    Args:
        text: Input text to split
        max_chars: Target maximum characters per chunk (default: 150)

    Returns:
        List of text chunks, each containing complete words

    Example:
        >>> split_text_by_words("the secret passage under the cottage", 20)
        ['the secret passage', 'under the cottage']
        >>> split_text_by_words("Di halaman rumah nenek", 10)
        ['Di halaman', 'rumah nenek']
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        word_len = len(word)

        # Check if adding this word would exceed max_chars
        # Only start a new chunk if we already have content
        if current_chunk and current_length + word_len + 1 > max_chars:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.append(word)
        current_length += word_len + (1 if current_chunk else 0)

    # Add the last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
