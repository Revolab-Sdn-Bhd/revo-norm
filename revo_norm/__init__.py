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

__version__ = "0.6.0"

from revo_norm.config import SUPPORTED_LANGUAGES, Config, Feature, Profile
from revo_norm.entity_extractor import Entity, EntityExtractor, EntityType
from revo_norm.langpack import LanguagePack, register_language, supported_languages
from revo_norm.pronunciation_mappings import (
    add_custom_mapping,
    get_pronunciation_mappings,
    get_registered_profiles,
    pronunciations_from_file,
    register_pronunciation_profile,
)
from revo_norm.text_normalizer import (
    NormalizationResult,
    normalize_text,
    normalize_text_detailed,
)
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
    "normalize_text_detailed",
    "NormalizationResult",
    # Configuration
    "Config",
    "Profile",
    "Feature",
    "SUPPORTED_LANGUAGES",
    # Language packs
    "LanguagePack",
    "register_language",
    "supported_languages",
    # Entity extraction
    "Entity",
    "EntityExtractor",
    "EntityType",
    # Pronunciation mappings
    "add_custom_mapping",
    "get_pronunciation_mappings",
    "get_registered_profiles",
    "pronunciations_from_file",
    "register_pronunciation_profile",
    # TTS utilities
    "parse_sound_word_field",
    "smart_remove_sound_words",
    "add_random_commas",
]
