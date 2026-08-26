"""
Normalization configuration for revo-norm.

Simple feature-toggle configuration with profile presets.

Example:
    >>> from revo_norm import normalize_text, Config
    >>> result = normalize_text("The API uses 5GB", language="en")
    >>> result = normalize_text("test", language="en", profile="minimal")
    >>> result = normalize_text("test", language="en", disable=["acronyms", "measurements"])
"""

import warnings
from dataclasses import dataclass, field
from enum import Enum

# Single source of truth for language codes accepted by the pipeline.
# Every language-dispatch point validates against this and fails fast.
SUPPORTED_LANGUAGES = ("en", "ms", "id", "zh", "zh_my")


class Profile(str, Enum):
    """Normalization profiles: how much of the pipeline runs."""

    MINIMAL = "minimal"
    BASIC = "basic"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"


class Feature(str, Enum):
    """Toggleable pipeline features — the names Config and disable= accept."""

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


# Keep old enum names importable for any code that references them
# They map to simple strings now.

try:
    from enum import Enum
except ImportError:
    Enum = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Profile definitions
# ---------------------------------------------------------------------------

_MINIMAL_FIELDS: dict[str, bool] = {
    "spacing": True,
    # everything else False
}

_BASIC_FIELDS: dict[str, bool] = {
    "spacing": True,
    "acronyms": True,
    "abbreviations": True,
    "elongated": True,
    "malay_local": True,
    "special_chars": True,
}

# STANDARD / AGGRESSIVE = everything True (aggressive adds sound_words behaviour
# which is handled separately via sound_words list).

# Default sound words removed by the aggressive profile.
# Format matches parse_sound_word_field: "pattern => replacement" or "pattern" (remove).
# Aggressive profile strips all [...] content via strip_bracketed flag.

# ---------------------------------------------------------------------------
# Config dataclass
# ---------------------------------------------------------------------------


@dataclass
class Config:
    """Simple feature-toggle configuration for text normalization.

    All features default to True (standard profile).

    Create from a profile name:
        >>> cfg = Config.from_profile("minimal")
        >>> cfg = Config.from_profile("basic")

    Disable specific features:
        >>> cfg = Config.with_disabled(["acronyms", "measurements"])

    Check a feature:
        >>> cfg.is_enabled("acronyms")
        False
    """

    # Feature toggles — all default True (standard)
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

    # Sound words for removal (aggressive profile may populate this)
    sound_words: list[str] = field(default_factory=list)

    # Strip all bracketed content like [laughter], [music], etc.
    strip_bracketed: bool = False

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_profile(cls, name: str) -> "Config":
        """Create a Config from a profile name.

        Profiles:
            minimal   — spacing only
            basic     — spacing, acronyms, abbreviations, elongated, malay_local, special_chars
            standard  — everything enabled (default)
            aggressive — everything enabled
        """
        name = name.lower()
        if name == "standard":
            return cls()
        if name == "aggressive":
            return cls(
                strip_bracketed=True,
            )
        if name == "minimal":
            return cls(
                **{k: False for k in cls._feature_fields() if k not in _MINIMAL_FIELDS},
                **_MINIMAL_FIELDS,
            )
        if name == "basic":
            return cls(
                **{k: False for k in cls._feature_fields() if k not in _BASIC_FIELDS},
                **_BASIC_FIELDS,
            )
        raise ValueError(f"Unknown profile: {name!r}")

    @classmethod
    def with_disabled(cls, features: list[str]) -> "Config":
        """Create a standard Config with specific features disabled."""
        cfg = cls()
        for f in features:
            if hasattr(cfg, f):
                setattr(cfg, f, False)
            else:
                warnings.warn(f"Unknown feature {f!r} in disable list — ignored.", stacklevel=2)
        return cfg

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @classmethod
    def _feature_fields(cls) -> list[str]:
        """Return names of all boolean feature fields."""
        return [
            f.name
            for f in cls.__dataclass_fields__.values()  # type: ignore[attr-defined]
            if f.type is bool or f.type == "bool"
        ]

    def is_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled.

        Returns True for unknown feature names (safe default).
        """
        return getattr(self, feature, True)

    def should_run_shared_features(self, language: str) -> bool:
        """Return True if Malay-local features should run for the given language."""
        return self.malay_local and language == "ms"


