# revonorm-core — Rust core for revo-norm

One normalization logic, many SDKs. A faithful Rust port of the Python
`revo_norm` pipeline, built once and consumed as:

- **wasm** (browser/node — `normalize(text, lang, options_json)`;
  errors cross the boundary as `__ERROR__`-prefixed strings)
- **cdylib / C ABI** (C# via `DllImport`, Python via `ctypes`)
- **PyO3 wheel** (`pip install revonorm-core` →
  `from revonorm_core import normalize_text`)

## Status

**All five languages ported and at parity**: ms, id, en, zh, zh_my —
95 fixture cases byte-equal against the Python library, plus an
81-case differential smoke (wheel vs pure-Python) and consumer
call-path verification.

## Layout

| Module | Purpose |
|---|---|
| `pipeline.rs` | Step order (python's): suffixes → negatives → extract → overrides → measurements → pron → stash → language pass → acronyms → restore → symbols |
| `langpack.rs` + `lang/` | Per-language packs — symbol words, digits, months, unit tables, negative word, currency names |
| `normalize.rs` / `_id` / `_en` / `_zh` | Language normalizer passes (self-contained, like python's) |
| `num2word.rs` / `num2word_en.rs` | Number engines: ms/id vocab-parameterized; en inflect-compatible (107/107 cross-check) |
| `entities.rs` | Extract → `<<<TYPE_N>>>` placeholders → restore with spoken converters |
| `shared.rs` | Measurements pass + shared-feature entities (temperature, fraction, x-kali, IC, hari-bulan, hijri) |
| `pron.rs` | Builtin pronunciation profile, whole-word apply |
| `options.rs` | JSON config surface (profile, disable, pronunciation layers) |
| `pybind.rs` | PyO3 surface (`pyffi` feature) |

## Parity contract

The Rust code must behave **exactly** like the Python implementation.
`tests/fixtures/*.txt` are generated from Python
(`uv run python revonorm-core/tests/gen_fixtures.py` from the repo
root); `tests/parity.rs` asserts byte-equality:

| Suite | Cases |
|---|---|
| num2word ms | 175 (handpicked + boundaries + random to 10⁷) |
| pipeline ms | 35 |
| pipeline id | 20 |
| pipeline en | 24 |
| pipeline zh | 16 |
| options/layers | error paths, pronunciation layers, profiles |

CI regenerates fixtures from Python on every PR — a Python rule change
without a matching Rust change fails the build.

## Commands

```bash
cargo test --manifest-path revonorm-core/Cargo.toml   # parity
cargo clippy --manifest-path revonorm-core/Cargo.toml -- -D warnings
cargo build --release --manifest-path revonorm-core/Cargo.toml \
  --target wasm32-unknown-unknown                      # wasm
PYO3_PYTHON=$(which python) maturin develop --release \
  --manifest-path revonorm-core/Cargo.toml             # python wheel
```

## When Python rules change

1. Regenerate: `uv run python revonorm-core/tests/gen_fixtures.py`
2. Fix the Rust side until `cargo test` is green
3. CI enforces this on every PR

## Known tracked gaps

- `add_random_commas` and tts_utils stay pure-Python (server-side
  text hygiene, not normalization logic)
- zh_my URL separator deliberately differs from zh (冒号 slash slash)
