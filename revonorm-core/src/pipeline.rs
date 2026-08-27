//! pipeline — mirrors revo_norm/text_normalizer.py's top-level flow for the
//! stages this crate implements (milestone 1): the language normalizer pass
//! wrapped by the pack-driven steps whose behavior is per-language data.
//!
//! Python order (subset): currency suffix -> ussd -> negative sign ->
//! [entity extraction: python-only for now] -> pronunciation mappings ->
//! [number normalization inside the language pass] -> special chars ->
//! exclamation drop.
//!
//! Differences from Python (documented, not ported yet): entity extraction,
//! pronunciation profile layers, URL/email speech. They land in later
//! milestones; parity fixtures only cover ported behavior.

use fancy_regex::Regex;
use std::sync::LazyLock;

use crate::langpack::{get_pack, is_supported};
use crate::normalize::normalize_malay;

static RE_NEG_SIGN: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<![\w\-])-(?=\d)").unwrap());
static RE_MULTI_SPACES: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\s+").unwrap());
static RE_EXCLAIM: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"!+").unwrap());
static RE_ENTITY_PH: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"<<<[A-Z_]+_(\d+)>>>").unwrap());

/// Replace entity placeholders with pure-alpha stash tokens (`entstashaa`,
/// `entstashab`, ...) that no language pass can match — port of python
/// _stash_placeholders. Returns (text, stash) where stash[i] holds the
/// original placeholder string for token i.
fn stash_placeholders(text: &str) -> (String, Vec<String>) {
    let mut stash: Vec<String> = Vec::new();
    let out = RE_ENTITY_PH
        .replace_all(text, |c: &fancy_regex::Captures<str>| {
            let idx = stash.len();
            stash.push(c.get(0).map(|m| m.as_str().to_string()).unwrap_or_default());
            format!("entstash{}", idx_to_letters(idx))
        })
        .into_owned();
    (out, stash)
}

/// 0→aa, 1→ab, ..., 25→az, 26→ba — python's _idx_to_letters.
fn idx_to_letters(mut n: usize) -> String {
    let letters = b"abcdefghijklmnopqrstuvwxyz";
    let mut out = Vec::new();
    loop {
        out.push(letters[n % 26] as char);
        n = if n >= 26 { (n / 26) - 1 } else { break };
    }
    out.reverse();
    out.into_iter().collect()
}

fn unstash_placeholders(text: &str, stash: &[String]) -> String {
    let mut out = text.to_string();
    for (i, ph) in stash.iter().enumerate() {
        out = out.replace(&format!("entstash{}", idx_to_letters(i)), ph);
    }
    out
}

/// Normalize `text` for a language. `language` must be one of
/// `supported_languages()`; anything else returns an error message the
/// caller can surface (the Python library raises ValueError naming the code —
/// the wasm/C callers get the same message as an Err string).
pub fn normalize(text: &str, language: &str) -> Result<String, String> {
    normalize_with(text, language, &crate::options::Options::default())
}

/// `normalize` with an options object (FFI callers parse from JSON).
pub fn normalize_with(
    text: &str,
    language: &str,
    options: &crate::options::Options,
) -> Result<String, String> {
    let code = language.trim().to_lowercase();
    if !is_supported(&code) {
        let langs = crate::langpack::supported_languages().join(", ");
        return Err(format!(
            "Unsupported language: '{language}' (expected one of ({langs}))"
        ));
    }
    if text.trim().is_empty() {
        return Ok(String::new());
    }

    // All five languages have ported normalizers; unsupported codes were
    // rejected by is_supported above (never a silent Malay fallback).

    let pack = get_pack(&code);
    // id rewrites its written number conventions first (dotted thousands,
    // comma decimals, Rp slang) and skips the en-semantics M expansion.
    let mut out = if code == "id" {
        crate::normalize_id::preparse_number_formats(text)
    } else {
        text.to_string()
    };
    let suffix_out = if code == "id" {
        crate::normalize::expand_suffixes_no_m(&out)
    } else {
        crate::normalize::expand_all_currency_suffixes(&out)
    };
    out = suffix_out;

    // Step 1b (python): USSD codes (*120# -> star satu dua kosong hash).
    out = crate::misc_passes::expand_ussd(&out, &code);

    // Step 1c (python): negative signs — before number normalization.
    out = RE_NEG_SIGN
        .replace_all(&out, format!(" {} ", pack.negative_word))
        .into_owned();

    // Step 1c-2 (python): digit-by-digit contexts (exit 5, iPhone 15).
    out = crate::misc_passes::expand_digit_contexts(&out, &code);

    // Step 3 (python): entity extraction — gated types only fire when their
    // feature is on (python: temperature -> TEMPERATURE, fractions ->
    // FRACTION/ADDRESS_SLASH, ...); URL/EMAIL/PHONE/VERSION/CURRENCY always.
    let (out, entities) = crate::entities::extract_gated(&out, options);

    // Step 6 (python): pronunciation overrides — BEFORE measurements, so a
    // raw "2kg" becomes singular "2 kilogram" before the unit table runs
    // ("two kilogram weights", not "two kilograms weights").
    let out = if options.is_enabled("pronunciation_overrides") {
        crate::normalize_en::apply_pronunciation_overrides(&out, &code)
    } else {
        out
    };

    // Step 6.1 (python): measurements — after overrides, before the language
    // normalizer so "5km" never becomes "five K M" (acronym split).
    let out = if options.is_enabled("measurements") {
        crate::shared::normalize_measurements(&out, &code)
    } else {
        out
    };

    // Step 4 (python): pronunciation mappings — gated by
    // pronunciation_overrides (minimal profile skips WiFi -> wi fi).
    let out = if options.is_enabled("pronunciation_overrides") {
        let pron_table = options.resolve_pronunciations(&code);
        crate::pron::apply(&out, &pron_table)
    } else {
        out
    };

    // Step 5 (python): stash placeholders as pure-alpha tokens so language
    // normalizers (mixed-alnum, number passes) cannot touch them.
    let (out, stash) = stash_placeholders(&out);

    // Step 6-2 (python): elongated words (betuiii -> betuii), before the
    // language normalizer, gated by the elongated feature.
    let out = if options.is_enabled("elongated") {
        crate::misc_passes::normalize_elongated(&out)
    } else {
        out
    };

    // Language normalizer pass (currency, dates, times, numbers...).
    let out = match code.as_str() {
        "id" => crate::normalize_id::normalize_indonesian(&out),
        "en" => crate::normalize_en::normalize_english(&out),
        "zh" => crate::normalize_zh::normalize_zh(&out),
        "zh_my" => crate::normalize_zh::normalize_zh_my(&out),
        _ => normalize_malay(&out),
    };

    // Step 6-3 (python): repeated-word comma insertion — always runs, after
    // the language normalizer ("test test test test" -> "test test test, test").
    let out = crate::misc_passes::insert_comma_repeated(&out, 3);

    // Step 6b (python): acronym expansion (letter-period, hyphen split,
    // uppercase runs) — after the language normalizer.
    let out = if options.is_enabled("acronyms") {
        crate::normalize_en::replace_letter_period_sequences(&out)
    } else {
        out
    };

    // Step 6.5: unstash back to <<<TYPE_N>>> placeholders.
    let mut out = unstash_placeholders(&out, &stash);

    // Step 7 (python): restore entities as spoken form. DATE/TIME only speak
    // when their feature is on (python speak_entities gating); gated types
    // were never extracted when off, so only the always-on set + speak
    // decision matter here.
    out = crate::entities::restore_gated(&out, &entities, &code, options);

    // Special chars: spell out symbols from the pack table.
    let out = if options.is_enabled("special_chars") {
        let mut o = out;
        for (ch, spoken) in &pack.symbol_words {
            o = o.replace(
                &ch.to_string(),
                &format!(" {spoken} "),
            );
        }
        for (sym, spoken) in &pack.symbol_words_multi {
            o = o.replace(sym, &format!(" {spoken} "));
        }
        o
    } else {
        out
    };

    // Exclamation drop where the pack opts in.
    let out = if pack.drops_exclamation {
        RE_EXCLAIM.replace_all(&out, "").into_owned()
    } else {
        out
    };

    Ok(RE_MULTI_SPACES.replace_all(out.trim(), " ").into_owned())
}
