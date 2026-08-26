# revonorm-core — Rust core for revo-norm

One normalization logic, many SDKs. This crate is a faithful Rust port of
the Python `revo_norm` normalizers, built once and consumed as:

- **wasm** (browser — `revolab-web` npm package uses it to expand
  `RM10.50` → "sepuluh ringgit lima puluh sen" before phonemization)
- **cdylib / C ABI** (C#/.NET via `DllImport`, Python via `ctypes`)
- future PyO3 wheel

## Status

The **Malay** path is complete and proven:
`normalizer_ms.py` + `num2word_ms.py` + `currency_utils.py`.

Other languages (id/en/zh/zh_my) remain Python-only until ported —
the porting pattern is established here and repeats per language.

## Parity contract

The Rust code must behave **exactly** like the Python implementation.
`tests/*.txt` fixtures are generated from Python
(`tests/parity_gen.py` + the corpus generator script); every test
suite asserts exact-match:

| Suite | Cases |
|---|---|
| num2word unit | 26 handpicked |
| num2word fixtures | 199 (random to 10⁷ + magnitude boundaries) |
| normalize targeted | 28 (currency, dates, times, %, phones, mixed-alnum — incl. Python's quirks) |
| normalize corpus | 2,000 shuffled corpus sentences |
| wasm corpus | the same 2,000 through the wasm build |

Run:

```bash
cd revonorm-core
cargo test                                   # native parity
wasm-bindgen --target nodejs --out-dir pkg-node \
  target/wasm32-unknown-unknown/release/revonorm_core.wasm   # wasm parity (see repo CI)
```

When Python normalization rules change: regenerate fixtures from the
updated Python, fix the Rust side until all suites pass. CI enforces
this on every PR.
