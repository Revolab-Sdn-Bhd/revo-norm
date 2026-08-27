"""revo_norm — shim over the compiled revonorm engine.

This package re-exports revonorm wholesale; the Rust engine is the single
source of truth. The public API is unchanged.
"""

from revonorm import *  # noqa: F401,F403
__version__ = "0.9.0"
from revonorm import normalize_text  # explicit for importers
from revonorm.compat import (  # noqa: F401
    PRONUNCIATION_MAPPINGS,
    SUPPORTED_LANGUAGES,
    Config,
    Entity,
    EntityExtractor,
    EntityType,
    Feature,
    Profile,
    add_custom_mapping,
    get_pronunciation_mappings,
    normalize_text_detailed,
)
from revonorm import tts_utils

# submodules the private test suite imports directly
import revonorm.pronunciation_mappings_compat as pronunciation_mappings  # noqa: F401
