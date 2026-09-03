"""revonorm — multilingual TTS text normalization.

The full original revo_norm API surface, backed by the compiled engine:
normalize_text + config + pronunciation layers + num2word functions +
entity extraction + tts_utils. Consumers can switch imports from
revo_norm to revonorm with zero code changes.
"""

from . import tts_utils
from ._core import (
    normalize,
    supported_languages,
    to_cardinal_id,
    to_cardinal_ms,
    to_cardinal_zh,
    to_currency_zh,
    to_year_zh,
)
from .compat import (
    SUPPORTED_LANGUAGES,
    Config,
    Entity,
    EntityExtractor,
    EntityType,
    Feature,
    LanguagePack,
    NormalizationResult,
    Profile,
    add_custom_mapping,
    get_pronunciation_mappings,
    get_registered_profiles,
    normalize_text,
    normalize_text_detailed,
    pronunciations_from_file,
    register_language,
    register_pronunciation_profile,
)

__version__ = "1.2.0"

__all__ = [
    "__version__",
    # Main API
    "normalize_text",
    "normalize_text_detailed",
    "NormalizationResult",
    "normalize",
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
    # num2word
    "to_cardinal_ms",
    "to_cardinal_id",
    "to_cardinal_zh",
    "to_currency_zh",
    "to_year_zh",
    # TTS utilities (pure python by design)
    "tts_utils",
]
