# revonorm

Text normalization for TTS — converts written text (numbers, currency, dates,
times, symbols) into spoken words across 5 languages: `ms`, `id`, `en`, `zh`,
`zh_my`.

```bash
pip install revonorm
```

## Use

```python
from revonorm import normalize_text

normalize_text('Harga RM10.50 sahaja', 'ms')   # "Harga sepuluh ringgit lima puluh sen sahaja"
normalize_text('It costs $5.50', 'en')         # "It costs five dollar fifty cents"
normalize_text('价格是RM50，温度25C', 'zh')     # "价格是五十令吉，温度二十五摄氏度"
normalize_text('Rp5rb dan 5jt', 'id')          # "lima ribu rupiah dan lima juta"
```

## API

### `normalize_text(text, language, profile=None, disable=None)` → `str`

Language is required. Unknown codes raise `ValueError`.

| Option | What it does |
|---|---|
| `profile` | `"minimal"`, `"basic"`, `"standard"`, `"aggressive"` |
| `disable` | Features to turn off, e.g. `["acronyms", "measurements"]` |

### `normalize(text, language, options_json="")` → `str`

The same pipeline with config as JSON — pronunciation overrides live here:

```python
normalize('top up RevoPay RM30K', 'ms', '{"pronunciations": {"*": {"RevoPay": "revo pay"}}}')
# "top up revo pay tiga puluh ribu ringgit"

normalize('sambung WiFi', 'ms', '{"pronunciations": {"*": {"WiFi": null}}}')
# "sambung WiFi"  (null = leave as written)
```

Pronunciations: `"*"` applies to all languages; a language code scopes it;
`null` deletes the term.

### `supported_languages()` → `list[str]`

```python
supported_languages()   # ['en', 'id', 'ms', 'zh', 'zh_my']
```

## Relationship to `revo-norm`

`revonorm` (this package) and `revo-norm` (pure Python) expose the same
`normalize_text(text, language=...)` API and produce identical output.
Consumers can switch between them without code changes.
