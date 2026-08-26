"""
Pronunciation mappings for TTS (Text-to-Speech) applications.

⚠️  TTS-ONLY: This module maps terms to their **spoken pronunciation**, NOT their
    expanded meaning. For example:
    - ✅ "GUI" → "gooey" (how you SAY it)
    - ✅ "IEEE" → "I triple E" (how you SAY it)
    - ❌ "AMN" → "Ahli Mangku Negara" (what it MEANS, not pronunciation)

Mappings resolve in layers; later layers win:
    1. ``PRONUNCIATION_MAPPINGS`` — legacy process-global table written by
       ``add_custom_mapping()``. Prefer request-scoped config in a server.
    2. The active profile — ``"builtin"`` (default, ships with the library),
       ``"none"``, or one registered with ``register_pronunciation_profile()``.
    3. ``Config.pronunciations`` — per-call, last say.

Every layer may be language-scoped: ``{"*": {...}, "ms": {...}}`` — a flat
dict means all languages. A ``None`` value removes the term from all lower
layers ("my TTS model handles this, leave it alone").

Applied HIGHEST priority, before any other transformation (acronym
expansion, abbreviation expansion, ...).
"""

from __future__ import annotations

import json
import logging
import re
import warnings

logger = logging.getLogger(__name__)

# Scope key that applies to every language.
ALL_LANGUAGES = "*"

# --- Layer 1: legacy global table ------------------------------------------
# Process-wide mutable state kept for backward compatibility. Snapshot/restore
# this in tests; in a server prefer Config.pronunciations.
PRONUNCIATION_MAPPINGS: dict[str, str] = {}

# --- Layer 2: profiles ------------------------------------------------------
# Curated, named mapping sets. "builtin" ships with the library and stays the
# default so existing consumers keep identical output; "none" is empty.
# register_pronunciation_profile() adds company/TTS-model tables at startup.
BUILTIN_PROFILE: dict[str, dict[str, str | None]] = {
    ALL_LANGUAGES: {
        # Technology terms with special pronunciations (not following
        # generalized rules). Tech terms sound the same across languages in
        # the Malaysian context.
        "GUI": "gooey",
        "ASCII": "as key",
        "IEEE": "I triple E",
        "GIF": "gif",
        "WiFi": "wi fi",
        "iOS": "I O S",
        "UiTM": "U I T M",
    },
    # Malay honorifics — pronounced in full in Malay/Indonesian text only.
    # Title entries ("Dato" -> "Dato") are identity mappings: they protect
    # titles from downstream letter-splitting, so the title survives intact.
    "ms": {
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
    },
    "id": {
        "Hj": "Haji",
        "Hjh": "Hajah",
        "Dr": "Doktor",
        "Dr.": "Doktor",
        "Prof": "Profesor",
        "Prof.": "Profesor",
    },
}

_PROFILES: dict[str, dict[str, dict[str, str | None]]] = {
    "builtin": BUILTIN_PROFILE,
    "none": {},
}


def _normalize_scopes(mappings: dict) -> dict[str, dict[str, str | None]]:
    """Accept a flat dict (all languages) or a scoped one; validate shape."""
    if not mappings:
        return {}
    first = next(iter(mappings.values()))
    if isinstance(first, str) or first is None:
        # Flat: term -> pronunciation, applies to every language
        return {ALL_LANGUAGES: dict(mappings)}
    for scope, table in mappings.items():
        if not isinstance(scope, str):
            raise TypeError(f"Scope keys must be language codes or '*', got {scope!r}")
        if not isinstance(table, dict):
            raise TypeError(f"Scope {scope!r} must map to a dict, got {type(table).__name__}")
    return {scope: dict(table) for scope, table in mappings.items()}


def register_pronunciation_profile(name: str, mappings: dict) -> None:
    """Register a named pronunciation profile.

    A profile is language-scoped: ``{"*": {...}, "ms": {...}}``. A flat dict
    is treated as all-languages. Re-registering a name replaces it.

    Use this for company or TTS-model-specific tables at process startup,
    then select per call via ``Config(pronunciation_profile=name)``.
    """
    _PROFILES[name] = _normalize_scopes(mappings)


def get_registered_profiles() -> tuple[str, ...]:
    """All registered profile names."""
    return tuple(_PROFILES)


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


def _warn_if_expansion(source: str, term: str, pronunciation: str) -> None:
    """Warn (not block) when a user-provided mapping looks like an expansion."""
    if _is_likely_expansion(term, pronunciation):
        warnings.warn(
            f'{source}: mapping "{term}" → "{pronunciation}" looks like an '
            f"abbreviation expansion, not a pronunciation guide. This normalizer "
            f"is for TTS — map how terms SOUND, not what they mean.",
            UserWarning,
            stacklevel=3,
        )


def resolve_pronunciations(
    language: str,
    profile: str = "builtin",
    user_mappings: dict | None = None,
    legacy: dict[str, str] | None = None,
) -> dict[str, str]:
    """Merge all layers into one flat term → pronunciation table for *language*.

    Later layers win; a ``None`` value removes the term from lower layers.
    """
    merged: dict[str, str] = {}

    def _apply(scopes: dict[str, dict[str, str | None]]) -> None:
        for term, spoken in scopes.get(ALL_LANGUAGES, {}).items():
            if spoken is None:
                merged.pop(term, None)
            else:
                merged[term] = spoken
        for term, spoken in scopes.get(language, {}).items():
            if spoken is None:
                merged.pop(term, None)
            else:
                merged[term] = spoken

    # Layer 1: legacy global (flat, all languages) — always merged so
    # add_custom_mapping() entries stay effective alongside the profile.
    if legacy is None:
        legacy = PRONUNCIATION_MAPPINGS
    if legacy:
        _apply(_normalize_scopes(legacy))
    # Layer 2: named profile
    if profile != "none":
        _apply(_PROFILES.get(profile, {}))
    # Layer 3: user config — last say
    if user_mappings:
        user_scopes = _normalize_scopes(user_mappings)
        for term, spoken in user_scopes.get(ALL_LANGUAGES, {}).items():
            if spoken is None:
                merged.pop(term, None)
            else:
                _warn_if_expansion("Config.pronunciations", term, spoken)
                merged[term] = spoken
        for term, spoken in user_scopes.get(language, {}).items():
            if spoken is None:
                merged.pop(term, None)
            else:
                _warn_if_expansion("Config.pronunciations", term, spoken)
                merged[term] = spoken

    return merged


def get_pronunciation_mappings(language: str = "en") -> dict[str, str]:
    """Effective mappings for *language*: legacy global + builtin profile."""
    return resolve_pronunciations(language, profile="builtin")


def apply_pronunciation_mappings(
    text: str, language: str = "en", mappings: dict[str, str] | None = None
) -> str:
    """Apply pronunciation mappings to text.

    Whole-word matches only, case-insensitive, longest term first. Runs first
    in the normalization pipeline, before any other transformation.

    Args:
        text: Input text
        language: Language code
        mappings: Pre-resolved flat table; when *None*, the builtin profile
            for *language* is used (pipeline callers pass the resolved table).

    Example:
        >>> apply_pronunciation_mappings("Build GUI interface", "en")
        'Build gooey interface'
    """
    table = mappings if mappings is not None else get_pronunciation_mappings(language)
    if not table:
        return text

    sorted_mappings = sorted(table.items(), key=lambda x: len(x[0]), reverse=True)

    result = text
    for term, pronunciation in sorted_mappings:
        pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        result = pattern.sub(pronunciation, result)

    return result


def add_custom_mapping(term: str, pronunciation: str, language: str = "en") -> None:
    """Add a custom pronunciation mapping to the process-global legacy table.

    ⚠️  Process-wide mutable state. Prefer ``Config.pronunciations`` —
    request-scoped, layerable, warn-only validation. This legacy path keeps
    its hard ``ValueError`` on expansion-looking mappings.

    Args:
        term: The term to map (e.g., "SQL")
        pronunciation: The spoken form (e.g., "sequel")
        language: Ignored — the legacy table applies to all languages

    Raises:
        ValueError: If the mapping looks like an abbreviation expansion
                    rather than a pronunciation guide.
    """
    if _is_likely_expansion(term, pronunciation):
        raise ValueError(
            f'Mapping "{term}" → "{pronunciation}" looks like an abbreviation '
            f"expansion, not a pronunciation guide. This normalizer is for TTS — "
            f"map how terms SOUND, not what they mean. If you're sure this is "
            f"pronunciation, set it request-scoped instead: "
            f"Config.pronunciations = {{'{term}': '{pronunciation}'}}"
        )

    PRONUNCIATION_MAPPINGS[term] = pronunciation
    logger.info("Added pronunciation mapping: %s → %s", term, pronunciation)


def pronunciations_from_file(path: str) -> dict:
    """Load language-scoped mappings from a JSON file.

    The file holds one object; a flat object means all languages, keyed
    scopes (``{"*": {...}, "ms": {...}}``) pass through::

        {"*": {"WiFi": "wai fai"}, "ms": {"Dato": "Dato"}}

    Returns the dict for ``Config.pronunciations = pronunciations_from_file(path)``.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object, got {type(data).__name__}")
    return data


def remove_preservation_markers(text: str) -> str:
    """Remove preservation markers added by pronunciation mappings."""
    return re.sub(r"__PRESERVED__(.+?)__", r"\1", text)
