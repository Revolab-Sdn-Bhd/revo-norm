"""
Revo Norm — unified single-pipeline text normalizer for TTS.

Public API
----------
    normalize_text(text, language, profile, disable)

Everything else is an internal helper.
"""

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from revo_norm.config import SUPPORTED_LANGUAGES, Config
from revo_norm.currency_utils import (
    CURRENCY_B_SUFFIX_PATTERN,
    CURRENCY_JUTA_PATTERN,
    CURRENCY_K_SUFFIX_PATTERN,
    CURRENCY_M_SUFFIX_PATTERN,
    CURRENCY_MILIAR_PATTERN,
    CURRENCY_RIBU_PATTERN,
    CURRENCY_T_SUFFIX_PATTERN,
    CURRENCY_TRILIUN_PATTERN,
    expand_currency_b_suffix,
    expand_currency_k_suffix,
    expand_currency_m_suffix,
    expand_currency_t_suffix,
)
from revo_norm.langpack import get_pack
from revo_norm.pronunciation_mappings import (
    apply_pronunciation_mappings,
    resolve_pronunciations,
)
from revo_norm.shared_features import (
    normalize_elongated_text,
    normalize_measurements,
    normalize_x_kali_text,
)
from revo_norm.tts_utils import parse_sound_word_field, smart_remove_sound_words

if TYPE_CHECKING:
    from revo_norm.entity_extractor import EntityExtractor

# ===================================================================
# Internal helpers (used by entity_extractor too)
# ===================================================================


def _normalize_whitespace(text: str) -> str:
    """Collapse multiple whitespace to single space and strip."""
    return re.sub(r"\s{2,}", " ", text.strip())


# Public alias kept for backward compat
normalize_whitespace = _normalize_whitespace


# Digit-to-word mapping
_DIGIT_WORDS = {
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
}

_DIGIT_WORDS_MS = {
    "0": "kosong",
    "1": "satu",
    "2": "dua",
    "3": "tiga",
    "4": "empat",
    "5": "lima",
    "6": "enam",
    "7": "tujuh",
    "8": "lapan",
    "9": "sembilan",
}

_DIGIT_WORDS_ID = {
    "0": "nol",
    "1": "satu",
    "2": "dua",
    "3": "tiga",
    "4": "empat",
    "5": "lima",
    "6": "enam",
    "7": "tujuh",
    "8": "delapan",
    "9": "sembilan",
}

_DIGIT_WORDS_ZH = {
    "0": "零",
    "1": "一",
    "2": "二",
    "3": "三",
    "4": "四",
    "5": "五",
    "6": "六",
    "7": "七",
    "8": "八",
    "9": "九",
}


def _digit_word(digit: str, language: str) -> str:
    """Convert a single digit to its spoken word."""
    return get_pack(language).digit_words.get(digit, digit)


def email_to_spoken(email: str, language: str = "en") -> str:
    """Convert an email address to spoken-friendly form for TTS."""
    if language == "zh":
        spoken = email.replace("@", "艾特")
        spoken = spoken.replace(".", "点")
        spoken = spoken.replace("_", "下划线")
        spoken = spoken.replace("+", "加")
        spoken = spoken.replace("-", "杠")
    else:
        spoken = email.replace("@", " at ")
        spoken = spoken.replace(".", " dot ")
        spoken = spoken.replace("_", " underscore ")
        spoken = spoken.replace("+", " plus ")
        spoken = spoken.replace("-", " dash ")

    spoken = re.sub(r"(?<=[a-zA-Z])(?=\d)|(?<=\d)(?=[a-zA-Z])", " ", spoken)
    spoken = re.sub(
        r"\d+", lambda m: " ".join(_digit_word(c, language) for c in m.group(0)), spoken
    )

    return re.sub(r"\s+", " ", spoken).strip()


_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", re.IGNORECASE)


def convert_emails_to_spoken(text: str, language: str = "en") -> str:
    """Replace all email addresses in *text* with spoken form."""
    return _EMAIL_RE.sub(lambda m: email_to_spoken(m.group(0), language), text)


_USSD_RE = re.compile(r"\*(\d+)#")


def _expand_ussd_codes(text: str, language: str) -> str:
    """Expand USSD codes (*120#) to digit-by-digit spoken form."""

    def _replace(m: re.Match) -> str:
        digits = " ".join(_digit_word(d, language) for d in m.group(1))
        return f"star {digits} hash"

    return _USSD_RE.sub(_replace, text)


# Numbers after these words should be read digit-by-digit
_DIGIT_BY_DIGIT_CTX_RE = re.compile(
    r"\b(exit|gate|lot|platform|bus\s+no|flight|stand|bay|block|blok)"
    r"\s+(\d+)\b",
    re.IGNORECASE,
)

# Product/model names with 3+ digit numbers read digit-by-digit
_PRODUCT_DIGIT_CTX_RE = re.compile(
    r"\b(Office|Windows|PlayStation|PS|Xbox|iPhone|iPad|Galaxy|Pixel|Model|MacBook|AirPods)"
    r"\s+(\d{3,})\b",
    re.IGNORECASE,
)


def _expand_digit_by_digit_context(text: str, language: str) -> str:
    """Expand numbers in specific contexts (exit, gate, lot, etc.) digit-by-digit."""

    def _replace(m: re.Match) -> str:
        prefix = m.group(1)
        digits = " ".join(_digit_word(d, language) for d in m.group(2))
        return f"{prefix} {digits}"

    text = _DIGIT_BY_DIGIT_CTX_RE.sub(_replace, text)
    text = _PRODUCT_DIGIT_CTX_RE.sub(_replace, text)
    return text


def _spell_special_chars(text: str, language: str = "en") -> str:
    """Spell out symbols (&, *, #, %, +, =, etc.) that TTS engines otherwise
    read as their raw character name instead of skipping or pronouncing sensibly."""
    symbols = get_pack(language).symbol_words
    for char, replacement in symbols.items():
        text = text.replace(char, f" {replacement} ")
    return re.sub(r"\s+", " ", text).strip()


def url_to_spoken(url: str, language: str = "en") -> str:
    """Convert a URL into spoken-friendly form for TTS."""
    spoken = url
    if "://" in spoken:
        protocol, _ = spoken.split("://", 1)
        protocol_spoken = " ".join(list(protocol))
        if language == "zh":
            spoken = spoken.replace(f"{protocol}://", f"{protocol_spoken} 冒号斜杠斜杠")
        elif language == "zh_my":
            spoken = spoken.replace(f"{protocol}://", f"{protocol_spoken} 冒号 slash slash ")
        else:
            spoken = spoken.replace(f"{protocol}://", f"{protocol_spoken} colon slash slash ")

    if language == "zh":
        spoken = re.sub(r"www\.?", "w w w 点 ", spoken)
    else:
        spoken = re.sub(r"www\.?", "w w w dot ", spoken)

    def _replace_port(m: re.Match, language: str) -> str:
        if language in ("zh", "zh_my"):
            return "冒号" + " ".join(_digit_word(c, language) for c in m.group(1))
        else:
            return " colon " + " ".join(_digit_word(c, language) for c in m.group(1))

    spoken = re.sub(r":(\d+)", lambda m: _replace_port(m, language), spoken)

    if language == "zh":
        spoken = spoken.replace(".", "点")
        spoken = spoken.replace("/", "斜杠")
        spoken = spoken.replace("-", "杠")
    else:
        spoken = spoken.replace(".", " dot ")
        spoken = spoken.replace("/", " slash ")
        spoken = spoken.replace("-", " dash ")

    # Query strings/fragments carry ?, =, &, *, ! that would otherwise reach
    # the TTS engine as raw characters instead of being spoken/dropped.
    if language in ("zh", "zh_my"):
        spoken = spoken.replace("?", " 问号 ").replace("=", " 等于 ")
    else:
        spoken = spoken.replace("?", " question mark ").replace("=", " equals ")
    if language in ("zh", "zh_my"):
        spoken = spoken.replace("&", " 和 ").replace("*", " 星号 ")
    else:
        star_word = " " if language in ("en", "ms") else " star "
        spoken = spoken.replace("&", " and ").replace("*", star_word)
    # "!" is only dropped for en/ms; id/zh/zh_my keep it as-is.
    if language in ("en", "ms"):
        spoken = spoken.replace("!", "")

    if language in ("zh", "zh_my"):
        spoken = re.sub(
            r"\d+", lambda m: " ".join(_digit_word(c, language) for c in m.group(0)), spoken
        )
    else:
        spoken = re.sub(
            r"\d+", lambda m: " ".join(_digit_word(c, language) for c in m.group(0)), spoken
        )

    return re.sub(r"\s+", " ", spoken).strip()


_URL_RE = re.compile(
    r"(?:[a-zA-Z][a-zA-Z0-9+.-]*://|www\.)[^\s]+|"
    r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/[^\s]*)?|"
    r"\b[A-Za-z0-9-]+\.[A-Za-z]{2,}(?:/[^\s]*)?",
    re.IGNORECASE,
)


def convert_urls_to_spoken(text: str, language: str = "en") -> str:
    """Replace all URLs in *text* with spoken form."""
    return _URL_RE.sub(lambda m: url_to_spoken(m.group(0), language), text)


def replace_letter_period_sequences(text: str, process_acronyms: bool = True) -> str:
    """Replace letter-period sequences (I.B.M. -> I B M) and optionally expand acronyms."""

    def _replacer_periods(m: re.Match) -> str:
        return " ".join(m.group(0).rstrip(".").split("."))

    text = re.sub(r"\b(?:[A-Za-z]\.){2,}\.?", _replacer_periods, text)
    text = re.sub(r"(?<=[A-Za-z])-(?=[A-Za-z])", " ", text)

    if process_acronyms:
        text = re.sub(r"\b[A-Z]{2,10}\b", lambda m: expand_acronym(m.group(0)), text)

    return text


# Backward-compat alias
expand_capitalized_initialisms = replace_letter_period_sequences


def remove_inline_reference_numbers(text: str) -> str:
    """Remove reference numbers after punctuation."""
    return re.sub(r'([.!?,\\\'"\)\]])(\d+)(?=\s|$)', r"\1", text)


def expand_acronym(acronym: str) -> str:
    """Expand an acronym into spoken form.

    Rules:
    1. PRESERVE as-is: NASA
    2. SPLIT letter-by-letter: API, GPU, CPU, AI, ML, LLM, etc.
    3. ALWAYS SPELL: Malaysian university/org acronyms (UITM, UKM, etc.)
    4. Pronounceable word (4+ letters, 30-60% vowels): MARA -> mara, FELDA -> felda
    5. C-V-C pattern: JSON -> J son
    6. Otherwise split all letters.
    """
    vowels = set("aeiou")

    # Explicit word expansions — checked before any heuristic
    EXPAND_AS = {"SDN": "sendirian", "BHD": "berhad"}  # noqa: N806
    if acronym in EXPAND_AS:
        return EXPAND_AS[acronym]

    PRESERVE_THESE = {"NASA", "PLUS"}  # noqa: N806
    if acronym in PRESERVE_THESE:
        return acronym

    SPLIT_THESE = {"API", "GPU", "CPU", "AI", "ML", "DL", "NLP", "LLM", "RL", "PLUS"}  # noqa: N806
    if acronym in SPLIT_THESE:
        return " ".join(list(acronym))

    ALWAYS_SPELL = {"UITM", "UKM", "USM", "UTM", "UPNM", "IIUM", "UM", "UPM"}  # noqa: N806
    if acronym in ALWAYS_SPELL:
        return " ".join(list(acronym))

    vowel_count = sum(1 for ch in acronym if ch.lower() in vowels)
    # Y acts as a vowel when it ends the word (e.g. CENTURY, ARMY, DUTY)
    if len(acronym) > 1 and acronym[-1].lower() == "y":
        vowel_count += 1
    vowel_ratio = vowel_count / len(acronym) if acronym else 0
    has_consonants = any(ch.lower() not in vowels and ch.lower() != "y" for ch in acronym)

    if len(acronym) >= 4 and 0.3 <= vowel_ratio <= 0.6 and has_consonants:
        return acronym.lower()

    rest = acronym[1:].lower()
    has_vowel_in_middle = any(ch in vowels for ch in rest[1:-1])
    if len(rest) >= 3 and rest[0] not in vowels and rest[-1] not in vowels and has_vowel_in_middle:
        return f"{acronym[0]} {rest}"
    return " ".join(list(acronym))


def expand_abbreviations(text: str, language: str = "en") -> str:
    """No-op placeholder. Abbreviation expansion is disabled."""
    return text


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences using basic regex."""
    return [s.strip() for s in re.compile(r"(?<=[.!?])\s+(?=[A-Z])").split(text) if s.strip()]


def insert_comma_after_repeated_words(text: str, min_repeat: int = 3) -> str:
    """Insert comma after repeated words, but not within digit-word sequences."""
    from revo_norm.tts_utils import _is_digit_word

    pattern = re.compile(r"\b(?P<word>\w+)\b(?: \1){" + str(min_repeat) + r",}", re.IGNORECASE)

    def _replacer(m: re.Match) -> str:
        if _is_digit_word(m.group("word")):
            return m.group(0)
        words = m.group(0).split()
        return " ".join(words[:-1]) + ", " + words[-1]

    return pattern.sub(_replacer, text)


# Pre-compiled pronunciation override patterns
_PRONUNCIATION_OVERRIDE_PATTERNS = [
    (re.compile(r"\btwenty-three\b", re.IGNORECASE), "twenty tree"),
    (re.compile(r"\bthree\b", re.IGNORECASE), "three"),
    (re.compile(r"\btwenty-eight\b", re.IGNORECASE), "twenty, eight"),
    (re.compile(r"\bcut-off\b", re.IGNORECASE), "kad off"),
    (re.compile(r"\beighty-eight\b", re.IGNORECASE), "eighty eight"),
    (re.compile(r"\bNumber\b", re.IGNORECASE), "number"),
    (re.compile(r"\ba/l\b", re.IGNORECASE), "anak lelaki"),
    (re.compile(r"\ba/p\b", re.IGNORECASE), "anak perempuan"),
    (re.compile(r"\b1Malaysia\b", re.IGNORECASE), "satu malaysia"),
    # Malaysian company suffixes — must be matched as a pair to avoid
    # "SDN" or "BHD" expanding in unrelated contexts
    (re.compile(r"\bsdn\.?\s+bhd\b\.?", re.IGNORECASE), "sendirian berhad"),
]

_PRONUNCIATION_UNIT_MAP = {
    "mg": (re.compile(r"(\d+)\s*mg\b", re.IGNORECASE), "milligram"),
    "kg": (re.compile(r"(\d+)\s*kg\b", re.IGNORECASE), "kilogram"),
    "GB": (re.compile(r"(\d+)\s*GB\b", re.IGNORECASE), "gigabyte"),
}


def apply_pronunciation_overrides(text: str, language: str = "en") -> str:
    """Apply pronunciation overrides for specific words and phrases."""
    for pattern, replacement in _PRONUNCIATION_OVERRIDE_PATTERNS:
        text = pattern.sub(replacement, text)
    if language not in ("zh", "zh_my"):
        for _unit, (pattern, spoken) in _PRONUNCIATION_UNIT_MAP.items():
            text = pattern.sub(rf"\1 {spoken}", text)

    no_word = {"ms": "nombor", "id": "nomor"}.get(language, "number")
    text = re.sub(r"\bNo\.\s", f"{no_word} ", text, flags=re.IGNORECASE)

    return text


# Placeholder protection pattern (<<<TYPE_ID>>>)
_PLACEHOLDER_RE = re.compile(r"<<<[A-Z_]+_\d+>>>")


def _stash_placeholders(text: str) -> tuple[str, list[str]]:
    """Replace entity placeholders with safe single-word tokens.

    Uses purely alphabetic tokens (e.g. ``entstashaa``, ``entstashab``)
    so language normalizers that match mixed-alphanumeric or number
    patterns won't touch them.
    """
    stash: list[str] = []
    _counter_letters = "abcdefghijklmnopqrstuvwxyz"

    def _idx_to_letters(n: int) -> str:
        """Convert integer to letter string: 0→aa, 1→ab, ..., 25→az, 26→ba, etc."""
        result = []
        n_shifted = n
        while True:
            result.append(_counter_letters[n_shifted % 26])
            n_shifted = n_shifted // 26 - 1
            if n_shifted < 0:
                break
        return "".join(reversed(result))

    def _save(m: re.Match) -> str:
        stash.append(m.group(0))
        return f"entstash{_idx_to_letters(len(stash) - 1)}"

    text = _PLACEHOLDER_RE.sub(_save, text)
    return text, stash


def _unstash_placeholders(text: str, stash: list[str]) -> str:
    """Restore stashed placeholders back into text."""
    _counter_letters = "abcdefghijklmnopqrstuvwxyz"

    def _idx_to_letters(n: int) -> str:
        result = []
        n_shifted = n
        while True:
            result.append(_counter_letters[n_shifted % 26])
            n_shifted = n_shifted // 26 - 1
            if n_shifted < 0:
                break
        return "".join(reversed(result))

    for i, ph in enumerate(stash):
        text = text.replace(f"entstash{_idx_to_letters(i)}", ph)
    return text


def _restore_entities(
    text: str,
    extractor: "EntityExtractor",
    speak_entities: set,
    language: str,
) -> str:
    """Restore entity placeholders.

    Entities in *speak_entities* are converted to spoken form.
    All others are restored as original text (unprocessed).
    """
    result = text
    for entity in reversed(extractor.entities):
        placeholder = f"<<<{entity.type.value.upper()}_{entity.placeholder_id}>>>"
        if placeholder not in result:
            continue
        if entity.type in speak_entities:
            spoken = extractor._convert_entity_to_spoken(entity, language)
            result = result.replace(placeholder, spoken, 1)
        else:
            # Restore original text unchanged
            result = result.replace(placeholder, entity.text, 1)
    return result


def special_replace(text: str, language: str = "en") -> str:
    """Special character and punctuation normalization.

    Entity placeholders (<<<TYPE_ID>>>) are preserved intact.
    """
    import re as _re

    # Protect entity placeholders from character replacement
    placeholders: list[str] = []
    placeholder_pattern = _re.compile(r"<<<[A-Z_]+_\d+>>>")

    def _stash(m: _re.Match) -> str:
        placeholders.append(m.group(0))
        return f"__PH_{len(placeholders) - 1}__"

    text = placeholder_pattern.sub(_stash, text)

    text = _spell_special_chars(text, language)

    # Restore placeholders
    for i, ph in enumerate(placeholders):
        text = text.replace(f"__PH_{i}__", ph)

    return text


# ===================================================================
# THE ONE PIPELINE (core)
# ===================================================================


@dataclass(frozen=True)
class NormalizationResult:
    """Detailed normalization outcome — what changed and why.

    ``normalize_text_detailed`` returns this; ``normalize_text`` returns
    only ``text``.
    """

    text: str
    original: str
    language: str
    mappings: list[dict] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)


def _normalize_core(
    text: str,
    language: str,
    profile: Optional[str],
    disable: Optional[list[str]],
    config: Optional[Config] = None,
) -> NormalizationResult:
    """Shared pipeline. Returns the full result; public wrappers slice it."""
    # Canonicalize before validating so "ID", " en ", "Zh_MY" just work
    language = language.strip().lower()
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language: {language!r} (expected one of {SUPPORTED_LANGUAGES})"
        )

    # --- Build config ------------------------------------------------
    cfg = _build_config(profile, disable, config)

    text = text.strip()
    if not text:
        return NormalizationResult(
            text="", original="", language=language, mappings=[], rules=[]
        )

    original_text = text
    _rules: list[str] = []
    _mappings: list[dict] = []

    def _track(step: str, before: str, after: str) -> None:
        if after != before:
            _rules.append(step)

    # --- Step 1: Currency suffix expansion (always runs) -----
    before = text
    pack = get_pack(language)
    # Written number conventions (1.000.000, 10,5, Rp5M) are rewritten to
    # plain digits + magnitude words first, per language.
    if pack.preparse_number_formats is not None:
        text = pack.preparse_number_formats(text)
    text = CURRENCY_T_SUFFIX_PATTERN.sub(expand_currency_t_suffix, text)
    text = CURRENCY_TRILIUN_PATTERN.sub(expand_currency_t_suffix, text)
    text = CURRENCY_B_SUFFIX_PATTERN.sub(expand_currency_b_suffix, text)
    text = CURRENCY_MILIAR_PATTERN.sub(expand_currency_b_suffix, text)
    if pack.use_en_currency_m_suffix:
        text = CURRENCY_M_SUFFIX_PATTERN.sub(expand_currency_m_suffix, text)
    text = CURRENCY_JUTA_PATTERN.sub(expand_currency_m_suffix, text)
    text = CURRENCY_K_SUFFIX_PATTERN.sub(expand_currency_k_suffix, text)
    text = CURRENCY_RIBU_PATTERN.sub(expand_currency_k_suffix, text)
    _track("currency_suffix", before, text)

    # --- Step 1b: USSD code expansion (before number normalization) ---
    before = text
    text = _expand_ussd_codes(text, language)
    _track("ussd_codes", before, text)

    # --- Step 1c: Negative signs ---
    # A '-' directly before digits is a negative sign, not a dash — speak it
    # now, before number normalization consumes the digits. Digit-joined
    # dashes (03-8888, 3-10) are excluded by the lookbehind.
    before = text
    text = re.sub(r"(?<![\w\-])-(?=\d)", f" {pack.negative_word} ", text)
    _track("negative_sign", before, text)

    # --- Step 1c: Digit-by-digit context (exit, gate, lot, etc.) ---
    before = text
    text = _expand_digit_by_digit_context(text, language)
    _track("digit_by_digit_context", before, text)

    # --- Step 2: Entity extraction handles all entity patterns -----------
    # any URL/email regex processing, preventing pattern conflicts.

    # --- Step 3: Entity extraction → placeholders --------------------
    from revo_norm.entity_extractor import EntityExtractor, EntityType

    # Entities that are always extracted (core infrastructure + protection)
    always_extract = [
        EntityType.EMAIL,
        EntityType.URL,
        EntityType.PHONE,
        EntityType.VERSION,
        EntityType.CURRENCY,
        # DATE and TIME always extracted to protect from language normalizer
        # (EN normalizer has its own date/time regexes)
        EntityType.DATE,
        EntityType.TIME,
    ]
    # Feature-gated entities — only extracted when enabled
    if cfg.temperature:
        always_extract.append(EntityType.TEMPERATURE)
    if cfg.fractions:
        always_extract.append(EntityType.ADDRESS_SLASH)
        always_extract.append(EntityType.FRACTION)
    if cfg.x_kali:
        always_extract.append(EntityType.X_KALI)
    if cfg.ic:
        always_extract.append(EntityType.IC)
    if cfg.hari_bulan:
        always_extract.append(EntityType.HARI_BULAN)
    if cfg.hijri:
        always_extract.append(EntityType.HIJRI)

    # DATE/TIME are always extracted but only spoken when enabled
    speak_entities: set[object] = {
        EntityType.EMAIL,
        EntityType.URL,
        EntityType.PHONE,
        EntityType.VERSION,
        EntityType.CURRENCY,
    }
    if cfg.temperature:
        speak_entities.add(EntityType.TEMPERATURE)
    if cfg.fractions:
        speak_entities.add(EntityType.ADDRESS_SLASH)
        speak_entities.add(EntityType.FRACTION)
    if cfg.x_kali:
        speak_entities.add(EntityType.X_KALI)
    if cfg.ic:
        speak_entities.add(EntityType.IC)
    if cfg.hari_bulan:
        speak_entities.add(EntityType.HARI_BULAN)
    if cfg.hijri:
        speak_entities.add(EntityType.HIJRI)
    if cfg.dates:
        speak_entities.add(EntityType.DATE)
    if cfg.times:
        speak_entities.add(EntityType.TIME)

    extractor = EntityExtractor()
    protected_text, _entities = extractor.extract(text, always_extract)

    for entity in extractor.entities:
        if entity.type in speak_entities:
            spoken = extractor._convert_entity_to_spoken(entity, language)
            if spoken != entity.text:
                rule_name = entity.type.value
                _mappings.append(
                    {
                        "original": entity.text,
                        "normalized": spoken,
                        "rule": rule_name,
                    }
                )
                if rule_name not in _rules:
                    _rules.append(rule_name)

    # --- Step 4: Pronunciation mappings (always, on protected text) --
    if cfg.pronunciation_overrides:
        before = protected_text
        pronunciation_table = resolve_pronunciations(
            language,
            profile=cfg.pronunciation_profile,
            user_mappings=cfg.pronunciations or None,
        )
        protected_text = apply_pronunciation_mappings(protected_text, language, pronunciation_table)
        _track("pronunciation_mappings", before, protected_text)
        for term, spoken in pronunciation_table.items():
            pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
            if pattern.search(before):
                _mappings.append(
                    {"original": term, "normalized": spoken, "rule": "pronunciation"}
                )

    # --- Step 5: Stash placeholders to protect from downstream processing --
    protected_text, ph_stash = _stash_placeholders(protected_text)

    # --- Step 6: Feature-gated processing on non-entity text ---------
    # Pronunciation overrides
    if cfg.pronunciation_overrides:
        before = protected_text
        protected_text = apply_pronunciation_overrides(protected_text, language)
        _track("pronunciation_overrides", before, protected_text)

    # Elongated words
    if cfg.elongated:
        before = protected_text
        protected_text = normalize_elongated_text(protected_text)
        _track("elongated_words", before, protected_text)

    # Measurements — MUST run before language normalizer and acronym expansion
    # to prevent "5km" → "five K M" (acronym split) instead of "five kilometers"
    if cfg.measurements:
        before = protected_text
        protected_text = normalize_measurements(protected_text, language)
        _track("measurements", before, protected_text)

    # X-kali — run before language normalizer for the same reason
    if cfg.x_kali:
        before = protected_text
        protected_text = normalize_x_kali_text(protected_text, language)
        _track("x_kali", before, protected_text)

    # Language-specific normalizer (always runs for contractions, numbers, etc.)
    before = protected_text
    assert pack.normalize is not None  # registered packs always carry one
    protected_text = pack.normalize(protected_text)
    _track(f"language_normalizer_{language}", before, protected_text)

    # Spacing normalization
    if cfg.spacing:
        before = protected_text
        protected_text = _normalize_whitespace(protected_text)
        _track("spacing", before, protected_text)

    # Sound word removal
    if cfg.sound_words:
        sound_word_tuples = parse_sound_word_field("\n".join(cfg.sound_words))
        if sound_word_tuples:
            before = protected_text
            protected_text = smart_remove_sound_words(protected_text, sound_word_tuples)
            _track("sound_words", before, protected_text)

    # Strip all bracketed content like [laughter], [music], etc. (aggressive profile)
    if cfg.strip_bracketed:
        before = protected_text
        protected_text = re.sub(r"\[[^\]]*\]\s*", "", protected_text)
        _track("strip_bracketed", before, protected_text)

    # Abbreviation expansion (currently no-op)
    if cfg.abbreviations:
        before = protected_text
        protected_text = expand_abbreviations(protected_text, language)
        _track("abbreviations", before, protected_text)

    # Acronym expansion
    if cfg.acronyms:
        before = protected_text
        protected_text = replace_letter_period_sequences(protected_text, process_acronyms=True)
        _track("acronyms", before, protected_text)

    # Comma insertion for repeated words (always)
    before = protected_text
    protected_text = insert_comma_after_repeated_words(protected_text, min_repeat=3)
    _track("comma_insertion", before, protected_text)

    # Special character replacement
    if cfg.special_chars:
        before = protected_text
        protected_text = special_replace(protected_text, language)
        _track("special_chars", before, protected_text)

    # Exclamation marks read poorly on TTS (over-emphasis) — drop them
    # where the language's pack opts in.
    if pack.drops_exclamation:
        before = protected_text
        protected_text = re.sub(r" {2,}", " ", re.sub(r"!+", "", protected_text)).strip()
        _track("strip_exclamation", before, protected_text)

    # --- Step 7: Restore placeholders then entities as spoken form ---
    protected_text = _unstash_placeholders(protected_text, ph_stash)
    result = _restore_entities(protected_text, extractor, speak_entities, language)

    return NormalizationResult(
        text=result,
        original=original_text,
        language=language,
        mappings=_mappings,
        rules=_rules,
    )


def normalize_text(
    text: str,
    language: str,
    profile: Optional[str] = None,
    disable: Optional[list[str]] = None,
    config: Optional[Config] = None,
) -> str:
    """Normalize *text* for TTS in the given *language*.

    Parameters
    ----------
    text : str
        Input text to normalize.
    language : str
        Required. One of ``SUPPORTED_LANGUAGES``. Case and surrounding
        whitespace are ignored; an unrecognized code raises ``ValueError``
        listing the accepted values.
    profile : str or None
        One of ``"minimal"``, ``"basic"``, ``"standard"``, ``"aggressive"``.
        If *None* the standard profile (all features on) is used.
    disable : list[str] or None
        Feature names to turn off, e.g. ``["acronyms", "measurements"]``.
    config : Config or None
        A ready :class:`~revo_norm.config.Config`; overrides *profile*.
        Mutually independent — pass one or the other, not both.

    Returns
    -------
    str
        The normalized text. For mappings and triggered rules use
        :func:`normalize_text_detailed`.
    """
    return _normalize_core(text, language, profile, disable, config).text


def normalize_text_detailed(
    text: str,
    language: str,
    profile: Optional[str] = None,
    disable: Optional[list[str]] = None,
    config: Optional[Config] = None,
) -> NormalizationResult:
    """Like :func:`normalize_text` but returns a :class:`NormalizationResult`
    with the normalized text plus per-entity mappings and the list of
    pipeline rules that fired."""
    return _normalize_core(text, language, profile, disable, config)


# ===================================================================
# Config builder
# ===================================================================


def _build_config(
    profile: Optional[str],
    disable: Optional[list[str]],
    config: Optional[Config] = None,
) -> Config:
    """Resolve a Config from an explicit one, or profile + disable."""
    if config is not None:
        cfg = config
    else:
        cfg = Config.from_profile(profile) if profile is not None else Config()

    if disable:
        for f in disable:
            if hasattr(cfg, f):
                setattr(cfg, f, False)

    return cfg


# ===================================================================
# Malay pre-processing helper
# ===================================================================


def _preprocess_malay_patterns(text: str) -> str:
    """Pre-process Malay-specific currency, dates, times, percentages
    before URL regex runs (prevents URL pattern from mangling them)."""
    from revo_norm.normalizer_ms import (
        _currency_re,
        _date_re,
        _date_ymd_re,
        _percentage_re,
        _time_no_meridian_re,
        _time_re,
        normalize_currency,
        normalize_date,
        normalize_date_ymd,
        normalize_percentage,
        normalize_time,
        normalize_time_no_meridian,
    )

    text = _date_ymd_re.sub(normalize_date_ymd, text)
    text = _date_re.sub(normalize_date, text)
    text = _currency_re.sub(normalize_currency, text)
    text = _time_re.sub(normalize_time, text)
    text = _time_no_meridian_re.sub(normalize_time_no_meridian, text)
    text = _percentage_re.sub(normalize_percentage, text)
    return text
