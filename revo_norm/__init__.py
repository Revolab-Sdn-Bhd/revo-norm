"""
Revo Norm — multilingual text normalization for TTS.

Quick start::

    from revo_norm import normalize_text

    normalize_text("Hello RM50K", language="en")
    normalize_text("Suhu 25C", language="ms")
    normalize_text("Harga Rp1.500.000", language="id")
    normalize_text("test", language="en", profile="minimal")
    normalize_text("test", language="en", disable=["acronyms"])
"""

__version__ = "0.4.2"

# Main entry point
# Simple configuration
# ---------------------------------------------------------------------------
# Deprecated backward-compat re-exports
# ---------------------------------------------------------------------------
from revo_norm.config import (
    SUPPORTED_LANGUAGES,
    Config,
    FeatureGroup,
    FeatureLevel,
    NormalizationConfig,
    Profile,
    aggressive_config,
    basic_config,
    minimal_config,
    standard_config,
)

# Entity extraction (advanced users)
from revo_norm.entity_extractor import Entity, EntityExtractor, EntityType

# Custom pronunciation mappings
# Pronunciation mapping helper (kept for advanced users)
from revo_norm.pronunciation_mappings import add_custom_mapping, get_pronunciation_mappings
from revo_norm.text_normalizer import normalize_text

# TTS utilities
from revo_norm.tts_utils import (
    add_random_commas,
    parse_sound_word_field,
    smart_remove_sound_words,
)

__all__ = [
    # Version
    "__version__",
    # Main API
    "normalize_text",
    # Configuration
    "Config",
    "SUPPORTED_LANGUAGES",
    # Entity extraction
    "Entity",
    "EntityExtractor",
    "EntityType",
    # Pronunciation mappings
    "add_custom_mapping",
    "get_pronunciation_mappings",
    # TTS utilities
    "parse_sound_word_field",
    "smart_remove_sound_words",
    "add_random_commas",
    # ---- Deprecated (backward compat) ----
    "NormalizationConfig",
    "Profile",
    "FeatureGroup",
    "FeatureLevel",
    "minimal_config",
    "basic_config",
    "standard_config",
    "aggressive_config",
]
