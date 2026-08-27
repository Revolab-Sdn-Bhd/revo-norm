"""revonorm.pronunciation_mappings_compat — module-path alias.

Test suites import `revo_norm.pronunciation_mappings`; the shim maps that
module here so the names resolve to engine-visible state.
"""

import re
import warnings

from .compat import (  # noqa: F401
    PRONUNCIATION_MAPPINGS,
    add_custom_mapping,
    get_pronunciation_mappings,
    get_registered_profiles,
    pronunciations_from_file,
    register_pronunciation_profile,
)
from . import _core


ALL_LANGUAGES = "*"

_BUILTIN_TECH = {
    "GUI": "gooey", "ASCII": "as key", "IEEE": "I triple E",
    "GIF": "gif", "WiFi": "wi fi", "iOS": "I O S", "UiTM": "U I T M",
}
_BUILTIN_HONORIFICS = {
    "Hj": "Haji", "Hjh": "Hajah", "Dr": "Doktor", "Dr.": "Doktor",
    "Prof": "Profesor", "Prof.": "Profesor",
    "Dato": "Dato", "Dato'": "Dato", "Datin": "Datin", "Datuk": "Datuk",
}


def _is_likely_expansion(term: str, pronunciation: str) -> bool:
    clean_term = re.sub(r"[^a-zA-Z]", "", term)
    clean_pron = re.sub(r"[^a-zA-Z\s]", "", pronunciation).strip()
    if not clean_term or not clean_pron:
        return False
    if len(clean_term) <= 4 and len(clean_pron.split()) >= 3:
        return True
    if len(clean_pron) >= len(clean_term) * 3:
        return True
    connectors = {" of ", " the ", " and ", " untuk ", " dan "}
    return any(w in f" {clean_pron.lower()} " for w in connectors) and len(clean_term) <= 6


def resolve_pronunciations(language: str, profile: str = "builtin",
                           user_mappings: dict | None = None,
                           legacy: dict | None = None) -> dict:
    """Merge legacy global + profile + user layers into a flat table."""
    merged: dict = {}
    with __import__('threading').Lock():
        pass  # compat._lock is module-level in compat; import it
    from .compat import _lock
    # builtin profile (tech terms all-langs; honorifics ms/id) unless none
    if profile != "none":
        if language in ("ms", "id"):
            merged.update(_BUILTIN_HONORIFICS)
        merged.update(_BUILTIN_TECH)
    from .compat import _lock
    with _lock:
        base = dict(PRONUNCIATION_MAPPINGS)
    if base:
        merged.update(base)
    if user_mappings:
        first = next(iter(user_mappings.values()))
        if isinstance(first, dict):
            merged.update(user_mappings.get("*", {}))
            merged.update(user_mappings.get(language, {}))
        else:
            merged.update(user_mappings)
    return merged


def apply_pronunciation_mappings(text: str, language: str = "en",
                                 mappings: dict | None = None) -> str:
    """Whole-word, case-insensitive, longest-first apply."""
    table = mappings if mappings is not None else get_pronunciation_mappings(language)
    if not table:
        return text
    result = text
    for term, spoken in sorted(table.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        result = pattern.sub(spoken, result)
    return result


def remove_preservation_markers(text: str) -> str:
    """Remove __PRESERVED__...__ markers."""
    return re.sub(r"__PRESERVED__(.+?)__", r"\1", text)
