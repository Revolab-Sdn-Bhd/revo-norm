# Revo Norm

**Text normalization library for TTS applications — English, Malay, Indonesian, and Chinese.**

> Designed for **text-to-speech** only. NOT for ASR preprocessing.

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

## Install

The same engine ships as three packages — pick the one for your runtime:

```bash
pip install revonorm                    # Python (wheel)
npm install @revolab/revonorm           # Node.js
npm install @revolab/revonorm-web       # Browser (webpack/vite/esbuild)
```

> `revo-norm` (pure Python) still exists and exposes the identical API; it is
> the original implementation. `revonorm` is the compiled engine.

## Usage

### Python

```python
from revonorm import normalize_text

# English
normalize_text("Meeting at 3:30 pm", language="en")

# Malay
normalize_text("Harga RM100 untuk 5 unit", language="ms")

# Indonesian
normalize_text("Harga Rp1.500.000 untuk 5 unit", language="id")

# Chinese (Standard)
normalize_text("RM50 在 15/08/2025", language="zh")

# Malaysian Chinese (colloquial currency, code-mixing)
normalize_text("花了 $100 买 5km 外的东西", language="zh_my")

# With profile
normalize_text(text, language="en", profile="basic")

# Disable features
normalize_text(text, language="en", disable=["temperature", "measurements"])
```

### JavaScript

```js
const { normalize } = require('@revolab/revonorm');

normalize('Harga RM10.50 sahaja', 'ms');   // "Harga sepuluh ringgit lima puluh sen sahaja"
normalize('It costs $5.50', 'en');         // "It costs five dollar fifty cents"
normalize('价格是RM50，温度25C', 'zh');     // "价格是五十令吉，温度二十五摄氏度"

// Pronunciation overrides (company terms, model quirks)
normalize('top up RevoPay RM30K', 'ms', JSON.stringify({
  pronunciations: { '*': { RevoPay: 'revo pay' } },
}));
```

Errors return strings prefixed with `__ERROR__` — check the prefix.

## Supported Languages

| Code | Language |
|------|----------|
| `en` | English |
| `ms` | Malay (Bahasa Melayu) |
| `id` | Indonesian (Bahasa Indonesia) |
| `zh` | Chinese (Standard) |
| `zh_my` | Malaysian Chinese |

## Documentation

**[revolab-sdn-bhd.github.io/revo-norm](https://revolab-sdn-bhd.github.io/revo-norm/)**

## Contributing

See **[CONTRIBUTING.md](CONTRIBUTING.md)**. Short version: fork, branch,
PR — tests live in a private repo and run in CI automatically.

## License

MIT
