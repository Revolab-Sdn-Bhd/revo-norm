# Configuration

Revo-norm provides a simple feature-toggle system with profile presets. By default, all features are enabled -- no configuration is needed for most use cases.

## Quick Start

```python
from revo_norm import normalize_text

# Default: all features enabled
result = normalize_text("RM 4500 & 25C", language="ms")
```

If you want less or more aggressive normalization, use profiles or disable specific features.

---

## Profile Presets

Profiles provide pre-configured sets of feature toggles for common use cases. Pass the profile name as a string to `normalize_text()`:

```python
result = normalize_text(text, language="en", profile="basic")
```

### Available Profiles

| Profile | Description | Best For |
|---------|-------------|----------|
| `minimal` | Spacing cleanup only | Pre-processed text, minimal transformation |
| `basic` | Core text cleanup (acronyms, abbreviations, spacing) | Conversational chat, informal text |
| `standard` | All features enabled (default) | News, articles, formal text |
| `aggressive` | All features + strips any `[...]` content | Social media, noisy transcripts |

### Feature Comparison

| Feature | `minimal` | `basic` | `standard` | `aggressive` |
|---------|:---------:|:-------:|:----------:|:------------:|
| spacing | yes | yes | yes | yes |
| acronyms | no | yes | yes | yes |
| abbreviations | no | yes | yes | yes |
| elongated | no | yes | yes | yes |
| malay_local | no | yes | yes | yes |
| special_chars | no | yes | yes | yes |
| measurements | no | no | yes | yes |
| dates | no | no | yes | yes |
| times | no | no | yes | yes |
| temperature | no | no | yes | yes |
| fractions | no | no | yes | yes |
| x_kali | no | no | yes | yes |
| ic | no | no | yes | yes |
| hari_bulan | no | no | yes | yes |
| hijri | no | no | yes | yes |
| pronunciation_overrides | no | no | yes | yes |
| strip_bracketed `[...]` | no | no | no | yes |

### Choosing the Right Profile

**Chat applications (WhatsApp, Telegram, Discord):**
```python
normalize_text(text, language="ms", profile="basic")
```
Enables core cleanup (contractions, acronyms, spacing) without heavy entity processing. Keeps responses fast and predictable.

**News and articles:**
```python
normalize_text(text, language="en")  # standard is default
```
Full normalization including dates, times, currency, measurements, and all entity types.

**Social media (Twitter/X, TikTok comments):**
```python
normalize_text(text, language="ms", profile="aggressive")
```
Handles elongated words ("celakaaa"), special characters, and all entity types. Populate `sound_words` to remove filler words.

**Already-clean text (subtitles, transcripts):**
```python
normalize_text(text, language="en", profile="minimal")
```
Only collapses whitespace. Useful when text has already been processed and you want minimal side effects.

---

## Disabling Specific Features

If a profile is close to what you need but you want to turn off one or two features, use the `disable` parameter:

```python
result = normalize_text(
    "5km run at 25C",
    language="en",
    disable=["measurements", "temperature"]
)
# Output: "five k m run at twenty five C" (measurements and temperature left unprocessed)
```

### Complete List of Disable-able Feature Names

These are the boolean fields on the `Config` object that can be passed in the `disable` list:

| Feature Name | What It Controls |
|-------------|-----------------|
| `acronyms` | Acronym expansion (`API` -> `A P I`, `NASA` -> `NASA`) |
| `abbreviations` | Abbreviation expansion (`Dr.` -> `Doctor`, `Mr.` -> `Mister`) |
| `spacing` | Whitespace collapsing and normalization |
| `measurements` | Unit conversion (`5km` -> `five kilometers`, `10kg` -> `ten kilograms`) |
| `dates` | Date normalization (`15/08/2025` -> spoken date) |
| `times` | Time normalization (`3:30 pm` -> spoken time) |
| `temperature` | Temperature normalization (`25C` -> `twenty five degrees celsius`) |
| `fractions` | Fraction normalization (`3/4` -> `three quarters`) |
| `x_kali` | Malay x-kali multiplier (`3x` -> `tiga kali`) |
| `ic` | Malaysian IC number normalization (12-digit identity card) |
| `hari_bulan` | Malay hari bulan date format (`10 hari bulan 5`) |
| `hijri` | Hijri/Islamic calendar year conversion |
| `elongated` | Elongated word normalization (`celakaaa` -> `celaka`) |
| `malay_local` | Malay-specific local features |
| `special_chars` | Special character replacement (`&` -> `and`, `@` -> `at`) |
| `pronunciation_overrides` | Legacy pronunciation override patterns |

### Examples

```python
from revo_norm import normalize_text

# Disable temperature and measurements for a weather script that handles these separately
result = normalize_text(text, language="en", disable=["temperature", "measurements"])

# Combine profile with disable
result = normalize_text(text, language="ms", profile="basic", disable=["acronyms"])

# Disable multiple features
result = normalize_text(
    text,
    language="en",
    disable=["fractions", "dates", "times", "temperature"]
)
```

---

## Advanced: Creating a Config Object Directly

For fine-grained control, create a `Config` object and pass individual feature toggles:

```python
from revo_norm import normalize_text
from revo_norm.config import Config

# Create a custom config
cfg = Config()
cfg.temperature = False
cfg.measurements = False
cfg.hijri = False

# Use it (via the legacy config= parameter)
result = normalize_text(text, language="ms", config=cfg)
```

### Config Class Methods

```python
from revo_norm.config import Config

# From profile name
cfg = Config.from_profile("basic")

# With specific features disabled
cfg = Config.with_disabled(["acronyms", "measurements"])

# Check if a feature is enabled
cfg.is_enabled("temperature")  # Returns True

# List all feature fields
Config._feature_fields()  # Returns list of boolean field names
```

### Programmatic Feature Control

```python
from revo_norm.config import Config

cfg = Config()           # All features on (standard)
cfg.acronyms = False     # Turn off acronym expansion
cfg.fractions = False    # Turn off fraction normalization
cfg.dates = True         # Explicitly enable (already default)

# Check before running
if cfg.should_run_shared_features("ms"):
    # Malay-specific features will run
    pass
```

---

## Adding Custom Pronunciation Mappings

The pronunciation mappings system lets you define how specific terms should be spoken. These mappings are applied **first** in the pipeline, before any other transformations, so they always take priority.

```python
from revo_norm import normalize_text
from revo_norm.pronunciation_mappings import add_custom_mapping

# Add a custom mapping
add_custom_mapping("YOLO", "you only live once", "en")

result = normalize_text("YOLO approach", language="en")
# Output: "you only live once approach"
```

> **Note:** `add_custom_mapping()` modifies a module-level dictionary and is not thread-safe. For thread-safe usage, add mappings during application startup before any calls to `normalize_text()`.

---

## Backward Compatibility

The old API (boolean flags, `NormalizationConfig`, `FeatureGroup`, `FeatureLevel`, `Profile` enums) is still accepted but emits `DeprecationWarning`. See the [Migration Guide](migration.md) for details.
