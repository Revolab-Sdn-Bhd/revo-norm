"""revo_norm — shim over the compiled revonorm engine.

This package re-exports revonorm wholesale; the Rust engine is the single
source of truth. The public API is unchanged.
"""

from revonorm import *  # noqa: F401,F403

__version__ = "0.9.0"
# submodules the private test suite imports directly
import revonorm.pronunciation_mappings_compat as pronunciation_mappings  # noqa: F401,E402
from revonorm import tts_utils  # noqa: F401,E402
from revonorm.compat import (  # noqa: F401,E402
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
