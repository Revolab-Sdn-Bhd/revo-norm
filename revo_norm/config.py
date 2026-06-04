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

# ---------------------------------------------------------------------------
# Deprecated legacy aliases (kept for backward compatibility)
# ---------------------------------------------------------------------------


class _DeprecatedEnumAlias:
    """Base class that emits DeprecationWarning when instantiated or accessed."""

    _real_cls = None

    def __class_getitem__(cls, item):
        warnings.warn(
            f"{cls.__name__} is deprecated. Use Config directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        return cls._real_cls[item]


# Keep old enum names importable for any code that references them
# They map to simple strings now.

try:
    from enum import Enum
except ImportError:
    Enum = None  # type: ignore[assignment,misc]


if Enum is not None:

    class FeatureGroup(str, Enum):
        """DEPRECATED. Feature group names — kept for backward compat."""

        NUMBERS = "numbers"
        ENTITIES = "entities"
        SPACING = "spacing"
        MEASUREMENTS = "measurements"
        MALAY_LOCAL = "malay_local"
        ABBREVIATIONS = "abbreviations"
        ACRONYMS = "acronyms"
        ELONGATED = "elongated"
        DATES = "dates"
        TIMES = "times"

    class FeatureLevel(str, Enum):
        """DEPRECATED. Kept for backward compat."""

        OFF = "off"
        BASIC = "basic"
        STANDARD = "standard"
        AGGRESSIVE = "aggressive"

    class Profile(str, Enum):
        """DEPRECATED. Use profile name strings instead."""

        MINIMAL = "minimal"
        BASIC = "basic"
        STANDARD = "standard"
        AGGRESSIVE = "aggressive"

else:
    FeatureGroup = None  # type: ignore[assignment,misc]
    FeatureLevel = None  # type: ignore[assignment,misc]
    Profile = None  # type: ignore[assignment,misc]


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

    # ------------------------------------------------------------------
    # Deprecated builder methods (backward compat)
    # ------------------------------------------------------------------

    def with_feature(self, group: "FeatureGroup", level: "FeatureLevel") -> "Config":
        """DEPRECATED. Set a feature toggle. Use ``cfg.<field> = True/False`` instead."""
        warnings.warn(
            "with_feature() is deprecated. Set attributes directly: cfg.acronyms = False",
            DeprecationWarning,
            stacklevel=2,
        )
        name = group.value if isinstance(group, FeatureGroup) else str(group)
        off = isinstance(level, FeatureLevel) and level == FeatureLevel.OFF
        if hasattr(self, name):
            setattr(self, name, not off)
        return self

    def with_sound_words(self, words: list[str]) -> "Config":
        """DEPRECATED. Set ``cfg.sound_words`` directly instead."""
        warnings.warn(
            "with_sound_words() is deprecated. Set cfg.sound_words directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.sound_words = words
        return self


# ---------------------------------------------------------------------------
# Backward-compatible alias
# ---------------------------------------------------------------------------

NormalizationConfig = Config


# ---------------------------------------------------------------------------
# Deprecated factory functions
# ---------------------------------------------------------------------------


def minimal_config(**kwargs) -> Config:  # type: ignore[type-arg]
    """DEPRECATED. Use Config.from_profile('minimal') instead."""
    warnings.warn(
        "minimal_config() is deprecated. Use Config.from_profile('minimal').",
        DeprecationWarning,
        stacklevel=2,
    )
    cfg = Config.from_profile("minimal")
    for k, v in kwargs.items():
        if hasattr(cfg, k):
            setattr(cfg, k, v)
    return cfg


def basic_config(**kwargs) -> Config:  # type: ignore[type-arg]
    """DEPRECATED. Use Config.from_profile('basic') instead."""
    warnings.warn(
        "basic_config() is deprecated. Use Config.from_profile('basic').",
        DeprecationWarning,
        stacklevel=2,
    )
    cfg = Config.from_profile("basic")
    for k, v in kwargs.items():
        if hasattr(cfg, k):
            setattr(cfg, k, v)
    return cfg


def standard_config(**kwargs) -> Config:  # type: ignore[type-arg]
    """DEPRECATED. Use Config() or Config.from_profile('standard') instead."""
    warnings.warn(
        "standard_config() is deprecated. Use Config() or Config.from_profile('standard').",
        DeprecationWarning,
        stacklevel=2,
    )
    cfg = Config()
    for k, v in kwargs.items():
        if hasattr(cfg, k):
            setattr(cfg, k, v)
    return cfg


def aggressive_config(**kwargs) -> Config:  # type: ignore[type-arg]
    """DEPRECATED. Use Config.from_profile('aggressive') instead."""
    warnings.warn(
        "aggressive_config() is deprecated. Use Config.from_profile('aggressive').",
        DeprecationWarning,
        stacklevel=2,
    )
    cfg = Config.from_profile("aggressive")
    for k, v in kwargs.items():
        if hasattr(cfg, k):
            setattr(cfg, k, v)
    return cfg
