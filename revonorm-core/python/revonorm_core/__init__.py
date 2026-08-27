"""PyO3 bindings: revonorm_core.normalize_text mirrors revo_norm's API.

The rust core is the single source of truth for normalization logic; this
wrapper keeps the python calling convention stable for consumers.
"""

from ._core import normalize, supported_languages

__all__ = ["normalize", "supported_languages"]


def normalize_text(text: str, language: str, profile: str | None = None,
                   disable: list[str] | None = None) -> str:
    """Normalize *text* for *language* — same signature as revo_norm.

    profile/disable map into the options JSON the rust pipeline consumes.
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
