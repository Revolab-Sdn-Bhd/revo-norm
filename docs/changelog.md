# Changelog

All notable changes to revo-norm are documented here.

## v0.6.0 (Current)

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
