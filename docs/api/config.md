# `Config`

Feature-toggle configuration for text normalization.

::: revo_norm.config.Config

## Feature Fields

All boolean fields default to `True` (standard profile).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `acronyms` | `bool` | `True` | Expand acronyms (I.B.M. to I B M, API to A P I) |
| `abbreviations` | `bool` | `True` | Expand abbreviations (currently a no-op placeholder) |
| `spacing` | `bool` | `True` | Normalize whitespace (collapse multiple spaces) |
| `measurements` | `bool` | `True` | Normalize measurements (5km to five kilometers, 10kg to ten kilograms) |
| `dates` | `bool` | `True` | Convert dates to spoken form (15/08/2025 to fifteenth of August ...) |
| `times` | `bool` | `True` | Convert times to spoken form (3:30 pm to three thirty p m) |
| `temperature` | `bool` | `True` | Convert temperatures to spoken form (25C to twenty five degrees Celsius) |
| `fractions` | `bool` | `True` | Convert fractions to spoken form (3/4 to three quarters) |
| `x_kali` | `bool` | `True` | Convert multipliers to spoken form (5x to lima kali) |
| `ic` | `bool` | `True` | Normalize Malaysian IC numbers (900101-10-1234 to spoken form) |
| `hari_bulan` | `bool` | `True` | Normalize hari bulan patterns (Malay day-of-month format) |
| `hijri` | `bool` | `True` | Normalize Hijri years to spoken form |
| `elongated` | `bool` | `True` | Normalize elongated words (soooo to so) |
| `malay_local` | `bool` | `True` | Enable Malay-specific local features |
| `special_chars` | `bool` | `True` | Replace special characters (& to and, % to percent/peratus) |
| `pronunciation_overrides` | `bool` | `True` | Apply pronunciation overrides (legacy word-level corrections) |
| `sound_words` | `list[str]` | `[]` | Sound words to remove or replace (e.g., `[laughter]`, `[applause]`) |
| `strip_bracketed` | `bool` | `False` | Strip all `[...]` content from text (enabled in aggressive profile) |

## Constructors

### `Config()` {: #config-init }

Creates a standard configuration with all features enabled.

```python
from revo_norm.config import Config

cfg = Config()  # All features enabled
```

### `Config.from_profile(name)` {: #from-profile }

::: revo_norm.config.Config.from_profile

Creates a Config from a named profile.

**Profile comparison:**

| Feature | `minimal` | `basic` | `standard` | `aggressive` |
|---------|:---------:|:-------:|:----------:|:------------:|
| `spacing` | ON | ON | ON | ON |
| `acronyms` | off | ON | ON | ON |
| `abbreviations` | off | ON | ON | ON |
| `elongated` | off | ON | ON | ON |
| `malay_local` | off | ON | ON | ON |
| `special_chars` | off | ON | ON | ON |
| `measurements` | off | off | ON | ON |
| `dates` | off | off | ON | ON |
| `times` | off | off | ON | ON |
| `temperature` | off | off | ON | ON |
| `fractions` | off | off | ON | ON |
| `x_kali` | off | off | ON | ON |
| `ic` | off | off | ON | ON |
| `hari_bulan` | off | off | ON | ON |
| `hijri` | off | off | ON | ON |
| `pronunciation_overrides` | off | off | ON | ON |

!!! note
    `aggressive` has the same feature toggles as `standard`. The difference is that `aggressive` may populate `sound_words` with a default list.

```python
from revo_norm.config import Config

cfg = Config.from_profile("minimal")  # Spacing only
cfg = Config.from_profile("basic")    # Core features
cfg = Config.from_profile("standard") # Everything
cfg = Config.from_profile("aggressive") # Everything
```

Raises `ValueError` for unknown profile names.

### `Config.with_disabled(features)` {: #with-disabled }

::: revo_norm.config.Config.with_disabled

Creates a standard Config with specific features disabled. Unknown feature names emit a warning and are ignored.

```python
from revo_norm.config import Config

# Disable acronym expansion and measurement normalization
cfg = Config.with_disabled(["acronyms", "measurements"])

# cfg.acronyms == False
# cfg.measurements == False
# cfg.dates == True  (everything else stays on)
```

## Methods

### `is_enabled(feature)` {: #is-enabled }

::: revo_norm.config.Config.is_enabled

Check whether a feature is enabled. Returns `True` for unknown feature names (safe default).

```python
from revo_norm.config import Config

cfg = Config.with_disabled(["acronyms"])
cfg.is_enabled("acronyms")    # False
cfg.is_enabled("temperature") # True
cfg.is_enabled("unknown")     # True (safe default)
```

### `should_run_shared_features(language)` {: #should-run-malay }

Returns `True` if Malay-local features should run for the given language. This is `True` only when `malay_local` is enabled **and** `language == "ms"`.

## Deprecated Methods

These methods are retained for backward compatibility but emit `DeprecationWarning`.

### `with_feature(group, level)` {: #with-feature }

Use direct attribute assignment instead:

```python
# Deprecated
cfg.with_feature(FeatureGroup.ACRONYMS, FeatureLevel.OFF)

# Preferred
cfg.acronyms = False
```

### `with_sound_words(words)` {: #with-sound-words }

Set `cfg.sound_words` directly instead:

```python
# Deprecated
cfg.with_sound_words(["[laughter]", "[applause]"])

# Preferred
cfg.sound_words = ["[laughter]", "[applause]"]
```

## Deprecated Factory Functions

These module-level functions are deprecated in favor of `Config.from_profile()`:

| Deprecated | Replacement |
|------------|-------------|
| `minimal_config()` | `Config.from_profile("minimal")` |
| `basic_config()` | `Config.from_profile("basic")` |
| `standard_config()` | `Config()` or `Config.from_profile("standard")` |
| `aggressive_config()` | `Config.from_profile("aggressive")` |

## Backward-Compatible Aliases

| Alias | Actual Class |
|-------|-------------|
| `NormalizationConfig` | `Config` |

The deprecated enums `FeatureGroup`, `FeatureLevel`, and `Profile` are still importable for backward compatibility but should not be used in new code.
