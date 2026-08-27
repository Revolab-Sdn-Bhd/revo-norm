"""revonorm — multilingual TTS text normalization.

normalize_text(text, language) mirrors revo_norm's API; options map into
the JSON the pipeline consumes.
"""

from ._core import normalize, supported_languages

__all__ = ["normalize", "normalize_text", "supported_languages"]


def normalize_text(text: str, language: str, profile: str | None = None,
                   disable: list[str] | None = None) -> str:
    """Normalize *text* for *language* — same signature as revo_norm.

    profile/disable map into the options JSON the pipeline consumes.
    """
    import json

    opts: dict = {}
    if profile is not None:
        opts["profile"] = profile
    if disable:
        opts["disable"] = disable
    result = normalize(text, language, json.dumps(opts) if opts else "")
    if result.startswith("__ERROR__"):
        raise ValueError(result[len("__ERROR__"):])
    return result
