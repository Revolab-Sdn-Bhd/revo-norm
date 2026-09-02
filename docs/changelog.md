# Changelog

All notable changes to revo-norm are documented here.

## v1.0.0 (Current)

**One package: `revonorm`.** The `revo_norm` Python package is deleted; the compiled engine is the sole implementation and the sole import path.

### Docs

- Feature pages (`currency`, `dates`, `times`, `numbers`, `measurements`) cover `id` and `zh`/`zh_my` alongside `en`/`ms`: rupiah and its `rb`/`jt`/`M`/`T` shorthand, Indonesian month names and `pagi`/`siang`/`sore`/`malam` meridians, dotted-thousands number conventions, Chinese unit words, colloquial `zh_my` currency (美金/英磅/块), and Chinese 第-ordinals, percentages, and fractions.
- `docs/features/` now holds cross-language feature pages only. `features/malay.md` is folded into the **Malay Specifics** section of `docs/languages.md` and deleted, along with its nav entry.
- `docs/languages.md` gained the Malay-local feature set (IC numbers, x-kali, hari bulan, Hijri years, elongated words, their disable flags and interactions), an Indonesian equivalents section, and corrected Chinese currency/percent/ordinal tables.
- `quickstart.md` / `index.md` show all five language codes instead of en/ms only.

### Fixed

- Stale example outputs corrected against engine behavior: zh_my `$`/`USD` → 美金 (not 块/美元), `£` sub-unit → 便士, `00:00`/`12:00` → `zero zero`/`twelve zero` (not "midnight"/"noon"), `15/08/2025` → `fifteen of August twenty twenty-five`, `WiFi` → `wi fi`, `$45.99` → `forty-five dollar ninety-nine cents`, `disable=["measurements"]` → `five K M away`.
- Documented two engine limitations instead of misdocumenting them: `100th` and `Aug. 15, 2025` are not converted; Indonesian multi-digit comma fractions (`3,14`) read as two numbers unless preceded by a dotted group.

### Breaking

- `import revo_norm` no longer exists — use `from revonorm import normalize_text`. Same signatures, same output; the 498-test suite passes through the `revonorm` package directly.
- The root project is a dev-only workspace (no hatch package, no registry release under `revo-norm`).

### Added

- Engine-exposed entity API: `EntityExtractor.extract/restore` now run the engine's full 13-type extraction (via `extract_entities`/`entity_to_spoken` pybind surface), honoring `enabled_entities` with caller-ordered ids — python's exact semantics.
- `EntityExtractor._convert_entity_to_spoken` raises `ValueError` on unknown languages (engine gained a non-panicking pack lookup; a cross-FFI `PanicException` is now impossible from this path).
- pybind num2word parity: `to_cardinal_id` accepts negatives (`negatif`), `to_cardinal_zh` raises `OverflowError` past 10¹⁶, `to_currency_zh` speaks the given unit verbatim.

### Changed

- CI lint targets `revonorm-core/python/revonorm/`; docs identifiers and mkdocs paths point at the engine package; the stale `generate_flow.py` analysis script is removed.

## v0.9.0

**The SSOT flip — the Rust engine drives everything.**

### Changed

- **Breaking (internal):** `revonorm` is now a shim re-exporting the compiled `revonorm` engine. Public API unchanged — same imports, signatures, and output — but every normalization rule executes in Rust. Rule edits happen in `revonorm-core/src/` only; the pure-Python implementation lives in git history.
- The full private 498-test suite passes through the engine: all languages, profiles, entity extraction, layered pronunciations, cultural cases

### Added

- Complete feature semantics in the engine: profile/disable gating (incl. entity-type gating with DATE/TIME protect-but-don't-speak), USSD codes, digit-by-digit contexts, elongated words, repeated-word commas, sound-words via the compat layer
- `ADDRESS_SLASH` entity (street-prefixed `Jalan SS2/72` → spoken digits, beats fraction interpretation)
- zh_my colloquial currency (美金/英磅/块), percentage (巴仙), meridian (早上); zh email speech (艾特/点); MM/DD date swap; hour-only meridians by hour
- Python compat layer: `Config`/`Profile`/`Feature`, layered pronunciations (legacy-global < profile < user), entity facade, num2word functions, module-path aliases
- CI snapshots engine output as fixtures (101 cases × 3 profiles + num2word) — regressions fail the build

### Fixed

- num2word: ms/id 8 (`lapan`/`delapan`) hardcoded in the shared tens/teens/hundreds path

## v0.7.0

Rust core at full parity — the single-source-of-truth groundwork.

### Added

- **`revonorm-core/`**: a Rust port of the entire normalization pipeline, all five languages, consumed as **wasm** (`normalize(text, lang, options_json)`), **cdylib** (C ABI), and a **PyO3 wheel** (`from revonorm_core import normalize_text`)
- **Parity contract, CI-enforced**: fixtures are regenerated from Python on every PR (35 ms + 20 id + 24 en + 16 zh byte-equal cases + 175 num2word) — a Python rule change without a matching Rust change fails the build
- **Options surface** (wasm/pyo3): `profile`, `disable`, layered `pronunciations` (`{"*": {...}, "ms": {...}}` with null-deletion) — the model-specific pronunciation use case works from every consumer
- **Verified equivalence beyond fixtures**: 81-case differential smoke (wheel vs pure-Python, all languages) and the internal consumers' call shapes exercised end-to-end

### Notes

- The Python package is unchanged — same API, same behavior; the wheel is a drop-in for `normalize_text(text, language=...)`
- `tts_utils` (sound words, `add_random_commas`) stays pure-Python by design
- Flipping consumers to the wheel is a deployment decision per consumer; output is proven identical and the parity CI keeps both locked

## v0.6.1

Raw-particle TTS fixes — the last of the same family as the `!`/`&`/`*` bug.

### Fixed

- Negative signs: `-` before digits speaks the language's negative word (`negative` / `negatif` / `负`) instead of reaching TTS raw (`suhu -5` → `suhu negatif lima`). Digit-joined dashes (`03-8888`, `3-10`) keep dash behavior.
- URL query strings: `?` and `=` are spoken (`question mark` / `equals`, 问号 / 等于) instead of reaching TTS raw.
- No-minutes meridian times normalize: `jam 3 pm` → `tiga sore` (id), `jumpa 3 petang` → `tiga petang` (ms), `at 7 pm` → `seven p m` (en).

## v0.6.0

Layered pronunciation mappings — model-specific corrections and company personalization without global state.

### Added

- **Pronunciation layers**: legacy global < named profile < `Config.pronunciations`; later layers win, `None` deletes a term from lower layers
- **Named profiles**: `register_pronunciation_profile(name, mappings)` for TTS-model or company tables at startup; `"builtin"` (default) and `"none"` ship with the library
- `Config.pronunciation_profile` and `Config.pronunciations` — request-scoped, thread-safe personalization; every layer supports language scoping (`{"*": {...}, "ms": {...}}`; flat dict = all languages)
- `pronunciations_from_file(path)` — JSON loader for deployment-driven config
- `normalize_text_detailed()` records each fired pronunciation replacement (`rule: "pronunciation"`)
- Config entries that look like abbreviation expansions now `UserWarning` instead of raising — the caller owns their output; legacy `add_custom_mapping()` keeps its `ValueError`

### Changed

- **Malay honorifics (`Hj`, `Dr`, `Prof`, title identities `Dato`/`Datin`/`Datuk`) now apply to `ms`/`id` only** — English output stops inheriting them
- The `bias` → `bai yers` OCR patch is removed — fix OCR errors at the input source
- `Config.pronunciation_overrides = False` now disables all pronunciation behavior (every layer), not just the step-6 helper

## v0.5.0

Multilingual-first architecture and a clean API. Breaking changes ride in the 0.x minor.

### Breaking

- `language` is now a required argument — the old `"en"` default silently normalized non-English input with English rules; omitting it now raises `TypeError`
- `normalize_text` always returns `str`; the `verbose=True` dict return moved to `normalize_text_detailed()` as a typed `NormalizationResult` (`.text`, `.original`, `.language`, `.mappings`, `.rules`)
- Legacy `**kwargs` boolean flags removed (`sound_words_field`, `normalize_spacing`, `*_flag`, ...); use `config=Config(...)`, `profile=`, or `disable=`
- Deprecated shims removed: `minimal_config()` / `basic_config()` / `standard_config()` / `aggressive_config()`, `NormalizationConfig`, `FeatureGroup`, `FeatureLevel`, `Config.with_feature()`, `Config.with_sound_words()`

### Added

- **Language packs** (`revo_norm.langpack`): every language is one `LanguagePack` — unit tables, month names, symbol words, digit words, currency names, plus behavior hooks (`normalize`, `speak_number`, `num2word`, `preparse_number_formats`). `register_language(pack)` adds a new language with zero core-file edits; `LanguagePack`, `register_language`, `supported_languages` are exported
- `Profile` and `Feature` enums — IDE autocomplete for `profile=` and `disable=`
- `normalize_text(config=...)` accepts a ready `Config`

### Changed

- Core pipeline files no longer branch on language codes for vocabulary; per-language dispatch lives in the packs (81 → 39 language branches in `text_normalizer`/`shared_features`/`entity_extractor`; the remainder is genuine per-language behavior)

## v0.4.2

TTS symbol fixes and Indonesian deltas validated on the TTS server.

### Fixed

- `*` and `!` are silently dropped for `en`/`ms` (prose and URL queries) instead of being pronounced literally ("asterisk", exclamation over-emphasis); `zh`/`zh_my`/`id` keep prior behavior
- `&` inside URL query strings (`https://example.com?a=1&b=2`) is spoken ("and" / 和) instead of reaching TTS raw
- Indonesian dotted no-meridian times (`jam 09.30`) read as a time ("sembilan tiga puluh"), not a decimal
- Indonesian `am`/`pm` map to `pagi`/`sore`/`malam` in `normalize_time` instead of leaving raw "pm"
- Indonesian negative cardinals speak `negatif`, not `minus`

## v0.4.1

Explicit language scope and more lenient language input.

### Added

- `SUPPORTED_LANGUAGES` exported from the package root — single source of truth for the accepted language codes (`en`, `ms`, `id`, `zh`, `zh_my`)

### Changed

- `language` input is canonicalized (trimmed and lowercased) before dispatch, so `"ID"`, `" en "`, `"Zh_MY"` resolve correctly
- Unknown-language validation now also fails fast at the entity-extractor entry point (not just `normalize_text`)

## v0.4.0

Indonesian (`id`) support.

### Added

- Indonesian normalizer: number-to-words, rupiah currency, dates (Maret/Agustus), times (siang/sore), percentages (persen), measurements
- Indonesian written number conventions: dotted thousands (`1.000.000`), comma decimals (`10,5`), and rupiah slang suffixes (`rb` = ribu, `jt` = juta, `M` = miliar, `T` = triliun)

### Changed

- **Breaking:** unknown language codes now raise `ValueError` instead of silently falling back to Malay normalization
- Single-digit-month slash dates (`15/8/2025`) now speak the month name instead of reading the digit

## v0.3.0

Chinese support.

### Added

- Standard Chinese (`zh`) and Malaysian Chinese (`zh_my`) normalizers
- Chinese number-to-words, currency, dates/times, and measurements
- `zh_my` colloquial currency and code-mixing support

## v0.2.0

Single unified pipeline architecture with entity extraction always enabled.

### Added

- **Single pipeline architecture**: Entity extraction is always enabled, replacing the dual-pipeline (legacy vs entity extraction) approach
- **`profile=` parameter**: Preset configurations (`minimal`, `basic`, `standard`, `aggressive`) passed directly to `normalize_text()`
- **`disable=` parameter**: Disable specific features by name instead of individual boolean flags
- **`Config` dataclass**: Simple feature-toggle configuration replacing `NormalizationConfig`, `FeatureGroup`, `FeatureLevel`, and `Profile` enums
- **Pronunciation mappings system**: Explicit mappings applied first in pipeline (`GUI` -> `gooey`, `ASCII` -> `as key`, `IEEE` -> `I triple E`)
- **Custom pronunciation mappings**: `add_custom_mapping()` API for user-defined overrides
- **Currency entity extraction**: `RM`, `$`, `EUR`, `GBP` amounts protected from downstream acronym/abbreviation expansion
- **Currency K/M/B/T suffix expansion**: `RM30K` -> `RM30000`, `RM1.5M` -> `RM1500000`
- **Date recognition**: `15/08/2025` -> spoken date form (DD/MM/YYYY and YYYY-MM-DD formats)
- **Time recognition**: `3:30 pm` -> spoken time form
- **Malay-specific features**: IC numbers, hari bulan, hijri years, x-kali multipliers, elongated word normalization
- **Entity types**: URL, email, date, time, currency, fraction, temperature, IC, hari_bulan, hijri, x_kali

### Changed

- Entity extraction runs automatically (no `extract_entities_first` flag needed)
- Acronym expansion merged into `replace_letter_period_sequences()`
- 96 acronyms removed from abbreviation list to avoid conflicts with acronym expansion
- Single-letter and short uppercase abbreviation expansion disabled to prevent breaking domain terms
- Pre-compiled regex patterns at module level for performance

### Deprecated

- Boolean flags in `normalize_text()` (e.g., `normalize_temperature_flag=False`) -- use `disable=["temperature"]`
- `NormalizationConfig` class -- use `Config`
- `FeatureGroup`, `FeatureLevel`, `Profile` enums -- use plain strings
- `minimal_config()`, `basic_config()`, `standard_config()`, `aggressive_config()` -- use `Config.from_profile()` or `profile=` parameter
- `config.with_feature()` -- set attributes directly: `cfg.acronyms = False`
- `config.with_sound_words()` -- set `cfg.sound_words` directly

### Fixed

- Date/fraction pattern conflict (entity extraction prevents false fraction matches on dates)
- `RM` currency split to "R M" by acronym expansion (entity extraction protects currency)
- `JSON`/`ML`/`AI` unwanted splitting by pronunciation mappings and acronym rules
- Double pronunciation override call
- Hari bulan placeholder robustness (`__HARI_BULAN__`)
- Hyphens between words replaced with spaces before acronym expansion

## v0.1.0

Initial release.

- Basic text normalization for English and Malay
- Number-to-words conversion
- Contraction expansion (English)
- Abbreviation expansion
- Acronym expansion
- URL and email to spoken form
- Currency normalization
- Temperature normalization
- Fraction normalization
- Measurement normalization
