# Revo Norm

Text normalization for Text-to-Speech, built for **English** and **Malay** (Bahasa Melayu).

Revo Norm converts written text — numbers, currency, dates, times, abbreviations, acronyms, and more — into natural spoken form so your TTS engine reads it the way a human would say it.

---

## 30-Second Quickstart

```python
from revonorm import normalize_text

# English
print(normalize_text("The price is RM50K due on 15/08/2025", language="en"))
# "The price is fifty thousand ringgit due on fifteen of August twenty twenty-five"

# Malay
print(normalize_text("Suhu 25C hari ini", language="ms"))
# "Suhu dua puluh lima celcius hari ini"

# Minimal — just fix spacing
print(normalize_text("Hello   world", language="en", profile="minimal"))
# "Hello world"
```

## Key Features

- **Currency normalization** — `RM50K`, `$1.5M`, `USD 200B` expanded and spoken
- **Date recognition** — `15/08/2025`, `2025-08-15`, `15 August 2025`
- **Time recognition** — `3:30 pm`, `14:00`
- **Number-to-words** — cardinal and ordinal numbers in the selected language
- **Acronym handling** — `IBM` → "I B M", `NASA` preserved, `JSON` → "J son"
- **Temperature** — `25C`, `100°F` converted to spoken form
- **Fractions** — `3/4` → "three over four"
- **Measurements** — `5km`, `10kg`, `3GB`
- **Entity protection** — currency, URLs, emails, and dates shielded from cascading transforms
- **Pronunciation mappings** — custom overrides with highest pipeline priority (`GUI` → "gooey")
- **Multilingual** — one `language` parameter selects the normalizer (see [Languages](languages.md))
- **Configurable profiles** — `minimal`, `basic`, `standard`, `aggressive` presets

## Installation

```bash
# pip
pip install revo-norm

# uv (recommended)
uv add revo-norm
```

See the [Installation Guide](installation.md) for all options including source installs and dev setup.

## Documentation

| Page | Description |
|------|-------------|
| [Installation](installation.md) | Install via pip, uv, or from source |
| [Quickstart Guide](quickstart.md) | 5-minute walkthrough with examples |
| [API Reference](api/normalize.md) | Full API documentation |
| [Features](features/currency.md) | Detailed feature guides |

## License

MIT
