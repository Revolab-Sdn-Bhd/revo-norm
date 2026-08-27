"""revonorm.compat — the original revo_norm API shapes over the engine.

Config/Profile/Feature mirror python's config.py; pronunciation globals
(PRONUNCIATION_MAPPINGS, add_custom_mapping) write engine-visible state;
EntityExtractor/EntityType expose the extraction API; normalize_text /
normalize_text_detailed wrap the compiled pipeline with the original
signatures (language= keyword, config= passthrough).
"""

import re
import threading
from dataclasses import dataclass, field
from enum import Enum

from . import _core

# ---------------------------------------------------------------------------
# Global pronunciation state — python's process-global legacy table, kept
# for API compatibility. Feeds the engine as the lowest user layer.
# ---------------------------------------------------------------------------

PRONUNCIATION_MAPPINGS: dict[str, str] = {}
_lock = threading.Lock()

_PROFILE_REGISTRY: dict[str, dict] = {
    "builtin": None,  # engine built-in
    "none": {},
}


class Config:
    """Feature-toggle configuration, mirrors revo_norm.config.Config."""

    acronyms: bool = True
    abbreviations: bool = True
    spacing: bool = True
    measurements: bool = True
    dates: bool = True
    times: bool = True
    temperature: bool = True
    fractions: bool = True
    x_kali: bool = True
    ic: bool = True
    hari_bulan: bool = True
    hijri: bool = True
    elongated: bool = True
    malay_local: bool = True
    special_chars: bool = True
    pronunciation_overrides: bool = True
    pronunciation_profile: str = "builtin"
    pronunciations: dict = {}
    sound_words: list = []
    strip_bracketed: bool = False

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self.__class__, k) or k in (
                "pronunciation_profile", "pronunciations", "sound_words",
            ):
                setattr(self, k, v)

    @classmethod
    def from_profile(cls, name: str) -> "Config":
        c = cls()
        if name == "minimal":
            for f in (
                "abbreviations", "acronyms", "dates", "elongated", "fractions",
                "hari_bulan", "hijri", "ic", "malay_local", "measurements",
                "pronunciation_overrides", "special_chars", "temperature",
                "times", "x_kali",
            ):
                setattr(c, f, False)
        elif name == "basic":
            for f in (
                "dates", "fractions", "hari_bulan", "hijri", "ic",
                "measurements", "pronunciation_overrides", "temperature",
                "times", "x_kali",
            ):
                setattr(c, f, False)
        elif name == "aggressive":
            c.strip_bracketed = True
        # standard: everything on
        return c

    @staticmethod
    def with_disabled(features: list) -> "Config":
        c = Config()
        for f in features:
            if hasattr(c, f):
                setattr(c, f, False)
        return c

    def is_enabled(self, feature: str) -> bool:
        return bool(getattr(self, feature, True))


class Profile(str, Enum):
    MINIMAL = "minimal"
    BASIC = "basic"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"


class Feature(str, Enum):
    SPACING = "spacing"
    ABBREVIATIONS = "abbreviations"
    ACRONYMS = "acronyms"
    PRONUNCIATION_OVERRIDES = "pronunciation_overrides"
    ELONGATED = "elongated"
    FRACTIONS = "fractions"
    X_KALI = "x_kali"
    TEMPERATURE = "temperature"
    IC = "ic"
    MEASUREMENTS = "measurements"
    HARI_BULAN = "hari_bulan"
    HIJRI = "hijri"
    DATES = "dates"
    TIMES = "times"
    SPECIAL_CHARS = "special_chars"
    SOUND_WORDS = "sound_words"


SUPPORTED_LANGUAGES = tuple(_core.supported_languages())


# ---------------------------------------------------------------------------
# Pronunciation mappings — legacy global API
# ---------------------------------------------------------------------------

def add_custom_mapping(term: str, pronunciation: str, language: str = "en") -> None:
    """Add a pronunciation mapping to the process-global legacy table.

    Raises ValueError when the mapping looks like an abbreviation expansion
    (python parity).
    """
    if _is_likely_expansion(term, pronunciation):
        raise ValueError(
            f'Mapping "{term}" → "{pronunciation}" looks like an abbreviation '
            f"expansion, not a pronunciation guide. This normalizer is for TTS — "
            f"map how terms SOUND, not what they mean. If you're sure this is "
            f"pronunciation, set it request-scoped instead: "
            f"Config.pronunciations = {{'{term}': '{pronunciation}'}}"
        )
    with _lock:
        PRONUNCIATION_MAPPINGS[term] = pronunciation


def get_pronunciation_mappings(language: str = "en") -> dict:
    """Legacy view: global table + builtin profile for the language."""
    base = {}
    if language in ("ms", "id"):
        base.update(_builtin_honorifics())
    base.update(_builtin_tech())
    with _lock:
        base.update(dict(PRONUNCIATION_MAPPINGS))
    return base


def _builtin_tech() -> dict:
    return {
        "GUI": "gooey", "ASCII": "as key", "IEEE": "I triple E",
        "GIF": "gif", "WiFi": "wi fi", "iOS": "I O S", "UiTM": "U I T M",
    }


def _builtin_honorifics() -> dict:
    return {
        "Hj": "Haji", "Hjh": "Hajah", "Dr": "Doktor", "Dr.": "Doktor",
        "Prof": "Profesor", "Prof.": "Profesor",
    }


def get_registered_profiles() -> tuple:
    with _lock:
        return tuple(sorted(_PROFILE_REGISTRY.keys()))


def register_pronunciation_profile(name: str, mappings: dict) -> None:
    """Register a named profile (API compat; feeds resolve via Config)."""
    flat = mappings.get("*", mappings) if isinstance(mappings, dict) else {}
    with _lock:
        _PROFILE_REGISTRY[name] = dict(flat)


def pronunciations_from_file(path: str) -> dict:
    import json

    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object, got {type(data).__name__}")
    return data


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


# ---------------------------------------------------------------------------
# Entity extraction — thin facade over engine placeholders
# ---------------------------------------------------------------------------

class EntityType(str, Enum):
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    VERSION = "version"
    CURRENCY = "currency"
    DATE = "date"
    TIME = "time"
    TEMPERATURE = "temperature"
    FRACTION = "fraction"
    X_KALI = "x_kali"
    IC = "ic"
    HARI_BULAN = "hari_bulan"
    HIJRI = "hijri"


@dataclass
class Entity:
    type: EntityType
    text: str
    start: int = 0
    end: int = 0
    placeholder_id: int = 0


class EntityExtractor:
    """API-compat extractor: extract() returns placeholder-protected text."""

    def __init__(self):
        self.entities: list = []
        self.next_id = 1

    def extract(self, text, enabled_entities=None):
        """API-compat placeholder extraction (pure-python, python parity)."""
        import re as _re

        patterns = {
            EntityType.EMAIL: _re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", _re.IGNORECASE),
            EntityType.URL: _re.compile(
                r"(?:https?://|ftp://|www\.)[^\s]+"
                r"|\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/[^\s]*)?"
                r"|\b[A-Za-z0-9-]+\.[A-Za-z]{2,}(?:/[^\s]*)?",
                _re.IGNORECASE,
            ),
        }
        self.entities = []
        self.next_id = 1
        protected = text
        for etype in (EntityType.EMAIL, EntityType.URL):
            def _stash(m):
                ent = Entity(type=etype, text=m.group(0), start=m.start(),
                             end=m.end(), placeholder_id=self.next_id)
                self.entities.append(ent)
                ph = f"<<<{etype.value.upper()}_{self.next_id}>>>"
                self.next_id += 1
                return ph
            protected = patterns[etype].sub(_stash, protected)
        return protected, self.entities


# ---------------------------------------------------------------------------
# Language packs — registration is engine-side; expose API shapes
# ---------------------------------------------------------------------------

class LanguagePack:
    """API-compat dataclass; registering affects the python-side registry."""

    def __init__(self, code, **kwargs):
        self.code = code
        for k, v in kwargs.items():
            setattr(self, k, v)


_REGISTERED_LANGS: dict = {}


def register_language(pack) -> None:
    _REGISTERED_LANGS[pack.code] = pack





# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

@dataclass
class NormalizationResult:
    text: str
    original: str
    language: str
    mappings: list = field(default_factory=list)
    rules: list = field(default_factory=list)


def _normalize_pron_scope(mapping):
    """Flat {term: spoken} becomes {"*": {...}}; keyed scopes pass through."""
    if not isinstance(mapping, dict) or not mapping:
        return mapping
    first = next(iter(mapping.values()))
    if isinstance(first, dict):
        return mapping
    return {"*": dict(mapping)}


def _validate_pron_scope(mapping, source="Config.pronunciations"):
    """Raise TypeError on scalar-under-language-code shape; warn on
    expansion-looking entries (python parity)."""
    import warnings as _w

    if not isinstance(mapping, dict) or not mapping:
        return
    known = {"en", "ms", "id", "zh", "zh_my", "ja", "ko", "th", "tl",
             "vi", "ta", "ar", "hi", "bn", "ur", "fa"}
    keys_look_lang = all(
        k == "*" or (isinstance(k, str) and len(k) <= 5 and k.lower() in known)
        for k in mapping
    )
    scalars = [v for v in mapping.values() if isinstance(v, (str, type(None)))]
    if keys_look_lang and scalars and set(mapping) - {"*"}:
        raise TypeError(
            f"Scope keys (language codes / '*') must map to dicts; got scalar "
            f"values under {sorted(mapping)}. If these are terms, note that "
            f"terms named like language codes are not supported in flat form."
        )
    # warn on expansions in any table
    def check(table):
        for term, spoken in table.items():
            if spoken and _is_likely_expansion(term, spoken):
                _w.warn(
                    f'{source}: mapping "{term}" → "{spoken}" looks like an '
                    f"abbreviation expansion, not a pronunciation guide. This "
                    f"normalizer is for TTS — map how terms SOUND, not what "
                    f"they mean.",
                    UserWarning,
                    stacklevel=3,
                )
    first = next(iter(mapping.values()))
    if isinstance(first, dict):
        for t in mapping.values():
            check(t)
    else:
        check(mapping)


def _config_to_options(config=None, profile=None, disable=None):
    import json

    opts = {}
    if config is not None:
        profile = getattr(config, "_profile_name", None) or profile
        off = [
            f for f in (
                "abbreviations", "acronyms", "dates", "elongated", "fractions",
                "hari_bulan", "hijri", "ic", "malay_local", "measurements",
                "pronunciation_overrides", "special_chars", "temperature",
                "times", "x_kali",
            )
            if not getattr(config, f, True)
        ]
        if profile:
            opts["profile"] = profile
        if off:
            opts["disable"] = off
        prof = getattr(config, "pronunciation_profile", "builtin")
        if prof == "none":
            opts["pronunciation_profile"] = "none"
        elif prof not in ("builtin", "none"):
            with _lock:
                table = dict(_PROFILE_REGISTRY.get(prof, {}))
            # a selected profile REPLACES builtin (python: _PROFILES lookup,
            # builtin not merged) — disable builtin, layer the table on top
            opts["pronunciation_profile"] = "none"
            opts["pronunciations"] = {"*": table}
        if getattr(config, "pronunciations", None):
            _validate_pron_scope(config.pronunciations)
            opts["pronunciations"] = _normalize_pron_scope(config.pronunciations)
    else:
        if profile is not None:
            opts["profile"] = profile
        if disable:
            opts["disable"] = list(disable)
    with _lock:
        legacy = dict(PRONUNCIATION_MAPPINGS)
    if legacy:
        user = opts.get("pronunciations") or {}
        # legacy is the LOWEST layer: user entries overwrite it, never the
        # reverse (python: legacy < profile < user)
        star = dict(legacy)
        if isinstance(user, dict):
            star.update(user.get("*", {}))
            merged = dict(user)
        else:
            merged = {}
        merged["*"] = star
        opts["pronunciations"] = merged
    return json.dumps(opts) if opts else ""


def normalize_text(text: str, language: str, profile=None, disable=None,
                   config=None) -> str:
    import json as _json

    opts_json = _config_to_options(config, profile, disable)
    # sound words: strip [x] patterns pre-engine (pure-python pass; the
    # engine has no sound-words feature by design)
    words = None
    if config is not None and getattr(config, "sound_words", None):
        words = config.sound_words
    else:
        try:
            o = _json.loads(opts_json) if opts_json else {}
            words = o.get("sound_words")
        except Exception:
            words = None
    if words:
        text = _strip_sound_words(text, words)
    result = _core.normalize(text, language, opts_json)
    if result.startswith("__ERROR__"):
        raise ValueError(result[len("__ERROR__"):])
    return result


def _strip_sound_words(text: str, words) -> str:
    import re as _re

    for w in words:
        w = w.strip()
        if not w:
            continue
        text = _re.sub(_re.escape(w) + r"\s*", "", text)
    return text


def normalize_text_detailed(text: str, language: str, profile=None,
                            disable=None, config=None) -> NormalizationResult:
    import json as _json
    import re as _re

    out = normalize_text(text, language, profile, disable, config)
    mappings = []
    rules = []
    # pronunciation replacements: compare each effective table term
    if text != out:
        table = resolve_pron_effective(language, profile, disable, config)
        for term, spoken in table.items():
            if _re.search(rf"\b{_re.escape(term)}\b", text, _re.IGNORECASE):
                mappings.append(
                    {"original": term, "normalized": spoken, "rule": "pronunciation"}
                )
                if "pronunciation" not in rules:
                    rules.append("pronunciation")
    return NormalizationResult(
        text=out, original=text, language=language, mappings=mappings, rules=rules
    )


def resolve_pron_effective(language, profile=None, disable=None, config=None):
    """Flat effective table for the detailed-result diff scan."""
    import json as _json

    opts = _json.loads(_config_to_options(config, profile, disable) or "{}")
    user = opts.get("pronunciations") or {}
    flat = {}
    if isinstance(user, dict):
        flat.update(user.get("*", {}))
        flat.update(user.get(language, {}))
        flat = {k: v for k, v in flat.items() if v}
    if opts.get("pronunciation_profile", "builtin") != "none":
        from .pronunciation_mappings_compat import (
            _BUILTIN_HONORIFICS, _BUILTIN_TECH,
        )
        if language in ("ms", "id"):
            flat.update(_BUILTIN_HONORIFICS)
        flat.update(_BUILTIN_TECH)
    return {k: v for k, v in flat.items() if v}
