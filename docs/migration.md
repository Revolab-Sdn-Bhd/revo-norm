# Migration Guide

Covers migrating to the **v0.5.0** API. v0.5.0 removed the deprecated surface outright — old calls now raise `TypeError`, not `DeprecationWarning`.

## v0.5.0 in one minute

| Pre-0.5 call | v0.5.0 call |
|---|---|
| `normalize_text(text)` (defaulted to `en`) | `normalize_text(text, language="en")` — **required** |
| `normalize_text(text, "ms", verbose=True)` | `normalize_text_detailed(text, "ms").text / .mappings / .rules` |
| `normalize_text(..., sound_words_field="a\nb")` | `cfg = Config(); cfg.sound_words = ["a", "b"]` then `normalize_text(..., config=cfg)` |
| `normalize_text(..., normalize_temperature_flag=False)` | `normalize_text(..., disable=[Feature.TEMPERATURE])` |
| `standard_config()` etc. | `Config()` / `Config.from_profile("standard")` or `profile=` |
| `NormalizationConfig`, `FeatureGroup`, `FeatureLevel` | `Config`, `Feature` (profile strings or `Profile` enum) |

New in v0.5.0: `Profile` and `Feature` enums, `normalize_text_detailed` → typed `NormalizationResult`, `config=` passthrough, and language packs (`LanguagePack`, `register_language`, `supported_languages`) for adding languages without touching core files.

---

## Legacy reference (pre-0.4 → 0.4)

## Quick Reference

### Old API to New API

| Old API | New API |
|---------|---------|
| `normalize_text(text, language, extract_entities_first=True)` | `normalize_text(text, language)` |
| `normalize_text(text, language, normalize_temperature_flag=False)` | `normalize_text(text, language, disable=["temperature"])` |
| `normalize_text(text, language, config=standard_config())` | `normalize_text(text, language)` |
| `normalize_text(text, language, config=NormalizationConfig.from_preset("minimal"))` | `normalize_text(text, language, profile="minimal")` |
| `config.with_feature(FeatureGroup.ACRONYMS, FeatureLevel.OFF)` | `disable=["acronyms"]` or `cfg.acronyms = False` |
| `NormalizationConfig.from_preset("minimal")` | `Config.from_profile("minimal")` or `profile="minimal"` |
| `minimal_config()` | `Config.from_profile("minimal")` or `profile="minimal"` |
| `basic_config()` | `Config.from_profile("basic")` or `profile="basic"` |
| `standard_config()` | `Config()` or `profile="standard"` |
| `aggressive_config()` | `Config.from_profile("aggressive")` or `profile="aggressive"` |
| `FeatureGroup.ACRONYMS` | String `"acronyms"` |
| `FeatureLevel.OFF` | Boolean `False` |
| `Profile.MINIMAL` | String `"minimal"` |

### Old Flags to New Disable Names

Each legacy boolean flag maps to a feature name you can pass in `disable`:

| Old Flag | New Feature Name |
|----------|-----------------|
| `normalize_spacing` | `spacing` |
| `fix_dot_letters` | `acronyms` |
| `apply_pronunciation_overrides_flag` | `pronunciation_overrides` |
| `expand_abbreviations_flag` | `abbreviations` |
| `expand_acronyms_flag` | `acronyms` |
| `normalize_elongated_flag` | `elongated` |
| `normalize_fractions_flag` | `fractions` |
| `normalize_x_kali_flag` | `x_kali` |
| `normalize_temperature_flag` | `temperature` |
| `normalize_ic_flag` | `ic` |
| `normalize_measurements_flag` | `measurements` |
| `normalize_hari_bulan_flag` | `hari_bulan` |
| `normalize_hijri_flag` | `hijri` |
| `sound_words_field` | `cfg.sound_words` (list) |
| `extract_entities_first` | Always enabled (ignore) |

---

## What Changed

### 1. `profile=` Parameter Replaces Config Factory Functions

Previously, you needed to import and call a factory function:

```python
# OLD
from revo_norm import normalize_text
from revo_norm.config import standard_config

config = standard_config()
result = normalize_text(text, language="en", config=config)
```

Now, use the `profile` parameter directly:

```python
# NEW
from revo_norm import normalize_text

result = normalize_text(text, language="en")                    # standard (default)
result = normalize_text(text, language="en", profile="minimal") # minimal
result = normalize_text(text, language="en", profile="basic")   # basic
```

### 2. `disable=` Parameter Replaces Boolean Flags

Previously, each feature had its own boolean flag:

```python
# OLD
result = normalize_text(
    text,
    language="en",
    normalize_temperature_flag=False,
    normalize_measurements_flag=False,
    normalize_fractions_flag=False,
)
```

Now, use the `disable` list:

```python
# NEW
result = normalize_text(
    text,
    language="en",
    disable=["temperature", "measurements", "fractions"]
)
```

### 3. Entity Extraction Is Always Enabled

The `extract_entities_first=True` parameter used to opt into the entity extraction pipeline. Entity extraction is now always enabled as part of the single unified pipeline. Passing `extract_entities_first=True` is accepted but ignored.

```python
# OLD
result = normalize_text(text, language="ms", extract_entities_first=True)

# NEW (identical behavior, just remove the flag)
result = normalize_text(text, language="ms")
```

### 4. Enums Replaced by Strings

The `FeatureGroup`, `FeatureLevel`, and `Profile` enums are deprecated. Use plain strings instead:

```python
# OLD
from revo_norm.config import FeatureGroup, FeatureLevel, Profile

cfg = Config()
cfg.with_feature(FeatureGroup.ACRONYMS, FeatureLevel.OFF)
profile_name = Profile.MINIMAL

# NEW
cfg = Config()
cfg.acronyms = False
profile_name = "minimal"
```

---

## What Was Removed

The following were **removed in v0.5.0** — importing or calling them now raises:

| Removed | Replacement |
|---------|-------------|
| `NormalizationConfig` class | `Config` class |
| `FeatureGroup` enum | `Feature` enum or plain strings (`"acronyms"`, `"measurements"`, etc.) |
| `FeatureLevel` enum | Boolean `True`/`False` |
| Old `Profile` enum | New `Profile` enum or plain strings (`"minimal"`, `"basic"`, `"standard"`, `"aggressive"`) |
| `minimal_config()` | `Config.from_profile("minimal")` or `profile="minimal"` |
| `basic_config()` | `Config.from_profile("basic")` or `profile="basic"` |
| `standard_config()` | `Config()` or `profile="standard"` |
| `aggressive_config()` | `Config.from_profile("aggressive")` or `profile="aggressive"` |
| `config.with_feature()` | Direct attribute: `cfg.acronyms = False` |
| `config.with_sound_words()` | Direct attribute: `cfg.sound_words = [...]` |
| Legacy boolean flags in `normalize_text()` | `profile=`, `disable=`, or `config=Config(...)` (sound words: `cfg.sound_words`) |

---

## Migration Examples

### Minimal Cleanup

```python
# OLD
result = normalize_text(text, language="en", config=minimal_config())

# NEW
result = normalize_text(text, language="en", profile="minimal")
```

### Disable Temperature and Measurements

```python
# OLD
result = normalize_text(
    text, language="en",
    normalize_temperature_flag=False,
    normalize_measurements_flag=False,
)

# NEW
result = normalize_text(text, language="en", disable=["temperature", "measurements"])
```

### Custom Config with Feature Control

```python
# OLD
from revo_norm.config import standard_config, FeatureGroup, FeatureLevel

cfg = standard_config()
cfg.with_feature(FeatureGroup.ACRONYMS, FeatureLevel.OFF)
cfg.with_feature(FeatureGroup.MEASUREMENTS, FeatureLevel.OFF)
result = normalize_text(text, language="en", config=cfg)

# NEW
from revo_norm import normalize_text

result = normalize_text(text, language="en", disable=["acronyms", "measurements"])
```

### Sound Words Removal

```python
# OLD
result = normalize_text(
    text, language="ms",
    sound_words_field="lah\nke"
)

# NEW
from revo_norm.config import Config

cfg = Config()
cfg.sound_words = ["lah", "ke"]
result = normalize_text(text, language="ms", config=cfg)
```

---

## Deprecation Timeline

- **v0.2.0:** Old API still works but emits `DeprecationWarning` for all legacy parameters
- **v0.3.0 (planned):** Legacy parameters, enums, and factory functions will be removed
- The new `profile=` and `disable=` API is stable and recommended for all new code
