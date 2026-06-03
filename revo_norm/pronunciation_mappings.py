"""
Pronunciation mappings for TTS (Text-to-Speech) applications.

⚠️  TTS-ONLY: This module maps terms to their **spoken pronunciation**, NOT their
    expanded meaning. For example:
    - ✅ "GUI" → "gooey" (how you SAY it)
    - ✅ "IEEE" → "I triple E" (how you SAY it)
    - ✅ "Hj" → "Haji" (how you PRONOUNCE the abbreviation)
    - ❌ "AMN" → "Ahli Mangku Negara" (what it MEANS, not pronunciation)

    Adding abbreviation expansions here will produce incorrect TTS output.
    Use `add_custom_mapping()` to add new entries — it validates against
    expansions that look like abbreviation lookups rather than pronunciation.

These mappings have the HIGHEST PRIORITY in the normalization pipeline and are
applied BEFORE any other transformations (acronym expansion, abbreviation
expansion, etc.).
"""

import logging
import re

logger = logging.getLogger(__name__)

# Single pronunciation mapping for all languages (English and Malay)
# Tech terms are pronounced the same way in both languages for Malaysian context
#
# GUIDELINES for adding entries:
# 1. The mapping must represent how a term SOUNDS when spoken aloud
# 2. The replacement should be similar length to the spoken form
# 3. Multi-word expansions (like "Ahli Mangku Negara") are abbreviation
#    expansions, NOT pronunciation — they do NOT belong here
PRONUNCIATION_MAPPINGS: dict[str, str] = {
    # Text corrections / OCR error fixes
    "bias": "bai yers",
    # Malay honorifics - how they are pronounced in full
    "Hj": "Haji",
    "Hjh": "Hajah",
    "Dr": "Doktor",
    "Dr.": "Doktor",
    "Prof": "Profesor",
    "Prof.": "Profesor",
    "Dato": "Dato",
    "Dato'": "Dato",
    "Datin": "Datin",
    "Datuk": "Datuk",
    # Technology terms with special pronunciations (not following generalized rule)
    "GUI": "gooey",
    "ASCII": "as key",
    "IEEE": "I triple E",
    "GIF": "gif",
    "WiFi": "wi fi",
    "iOS": "I O S",
    "UiTM": "U I T M",
}


def _is_likely_expansion(term: str, pronunciation: str) -> bool:
    """Check if a mapping looks like abbreviation expansion rather than pronunciation.

    Heuristics:
    - Replacement is 3x+ longer than the original (character count)
    - Replacement contains 3+ words and the original is a short abbreviation (≤4 chars)
    - Replacement contains words like "of", "the", "and" suggesting a full name/title
    """
    # Ignore punctuation in length comparison
    clean_term = re.sub(r"[^a-zA-Z]", "", term)
    clean_pron = re.sub(r"[^a-zA-Z\s]", "", pronunciation).strip()

    if not clean_term or not clean_pron:
        return False

    # Short abbreviation (≤4 chars) expanded to 3+ words → likely expansion
    if len(clean_term) <= 4:
        word_count = len(clean_pron.split())
        if word_count >= 3:
            return True

    # Replacement is 3x+ longer than original → likely expansion
    if len(clean_pron) >= len(clean_term) * 3:
        return True

    # Contains connector words typical of full names/titles
    connector_words = {" of ", " the ", " and ", " untuk ", " dan "}
    return any(w in f" {clean_pron.lower()} " for w in connector_words) and len(clean_term) <= 6


def get_pronunciation_mappings(language: str = "en") -> dict[str, str]:
    """Get pronunciation mappings for a language.

    Args:
        language: Language code ('en' for English, 'ms' for Malay)
                  Note: Same mappings used for both languages

    Returns:
        Dictionary mapping terms to their spoken forms
    """
    return PRONUNCIATION_MAPPINGS.copy()


def apply_pronunciation_mappings(text: str, language: str = "en") -> str:
    """Apply pronunciation mappings to text.

    This should be called FIRST in the normalization pipeline, before any
    other transformations. Mappings are applied as whole-word matches only.

    Args:
        text: Input text
        language: Language code ('en' for English, 'ms' for Malay)

    Returns:
        Text with pronunciation mappings applied

    Example:
        >>> apply_pronunciation_mappings("Build GUI interface", "en")
        'Build gooey interface'
    """
    mappings = get_pronunciation_mappings(language)
    if not mappings:
        return text

    sorted_mappings = sorted(mappings.items(), key=lambda x: len(x[0]), reverse=True)

    result = text
    for term, pronunciation in sorted_mappings:
        pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        result = pattern.sub(pronunciation, result)

    return result


def add_custom_mapping(term: str, pronunciation: str, language: str = "en") -> None:
    """Add a custom pronunciation mapping.

    ⚠️  Only add PRONUNCIATION mappings here — how a term SOUNDS when spoken.
    Do NOT add abbreviation expansions (what a term MEANS).

    Args:
        term: The term to map (e.g., "JSON")
        pronunciation: The spoken form (e.g., "jay son")
        language: Language code ('en' or 'ms') - ignored, applies to both

    Raises:
        ValueError: If the mapping looks like an abbreviation expansion
                    rather than a pronunciation guide.

    Examples:
        >>> add_custom_mapping("YOLO", "you only live once")  # ← WRONG, this is expansion
        ValueError: Mapping "YOLO" → "you only live once" looks like an abbreviation
        expansion, not a pronunciation guide. This normalizer is for TTS — map how
        terms SOUND, not what they mean.

        >>> add_custom_mapping("SQL", "sequel")  # ✅ Correct, this is pronunciation
    """
    if _is_likely_expansion(term, pronunciation):
        raise ValueError(
            f'Mapping "{term}" → "{pronunciation}" looks like an abbreviation '
            f"expansion, not a pronunciation guide. This normalizer is for TTS — "
            f"map how terms SOUND, not what they mean. If you're sure this is "
            f"pronunciation, set the mapping directly: "
            f"PRONUNCIATION_MAPPINGS['{term}'] = '{pronunciation}'"
        )

    PRONUNCIATION_MAPPINGS[term] = pronunciation
    logger.info("Added pronunciation mapping: %s → %s", term, pronunciation)


def remove_preservation_markers(text: str) -> str:
    """Remove preservation markers added by pronunciation mappings."""
    return re.sub(r"__PRESERVED__(.+?)__", r"\1", text)
