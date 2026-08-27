# @revolab/revonorm

Text normalization for TTS — converts written text (numbers, currency, dates,
times, symbols) into spoken words across 5 languages: `ms`, `id`, `en`, `zh`,
`zh_my`.

```bash
npm install @revolab/revonorm        # node
npm install @revolab/revonorm-web    # browser (webpack/vite/esbuild)
```

Both packages have the identical API — the only difference is how the wasm loads.

## Use

```js
const { normalize } = require('@revolab/revonorm');

normalize('Harga RM10.50 sahaja', 'ms');   // "Harga sepuluh ringgit lima puluh sen sahaja"
normalize('It costs $5.50', 'en');         // "It costs five dollar fifty cents"
normalize('价格是RM50，温度25C', 'zh');     // "价格是五十令吉，温度二十五摄氏度"
normalize('Rp5rb dan 5jt', 'id');          // "lima ribu rupiah dan lima juta"
```

## API

### `normalize(text, language)` → `string`

Language is required.

### `normalize_with_options(text, language, optionsJson)` → `string`

Config as JSON:

```js
normalize_with_options('top up RevoPay RM30K', 'ms', JSON.stringify({
  pronunciations: { '*': { RevoPay: 'revo pay' } },
}));
// "top up revo pay tiga puluh ribu ringgit"

normalize_with_options('sambung WiFi', 'ms', JSON.stringify({
  pronunciations: { '*': { WiFi: null } },   // null = leave as written
}));
// "sambung WiFi"
```

| Option | What it does |
|---|---|
| `profile` | `"minimal"`, `"basic"`, `"standard"`, `"aggressive"` |
| `disable` | Features to turn off, e.g. `["acronyms", "measurements"]` |
| `pronunciation_profile` | `"builtin"` (default), `"none"`, or a custom name |
| `pronunciations` | Term overrides. `"*"` = all languages; a language code scopes it. `null` deletes the term. |

### `supported_languages()` → `string`

```js
supported_languages();   // "en,id,ms,zh,zh_my"
```

## Errors

Failures return a string prefixed with `__ERROR__`:

```js
const out = normalize(text, lang);
if (out.startsWith('__ERROR__')) throw new Error(out.slice(9));
```
